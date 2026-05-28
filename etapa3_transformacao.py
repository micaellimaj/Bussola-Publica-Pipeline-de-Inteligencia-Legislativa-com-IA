"""
=============================================================================
BUSSOLA PUBLICA - Projeto Integrador | Pos Tech Engenharia de Dados e IA
=============================================================================
Etapa 3: Transformacao com Pandas e Carga no PostgreSQL

Boas praticas aplicadas (Nivelamento + APIs + POO / Prof. Iago Braz / Xperiun):

  POO (Programacao Orientada a Objetos):
    - TransformadorBase      -> classe base com metodos comuns de leitura
    - Transformadores        -> um por entidade (deputados, proposicoes, etc.)
    - ValidadorDados         -> responsabilidade unica: validar DataFrames
    - CargaPostgreSQL        -> responsabilidade unica: persistir no banco
    - PipelineEtapa3         -> orquestra transformacao + validacao + carga

  Pandas:
    - pd.read_json()         -> carrega JSON bruto salvo na Etapa 2
    - pd.json_normalize()    -> desnormaliza campos aninhados (dicts dentro de dicts)
    - df.drop_duplicates()   -> deduplicacao de registros
    - df.dropna()            -> remove/identifica nulos em campos obrigatorios
    - df[df['col'] < 0]      -> identifica valores invalidos (ex: monetarios)
    - pd.to_datetime()       -> converte e valida datas

  Modelo de dados (Star Schema):
    - Dimensao: dim_deputados, dim_partidos
    - Fato    : fato_proposicoes, fato_votacoes, fato_votos

  Banco de dados:
    - SQLAlchemy + psycopg2  -> conexao e carga no PostgreSQL
    - df.to_sql()            -> insere DataFrame direto na tabela
    - Variaveis de ambiente  -> nunca expor credenciais no codigo (.env)

Como usar:
    1. Copie .env.example para .env e preencha com suas credenciais
    2. pip install -r requirements.txt
    3. Rode a Etapa 2 primeiro para gerar os JSONs em data/raw/
    4. python etapa3_transformacao.py

Hospedagem recomendada para o PostgreSQL:
    - Supabase : https://supabase.com  (gratuito, pgvector incluido)
    - Neon     : https://neon.tech     (gratuito, serverless)
    - Railway  : https://railway.app   (gratuito com limites)
=============================================================================
"""

# PASSO 1: Importar bibliotecas
import os
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# SQLAlchemy - conexao com PostgreSQL
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# PASSO 2: Carrega variaveis de ambiente do arquivo .env
# NUNCA deixe credenciais hardcoded no codigo - boa pratica fundamental do curso
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# Formato esperado no .env:
#   DATABASE_URL=postgresql://usuario:senha@host:porta/nome_banco
# Supabase: Settings -> Database -> Connection string (URI mode)

RAW_DIR = Path("data/raw")    # onde os JSONs da Etapa 2 foram salvos
DATA    = datetime.today().strftime("%Y%m%d")

# Configuracao de log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"transformacao_{DATA}.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# =============================================================================
# CLASSE BASE: TransformadorBase
#
# Responsabilidade: ler JSONs brutos e expor metodos uteis de normalizacao.
# Nao sabe nada de validacao nem de banco - generica por design.
# =============================================================================
class TransformadorBase:
    """Classe base para todos os transformadores de dados."""

    def __init__(self, raw_dir):
        """
        Parametros:
            raw_dir (Path): caminho para a pasta com os JSONs brutos
        """
        self.raw_dir = Path(raw_dir)

    def _ler_json(self, subpasta, prefixo):
        """
        Encontra o arquivo JSON mais recente em raw_dir/subpasta
        que comeca com o prefixo informado.

        Por que ler o mais recente?
        Cada execucao da Etapa 2 gera um arquivo com timestamp.
        Queremos sempre o dado mais atual sem precisar hardcodar o nome.

        Retorna:
            list de dicionarios ou None se nao encontrado.
        """
        pasta = self.raw_dir / subpasta
        arquivos = sorted(pasta.glob(f"{prefixo}*.json"), reverse=True)

        if not arquivos:
            log.error(f"Nenhum arquivo '{prefixo}*.json' encontrado em {pasta}")
            return None

        caminho = arquivos[0]
        log.info(f"  Lendo: {caminho}")

        try:
            with open(caminho, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Erro ao ler {caminho}: {e}")
            return None

    def _normalizar(self, dados, campos_meta=None):
        """
        Usa pd.json_normalize() para achatar campos aninhados.

        pd.json_normalize() e o mais indicado quando o JSON tem dicts
        dentro de dicts (ex: deputado.ultimoStatus.siglaPartido).
        Ele cria colunas novas com o caminho completo: 'ultimoStatus.siglaPartido'.

        Parametros:
            dados       (list): lista de dicionarios (retorno da API)
            campos_meta (list): caminhos de campos aninhados para expandir
        """
        if not dados:
            return pd.DataFrame()
        try:
            if campos_meta:
                return pd.json_normalize(dados, meta=campos_meta)
            return pd.json_normalize(dados)
        except Exception as e:
            log.warning(f"json_normalize falhou, usando pd.DataFrame: {e}")
            return pd.DataFrame(dados)


# =============================================================================
# CLASSE: TransformadorDeputados
# Responsabilidade: transformar os dados brutos de deputados
# em dim_deputados (tabela dimensao).
# =============================================================================
class TransformadorDeputados(TransformadorBase):
    """Transforma os dados brutos de deputados em dim_deputados."""

    def transformar(self):
        """
        Carrega, normaliza e seleciona os campos de dim_deputados.

        Retorna:
            DataFrame pronto para carga, ou DataFrame vazio em caso de erro.
        """
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Deputados -> dim_deputados")
        log.info("-" * 50)

        dados = self._ler_json("deputados", "deputados_")
        if dados is None:
            return pd.DataFrame()

        df = self._normalizar(dados)
        log.info(f"  Bruto: {df.shape[0]} linhas x {df.shape[1]} colunas")
        log.info(f"  Colunas disponiveis: {list(df.columns)}")

        # Selecao e renomeacao de colunas para o modelo dimensional
        # Usa .get() no rename para nao quebrar se uma coluna nao existir
        colunas = {
            "id":           "id_deputado",
            "nome":         "nome",
            "siglaPartido": "sigla_partido",
            "siglaUf":      "sigla_uf",
            "idLegislatura":"id_legislatura",
            "urlFoto":      "url_foto",
            "uri":          "uri"
        }
        # So renomeia colunas que existem no DataFrame
        colunas_presentes = {k: v for k, v in colunas.items() if k in df.columns}
        df = df[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

        log.info(f"  Apos selecao: {df.shape[0]} linhas x {df.shape[1]} colunas")
        return df


# =============================================================================
# CLASSE: TransformadorPartidos
# Responsabilidade: transformar dados de partidos em dim_partidos.
# =============================================================================
class TransformadorPartidos(TransformadorBase):
    """Transforma os dados brutos de partidos em dim_partidos."""

    def transformar(self):
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Partidos -> dim_partidos")
        log.info("-" * 50)

        dados = self._ler_json("partidos", "partidos_")
        if dados is None:
            return pd.DataFrame()

        df = self._normalizar(dados)
        log.info(f"  Bruto: {df.shape[0]} linhas x {df.shape[1]} colunas")

        colunas = {
            "id":   "id_partido",
            "sigla":"sigla",
            "nome": "nome",
            "uri":  "uri"
        }
        colunas_presentes = {k: v for k, v in colunas.items() if k in df.columns}
        df = df[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

        log.info(f"  Apos selecao: {df.shape[0]} linhas x {df.shape[1]} colunas")
        return df


# =============================================================================
# CLASSE: TransformadorProposicoes
# Responsabilidade: transformar proposicoes em fato_proposicoes
# e o relacionamento com autores em fato_proposicoes_autores.
# =============================================================================
class TransformadorProposicoes(TransformadorBase):
    """Transforma proposicoes em fato_proposicoes e tabela de autores."""

    def transformar(self):
        """
        Retorna:
            dict com chaves "proposicoes" e "autores" (DataFrames)
        """
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Proposicoes -> fato_proposicoes")
        log.info("-" * 50)

        # --- Proposicoes ---
        dados_props = self._ler_json("proposicoes", "proposicoes_")
        df_props = pd.DataFrame()

        if dados_props is not None:
            df_props = self._normalizar(dados_props)
            log.info(f"  Bruto: {df_props.shape[0]} linhas x {df_props.shape[1]} colunas")

            colunas = {
                "id":              "id_proposicao",
                "siglaTipo":       "sigla_tipo",
                "numero":          "numero",
                "ano":             "ano",
                "ementa":          "ementa",
                "dataApresentacao":"data_apresentacao",
            }
            colunas_presentes = {k: v for k, v in colunas.items() if k in df_props.columns}
            df_props = df_props[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

            # Converte data_apresentacao para datetime (valida formato tambem)
            if "data_apresentacao" in df_props.columns:
                df_props["data_apresentacao"] = pd.to_datetime(
                    df_props["data_apresentacao"], errors="coerce"
                )

            log.info(f"  Apos selecao: {df_props.shape[0]} linhas x {df_props.shape[1]} colunas")

        # --- Autores ---
        log.info("TRANSFORMANDO: Autores -> fato_proposicoes_autores")
        dados_autores = self._ler_json("proposicoes", "proposicoes_autores_")
        df_autores = pd.DataFrame()

        if dados_autores is not None:
            df_autores = self._normalizar(dados_autores)
            log.info(f"  Bruto autores: {df_autores.shape[0]} linhas x {df_autores.shape[1]} colunas")

            colunas_aut = {
                "id_proposicao": "id_proposicao",
                "nome":          "nome_autor",
                "tipo":          "tipo_autor",
                "uri":           "uri_autor"
            }
            colunas_presentes_aut = {k: v for k, v in colunas_aut.items() if k in df_autores.columns}
            df_autores = df_autores[list(colunas_presentes_aut.keys())].rename(columns=colunas_presentes_aut)

        return {
            "proposicoes": df_props,
            "autores":     df_autores
        }


# =============================================================================
# CLASSE: TransformadorVotacoes
# Responsabilidade: transformar votacoes e votos individuais.
# =============================================================================
class TransformadorVotacoes(TransformadorBase):
    """Transforma votacoes e votos individuais."""

    def transformar(self):
        """
        Retorna:
            dict com chaves "votacoes" e "votos" (DataFrames)
        """
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Votacoes -> fato_votacoes")
        log.info("-" * 50)

        # --- Votacoes ---
        dados_vots = self._ler_json("votacoes", "votacoes_")
        df_vots = pd.DataFrame()

        if dados_vots is not None:
            df_vots = self._normalizar(dados_vots)
            log.info(f"  Bruto: {df_vots.shape[0]} linhas x {df_vots.shape[1]} colunas")

            colunas = {
                "id":               "id_votacao",
                "descricao":        "descricao",
                "dataHoraRegistro": "data_hora_registro",
                "aprovacao":        "aprovacao",
            }
            # Inclui id da proposicao vinculada se existir (pode estar aninhado)
            if "proposicaoObjeto" in df_vots.columns:
                colunas["proposicaoObjeto"] = "proposicao_objeto"

            colunas_presentes = {k: v for k, v in colunas.items() if k in df_vots.columns}
            df_vots = df_vots[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

            if "data_hora_registro" in df_vots.columns:
                df_vots["data_hora_registro"] = pd.to_datetime(
                    df_vots["data_hora_registro"], errors="coerce"
                )

            log.info(f"  Apos selecao: {df_vots.shape[0]} linhas x {df_vots.shape[1]} colunas")

        # --- Votos individuais ---
        log.info("TRANSFORMANDO: Votos -> fato_votos")
        dados_votos = self._ler_json("votacoes", "votos_")
        df_votos = pd.DataFrame()

        if dados_votos is not None:
            # json_normalize expande o campo aninhado "deputado_"
            df_votos = pd.json_normalize(
                dados_votos,
                sep="_"
            )
            log.info(f"  Bruto votos: {df_votos.shape[0]} linhas x {df_votos.shape[1]} colunas")
            log.info(f"  Colunas: {list(df_votos.columns)}")

            # Campos possiveis apos normalizacao do campo aninhado deputado_
            colunas_votos = {
                "id_votacao":            "id_votacao",
                "tipoVoto":              "tipo_voto",
                "deputado__id":          "id_deputado",
                "deputado__nome":        "nome_deputado",
                "deputado__siglaPartido":"sigla_partido",
                "deputado__siglaUf":     "sigla_uf",
            }
            colunas_presentes_v = {k: v for k, v in colunas_votos.items() if k in df_votos.columns}
            if colunas_presentes_v:
                df_votos = df_votos[list(colunas_presentes_v.keys())].rename(columns=colunas_presentes_v)

        return {
            "votacoes": df_vots,
            "votos":    df_votos
        }


# =============================================================================
# CLASSE: ValidadorDados
#
# Responsabilidade UNICA: validar DataFrames antes de carregar no banco.
# Nao sabe nada de HTTP, arquivos ou banco - so valida.
#
# Seguindo a dica do desafio:
#   df[df['valor'] < 0]  -> encontra valores invalidos
#   df.dropna(subset=[]) -> identifica nulos em campos obrigatorios
# =============================================================================
class ValidadorDados:
    """
    Valida DataFrames antes da carga no banco.
    Cada metodo retorna o DataFrame limpo e loga os problemas encontrados.
    """

    def validar(self, df, nome_tabela, campos_obrigatorios=None, coluna_id=None):
        """
        Aplica todas as validacoes em sequencia.
        Retorna o DataFrame validado e um dicionario com o relatorio.

        Validacoes aplicadas:
          1. DataFrame nao vazio
          2. Campos obrigatorios sem nulos
          3. Deduplicacao por coluna de ID
          4. Datas dentro de um range valido (2000 ate hoje)
        """
        relatorio = {
            "tabela":     nome_tabela,
            "original":   len(df),
            "alertas":    []
        }

        if df.empty:
            log.warning(f"  [{nome_tabela}] DataFrame vazio - nenhuma validacao aplicada.")
            relatorio["final"] = 0
            return df, relatorio

        # 1. Campos obrigatorios nao nulos
        if campos_obrigatorios:
            df, relatorio = self._validar_nulos(df, campos_obrigatorios, nome_tabela, relatorio)

        # 2. Deduplicacao por ID
        if coluna_id and coluna_id in df.columns:
            df, relatorio = self._deduplicar(df, coluna_id, nome_tabela, relatorio)

        # 3. Validacao de datas
        colunas_data = [c for c in df.columns if "data" in c.lower()]
        for col in colunas_data:
            df, relatorio = self._validar_datas(df, col, nome_tabela, relatorio)

        relatorio["final"] = len(df)
        removidos = relatorio["original"] - relatorio["final"]
        log.info(f"  [{nome_tabela}] Validacao concluida: {relatorio['final']} linhas validas | {removidos} removidas")

        return df, relatorio

    def _validar_nulos(self, df, campos, nome_tabela, relatorio):
        """Remove linhas com nulos em campos obrigatorios e reporta."""
        antes = len(df)
        df_valido = df.dropna(subset=[c for c in campos if c in df.columns])
        nulos = antes - len(df_valido)

        if nulos > 0:
            msg = f"  [{nome_tabela}] {nulos} linhas com nulos em campos obrigatorios {campos}"
            log.warning(msg)
            relatorio["alertas"].append(msg)

            # Mostra quais campos tem mais nulos (util para debugar)
            for campo in campos:
                if campo in df.columns:
                    qtd = df[campo].isna().sum()
                    if qtd > 0:
                        log.warning(f"    -> Campo '{campo}': {qtd} nulos")

        return df_valido, relatorio

    def _deduplicar(self, df, coluna_id, nome_tabela, relatorio):
        """Remove registros duplicados pela coluna de ID."""
        antes = len(df)
        df_dedup = df.drop_duplicates(subset=[coluna_id], keep="first")
        duplicados = antes - len(df_dedup)

        if duplicados > 0:
            msg = f"  [{nome_tabela}] {duplicados} registros duplicados removidos (por '{coluna_id}')"
            log.warning(msg)
            relatorio["alertas"].append(msg)

        return df_dedup, relatorio

    def _validar_datas(self, df, coluna, nome_tabela, relatorio):
        """
        Identifica e remove datas invalidas (nulas apos conversao
        ou fora do range 2000-hoje).

        Tecnica ensinada no curso:
          df[df['coluna'] < valor]  -> filtra linhas invalidas
        """
        if coluna not in df.columns:
            return df, relatorio

        # Tenta converter para datetime se ainda nao for
        if not pd.api.types.is_datetime64_any_dtype(df[coluna]):
            df[coluna] = pd.to_datetime(df[coluna], errors="coerce")

        # Datas nulas apos conversao (formato invalido)
        nulas = df[coluna].isna().sum()
        if nulas > 0:
            msg = f"  [{nome_tabela}] {nulas} datas invalidas/nulas em '{coluna}'"
            log.warning(msg)
            relatorio["alertas"].append(msg)

        # Datas fora do range valido (ex: anos absurdos)
        data_min = pd.Timestamp("2000-01-01")
        data_max = pd.Timestamp(datetime.today())

        # df[condicao] - padrao ensinado no desafio para encontrar invalidos
        invalidas = df[(df[coluna].notna()) & ((df[coluna] < data_min) | (df[coluna] > data_max))]
        if len(invalidas) > 0:
            msg = f"  [{nome_tabela}] {len(invalidas)} datas fora do range valido em '{coluna}'"
            log.warning(msg)
            relatorio["alertas"].append(msg)
            df = df[~((df[coluna].notna()) & ((df[coluna] < data_min) | (df[coluna] > data_max)))]

        return df, relatorio

    def validar_valores_positivos(self, df, colunas_monetarias, nome_tabela):
        """
        Valida que colunas monetarias nao tenham valores negativos.
        Tecnica direta do desafio: df[df['valor'] < 0]
        """
        for col in colunas_monetarias:
            if col not in df.columns:
                continue
            negativos = df[df[col] < 0]
            if len(negativos) > 0:
                log.warning(f"  [{nome_tabela}] {len(negativos)} valores negativos em '{col}'")
                # Remove os negativos (ou substitui por NaN conforme regra de negocio)
                df = df[df[col] >= 0]
        return df


# =============================================================================
# CLASSE: CargaPostgreSQL
#
# Responsabilidade UNICA: persistir DataFrames no PostgreSQL.
# Nao sabe nada de transformacao ou validacao - so carrega.
#
# Usa SQLAlchemy (recomendado com pandas .to_sql()) e psycopg2 como driver.
# =============================================================================
class CargaPostgreSQL:
    """
    Gerencia a conexao com o PostgreSQL e a carga dos DataFrames.

    Compativel com Supabase, Neon, Railway e PostgreSQL local.
    A connection string vem do arquivo .env - nunca hardcodada.
    """

    def __init__(self, database_url):
        """
        Parametros:
            database_url (str): connection string PostgreSQL
                Ex: postgresql://user:pass@host:5432/dbname
        """
        self.database_url = database_url
        self.engine       = None

    def conectar(self):
        """
        Cria o engine SQLAlchemy.
        Testa a conexao antes de prosseguir.

        Retorna True se conectou, False se falhou.
        """
        try:
            self.engine = create_engine(self.database_url)
            # Testa a conexao com uma query simples
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("  Conexao com PostgreSQL estabelecida com sucesso.")
            return True
        except SQLAlchemyError as e:
            log.error(f"  Erro ao conectar no PostgreSQL: {e}")
            return False
        except Exception as e:
            log.error(f"  Erro inesperado na conexao: {e}")
            return False

    def carregar(self, df, nome_tabela, if_exists="replace"):
        """
        Carrega um DataFrame no PostgreSQL usando df.to_sql().

        Parametros:
            df          (DataFrame): dados a carregar
            nome_tabela (str): nome da tabela no banco
            if_exists   (str): "replace" recriar | "append" adicionar | "fail" erro se existir

        Por que "replace" por padrao?
        Na Etapa 3 do desafio, recriamos as tabelas a cada execucao.
        Em producao voce mudaria para "append" com logica de upsert.
        """
        if df.empty:
            log.warning(f"  [{nome_tabela}] DataFrame vazio - carga ignorada.")
            return 0

        if self.engine is None:
            log.error(f"  [{nome_tabela}] Sem conexao com o banco. Chame conectar() primeiro.")
            return 0

        try:
            linhas = df.to_sql(
                nome_tabela,
                con=self.engine,
                if_exists=if_exists,
                index=False,         # nao inclui o indice do pandas como coluna
                method="multi",      # insere varios registros por vez (mais rapido)
                chunksize=500        # lotes de 500 para nao sobrecarregar a conexao
            )
            qtd = len(df)
            log.info(f"  [{nome_tabela}] {qtd} registros carregados com sucesso.")
            return qtd
        except SQLAlchemyError as e:
            log.error(f"  [{nome_tabela}] Erro SQLAlchemy ao carregar: {e}")
        except Exception as e:
            log.error(f"  [{nome_tabela}] Erro inesperado ao carregar: {e}")

        return 0

    def desconectar(self):
        """Fecha o engine e libera conexoes do pool."""
        if self.engine:
            self.engine.dispose()
            log.info("  Conexao com PostgreSQL encerrada.")


# =============================================================================
# CLASSE: PipelineEtapa3
#
# Responsabilidade: orquestrar transformacao + validacao + carga.
# Nao sabe nada de HTTP, arquivos ou SQL - so coordena as pecas.
# Analogo ao PipelineService da Etapa 2.
# =============================================================================
class PipelineEtapa3:
    """
    Orquestra o pipeline ETL da Etapa 3:
      1. Transforma cada conjunto de dados (JSON -> DataFrame limpo)
      2. Valida os DataFrames (nulos, duplicados, datas invalidas)
      3. Carrega no PostgreSQL (modelo estrela: dim + fato)
    """

    def __init__(self, raw_dir, database_url):
        self.raw_dir = raw_dir

        # Instancia cada peca com sua responsabilidade separada
        self.t_deputados  = TransformadorDeputados(raw_dir)
        self.t_partidos   = TransformadorPartidos(raw_dir)
        self.t_props      = TransformadorProposicoes(raw_dir)
        self.t_vots       = TransformadorVotacoes(raw_dir)
        self.validador    = ValidadorDados()
        self.banco        = CargaPostgreSQL(database_url)

    def executar(self):
        """
        Executa o pipeline completo e retorna um resumo dos resultados.
        """
        import time
        inicio = time.time()

        log.info("BUSSOLA PUBLICA - Pipeline ETL | Etapa 3: Transformacao + Carga")
        log.info(f"  Fonte   : {self.raw_dir}")

        resumo = {}   # dicionario para acumular resultados - padrao do curso

        # --- Conecta ao banco ---
        if not self.banco.conectar():
            log.error("Pipeline abortado: nao foi possivel conectar ao banco.")
            return resumo

        # --- 1. Dimensao: Deputados ---
        try:
            df_dep = self.t_deputados.transformar()
            df_dep, _ = self.validador.validar(
                df_dep, "dim_deputados",
                campos_obrigatorios=["id_deputado", "nome"],
                coluna_id="id_deputado"
            )
            resumo["dim_deputados"] = self.banco.carregar(df_dep, "dim_deputados")
        except Exception as e:
            log.error(f"Falha em dim_deputados: {e}")
            resumo["dim_deputados"] = "ERRO"

        # --- 2. Dimensao: Partidos ---
        try:
            df_part = self.t_partidos.transformar()
            df_part, _ = self.validador.validar(
                df_part, "dim_partidos",
                campos_obrigatorios=["id_partido", "sigla"],
                coluna_id="id_partido"
            )
            resumo["dim_partidos"] = self.banco.carregar(df_part, "dim_partidos")
        except Exception as e:
            log.error(f"Falha em dim_partidos: {e}")
            resumo["dim_partidos"] = "ERRO"

        # --- 3. Fato: Proposicoes + Autores ---
        try:
            resultado_props = self.t_props.transformar()

            df_props = resultado_props["proposicoes"]
            df_props, _ = self.validador.validar(
                df_props, "fato_proposicoes",
                campos_obrigatorios=["id_proposicao", "ementa"],
                coluna_id="id_proposicao"
            )
            resumo["fato_proposicoes"] = self.banco.carregar(df_props, "fato_proposicoes")

            df_autores = resultado_props["autores"]
            df_autores, _ = self.validador.validar(
                df_autores, "fato_proposicoes_autores",
                campos_obrigatorios=["id_proposicao"]
            )
            resumo["fato_proposicoes_autores"] = self.banco.carregar(
                df_autores, "fato_proposicoes_autores"
            )
        except Exception as e:
            log.error(f"Falha em fato_proposicoes: {e}")
            resumo["fato_proposicoes"] = "ERRO"

        # --- 4. Fato: Votacoes + Votos ---
        try:
            resultado_vots = self.t_vots.transformar()

            df_vots = resultado_vots["votacoes"]
            df_vots, _ = self.validador.validar(
                df_vots, "fato_votacoes",
                campos_obrigatorios=["id_votacao"],
                coluna_id="id_votacao"
            )
            resumo["fato_votacoes"] = self.banco.carregar(df_vots, "fato_votacoes")

            df_votos = resultado_vots["votos"]
            df_votos, _ = self.validador.validar(
                df_votos, "fato_votos",
                campos_obrigatorios=["id_votacao", "tipo_voto"]
            )
            resumo["fato_votos"] = self.banco.carregar(df_votos, "fato_votos")
        except Exception as e:
            log.error(f"Falha em fato_votacoes: {e}")
            resumo["fato_votacoes"] = "ERRO"

        # --- Finaliza ---
        self.banco.desconectar()
        duracao = time.time() - inicio

        log.info("")
        log.info("ETAPA 3 CONCLUIDA - Resumo de carga:")
        for tabela, qtd in resumo.items():
            status = f"{qtd} registros" if isinstance(qtd, int) else qtd
            log.info(f"  {tabela:35s}: {status}")
        log.info(f"  Duracao total: {duracao:.1f}s")
        log.info("Proximo passo -> Etapa 4: Classificacao com IA Generativa.")

        return resumo


# =============================================================================
# EXECUCAO PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    if not DATABASE_URL:
        log.error("DATABASE_URL nao encontrada! Configure o arquivo .env")
        log.error("Consulte o .env.example para o formato correto.")
        exit(1)

    pipeline = PipelineEtapa3(
        raw_dir      = RAW_DIR,
        database_url = DATABASE_URL
    )
    pipeline.executar()
