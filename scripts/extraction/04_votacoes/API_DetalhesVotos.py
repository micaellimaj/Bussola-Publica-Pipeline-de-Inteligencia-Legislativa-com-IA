import requests
import pandas as pd
import sqlite3
import time

def realizar_eda(df, nome_tabela):
    print("\n" + "="*40)
    print(f"📊 RESUMO EXPLORATÓRIO: {nome_tabela}")
    print("="*40)
    print(f"• Linhas: {df.shape[0]}")
    print(f"• Duplicatas: {df.duplicated().sum()}")
    
    if 'voto' in df.columns:
        print("\n• Distribuição de Votos:")
        print(df['voto'].value_counts())
    
    print("-" * 40)

def automacao_votos_votacoes():
    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    try:
        # Busca IDs da tabela de votacoes
        ids_votacoes = pd.read_sql("SELECT id FROM tb_votacoes", conn)['id'].tolist()
    except:
        print("❌ Tabela 'tb_votacoes' não encontrada.")
        return

    lista_votos = []

    print(f"🚀 Coletando votos de {len(ids_votacoes)} votações...")

    for i, id_votacao in enumerate(ids_votacoes[:5]): # Limitado a 5 (votos geram muitos dados)
        print(f"📡 Votação ID {id_votacao} ({i+1}/5)")
        url = f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{id_votacao}/votos"
        res = requests.get(url)
        
        if res.status_code == 200:
            dados = res.json()["dados"]
            for v in dados:
                # Extraindo dados do dicionário 'deputado' que vem no JSON
                linha = {
                    "id_votacao": id_votacao,
                    "voto": v.get("tipoVoto"),
                    "dataHora": v.get("dataHoraVoto"),
                    "id_deputado": v.get("deputado", {}).get("id"),
                    "nome_deputado": v.get("deputado", {}).get("nome")
                }
                lista_votos.append(linha)
        time.sleep(0.1)

    if lista_votos:
        df_votos = pd.DataFrame(lista_votos)
        realizar_eda(df_votos, "TB_VOTOS_DETALHADOS")
        df_votos.to_sql("tb_votacoes_votos", conn, if_exists="replace", index=False)

    conn.close()
    print("✅ Banco atualizado com os votos detalhados.")

if __name__ == "__main__":
    automacao_votos_votacoes()