import requests
import pandas as pd
import sqlite3

url_partidos = "https://dadosabertos.camara.leg.br/api/v2/partidos"
params = {
    "dataInicio": "2026-04-01", "dataFim": "2026-04-10",
    "pagina": 1, "itens": 100, "ordenarPor": "id", "ordem": "ASC"
}

response = requests.get(url_partidos, params=params)

if response.status_code == 200:
    df_partidos = pd.DataFrame(response.json()["dados"])
    df_partidos = df_partidos[["id", "sigla", "nome", "uri"]]

    print("\n📊 EDA - PARTIDOS")
    print(f"Linhas: {len(df_partidos)} | Duplicatas: {df_partidos.duplicated().sum()}")
    print("Nulos por coluna:\n", df_partidos.isnull().sum())

    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    df_partidos.to_sql("tb_partidos", conn, if_exists="replace", index=False)
    conn.close()
    print("✅ Tabela 'tb_partidos' salva.")