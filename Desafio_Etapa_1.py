"""
=============================================================================
BUSSOLA PUBLICA - Projeto Integrador | Pos Tech Engenharia de Dados e IA
=============================================================================
Etapa 1: Exploracao da API da Camara dos Deputados

Objetivo : Entender a estrutura dos dados ANTES de construir o pipeline.
           Engenheiro que pula essa etapa, retrabalha o pipeline inteiro depois.

Boas praticas aplicadas (Nivelamento Xperiun / Prof. Iago Braz):
  - import requests + pandas
  - try/except com excecoes especificas (Timeout, ConnectionError, HTTPError)
  - response.status_code validado antes de processar
  - response.json() para converter resposta em dicionario Python
  - type() / len() / dado[0] para inspecionar o retorno da API
  - funcoes com return (nao apenas print)
  - timeout em todas as requisicoes
  - comentarios explicando cada decisao

API Base : https://dadosabertos.camara.leg.br/api/v2
Docs     : https://dadosabertos.camara.leg.br/swagger/api.html
=============================================================================
"""

# PASSO 1: Importar as bibliotecas necessarias
# requests -> para fazer as chamadas HTTP a API
# pandas   -> para transformar os dados em tabela (DataFrame) e inspecionar
import requests
import pandas as pd
from datetime import datetime, timedelta

# PASSO 2: Configuracao global
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

# Janela de 30 dias para filtrar proposicoes e votacoes
HOJE   = datetime.today()
INICIO = (HOJE - timedelta(days=30)).strftime("%Y-%m-%d")
FIM    = HOJE.strftime("%Y-%m-%d")


def busca_endpoint(endpoint, params=None):
    """
    Faz uma requisicao GET a API da Camara e retorna o JSON como dicionario.

    Trata 3 tipos de erro (Timeout, ConnectionError, HTTPError) -
    cada um com mensagem especifica, sem derrubar o restante do codigo.

    Parametros:
        endpoint (str): rota da API, ex: "/deputados"
        params   (dict): filtros opcionais, ex: {"itens": 5}

    Retorna:
        dict com os dados da API, ou None se houver erro.
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        # Sempre com timeout - sem ele o script pode travar para sempre em producao
        resposta = requests.get(url, params=params, timeout=15)

        # raise_for_status() lanca HTTPError se o status nao for 2
        resposta.raise_for_status()

        # .json() converte a resposta (texto) para dicionario Python
        return resposta.json()

    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] Servidor demorou mais de 15s: {endpoint}")

    except requests.exceptions.ConnectionError:
        print(f"[CONEXAO] Sem internet ou servico fora do ar: {endpoint}")

    except requests.exceptions.HTTPError as e:
        print(f"[HTTP ERROR] O servico retornou um erro: {e}")

    except Exception as e:
        print(f"[ERRO] Inesperado: {e}")

    return None  # retorna None para que o codigo chamador possa tratar


def inspecionar_dados(dados, nome_endpoint):
    """
    Inspeciona o retorno da API: tipo, quantidade e primeiro registro.

    Segue o padrao do capitulo 8 do curso:
      print(type(dados)) -> print(len(dados)) -> print(dados[0])

    Esse e o primeiro passo - entender o que a API esta devolvendo.
    """
    print(f"\n{'='*60}")
    print(f"  ENDPOINT: {nome_endpoint}")
    print(f"{'='*60}")

    if dados is None:
        print("  Nenhum dado retornado (erro na requisicao).")
        return []

    itens = dados.get("dados", [])

    # As tres inspecoes fundamentais - ensinadas no capitulo de APIs
    print(f"  Tipo do retorno  : {type(itens)}")
    print(f"  Quantidade itens : {len(itens)}")

    if itens:
        print(f"\n  Primeiro registro (dados[0]):")
        primeiro = itens[0]
        for chave, valor in primeiro.items():
            print(f"    {chave:25s}: {str(valor)[:70]}")

    # Links de paginacao - importante identificar na exploracao
    links = dados.get("links", [])
    rels  = [l.get("rel") for l in links if isinstance(l, dict)]
    print(f"\n  Links paginacao  : {rels}")

    return itens


# =============================================================================
# EXPLORACAO DOS ENDPOINTS
# Para cada endpoint: busca -> inspeciona -> levanta hipoteses
# Padrao identico ao projeto pratico do capitulo 8 do curso.
# =============================================================================

print("\nINICIANDO EXPLORACAO DA API DA CAMARA DOS DEPUTADOS")
print(f"Periodo: {INICIO} -> {FIM}\n")


# --- 1. /deputados -----------------------------------------------------------
dados_deputados = busca_endpoint(
    "/deputados",
    params={"itens": 5, "ordem": "ASC", "ordenarPor": "nome"}
)
itens_deputados = inspecionar_dados(dados_deputados, "/deputados")

print("""
  CAMPOS UTEIS IDENTIFICADOS:
    id           -> chave primaria (usar para buscar detalhes)
    nome         -> nome parlamentar
    siglaPartido -> partido (join com tabela partidos)
    siglaUf      -> estado representado
    urlFoto      -> imagem (enriquecimento opcional)

  HIPOTESES:
    H1. Quantos deputados por partido? (siglaPartido -> COUNT)
    H2. Qual UF tem mais deputados? (siglaUf -> COUNT)
""")


# --- 2. /deputados/{id} - detalhe --------------------------------------------
# Seguindo o padrao: pega o id do primeiro item retornado e busca o detalhe
if itens_deputados:
    id_dep = itens_deputados[0]["id"]
    dados_dep_detalhe = busca_endpoint(f"/deputados/{id_dep}")
    inspecionar_dados(dados_dep_detalhe, f"/deputados/{id_dep} (detalhe)")
    print("""
  CAMPOS EXTRAS NO DETALHE:
    cpf              -> CPF do deputado
    dataNascimento   -> para analise demografica
    escolaridade     -> perfil educacional
    situacao         -> ativo, licenciado, etc.
""")


# --- 3. /proposicoes ---------------------------------------------------------
dados_props = busca_endpoint(
    "/proposicoes",
    params={
        "dataInicio":  INICIO,
        "dataFim":     FIM,
        "itens":       5,
        "ordem":       "DESC",
        "ordenarPor":  "id"
    }
)
itens_props = inspecionar_dados(dados_props, "/proposicoes (ultimos 30 dias)")

print("""
  CAMPOS UTEIS IDENTIFICADOS:
    id               -> chave primaria
    siglaTipo        -> PL, PEC, MPV, PDL, etc.
    numero / ano     -> identificacao publica
    ementa           -> TEXTO PRINCIPAL para classificacao com IA
    dataApresentacao -> quando entrou na Camara

  HIPOTESES:
    H3. Quantas proposicoes por tipo/semana? (siglaTipo -> COUNT)
    H4. Quais temas dominam? (NLP na ementa)
    H5. Quais deputados mais apresentam? (cruzar com /autores)
""")


# --- 4. /proposicoes/{id}/autores --------------------------------------------
if itens_props:
    id_prop = itens_props[0]["id"]
    dados_autores = busca_endpoint(f"/proposicoes/{id_prop}/autores")
    inspecionar_dados(dados_autores, f"/proposicoes/{id_prop}/autores")


# --- 5. /votacoes ------------------------------------------------------------
dados_vots = busca_endpoint(
    "/votacoes",
    params={
        "dataInicio":  INICIO,
        "dataFim":     FIM,
        "itens":       5,
        "ordem":       "DESC",
        "ordenarPor":  "dataHoraRegistro"
    }
)
itens_vots = inspecionar_dados(dados_vots, "/votacoes (ultimos 30 dias)")

print("""
  CAMPOS UTEIS IDENTIFICADOS:
    id                -> chave primaria da votacao
    descricao         -> o que foi votado
    dataHoraRegistro  -> quando ocorreu
    aprovacao         -> 1=aprovado, 0=rejeitado
    proposicaoObjeto  -> proposicao vinculada

  HIPOTESES:
    H6. Qual partido mais aprova/rejeita? (tipoVoto por siglaPartido)
    H7. Quais deputados mais se absteem?
""")


# --- 6. /votacoes/{id}/votos - votos individuais -----------------------------
if itens_vots:
    id_vot = itens_vots[0]["id"]
    dados_votos = busca_endpoint(f"/votacoes/{id_vot}/votos")
    itens_votos = inspecionar_dados(dados_votos, f"/votacoes/{id_vot}/votos")

    if itens_votos:
        print("\n  Amostra dos votos (padrao lista + append do curso):")
        nomes      = []   # lista vazia
        partidos   = []
        tipos_voto = []

        for voto in itens_votos[:5]:
            dep = voto.get("deputado_", {})
            nomes.append(dep.get("nome", "N/A"))          # append acumula
            partidos.append(dep.get("siglaPartido", "N/A"))
            tipos_voto.append(voto.get("tipoVoto", "N/A"))

        # dict -> DataFrame (padrao do curso, Capitulo 7.4)
        amostra = pd.DataFrame({
            "deputado": nomes,
            "partido":  partidos,
            "voto":     tipos_voto
        })
        print(amostra.to_string(index=False))


# --- 7. /partidos ------------------------------------------------------------
dados_part = busca_endpoint(
    "/partidos",
    params={"itens": 5, "ordem": "ASC", "ordenarPor": "sigla"}
)
inspecionar_dados(dados_part, "/partidos")

print("""
  CAMPOS UTEIS IDENTIFICADOS:
    id    -> chave primaria (join com deputados)
    sigla -> identificador curto (PT, PL, UNIAO...)
    nome  -> nome completo

  HIPOTESE:
    H8. Quais partidos apresentam mais proposicoes aprovadas?
""")


# =============================================================================
# DECISAO FINAL - Estrutura de tabelas para o pipeline ETL
# =============================================================================
print("""
+------------------------------------------------------------------+
|  DECISAO: TABELAS E CAMPOS QUE VAO PARA O PIPELINE (Etapa 2)    |
+------------------------------------------------------------------+
|  deputados           -> id, nome, siglaPartido, siglaUf          |
|  proposicoes         -> id, siglaTipo, numero, ano, ementa,      |
|                          dataApresentacao                         |
|  proposicoes_autores -> id_proposicao, id_dep, nome, codTipo     |
|  votacoes            -> id, descricao, dataHoraRegistro,         |
|                          aprovacao                               |
|  votos               -> id_votacao, id_dep, nome_dep, tipoVoto   |
|  partidos            -> id, sigla, nome                          |
+------------------------------------------------------------------+
|  PROXIMO PASSO -> Etapa 2: Extracao completa com OOP + pandas    |
+------------------------------------------------------------------+
""")