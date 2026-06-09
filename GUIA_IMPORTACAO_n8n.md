# Guia de importação do workflow n8n — Bússola Pública

Workflow: **`bussola_publica_ingestao_diaria.json`**
Objetivo da Etapa 5: rodar o pipeline automaticamente **todo dia às 06h** e notificar o time por e-mail, sem ninguém olhando.

## O que o workflow faz

```
[Agendamento 06h]  →  [Rodar Pipeline (main.py)]  →  [Pipeline OK?]
                                                         ├─ SIM → [Consultar Proposições do Dia] → [Montar Digest HTML] → [Enviar Digest]
                                                         └─ NÃO → [Alerta de Falha]
```

1. **Agendamento 06h (Schedule Trigger):** cron `0 6 * * *`, timezone `America/Sao_Paulo`.
2. **Rodar Pipeline (Execute Command):** executa `poetry run python main.py` no servidor (ingestão incremental + carga no Supabase).
3. **Pipeline OK? (IF):** checa o `exitCode`. Zero = sucesso.
4. **Consultar Proposições do Dia (Postgres):** lê as 5 proposições das últimas 24h com **tema (embeddings)** e **resumo (GPT)** — a IA aparece no produto.
5. **Montar Digest / Enviar Digest (Email):** monta o HTML e envia o radar diário.
6. **Alerta de Falha (Email):** se o pipeline quebrar, avisa na hora com o `stderr`.

## Passo a passo da importação

1. Abra o n8n → menu **⋯ (canto superior direito)** → **Import from File**.
2. Selecione `bussola_publica_ingestao_diaria.json`.
3. Configure as **credenciais** (os campos vêm com placeholders):
   - **Postgres / Supabase:** crie a credencial *Postgres* com Host, Database, User, Password e Porta do Supabase (Settings → Database → Connection info). Marque SSL.
   - **SMTP:** crie a credencial *SMTP* (Gmail: `smtp.gmail.com`, porta 465 SSL, App Password). Vincule aos dois nós de e-mail.
4. No nó **Rodar Pipeline**, ajuste o caminho `cd /opt/bussola-publica` para a pasta real do repositório no servidor onde o n8n roda.
5. Ajuste os destinatários nos nós de e-mail (`toEmail`).
6. Clique em **Execute Workflow** para um teste manual (captura o print pedido na entrega) e depois **ative** o workflow (toggle *Active*).

## Encadear a camada de IA (opcional, recomendado)

Para que o tema e o resumo já saiam atualizados no digest do dia, troque o comando do nó **Rodar Pipeline** por:

```bash
cd /opt/bussola-publica && poetry run python main.py \
  && DRY_RUN=false poetry run python -m src.ai_layer \
  && DRY_RUN=false poetry run python -m src.classificacao_tematica 2>&1
```

> ⚠️ Rode a camada de IA primeiro em `DRY_RUN=true` para conferir o custo estimado antes de ativar em produção (orientação do desafio: teste com 10, calcule, decida).

## Print da execução (entregável)

Após o teste manual bem-sucedido, salve um print da tela de execução do n8n (com os nós verdes) em `../prints/n8n_execucao_sucesso.png`. Esse print é um dos entregáveis obrigatórios da Etapa 5.

## Alternativa sem servidor dedicado

Se você não tiver um servidor onde o repo está clonado, há duas opções:

- **n8n + Execute Command** exige que o n8n esteja no mesmo host do projeto (VPS, Docker, máquina local com n8n self-hosted). É a opção deste workflow.
- **n8n puro (sem Execute Command):** dá para reimplementar a ingestão com nós nativos — *HTTP Request* (API da Câmara, com paginação via loop) → *Postgres* (insert). Funciona no n8n Cloud, mas duplica a lógica que já existe em Python. Por isso optamos por orquestrar o `main.py` existente.
