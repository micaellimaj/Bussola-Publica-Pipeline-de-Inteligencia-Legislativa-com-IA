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
| created_at | timestamptz | | Data/hora da PRIMEIRA ingestão do registro (não muda em re-execuções). |
| resumo_executivo | text | **[IA]** | Resumo gerado via GPT-4o-mini. |
| data_resumo | timestamptz | **[IA]** | Quando o resumo foi gerado. |
| **tema** | text | **[IA · NOVO Etapa 5]** | Tema classificado por embeddings. |
| **tema_score** | float8 | **[IA · NOVO Etapa 5]** | Similaridade de cosseno (0–1). Coluna prevista no modelo; na execução atual está `NULL` para todos os registros (ver nota abaixo). |
| **data_tema** | timestamptz | **[IA · NOVO Etapa 5]** | Quando o tema foi classificado. |

> **Nota sobre `tema_score`:** o código (`classificacao_tematica.py`) calcula o score
> e grava `tema`, `tema_score` e `data_tema` juntos no mesmo `UPDATE`. Na carga
> atual do banco, `tema` está preenchido para as proposições classificadas, mas
> `tema_score` ficou `NULL` em todas as linhas — indício de que essa execução foi
> feita com uma versão anterior do script (antes da gravação do score) ou que o
> `UPDATE` não persistiu essa coluna. Não bloqueia o uso de `tema` no
> digest/alertas do n8n; fica registrado como ponto de atenção para a próxima
> reexecução da classificação temática.

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
| created_at | timestamptz | | Data/hora da PRIMEIRA ingestão do registro (não muda em re-execuções). |

### `fato_votos`
| Campo | Tipo | Restrição | Descrição |
|---|---|---|---|
| id | int4 | PK identity | Chave sequencial. |
| id_votacao | varchar | NOT NULL → fato_votacoes | Votação correspondente. |
| tipo_voto | varchar | | Sim / Não / Abstenção / Obstrução. |
| id_deputado | int4 | → dim_deputados | Parlamentar que votou. |
| created_at | timestamptz | | Data/hora da PRIMEIRA ingestão do registro (não muda em re-execuções). |

## Relacionamentos
- `fato_proposicoes` 1—N `fato_proposicoes_autores` (por `id_proposicao`).
- `fato_votacoes` 1—N `fato_votos` (por `id_votacao`).
- `fato_votos` N—1 `dim_deputados` (por `id_deputado`).
- `dim_deputados` N—1 `dim_partidos` (por `sigla_partido` / `sigla`).
- `fato_proposicoes.tema` alimenta os alertas/digest do workflow n8n da Etapa 5.

## Estratégia de carga (Etapa 3 — `transformacao.py`)

| Tabela | Modo | Por quê |
|---|---|---|
| `dim_deputados`, `dim_partidos` | `TRUNCATE` + reload (`carregar`) | São catálogos completos devolvidos do zero pela API em toda execução — não há histórico a preservar. |
| `fato_proposicoes`, `fato_votacoes` | **UPSERT** (`carregar_upsert`) — `INSERT ... ON CONFLICT (pk) DO UPDATE` | Registro novo → `INSERT` com `created_at = now()`. Registro já existente → `UPDATE` dos campos vindos da API, **sem tocar** em `created_at` nem nas colunas de IA (`resumo_executivo`, `tema`, ...). |
| `fato_proposicoes_autores`, `fato_votos` | **DELETE + INSERT escopado** (`carregar_incremental_assoc`) | Sem PK próprio. Apaga só os registros associados aos `id_proposicao`/`id_votacao` do lote atual e reinsere — preserva associações de execuções anteriores. |

**Antes (v1):** todas as tabelas usavam `if_exists="replace"` (TRUNCATE CASCADE + reinsere tudo). Isso fazia com que **toda execução zerasse `created_at` da tabela inteira** (todas as linhas ganhavam o mesmo timestamp), invalidando o filtro `created_at >= NOW() - INTERVAL '24h'` usado no digest do n8n (que passava a contar a tabela toda como "novas") e impedia o banco de **acumular** histórico além da janela `EXTRACAO_DIAS` da última execução.

**Agora (v2):** `carregar_upsert`/`carregar_incremental_assoc` tornam a carga idempotente e cumulativa — rodar o pipeline diariamente (ou várias vezes) faz o banco **crescer**, e `created_at` reflete a data real da primeira ingestão de cada proposição/votação. Os helpers `_garantir_created_at` e `_garantir_pk` aplicam `ALTER TABLE ... ADD COLUMN/PRIMARY KEY IF NOT EXISTS` de forma defensiva, então o pipeline também funciona em um Supabase novo, criado do zero.

### Backfill de 30 dias (entregável "banco com ≥ 30 dias de dados")

Para popular a janela de 30 dias sem esperar 30 dias de execuções diárias, rode uma vez com janela maior:

```bash
EXTRACAO_DIAS=30 poetry run python main.py
```

Como a carga agora é cumulativa (upsert), essa execução soma-se às anteriores em vez de substituí-las. Para evidenciar no print do Supabase, use:

```sql
SELECT MIN(data_apresentacao) AS mais_antiga,
       MAX(data_apresentacao) AS mais_recente,
       COUNT(*) AS total
FROM fato_proposicoes;
```

Evidência (print): `05_automacao_ia/prints/supabase_30dias.jpg` — execução real em 14/06/2026
retornou `mais_antiga = 2003-05-21`, `mais_recente = 2026-06-12`, `total = 4304`, ou seja, a
cobertura de `data_apresentacao` já excede em muito os 30 dias exigidos.

## Decisão de escopo: tabela `despesas` (cota parlamentar)

O desafio cita `despesas` como exemplo de tabela fato adicional (cota parlamentar
por deputado). Optamos por **não incluí-la** neste modelo: o produto da Bússola
Pública está centrado em `fato_proposicoes` (tema + resumo executivo) e
`fato_votacoes`/`fato_votos`, que são o que alimenta o digest e os alertas da
Etapa 5. Despesas não compõem nenhuma saída atual do pipeline.

Caso seja incorporada futuramente, o desenho seria direto: `fato_despesas`
(`id_deputado` FK → `dim_deputados`, `ano`, `mes`, `tipo_despesa`, `valor_liquido`,
`nome_fornecedor`, `data_documento`), carregada com a mesma estratégia de
`carregar_upsert` usando `(id_deputado, ano, mes, tipo_despesa, nome_fornecedor,
data_documento)` como chave de deduplicação.
