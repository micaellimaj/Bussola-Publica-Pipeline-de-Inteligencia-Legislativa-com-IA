# =============================================================================
# Bussola Publica - imagem n8n + Python + Poetry (base Debian)
# -----------------------------------------------------------------------------
# Por que NAO usamos a imagem oficial do n8n como base?
# A imagem oficial 'n8nio/n8n:latest' virou uma "Docker Hardened Image": e
# blindada, sem gerenciador de pacotes (apk/apt) e sem Python. Logo, e
# impossivel instalar Python nela para o no "Execute Command".
#
# Solucao: partimos de uma base Debian (node:20-bookworm-slim), que tem apt, e
# instalamos n8n (via npm) + Python + Poetry no MESMO container. Em Debian
# (glibc), pandas/psycopg2 instalam por wheels prontos, sem compilar.
# =============================================================================
FROM node:20-bookworm-slim

USER root

# Python, pip, venv, git e ferramentas de build (para deps nativas do n8n).
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv python3-dev \
        git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry (PEP 668: --break-system-packages no pip do Debian 12)
RUN python3 -m pip install --no-cache-dir --break-system-packages poetry \
    && poetry --version

# Instala o n8n globalmente via npm.
RUN npm install -g n8n \
    && n8n --version

# Configuracoes:
#  - venv do Poetry dentro do projeto (.venv), cacheavel.
#  - N8N_USER_FOLDER aponta para /home/node, casando com o volume n8n_data
#    montado em /home/node/.n8n no docker-compose.
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    N8N_USER_FOLDER=/home/node \
    N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=false

# Garante a pasta de dados do n8n com dono correto.
RUN mkdir -p /home/node/.n8n && chown -R node:node /home/node

EXPOSE 5678

# Roda o n8n como usuario sem privilegios (boa pratica).
USER node

CMD ["n8n"]
