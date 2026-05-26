
import requests
import pandas as pd

# PROPOSICOES

url_proposicoes = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

params = {
    "dataInicio": "2026-04-01",
    "dataFim": "2026-04-10",
    "pagina": 1,
    "itens": 10,
    "ordenarPor": "id",
    "ordem": "ASC"
}

# FAZ A CHAMADA DA URL
response_proposicoes= requests.get(url_proposicoes, params=params)

# VERFICA SE RETORNOU "STATUS 200"
if response_proposicoes.status_code == 200:
    dados_proposicoes = response_proposicoes.json()["dados"]
    print("200 - OK")

#print(response_proposicoes.json())

# PASSA O RETORNO DA API PARA O DATA FRAME
df_proposicoes = pd.DataFrame(dados_proposicoes)

# SELECIONA OS COLUNAS
df_proposicoes = df_proposicoes[
    [
        "id",
        "uri",
        "siglaTipo",
        "codTipo",
        "numero",
        "ano",
        "ementa",
        "dataApresentacao"
    ]
]

# IMPRIME O DATA FRAME
print(df_proposicoes)
# IMPRIME O JSON
print(dados_proposicoes)