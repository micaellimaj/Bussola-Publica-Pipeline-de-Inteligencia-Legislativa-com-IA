import requests
import pandas as pd
import sqlite3

# 1. Configuração da URL e Chamada da API
url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
print("🔍 Acessando API da Câmara...")
response = requests.get(url)

if response.status_code == 200:
    dados_brutos = response.json()["dados"]
    df_deputados = pd.DataFrame(dados_brutos)
    
    colunas_interesse = ["id", "nome", "siglaPartido", "siglaUf", "idLegislatura", "urlFoto", "email"]
    df_final = df_deputados[colunas_interesse]

    # --- BLOCO DE ANÁLISE EXPLORATÓRIA (EDA) ---
    print("\n" + "="*40)
    print("📊 RESUMO EXPLORATÓRIO DOS DADOS")
    print("="*40)

    # 1. Dimensões do Dataset
    print(f"• Quantidade de linhas: {df_final.shape[0]}")
    print(f"• Quantidade de colunas: {df_final.shape[1]}")

    # 2. Valores Nulos (Missing Values)
    print("\n• Valores nulos por coluna:")
    print(df_final.isnull().sum())

    # 3. Duplicatas
    duplicatas = df_final.duplicated().sum()
    print(f"\n• Linhas duplicadas encontradas: {duplicatas}")

    # 4. Informações de Tipos de Dados
    print("\n• Tipos de dados e memória:")
    print(df_final.info())

    # 5. Breve Estatística de Categorias (Partidos e Estados)
    print("\n• Top 5 Partidos com mais deputados:")
    print(df_final['siglaPartido'].value_counts().head(5))

    print("\n• Distribuição por UF (Top 5):")
    print(df_final['siglaUf'].value_counts().head(5))
    print("="*40 + "\n")
    # -------------------------------------------

    # 2. Salvando no SQLite
    conexao = sqlite3.connect("../../data/raw/dados_camara.db")
    df_final.to_sql("tb_deputados", conexao, if_exists="replace", index=False)
    conexao.close()
    
    print("✅ Banco 'dados_camara.db' atualizado com sucesso!")

else:
    print(f"❌ Erro ao acessar a API. Status: {response.status_code}")
