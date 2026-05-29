import os
import logging
from datetime import datetime, timedelta

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}
ITENS_PAG = 100
MAX_TENTATIVAS = 3
ESPERA_RETRY = 5

# Janela de 30 dias para filtrar proposições e votações
HOJE = datetime.today()
INICIO = (HOJE - timedelta(days=30)).strftime("%Y-%m-%d")
FIM = HOJE.strftime("%Y-%m-%d")
DATA = HOJE.strftime("%Y%m%d")  # sufixo YYYYMMDD para arquivos

def configurar_logging():
    """Centraliza a configuração de logs para todo o sistema."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/extracao_{DATA}.log", encoding="utf-8"),
        ]
    )
    return logging.getLogger(__name__)