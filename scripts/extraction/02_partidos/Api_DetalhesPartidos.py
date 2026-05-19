import requests
import pandas as pd
import sqlite3
import time

def realizar_eda(df, nome_tabela):
    print("\n" + "="*40)
    print(f"📊 RESUMO EXPLORATÓRIO: {nome_tabela}")
    print("="*40)
    print(f"• Linhas: {df.shape[0]} | Colunas: {df.shape[1]}")
    print(f"• Duplicatas: {df.duplicated().sum()}")
    print("\n• Valores nulos por coluna:")
    print(df.isnull().sum())
    print("-" * 40)

def automacao_membros_partidos():
    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    try:
        # Busca IDs da tabela de partidos ja existente
        ids_partidos = pd.read_sql("SELECT id FROM tb_partidos", conn)['id'].tolist()
    except:
        print("❌ Tabela 'tb_partidos' não encontrada.")
        return

    lista_membros = []

    print(f"🚀 Coletando membros de {len(ids_partidos)} partidos...")

    for i, id_partido in enumerate(ids_partidos[:10]):
        print(f"📡 Partido ID {id_partido} ({i+1}/10)")
        url = f"https://dadosabertos.camara.leg.br/api/v2/partidos/{id_partido}/membros"
        res = requests.get(url)
        
        if res.status_code == 200:
            dados = res.json()["dados"]
            for m in dados:
                m["id_partido"] = id_partido
                lista_membros.append(m)
        time.sleep(0.1)

    if lista_membros:
        df_membros = pd.DataFrame(lista_membros)
        realizar_eda(df_membros, "TB_PARTIDOS_MEMBROS")
        df_membros.to_sql("tb_partidos_membros", conn, if_exists="replace", index=False)

    conn.close()
    print("✅ Banco atualizado com membros dos partidos.")

if __name__ == "__main__":
    automacao_membros_partidos()