import requests
import pandas as pd

# VOTACOES

url_votacoes = "https://dadosabertos.camara.leg.br/api/v2/votacoes"

params = {
    "dataInicio": "2026-04-01",
    "dataFim": "2026-04-10",
    "pagina": 1,
    "itens": 10,
    "ordenarPor": "id",
    "ordem": "ASC"
}

# FAZ A CHAMADA DA URL
response_votacoes= requests.get(url_votacoes, params=params)

# VERFICA SE RETORNOU "STATUS 200"
if response_votacoes.status_code == 200:
    dados_votacoes = response_votacoes.json()["dados"]
    print("200 - OK")

#print(response_votacoes.json())

# PASSA O RETORNO DA API PARA O DATA FRAME
df_votacoes = pd.DataFrame(dados_votacoes)

# SELECIONA OS COLUNAS
df_votacoes = df_votacoes[
    [
        "aprovacao",
        "data",
        "dataHoraRegistro",
        "descricao",
        "id",
        "proposicaoObjeto",
        "siglaOrgao",
        "uri",
        "uriEvento",
        "uriOrgao",
        "uriProposicaoObjeto"
    ]
]

# IMPRIME O DATA FRAME
print(df_votacoes)
# IMPRIME O JSON
print(dados_votacoes)