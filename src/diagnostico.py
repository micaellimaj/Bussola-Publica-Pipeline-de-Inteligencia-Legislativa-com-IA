import os
import sys
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine, text

def executar_diagnostico() -> bool:
    """
    Realiza o diagnóstico completo do ambiente antes da execução do pipeline.
    Retorna True se passar em todas as verificações críticas, ou False caso falhe.
    """
    print("\n" + "=" * 60)
    print("BÚSSOLA PÚBLICA | Diagnóstico Pré-Execução (Etapa 4)")
    print("=" * 60)

    passou = []
    falhou = []
    avisos = []

    # 1. Carregamento e Verificação do .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        print("  [FALHA] Arquivo .env não encontrado na raiz do projeto!")
        return False
    
    load_dotenv(env_path)
    database_url = os.getenv("DATABASE_URL")
    openai_key = os.getenv("OPENAI_API_KEY")
    modelo_ia = os.getenv("MODELO_IA", "gpt-4o-mini")

    # Validando variáveis cruciais
    for var, valor in [("DATABASE_URL", database_url), ("OPENAI_API_KEY", openai_key)]:
        if not valor or "SUA_CHAVE" in valor or "usuario" in valor:
            print(f"  [FALHA] Variável {var} está vazia ou com valor de exemplo.")
            falhou.append(var)
        else:
            exibir = valor[:8] + "..." if var == "OPENAI_API_KEY" else valor.split("@")[-1]
            print(f"  [OK]    {var} configurada: {exibir}")
            passou.append(var)

    if falhou:
        return False

    # 2. Testando Conexão com PostgreSQL (Supabase)
    print("\n[Diagnóstico] Conectando ao PostgreSQL...")
    try:
        engine = create_engine(database_url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            resultado = conn.execute(text("SELECT version();")).fetchone()
        print(f"  [OK]    PostgreSQL Conectado: {str(resultado[0])[:45]}...")
        passou.append("PostgreSQL")
    except Exception as e:
        print(f"  [ERRO]  Falha crítica de conexão ao banco: {e}")
        return False

    # 3. Verificando Tabela fato_proposicoes
    print("\n[Diagnóstico] Verificando integridade da tabela 'fato_proposicoes'...")
    try:
        with engine.connect() as conn:
            existe = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'fato_proposicoes';
            """)).scalar()

            if not existe:
                print("  [FALHA] Tabela 'fato_proposicoes' não existe no banco de dados!")
                print("          Execute as Etapas 1 e 3 para criar a estrutura inicial.")
                return False
            
            total = conn.execute(text("SELECT COUNT(*) FROM fato_proposicoes;")).scalar()
            
            col_existe = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = 'fato_proposicoes' AND column_name = 'resumo_executivo';
            """)).scalar()

            if col_existe:
                com_resumo = conn.execute(text("""
                    SELECT COUNT(*) FROM fato_proposicoes WHERE resumo_executivo IS NOT NULL;
                """)).scalar()
                print(f"  [OK]    Registros totais: {total} | Já resumidos: {com_resumo} | Pendentes: {total - com_resumo}")
            else:
                print(f"  [OK]    Registros totais: {total}")
                print("  [INFO]  A coluna 'resumo_executivo' será criada de forma dinâmica na Etapa 4.")

            if total == 0:
                print("  [AVISO] A tabela 'fato_proposicoes' está vazia.")
                avisos.append("Tabela Vazia")
            else:
                # Amostra usando id_proposicao baseado na sua query estruturada
                amostra = conn.execute(text("""
                    SELECT id_proposicao, sigla_tipo, numero, ano, LEFT(ementa, 50)
                    FROM fato_proposicoes WHERE ementa IS NOT NULL LIMIT 2;
                """)).fetchall()
                print("          Amostra de dados encontrados:")
                for row in amostra:
                    print(f"          - ID {row[0]} | {row[1]} {row[2]}/{row[3]} | {row[4]}...")

    except Exception as e:
        print(f"  [ERRO]  Falha ao analisar tabelas: {e}")
        return False
    finally:
        engine.dispose()

    # 4. Validando credenciais e comunicação com OpenAI
    print("\n[Diagnóstico] Autenticando com a API da OpenAI...")
    try:
        client = OpenAI(api_key=openai_key, timeout=10)
        client.models.list()
        print(f"  [OK]    OpenAI conectada com sucesso. Modelo Alvo: '{modelo_ia}'")
        passou.append("OpenAI")
    except Exception as e:
        print(f"  [ERRO]  Chave da OpenAI inválida ou problemas de saldo/crédito: {e}")
        return False

    print("\n" + "=" * 60)
    print(f"DIAGNÓSTICO CONCLUÍDO: Ambiente pronto para o pipeline.")
    print("=" * 60 + "\n")
    return True