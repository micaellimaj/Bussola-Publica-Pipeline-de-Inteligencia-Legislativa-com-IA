import requests
import pandas as pd

# PARTIDOS

url_partidos = "https://dadosabertos.camara.leg.br/api/v2/partidos"

params = {
    "dataInicio": "2026-04-01",
    "dataFim": "2026-04-10",
    "pagina": 1,
    "itens": 10,
    "ordenarPor": "id",
    "ordem": "ASC"
}

# FAZ A CHAMADA DA URL
response_partidos= requests.get(url_partidos, params=params)

# VERFICA SE RETORNOU "STATUS 200"
if response_partidos.status_code == 200:
    dados_partidos = response_partidos.json()["dados"]
    print("200 - OK")

#print(response_partidos.json())

# PASSA O RETORNO DA API PARA O DATA FRAME
df_partidos = pd.DataFrame(dados_partidos)

# SELECIONA OS COLUNAS
df_partidos = df_partidos[
    [
        "id",
        "sigla",
        "nome",
        "uri"
    ]
]

# IMPRIME O DATA FRAME
print(df_partidos)
# IMPRIME O JSON
print(dados_partidos)