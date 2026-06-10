#!/usr/bin/env python3
# =============================================================================
# Bussola Publica - Orquestrador do pipeline (Etapa 5)
# -----------------------------------------------------------------------------
# Ponto de entrada chamado pelo no "Rodar Pipeline (main.py)" do workflow n8n:
#      cd /opt/bussola-publica && poetry run python main.py 2>&1
#
# Executa as etapas do desafio NA ORDEM e propaga o resultado pelo exit code:
#   - exit 0  -> n8n segue para o ramo de SUCESSO (digest por e-mail)
#   - exit !=0 -> n8n segue para o ramo de FALHA  (alerta por e-mail)
# =============================================================================

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Força o silenciamento do motor do SQLAlchemy E do logger do root para pacotes terceiros
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.ERROR)

# Configuração de Log global unificada para o Orquestrador
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Importações diretas dos módulos da pasta src
from src.diagnostico import executar_diagnostico
from src.extraction import (
    DeputadosExtractor,
    PartidosExtractor,
    ProposicoesExtractor,
    VotacoesExtractor
)
from src.transformation import PipelineEtapa3
from src.ai_layer import PipelineEtapa4

# Raiz do repositorio
ROOT = Path(__file__).resolve().parent


def _flag(nome: str, padrao: bool = True) -> bool:
    """Le uma variavel de ambiente booleana (true/false)."""
    return os.getenv(nome, "true" if padrao else "false").strip().lower() == "true"


def salvar_json_bruto(dados, subpasta, prefixo, pasta_raiz="data/raw"):
    """Salva os dados extraídos em arquivos estruturados que o Transformador espera."""
    pasta_destino = ROOT / pasta_raiz / subpasta
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{prefixo}_{timestamp}.json"
    caminho_completo = pasta_destino / nome_arquivo
    
    conteudo = {"dados": dados} if isinstance(dados, list) else dados

    with open(caminho_completo, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=4)
    
    log.info(f"   [Arquivo] Dados salvos brutos em: {caminho_completo}")


def main() -> int:
    load_dotenv()

    log.info("=" * 70)
    log.info("BUSSOLA PUBLICA - Orquestrador do pipeline Nativo (Etapa 5)")
    log.info(f"Raiz do projeto: {ROOT}")
    
    dry = os.getenv("DRY_RUN", "true").strip().lower() == "true"
    log.info(f"DRY_RUN da IA: {dry}  (true = IA so estima custo, nao gasta)")
    log.info("-" * 70)

    # -------------------------------------------------------------------------
    # VALIDAÇÃO ANTES DA EXECUÇÃO (DIAGNÓSTICO INTEGRADO)
    # -------------------------------------------------------------------------
    if not executar_diagnostico():
        log.error("Pipeline interrompido: O diagnóstico apontou falhas críticas no ambiente.")
        log.info("O n8n deve disparar o ALERTA DE FALHA.")
        return 1

    # Modo verificação: se CHECK_ONLY=true, para por aqui com sucesso
    if os.getenv("CHECK_ONLY", "false").strip().lower() == "true":
        log.info("CHECK_ONLY=true -> ambiente validado com sucesso. Saindo (0).")
        return 0

    database_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    batch_size = int(os.getenv("BATCH_SIZE", "10"))
    
    # Variáveis da Camada de IA (Chat e Embeddings)
    modelo_ia = os.getenv("MODELO_IA", "gpt-4o-mini")
    modelo_embed = os.getenv("MODELO_EMBED", "text-embedding-3-small")
    
    raw_dir = "data/raw"

    inicio_total = time.time()

    # -------------------------------------------------------------------------
    # ETAPA 1 e 2: EXTRAÇÃO DA API DA CÂMARA
    # -------------------------------------------------------------------------
    if _flag("RUN_EXTRACT", padrao=True):
        log.info("\n>>> ETAPA 2: EXTRAÇÃO DE DADOS DA API <<<")
        inicio_stage = time.time()
        try:
            api_deputados = DeputadosExtractor()
            api_partidos = PartidosExtractor()
            api_proposicoes = ProposicoesExtractor()
            api_votacoes = VotacoesExtractor()

            salvar_json_bruto(api_deputados.extrair(), "deputados", "deputados")
            salvar_json_bruto(api_partidos.extrair(), "partidos", "partidos")

            dados_prop_completos = api_proposicoes.extrair()
            salvar_json_bruto(dados_prop_completos["proposicoes"], "proposicoes", "proposicoes")
            salvar_json_bruto(dados_prop_completos["autores"], "proposicoes", "proposicoes_autores")

            dados_vot_completos = api_votacoes.extrair()
            salvar_json_bruto(dados_vot_completos["votacoes"], "votacoes", "votacoes")
            salvar_json_bruto(dados_vot_completos["votos"], "votacoes", "votos")

            dur_stage = time.time() - inicio_stage
            log.info(f"OK          -> Etapa 2 - Extracao concluída ({dur_stage:.1f}s)")
        except Exception as e:
            log.error(f"FALHOU      -> Etapa 2 - Extracao: {e}")
            log.info("=" * 70)
            log.info("PIPELINE INTERROMPIDO na etapa: Etapa 2 - Extracao (API Camara).")
            log.info("O n8n deve disparar o ALERTA DE FALHA.")
            return 1
    else:
        log.info("\n[Ignorado] Etapa 2 - Extração desabilitada via RUN_EXTRACT.")

    # -------------------------------------------------------------------------
    # ETAPA 3: TRANSFORMAÇÃO, VALIDAÇÃO E CARGA NO POSTGRESQL (SUPABASE)
    # -------------------------------------------------------------------------
    if _flag("RUN_TRANSFORM", padrao=True):
        log.info("\n>>> ETAPA 3: TRANSFORMAÇÃO E CARGA NO BANCO <<<")
        inicio_stage = time.time()
        try:
            pipeline_etapa3 = PipelineEtapa3(raw_dir=raw_dir, database_url=database_url)
            resumo_carga = pipeline_etapa3.executar()
            
            # Verifica se houve falha crítica interna que retornou dicionário vazio ou nulo
            if not resumo_carga:
                 raise RuntimeError("A Etapa 3 retornou um resumo vazio. Possível falha de banco.")
                 
            dur_stage = time.time() - inicio_stage
            log.info(f"OK          -> Etapa 3 - Transformacao + Carga concluída ({dur_stage:.1f}s)")
        except Exception as e:
            log.error(f"FALHOU      -> Etapa 3 - Transformacao + Carga: {e}")
            log.info("=" * 70)
            log.info("PIPELINE INTERROMPIDO na etapa: Etapa 3 - Transformacao + Carga.")
            log.info("O n8n deve disparar o ALERTA DE FALHA.")
            return 1
    else:
        log.info("\n[Ignorado] Etapa 3 - Transformação desabilitada via RUN_TRANSFORM.")

    # -------------------------------------------------------------------------
    # ETAPA 4 e 5: CAMADA DE IA - ENRIQUECIMENTO COM RESUMOS EXECUTIVOS E TEMAS
    # -------------------------------------------------------------------------
    if _flag("RUN_IA_RESUMO", padrao=True):
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
            
            # Captura falhas controladas retornadas pelo dicionário do Orqueatrador de IA
            if resumo_ia and resumo_ia.get("status") == "erro":
                raise RuntimeError(f"A camada de IA falhou internamente: {resumo_ia.get('motivo')}")
            
            dur_stage = time.time() - inicio_stage
            log.info(f"OK          -> Etapa 4 e 5 - IA concluída ({dur_stage:.1f}s)")
        except Exception as e:
            log.error(f"FALHOU      -> Etapa 4 e 5 - IA: {e}")
            log.info("=" * 70)
            log.info("PIPELINE INTERROMPIDO na etapa: Etapa 4 e 5 - IA: Resumos e Temas.")
            log.info("O n8n deve disparar o ALERTA DE FALHA.")
            return 1
    else:
        log.info("\n[Ignorado] Etapa 4 e 5 - IA desabilitada via RUN_IA_RESUMO.")

    dur_total = time.time() - inicio_total
    log.info("=" * 70)
    log.info(f"PIPELINE CONCLUIDO COM SUCESSO em {dur_total:.1f}s. Todas as etapas OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())