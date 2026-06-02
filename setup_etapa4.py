"""
=============================================================================
BUSSOLA PUBLICA - Setup Interativo | Etapa 4
=============================================================================
Script de configuracao guiada para rodar a Etapa 4 (Resumo Executivo com IA).

Uso:
    python setup_etapa4.py

O que faz:
  1. Cria o arquivo .env perguntando suas credenciais
  2. Valida a conexao com o banco de dados
  3. Verifica quantas proposicoes estao pendentes de resumo
  4. Estima o custo da chamada a OpenAI
  5. Pergunta se deseja executar de verdade
=============================================================================
"""

import os
import sys
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"


def limpar():
    os.system("cls" if os.name == "nt" else "clear")


def titulo(texto):
    print()
    print("=" * 60)
    print(f"  {texto}")
    print("=" * 60)


def ok(msg):  print(f"  [OK]    {msg}")
def erro(msg): print(f"  [ERRO]  {msg}")
def info(msg): print(f"  [INFO]  {msg}")
def aviso(msg): print(f"  [!]     {msg}")


# ---------------------------------------------------------------------------
# PASSO 1 - Verificar / criar .env
# ---------------------------------------------------------------------------
def configurar_env():
    titulo("PASSO 1/4 — Configurar credenciais (.env)")

    env_atual = {}
    if ENV_PATH.exists():
        ok(f".env encontrado em {ENV_PATH}")
        from dotenv import dotenv_values
        env_atual = dotenv_values(ENV_PATH)
    else:
        aviso(".env nao encontrado. Vamos criar agora.")

    print()

    # DATABASE_URL
    db_atual = env_atual.get("DATABASE_URL", "")
    if db_atual and "usuario" not in db_atual and "senha" not in db_atual:
        ok(f"DATABASE_URL configurado -> {db_atual.split('@')[-1]}")
        database_url = db_atual
    else:
        print("  Onde encontrar o DATABASE_URL:")
        print("  -> Supabase: Project Settings > Database > Connection string (URI)")
        print("  -> Formato: postgresql://postgres:[SENHA]@[HOST]:5432/postgres")
        print()
        database_url = input("  Cole seu DATABASE_URL: ").strip()
        if not database_url:
            erro("DATABASE_URL nao pode ser vazio.")
            sys.exit(1)

    print()

    # OPENAI_API_KEY
    oai_atual = env_atual.get("OPENAI_API_KEY", "")
    if oai_atual and oai_atual.startswith("sk-") and "SUA_CHAVE" not in oai_atual:
        ok(f"OPENAI_API_KEY configurada -> {oai_atual[:12]}...")
        openai_key = oai_atual
    else:
        print("  Como obter sua OPENAI_API_KEY (gratis para criar conta):")
        print()
        print("  1. Acesse: https://platform.openai.com/api-keys")
        print("  2. Faca login ou crie conta gratuita")
        print("  3. Clique em 'Create new secret key'")
        print("  4. Copie a chave (comeca com sk-proj-...)")
        print()
        print("  Custo estimado para o desafio inteiro: < R$ 0,15 (gpt-4o-mini)")
        print()
        openai_key = input("  Cole sua OPENAI_API_KEY: ").strip()
        if not openai_key or not openai_key.startswith("sk-"):
            erro("Chave invalida. Deve comecar com sk-")
            sys.exit(1)

    print()

    # Modelo
    modelo_atual = env_atual.get("MODELO_IA", "gpt-4o-mini")
    print(f"  Modelo de IA: {modelo_atual} (recomendado para o desafio)")
    print("  -> Para usar GPT-4o (mais caro), edite MODELO_IA no .env depois")
    modelo = modelo_atual

    # Salva o .env
    conteudo = f"""# BUSSOLA PUBLICA - Variaveis de Ambiente
# Gerado por setup_etapa4.py
# NAO suba este arquivo para o GitHub!

DATABASE_URL={database_url}
OPENAI_API_KEY={openai_key}

# Controles da Etapa 4
DRY_RUN=true
BATCH_SIZE=10
MODELO_IA={modelo}
"""
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(conteudo)

    ok(f".env salvo em {ENV_PATH}")
    return database_url, openai_key, modelo


# ---------------------------------------------------------------------------
# PASSO 2 - Testar banco e contar proposicoes pendentes
# ---------------------------------------------------------------------------
def verificar_banco(database_url):
    titulo("PASSO 2/4 — Verificar banco de dados")

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url, connect_args={"connect_timeout": 10})

        with engine.connect() as conn:
            # Testa conexao
            conn.execute(text("SELECT 1"))
            ok("Conexao com PostgreSQL estabelecida")

            # Verifica se fato_proposicoes existe
            existe = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'fato_proposicoes'
            """)).scalar()

            if not existe:
                erro("Tabela 'fato_proposicoes' NAO encontrada!")
                aviso("Rode as Etapas 2 e 3 primeiro (main.py do repositorio do squad)")
                engine.dispose()
                sys.exit(1)

            # Conta total
            total = conn.execute(text(
                "SELECT COUNT(*) FROM fato_proposicoes WHERE ementa IS NOT NULL"
            )).scalar()

            # Verifica coluna resumo_executivo
            col_existe = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name='fato_proposicoes' AND column_name='resumo_executivo'
            """)).scalar()

            if col_existe:
                com_resumo = conn.execute(text(
                    "SELECT COUNT(*) FROM fato_proposicoes WHERE resumo_executivo IS NOT NULL"
                )).scalar()
                pendentes = total - com_resumo
                ok(f"fato_proposicoes: {total} registros total")
                ok(f"Com resumo ja   : {com_resumo}")
                ok(f"Pendentes       : {pendentes}")
            else:
                pendentes = total
                ok(f"fato_proposicoes: {total} proposicoes com ementa")
                info("Coluna 'resumo_executivo' sera criada automaticamente")

            # Mostra 3 exemplos
            amostra = conn.execute(text("""
                SELECT id_proposicao, COALESCE(sigla_tipo,'?') as tipo,
                       COALESCE(numero::text,'?') as num,
                       COALESCE(ano::text,'?') as ano,
                       LEFT(ementa, 90) as ementa
                FROM fato_proposicoes
                WHERE ementa IS NOT NULL AND trim(ementa) <> ''
                LIMIT 3
            """)).fetchall()

            if amostra:
                print()
                info("Amostra de proposicoes que serao resumidas:")
                for r in amostra:
                    print(f"    ID {r[0]} | {r[1]} {r[2]}/{r[3]}")
                    print(f"    \"{r[4]}...\"")
                    print()

        engine.dispose()
        return pendentes

    except Exception as e:
        erro(f"Falha no banco: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# PASSO 3 - Validar OpenAI e estimar custo
# ---------------------------------------------------------------------------
def verificar_openai(openai_key, modelo, pendentes):
    titulo("PASSO 3/4 — Validar OpenAI e estimar custo")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key, timeout=10)
        client.models.list()
        ok("OpenAI API: chave valida")
    except Exception as e:
        erro(f"Chave OpenAI invalida: {e}")
        aviso("Verifique se a chave esta correta e se ha credito na conta")
        aviso("-> https://platform.openai.com/usage")
        sys.exit(1)

    # Estimativa de custo
    CUSTO_IN  = {"gpt-4o": 0.0025,  "gpt-4o-mini": 0.000150}
    CUSTO_OUT = {"gpt-4o": 0.010,   "gpt-4o-mini": 0.000600}
    TK_IN, TK_OUT = 300, 150
    taxa_brl = 5.20

    c_in  = CUSTO_IN.get(modelo, 0.000150)
    c_out = CUSTO_OUT.get(modelo, 0.000600)
    batch = min(10, pendentes)

    custo_10  = ((10 * TK_IN / 1000 * c_in) + (10 * TK_OUT / 1000 * c_out)) * taxa_brl
    custo_all = ((pendentes * TK_IN / 1000 * c_in) + (pendentes * TK_OUT / 1000 * c_out)) * taxa_brl

    print()
    info(f"Modelo escolhido    : {modelo}")
    info(f"Proposicoes total   : {pendentes}")
    info(f"Batch (primeiro run): {batch}")
    print()
    print(f"  Custo estimado (10 proposicoes) : ~R$ {custo_10:.4f}")
    print(f"  Custo estimado (TODAS)          : ~R$ {custo_all:.4f}")
    print()

    return batch


# ---------------------------------------------------------------------------
# PASSO 4 - Executar
# ---------------------------------------------------------------------------
def executar(database_url, openai_key, modelo, batch):
    titulo("PASSO 4/4 — Executar Etapa 4")

    print(f"  Pronto para gerar resumos de {batch} proposicoes.")
    print()
    resposta = input("  Deseja executar agora? (s/n): ").strip().lower()

    if resposta != "s":
        info("Execucao cancelada pelo usuario.")
        info("Para rodar manualmente depois:")
        info("  1. Edite .env -> DRY_RUN=false")
        info("  2. python Desafio_Etapa4_IA.py")
        return

    # Atualiza .env para DRY_RUN=false
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        conteudo = f.read()
    conteudo = conteudo.replace("DRY_RUN=true", "DRY_RUN=false")
    conteudo = conteudo.replace(f"BATCH_SIZE=10", f"BATCH_SIZE={batch}")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(conteudo)

    ok(f".env atualizado: DRY_RUN=false | BATCH_SIZE={batch}")
    print()
    info("Iniciando pipeline de IA...")
    print()

    # Executa o pipeline
    import subprocess
    script = Path(__file__).parent / "Desafio_Etapa4_IA.py"
    resultado = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script.parent)
    )

    print()
    if resultado.returncode == 0:
        ok("Pipeline Etapa 4 concluido!")
        print()
        info("Verifique no Supabase:")
        info("  Table Editor -> fato_proposicoes -> coluna 'resumo_executivo'")
        print()
        info("Para processar mais proposicoes:")
        info("  1. Aumente BATCH_SIZE no .env")
        info("  2. python Desafio_Etapa4_IA.py")
    else:
        erro(f"Pipeline encerrou com codigo {resultado.returncode}")
        info("Verifique o arquivo etapa4_ia_*.log para detalhes do erro")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    limpar()
    print()
    print("  BUSSOLA PUBLICA | Setup Interativo - Etapa 4")
    print("  Resumo Executivo com IA (GPT-4o-mini)")
    print()

    # Verifica dependencias antes de tudo
    faltando = []
    for dep in ["openai", "sqlalchemy", "psycopg2", "pandas", "dotenv"]:
        try:
            __import__(dep)
        except ImportError:
            faltando.append(dep)

    if faltando:
        print("  Instalando dependencias faltantes...")
        import subprocess
        pkgs = ["openai", "sqlalchemy", "psycopg2-binary", "pandas", "python-dotenv"]
        subprocess.run([sys.executable, "-m", "pip", "install"] + pkgs, check=True)
        print()

    # Executa os passos
    database_url, openai_key, modelo = configurar_env()
    pendentes = verificar_banco(database_url)
    batch = verificar_openai(openai_key, modelo, pendentes)
    executar(database_url, openai_key, modelo, batch)
