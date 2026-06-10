# Rodar o n8n na sua máquina (Windows) — passo a passo

Esta configuração sobe o n8n localmente com **Python + Poetry dentro do container**, então o nó *Execute Command* consegue rodar o pipeline (`main.py`). Você só precisa do **Docker Desktop**. É o **n8n Community (self-hosted), gratuito e ilimitado** — não precisa de conta paga.

Arquivos usados (pasta `docker/`): `Dockerfile`, `docker-compose.yml`, `.env.example`.

---

## ⚡ Caminho rápido (2 scripts)

Se quiser o atalho, use os scripts da pasta `scripts/` em vez de fazer manualmente:

1. **Instalar o Docker:** clique com o botão direito em `scripts/1_instalar_docker.ps1` → **Executar com o PowerShell** (como Administrador). Depois reinicie se pedir, abra o **Docker Desktop** e aceite os termos (1 vez).
2. **Subir o n8n:** com o Docker rodando, clique com o botão direito em `scripts/2_subir_n8n.ps1` → **Executar com o PowerShell**. Ele gera a chave, acha o repositório, builda, instala as dependências e **abre o navegador** em http://localhost:5678.

> Se o Windows bloquear o script, abra o PowerShell e rode:
> `powershell -ExecutionPolicy Bypass -File .\scripts\2_subir_n8n.ps1`

Depois disso, pule direto para o **Passo 5 (Importar o workflow)** abaixo.

> ℹ️ **Primeiro acesso:** versões recentes do n8n pedem para **criar uma conta de dono** (e-mail + senha) na primeira tela, em vez do login básico. É local, fica só na sua máquina — preencha e siga.

---

## Caminho manual (passo a passo detalhado)

---

## Pré-requisito: Docker Desktop

1. Baixe e instale o **Docker Desktop for Windows**: https://www.docker.com/products/docker-desktop/
2. Abra o Docker Desktop e espere ficar **"Running"** (ícone da baleia verde).
3. Teste no PowerShell:
   ```powershell
   docker --version
   docker compose version
   ```

---

## Passo 1 — Ajustar o caminho do seu repositório

No arquivo `docker/docker-compose.yml`, encontre esta linha (seção `volumes`):

```yaml
- "C:/Users/marlon.vargas/OneDrive/Área de Trabalho/Marlon/Pós Tech/Bussola-Publica:/opt/bussola-publica"
```

Troque a parte **antes do `:`** pelo caminho real onde está o seu repositório clonado (a pasta que tem o `main.py` e o `pyproject.toml`). Use **barras normais `/`**. A parte depois do `:` (`/opt/bussola-publica`) **não muda** — é o que o workflow espera.

> Dica: se ainda não clonou o repo, faça `git clone` numa pasta e use esse caminho.

---

## Passo 2 — Criar o arquivo .env do n8n

No PowerShell, entre na pasta `docker/` e copie o exemplo:

```powershell
cd "C:\Users\marlon.vargas\OneDrive\Área de Trabalho\Marlon\Pós Tech\Desafio_Data_Challenges\Etapa5_Automacao_e_IA\docker"
Copy-Item .env.example .env
```

Abra o `.env` e preencha:
- `N8N_USER` / `N8N_PASSWORD` — login para abrir o n8n.
- `N8N_ENCRYPTION_KEY` — uma chave aleatória longa. Gere uma com:
  ```powershell
  python -c "import secrets; print(secrets.token_hex(24))"
  ```
  Cole o resultado. **Não mude essa chave depois** de criar credenciais.

---

## Passo 3 — Subir o n8n

Ainda na pasta `docker/`:

```powershell
docker compose up -d --build
```

A primeira vez demora (baixa a imagem e instala Python/Poetry). Acompanhe:

```powershell
docker compose logs -f n8n
```

Quando aparecer `Editor is now accessible via http://localhost:5678`, abra no navegador: **http://localhost:5678** e faça login com o usuário/senha do `.env`.

---

## Passo 4 — Instalar as dependências do projeto (uma vez)

O pipeline precisa das libs instaladas pelo Poetry dentro do container. Rode uma vez:

```powershell
docker compose exec n8n sh -c "cd /opt/bussola-publica && poetry install --no-root"
```

> Isso cria o `.venv` dentro do repo (fica salvo, não precisa repetir a cada execução).

Confira se o `.env` **do projeto** (com `DATABASE_URL` e `OPENAI_API_KEY`) existe na raiz do repo — ele é lido pelo `main.py`. Como o repo está montado, o mesmo `.env` vale dentro do container.

---

## Passo 5 — Importar o workflow

1. No n8n (http://localhost:5678) → menu **⋯** (canto superior direito) → **Import from File**.
2. Selecione `n8n/bussola_publica_ingestao_diaria.json`.
3. O workflow abre no canvas com os 7 nós.

---

## Passo 6 — Configurar as credenciais

No canvas, os nós que pedem credencial mostram um aviso. Crie duas credenciais:

**Postgres (Supabase):** clique no nó *Consultar Proposições do Dia* → Credential → *Create New*:
- Host: `db.<seu-projeto>.supabase.co` (Supabase → Settings → Database → Connection info)
- Database: `postgres`
- User: `postgres`
- Password: a senha do banco
- Port: `5432`
- SSL: ligado (`require`)

**SMTP (e-mail):** clique no nó *Enviar Digest (Sucesso)* → Credential → *Create New* (ex. Gmail):
- Host: `smtp.gmail.com`, Port: `465`, SSL ligado
- User: seu e-mail
- Password: uma **App Password** do Google (não a senha normal)
- Vincule a mesma credencial no nó *Alerta de Falha*.

Ajuste também o `toEmail` dos nós de e-mail para o destinatário desejado.

---

## Passo 7 — Testar

1. Clique em **Execute Workflow** (canto superior direito) para um teste manual.
2. Se tudo estiver certo, os nós ficam **verdes** e você recebe o e-mail digest.
3. Tire o print dessa tela → salve em `prints/n8n_execucao_sucesso.png` (entregável).
4. Por fim, **ative** o workflow (toggle *Active*) para ele rodar sozinho às 06h.

---

## Comandos úteis

```powershell
docker compose up -d            # ligar
docker compose down             # desligar (mantém dados)
docker compose logs -f n8n      # ver logs
docker compose exec n8n sh      # abrir um terminal dentro do container
# rodar o pipeline manualmente (mesmo comando do workflow):
docker compose exec n8n sh -c "cd /opt/bussola-publica && poetry run python main.py"
```

---

## Problemas comuns

- **"Execute Command" não roda / comando não encontrado:** confirme que subiu com `--build` (para incluir Python/Poetry) e que rodou o `poetry install` do Passo 4.
- **Pipeline não acha o `.env`:** ele precisa estar na raiz do repo que você montou no Passo 1.
- **Cron não dispara no horário certo:** confirme `TZ=America/Sao_Paulo` (já está no compose) e que o workflow está **Active**.
- **Caminho com acento/espaço no volume:** mantenha as aspas na linha do volume (já estão no arquivo).
- **Porta 5678 ocupada:** troque para `"5679:5678"` no compose e acesse `http://localhost:5679`.

---

## Alternativa sem Docker (mais leve, exige Node.js)

Se preferir não usar Docker e já tem **Node.js 18+** e **Poetry** instalados no Windows:

```powershell
npx n8n
```

Abre o n8n em http://localhost:5678. Como roda direto no host, o *Execute Command* chama o Poetry da sua máquina — nesse caso, no nó *Rodar Pipeline* troque o comando para o caminho Windows do repo, por exemplo:
```
cd "C:\caminho\para\Bussola-Publica" && poetry run python main.py
```
O Docker é o caminho recomendado por ser reproduzível e isolado.
