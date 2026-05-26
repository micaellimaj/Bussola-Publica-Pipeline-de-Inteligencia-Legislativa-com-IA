import requests
import pandas as pd

# URL DA API DE DEPUTADOS
url = "https://dadosabertos.camara.leg.br/api/v2/deputados"

# FAZ A CHAMADA DA URL
response_deputados = requests.get(url)

# VERFICA SE RETORNOU "STATUS 200"
if response_deputados.status_code == 200:
    dados_deputados = response_deputados.json()["dados"]
    print("200 - OK")

else:
    print(f"Erro: {response_deputados.status_code}")

# PASSA O RETORNO DA API PARA O DATA FRAME
df_deputados = pd.DataFrame(dados_deputados)

# SELECIONA OS COLUNAS
df_deputados = df_deputados[
    [
        "id",
        "nome",
        "siglaPartido",
        "siglaUf",
        "idLegislatura",
        "urlFoto",
        "email"
    ]
]

# IMPRIME O DATA FRAME
print(df_deputados)
# IMPRIME O JSON
print(dados_deputados)






