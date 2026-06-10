# Guia de Git — subir o projeto para o GitHub

> Nada aqui mexe no seu GitHub automaticamente. **Você** roda os comandos quando
> quiser. O desafio costuma penalizar "commit único", então a sugestão é fazer
> commits pequenos, um por etapa.

## 0. Antes de tudo — checklist de segurança

- [ ] O `.env` (com `DATABASE_URL` e `OPENAI_API_KEY` reais) **não** será enviado —
      ele está no `.gitignore`. Confirme com `git status` (não pode aparecer).
- [ ] O `05_automacao_ia/docker/.env` também está protegido pelo `.gitignore`.
- [ ] O workflow do n8n usa placeholders (`REPLACE_*`), sem credenciais reais.
- [ ] A pasta `data/` (JSONs/CSVs gerados) e `.venv/` estão ignoradas.

> Recomendação: como senha do banco e chave da OpenAI já apareceram em prints
> durante o setup, **troque a senha do Supabase e gere uma nova OpenAI API key**
> antes de tornar o reppositório público.

## 1. Iniciar o repositório (uma vez)

Na raiz do projeto (`Desafio_Data_Challenges`):

```bash
git init
git add .gitignore
git commit -m "chore: estrutura inicial e .gitignore"
```

Confirme que o `.env` NÃO está sendo rastreado:

```bash
git status            # .env nao pode aparecer em "Changes to be committed"
```

## 2. Commits por etapa (sugestão)

```bash
# Base do projeto
git add README.md pyproject.toml requirements.txt .env.example main.py
git commit -m "docs+chore: README, dependencias e orquestrador main.py"

# Etapa 1 - Exploracao
git add 01_exploracao/
git commit -m "feat(etapa1): exploracao da API da Camara"

# Etapa 2 - Extracao
git add 02_extracao/
git commit -m "feat(etapa2): extracao com paginacao, timeout e salvamento do JSON bruto"

# Etapa 3 - Transformacao e Carga
git add 03_transformacao/
git commit -m "feat(etapa3): transformacao, validacao e carga no PostgreSQL (modelo estrela)"

# Etapa 4 - Camada de IA
git add 04_camada_ia/
git commit -m "feat(etapa4): camada de IA - resumo executivo com GPT (+docs e diagnostico)"

# Etapa 5 - Automacao e IA
git add 05_automacao_ia/
git commit -m "feat(etapa5): classificacao tematica (embeddings), workflow n8n, docker e docs"
```

## 3. Conectar ao GitHub e enviar

Crie um repositório vazio no GitHub (pelo site), copie a URL e:

```bash
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

## 4. Depois de testar o n8n (prints)

```bash
git add 05_automacao_ia/prints/
git commit -m "docs: prints de execucao do n8n, digest por e-mail e tema no Supabase"
git push
```

## Dica
Se algum arquivo grande/desnecessário entrar por engano:

```bash
git rm --cached caminho/do/arquivo     # remove do versionamento, mantém no disco
```
