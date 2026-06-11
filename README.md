# <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExMnZqZHNscWsxb3MzcmxkdGVuMGUxMWFwNnpodHczYWQ3eTY3OWJqMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/YnUcQkUvPdHMmkLBZn/giphy.gif" alt="dados_1" width="50" height="50" /> SQUAD: LegoDados - Projeto de Inteligência Legislativa & Engenharia de dados

![logo](readme/legodadosbanner.png)


Este repositório contém o Projeto Integrador da pós-graduação em Engenharia de Dados e Inteligência Artificial. O objetivo é desenvolver um pipeline de dados completo (ETL) que automatiza a captura, organização e análise de dados da API de Dados Abertos da Câmara dos Deputados.

## <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmVuYTBwNnoxMWt3MnE1MHduNGk1anh4a3Jyc202dW0xNm8xeGJveiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/riAbhlrWv6dSFutbOj/giphy.gif" alt="dados_2" width="30" height="30" /> Propósito do Projeto:

Transformar o [oceano de dados brutos do legislativo brasileiro](https://dadosabertos.camara.leg.br/swagger/api.html) em sinais acionáveis para consultorias de relações governamentais e empresas reguladas. O projeto visa substituir processos manuais e inconsistentes por uma arquitetura escalável que utiliza IA Generativa para classificação temática e resumos executivos.

## <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExejRkbmF2OHhtNDNnejFtcDRqaW11cTY3Z3Bubm1vbHJ5ZGp6MWtwZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/nRiEzx0joBH6JECMkD/giphy.gif" alt="dados_3" width="30" height="30" /> Stack Tecnológica:

<div align="center" style="display: inline_block">
  <img align="center" alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img align="center" alt="Poetry" src="https://img.shields.io/badge/Poetry-60A5FA?style=for-the-badge&logo=poetry&logoColor=white" />
  <img align="center" alt="Pandas" src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img align="center" alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img align="center" alt="Supabase" src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" />
  <img align="center" alt="OpenAI" src="https://img.shields.io/badge/OpenAI_GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white" />
  <img align="center" alt="n8n" src="https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white" />
</div>


## <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHdwMnFrc2V2cHM2aGltMHJ5cXcxaXlhNGJneHNkOHl3d3JpNWdqcyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9LZSPFwk4UkeVUvJRV/giphy.gif" alt="dados_4" width="30" height="30" /> Arquitetura e Funcionamento do Pipeline:

![roadmap](readme/diagrama_pipeline.svg)

O ciclo de vida dos dados e a esteira de inteligência do projeto estão estruturados em cinco etapas fundamentais e totalmente integradas:

1. **Exploração e Extração (Ingestão)**

* Desenvolvimento de scripts Python estruturados em `src/extraction.py` para consumo resiliente da API de Dados Abertos da Câmara dos Deputados.
* Extração modularizada por meio de componentes especializados: `DeputadosExtractor`, `PartidosExtractor`, `ProposicoesExtractor` e `VotacoesExtractor`.
* Gerenciamento eficiente de paginação, tratamento de timeouts e persistência do JSON bruto no diretório `data/raw/` (Camada Bronze).

2. **Diagnóstico e Configuração**

* Implementação de rotinas automáticas de validação (`src/diagnostico.py`), executadas previamente ao pipeline principal, garantindo a integridade de diretórios, conectividade com banco de dados e APIs.
* Centralização e isolamento de credenciais e parâmetros operacionais por meio de variáveis de ambiente controladas em `src/config.py` e `.env`.

3. **Transformação e Carga (ETL)**

* Limpeza, padronização e estruturação dos dados brutos com Pandas em `src/transformers.py`.
* Modelagem dimensional (Schema) convertendo estruturas JSON aninhadas em tabelas relacionais de Fato e Dimensão.
* Orquestração e persistência da carga incremental no banco de dados PostgreSQL via SQLAlchemy em `src/transformation.py`.

4. **Camada de Inteligência Artificial**

* Enriquecimento analítico das proposições tramitadas utilizando os modelos da OpenAI estruturado em `src/ai_layer.py`.
* **Classificação Temática Automatizada:** Mapeamento de ementas legislativas através de vetores de alta densidade (`text-embedding-3-small`) e similaridade de cosseno contra um catálogo fechado de temas.
* **Resumo Executivo:** Geração automatizada de sumários executivos direcionados ao mercado corporativo utilizando o modelo `gpt-4o-mini`.
* **Modo de Simulação (Dry Run):** Mecanismo de auditoria que calcula previamente o volume de tokens e custos estimados em USD/BRL antes de efetivar as chamadas reais.

5. **Automação, Orquestração e Monitoramento**

* Centralização do fluxo operacional no n8n através do agendamento automatizado da rotina principal (`main.py`).
* Mecanismo de entrega baseado em relatórios diários de alto impacto (Digest HTML via E-mail) contendo temas classificados e resumos gerados pela IA, além de alertas dedicados para monitoramento de falhas e sucessos do pipeline.

## <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGRxeDNjenpocXN6M2lsdzZ2Z2toYzIwNHM0ODJ4MjJxdXliaGR6eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/1ZIoSmnkIP0ghBiiAw/giphy.gif" alt="dados_4" width="30" height="30" />  Motivo das decisões técnicas:

![roadmap](readme/roadmap.png)

1. **Por que orquestrar `main.py` no n8n (Execute Command) em vez de reimplementar a ingestão em nós nativos?**

* A lógica de paginação, retry, validação e carga já está testada em Python. Reescrevê-la em nós HTTP do n8n duplicaria código e criaria duas fontes de verdade. O n8n entra como **orquestrador e camada de notificação**, não como ETL paralelo. O custo dessa escolha é que o n8n precisa rodar no mesmo host do repositório (VPS/Docker/local self-hosted) — documentado no guia.

2. **Por que classificação por embeddings (Caminho A) e não pedir o tema direto à LLM?**

* **Três motivos**: 
  * **custo** — 1 embedding por ementa com `text-embedding-3-small` custa frações de centavo, muito abaixo de uma chamada de chat por proposição;
  * **consistência** — a lista de ~11 temas é um catálogo fechado, então a similaridade de cosseno sempre escolhe um rótulo válido, enquanto a LLM poderia inventar categorias novas; 
  * **auditabilidade** — guardamos o `tema_score`, deixando a classificação transparente e com limiar ajustável (`LIMIAR_TEMA`).

3. **Por que e-mail e não Telegram (nesta entrega) ?**

* E-mail é o canal mais simples de configurar, demonstrar e printar para a avaliação, e é o formato que o cliente corporativo da Bússola Pública já consome. O workflow é trivialmente extensível para Telegram (basta um nó `Telegram` em paralelo ao e-mail de sucesso).

4. **Por que o digest mostra tema + resumo ?**

* Para a IA não ser decoração. O e-mail das 06h traz, para cada proposição priorizada, **o tema (embeddings)** e **o resumo executivo (GPT)**. A IA aparece no produto final que chega ao cliente — exatamente o que o desafio cobra.

5. **Controle de custo de IA:**

* Tanto  (resumo) quanto  (tema) do `ai_layer.py` sobem em `DRY_RUN=true` por padrão: estimam tokens e custo (USD/BRL) **antes** de gastar. Só com `DRY_RUN=false` há chamada real e gravação. Processamento é idempotente — pula o que já tem `resumo_executivo`/`tema`.

## <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTk3OHU4ajh0M3d3aDZjajJ1bHh2cDV1N3J5Z20yaDBoMGZjcmRncyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/l1KVbQDHx8NDa2XBK/giphy.gif" alt="dados_4" width="30" height="30" />  Prompts e parâmetros da camada de IA:

1. **Resumo executivo (Caminho B)**:

* System prompt (perfil de analista) + user prompt com a ementa. Regras: máximo 3 frases, sem jargão, estrutura (1) o que propõe, (2) quem é impactado, (3) ponto de atenção para empresas. Modelo `gpt-4o-mini`, `temperature=0.3`, `max_tokens=300`, `timeout=30`.


2. **Classificação temática (Caminho A)**:

* Não usa prompt de chat: usa **embeddings**. Para cada tema do catálogo, uma frase-descrição rica é embedada uma única vez; cada ementa é embedada e comparada por **similaridade de cosseno**. O tema de maior score vence; abaixo de `LIMIAR_TEMA` (0,20) cai em "Outros".
* Catálogo de temas: Tecnologia e IA · Tributário · Saúde · Trabalho e Previdência · Meio Ambiente · Economia e Finanças · Educação · Segurança Pública · Agronegócio · Infraestrutura e Transporte · Direitos e Cidadania.
* Custo de referência (mai/2025): `text-embedding-3-small` ≈ US$ 0,02 / 1M tokens. Para ~120 tokens por ementa, classificar 1.000 proposições custa da ordem de US$ 0,002 (poucos centavos de real).

## <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2FuanM5OHhoYTZzZDU3ODlqbmQ4YjNxdm9qd2pxcDZmNmkza2VoNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/0sUBW0QZExZ1HJrmyr/giphy.gif" alt="dados_5" width="30" height="30" /> Modelo de Dados (DWH / Camada Relacional):

Para suportar as análises legislativas e o enriquecimento com Inteligência Artificial, os dados transformados foram estruturados em um modelo relacional (Fatos e Dimensões).

![logo](readme/schema.png)

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3cxYXpwZm00OW9ocDA5a3NrczMwM284Y2Mya3E3cmhyNnRldmk3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9NDxo04budFf554AWO/giphy.gif" alt="dados_5_1" width="20" height="20" /> Tabelas de Dimensão (Dim):

`dim_deputados`
* Armazena os dados cadastrais e identificadores únicos dos deputados federais.

| Campo             | Tipo  | Restrição   | Descrição |
|-------------------|-------|------------|------------|
| id_deputado       | int8  | Primary Key | Identificador único do deputado na API da Câmara. |
| nome              | text  | Nullable    | Nome parlamentar do deputado. |
| sigla_partido     | text  | Nullable    | Sigla do partido político atual. |
| sigla_uf          | text  | Nullable    | Estado (Unidade da Federação) pelo qual foi eleito. |
| id_legislatura    | int8  | Nullable    | Identificador da legislatura atual. |
| url_foto          | text  | Nullable    | Link para a foto oficial do parlamentar. |
| uri               | text  | Nullable    | Link do endpoint oficial do deputado na API. |


`dim_partidos`
* Dicionário de partidos políticos mapeados no pipeline.

| Campo      | Tipo | Restrição   | Descrição |
|------------|------|------------|------------|
| id_partido | int8 | Primary Key | Identificador único do partido na API. |
| sigla      | text | Nullable    | Sigla oficial do partido político. |
| nome       | text | Nullable    | Nome completo do partido político. |
| uri        | text | Nullable    | Link do endpoint oficial do partido na API. |

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3cxYXpwZm00OW9ocDA5a3NrczMwM284Y2Mya3E3cmhyNnRldmk3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9NDxo04budFf554AWO/giphy.gif" alt="dados_5_2" width="20" height="20" />  Tabelas de Fato (Fact):

`fato_proposicoes`
* Entidade central de análise que armazena os textos, metadados e os enriquecimentos de IA (resumos executivos).

| Campo              | Tipo        | Restrição   | Descrição |
|--------------------|------------|------------|------------|
| id_proposicao      | int8       | Primary Key | Identificador único da proposição (projeto de lei, PEC, etc). |
| sigla_tipo         | text       | Nullable    | Tipo da proposição (ex: PL, PEC, MPV). |
| numero             | int8       | Nullable    | Número oficial da proposição no ano. |
| ano                | int8       | Nullable    | Ano de apresentação da matéria legislativa. |
| ementa             | text       | Nullable    | Texto original da ementa detalhando o objetivo do projeto. |
| data_apresentacao  | timestamptz | Nullable   | Data e hora em que a matéria foi protocolada. |
| created_at         | timestamptz | Nullable   | Data/Hora de inserção do registro no banco de dados. |
| resumo_executivo   | text        | Nullable    | [IA Layer] Resumo analítico simplificado gerado via OpenAI. |
| data_resumo        | timestamptz | Nullable   | [IA Layer] Timestamp de quando o resumo de IA foi gerado. |
| tema               | text        |  Nullable   | [IA Layer] Tema classificado por embeddings. |
| tema_score         | float8      |   Nullable     | [IA Layer] Similaridade de cosseno (0–1). |
| data_tema          | timestamptz |    Nullable    | [IA Layer] Quando o tema foi classificado. |

`fato_proposicoes_autores`
* Tabela associativa que mapeia a autoria ou coautoria de cada proposição legislativa.

| Campo          | Tipo | Restrição | Descrição |
|----------------|------|-----------|------------|
| id_proposicao  | int8 | Nullable  | ID da proposição (chave estrangeira para fato_proposicoes). |
| nome_autor     | text | Nullable  | Nome do parlamentar ou órgão autor da matéria. |
| tipo_autor     | text | Nullable  | Categoria do autor (ex: Deputado, Órgão Executivo). |
| uri_autor      | text | Nullable  | Link do endpoint do autor na API. |


`fato_votacoes`
* Registra as sessões de votações ocorridas na Câmara para deliberação das matérias.

| Campo                | Tipo        | Restrição   | Descrição |
|----------------------|------------|------------|------------|
| id_votacao           | text       | Primary Key | Identificador alfanumérico único da votação. |
| descricao            | text       | Nullable    | Detalhamento do que está sendo votado em plenário ou comissão. |
| data_hora_registro   | timestamptz | Nullable   | Data e hora exata da sessão de votação. |
| aprovacao            | int2       | Nullable    | Indicador binário/status se a matéria foi aprovada (1) ou não (0). |
| proposicao_objeto    | text       | Nullable    | Descrição ou link da matéria que originou a votação. |
| created_at           | timestamptz | Nullable   | Registro de auditoria de inserção da linha no banco. |

`fato_votos`
* Contém o posicionamento individual e nominal de cada parlamentar em uma votação específica.

| Campo       | Tipo        | Restrição       | Descrição |
|------------|------------|----------------|------------|
| id         | int4       | PK / Identity   | Chave primária sequencial auto-incremental da tabela. |
| id_votacao | varchar    | Non-Nullable    | ID da votação correspondente (Relaciona-se com fato_votacoes). |
| tipo_voto  | varchar    | Nullable        | O voto computado do deputado (ex: Sim, Não, Abstenção, Obstrução). |
| id_deputado| int4       | Nullable        | ID do parlamentar que votou (Relaciona-se com dim_deputados). |
| created_at | timestamptz | Nullable       | Data de inserção do registro de voto. |


###  <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3cxYXpwZm00OW9ocDA5a3NrczMwM284Y2Mya3E3cmhyNnRldmk3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9NDxo04budFf554AWO/giphy.gif" alt="dados_5_3" width="20" height="20" /> Relacionamentos:

- `fato_proposicoes` 1—N `fato_proposicoes_autores` (por `id_proposicao`).
- `fato_votacoes` 1—N `fato_votos` (por `id_votacao`).
- `fato_votos` N—1 `dim_deputados` (por `id_deputado`).
- `dim_deputados` N—1 `dim_partidos` (por `sigla_partido` / `sigla`).
- `fato_proposicoes.tema` alimenta os alertas/digest do workflow n8n da Etapa de automação.


## Critérios de avaliação atendidos

- **Funcionamento:** pipeline roda do início ao fim (extração → carga → IA → notificação).
- **Modelagem:** modelo estrela preservado; IA adiciona colunas, não quebra o schema.
- **IA aplicada:** tema (embeddings) e resumo (GPT) chegam ao e-mail do cliente — não é decoração.
- **Automação:** workflow n8n agendado, com sucesso e falha tratados.
- **Comunicação:** diagrama, doc técnica, prompts e pitch executivo.


## <img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbDY4OGlpMW9yZ3JvcHAzamw3NnU3ZHZ3MHBjZDRyOHdtNG16cHRqMiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/Op1ku9feTAxo1zA8ff/giphy.gif" alt="dados_6" width="30" height="30" /> Como Executar o Projeto:

Siga os passos abaixo para clonar o repositório, configurar as variáveis de ambiente, subir a infraestrutura do n8n via Docker e executar o pipeline de inteligência legislativa.

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTV4ZGFjc3VoZnJvbWs0YW00dXowMGk2OG0wcmVxcWtudmFxbm8xbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dv7sW46M17UQ36WVBT/giphy.gif" alt="dados_6_1" width="20" height="20" /> **Pré-requisitos**:

Antes de começar, certifique-se de ter instalado em sua máquina:

* **Python** (versão ^3.11 requisitada pelo projeto)
* **Git**
* **Docker Desktop** ([Baixe o instalador oficial aqui](https://www.docker.com/products/docker-desktop/))
* **Poetry** (opcional, caso queira utilizar o gerenciamento por Poetry)

---

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTV4ZGFjc3VoZnJvbWs0YW00dXowMGk2OG0wcmVxcWtudmFxbm8xbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dv7sW46M17UQ36WVBT/giphy.gif" alt="dados_6_2" width="20" height="20" /> **Passo a Passo**:

### 1. **Clonar o Repositório e Acessar a Pasta**

Abra o seu terminal e execute os comandos abaixo para clonar o projeto e entrar no diretório raiz:

```bash
git clone https://github.com/micaellimal/Bussola-Publica-Pipeline-de-Inteligencia-Legislativa-com-IA.git
cd Bussola-Publica-Pipeline-de-Inteligencia-Legislativa-com-IA
```

### 2. **Configurar as Variáveis de Ambiente (.env)**

O pipeline e o container do n8n precisam de credenciais e parâmetros de volume definidos.

* Duplique o arquivo de exemplo para criar o seu arquivo `.env` definitivo:

```bash
cp .env.example .env
```

* Abra o arquivo `.env` gerado no seu editor e preencha com as suas credenciais reais:

```env
# =============================================================================
# BUSSOLA PUBLICA - Variáveis de Ambiente
# =============================================================================

# --- PostgreSQL (Supabase / Neon) ---
DATABASE_URL=postgresql://usuario:senha@host:5432/banco

# --- OpenAI API ---
OPENAI_API_KEY=sk-proj-SUA_CHAVE_REAL_AQUI

# --- Configurações de Acesso e Sincronização do n8n ---
N8N_USER=admin
N8N_PASSWORD=bussola123
REPO_PATH=C:/Caminho/Ate/O/Projeto/Bussola-Publica-Pipeline-de-Inteligencia-Legislativa-com-IA

# --- Configurações do Pipeline de IA ---
DRY_RUN=true
BATCH_SIZE=10
MODELO_IA=gpt-4o-mini
```

> ⚠️ **Importante:** No parâmetro `REPO_PATH`, utilize barras normais (`/`) mesmo no Windows para garantir que o Docker consiga mapear o volume corretamente.

---

### 3. **Subir a Infraestrutura com Docker**

Com o Docker Desktop aberto e exibindo o status **Engine Running**, execute:

```bash
docker compose up -d --build
```

Este comando irá construir e iniciar todos os containers necessários para o funcionamento do projeto.

---

### 4. **Sincronizar as Dependências Python no Container**

Após os containers estarem em execução, instale as dependências do projeto dentro do container do n8n.

#### Opção A: Via requirements.txt (Recomendado)

Instalação direta utilizando o `pip3` nativo do Linux:

```bash
docker compose exec -T n8n sh -c "cd /opt/bussola-publica && pip3 install --no-cache-dir --break-system-packages -r requirements.txt"
```

#### Opção B: Via Poetry

Caso prefira manter o gerenciamento de dependências através do Poetry:

```bash
docker compose exec -T n8n sh -c "cd /opt/bussola-publica && poetry config cache-dir /home/node/.cache/pypoetry && poetry config virtualenvs.create false && poetry install --no-root"
```

---

### 5. **Configurar e Executar o Workflow no n8n**

Agora que os containers e as dependências estão prontos, todo o pipeline passa a ser controlado visualmente pelo n8n.

#### Acessar a Interface

Abra o navegador e acesse:

```text
http://localhost:5678
```

#### Criar a Conta de Administrador

No primeiro acesso, será exibida a tela **Set up owner account**. Crie o usuário e senha que serão utilizados para administrar sua instância local do n8n.

#### Importar o Workflow

1. No canto superior direito do painel do n8n, clique no menu de três pontos.
2. Selecione **Import from File**.
3. Escolha o arquivo:

```text
workflows/bussola_publica_ingestao_diaria.json
```

#### Configurar as Credenciais

Após importar o fluxo:

* Configure as credenciais de banco de dados (PostgreSQL / Supabase).
* Configure as credenciais de e-mail (SMTP), caso utilize notificações.

#### Executar o Pipeline

Para testar toda a esteira de processamento imediatamente:

1. Abra o workflow importado.
2. Clique em **Execute Workflow**.

A execução percorrerá todas as etapas do pipeline, incluindo:

* Gatilho de agendamento;
* Coleta das proposições legislativas;
* Processamento e enriquecimento com IA;
* Persistência dos dados;
* Geração do Digest HTML;
* Envio das notificações configuradas.

---

### 6. **Encerrar os Serviços**

Quando finalizar o desenvolvimento ou desejar desligar a infraestrutura local, execute:

```bash
docker compose down
```

Este comando interromperá e removerá os containers criados pelo projeto.

## <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExdGU3cXhzeHF5YmhsdmtxdzA1bGg1dWRwMWF6MmZjYWM5MjN2dTg1dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/AvSbLuJ4mVgpl4sG4M/giphy.gif" alt="dados_7" width="30" height="30" />  Estrutura de Pastas e Arquivos:

Abaixo está a arquitetura modular implementada no projeto para garantir a separação de responsabilidades em cada etapa do pipeline:


```

├── .venv/                          # Ambiente virtual local
├── .vscode/                        # Configurações do editor (settings.json)
├── data/                           # Diretório de dados do projeto
│   └── raw/                        # Data Lake - Camada Bronze (Arquivos JSON brutos)
│       ├── deputados/              # JSONs de deputados com timestamp
│       ├── partidos/               # JSONs de partidos
│       ├── proposicoes/            # JSONs de proposições e autores
│       └── votacoes/               # JSONs de votações e votos
├── docs/                           # Documentações, guias e relatórios do projeto
│   ├── Bussola_Publica_Pitch.pptx  # Slide de pitch do projeto
│   ├── Etapa4_Camada_IA.pdf        # Relatório de especificação da camada de IA
│   ├── Etapa5_Documentacao_Tecnica.md # Documentação técnica da Etapa 5
│   ├── GUIA_GIT_COMMITS.md         # Guia de padronização de commits
│   ├── GUIA_IMPORTACAO_n8n.md      # Guia para importação de fluxos no n8n
│   ├── modelo_dados.md             # Detalhamento do modelo de dados
│   ├── README_snippet_Etapa5.md    # Snippet de documentação complementar
│   └── SETUP_n8n_WINDOWS.md        # Guia de configuração do n8n no Windows
├── logs/                           # Logs de execução do pipeline
├── readme/                         # Ativos visuais e mídias do README
│   ├── diagrama_pipeline.svg       # Diagrama SVG do fluxo do pipeline
│   ├── icon_legodados.png          # Ícone do projeto
│   ├── LegoDados.png               # Logotipo LegoDados
│   ├── legodadosbanner.png         # Banner principal do repositório
│   ├── roadmap.png                 # Imagem do roadmap de desenvolvimento
│   └── schema.png                  # Diagrama do esquema de banco de dados
├── scripts/                        # Scripts utilitários de automação e setup
│   ├── 1_instalar_docker.ps1       # Script PowerShell para instalação do Docker
│   ├── 2_subir_n8n.ps1             # Script PowerShell para inicialização do n8n
│   └── build_deck.js               # Script JavaScript para build/geração de apresentação
├── src/                            # Código-fonte principal do projeto
│   ├── __pycache__/
│   ├── __init__.py
│   ├── ai_layer.py                 # Etapa 4: Integração com OpenAI (Resumos/Embeddings)
│   ├── config.py                   # Configurações globais e variáveis de ambiente
│   ├── diagnostico.py              # Script de validação e saúde do ambiente
│   ├── extraction.py               # Etapa 1: Scripts de extração/ingestão da API
│   ├── transformation.py           # Etapa 3: Classe PipelineEtapa3 (Orquestrador de carga)
│   └── transformers.py             # Funções de transformação e limpeza com Pandas
├── workflows/                      # Workflows exportados para automação
│   └── bussola_publica_ingestao_diaria.json # Fluxo de automação do n8n
├── .env                            # Variáveis de ambiente locais (Credenciais)
├── .env.example                    # Modelo de configuração das variáveis de ambiente
├── .gitignore                      # Arquivos e pastas ignorados pelo Git
├── docker-compose.yml              # Arquivo de especificação dos containers Docker
├── Dockerfile                      # Instruções de build da imagem personalizada do container
├── LEIA-ME.md                      # Documentação de introdução em português
├── LICENSE                         # Licença de uso do projeto
├── main.py                         # Ponto de entrada principal do pipeline
├── main2.py                        # Ponto de entrada alternativo/testes de execução
├── poetry.lock                     # Trava de versões das dependências do Poetry
├── pyproject.toml                  # Configurações do projeto e dependências (Poetry)
├── README.md                       # Documentação principal do projeto
├── README2.md                      # Documentação secundária/rascunho
└── requirements.txt                # Lista de dependências Python para instalação via pip

```