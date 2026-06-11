# Bússola Pública — Pipeline de Dados Legislativos

Projeto de engenharia de dados que consome a **API de Dados Abertos da Câmara dos
Deputados**, organiza as informações num data warehouse (Supabase/PostgreSQL,
modelo estrela), enriquece as proposições com **IA generativa** (resumo executivo
e classificação temática) e **automatiza** a ingestão diária com notificação por
e-mail via n8n.

Desenvolvido como desafio prático (*Data Challenges*) do MBA em BI & Analytics /
Pós Tech, em 5 etapas — cada uma em sua própria pasta.

---

## Fluxo do pipeline

```
API Câmara dos Deputados
        │  (Etapa 1: exploração da API)
        ▼
   Extração (Etapa 2)  ──►  JSON bruto em data/raw/
        │
        ▼
Transformação + Carga (Etapa 3)  ──►  Supabase/PostgreSQL (modelo estrela)
        │
        ▼
  Camada de IA (Etapa 4)  ──►  resumo executivo (GPT) gravado nas proposições
        │
        ▼
Automação + IA (Etapa 5)  ──►  classificação temática (embeddings) +
                                 workflow n8n diário (digest e alerta por e-mail)
```

---

## Estrutura do repositório

| Pasta / arquivo | Etapa | O que contém | Entregável |
|---|---|---|---|
| `01_exploracao/` | 1 — Exploração | `exploracao.py`: inspeção dos endpoints da API (`type`, `len`, amostras) | Script de exploração |
| `02_extracao/` | 2 — Extração | `extracao.py`: extratores OOP com paginação, timeout e salvamento do JSON bruto | Script de extração |
| `03_transformacao/` | 3 — Transformação + Carga | `transformacao.py`: limpeza, validação e carga no PostgreSQL (modelo estrela) | Script de transformação/carga |
| `04_camada_ia/` | 4 — Camada de IA | `ia_resumo.py` (resumo GPT), `classificacao`/diagnóstico, `Etapa4_Camada_IA.pdf/.docx` | Script de IA + documento da etapa |
| `05_automacao_ia/` | 5 — Automação + IA | n8n, Docker, classificação temática (embeddings), documentação técnica, pitch, prints | Workflow, docs e apresentação |
| `main.py` | 5 (orquestrador) | Executa as etapas 2 → 3 → 4 → tema em ordem; usado pelo nó *Execute Command* do n8n | Orquestrador |
| `pyproject.toml` / `requirements.txt` | — | Dependências (Poetry e espelho em pip) | Configuração |
| `.env.example` | — | Modelo das variáveis de ambiente (sem segredos) | Configuração |

Detalhe da Etapa 5 (`05_automacao_ia/`):

```
05_automacao_ia/
├── src/classificacao_tematica.py     # IA: tema por embeddings (text-embedding-3-small)
├── n8n/                              # workflow + guia de importação
├── docker/                          # Dockerfile + docker-compose + .env.example
├── scripts/                         # instalar Docker / subir n8n (PowerShell)
├── docs/                            # documentação técnica, modelo de dados, diagrama
├── apresentacao/                    # pitch executivo (.pptx)
├── prints/                          # capturas de tela (entregáveis)
├── COMECE_AQUI_n8n.md               # passo a passo para rodar o n8n
└── SETUP_n8n_WINDOWS.md             # setup detalhado no Windows
```

---

## Modelo de dados (Supabase / PostgreSQL)

Modelo estrela com dimensões e fatos:

- `dim_deputados`, `dim_partidos`
- `fato_proposicoes` (recebe também `resumo_executivo`, `tema`, `tema_score` da IA)
- `fato_proposicoes_autores`
- `fato_votacoes`, `fato_votos`

Detalhes em [`05_automacao_ia/docs/modelo_dados.md`](05_automacao_ia/docs/modelo_dados.md).

---

## Como executar

### 1. Pré-requisitos
- Python 3.11+
- Conta no Supabase (PostgreSQL) e uma chave da OpenAI
- Opcional: Poetry (ou use `pip install -r requirements.txt`)

### 2. Configurar variáveis de ambiente
Copie o modelo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Variáveis principais: `DATABASE_URL`, `OPENAI_API_KEY`, `DRY_RUN`, `BATCH_SIZE`,
`MODELO_IA`, `MODELO_EMBEDDING`.

### 3. Instalar dependências
```bash
poetry install --no-root      # ou: pip install -r requirements.txt
```

### 4. Rodar etapa por etapa
```bash
python 02_extracao/extracao.py            # extrai e salva JSON bruto
python 03_transformacao/transformacao.py  # transforma e carrega no banco
python 04_camada_ia/ia_resumo.py          # resumo executivo (respeita DRY_RUN)
python 05_automacao_ia/src/classificacao_tematica.py  # tema por embeddings
```

> A camada de IA roda em `DRY_RUN=true` por padrão (só estima o custo, não gasta).
> Defina `DRY_RUN=false` no `.env` quando quiser executar de verdade.

### 5. Rodar o pipeline completo (orquestrado)
```bash
python main.py
```

`main.py` executa as etapas 2 → 3 → 4 → tema e propaga o resultado pelo código de
saída (usado pelo n8n para decidir entre digest de sucesso e alerta de falha).

---

## Etapa 5 — Automação e Monitoramento

- Workflow no **n8n** (`05_automacao_ia/n8n/bussola_publica_ingestao_diaria.json`)
  agendado para **06h diariamente** (cron `0 6 * * *`), executando o `main.py` via
  *Execute Command*.
- **Digest diário por e-mail** com as 5 proposições mais relevantes das últimas 24h,
  já com **tema (embeddings)** e **resumo executivo (GPT)**.
- **Alerta de falha**: ramo dedicado que envia e-mail com o `stderr` caso o pipeline
  quebre.
- Para subir o n8n localmente, veja [`05_automacao_ia/COMECE_AQUI_n8n.md`](05_automacao_ia/COMECE_AQUI_n8n.md).

---

## Stack

Python · pandas · SQLAlchemy · psycopg2 · requests · OpenAI (GPT + embeddings) ·
PostgreSQL (Supabase) · n8n · Docker · Poetry.

---

## Segurança

- O arquivo `.env` (com `DATABASE_URL` e `OPENAI_API_KEY` reais) **não é versionado**
  — está no `.gitignore`. Use sempre o `.env.example` como modelo.
- O workflow do n8n usa **placeholders** de credencial; as credenciais reais ficam
  apenas na sua instância local do n8n.
