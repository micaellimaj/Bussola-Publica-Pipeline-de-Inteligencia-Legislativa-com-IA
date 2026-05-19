import requests
import pandas as pd
import sqlite3

url_proposicoes = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
params = {
    "dataInicio": "2026-04-01", "dataFim": "2026-04-10",
    "pagina": 1, "itens": 100, "ordenarPor": "id", "ordem": "ASC"
}

response = requests.get(url_proposicoes, params=params)

if response.status_code == 200:
    df_proposicoes = pd.DataFrame(response.json()["dados"])
    colunas = ["id", "uri", "siglaTipo", "codTipo", "numero", "ano", "ementa", "dataApresentacao"]
    df_proposicoes = df_proposicoes[colunas]

    print("\n📊 EDA - PROPOSIÇÕES")
    print(f"Linhas: {len(df_proposicoes)} | Nulos na Ementa: {df_proposicoes['ementa'].isnull().sum()}")
    print("\nTipos mais comuns de proposição:")
    print(df_proposicoes['siglaTipo'].value_counts().head())

    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    df_proposicoes.to_sql("tb_proposicoes", conn, if_exists="replace", index=False)
    conn.close()
    print("✅ Tabela 'tb_proposicoes' salva.")