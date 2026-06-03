import os
import json
import logging
import sys
from datetime import datetime
from dotenv import load_dotenv

# Importação do validador/diagnóstico
from src.diagnostico import executar_diagnostico

# Importações dos seus extratores (Etapa 1)
from src.extraction import (
    DeputadosExtractor,
    PartidosExtractor,
    ProposicoesExtractor,
    VotacoesExtractor
)

# Importação do seu orquestrador de carga (Etapa 3)
from src.transformation import PipelineEtapa3

# NOVO IMPORT: Importação da Camada de IA (Etapa 4)
from src.ai_layer import PipelineEtapa4

# Configuração de Log global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

def salvar_json_bruto(dados, subpasta, prefixo, pasta_raiz="data/raw"):
    """Salva os dados extraídos em arquivos estruturados que o Transformador espera."""
    pasta_destino = os.path.join(pasta_raiz, subpasta)
    os.makedirs(pasta_destino, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{prefixo}_{timestamp}.json"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    conteudo = {"dados": dados} if isinstance(dados, list) else dados

    with open(caminho_completo, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=4)
    
    log.info(f"  [Arquivo] Dados salvos brutos em: {caminho_completo}")


def rodar_pipeline_completo():
    load_dotenv()
    
    # -------------------------------------------------------------------------
    # VALIDAÇÃO ANTES DA EXECUÇÃO (DIAGNÓSTICO INTEGRADO)
    # -------------------------------------------------------------------------
    if not executar_diagnostico():
        log.error("Pipeline interrompido: O diagnóstico apontou falhas críticas no ambiente.")
        sys.exit(1)

    database_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Parâmetros operacionais para a IA vindos com segurança do .env
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    batch_size = int(os.getenv("BATCH_SIZE", "10"))
    modelo_ia = os.getenv("MODELO_IA", "gpt-4o-mini")
    
    raw_dir = "data/raw"
    
    log.info("==================================================")
    log.info("INICIANDO PIPELINE COMPLETO - BÚSSOLA PÚBLICA")
    log.info("==================================================")

    # -------------------------------------------------------------------------
    # ETAPA 1: EXTRAÇÃO DA API DA CÂMARA
    # -------------------------------------------------------------------------
    log.info("\n>>> ETAPA 1: EXTRAÇÃO DE DADOS DA API <<<")
    
    api_deputados = DeputadosExtractor()
    api_partidos = PartidosExtractor()
    api_proposicoes = ProposicoesExtractor()
    api_votacoes = VotacoesExtractor()

    dados_dep = api_deputados.extrair()
    salvar_json_bruto(dados_dep, "deputados", "deputados")

    dados_part = api_partidos.extrair()
    salvar_json_bruto(dados_part, "partidos", "partidos")

    dados_prop_completos = api_proposicoes.extrair()
    salvar_json_bruto(dados_prop_completos["proposicoes"], "proposicoes", "proposicoes")
    salvar_json_bruto(dados_prop_completos["autores"], "proposicoes", "proposicoes_autores")

    dados_vot_completos = api_votacoes.extrair()
    salvar_json_bruto(dados_vot_completos["votacoes"], "votacoes", "votacoes")
    salvar_json_bruto(dados_vot_completos["votos"], "votacoes", "votos")

    log.info("\nEtapa 1 finalizada com sucesso! Todos os JSONs brutos salvos em disco.")

    # -------------------------------------------------------------------------
    # ETAPA 3: TRANSFORMAÇÃO, VALIDAÇÃO E CARGA NO POSTGRESQL (SUPABASE)
    # -------------------------------------------------------------------------
    log.info("\n>>> ETAPA 3: TRANSFORMAÇÃO E CARGA NO BANCO <<<")
    
    pipeline_etapa3 = PipelineEtapa3(raw_dir=raw_dir, database_url=database_url)
    resumo_carga = pipeline_etapa3.executar()

    log.info(f"Registros atualizados/inseridos no Supabase: {resumo_carga}")

    # -------------------------------------------------------------------------
    # ETAPA 4: CAMADA DE IA - ENRIQUECIMENTO COM RESUMOS EXECUTIVOS
    # -------------------------------------------------------------------------
    log.info("\n>>> ETAPA 4: ENRIQUECIMENTO INTELIGENTE (OPENAI IA) <<<")
    
    pipeline_etapa4 = PipelineEtapa4(
        database_url=database_url,
        openai_api_key=openai_api_key,
        modelo=modelo_ia,
        batch_size=batch_size,
        dry_run=dry_run
    )
    resumo_ia = pipeline_etapa4.executar()

    log.info("==================================================")
    log.info("PIPELINE COMPLETO DE DADOS E ENRIQUECIMENTO CONCLUÍDO!")
    log.info(f"  Métricas Finais da Execução: {resumo_ia}")
    log.info("==================================================")


if __name__ == "__main__":
    rodar_pipeline_completo()