<!-- =======================================================================
  SNIPPET PARA O README.md PRINCIPAL
  Cole este bloco substituindo a seção "5. Automação e Monitoramento [PLANEJADO]".
  (Você atualiza o GitHub manualmente — nada aqui altera o repositório.)
======================================================================= -->

5. **Automação e Monitoramento** `[CONCLUÍDO]`

- Workflow no **n8n** (`n8n/bussola_publica_ingestao_diaria.json`) agendado para **06h diariamente** (cron `0 6 * * *`), executando o pipeline principal (`main.py`) via *Execute Command* sobre o ambiente Poetry.
- **Notificação automática por e-mail** com o digest do dia: as 5 proposições mais relevantes das últimas 24h, já com **tema (embeddings)** e **resumo executivo (GPT)** — a IA chega ao produto final.
- **Tratamento de falha:** ramo dedicado que dispara e-mail de alerta com o `stderr` caso o pipeline quebre, sem depender da memória do analista.
- **Classificação temática por embeddings** (`src/classificacao_tematica.py`): `text-embedding-3-small` + similaridade de cosseno gravam `tema`, `tema_score` e `data_tema` em `fato_proposicoes`, habilitando filtros e alertas por tema.

### Como ativar a automação

```bash
# Pipeline + IA (estimar custo antes; DRY_RUN padrão = true)
poetry run python main.py
poetry run python -m src.ai_layer
poetry run python -m src.classificacao_tematica
# Rodar IA de verdade:
DRY_RUN=false poetry run python -m src.ai_layer
DRY_RUN=false poetry run python -m src.classificacao_tematica
```

Importe o workflow no n8n e configure as credenciais Postgres (Supabase) e SMTP — passo a passo em [`n8n/GUIA_IMPORTACAO_n8n.md`](n8n/GUIA_IMPORTACAO_n8n.md). Documentação técnica completa em [`docs/Etapa5_Documentacao_Tecnica.md`](docs/Etapa5_Documentacao_Tecnica.md).

<!-- Sugestão: adicionar prints em readme/ ou prints/ -->
<!-- ![n8n execução](prints/n8n_execucao_sucesso.png) -->
<!-- ![e-mail digest](prints/email_digest.png) -->
<!-- ![tabela com tema no Supabase](prints/supabase_tema.png) -->
