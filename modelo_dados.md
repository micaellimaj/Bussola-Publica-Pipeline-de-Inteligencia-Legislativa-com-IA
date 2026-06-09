# Modelo de Dados — Bússola Pública (Supabase / PostgreSQL)

Modelo estrela: tabelas **Dimensão** (`dim_`) e **Fato** (`fato_`). Colunas marcadas com **[IA]** são adicionadas pela camada de Inteligência Artificial (Etapa 4/5) via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, sem recriar as tabelas.

## Dimensões

### `dim_deputados`
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id_deputado | int8 | PK | Identificador do deputado na API. |
| nome | text | | Nome parlamentar. |
| sigla_partido | text | | Partido atual. |
| sigla_uf | text | | UF de eleição. |
| id_legislatura | int8 | | Legislatura atual. |
| url_foto | text | | Foto oficial. |
| uri | text | | Endpoint do deputado na API. |

### `dim_partidos`
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id_partido | int8 | PK | Identificador do partido. |
| sigla | text | | Sigla oficial. |
| nome | text | | Nome completo. |
| uri | text | | Endpoint do partido na API. |

## Fatos

### `fato_proposicoes` (entidade central de análise)
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id_proposicao | int8 | PK | Identificador da proposição. |
| sigla_tipo | text | | Tipo (PL, PEC, MPV…). |
| numero | int8 | | Número no ano. |
| ano | int8 | | Ano de apresentação. |
| ementa | text | | Texto oficial da ementa. |
| data_apresentacao | timestamptz | | Data de protocolo. |
| created_at | timestamptz | | Inserção no banco. |
| resumo_executivo | text | **[IA]** | Resumo gerado via GPT-4o-mini. |
| data_resumo | timestamptz | **[IA]** | Quando o resumo foi gerado. |
| **tema** | text | **[IA · NOVO Etapa 5]** | Tema classificado por embeddings. |
| **tema_score** | float8 | **[IA · NOVO Etapa 5]** | Similaridade de cosseno (0–1). |
| **data_tema** | timestamptz | **[IA · NOVO Etapa 5]** | Quando o tema foi classificado. |

### `fato_proposicoes_autores` (associativa)
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id_proposicao | int8 | FK → fato_proposicoes | Proposição. |
| nome_autor | text | | Autor (parlamentar/órgão). |
| tipo_autor | text | | Categoria do autor. |
| uri_autor | text | | Endpoint do autor. |

### `fato_votacoes`
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id_votacao | text | PK | ID alfanumérico da votação. |
| descricao | text | | O que foi votado. |
| data_hora_registro | timestamptz | | Momento da sessão. |
| aprovacao | int2 | | Aprovado (1) / não (0). |
| proposicao_objeto | text | | Matéria que originou a votação. |
| created_at | timestamptz | | Inserção no banco. |

### `fato_votos`
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id | int4 | PK identity | Chave sequencial. |
| id_votacao | varchar | NOT NULL → fato_votacoes | Votação correspondente. |
| tipo_voto | varchar | | Sim / Não / Abstenção / Obstrução. |
| id_deputado | int4 | → dim_deputados | Parlamentar que votou. |
| created_at | timestamptz | | Inserção no banco. |

## Relacionamentos
- `fato_proposicoes` 1—N `fato_proposicoes_autores` (por `id_proposicao`).
- `fato_votacoes` 1—N `fato_votos` (por `id_votacao`).
- `fato_votos` N—1 `dim_deputados` (por `id_deputado`).
- `dim_deputados` N—1 `dim_partidos` (por `sigla_partido` / `sigla`).
- `fato_proposicoes.tema` alimenta os alertas/digest do workflow n8n da Etapa 5.
