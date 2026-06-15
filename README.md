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


## <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHdwMnFrc2V2cHM2aGltMHJ5cXcxaXlhNGJneHNkOHl3d3JpNWdqcyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9LZSPFwk4UkeVUvJRV/giphy.gif" alt="dados_4" width="30" height="30" /> Arquitetura e Roadmap de Desenvolvimento:

![diagrama](readme/diagrama_pipeline.svg)

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

4. **Camada de Inteligência Artificial** `[CONCLUÍDO]`

* Estruturação da lógica em src/ai_layer.py para enriquecimento analítico inteligente de proposições parlamentares pendentes através da API da OpenAI.
* Modo de Simulação (Dry Run): Implementação de estimativas financeiras automatizadas de consumo de tokens (Métricas de Custo Estimado em USD/BRL baseadas no modelo gpt-4o-mini) para validação prévia de lotes (Batch) antes do processamento real.
* Resumo Executivo: Geração automática de resumos simplificados e acionáveis das proposições legislativas pendentes diretamente integrados à base de dados.
* Classificação Temática (Etapa 5 - Caminho A): cada proposição é classificada por embeddings (`text-embedding-3-small`) + similaridade de cosseno contra um catálogo de temas de negócio, gravando `tema`, `tema_score` e `data_tema` em `fato_proposicoes` (`src/classificacao_tematica.py`).

5. **Automação e Monitoramento** `[CONCLUÍDO]`

* Workflow no **n8n** (`n8n/bussola_publica_ingestao_diaria.json`) agendado para **06h diariamente** (cron `0 6 * * *`), executando o pipeline principal (`main.py`) via *Execute Command*.
* **Notificação automática por e-mail** com o digest do dia: as 5 proposições mais relevantes das últimas 24h, já com **tema (embeddings)** e **resumo executivo (GPT)** — a IA chega ao produto final.
* **Tratamento de falha:** ramo dedicado que dispara e-mail de alerta com o `stderr` caso o pipeline quebre, sem depender da memória do analista.
* Passo a passo de importação e credenciais em [`n8n/GUIA_IMPORTACAO_n8n.md`](n8n/GUIA_IMPORTACAO_n8n.md); decisões técnicas e prompts da IA em [`docs/Etapa5_Documentacao_Tecnica.md`](docs/Etapa5_Documentacao_Tecnica.md).

6. **Visualização de Dados e Analytics (Power BI)** `[CONCLUÍDO]`

* Criação do layout e prototipagem de alta fidelidade das telas utilizando o **Figma**.
* Conexão nativa do Power BI Desktop ao data warehouse (PostgreSQL) hospedado no **Supabase**.
* Modelagem e relacionamentos Star Schema replicados no Power BI, com criação de medidas em DAX para contadores e distribuições.
* Publicação do relatório no Power BI Service e disponibilização de link público para consumo.

## <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGRxeDNjenpocXN6M2lsdzZ2Z2toYzIwNHM0ODJ4MjJxdXliaGR6eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/1ZIoSmnkIP0ghBiiAw/giphy.gif" alt="dados_5" width="30" height="30" />  Motivo das decisões técnicas:


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

6. **Por que o deploy público do Power BI não atualiza em tempo real com o n8n?**

* O link de compartilhamento web público (`Embed to website`) no plano gratuito do Power BI Service possui restrições de atualização automática para fontes cloud diretas via DirectQuery sem Gateway corporativo. Portanto, o painel online reflete os dados históricos estáticos da última publicação manual do arquivo `.pbix`. O pipeline no n8n popula o banco de dados Supabase em tempo real, mas o painel público web exige um reenvio do arquivo para refletir o estado mais recente.

7. **Resolução de Problema Crítico: Conexão Power BI ↔ Supabase (Erro de SSL):**

* Durante a configuração inicial, o Power BI Desktop rejeitou a conexão criptografada com o PostgreSQL do Supabase, retornando um erro de handshake SSL. 
* **Solução:** Foi necessário baixar o certificado raiz do Supabase (`prod-ca-2021.crt`) e instalá-lo no Windows na pasta de **Autoridades de Certificação Raiz Confiáveis** (via `certlm.msc`). Isso permitiu que o driver ODBC/PostgreSQL do Power BI validasse a identidade do servidor e estabelecesse a conexão segura.


## <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTk3OHU4ajh0M3d3aDZjajJ1bHh2cDV1N3J5Z20yaDBoMGZjcmRncyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/l1KVbQDHx8NDa2XBK/giphy.gif" alt="dados_6" width="30" height="30" />  Prompts e parâmetros da camada de IA:

1. **Resumo executivo (Caminho B)**:

* System prompt (perfil de analista) + user prompt com a ementa. Regras: máximo 3 frases, sem jargão, estrutura (1) o que propõe, (2) quem é impactado, (3) ponto de atenção para empresas. Modelo `gpt-4o-mini`, `temperature=0.3`, `max_tokens=300`, `timeout=30`.


2. **Classificação temática (Caminho A)**:

* Não usa prompt de chat: usa **embeddings**. Para cada tema do catálogo, uma frase-descrição rica é embedada uma única vez; cada ementa é embedada e comparada por **similaridade de cosseno**. O tema de maior score vence; abaixo de `LIMIAR_TEMA` (0,20) cai em "Outros".
* Catálogo de temas: Tecnologia e IA · Tributário · Saúde · Trabalho e Previdência · Meio Ambiente · Economia e Finanças · Educação · Segurança Pública · Agronegócio · Infraestrutura e Transporte · Direitos e Cidadania.
* Custo de referência (mai/2025): `text-embedding-3-small` ≈ US$ 0,02 / 1M tokens. Para ~120 tokens por ementa, classificar 1.000 proposições custa da ordem de US$ 0,002 (poucos centavos de real).

## <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3PsZHg2Nmxhejc2eHc3bHB6N3lxaGt4cXJiOXNubmR3Ym1zYTMxdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/TKcnPuNL3VdTah6ymA/giphy.gif" alt="dados_7" width="30" height="30" /> Insights Extraídos do Dashboard (LegoDados)

<div align="center">
  <p align="center"><b>Visualização das Telas do Painel</b></p>
  <img src="readme/powerBI/CAPA.png" width="32%" alt="Tela de Início" />
  <img src="readme/powerBI/TELA1.png" width="32%" alt="Relatório Principal" />
  <img src="readme/powerBI/TELA2.png" width="32%" alt="Equipe e BI" />
</div>

<br />

A análise do painel legislativo consolidado (com dados mapeados entre **01/06/2026 e 12/06/2026**) gera diagnósticos acionáveis para consultorias de relações governamentais:

*   **Predomínio Temático de "Segurança Pública" e "Saúde":** Das 200 proposições classificadas por IA, o tema *Saúde* desponta com 39 projetos. Isso indica uma forte janela de oportunidade (ou risco regulatório) para empresas do setor monitorarem o Plenário.
*   **Eficiência da IA no Filtro de Ruído:** O alto volume de proposições em "Outros" (115) demonstra a precisão do modelo em isolar matérias administrativas ou protocolares, focando o esforço humano apenas no que é estratégico.
*   **Concentração Política:** A visualização por partido mostra que **PL** e **PT** dominam o volume de proposições, sendo os stakeholders centrais para qualquer estratégia de advocacy.
*   **Detalhamento Executivo:** O cruzamento direto entre o resumo gerado pela IA e a ementa original permite uma tomada de decisão rápida sem a necessidade de ler o documento íntegro da Câmara.

> [IMPORTANT]
> **Observação sobre Atualização:** O link de deploy (Power BI Web) reflete os dados da última publicação manual do arquivo `.pbix`. Embora o pipeline (Python + n8n) atualize o banco de dados diariamente, o painel público só apresentará os novos dados após o reenvio do arquivo para o Power BI Service.

---

### <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjlyMG1wb3dkcXRjeG9pcWlsZGNkYWVwN2NlNDd5MmIzZTA4cms0byZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/spuwPuxfMgN6OkcVMy/giphy.gif" alt="dados_7_1" width="20" height="20" /> Links do Painel

*   **Protótipo do Layout (Figma):** Dowload dos [layouts](docs/figma/)
*   **Painel Interativo (Power BI Web):** [Acesse o Dashboard Publicado](https://app.powerbi.com/view?r=eyJrIjoiMDQwMjE3NDQtMjExMi00MWExLWFhNTAtNWM3ODAyYzk5M2NlIiwidCI6IjUxZGQ3ZDM4LTYwNzctNDgzNy1hYTE0LWFlNDNmZThiM2ViMCJ9)
*   **Arquivo Fonte do Projeto:** Download do arquivo [`LegoDados_Relatorio_Legislativo.pbix`](docs/power-BI/legislativoProjeto.pbix)



## <img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXJ1eHhyZmx5N2FtN29ia2tjMHdoZTRsOGpyNXQ3dDE0ZXVlNXNhciZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/S7sG06q4piBfxJ2iPL/giphy.gif" alt="dados_8" width="30" height="30" /> Evidências de Execução:


| Recurso | Evidência Visual |
| :--- | :--- |
| **DWH (30 Dias)**  | ![30 dias supabase](readme/prints/n8n_execucao_sucesso.jpg) |
| **Email Digest** | ![e-mail digest](readme/prints/email_digest.jpg) |
| **Camada de IA** | ![tema no Supabase](readme/prints/supabase_tema.jpg) |
|  **Workflow n8n**| ![n8n execução](readme/prints/supabase_30dias.jpg) |

> O Table Editor do Supabase exige login (sem link público no plano Free); os prints acima + a Reference ID do projeto servem como evidência de acesso ao banco.

## <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ2FuanM5OHhoYTZzZDU3ODlqbmQ4YjNxdm9qd2pxcDZmNmkza2VoNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/0sUBW0QZExZ1HJrmyr/giphy.gif" alt="dados_9" width="30" height="30" /> Modelo de Dados (DWH / Camada Relacional):

Para suportar as análises legislativas e o enriquecimento com Inteligência Artificial, os dados transformados foram estruturados em um modelo relacional (Fatos e Dimensões).

![logo](readme/schema.png)

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3cxYXpwZm00OW9ocDA5a3NrczMwM284Y2Mya3E3cmhyNnRldmk3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9NDxo04budFf554AWO/giphy.gif" alt="dados_9_1" width="20" height="20" /> Tabelas de Dimensão (Dim):

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

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3cxYXpwZm00OW9ocDA5a3NrczMwM284Y2Mya3E3cmhyNnRldmk3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9NDxo04budFf554AWO/giphy.gif" alt="dados_9_2" width="20" height="20" />  Tabelas de Fato (Fact):

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
| tema               | text       | Nullable    | [Etapa 5] Tema classificado via embeddings + cosseno (ex: Saúde, Tributário). |
| tema_score         | float8     | Nullable    | [Etapa 5] Score de similaridade de cosseno (0 a 1) do tema atribuído. |
| data_tema          | timestamptz | Nullable   | [Etapa 5] Timestamp em que a classificação temática foi gerada. |

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


###  <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3cxYXpwZm00OW9ocDA5a3NrczMwM284Y2Mya3E3cmhyNnRldmk3ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/9NDxo04budFf554AWO/giphy.gif" alt="dados_9_3" width="20" height="20" /> Relacionamentos:

- `fato_proposicoes` 1—N `fato_proposicoes_autores` (por `id_proposicao`).
- `fato_votacoes` 1—N `fato_votos` (por `id_votacao`).
- `fato_votos` N—1 `dim_deputados` (por `id_deputado`).
- `dim_deputados` N—1 `dim_partidos` (por `sigla_partido` / `sigla`).
- `fato_proposicoes.tema` alimenta os alertas/digest do workflow n8n da Etapa de automação.

## <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExb20yN2Q3NG0wZDJ3bnpjYjIxb2JieWN5dnI0aXNrbzAzc2NqdndybCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/CmeI2Ndgz1B5JWJDbt/giphy.gif" alt="dados_10" width="30" height="30" /> Critérios de avaliação atendidos

- **Funcionamento:** pipeline roda do início ao fim (extração → carga → IA → notificação).
- **Modelagem:** modelo estrela preservado; IA adiciona colunas, não quebra o schema.
- **IA aplicada:** tema (embeddings) e resumo (GPT) chegam ao e-mail do cliente — não é decoração.
- **Automação:** workflow n8n agendado, com sucesso e falha tratados.
- **Comunicação:** diagrama, doc técnica, prompts e pitch executivo.


## <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExNGgzd21kbXZjNWVucm5mcGd4M2VhcmtxNnhyanRuM2JuZXE2eTV2bSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/VIWyDnerbiT4wfVTtt/giphy.gif" alt="dados_11" width="30" height="30" /> Equipe (Squad LegoDados):

<div align="center">
  <table>
    <tr>
      <td align="center" valign="top" width="25%">
        <img src="readme/team/Micael.png" width="120px" style="border-radius: 30%;" alt="Micael Lima"/><br />
        <b>Micael Lima</b><br />
        <sup>Data Analytics & AI Engineer</sup><br />
        <small>Python • SQL • Power BI • AI Automation</small><br /><br />
        <a href="https://github.com/micaellimaj" target="_blank">
          <img src="https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
        </a>
        <a href="https://www.linkedin.com/in/micael-lima-data-analytics-ia-engineer/" target="_blank">
          <img src="https://img.shields.io/badge/-LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" />
        </a>
      </td>
      <td align="center" valign="top" width="25%">
        <img src="readme/team/Guilherme.png" width="120px" style="border-radius: 30%;" alt="Guilherme Sobral"/><br />
        <b>Guilherme Sobral</b><br />
        <sup>Analista de Dados / BI</sup><br />
        <small>Power BI • SQL • Excel • BI</small><br /><br />
        <a href="https://github.com/Sobral-git" target="_blank">
          <img src="https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
        </a>
        <a href="https://www.linkedin.com/in/guilherme-sobral-santos/" target="_blank">
          <img src="https://img.shields.io/badge/-LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" />
        </a>
      </td>
      <td align="center" valign="top" width="25%">
        <img src="readme/team/Heitor.png" width="120px" style="border-radius: 30%;" alt="Heitor Nogueira"/><br />
        <b>Heitor Nogueira</b><br />
        <sup>Inteligência de Negócios</sup><br />
        <small>BI • SQL • Excel • MIS</small><br /><br />
        <a href="https://github.com/heitorgraciani" target="_blank">
          <img src="https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
        </a>
        <a href="https://www.linkedin.com/in/heitor-graciani-nogueira-35201b10a/" target="_blank">
          <img src="https://img.shields.io/badge/-LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" />
        </a>
      </td>
      <td align="center" valign="top" width="25%">
        <img src="readme/team/Marlom.png" width="120px" style="border-radius: 30%;" alt="Marlon Vargas"/><br />
        <b>Marlon Vargas</b><br />
        <sup>Power BI Specialist</sup><br />
        <small>Data Analyst • Data Engineer • Power Apps</small><br /><br />
        <a href="https://github.com/Mssvargas" target="_blank">
          <img src="https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
        </a>
        <a href="https://www.linkedin.com/in/marlonssv/" target="_blank">
          <img src="https://img.shields.io/badge/-LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" />
        </a>
      </td>
    </tr>
  </table>
</div>

## <img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbDY4OGlpMW9yZ3JvcHAzamw3NnU3ZHZ3MHBjZDRyOHdtNG16cHRqMiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/Op1ku9feTAxo1zA8ff/giphy.gif" alt="dados_12" width="30" height="30" /> Como Executar o Projeto:

Siga os passos abaixo para clonar o repositório, configurar o ambiente virtual com o Poetry, definir as variáveis de ambiente e executar o pipeline de inteligência legislativa.

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTV4ZGFjc3VoZnJvbWs0YW00dXowMGk2OG0wcmVxcWtudmFxbm8xbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dv7sW46M17UQ36WVBT/giphy.gif" alt="dados_12_1" width="20" height="20" /> **Pré-requisitos**:

Antes de começar, certifique-se de ter instalado em sua máquina:
* **Python** (versão ^3.11 requisitada pelo projeto)
* **Poetry** (gerenciador de pacotes e ambientes virtuais)
* **Git**

### <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTV4ZGFjc3VoZnJvbWs0YW00dXowMGk2OG0wcmVxcWtudmFxbm8xbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dv7sW46M17UQ36WVBT/giphy.gif" alt="dados_12_2" width="20" height="20" /> **Passo a Passo**:

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

# --- Configurações do Pipeline de IA (Etapas 4 e 5) ---
# DRY_RUN=true  -> Modo Simulação: apenas estima custos de tokens, não consome API e não grava no banco.
# DRY_RUN=false -> Modo Produção: executa o enriquecimento real e salva os dados.
DRY_RUN=true

# Quantidade de proposições pendentes a processar por lote/execução
BATCH_SIZE=10

# Modelo OpenAI escolhido (gpt-4o-mini é ~10x mais barato e ideal para os resumos)
MODELO_IA=gpt-4o-mini

# Etapa 5 — Classificação temática por embeddings
MODELO_EMBEDDING=text-embedding-3-small
LIMIAR_TEMA=0.20


# --- Configurações de Acesso e Sincronização do n8n ---
N8N_USER=admin
N8N_PASSWORD=bussola123
REPO_PATH=C:/Caminho/Ate/O/Projeto/Bussola-Publica-Pipeline-de-Inteligencia-Legislativa-com-IA

```

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
n8n/bussola_publica_ingestao_diaria.json
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

## <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExdGU3cXhzeHF5YmhsdmtxdzA1bGg1dWRwMWF6MmZjYWM5MjN2dTg1dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/AvSbLuJ4mVgpl4sG4M/giphy.gif" alt="dados_13" width="30" height="30" />  Estrutura de Pastas e Arquivos:

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
│   ├── Etapa4_Camada_IA.pdf       # Relatório de especificação da camada de IA
│   ├── Etapa5_Documentacao_Tecnica.md  # Etapa 5: decisões técnicas + prompts da IA
│   └── modelo_dados.md            # Modelo dimensional (tabelas e relacionamentos)
├── n8n/                           # Etapa 5: automação
│   ├── bussola_publica_ingestao_diaria.json          # Workflow n8n (ingestão 06h + digest)
│   ├── bussola_publica_ingestao_diaria_WINDOWS.json  # Variante para ambiente Windows
│   └── GUIA_IMPORTACAO_n8n.md     # Passo a passo de importação e credenciais
├── logs/                          # Logs de execução do pipeline
│   └── transformacao_20260528.log # Registro histórico de transformações
├── src/                           # Código-fonte principal do projeto
│   ├── __pycache__/
│   ├── _init_.py
│   ├── ai_layer.py                # Etapa 4: Integração com OpenAI (Resumos executivos)
│   ├── classificacao_tematica.py  # Etapa 5: Classificação temática (embeddings + cosseno)
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