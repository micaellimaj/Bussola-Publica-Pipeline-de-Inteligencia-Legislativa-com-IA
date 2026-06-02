---
name: engdados-pipeline
description: >
  Guia de boas práticas para construção de pipelines de dados em Python, seguindo o
  nivelamento do MBA em Business Intelligence & Analytics 360 (Xperiun / Prof. Iago Braz).
  Use esta skill SEMPRE que o usuário pedir para construir, revisar ou melhorar scripts
  Python de extração de dados, consumo de APIs, ETL, pipeline, automação de dados,
  tratamento de erros com try/except, paginação de APIs, OOP para dados, ou qualquer
  tarefa de engenharia de dados em Python — mesmo que não mencione explicitamente o curso
  ou a Xperiun. Ative também quando o usuário mencionar requests, pandas, DataFrame,
  Câmara dos Deputados, dados abertos ou projetos de Pós Tech em Engenharia de Dados.
---

# Guia de Boas Práticas — Engenharia de Dados com Python
**Referência:** MBA BI & Analytics 360 — Xperiun | Prof. Iago Braz
**Escopo:** Nivelamento Python + Consumo de APIs + POO

---

## 1. Princípios que norteiam tudo

> "Engenheiro de dados que pula a exploração retrabalha o pipeline inteiro depois.
> Curiosidade primeiro, código depois." — Prof. Iago Braz

Três pilares do curso que devem guiar qualquer script:

1. **Explorar antes de codar** — inspecionar a API com `type()`, `len()`, `dados[0]` antes de montar o extrator
2. **Salvar o bruto antes de transformar** — JSON em disco = seguro para reprocessar sem bater na API novamente
3. **Separar responsabilidades** — cada classe/função faz uma única coisa bem feita

---

## 2. Padrões fundamentais de Python

### 2.1 Variáveis e tipos
```python
nome     = "Iago"    # str
idade    = 30        # int
altura   = 1.80      # float
ativo    = True      # bool
```
Use `type()` para inspecionar qualquer dado recebido de API antes de processar.

### 2.2 Estruturas de dados
| Estrutura | Sintaxe | Mutável | Uso típico |
|-----------|---------|---------|------------|
| Lista     | `[]`    | ✅      | Acumular registros em loops |
| Tupla     | `()`    | ❌      | Dados fixos (coordenadas, credenciais) |
| Dicionário| `{}`    | ✅      | JSON da API → estrutura de tabela |

### 2.3 O padrão lista vazia → for → append (uso obrigatório em pipelines)
```python
# ✅ CORRETO — acumula todos os valores
registros = []                    # lista vazia antes do loop
for item in dados_da_api:
    registros.append(item["nome"])  # append dentro do for

# ❌ ERRADO — sobrescreve a cada volta, só fica o último
for item in dados_da_api:
    registro = item["nome"]       # variável simples perde dados!
```

### 2.4 Dicionário → DataFrame (padrão Pandas)
```python
import pandas as pd

# Cada chave = nome da coluna; cada lista = dados da coluna
preparar_base = {
    "nome":    nomes,
    "partido": partidos,
    "voto":    tipos_voto
}
df = pd.DataFrame(preparar_base)
df.to_csv("saida.csv", index=False)
```

---

## 3. Funções com return (não apenas print)

```python
# ✅ CORRETO — retorna valor para uso posterior
def buscar_dados(endpoint):
    resposta = requests.get(endpoint, timeout=15)
    return resposta.json()           # return permite capturar e reusar

resultado = buscar_dados("/deputados")  # capturado na variável

# ❌ ERRADO — print exibe, mas não retorna nada
def buscar_dados_errado(endpoint):
    resposta = requests.get(endpoint)
    print(resposta.json())           # None é retornado — não dá pra guardar
```

---

## 4. Consumo de APIs com requests

### 4.1 Template de requisição com boas práticas
```python
import requests

def get_api(url, params=None):
    """
    Toda requisição deve ter:
      - timeout → evita script travado em produção
      - raise_for_status() → detecta erros 4xx/5xx
      - try/except específico → mensagem clara por tipo de erro
    """
    try:
        resposta = requests.get(url, params=params, timeout=15)
        resposta.raise_for_status()   # lança HTTPError se não for 2xx
        return resposta.json()        # dict Python pronto para uso

    except requests.exceptions.Timeout:
        print("❌ Timeout: servidor não respondeu em 15s")

    except requests.exceptions.ConnectionError:
        print("❌ Sem conexão com a internet ou serviço fora do ar")

    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP: {e}")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    return None
```

### 4.2 Códigos HTTP que todo engenheiro deve conhecer
| Código | Significado | O que fazer |
|--------|-------------|-------------|
| 200    | Sucesso     | Processar normalmente |
| 400    | Requisição inválida | Verificar parâmetros |
| 401    | Não autorizado | Verificar API Key/token |
| 403    | Proibido | Verificar permissões |
| 404    | Não encontrado | Verificar endpoint/URL |
| 500    | Erro no servidor | Aguardar e tentar novamente |

### 4.3 Paginação com while (quando não se sabe quantas páginas há)
```python
import time

def get_paginado(endpoint, base_url, params=None):
    """
    Use while (não for) quando não sabe de antemão quantas páginas existem.
    O while para quando: (a) página vazia, ou (b) sem link 'next'.
    time.sleep() é obrigatório para respeitar rate limit.
    """
    params  = params or {}
    params["itens"] = 100      # máximo por página
    pagina  = 1
    todos   = []               # lista vazia — padrão do curso

    while True:
        params["pagina"] = pagina
        resposta = get_api(f"{base_url}{endpoint}", params.copy())

        if not resposta or not resposta.get("dados"):
            break

        for item in resposta["dados"]:
            todos.append(item)         # append acumula

        # Verifica link "next" para saber se tem próxima página
        links    = resposta.get("links", [])
        tem_next = any(l.get("rel") == "next" for l in links if isinstance(l, dict))

        if not tem_next:
            break

        pagina += 1
        time.sleep(0.3)        # pausa educada — não bombardeia o servidor

    return todos
```

### 4.4 Boas práticas obrigatórias de APIs
- **Sempre use `timeout`** — sem timeout, scripts ficam travados em produção
- **Sempre use `time.sleep()`** entre chamadas em loop — respeite o rate limit
- **Nunca deixe credenciais no código** — use variáveis de ambiente (`.env` + `python-dotenv`)
- **Versione as rotas** — `/api/v1/`, `/api/v2/` para não quebrar usuários existentes
- **Registre logs** — `logging.FileHandler` para rastrear erros em produção

---

## 5. Programação Orientada a Objetos para pipelines

### 5.1 Conceitos-chave
- **Classe** → o molde (a "planta da casa")
- **Objeto** → a instância concreta (a "casa construída")
- **`__init__`** → configuração automática no nascimento do objeto
- **`self`** → apontamento único de cada objeto — sem ele o Python não sabe de qual instância estamos falando
- **Atributo** → dado guardado no objeto (`self.nome`, `self.saldo`)
- **Método** → ação da classe (`def depositar(self, valor)`)

### 5.2 Template de classe para extratores de dados
```python
class ExtractorBase:
    """Classe base: encapsula a lógica de HTTP. Só sabe buscar."""

    def __init__(self, base_url, headers):
        self.base_url = base_url     # self = identidade única do objeto
        self.headers  = headers

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            print(f"Timeout: {endpoint}")
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP: {e}")
        return None


class DeputadosExtractor(ExtractorBase):
    """Responsabilidade única: extrair deputados. Não sabe nada sobre votações."""

    def extrair(self):
        dados    = []
        pagina   = 1
        while True:
            resposta = self._get("/deputados", {"pagina": pagina, "itens": 100})
            if not resposta or not resposta.get("dados"):
                break
            for dep in resposta["dados"]:
                dados.append(dep)       # padrão lista + append
            # ... lógica de próxima página ...
            pagina += 1
            time.sleep(0.3)
        return dados


class PipelineService:
    """
    Responsabilidade: orquestrar e salvar.
    Não sabe nada de HTTP — só coordena e persiste.
    Análogo ao PedidoService do módulo de POO.
    """

    def __init__(self):
        self.dep_extractor = DeputadosExtractor(BASE_URL, HEADERS)

    def executar(self):
        deputados = self.dep_extractor.extrair()
        self._salvar_json(deputados, "data/raw/deputados.json")
        df = pd.DataFrame(deputados)        # dict → DataFrame — padrão curso
        print(df.head())

    def _salvar_json(self, dados, caminho):
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
```

### 5.3 Separação de responsabilidades (regra de ouro)
| Classe | Responsabilidade | Não faz |
|--------|-----------------|---------|
| `ExtractorBase` | Chamadas HTTP, retry, timeout | Nada de negócio |
| `DeputadosExtractor` | Lógica específica de deputados | Votações, partidos |
| `PipelineService` | Orquestrar, salvar JSON | HTTP direto |

> Se você precisa mudar a regra de desconto, muda só o Service.
> Se muda o endpoint da API, muda só o Extractor.
> Nada se quebra junto.

---

## 6. Anti-patterns que o curso ensina a evitar

| ❌ Errado | ✅ Certo |
|-----------|---------|
| Variável simples dentro do for (sobrescreve) | Lista vazia + append |
| `print()` em vez de `return` em funções | `return` para poder capturar e reusar |
| Sem `timeout` nas requisições | `timeout=15` obrigatório |
| Sem `try/except` | try/except com exceções específicas |
| Transformar sem salvar bruto antes | Salvar JSON → depois transformar |
| API key hardcoded no código | `.env` + `os.getenv()` |
| Assumir que a primeira página é tudo | Loop de paginação completo |
| Loop infinito com while sem saída | while com condição de parada clara |

---

## 7. Checklist antes de entregar qualquer script de pipeline

- [ ] Bibliotecas importadas: `requests`, `pandas`, `json`, `time`, `logging`, `pathlib`
- [ ] Todas as requisições com `timeout`
- [ ] `try/except` com pelo menos Timeout, ConnectionError, HTTPError
- [ ] Paginação com while + condição de saída + `time.sleep()`
- [ ] Padrão lista vazia → for → append (nunca variável simples dentro do loop)
- [ ] Funções com `return` (não apenas print)
- [ ] JSON bruto salvo antes de qualquer transformação
- [ ] Conversão final: dict → `pd.DataFrame()` para inspecionar
- [ ] Classes com responsabilidades separadas (HTTP / lógica de negócio / orquestração)
- [ ] Logging ativo para rastrear execução