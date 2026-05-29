import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Importa o Pipeline unificado da pasta src
from src.transformation import PipelineEtapa3

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
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
        logging.FileHandler(f"logs/transformacao_{DATA_STR}.log", encoding="utf-8"),
    ]
)

logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.ERROR)

log = logging.getLogger(__name__)

if __name__ == "__main__":
    if not DATABASE_URL:
        log.error("DATABASE_URL não encontrada! Configure o arquivo .env")
        exit(1)

    pipeline = PipelineEtapa3(
        raw_dir=RAW_DIR,
        database_url=DATABASE_URL
    )
    pipeline.executar()