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
    
    if 'valorLiquido' in df.columns:
        print(f"\n• Valor Total Processado: R$ {df['valorLiquido'].sum():,.2f}")
    
    print("-" * 40)

def automacao_detalhes_deputados():
    # 1. Conexão e busca de IDs existentes
    conn = sqlite3.connect("../../data/raw/dados_camara.db")
    try:
        ids_deputados = pd.read_sql("SELECT id FROM tb_deputados", conn)['id'].tolist()
    except:
        print("❌ Erro: Tabela 'tb_deputados' não encontrada no banco.")
        return

    lista_despesas = []
    lista_profissoes = []
    
    # Colunas relevantes para Despesas
    colunas_despesa = [
        "id_deputado", "ano", "mes", "dataDocumento", 
        "nomeFornecedor", "cnpjCpfFornecedor", 
        "tipoDespesa", "valorLiquido", "urlDocumento"
    ]

    print(f"🚀 Iniciando coleta para {len(ids_deputados)} deputados...")

    # Limitador para teste (remova [:10] para rodar em todos)
    for i, id_deputado in enumerate(ids_deputados[:10]):
        print(f"📡 Processando ID {id_deputado} ({i+1}/{len(ids_deputados[:10])})")
        
        # --- COLETA DE DESPESAS ---
        url_desp = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/despesas"
        res_desp = requests.get(url_desp, params={"itens": 100})
        if res_desp.status_code == 200:
            dados = res_desp.json()["dados"]
            for d in dados:
                d["id_deputado"] = id_deputado
                lista_despesas.append(d)

        # --- COLETA DE PROFISSÕES ---
        url_prof = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/profissoes"
        res_prof = requests.get(url_prof)
        if res_prof.status_code == 200:
            dados = res_prof.json()["dados"]
            for p in dados:
                p["id_deputado"] = id_deputado
                lista_profissoes.append(p)
        
        time.sleep(0.1)

    # 2. Processamento e EDA: Despesas
    if lista_despesas:
        df_desp = pd.DataFrame(lista_despesas)
        df_desp = df_desp[colunas_despesa]
        realizar_eda(df_desp, "TB_DESPESAS")
        df_desp.to_sql("tb_deputados_despesas", conn, if_exists="replace", index=False)

    # 3. Processamento e EDA: Profissões
    if lista_profissoes:
        df_prof = pd.DataFrame(lista_profissoes)
        realizar_eda(df_prof, "TB_PROFISSOES")
        df_prof.to_sql("tb_deputados_profissoes", conn, if_exists="replace", index=False)

    conn.close()
    print("\n✅ Processo concluído e banco 'dados_camara.db' atualizado!")

if __name__ == "__main__":
    automacao_detalhes_deputados()