"""
=============================================================================
BUSSOLA PUBLICA - Projeto Integrador | Pos Tech Engenharia de Dados e IA
=============================================================================
Etapa 4: Camada de IA - Resumo Executivo Automatizado (Opcao B)

Objetivo do negocio:
    Para cada proposicao legislativa extraida e carregada nas etapas anteriores,
    gerar automaticamente um resumo em linguagem clara, objetiva e orientada
    para tomada de decisao de executivos — substituindo o trabalho manual dos
    analistas da Bussola Publica.

O que esta etapa faz:
    1. Le as proposicoes do PostgreSQL (fato_proposicoes) que ainda nao
       possuem resumo gerado.
    2. Envia a ementa de cada proposicao para o modelo GPT-4o via OpenAI API,
       com um prompt estruturado para producao de texto executivo.
    3. Salva o resumo como nova coluna 'resumo_executivo' em fato_proposicoes.
    4. Persiste um backup local em JSON (data/processed/) por seguranca.

Boas praticas aplicadas (Nivelamento + APIs + POO / Prof. Iago Braz / Xperiun):

  POO (Programacao Orientada a Objetos):
    - LeitorProposicoes      -> responsabilidade unica: ler do banco
    - GeradorResumoExecutivo -> responsabilidade unica: chamar a OpenAI API
    - AtualizadorBanco       -> responsabilidade unica: persistir resumos no banco
    - PipelineEtapa4         -> orquestra as tres pecas acima

  Controle de custo:
    - Modo DRY_RUN (padrao: True) -> estima o custo sem chamar a API
    - BATCH_SIZE configuravel     -> processa N proposicoes por vez
    - Skip automatico de proposicoes que ja tem resumo (idempotente)

  Boas praticas de APIs:
    - try/except com excecoes especificas
    - timeout em todas as requisicoes
    - time.sleep() entre chamadas (rate limit)
    - Credenciais via .env (nunca hardcoded)
    - Logging completo para rastrear execucao em producao

Como usar:
    1. Certifique-se de ter o .env configurado:
          DATABASE_URL=postgresql://usuario:senha@host:porta/banco
          OPENAI_API_KEY=sk-...
    2. Instale as dependencias:
          pip install openai sqlalchemy psycopg2-binary pandas python-dotenv
    3. Rode primeiro em modo DRY_RUN (padrao) para estimar custo:
          python Desafio_Etapa4_IA.py
    4. Quando satisfeito com o custo estimado, ajuste DRY_RUN = False no .env
       ou execute:
          DRY_RUN=false python Desafio_Etapa4_IA.py

Modelo de dados:
    fato_proposicoes (tabela existente, Etapa 3)
      + resumo_executivo TEXT  <- nova coluna adicionada por esta etapa
      + data_resumo     TIMESTAMP <- quando o resumo foi gerado
=============================================================================
"""

# PASSO 1: Importar bibliotecas
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# PASSO 2: Variaveis de ambiente
# NUNCA deixe credenciais hardcoded - regra fundamental do curso
load_dotenv()

DATABASE_URL  = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Controles operacionais (podem ser sobrescritos via .env)
# DRY_RUN=True  -> apenas estima custo, nao chama a API nem escreve no banco
# DRY_RUN=False -> executa de verdade
DRY_RUN    = os.getenv("DRY_RUN", "true").lower() == "true"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))   # proposicoes por execucao
MODELO_IA  = os.getenv("MODELO_IA", "gpt-4o-mini") # gpt-4o-mini: 10x mais barato, otimo para resumos curtos

# Diretorios
PROCESSED_DIR = Path("data/processed")
DATA          = datetime.today().strftime("%Y%m%d_%H%M%S")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"etapa4_ia_{DATA[:8]}.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

# Referencia de custo OpenAI (maio/2025 - atualize se mudar)
# https://openai.com/api/pricing/
CUSTO_INPUT_POR_1K_TOKENS  = {"gpt-4o": 0.0025, "gpt-4o-mini": 0.000150}
CUSTO_OUTPUT_POR_1K_TOKENS = {"gpt-4o": 0.010,  "gpt-4o-mini": 0.000600}
TOKENS_MEDIOS_INPUT        = 300   # estimativa conservadora por proposicao
TOKENS_MEDIOS_OUTPUT       = 150   # resumo de ~3 linhas


# =============================================================================
# CLASSE: LeitorProposicoes
#
# Responsabilidade UNICA: ler proposicoes do PostgreSQL.
# Nao sabe nada de IA ou atualizacao - so le dados.
# =============================================================================
class LeitorProposicoes:
    """
    Le proposicoes pendentes de resumo na tabela fato_proposicoes.

    'Pendente' significa: resumo_executivo IS NULL ou coluna nao existe.
    Isso torna a etapa idempotente: pode rodar varias vezes sem
    reprocessar o que ja foi feito.
    """

    def __init__(self, engine):
        """
        Parametros:
            engine: SQLAlchemy engine conectado ao PostgreSQL
        """
        self.engine = engine

    def ler_pendentes(self, limite=None):
        """
        Retorna um DataFrame com proposicoes que ainda nao tem resumo.

        Parametros:
            limite (int): maximo de registros a retornar (None = sem limite)

        Retorna:
            DataFrame com colunas: id_proposicao, sigla_tipo, numero, ano, ementa
        """
        log.info("-" * 50)
        log.info("LEITURA: Proposicoes pendentes de resumo")
        log.info("-" * 50)

        # Verifica se a coluna resumo_executivo ja existe
        # Se nao existir, todas as proposicoes sao consideradas pendentes
        sql_verifica_coluna = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'fato_proposicoes'
              AND column_name = 'resumo_executivo';
        """

        limite_clause = f"LIMIT {limite}" if limite else ""

        try:
            with self.engine.connect() as conn:
                resultado = conn.execute(text(sql_verifica_coluna)).fetchall()
                coluna_existe = len(resultado) > 0

            if coluna_existe:
                # Busca apenas proposicoes sem resumo (processamento incremental)
                sql = f"""
                    SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                    FROM fato_proposicoes
                    WHERE resumo_executivo IS NULL
                      AND ementa IS NOT NULL
                      AND trim(ementa) <> ''
                    ORDER BY data_apresentacao DESC NULLS LAST
                    {limite_clause};
                """
                log.info("  Coluna 'resumo_executivo' encontrada - buscando apenas pendentes.")
            else:
                # Primeira execucao: busca todas as proposicoes com ementa
                sql = f"""
                    SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                    FROM fato_proposicoes
                    WHERE ementa IS NOT NULL
                      AND trim(ementa) <> ''
                    ORDER BY data_apresentacao DESC NULLS LAST
                    {limite_clause};
                """
                log.info("  Primeira execucao - coluna 'resumo_executivo' sera criada.")

            df = pd.read_sql(text(sql), con=self.engine)
            log.info(f"  {len(df)} proposicoes encontradas para processar.")
            return df

        except SQLAlchemyError as e:
            log.error(f"  Erro ao ler proposicoes: {e}")
            return pd.DataFrame()
        except Exception as e:
            log.error(f"  Erro inesperado ao ler proposicoes: {e}")
            return pd.DataFrame()


# =============================================================================
# CLASSE: GeradorResumoExecutivo
#
# Responsabilidade UNICA: gerar resumos executivos via OpenAI API.
# Nao sabe nada de banco de dados ou arquivos - so conversa com a IA.
# =============================================================================
class GeradorResumoExecutivo:
    """
    Gera resumos executivos de proposicoes legislativas usando GPT-4o.

    Por que GPT-4o?
    O desafio menciona GPT-4o para resumos e linguagem clara. Para producao
    com alto volume, gpt-4o-mini e uma alternativa 10x mais barata com
    qualidade suficiente para resumos curtos. Configure via MODELO_IA no .env.

    Prompt estrategia:
    - System prompt: define o perfil do modelo como analista legislativo
    - User prompt: entrega a ementa e pede resumo em formato especifico
    - Resposta estruturada em 3 partes: O que e, Quem e afetado, Ponto de atencao
    """

    SYSTEM_PROMPT = """Voce e um analista legislativo senior da consultoria Bussola Publica.
Sua funcao e transformar ementas tecnicas de proposicoes da Camara dos Deputados
em resumos claros e acionaveis para executivos e areas de relacoes governamentais.

Regras para o resumo:
- Maximo 3 frases objetivas
- Linguagem direta, sem jargao juridico
- Estrutura: (1) O que propoe, (2) Quem/o que e impactado, (3) Ponto de atencao para empresas
- Se a ementa for muito tecnica ou vaga, informe isso claramente
- Responda APENAS com o resumo, sem introducoes como 'O resumo e:' ou 'Esta proposicao...'"""

    USER_PROMPT_TEMPLATE = """Proposicao: {sigla_tipo} {numero}/{ano}

Ementa oficial:
{ementa}

Gere o resumo executivo:"""

    def __init__(self, api_key, modelo=MODELO_IA):
        """
        Parametros:
            api_key (str): chave da OpenAI API (do .env)
            modelo  (str): modelo a usar (gpt-4o ou gpt-4o-mini)
        """
        self.modelo = modelo
        self.client = OpenAI(api_key=api_key)

    def gerar(self, id_proposicao, sigla_tipo, numero, ano, ementa):
        """
        Gera o resumo executivo de uma proposicao.

        Parametros:
            id_proposicao (int): ID para logs e rastreabilidade
            sigla_tipo    (str): ex: "PL", "PEC", "MPV"
            numero        (str): numero da proposicao
            ano           (str): ano da proposicao
            ementa        (str): texto da ementa oficial

        Retorna:
            str: resumo executivo gerado, ou None em caso de erro
        """
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            sigla_tipo=sigla_tipo or "Proposicao",
            numero=numero or "",
            ano=ano or "",
            ementa=ementa.strip()
        )

        try:
            resposta = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt}
                ],
                max_tokens=300,   # resumo curto - 3 frases cabem em ~150 tokens
                temperature=0.3,  # baixa aleatoriedade -> mais consistencia nos resumos
                timeout=30        # timeout obrigatorio - regra do curso
            )
            resumo = resposta.choices[0].message.content.strip()
            tokens_usados = resposta.usage.total_tokens
            log.info(f"    [ID {id_proposicao}] Resumo gerado | {tokens_usados} tokens")
            return resumo

        except APITimeoutError:
            log.warning(f"    [ID {id_proposicao}] Timeout na OpenAI API - pulando.")
        except RateLimitError:
            log.warning(f"    [ID {id_proposicao}] Rate limit atingido - aguardando 60s.")
            time.sleep(60)
        except APIConnectionError as e:
            log.error(f"    [ID {id_proposicao}] Erro de conexao: {e}")
        except APIStatusError as e:
            log.error(f"    [ID {id_proposicao}] Erro de status {e.status_code}: {e.message}")
        except Exception as e:
            log.error(f"    [ID {id_proposicao}] Erro inesperado: {e}")

        return None

    def estimar_custo(self, quantidade_proposicoes):
        """
        Estima o custo total em USD antes de processar.

        Por que estimar antes?
        O desafio orienta: 'Antes de rodar para 1000 proposicoes,
        teste com 10. Veja quanto custou. Multiplique. Decida.'
        Esta funcao faz exatamente isso de forma automatica.

        Parametros:
            quantidade_proposicoes (int): quantas proposicoes serao processadas

        Retorna:
            dict com custo estimado em USD e BRL
        """
        custo_input  = CUSTO_INPUT_POR_1K_TOKENS.get(self.modelo, 0.0025)
        custo_output = CUSTO_OUTPUT_POR_1K_TOKENS.get(self.modelo, 0.010)

        total_tokens_input  = quantidade_proposicoes * TOKENS_MEDIOS_INPUT
        total_tokens_output = quantidade_proposicoes * TOKENS_MEDIOS_OUTPUT

        custo_usd = (total_tokens_input  / 1000 * custo_input) + \
                    (total_tokens_output / 1000 * custo_output)
        custo_brl = custo_usd * 5.20  # taxa aproximada - atualize conforme necessario

        return {
            "modelo":               self.modelo,
            "quantidade":           quantidade_proposicoes,
            "tokens_estimados":     total_tokens_input + total_tokens_output,
            "custo_usd":            round(custo_usd, 4),
            "custo_brl":            round(custo_brl, 4),
        }


# =============================================================================
# CLASSE: AtualizadorBanco
#
# Responsabilidade UNICA: persistir resumos no PostgreSQL.
# Nao sabe nada de IA ou leitura - so escreve resultados.
# =============================================================================
class AtualizadorBanco:
    """
    Persiste os resumos executivos na tabela fato_proposicoes.

    Estrategia de upsert:
    - Adiciona as colunas 'resumo_executivo' e 'data_resumo' se nao existirem
    - Atualiza somente os registros processados nesta execucao
    - Nao toca nos registros que ja tinham resumo (idempotente)
    """

    def __init__(self, engine):
        """
        Parametros:
            engine: SQLAlchemy engine conectado ao PostgreSQL
        """
        self.engine = engine

    def garantir_colunas(self):
        """
        Adiciona as colunas 'resumo_executivo' e 'data_resumo'
        em fato_proposicoes caso ainda nao existam.

        Por que ALTER TABLE e nao recriar a tabela?
        A tabela ja tem dados da Etapa 3. Recriar perderia tudo.
        ALTER TABLE ADD COLUMN IF NOT EXISTS e seguro e idempotente.
        """
        sqls = [
            """
            ALTER TABLE fato_proposicoes
            ADD COLUMN IF NOT EXISTS resumo_executivo TEXT;
            """,
            """
            ALTER TABLE fato_proposicoes
            ADD COLUMN IF NOT EXISTS data_resumo TIMESTAMP;
            """
        ]
        try:
            with self.engine.begin() as conn:   # begin() garante commit automatico
                for sql in sqls:
                    conn.execute(text(sql))
            log.info("  Colunas 'resumo_executivo' e 'data_resumo' garantidas.")
            return True
        except SQLAlchemyError as e:
            log.error(f"  Erro ao garantir colunas: {e}")
            return False

    def atualizar(self, id_proposicao, resumo):
        """
        Atualiza o resumo de uma proposicao especifica.

        Usa UPDATE + WHERE para tocar apenas o registro correto,
        sem reconstruir a tabela inteira.

        Parametros:
            id_proposicao (int): ID da proposicao a atualizar
            resumo        (str): texto do resumo gerado pela IA

        Retorna:
            bool: True se atualizou, False se falhou
        """
        sql = text("""
            UPDATE fato_proposicoes
            SET resumo_executivo = :resumo,
                data_resumo      = :data_resumo
            WHERE id_proposicao  = :id_proposicao
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {
                    "resumo":        resumo,
                    "data_resumo":   datetime.now(),
                    "id_proposicao": id_proposicao
                })
            return True
        except SQLAlchemyError as e:
            log.error(f"  [ID {id_proposicao}] Erro ao atualizar banco: {e}")
            return False

    def salvar_backup_json(self, resultados, caminho):
        """
        Salva os resultados em JSON local como backup de seguranca.

        Por que salvar JSON alem do banco?
        Seguindo o principio da Etapa 2: dados persistidos localmente
        protegem contra falhas de conectividade e custos de re-execucao.

        Parametros:
            resultados (list): lista de dicts com id_proposicao e resumo
            caminho    (Path): onde salvar
        """
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
            log.info(f"  Backup salvo em: {caminho}")
        except Exception as e:
            log.warning(f"  Aviso: nao foi possivel salvar backup JSON: {e}")


# =============================================================================
# CLASSE: PipelineEtapa4
#
# Responsabilidade: orquestrar leitura + geracao de IA + persistencia.
# Nao sabe nada de HTTP, SQL ou OpenAI diretamente - so coordena as pecas.
# Analogo ao PipelineEtapa3 da etapa anterior.
# =============================================================================
class PipelineEtapa4:
    """
    Orquestra o pipeline de IA da Etapa 4:
      1. Le proposicoes pendentes do banco (LeitorProposicoes)
      2. Estima o custo antes de processar (GeradorResumoExecutivo.estimar_custo)
      3. Gera resumos executivos via GPT-4o (GeradorResumoExecutivo.gerar)
      4. Persiste os resumos no banco e em JSON (AtualizadorBanco)
    """

    def __init__(self, database_url, openai_api_key, modelo=MODELO_IA,
                 batch_size=BATCH_SIZE, dry_run=DRY_RUN):
        """
        Parametros:
            database_url    (str): connection string PostgreSQL do .env
            openai_api_key  (str): chave da OpenAI API do .env
            modelo          (str): modelo OpenAI a usar
            batch_size      (int): proposicoes por execucao
            dry_run         (bool): True = so estima, False = processa de verdade
        """
        self.batch_size = batch_size
        self.dry_run    = dry_run

        # Cria engine SQLAlchemy (reutilizavel entre leitura e escrita)
        self.engine = create_engine(database_url)

        # Instancia cada peca com sua responsabilidade separada
        self.leitor     = LeitorProposicoes(self.engine)
        self.gerador    = GeradorResumoExecutivo(openai_api_key, modelo)
        self.atualizador = AtualizadorBanco(self.engine)

    def _testar_conexao(self):
        """Verifica se o banco esta acessivel antes de comecar."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("  Conexao com PostgreSQL: OK")
            return True
        except Exception as e:
            log.error(f"  Falha ao conectar no PostgreSQL: {e}")
            return False

    def executar(self):
        """
        Executa o pipeline completo.

        Fluxo:
          1. Conecta ao banco
          2. Le proposicoes pendentes (ate batch_size)
          3. Exibe estimativa de custo
          4. Se DRY_RUN: encerra aqui
          5. Se nao: processa cada proposicao, atualiza banco, salva backup
        """
        import time as time_module
        inicio = time_module.time()

        log.info("=" * 60)
        log.info("BUSSOLA PUBLICA - Pipeline IA | Etapa 4: Resumo Executivo")
        log.info(f"  Modelo : {self.gerador.modelo}")
        log.info(f"  Batch  : {self.batch_size} proposicoes")
        log.info(f"  Modo   : {'DRY RUN (estimativa)' if self.dry_run else 'PRODUCAO'}")
        log.info("=" * 60)

        # --- 1. Testa conexao ---
        if not self._testar_conexao():
            log.error("Pipeline abortado: banco inacessivel.")
            return {}

        # --- 2. Le proposicoes pendentes ---
        df = self.leitor.ler_pendentes(limite=self.batch_size)

        if df.empty:
            log.info("  Nenhuma proposicao pendente. Pipeline encerrado.")
            return {"processadas": 0, "erros": 0}

        # --- 3. Estimativa de custo (sempre exibida, mesmo em producao) ---
        estimativa = self.gerador.estimar_custo(len(df))
        log.info("")
        log.info("ESTIMATIVA DE CUSTO:")
        log.info(f"  Proposicoes : {estimativa['quantidade']}")
        log.info(f"  Tokens est. : ~{estimativa['tokens_estimados']:,}")
        log.info(f"  Custo USD   : ~$ {estimativa['custo_usd']:.4f}")
        log.info(f"  Custo BRL   : ~R$ {estimativa['custo_brl']:.4f}")
        log.info(f"  Modelo      : {estimativa['modelo']}")
        log.info("")

        if self.dry_run:
            log.info("  [DRY RUN] Estimativa concluida. Para executar de verdade:")
            log.info("  -> Defina DRY_RUN=false no .env ou na variavel de ambiente.")
            log.info("  -> Execute novamente: python Desafio_Etapa4_IA.py")
            return {"dry_run": True, "estimativa": estimativa}

        # --- 4. Garante colunas no banco ---
        if not self.atualizador.garantir_colunas():
            log.error("Pipeline abortado: nao foi possivel adicionar colunas.")
            return {}

        # --- 5. Processa cada proposicao ---
        log.info("-" * 50)
        log.info(f"GERANDO RESUMOS para {len(df)} proposicoes...")
        log.info("-" * 50)

        resultados = []   # lista vazia -> for -> append (padrao do curso)
        contagem   = {"processadas": 0, "erros": 0, "puladas": 0}

        for i, linha in df.iterrows():
            id_prop    = linha["id_proposicao"]
            sigla_tipo = linha.get("sigla_tipo", "")
            numero     = linha.get("numero", "")
            ano        = linha.get("ano", "")
            ementa     = linha.get("ementa", "")

            log.info(f"  [{contagem['processadas'] + 1}/{len(df)}] "
                     f"{sigla_tipo} {numero}/{ano} | ID {id_prop}")

            # Gera o resumo
            resumo = self.gerador.gerar(id_prop, sigla_tipo, numero, ano, ementa)

            if resumo:
                # Atualiza no banco
                ok = self.atualizador.atualizar(id_prop, resumo)

                if ok:
                    contagem["processadas"] += 1
                    resultados.append({         # append acumula (padrao do curso)
                        "id_proposicao": id_prop,
                        "sigla_tipo":    sigla_tipo,
                        "numero":        numero,
                        "ano":           ano,
                        "ementa":        ementa,
                        "resumo_executivo": resumo,
                        "data_resumo":   datetime.now().isoformat()
                    })
                else:
                    contagem["erros"] += 1
            else:
                contagem["erros"] += 1

            # Rate limit: pausa entre chamadas para nao sobrecarregar a API
            # Orientacao do curso: time.sleep() entre requisicoes em loop
            time.sleep(0.5)

        # --- 6. Salva backup JSON ---
        if resultados:
            caminho_backup = PROCESSED_DIR / f"resumos_{DATA}.json"
            self.atualizador.salvar_backup_json(resultados, caminho_backup)

        # --- 7. Finaliza ---
        duracao = time_module.time() - inicio
        log.info("")
        log.info("=" * 60)
        log.info("ETAPA 4 CONCLUIDA - Resumo de execucao:")
        log.info(f"  Proposicoes processadas : {contagem['processadas']}")
        log.info(f"  Erros                   : {contagem['erros']}")
        log.info(f"  Puladas                 : {contagem['puladas']}")
        log.info(f"  Duracao total           : {duracao:.1f}s")
        log.info(f"  Custo real estimado     : ~$ {estimativa['custo_usd']:.4f} USD")
        log.info("=" * 60)
        log.info("Proximo passo -> Etapa 5: Automacao com n8n.")

        # Fecha o engine
        self.engine.dispose()

        return contagem


# =============================================================================
# EXECUCAO PRINCIPAL
# =============================================================================
if __name__ == "__main__":

    # Validacoes de ambiente antes de comecar
    erros_config = []

    if not DATABASE_URL:
        erros_config.append("DATABASE_URL nao encontrada no .env")

    if not OPENAI_API_KEY:
        erros_config.append("OPENAI_API_KEY nao encontrada no .env")

    if erros_config:
        log.error("Configuracao incompleta. Corrija o .env:")
        for erro in erros_config:
            log.error(f"  -> {erro}")
        log.error("")
        log.error("Exemplo de .env:")
        log.error("  DATABASE_URL=postgresql://usuario:senha@host:5432/banco")
        log.error("  OPENAI_API_KEY=sk-proj-...")
        log.error("  DRY_RUN=true       # true = so estima custo, false = executa")
        log.error("  BATCH_SIZE=10      # proposicoes por execucao")
        log.error("  MODELO_IA=gpt-4o   # ou gpt-4o-mini para menor custo")
        exit(1)

    # Instancia e executa o pipeline
    pipeline = PipelineEtapa4(
        database_url   = DATABASE_URL,
        openai_api_key = OPENAI_API_KEY,
        modelo         = MODELO_IA,
        batch_size     = BATCH_SIZE,
        dry_run        = DRY_RUN
    )

    resultado = pipeline.executar()
