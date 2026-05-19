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
    
    if 'tema' in df.columns:
        print("\n• Temas mais frequentes encontrados:")
        print(df['tema'].value_counts().head(5))
    
    print("-" * 40)

def automacao_detalhes_proposicoes():
    # 1. Conexão com o banco compartilhado
    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    
    try:
        # Busca IDs da tabela de proposições
        ids_proposicoes = pd.read_sql("SELECT id FROM tb_proposicoes", conn)['id'].tolist()
    except Exception as e:
        print(f"❌ Erro ao ler tabela 'tb_proposicoes': {e}")
        return

    lista_autores = []
    lista_temas = []

    print(f"🚀 Iniciando coleta detalhada para {len(ids_proposicoes)} proposições...")

    # 2. Loop pelos IDs (Limitado aos 10 primeiros para teste)
    for i, id_prop in enumerate(ids_proposicoes[:10]):
        print(f"📡 Processando Proposição {id_prop} ({i+1}/10)")

        # --- COLETA DE AUTORES ---
        url_autores = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_prop}/autores"
        res_aut = requests.get(url_autores)
        if res_aut.status_code == 200:
            dados = res_aut.json()["dados"]
            for a in dados:
                a["id_proposicao"] = id_prop
                lista_autores.append(a)

        # --- COLETA DE TEMAS ---
        url_temas = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_prop}/temas"
        res_tem = requests.get(url_temas)
        if res_tem.status_code == 200:
            dados = res_tem.json()["dados"]
            for t in dados:
                t["id_proposicao"] = id_prop
                lista_temas.append(t)

        time.sleep(0.1)

    # 3. Processamento e Salvamento
    # Tabela de Autores
    if lista_autores:
        df_autores = pd.DataFrame(lista_autores)
        realizar_eda(df_autores, "TB_PROPOSICOES_AUTORES")
        df_autores.to_sql("tb_proposicoes_autores", conn, if_exists="replace", index=False)

    # Tabela de Temas
    if lista_temas:
        df_temas = pd.DataFrame(lista_temas)
        realizar_eda(df_temas, "TB_PROPOSICOES_TEMAS")
        df_temas.to_sql("tb_proposicoes_temas", conn, if_exists="replace", index=False)

    conn.close()
    print("\n✅ Automação de Proposições finalizada no banco 'dados_camara.db'!")

if __name__ == "__main__":
    automacao_detalhes_proposicoes()