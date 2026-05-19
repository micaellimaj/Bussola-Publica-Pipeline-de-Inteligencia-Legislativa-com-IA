# Bússola Pública: Pipeline de Inteligência Legislativa com IA

Este repositório contém o Projeto Integrador da pós-graduação em Engenharia de Dados e Inteligência Artificial. O objetivo é desenvolver um pipeline de dados completo (ETL) que automatiza a captura, organização e análise de dados da API de Dados Abertos da Câmara dos Deputados.

## Propósito do Projeto

Transformar o oceano de dados brutos do legislativo brasileiro em sinais acionáveis para consultorias de relações governamentais e empresas reguladas. O projeto visa substituir processos manuais e inconsistentes por uma arquitetura escalável que utiliza IA Generativa para classificação temática e resumos executivos.

## Stack Tecnológica

* Linguagem: Python (v3.10+)
* Manipulação de Dados: Pandas
* Banco de Dados: PostgreSQL (Hospedado via Supabase)
* Orquestração & Automação: n8n
* Inteligência Artificial: OpenAI API (GPT-4o para resumos e text-embedding-3-small para classificação)
* Integrações: SQLAlchemy, Requests

## Roadmap de Desenvolvimento

O projeto está estruturado em cinco etapas principais:

1. **Exploração da API**: Mapeamento dos endpoints /deputados, /proposicoes, /votacoes e /partidos.
2. **Extração (Ingestão)**: Desenvolvimento de scripts Python para consumo da API com tratamento de paginação, erros de timeout e persistência de JSON bruto (Data Lake - Bronze Layer).
3. **Transformação e Carga**:
  * Limpeza e validação de dados com Pandas (datas, valores monetários, deduplicação).
  * Modelagem de dados em tabelas Fato e Dimensão.
  * Carga no PostgreSQL via SQLAlchemy.
4. **Camada de Inteligência Artificial**:
  * **Classificação Temática**: Uso de embeddings para categorizar proposições em temas como Tecnologia, Saúde e Tributação via similaridade de cosseno.
  * **Resumo Executivo**: Geração de resumos automáticos em linguagem clara para tomada de decisão.
5. **Automação e Monitoramento**:
  * Workflow no n8n para execução programada do pipeline.
  * Sistema de alertas (Email ou Telegram) para proposições críticas.


## Repositório:

```
Bussola-Publica/
├── data/               # Arquivos locais (não versionados no Git se forem grandes)
│   ├── raw/            # Onde ficaria seu dados_camara.db inicial
│   └── processed/      # Dados após limpeza ou processamento por IA
├── notebooks/          # Para testes rápidos e visualizações gráficas (arquivos .ipynb)
├── scripts/            # Onde a mágica acontece, dividido por etapas
│   ├── extraction/     # Seus scripts atuais de coleta da API
│   ├── analysis/       # Scripts de EDA (Análise Exploratória)
│   └── transform/      # Scripts de limpeza e preparação para IA
├── logs/               # Para salvar os prints/outputs de erro automaticamente
├── .gitignore          # Essencial para não subir o banco de dados e arquivos PDF
├── requirements.txt    # Lista de bibliotecas (pandas, requests, fpdf2, etc)
└── README.md           # Documentação do projeto

```