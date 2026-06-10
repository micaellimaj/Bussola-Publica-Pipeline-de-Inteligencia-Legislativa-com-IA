#!/usr/bin/env python3
# =============================================================================
# Bussola Publica - Pipeline Otimizado / Modo Rápido (Sem Coleta de API)
# -----------------------------------------------------------------------------
# Executa apenas as etapas de processamento local e IA (Etapas 3, 4 e 5)
# Ideal para desenvolvimento rápido ou atualizações em lote de IA.
# =============================================================================

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Força o silenciamento do motor do SQLAlchemy E do logger do root para pacotes terceiros
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.ERROR)

# Configuração global de logs direcionada para o console e arquivos diários
DATA_STR = datetime.today().strftime("%Y%m%d")
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
log = logging.getLogger(__name__)

# Importações diretas dos módulos da pasta src
from src.transformation import PipelineEtapa3
from src.ai_layer import PipelineEtapa4

# Raiz do repositorio
ROOT = Path(__file__).resolve().parent


def main() -> int:
    load_dotenv()

    log.info("=" * 70)
    log.info("BUSSOLA PUBLICA - Pipeline Otimizado (Sem Coleta da API)")
    log.info(f"Raiz do projeto: {ROOT}")
    
    dry = os.getenv("DRY_RUN", "true").strip().lower() == "true"
    log.info(f"DRY_RUN da IA: {dry}  (true = IA so estima custo, nao gasta)")
    log.info("-" * 70)

    database_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    batch_size = int(os.getenv("BATCH_SIZE", "10"))
    
    # Variáveis da Camada de IA (Chat e Embeddings)
    modelo_ia = os.getenv("MODELO_IA", "gpt-4o-mini")
    modelo_embed = os.getenv("MODELO_EMBED", "text-embedding-3-small")
    
    raw_dir = "data/raw"

    # Validações rápidas de infraestrutura de ambiente
    erros = []
    if not database_url:
        erros.append("DATABASE_URL não encontrada no .env")
    if not openai_api_key:
        erros.append("OPENAI_API_KEY não encontrada no .env")
        
    if erros:
        for erro in erros:
            log.error(erro)
        return 1

    inicio_total = time.time()

    # -------------------------------------------------------------------------
    # ETAPA 3: TRANSFORMAÇÃO, VALIDAÇÃO E CARGA LOCAL NO POSTGRESQL (SUPABASE)
    # -------------------------------------------------------------------------
    log.info("\n>>> ETAPA 3: TRANSFORMAÇÃO E CARGA NO BANCO (ARQUIVOS LOCAIS) <<<")
    inicio_stage = time.time()
    try:
        pipeline_etapa3 = PipelineEtapa3(raw_dir=raw_dir, database_url=database_url)
        resumo_carga = pipeline_etapa3.executar()
        
        # Verifica se houve falha crítica interna
        if not resumo_carga:
            raise RuntimeError("A Etapa 3 retornou um resumo vazio. Possível falha de banco.")
             
        dur_stage = time.time() - inicio_stage
        log.info(f"OK          -> Etapa 3 - Transformacao + Carga concluída ({dur_stage:.1f}s)")
    except Exception as e:
        log.error(f"FALHOU      -> Etapa 3 - Transformacao + Carga: {e}")
        log.info("=" * 70)
        log.info("PIPELINE INTERROMPIDO na etapa: Etapa 3 - Transformacao + Carga.")
        return 1

    # -------------------------------------------------------------------------
    # ETAPA 4 e 5: CAMADA DE IA - ENRIQUECIMENTO COM RESUMOS EXECUTIVOS E TEMAS
    # -------------------------------------------------------------------------
    log.info("\n>>> ETAPA 4 e 5: ENRIQUECIMENTO INTELIGENTE (OPENAI IA) <<<")
    inicio_stage = time.time()
    try:
        # Instanciação corrigida mapeando a assinatura exata de PipelineIA do ai_layer.py
        pipeline_etapa4 = PipelineEtapa4(
            database_url=database_url,
            openai_api_key=openai_api_key,
            modelo_chat=modelo_ia,
            modelo_embed=modelo_embed,
            batch_size=batch_size,
            dry_run=dry,
        )
        resumo_ia = pipeline_etapa4.executar()
        
        # Captura falhas controladas retornadas pelo dicionário do Orquestrador de IA
        if resumo_ia and resumo_ia.get("status") == "erro":
            raise RuntimeError(f"A camada de IA falhou internamente: {resumo_ia.get('motivo')}")
        
        dur_stage = time.time() - inicio_stage
        log.info(f"OK          -> Etapa 4 e 5 - IA concluída ({dur_stage:.1f}s)")
    except Exception as e:
        log.error(f"FALHOU      -> Etapa 4 e 5 - IA: {e}")
        log.info("=" * 70)
        log.info("PIPELINE INTERROMPIDO na etapa: Etapa 4 e 5 - IA: Resumos e Temas.")
        return 1

    dur_total = time.time() - inicio_total
    log.info("=" * 70)
    log.info(f"PIPELINE RÁPIDO CONCLUÍDO COM SUCESSO em {dur_total:.1f}s. Processamento OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())