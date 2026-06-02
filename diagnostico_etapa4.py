"""
=============================================================================
BUSSOLA PUBLICA - Diagnostico Pre-execucao | Etapa 4
=============================================================================
Rode este script ANTES de Desafio_Etapa4_IA.py para validar que:
  1. O arquivo .env existe e tem as variaveis necessarias
  2. A conexao com o PostgreSQL esta funcionando
  3. A tabela fato_proposicoes existe e tem dados
  4. A chave da OpenAI API esta valida
  5. As dependencias Python estao instaladas

Uso:
    python diagnostico_etapa4.py
=============================================================================
"""

import sys
import os

print("=" * 60)
print("BUSSOLA PUBLICA | Diagnostico Etapa 4")
print("=" * 60)

PASSOU  = []
FALHOU  = []
AVISOS  = []

# -------------------------------------------------------------------
# VERIFICACAO 1: Dependencias Python
# -------------------------------------------------------------------
print("\n[1/5] Verificando dependencias Python...")
dependencias = ["openai", "sqlalchemy", "psycopg2", "pandas", "dotenv"]
for dep in dependencias:
    try:
        __import__(dep)
        print(f"  OK  {dep}")
        PASSOU.append(dep)
    except ImportError:
        print(f"  FALTA  {dep}")
        FALHOU.append(f"Dependencia '{dep}' nao instalada")

if FALHOU:
    print("\n  -> Para instalar tudo de uma vez:")
    print("     pip install openai sqlalchemy psycopg2-binary pandas python-dotenv")

# -------------------------------------------------------------------
# VERIFICACAO 2: Arquivo .env
# -------------------------------------------------------------------
print("\n[2/5] Verificando arquivo .env...")
env_path = os.path.join(os.path.dirname(__file__), ".env")

if not os.path.exists(env_path):
    print("  FALTA  Arquivo .env nao encontrado!")
    print("  -> Copie o template: cp .env.example .env")
    print("  -> Preencha DATABASE_URL e OPENAI_API_KEY")
    FALHOU.append("Arquivo .env nao existe")
else:
    print(f"  OK  .env encontrado em {env_path}")
    PASSOU.append(".env encontrado")

    from dotenv import load_dotenv
    load_dotenv(env_path)

    variaveis = {
        "DATABASE_URL":   os.getenv("DATABASE_URL"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "DRY_RUN":        os.getenv("DRY_RUN", "true"),
        "BATCH_SIZE":     os.getenv("BATCH_SIZE", "10"),
        "MODELO_IA":      os.getenv("MODELO_IA", "gpt-4o-mini"),
    }

    for var, valor in variaveis.items():
        if not valor:
            print(f"  VAZIA  {var} nao configurada")
            FALHOU.append(f"Variavel {var} vazia no .env")
        elif var in ("DATABASE_URL", "OPENAI_API_KEY") and (
            "SUA_CHAVE" in valor or "usuario" in valor or "senha" in valor
        ):
            print(f"  PENDENTE  {var} ainda tem valor de exemplo - preencha com o valor real")
            FALHOU.append(f"{var} ainda tem valor de exemplo")
        else:
            # Mascara a chave para nao exibir no terminal
            if var == "OPENAI_API_KEY":
                exibir = valor[:8] + "..." + valor[-4:] if len(valor) > 12 else "***"
            elif var == "DATABASE_URL":
                exibir = valor.split("@")[-1] if "@" in valor else valor[:30] + "..."
            else:
                exibir = valor
            print(f"  OK  {var} = {exibir}")
            PASSOU.append(var)

# -------------------------------------------------------------------
# VERIFICACAO 3: Conexao com PostgreSQL
# -------------------------------------------------------------------
print("\n[3/5] Testando conexao com PostgreSQL...")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or "usuario" in (DATABASE_URL or ""):
    print("  PULADO  DATABASE_URL invalida - configure o .env primeiro")
    AVISOS.append("Conexao com banco nao testada")
else:
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            resultado = conn.execute(text("SELECT version()")).fetchone()
        print(f"  OK  PostgreSQL conectado: {str(resultado[0])[:50]}...")
        PASSOU.append("Conexao PostgreSQL")
        engine.dispose()
    except Exception as e:
        print(f"  ERRO  Falha na conexao: {e}")
        FALHOU.append(f"PostgreSQL inacessivel: {str(e)[:80]}")

# -------------------------------------------------------------------
# VERIFICACAO 4: Tabela fato_proposicoes e dados
# -------------------------------------------------------------------
print("\n[4/5] Verificando tabela fato_proposicoes...")
if not DATABASE_URL or "usuario" in (DATABASE_URL or ""):
    print("  PULADO  Configure DATABASE_URL primeiro")
else:
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Verifica se a tabela existe
            existe = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'fato_proposicoes'
            """)).scalar()

            if not existe:
                print("  FALTA  Tabela 'fato_proposicoes' nao existe!")
                print("  -> Rode a Etapa 2 (extracao) e Etapa 3 (transformacao + carga) primeiro")
                FALHOU.append("Tabela fato_proposicoes nao existe - rode Etapas 2 e 3 antes")
            else:
                # Conta total de registros
                total = conn.execute(text(
                    "SELECT COUNT(*) FROM fato_proposicoes"
                )).scalar()

                # Conta quantos ja tem resumo
                # Verifica se a coluna existe primeiro
                col_existe = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = 'fato_proposicoes'
                    AND column_name = 'resumo_executivo'
                """)).scalar()

                if col_existe:
                    com_resumo = conn.execute(text(
                        "SELECT COUNT(*) FROM fato_proposicoes WHERE resumo_executivo IS NOT NULL"
                    )).scalar()
                    sem_resumo = total - com_resumo
                    print(f"  OK  fato_proposicoes: {total} registros total")
                    print(f"      Com resumo    : {com_resumo}")
                    print(f"      Sem resumo    : {sem_resumo} (pendentes para Etapa 4)")
                else:
                    print(f"  OK  fato_proposicoes: {total} registros")
                    print(f"      Coluna 'resumo_executivo' ainda nao existe (sera criada na Etapa 4)")
                    sem_resumo = total

                if total == 0:
                    print("  AVISO  Tabela existe mas esta VAZIA - rode Etapas 2 e 3 primeiro")
                    AVISOS.append("fato_proposicoes vazia - rode etapas 2 e 3")
                else:
                    PASSOU.append(f"fato_proposicoes ({total} registros)")

                # Exibe amostra das ementas
                amostra = conn.execute(text("""
                    SELECT id_proposicao, sigla_tipo, numero, ano,
                           LEFT(ementa, 80) AS ementa_resumida
                    FROM fato_proposicoes
                    WHERE ementa IS NOT NULL AND trim(ementa) <> ''
                    LIMIT 3
                """)).fetchall()

                if amostra:
                    print("\n  Amostra de proposicoes:")
                    for row in amostra:
                        print(f"    ID {row[0]} | {row[1]} {row[2]}/{row[3]} | {row[4]}...")

        engine.dispose()
    except Exception as e:
        print(f"  ERRO  {e}")
        FALHOU.append(f"Erro ao verificar tabela: {str(e)[:80]}")

# -------------------------------------------------------------------
# VERIFICACAO 5: OpenAI API Key
# -------------------------------------------------------------------
print("\n[5/5] Verificando chave da OpenAI API...")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY or "SUA_CHAVE" in (OPENAI_API_KEY or ""):
    print("  FALTA  OPENAI_API_KEY nao configurada")
    print()
    print("  COMO OBTER SUA CHAVE (gratuito para criar, pague so o que usar):")
    print("  1. Acesse: https://platform.openai.com/api-keys")
    print("  2. Faca login ou crie uma conta")
    print("  3. Clique em 'Create new secret key'")
    print("  4. Copie a chave (sk-proj-...)")
    print("  5. Adicione ao .env:  OPENAI_API_KEY=sk-proj-SUA_CHAVE")
    print()
    print("  CUSTO ESTIMADO para o desafio (gpt-4o-mini):")
    print("    10 proposicoes  -> ~$ 0.0003 USD (~R$ 0.002)")
    print("    100 proposicoes -> ~$ 0.003  USD (~R$ 0.016)")
    print("    500 proposicoes -> ~$ 0.015  USD (~R$ 0.078)")
    FALHOU.append("OPENAI_API_KEY nao configurada")
else:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=10)
        # Testa com o endpoint mais barato (lista de modelos)
        modelos = client.models.list()
        modelo_ia = os.getenv("MODELO_IA", "gpt-4o-mini")
        ids = [m.id for m in modelos.data]
        if modelo_ia in ids:
            print(f"  OK  OpenAI API conectada | Modelo '{modelo_ia}' disponivel")
        else:
            print(f"  OK  OpenAI API conectada | Modelo '{modelo_ia}' nao listado (pode ser acesso de conta)")
        PASSOU.append("OpenAI API")
    except Exception as e:
        print(f"  ERRO  Chave invalida ou sem credito: {e}")
        FALHOU.append(f"OpenAI API invalida: {str(e)[:80]}")

# -------------------------------------------------------------------
# RESUMO FINAL
# -------------------------------------------------------------------
print()
print("=" * 60)
print("RESULTADO DO DIAGNOSTICO")
print("=" * 60)
print(f"  Passou  : {len(PASSOU)}")
print(f"  Falhou  : {len(FALHOU)}")
print(f"  Avisos  : {len(AVISOS)}")

if FALHOU:
    print()
    print("Itens que precisam de atencao:")
    for item in FALHOU:
        print(f"  -> {item}")

if AVISOS:
    print()
    print("Avisos:")
    for item in AVISOS:
        print(f"  ?? {item}")

print()
if not FALHOU:
    dry = os.getenv("DRY_RUN", "true")
    modelo = os.getenv("MODELO_IA", "gpt-4o-mini")
    print(f"  TUDO OK! Ambiente pronto para rodar a Etapa 4.")
    print()
    print("  Proximo passo:")
    if dry.lower() == "true":
        print("  1. Execute a estimativa de custo:")
        print("     python Desafio_Etapa4_IA.py")
        print()
        print("  2. Satisfeito com o custo? Mude no .env:")
        print("     DRY_RUN=false")
        print()
        print("  3. Rode de verdade:")
        print("     python Desafio_Etapa4_IA.py")
    else:
        print("  -> python Desafio_Etapa4_IA.py")
        print(f"     (DRY_RUN=false | Modelo={modelo})")
else:
    print("  Corrija os itens acima e rode o diagnostico novamente.")
    print("  -> python diagnostico_etapa4.py")

print("=" * 60)
