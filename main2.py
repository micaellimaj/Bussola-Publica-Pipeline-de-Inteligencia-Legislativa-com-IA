import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Importa os Pipelines unificados da pasta src
from src.transformation import PipelineEtapa3
from src.ai_layer import PipelineEtapa4
from src.classificacao_tematica import PipelineEtapa5

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Parâmetros operacionais para a camada de IA
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MODELO_IA = os.getenv("MODELO_IA", "gpt-4o-mini")

# Parâmetros operacionais para a classificação temática (Etapa 5 - Caminho A)
MODELO_EMBEDDING = os.getenv("MODELO_EMBEDDING", "text-embedding-3-small")
LIMIAR_TEMA = float(os.getenv("LIMIAR_TEMA", "0.20"))

RAW_DIR = Path("data/raw")
DATA_STR = datetime.today().strftime("%Y%m%d")

# Configuração global de logs direcionada para a pasta correta
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/pipeline_executivo_{DATA_STR}.log", encoding="utf-8"),
    ]
)

# Silencia logs verbosos do SQLAlchemy
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.ERROR)

log = logging.getLogger(__name__)

if __name__ == "__main__":
    # Validações rápidas de infraestrutura de ambiente
    erros = []
    if not DATABASE_URL:
        erros.append("DATABASE_URL não encontrada no .env")
    if not OPENAI_API_KEY:
        erros.append("OPENAI_API_KEY não encontrada no .env")

    if erros:
        for erro in erros:
            log.error(erro)
        exit(1)

    log.info("=" * 60)
    log.info("INICIANDO PIPELINE OTIMIZADO (SEM COLETA DE API)")
    log.info("=" * 60)

    # -------------------------------------------------------------------------
    # ETAPA 3: TRANSFORMAÇÃO E CARGA (POSTGRESQL / SUPABASE)
    # -------------------------------------------------------------------------
    log.info("\n>>> Executando Etapa 3: Carga de Dados no PostgreSQL <<<")
    pipeline_etapa3 = PipelineEtapa3(
        raw_dir=RAW_DIR,
        database_url=DATABASE_URL
    )
    resumo_carga = pipeline_etapa3.executar()
    log.info(f"Carga finalizada. Resumo: {resumo_carga}")

    # -------------------------------------------------------------------------
    # ETAPA 4: CAMADA DE IA (GERAÇÃO DE RESUMOS EXECUTIVOS)
    # -------------------------------------------------------------------------
    log.info("\n>>> Executando Etapa 4: Enriquecimento com IA (OpenAI) <<<")
    pipeline_etapa4 = PipelineEtapa4(
        database_url=DATABASE_URL,
        openai_api_key=OPENAI_API_KEY,
        modelo=MODELO_IA,
        batch_size=BATCH_SIZE,
        dry_run=DRY_RUN
    )
    resumo_ia = pipeline_etapa4.executar()

    # -------------------------------------------------------------------------
    # ETAPA 5: CLASSIFICAÇÃO TEMÁTICA (EMBEDDINGS + SIMILARIDADE DE COSSENO)
    # -------------------------------------------------------------------------
    log.info("\n>>> Executando Etapa 5: Classificação Temática (Embeddings) <<<")
    pipeline_etapa5 = PipelineEtapa5(
        database_url=DATABASE_URL,
        openai_api_key=OPENAI_API_KEY,
        modelo=MODELO_EMBEDDING,
        batch_size=BATCH_SIZE,
        dry_run=DRY_RUN,
        limiar_tema=LIMIAR_TEMA
    )
    resumo_tema = pipeline_etapa5.executar()

    log.info("=" * 60)
    log.info("PIPELINE RÁPIDO CONCLUÍDO COM SUCESSO!")
    log.info("=" * 60)
