"""
Bússola Pública - Camada de IA | Classificação Temática por Embeddings

Por que este módulo existe:
    A Etapa 4 (ai_layer.py) já entrega o resumo executivo (Caminho B do
    desafio). Para a Etapa 5 (automação + alertas) o tema precisa ser um
    dado REAL na tabela `fato_proposicoes` - não palavra-chave solta. Sem
    tema persistido, o alerta de "proposição de tema crítico" no n8n vira
    teatro. Este módulo classifica cada proposição em um dos temas do
    catálogo de negócio usando embeddings + similaridade de cosseno
    (Caminho A do desafio).

O que faz:
    1. Lê proposições de fato_proposicoes que ainda não têm `tema`.
    2. Gera o embedding da ementa via OpenAI (text-embedding-3-small).
    3. Gera (uma única vez, com cache em memória) os embeddings dos temas
       do catálogo de negócio.
    4. Calcula a similaridade de cosseno entre cada ementa e cada tema.
       O tema de maior similaridade vira a classificação; abaixo do
       limiar configurado, classifica como "Outros".
    5. Grava `tema`, `tema_score` e `data_tema` em fato_proposicoes.
    6. Salva backup local em JSON (data/processed/), no mesmo padrão da
       Etapa 4.

Por que cosseno e não a própria LLM responder o tema?
    - Custo: 1 embedding por ementa é ordens de magnitude mais barato que
      uma chamada de chat por proposição.
    - Consistência: a lista de temas é fixa; a LLM poderia inventar
      rótulos novos. Cosseno sempre escolhe um tema do catálogo controlado.
    - Auditável: o score fica salvo em `tema_score`, dando transparência
      à classificação.

Controle de custo:
    - DRY_RUN (padrão True) -> só estima o custo, não chama a API nem grava.
    - BATCH_SIZE configurável -> processa N proposições por execução.
    - Idempotente -> `ler_pendentes` pula proposições que já têm `tema`.
"""

import json
import logging
import math
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configuração do Logger local caso o arquivo seja chamado diretamente
log = logging.getLogger(__name__)


# =============================================================================
# CATÁLOGO DE TEMAS DE NEGÓCIO
#
# Cada tema tem uma frase-descrição rica (não só a palavra) porque o
# embedding do tema fica mais discriminativo quando descreve o escopo.
# Ajuste/expanda conforme os setores dos clientes da Bússola Pública.
# =============================================================================
TEMAS = {
    "Tecnologia e IA": (
        "Tecnologia, inteligencia artificial, dados pessoais, internet, "
        "telecomunicacoes, inovacao, startups, software, plataformas digitais e "
        "regulacao de algoritmos."
    ),
    "Tributario": (
        "Tributos, impostos, reforma tributaria, carga fiscal, ICMS, IRPF, "
        "isencoes, incentivos fiscais e arrecadacao."
    ),
    "Saude": (
        "Saude publica, SUS, medicamentos, planos de saude, vigilancia sanitaria, "
        "hospitais, vacinas e profissionais de saude."
    ),
    "Trabalho e Previdencia": (
        "Direitos trabalhistas, CLT, emprego, salario minimo, sindicatos, "
        "previdencia social, aposentadoria e relacoes de trabalho."
    ),
    "Meio Ambiente": (
        "Meio ambiente, clima, licenciamento ambiental, desmatamento, saneamento, "
        "energia renovavel, residuos e sustentabilidade."
    ),
    "Economia e Financas": (
        "Economia, mercado financeiro, bancos, credito, juros, inflacao, cambio, "
        "investimentos e orcamento publico."
    ),
    "Educacao": (
        "Educacao basica e superior, escolas, universidades, FIES, professores, "
        "curriculo, financiamento educacional e ensino."
    ),
    "Seguranca Publica": (
        "Seguranca publica, policia, crime, armas, codigo penal, sistema "
        "prisional e combate ao trafico."
    ),
    "Agronegocio": (
        "Agronegocio, agricultura, pecuaria, credito rural, defensivos, exportacao "
        "de commodities e producao no campo."
    ),
    "Infraestrutura e Transporte": (
        "Infraestrutura, rodovias, portos, aeroportos, mobilidade urbana, "
        "concessoes, obras publicas e transporte."
    ),
    "Direitos e Cidadania": (
        "Direitos humanos, igualdade, direitos do consumidor, familia, minorias, "
        "acesso a justica e cidadania."
    ),
}

# Tema atribuído quando a melhor similaridade fica abaixo do limiar
TEMA_PADRAO_FORA_LIMIAR = "Outros"


class LeitorProposicoes:
    """
    Lê proposições pendentes de classificação temática na tabela
    fato_proposicoes.

    'Pendente' significa: tema IS NULL ou a coluna `tema` ainda não existe.
    Isso torna a etapa idempotente: pode rodar várias vezes sem reprocessar
    o que já foi classificado.
    """

    def __init__(self, engine):
        """
        Parâmetros:
            engine: SQLAlchemy engine conectado ao PostgreSQL (Supabase)
        """
        self.engine = engine

    def ler_pendentes(self, limite=None) -> pd.DataFrame:
        """
        Retorna um DataFrame com proposições que ainda não têm tema.

        Parâmetros:
            limite (int): máximo de registros a retornar (None = sem limite)

        Retorna:
            DataFrame com colunas: id_proposicao, sigla_tipo, numero, ano, ementa
        """
        log.info("-" * 50)
        log.info("LEITURA: Proposições pendentes de classificação temática")
        log.info("-" * 50)

        # Verifica se a coluna `tema` já existe na tabela fato_proposicoes
        sql_verifica_coluna = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'fato_proposicoes'
              AND column_name = 'tema';
        """

        limite_clause = f"LIMIT {limite}" if limite else ""

        try:
            with self.engine.connect() as conn:
                resultado = conn.execute(text(sql_verifica_coluna)).fetchall()
                coluna_existe = len(resultado) > 0

            if coluna_existe:
                # Busca apenas proposições sem tema (processamento incremental / idempotente)
                sql = f"""
                    SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                    FROM fato_proposicoes
                    WHERE tema IS NULL
                      AND ementa IS NOT NULL
                      AND trim(ementa) <> ''
                    ORDER BY data_apresentacao DESC NULLS LAST
                    {limite_clause};
                """
                log.info("  [Tema] Coluna 'tema' encontrada - buscando apenas pendentes.")
            else:
                # Primeira execução: busca todas as proposições válidas com ementa
                sql = f"""
                    SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                    FROM fato_proposicoes
                    WHERE ementa IS NOT NULL
                      AND trim(ementa) <> ''
                    ORDER BY data_apresentacao DESC NULLS LAST
                    {limite_clause};
                """
                log.info("  [Tema] Primeira execução - colunas 'tema'/'tema_score'/'data_tema' serão criadas dinamicamente.")

            df = pd.read_sql(text(sql), con=self.engine)
            log.info(f"  [Tema] {len(df)} proposições encontradas para classificar.")
            return df

        except SQLAlchemyError as e:
            log.error(f"  [Erro Banco] Erro ao ler proposições no PostgreSQL: {e}")
            return pd.DataFrame()
        except Exception as e:
            log.error(f"  [Erro Inesperado] Erro ao identificar registros pendentes: {e}")
            return pd.DataFrame()


class ClassificadorTematico:
    """
    Gera embeddings (OpenAI) e classifica proposições por similaridade de
    cosseno contra o catálogo de temas de negócio.
    """

    # Referência de custo OpenAI - text-embedding-3-small: ~US$ 0.02 / 1M tokens
    CUSTO_EMBED_POR_1K_TOKENS = 0.00002
    TOKENS_MEDIOS_EMENTA = 120  # ementas costumam ser curtas

    def __init__(self, api_key: str, modelo: str = "text-embedding-3-small",
                 temas: dict = None, limiar_tema: float = 0.20):
        """
        Parâmetros:
            api_key (str): Chave de autenticação da OpenAI API
            modelo (str): Identificador do modelo de embedding (ex: text-embedding-3-small)
            temas (dict): Catálogo {tema: descrição}. Usa TEMAS por padrão.
            limiar_tema (float): Score mínimo de cosseno para aceitar a
                classificação. Abaixo disso, o tema vira "Outros".
        """
        self.modelo = modelo
        self.client = OpenAI(api_key=api_key)
        self.temas = temas or TEMAS
        self.limiar_tema = limiar_tema
        self._emb_temas = None  # cache dos embeddings dos temas

    @staticmethod
    def _cosseno(a, b) -> float:
        """Similaridade de cosseno entre dois vetores (listas de float)."""
        dot = sum(x * y for x, y in zip(a, b))
        norma_a = math.sqrt(sum(x * x for x in a))
        norma_b = math.sqrt(sum(y * y for y in b))
        if norma_a == 0 or norma_b == 0:
            return 0.0
        return dot / (norma_a * norma_b)

    def _embed(self, textos: list):
        """
        Gera embeddings para uma lista de textos (uma única chamada = mais
        barato). Retorna lista de vetores na mesma ordem da entrada, ou
        None em caso de erro.
        """
        try:
            resposta = self.client.embeddings.create(
                model=self.modelo,
                input=textos,
                timeout=30,
            )
            return [d.embedding for d in resposta.data]
        except RateLimitError:
            log.warning("    [Tema] Rate limit atingido na OpenAI. Pausando execução por 60s...")
            time.sleep(60)
        except (APITimeoutError, APIConnectionError) as e:
            log.error(f"    [Tema] Falha de conexão/timeout ao gerar embeddings: {e}")
        except APIStatusError as e:
            log.error(f"    [Tema] Resposta de erro HTTP da API OpenAI ({e.status_code}): {e.message}")
        except Exception as e:
            log.error(f"    [Tema] Erro inesperado ao gerar embeddings: {e}")
        return None

    def preparar_temas(self) -> bool:
        """Gera (uma única vez) os embeddings dos temas do catálogo."""
        log.info(f"  [Tema] Gerando embeddings de {len(self.temas)} temas do catálogo...")
        descricoes = list(self.temas.values())
        vetores = self._embed(descricoes)
        if vetores is None:
            return False
        self._emb_temas = dict(zip(self.temas.keys(), vetores))
        return True

    def classificar_lote(self, ementas: list) -> list:
        """
        Classifica uma lista de ementas.

        Retorna:
            lista de tuplas (tema, score) na ordem de entrada.
        """
        vetores = self._embed(ementas)
        if vetores is None:
            return [(None, 0.0)] * len(ementas)

        resultados = []
        for v in vetores:
            melhor_tema, melhor_score = TEMA_PADRAO_FORA_LIMIAR, 0.0
            for tema, emb_tema in self._emb_temas.items():
                score = self._cosseno(v, emb_tema)
                if score > melhor_score:
                    melhor_tema, melhor_score = tema, score
            if melhor_score < self.limiar_tema:
                melhor_tema = TEMA_PADRAO_FORA_LIMIAR
            resultados.append((melhor_tema, round(melhor_score, 4)))
        return resultados

    def estimar_custo(self, quantidade_proposicoes: int) -> dict:
        """Estima custo total (ementas + temas) antes de rodar."""
        total_tokens = (
            (quantidade_proposicoes * self.TOKENS_MEDIOS_EMENTA)
            + (len(self.temas) * 30)
        )
        custo_usd = total_tokens / 1000 * self.CUSTO_EMBED_POR_1K_TOKENS
        custo_brl = custo_usd * 5.20  # Cotação base para precificação estimada

        return {
            "modelo": self.modelo,
            "quantidade": quantidade_proposicoes,
            "tokens_estimados": total_tokens,
            "custo_usd": round(custo_usd, 6),
            "custo_brl": round(custo_brl, 6),
        }


class AtualizadorBanco:
    """
    Persiste tema/tema_score/data_tema em fato_proposicoes
    (ALTER + UPDATE idempotente).
    """

    def __init__(self, engine):
        self.engine = engine

    def garantir_colunas(self) -> bool:
        """
        Verifica e injeta as colunas necessárias à classificação temática de
        forma idempotente.
        """
        sqls = [
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS tema TEXT;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS tema_score FLOAT8;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS data_tema TIMESTAMPTZ;",
        ]
        try:
            with self.engine.begin() as conn:
                for sql in sqls:
                    conn.execute(text(sql))
            log.info("  [DB Update] Colunas estruturais 'tema', 'tema_score' e 'data_tema' validadas/criadas.")
            return True
        except SQLAlchemyError as e:
            log.error(f"  [DB Update] Falha ao injetar colunas de tema no PostgreSQL: {e}")
            return False

    def atualizar(self, id_proposicao: int, tema: str, score: float) -> bool:
        """
        Executa o update atômico de uma proposição classificada. `tema`,
        `tema_score` e `data_tema` são gravados juntos no mesmo UPDATE.
        """
        sql = text("""
            UPDATE fato_proposicoes
            SET tema       = :tema,
                tema_score = :score,
                data_tema  = :data_tema
            WHERE id_proposicao = :id_proposicao;
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {
                    "tema": tema,
                    "score": score,
                    "data_tema": datetime.now(),
                    "id_proposicao": id_proposicao,
                })
            return True
        except SQLAlchemyError as e:
            log.error(f"  [DB Update] [ID {id_proposicao}] Falha no UPDATE: {e}")
            return False

    def salvar_backup_json(self, resultados: list, caminho_arquivo: Path):
        """
        Cria cópia física local dos dados enriquecidos para auditoria ou
        recuperação ágil.
        """
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
            log.info(f"  [Backup] Dados armazenados preventivamente em: {caminho_arquivo}")
        except Exception as e:
            log.warning(f"  [Backup] Não foi possível salvar backup em JSON: {e}")


class PipelineEtapa5:
    """
    Orquestra o pipeline de IA da Etapa 5 (classificação temática):
      1. Lê proposições pendentes do banco (LeitorProposicoes)
      2. Estima o custo antes de processar (ClassificadorTematico.estimar_custo)
      3. Gera embeddings dos temas + das ementas e calcula similaridade de
         cosseno (ClassificadorTematico)
      4. Persiste tema/tema_score/data_tema no banco e em JSON (AtualizadorBanco)
    """

    def __init__(self, database_url: str, openai_api_key: str,
                 modelo: str = "text-embedding-3-small", batch_size: int = 20,
                 dry_run: bool = True, limiar_tema: float = 0.20):
        """
        Parâmetros vindos de forma tratada a partir do main.py
        """
        self.batch_size = batch_size
        self.dry_run = dry_run

        # Parâmetros de data para o backup em disco
        self.timestamp_execucao = datetime.today().strftime("%Y%m%d_%H%M%S")
        self.processed_dir = Path("data/processed")

        # Cria engine SQLAlchemy único reutilizável
        self.engine = create_engine(database_url)

        # Instancia as peças com responsabilidades segregadas (Injeção de Dependência)
        self.leitor = LeitorProposicoes(self.engine)
        self.classificador = ClassificadorTematico(openai_api_key, modelo, limiar_tema=limiar_tema)
        self.atualizador = AtualizadorBanco(self.engine)

    def _testar_conexao(self) -> bool:
        """Verifica se o banco de dados está acessível antes de acionar a IA."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            log.info("  [Conexão] Comunicação direta com PostgreSQL: OK")
            return True
        except Exception as e:
            log.error(f"  [Conexão] Falha ao alcançar o PostgreSQL antes do loop de IA: {e}")
            return False

    def executar(self) -> dict:
        """
        Executa a governança completa da Etapa 5 (classificação temática) de
        forma idempotente.
        """
        inicio_cronometro = time.time()

        log.info("=" * 60)
        log.info("BÚSSOLA PÚBLICA - Pipeline IA | Etapa 5: Classificação Temática (Embeddings)")
        log.info(f"  Modelo : {self.classificador.modelo}")
        log.info(f"  Batch  : {self.batch_size} proposições")
        log.info(f"  Limiar : {self.classificador.limiar_tema}")
        log.info(f"  Modo   : {'DRY RUN (Apenas Estimativa)' if self.dry_run else 'PRODUÇÃO (Gravação)'}")
        log.info("=" * 60)

        # 1. Validação de Conexão
        if not self._testar_conexao():
            log.error("Pipeline abortado: banco inacessível.")
            return {}

        # 2. Captura de Registros Pendentes
        df = self.leitor.ler_pendentes(limite=self.batch_size)

        if df.empty:
            log.info("  [INFO] Nenhuma proposição pendente de tema. Encerrando Etapa 5.")
            return {"processadas": 0, "erros": 0}

        log.info(f"  [Volume] Encontradas {len(df)} proposições pendentes para a janela atual (Batch: {self.batch_size}).")

        # 3. Estimativa Orçamentária Obrigatória
        estimativa = self.classificador.estimar_custo(len(df))
        log.info("\n=== ESTIMATIVA DE CUSTO FINANCEIRO (embeddings) ===")
        log.info(f"  Proposições a processar : {estimativa['quantidade']}")
        log.info(f"  Tokens Estimados        : ~{estimativa['tokens_estimados']:,}")
        log.info(f"  Custo Estimado USD      : $ {estimativa['custo_usd']:.6f}")
        log.info(f"  Custo Estimado BRL      : R$ {estimativa['custo_brl']:.6f}")
        log.info(f"  Modelo de IA Alvo       : {estimativa['modelo']}")
        log.info("====================================================\n")

        if self.dry_run:
            log.info("  [DRY RUN] Simulação finalizada. Nenhuma linha foi gravada ou consumida.")
            return {"dry_run": True, "estimativa": estimativa}

        # 4. Assegurar Colunas de Persistência
        if not self.atualizador.garantir_colunas():
            log.error("Pipeline abortado: Não foi possível estruturar as colunas de tema no banco.")
            return {}

        # 5. Embeddings do catálogo de temas (uma única vez)
        if not self.classificador.preparar_temas():
            log.error("Pipeline abortado: falha ao gerar embeddings dos temas do catálogo.")
            return {}

        # 6. Classificação em lote
        log.info("-" * 50)
        log.info(f"Classificando {len(df)} proposições por similaridade de cosseno...")
        log.info("-" * 50)

        ementas = df["ementa"].fillna("").tolist()
        pares = self.classificador.classificar_lote(ementas)

        resultados = []
        contagem = {"processadas": 0, "erros": 0}

        for (_, linha), (tema, score) in zip(df.iterrows(), pares):
            id_prop = linha["id_proposicao"]
            sigla_tipo = linha.get("sigla_tipo", "")
            numero = linha.get("numero", "")
            ano = linha.get("ano", "")

            if tema and self.atualizador.atualizar(id_prop, tema, score):
                contagem["processadas"] += 1
                resultados.append({
                    "id_proposicao": id_prop,
                    "sigla_tipo": sigla_tipo,
                    "numero": numero,
                    "ano": ano,
                    "tema": tema,
                    "tema_score": score,
                    "data_tema": datetime.now().isoformat(),
                })
                log.info(f"  [ID {id_prop}] {sigla_tipo} {numero}/{ano} -> {tema} ({score})")
            else:
                contagem["erros"] += 1

        # 7. Salvamento do Backup Local
        if resultados:
            caminho_backup = self.processed_dir / f"temas_{self.timestamp_execucao}.json"
            self.atualizador.salvar_backup_json(resultados, caminho_backup)

        # 8. Distribuição por tema (visão rápida de negócio)
        if resultados:
            dist = pd.Series([r["tema"] for r in resultados]).value_counts()
            log.info("")
            log.info("DISTRIBUIÇÃO POR TEMA:")
            for tema, qtd in dist.items():
                log.info(f"  {tema:32s}: {qtd}")

        # 9. Relatório de Encerramento
        duracao = time.time() - inicio_cronometro
        log.info("\n" + "=" * 60)
        log.info("ETAPA 5 (CLASSIFICAÇÃO TEMÁTICA) CONCLUÍDA")
        log.info(f"  Processadas com sucesso : {contagem['processadas']}")
        log.info(f"  Erros de processamento  : {contagem['erros']}")
        log.info(f"  Tempo de Execução       : {duracao:.1f}s")
        log.info(f"  Investimento Estimado   : $ {estimativa['custo_usd']:.6f} USD")
        log.info("=" * 60)

        self.engine.dispose()
        return contagem


# =============================================================================
# EXECUÇÃO PRINCIPAL (uso standalone, fora do main.py/main2.py)
# =============================================================================
if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    DATABASE_URL = os.getenv("DATABASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))
    MODELO_EMBEDDING = os.getenv("MODELO_EMBEDDING", "text-embedding-3-small")
    LIMIAR_TEMA = float(os.getenv("LIMIAR_TEMA", "0.20"))

    erros = []
    if not DATABASE_URL:
        erros.append("DATABASE_URL não encontrada no .env")
    if not OPENAI_API_KEY:
        erros.append("OPENAI_API_KEY não encontrada no .env")
    if erros:
        for e in erros:
            log.error(f"  -> {e}")
        sys.exit(1)

    PipelineEtapa5(
        database_url=DATABASE_URL,
        openai_api_key=OPENAI_API_KEY,
        modelo=MODELO_EMBEDDING,
        batch_size=BATCH_SIZE,
        dry_run=DRY_RUN,
        limiar_tema=LIMIAR_TEMA,
    ).executar()
