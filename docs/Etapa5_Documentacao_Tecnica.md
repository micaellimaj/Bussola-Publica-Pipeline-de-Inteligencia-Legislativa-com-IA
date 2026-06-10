# Etapa 5 — Automação e Monitoramento · Documentação Técnica

Bússola Pública — Pipeline de Inteligência Legislativa com IA
Projeto Integrador · Pós Tech Engenharia de Dados e IA

---

## 1. Visão geral

A Etapa 5 fecha o pipeline: o que era um conjunto de scripts rodados à mão passa a rodar **sozinho todo dia às 06h** via n8n, com notificação automática por e-mail. Junto, esta entrega habilita a **classificação temática por embeddings** (Caminho A da Etapa 4), porque o alerta/digest só tem valor de negócio se o **tema for um dado real** na base — e não palavra-chave solta.

O diagrama completo está em [`diagrama_pipeline.svg`](./diagrama_pipeline.svg).

```
API Câmara → [1] Extração → [2] Transformação → [3] Carga (Supabase)
                                                      ↓
                                          [4] Camada de IA
                                       (resumo GPT + tema embeddings)
                                                      ↓
                                      [5] n8n 06h → e-mail digest / alerta
```

## 2. Componentes entregues nesta etapa

| Arquivo | Papel |
|---|---|
| `src/classificacao_tematica.py` | Classifica proposições por tema (embeddings + cosseno) e grava `tema`, `tema_score`, `data_tema` em `fato_proposicoes`. |
| `n8n/bussola_publica_ingestao_diaria.json` | Workflow n8n importável: agenda 06h → roda `main.py` → consulta o dia → e-mail. |
| `n8n/GUIA_IMPORTACAO_n8n.md` | Passo a passo de import, credenciais e teste. |
| `docs/diagrama_pipeline.svg` | Diagrama do pipeline ponta a ponta. |
| `docs/modelo_dados.md` | Modelo físico das tabelas (fato/dimensão) + colunas de IA. |
| `requirements.txt` | Bibliotecas usadas (espelho do `pyproject.toml`, para avaliadores sem Poetry). |
| `GIT_GUIA_COMMITS.md` | Sequência sugerida de commits descritivos. |
| `apresentacao/Bussola_Publica_Pitch.pptx` | Pitch executivo (6 slides). |

## 3. Decisões técnicas e o porquê

**Por que orquestrar `main.py` no n8n (Execute Command) em vez de reimplementar a ingestão em nós nativos?**
A lógica de paginação, retry, validação e carga já está testada em Python. Reescrevê-la em nós HTTP do n8n duplicaria código e criaria duas fontes de verdade. O n8n entra como **orquestrador e camada de notificação**, não como ETL paralelo. O custo dessa escolha é que o n8n precisa rodar no mesmo host do repositório (VPS/Docker/local self-hosted) — documentado no guia.

**Por que classificação por embeddings (Caminho A) e não pedir o tema direto à LLM?**
Três motivos: (1) **custo** — 1 embedding por ementa com `text-embedding-3-small` custa frações de centavo, muito abaixo de uma chamada de chat por proposição; (2) **consistência** — a lista de ~11 temas é um catálogo fechado, então a similaridade de cosseno sempre escolhe um rótulo válido, enquanto a LLM poderia inventar categorias novas; (3) **auditabilidade** — guardamos o `tema_score`, deixando a classificação transparente e com limiar ajustável (`LIMIAR_TEMA`).

**Por que e-mail e não Telegram (nesta entrega)?**
E-mail é o canal mais simples de configurar, demonstrar e printar para a avaliação, e é o formato que o cliente corporativo da Bússola Pública já consome. O workflow é trivialmente extensível para Telegram (basta um nó `Telegram` em paralelo ao e-mail de sucesso).

**Por que o digest mostra tema + resumo?**
Para a IA não ser decoração. O e-mail das 06h traz, para cada proposição priorizada, **o tema (embeddings)** e **o resumo executivo (GPT)**. A IA aparece no produto final que chega ao cliente — exatamente o que o desafio cobra.

**Controle de custo de IA.**
Tanto `ai_layer.py` (resumo) quanto `classificacao_tematica.py` (tema) sobem em `DRY_RUN=true` por padrão: estimam tokens e custo (USD/BRL) **antes** de gastar. Só com `DRY_RUN=false` há chamada real e gravação. Processamento é idempotente — pula o que já tem `resumo_executivo`/`tema`.

## 4. Prompts e parâmetros da camada de IA

### 4.1 Resumo executivo (Caminho B — `ai_layer.py`)

System prompt (perfil de analista) + user prompt com a ementa. Regras: máximo 3 frases, sem jargão, estrutura (1) o que propõe, (2) quem é impactado, (3) ponto de atenção para empresas. Modelo `gpt-4o-mini`, `temperature=0.3`, `max_tokens=300`, `timeout=30`.

### 4.2 Classificação temática (Caminho A — `classificacao_tematica.py`)

Não usa prompt de chat: usa **embeddings**. Para cada tema do catálogo, uma frase-descrição rica é embedada uma única vez; cada ementa é embedada e comparada por **similaridade de cosseno**. O tema de maior score vence; abaixo de `LIMIAR_TEMA` (0,20) cai em "Outros".

Catálogo de temas: Tecnologia e IA · Tributário · Saúde · Trabalho e Previdência · Meio Ambiente · Economia e Finanças · Educação · Segurança Pública · Agronegócio · Infraestrutura e Transporte · Direitos e Cidadania.

Custo de referência (mai/2025): `text-embedding-3-small` ≈ US$ 0,02 / 1M tokens. Para ~120 tokens por ementa, classificar 1.000 proposições custa da ordem de US$ 0,002 (poucos centavos de real).

## 5. Como rodar a Etapa 5 ponta a ponta

```bash
# 1. Ingestão + carga (Etapas 2 e 3)
poetry run python main.py

# 2. Camada de IA — primeiro estimar custo (DRY_RUN padrão = true)
poetry run python -m src.ai_layer
poetry run python -m src.classificacao_tematica

# 3. Rodar a IA de verdade depois de conferir o custo
DRY_RUN=false poetry run python -m src.ai_layer
DRY_RUN=false poetry run python -m src.classificacao_tematica

# 4. Automação: importar o workflow no n8n (ver n8n/GUIA_IMPORTACAO_n8n.md),
#    configurar credenciais Postgres + SMTP, testar e ativar.
```

## 6. Variáveis de ambiente novas (adicionar ao `.env`)

```
# Classificação temática (Caminho A)
MODELO_EMBEDDING=text-embedding-3-small
LIMIAR_TEMA=0.20
# DRY_RUN e BATCH_SIZE já existem e são reutilizados
```

## 7. Critérios de avaliação atendidos

- **Funcionamento:** pipeline roda do início ao fim (extração → carga → IA → notificação).
- **Modelagem:** modelo estrela preservado; IA adiciona colunas, não quebra o schema.
- **IA aplicada:** tema (embeddings) e resumo (GPT) chegam ao e-mail do cliente — não é decoração.
- **Automação:** workflow n8n agendado, com sucesso e falha tratados.
- **Comunicação:** diagrama, doc técnica, prompts e pitch executivo.
