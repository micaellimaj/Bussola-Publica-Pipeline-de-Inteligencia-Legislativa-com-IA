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

* **Linguagem**: Python (v3.14 / gerenciado via Poetry)
* **Manipulação de Dados**: Pandas
* **Banco de Dados**: PostgreSQL (Hospedado via Supabase)
* **Orquestração & Automação**: n8n
* **Inteligência Artificial**: OpenAI API (GPT-4o-mini / GPT-4o para resumos e text-embedding-3-small para classificação)
* **Integrações e Ferramentas**: SQLAlchemy, Requests, Python-dotenv, Poetry


## <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHdwMnFrc2V2cHM2aGltMHJ5cXcxaXlhNGJneHNkOHl3d3JpNWdqcyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9LZSPFwk4UkeVUvJRV/giphy.gif" alt="dados_4" width="30" height="30" /> Arquitetura e Roadmap de Desenvolvimento:

![roadmap](readme/roadmap.png)

O projeto está estruturado em cinco etapas principais. Abaixo está o status atual de desenvolvimento do que já foi mapeado e implementado:

1. **Exploração e Extração (Ingestão)** `[CONCLUÍDO]`

* Desenvolvimento de scripts Python em src/extraction.py para consumo estruturado da API de Dados Abertos.
* Extração modularizada através de extratores específicos: DeputadosExtractor, PartidosExtractor, ProposicoesExtractor e VotacoesExtractor.
* Tratamento de paginação, resiliência contra erros de timeout e persistência do JSON bruto no diretório local data_raw/ (Camada Bronze).

2. **Diagnóstico e Configuração** `[CONCLUÍDO]`

* Implementação de rotinas de validação inicial (src/diagnostico.py) disparadas antes da execução principal para garantir a integridade dos diretórios e conexões.
* Centralização das configurações e segurança através de variáveis de ambiente gerenciadas em src/config.py e .env.

3. **Transformação e Carga (ETL)** `[CONCLUÍDO]`

* Limpeza, padronização e processamento dos dados brutos utilizando Pandas (src/transformers.py).
* Modelagem relacional transformando arquivos JSON em estruturas adequadas para tabelas Fato e Dimensão (ex: fato_proposicoes_autores, fato_votacoes, fato_votos).
* Orquestração e execução da carga incremental em banco de dados PostgreSQL via SQLAlchemy (src/transformation.py).

4. **Camada de Inteligência Artificial** `[EM DESENVOLVIMENTO / PARCIALMENTE IMPLEMENTADO]`

* Estruturação da lógica em src/ai_layer.py para enriquecimento analítico inteligente de proposições parlamentares pendentes através da API da OpenAI.
* Modo de Simulação (Dry Run): Implementação de estimativas financeiras automatizadas de consumo de tokens (Métricas de Custo Estimado em USD/BRL baseadas no modelo gpt-4o-mini) para validação prévia de lotes (Batch) antes do processamento real.
* Resumo Executivo: Geração automática de resumos simplificados e acionáveis das proposições legislativas pendentes diretamente integrados à base de dados.
* Próximo passo: Integração completa do cálculo de classificação temática via embeddings (text-embedding-3-small) utilizando similaridade de cosseno.

5. **Automação e Monitoramento** `[PLANEJADO]`

* Configuração de workflows no n8n para a execução programada do pipeline principal (main.py).
* Envio de alertas automatizados (via Telegram ou E-mail) contendo relatórios diários de proposições de alto impacto e métricas de custo.


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
| resumo_executivo   | text       | Nullable    | [IA Layer] Resumo analítico simplificado gerado via OpenAI. |
| data_resumo        | timestamptz | Nullable   | [IA Layer] Timestamp de quando o resumo de IA foi gerado. |

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

## <img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbDY4OGlpMW9yZ3JvcHAzamw3NnU3ZHZ3MHBjZDRyOHdtNG16cHRqMiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/Op1ku9feTAxo1zA8ff/giphy.gif" alt="dados_6" width="30" height="30" /> Como Executar o Projeto:

Siga os passos abaixo para clonar o repositório, configurar o ambiente virtual com o Poetry, definir as variáveis de ambiente e executar o pipeline de inteligência legislativa.

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTV4ZGFjc3VoZnJvbWs0YW00dXowMGk2OG0wcmVxcWtudmFxbm8xbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dv7sW46M17UQ36WVBT/giphy.gif" alt="dados_6_1" width="20" height="20" /> **Pré-requisitos**:

Antes de começar, certifique-se de ter instalado em sua máquina:
* **Python** (versão ^3.11 requisitada pelo projeto)
* **Poetry** (gerenciador de pacotes e ambientes virtuais)
* **Git**

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTV4ZGFjc3VoZnJvbWs0YW00dXowMGk2OG0wcmVxcWtudmFxbm8xbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dv7sW46M17UQ36WVBT/giphy.gif" alt="dados_6_2" width="20" height="20" /> **Passo a Passo**:

1. **Clonar o Repositório e Acessar a Pasta**:
Abra o seu terminal e execute os comandos abaixo para clonar o projeto e entrar no diretório raiz:

```
git clone https://github.com/micaellimal/Bussola-Publica-Pipeline-de-Inteligencia-Legislativa-com-IA.git
cd Bussola-Publica-Pipeline-de-Inteligencia-Legislativa-com-IA
```


2. **Instalar as Dependências com o Poetry**:

O projeto utiliza o Poetry para isolar o ambiente e gerenciar as bibliotecas estruturadas no pyproject.toml (como pandas, sqlalchemy, openai, entre outras). Instale todas as dependências executando:

```
poetry install
```

Este comando criará o ambiente virtual automaticamente e instalará os pacotes nas versões exatas necessárias.

3. **Configurar as Variáveis de Ambiente (.env)**:

O pipeline precisa de credenciais do banco de dados e da API da OpenAI para funcionar.

* Duplique o arquivo de exemplo para criar o seu arquivo .env definitivo:
```
cp .env.example .env
```

* Abra o arquivo .env recém-criado no seu editor (como o VS Code) e preencha os campos com as suas credenciais reais conforme o modelo abaixo:

```
# =============================================================================
# BUSSOLA PUBLICA - Variáveis de Ambiente
# =============================================================================

# --- PostgreSQL (Supabase / Neon / Railway) ---
# No Supabase: Settings > Database > Connection string > URI
DATABASE_URL=postgresql://usuario:senha@host:5432/banco

# --- OpenAI API ---
# Obtenha em: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-SUA_CHAVE_REAL_AQUI

# --- Configurações do Pipeline de IA (Etapa 4) ---
# DRY_RUN=true  -> Modo Simulação: apenas estima custos de tokens, não consome API e não grava no banco.
# DRY_RUN=false -> Modo Produção: executa o enriquecimento real e salva os dados.
DRY_RUN=true

# Quantidade de proposições pendentes a processar por lote/execução
BATCH_SIZE=10

# Modelo OpenAI escolhido (gpt-4o-mini é ~10x mais barato e ideal para os resumos)
MODELO_IA=gpt-4o-mini
```


4. **Executar o Pipeline**:

Com o ambiente configurado e as credenciais prontas, você pode rodar o ponto de entrada principal do projeto através do Poetry:

* **Para rodar o pipeline principal**:

```
poetry run python main.py
```

Se o DRY_RUN estiver definido como true, você verá no console o diagnóstico de custos e o volume de proposições que estão prontas para processamento, garantindo total controle financeiro antes de consumir os créditos da API.


## <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExdGU3cXhzeHF5YmhsdmtxdzA1bGg1dWRwMWF6MmZjYWM5MjN2dTg1dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/AvSbLuJ4mVgpl4sG4M/giphy.gif" alt="dados_7" width="30" height="30" />  Estrutura de Pastas e Arquivos:

Abaixo está a arquitetura modular implementada no projeto para garantir a separação de responsabilidades em cada etapa do pipeline:


```

├── .venv/                         # Ambiente virtual local
├── .vscode/                       # Configurações do editor (settings.json)
├── data_raw/                      # Data Lake - Camada Bronze (Arquivos JSON brutos)
│   ├── deputados/                 # JSONs de deputados com timestamp
│   ├── partidos/                  # JSONs de partidos
│   ├── proposicoes/               # JSONs de proposições e autores
│   └── votacoes/                  # JSONs de votações e votos
├── docs/                          # Documentações e relatórios das etapas
│   └── Etapa4_Camada_IA.pdf       # Relatório de especificação da camada de IA
├── logs/                          # Logs de execução do pipeline
│   └── transformacao_20260528.log # Registro histórico de transformações
├── src/                           # Código-fonte principal do projeto
│   ├── __pycache__/
│   ├── _init_.py
│   ├── ai_layer.py                # Etapa 4: Integração com OpenAI (Resumos/Embeddings)
│   ├── config.py                  # Configurações globais e variáveis de ambiente
│   ├── diagnostico.py             # Script de validação e saúde do ambiente
│   ├── extraction.py              # Etapa 1: Scripts de extração/ingestão da API
│   ├── transformation.py          # Etapa 3: Classe PipelineEtapa3 (Orquestrador de carga)
│   └── transformers.py            # Funções de transformação e limpeza com Pandas
├── .env                           # Variáveis de ambiente locais (Credenciais)
├── .env.example                   # Modelo de configuração das variáveis de ambiente
├── .gitignore                     # Arquivos ignorados pelo Git
├── LICENSE                        # Licença do projeto
├── main.py                        # Ponto de entrada do pipeline de extração/ingestão
├── main2.py                       # Ponto de entrada alternativo/testes de execução
├── poetry.lock                    # Trava de versões das dependências
├── pyproject.toml                 # Configurações do projeto e dependências (Poetry)
└── README.md                      # Documentação do projeto

```