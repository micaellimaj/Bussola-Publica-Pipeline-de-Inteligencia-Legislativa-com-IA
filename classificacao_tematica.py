"""
=============================================================================
BUSSOLA PUBLICA - Projeto Integrador | Pos Tech Engenharia de Dados e IA
=============================================================================
Etapa 4 (Caminho A) -> habilita a Etapa 5: Classificacao Tematica por Embeddings

Por que este modulo existe:
    A Etapa 4 ja entrega o resumo executivo (Caminho B). Para a Etapa 5
    (automacao + alertas) o tema precisa ser um dado REAL na tabela - nao
    palavra-chave solta. Sem tema persistido, o alerta de "proposicao de tema
    critico" vira teatro. Este modulo cria a coluna 'tema' em fato_proposicoes
    usando embeddings, de forma que o workflow n8n consiga filtrar por tema.

O que faz (Caminho A do desafio):
    1. Le proposicoes do PostgreSQL/Supabase que ainda nao tem tema.
    2. Gera o embedding da ementa via OpenAI (text-embedding-3-small - barato).
    3. Gera embeddings para ~10 temas de negocio (Saude, Tributario, etc.).
    4. Calcula a similaridade de cosseno entre cada ementa e cada tema.
       O tema de maior similaridade vira a classificacao.
    5. Grava 'tema', 'tema_score' e 'data_tema' em fato_proposicoes.
    6. Salva backup local em JSON (data/processed/).

Boas praticas aplicadas (Nivelamento + APIs + POO / Prof. Iago Braz / Xperiun):
    POO:
        - LeitorProposicoes        -> le do banco (responsabilidade unica)
        - ClassificadorTematico    -> conversa com a OpenAI e calcula cosseno
        - AtualizadorBanco         -> persiste o tema no banco
        - PipelineClassificacao    -> orquestra as tres pecas
    Controle de custo:
        - DRY_RUN (padrao True)    -> estima custo sem chamar a API nem gravar
        - BATCH_SIZE configuravel  -> processa N proposicoes por execucao
        - Idempotente              -> pula o que ja tem tema
    APIs:
        - try/except especifico, timeout, time.sleep entre chamadas
        - Credenciais via .env (NUNCA hardcoded)

Como usar (a partir da raiz do projeto, com Poetry):
    1. .env configurado com DATABASE_URL e OPENAI_API_KEY
    2. poetry install
    3. Estimar custo (modo padrao):   poetry run python -m src.classificacao_tematica
    4. Rodar de verdade:              DRY_RUN=false poetry run python -m src.classificacao_tematica

Modelo de dados (colunas novas em fato_proposicoes):
    + tema        TEXT        -> tema de negocio classificado
    + tema_score  FLOAT8      -> similaridade de cosseno (0 a 1) com o tema
    + data_tema   TIMESTAMPTZ -> quando a classificacao foi gerada
=============================================================================
"""

import os
import json
import time
import math
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# -----------------------------------------------------------------------------
# Variaveis de ambiente (mesmas chaves usadas no resto do projeto)
# -----------------------------------------------------------------------------
load_dotenv()

DATABASE_URL   = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DRY_RUN        = os.getenv("DRY_RUN", "true").lower() == "true"
BATCH_SIZE     = int(os.getenv("BATCH_SIZE", "20"))
MODELO_EMBED   = os.getenv("MODELO_EMBEDDING", "text-embedding-3-small")
# Score minimo para aceitar a classificacao. Abaixo disso -> "Outros".
LIMIAR_TEMA    = float(os.getenv("LIMIAR_TEMA", "0.20"))

PROCESSED_DIR  = Path("data/processed")
DATA           = datetime.today().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("classificacao_tematica")

# Referencia de custo OpenAI (maio/2025 - atualize se mudar)
# text-embedding-3-small: ~US$ 0.02 por 1.000.000 tokens
CUSTO_EMBED_POR_1K_TOKENS = 0.00002
TOKENS_MEDIOS_EMENTA      = 120   # ementas costumam ser curtas


# =============================================================================
# CATALOGO DE TEMAS DE NEGOCIO
#
# Cada tema tem uma frase-descricao rica (nao so a palavra) porque o embedding
# do tema fica mais discriminativo quando descreve o escopo. Ajuste/expanda
# conforme os setores dos clientes da Bussola Publica.
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


# =============================================================================
# CLASSE: LeitorProposicoes  (responsabilidade unica: ler do banco)
# =============================================================================
class LeitorProposicoes:
    """Le proposicoes pendentes de tema na tabela fato_proposicoes."""

    def __init__(self, engine):
        self.engine = engine

    def ler_pendentes(self, limite=None):
        """
        Retorna DataFrame de proposicoes sem tema (idempotente).
        Se a coluna 'tema' ainda nao existe, todas as proposicoes com ementa
        sao consideradas pendentes.
        """
        log.info("-" * 60)
        log.info("LEITURA: proposicoes pendentes de classificacao tematica")

        sql_coluna = """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'fato_proposicoes' AND column_name = 'tema';
        """
        limite_clause = f"LIMIT {limite}" if limite else ""
        try:
            with self.engine.connect() as conn:
                tem_coluna = len(conn.execute(text(sql_coluna)).fetchall()) > 0

            filtro_tema = "AND tema IS NULL" if tem_coluna else ""
            sql = f"""
                SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                FROM fato_proposicoes
                WHERE ementa IS NOT NULL AND trim(ementa) <> ''
                  {filtro_tema}
                ORDER BY data_apresentacao DESC NULLS LAST
                {limite_clause};
            """
            df = pd.read_sql(text(sql), con=self.engine)
            log.info(f"  {len(df)} proposicoes para classificar.")
            return df
        except SQLAlchemyError as e:
            log.error(f"  Erro ao ler proposicoes: {e}")
            return pd.DataFrame()


# =============================================================================
# CLASSE: ClassificadorTematico  (OpenAI embeddings + cosseno)
# =============================================================================
class ClassificadorTematico:
    """
    Gera embeddings e classifica proposicoes por similaridade de cosseno.

    Por que cosseno e nao a propria LLM responder o tema?
      - Custo: 1 embedding por ementa e ordens de magnitude mais barato que
        uma chamada de chat por proposicao.
      - Consistencia: a lista de temas e fixa; a LLM poderia inventar rotulos
        novos. Cosseno sempre escolhe um tema do catalogo controlado.
      - Auditavel: guardamos o score, dando transparencia a classificacao.
    """

    def __init__(self, api_key, modelo=MODELO_EMBED, temas=None):
        self.modelo = modelo
        self.client = OpenAI(api_key=api_key)
        self.temas  = temas or TEMAS
        self._emb_temas = None   # cache dos embeddings dos temas

    # --- utilitarios de vetor (numpy seria opcional; mantido em puro Python) ---
    @staticmethod
    def _cosseno(a, b):
        """Similaridade de cosseno entre dois vetores (listas de float)."""
        dot = sum(x * y for x, y in zip(a, b))
        na  = math.sqrt(sum(x * x for x in a))
        nb  = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _embed(self, textos):
        """
        Gera embeddings para uma lista de textos (uma unica chamada = mais barato).
        Retorna lista de vetores na mesma ordem da entrada, ou None em erro.
        """
        try:
            resp = self.client.embeddings.create(
                model=self.modelo,
                input=textos,
                timeout=30,
            )
            return [d.embedding for d in resp.data]
        except RateLimitError:
            log.warning("  Rate limit - aguardando 60s.")
            time.sleep(60)
        except (APITimeoutError, APIConnectionError) as e:
            log.error(f"  Erro de conexao/timeout no embedding: {e}")
        except APIStatusError as e:
            log.error(f"  Erro de status {e.status_code}: {e.message}")
        except Exception as e:
            log.error(f"  Erro inesperado no embedding: {e}")
        return None

    def preparar_temas(self):
        """Gera (uma unica vez) os embeddings dos temas do catalogo."""
        log.info(f"  Gerando embeddings de {len(self.temas)} temas...")
        descricoes = list(self.temas.values())
        vetores    = self._embed(descricoes)
        if vetores is None:
            return False
        self._emb_temas = dict(zip(self.temas.keys(), vetores))
        return True

    def classificar_lote(self, ementas):
        """
        Classifica uma lista de ementas.
        Retorna lista de tuplas (tema, score) na ordem de entrada.
        """
        vetores = self._embed(ementas)
        if vetores is None:
            return [(None, 0.0)] * len(ementas)

        resultados = []
        for v in vetores:
            melhor_tema, melhor_score = "Outros", 0.0
            for tema, emb_tema in self._emb_temas.items():
                score = self._cosseno(v, emb_tema)
                if score > melhor_score:
                    melhor_tema, melhor_score = tema, score
            if melhor_score < LIMIAR_TEMA:
                melhor_tema = "Outros"
            resultados.append((melhor_tema, round(melhor_score, 4)))
        return resultados

    def estimar_custo(self, quantidade):
        """Estima custo total (ementas + temas) antes de rodar."""
        total_tokens = (quantidade * TOKENS_MEDIOS_EMENTA) + (len(self.temas) * 30)
        custo_usd = total_tokens / 1000 * CUSTO_EMBED_POR_1K_TOKENS
        return {
            "modelo": self.modelo,
            "quantidade": quantidade,
            "tokens_estimados": total_tokens,
            "custo_usd": round(custo_usd, 6),
            "custo_brl": round(custo_usd * 5.20, 6),
        }


# =============================================================================
# CLASSE: AtualizadorBanco  (responsabilidade unica: persistir o tema)
# =============================================================================
class AtualizadorBanco:
    """Persiste tema/tema_score em fato_proposicoes (ALTER + UPDATE idempotente)."""

    def __init__(self, engine):
        self.engine = engine

    def garantir_colunas(self):
        sqls = [
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS tema TEXT;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS tema_score FLOAT8;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS data_tema TIMESTAMPTZ;",
        ]
        try:
            with self.engine.begin() as conn:
                for s in sqls:
                    conn.execute(text(s))
            log.info("  Colunas 'tema', 'tema_score', 'data_tema' garantidas.")
            return True
        except SQLAlchemyError as e:
            log.error(f"  Erro ao garantir colunas: {e}")
            return False

    def atualizar(self, id_proposicao, tema, score):
        sql = text("""
            UPDATE fato_proposicoes
            SET tema = :tema, tema_score = :score, data_tema = :data
            WHERE id_proposicao = :id
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {
                    "tema": tema, "score": score,
                    "data": datetime.now(), "id": id_proposicao,
                })
            return True
        except SQLAlchemyError as e:
            log.error(f"  [ID {id_proposicao}] Erro ao atualizar: {e}")
            return False

    def salvar_backup_json(self, resultados, caminho):
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
            log.info(f"  Backup salvo em: {caminho}")
        except Exception as e:
            log.warning(f"  Nao foi possivel salvar backup: {e}")


# =============================================================================
# CLASSE: PipelineClassificacao  (orquestra leitura + IA + carga)
# =============================================================================
class PipelineClassificacao:
    def __init__(self, database_url, openai_api_key,
                 modelo=MODELO_EMBED, batch_size=BATCH_SIZE, dry_run=DRY_RUN):
        self.batch_size = batch_size
        self.dry_run    = dry_run
        self.engine     = create_engine(database_url)
        self.leitor     = LeitorProposicoes(self.engine)
        self.classif    = ClassificadorTematico(openai_api_key, modelo)
        self.atualizador = AtualizadorBanco(self.engine)

    def _testar_conexao(self):
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("  Conexao com PostgreSQL: OK")
            return True
        except Exception as e:
            log.error(f"  Falha ao conectar: {e}")
            return False

    def executar(self):
        inicio = time.time()
        log.info("=" * 60)
        log.info("BUSSOLA PUBLICA - Etapa IA | Classificacao Tematica (Embeddings)")
        log.info(f"  Modelo : {self.classif.modelo}")
        log.info(f"  Batch  : {self.batch_size} | Modo: {'DRY RUN' if self.dry_run else 'PRODUCAO'}")
        log.info("=" * 60)

        if not self._testar_conexao():
            return {}

        df = self.leitor.ler_pendentes(limite=self.batch_size)
        if df.empty:
            log.info("  Nenhuma proposicao pendente de tema. Encerrado.")
            return {"processadas": 0}

        est = self.classif.estimar_custo(len(df))
        log.info("")
        log.info("ESTIMATIVA DE CUSTO (embeddings):")
        log.info(f"  Proposicoes : {est['quantidade']}")
        log.info(f"  Tokens est. : ~{est['tokens_estimados']:,}")
        log.info(f"  Custo USD   : ~$ {est['custo_usd']:.6f}")
        log.info(f"  Custo BRL   : ~R$ {est['custo_brl']:.6f}")
        log.info("")

        if self.dry_run:
            log.info("  [DRY RUN] Estimativa concluida. Para rodar de verdade:")
            log.info("  -> DRY_RUN=false poetry run python -m src.classificacao_tematica")
            return {"dry_run": True, "estimativa": est}

        if not self.atualizador.garantir_colunas():
            return {}
        if not self.classif.preparar_temas():
            log.error("Pipeline abortado: falha ao gerar embeddings dos temas.")
            return {}

        log.info("-" * 60)
        log.info(f"CLASSIFICANDO {len(df)} proposicoes...")

        ementas = df["ementa"].fillna("").tolist()
        pares   = self.classif.classificar_lote(ementas)

        resultados = []
        contagem   = {"processadas": 0, "erros": 0}
        for (idx, linha), (tema, score) in zip(df.iterrows(), pares):
            id_prop = linha["id_proposicao"]
            if tema and self.atualizador.atualizar(id_prop, tema, score):
                contagem["processadas"] += 1
                resultados.append({
                    "id_proposicao": id_prop,
                    "sigla_tipo": linha.get("sigla_tipo", ""),
                    "numero": linha.get("numero", ""),
                    "ano": linha.get("ano", ""),
                    "tema": tema,
                    "tema_score": score,
                    "data_tema": datetime.now().isoformat(),
                })
                log.info(f"  [ID {id_prop}] -> {tema} ({score})")
            else:
                contagem["erros"] += 1

        if resultados:
            self.atualizador.salvar_backup_json(
                resultados, PROCESSED_DIR / f"temas_{DATA}.json"
            )

        # Distribuicao por tema (visao rapida de negocio)
        if resultados:
            dist = pd.Series([r["tema"] for r in resultados]).value_counts()
            log.info("")
            log.info("DISTRIBUICAO POR TEMA:")
            for tema, qtd in dist.items():
                log.info(f"  {tema:32s}: {qtd}")

        log.info("")
        log.info("=" * 60)
        log.info(f"CLASSIFICACAO CONCLUIDA: {contagem['processadas']} ok | "
                 f"{contagem['erros']} erros | {time.time()-inicio:.1f}s")
        log.info("=" * 60)
        self.engine.dispose()
        return contagem


# =============================================================================
# EXECUCAO PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    erros = []
    if not DATABASE_URL:
        erros.append("DATABASE_URL nao encontrada no .env")
    if not OPENAI_API_KEY:
        erros.append("OPENAI_API_KEY nao encontrada no .env")
    if erros:
        for e in erros:
            log.error(f"  -> {e}")
        raise SystemExit(1)

    PipelineClassificacao(
        database_url=DATABASE_URL,
        openai_api_key=OPENAI_API_KEY,
        modelo=MODELO_EMBED,
        batch_size=BATCH_SIZE,
        dry_run=DRY_RUN,
    ).executar()
