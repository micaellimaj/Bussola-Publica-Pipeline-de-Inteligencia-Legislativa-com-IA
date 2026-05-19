import requests
import pandas as pd
import sqlite3

url_votacoes = "https://dadosabertos.camara.leg.br/api/v2/votacoes"
params = {
    "dataInicio": "2026-04-01", "dataFim": "2026-04-10",
    "pagina": 1, "itens": 100, "ordenarPor": "id", "ordem": "ASC"
}

response = requests.get(url_votacoes, params=params)

if response.status_code == 200:
    df_votacoes = pd.DataFrame(response.json()["dados"])
    colunas = ["id", "data", "dataHoraRegistro", "descricao", "siglaOrgao", "aprovacao"]
    # Filtramos as colunas existentes para evitar erro caso a API mude
    df_votacoes = df_votacoes[[c for c in colunas if c in df_votacoes.columns]]

    print("\n📊 EDA - VOTAÇÕES")
    print(f"Linhas: {len(df_votacoes)}")
    if 'aprovacao' in df_votacoes.columns:
        print("\nStatus de Aprovação (1=Sim, 0=Não, -1=Outros):")
        print(df_votacoes['aprovacao'].value_counts())

    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    df_votacoes.to_sql("tb_votacoes", conn, if_exists="replace", index=False)
    conn.close()
    print("✅ Tabela 'tb_votacoes' salva.")