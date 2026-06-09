#!/usr/bin/env python3
# =============================================================================
# Bussola Publica - Orquestrador do pipeline (Etapa 5)
# -----------------------------------------------------------------------------
# Ponto de entrada chamado pelo no "Rodar Pipeline (main.py)" do workflow n8n:
#       cd /opt/bussola-publica && poetry run python main.py 2>&1
#
# Executa as etapas do desafio NA ORDEM e propaga o resultado pelo exit code:
#   - exit 0  -> n8n segue para o ramo de SUCESSO (digest por e-mail)
#   - exit !=0 -> n8n segue para o ramo de FALHA  (alerta por e-mail)
#
# Cada etapa e um script ja existente, rodado como subprocesso isolado.
#
# Controle por variaveis de ambiente (todas opcionais):
#   RUN_EXTRACT, RUN_TRANSFORM, RUN_IA_RESUMO, RUN_IA_TEMA = true|false (default true)
#   CHECK_ONLY = true   -> apenas valida que os scripts existem e sai 0
# As etapas de IA respeitam o DRY_RUN do .env (true = so estima custo, nao gasta).
# =============================================================================

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Raiz do repositorio = pasta onde este main.py esta.
ROOT = Path(__file__).resolve().parent


def _flag(nome: str, padrao: bool = True) -> bool:
    """Le uma variavel de ambiente booleana (true/false)."""
    return os.getenv(nome, "true" if padrao else "false").strip().lower() == "true"


# Plano de execucao: (rotulo, caminho relativo do script, flag de ativacao)
# Caminhos seguem a organizacao por etapa do repositorio.
STAGES = [
    ("Etapa 2 - Extracao (API Camara)",        "02_extracao/extracao.py",                      "RUN_EXTRACT"),
    ("Etapa 3 - Transformacao + Carga",        "03_transformacao/transformacao.py",            "RUN_TRANSFORM"),
    ("Etapa 4 - IA: Resumo executivo (GPT)",   "04_camada_ia/ia_resumo.py",                    "RUN_IA_RESUMO"),
    ("Etapa 5 - IA: Classificacao tematica",   "05_automacao_ia/src/classificacao_tematica.py","RUN_IA_TEMA"),
]


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def stages_ativos():
    """Retorna a lista de etapas habilitadas pelas flags de ambiente."""
    ativos = []
    for rotulo, rel, flag in STAGES:
        if _flag(flag, padrao=True):
            ativos.append((rotulo, rel, flag))
    return ativos


def validar_existencia(ativos) -> list:
    """Verifica se os scripts das etapas habilitadas existem. Retorna faltantes."""
    faltando = []
    for rotulo, rel, _flag_name in ativos:
        if not (ROOT / rel).is_file():
            faltando.append(rel)
    return faltando


def rodar_stage(rotulo: str, rel: str) -> int:
    """Roda um script como subprocesso. Retorna o exit code."""
    script = ROOT / rel
    log("-" * 70)
    log(f"INICIANDO  -> {rotulo}")
    log(f"            ({rel})")
    inicio = time.time()
    # Usa o mesmo interpretador Python e roda a partir da raiz do repo,
    # para que caminhos relativos como 'data/raw' resolvam corretamente.
    proc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    dur = time.time() - inicio
    if proc.returncode == 0:
        log(f"OK         -> {rotulo}  ({dur:.1f}s)")
    else:
        log(f"FALHOU     -> {rotulo}  (exit {proc.returncode}, {dur:.1f}s)")
    return proc.returncode


def main() -> int:
    log("=" * 70)
    log("BUSSOLA PUBLICA - Orquestrador do pipeline (Etapa 5)")
    log(f"Raiz do projeto: {ROOT}")
    dry = os.getenv("DRY_RUN", "true").strip().lower() == "true"
    log(f"DRY_RUN da IA: {dry}  (true = IA so estima custo, nao gasta)")

    ativos = stages_ativos()
    log("Etapas habilitadas:")
    for rotulo, rel, _f in ativos:
        log(f"  - {rotulo}")

    # Confere que todos os scripts existem antes de comecar.
    faltando = validar_existencia(ativos)
    if faltando:
        log("ERRO: scripts nao encontrados:")
        for rel in faltando:
            log(f"  -> {rel}")
        return 1

    # Modo verificacao: nao roda nada, so confirma o plano.
    if os.getenv("CHECK_ONLY", "false").strip().lower() == "true":
        log("CHECK_ONLY=true -> plano validado, scripts presentes. Saindo (0).")
        return 0

    inicio_total = time.time()
    for rotulo, rel, _f in ativos:
        rc = rodar_stage(rotulo, rel)
        if rc != 0:
            log("=" * 70)
            log(f"PIPELINE INTERROMPIDO na etapa: {rotulo} (exit {rc}).")
            log("O n8n deve disparar o ALERTA DE FALHA.")
            return rc

    dur_total = time.time() - inicio_total
    log("=" * 70)
    log(f"PIPELINE CONCLUIDO COM SUCESSO em {dur_total:.1f}s. Todas as etapas OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
