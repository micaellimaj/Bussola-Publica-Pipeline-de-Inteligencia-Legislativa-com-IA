# main.py
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importações dos seus extratores (Etapa 1)
from src.extraction import (
    DeputadosExtractor,
    PartidosExtractor,
    ProposicoesExtractor,
    VotacoesExtractor
)

# Importação do seu orquestrador de carga (Etapa 3)
from src.transformation import PipelineEtapa3

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
    
    # O transformador espera uma chave "dados" contendo a lista de itens
    conteudo = {"dados": dados} if isinstance(dados, list) else dados

    with open(caminho_completo, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=4)
    
    log.info(f"  [Arquivo] Dados salvos brutos em: {caminho_completo}")


def rodar_pipeline_completo():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    raw_dir = "data/raw"
    
    log.info("==================================================")
    log.info("INICIANDO PIPELINE COMPLETO - BÚSSOLA PÚBLICA")
    log.info("==================================================")

    # -------------------------------------------------------------------------
    # ETAPA 1: EXTRAÇÃO DA API DA CÂMARA
    # -------------------------------------------------------------------------
    log.info("\n>>> ETAPA 1: EXTRAÇÃO DE DADOS DA API <<<")
    
    # Instanciando extratores
    api_deputados = DeputadosExtractor()
    api_partidos = PartidosExtractor()
    api_proposicoes = ProposicoesExtractor()
    api_votacoes = VotacoesExtractor()

    # Coletando e salvando fisicamente no formato esperado pelo transformador
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

    log.info("==================================================")
    log.info("PIPELINE DE EXTRACAO, TRANSFORMAÇÃO E CARGA CONCLUÍDO!")
    log.info(f"Registros inseridos no Supabase: {resumo_carga}")
    log.info("==================================================")


if __name__ == "__main__":
    rodar_pipeline_completo()