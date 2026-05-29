import json
import logging
import pandas as pd
from pathlib import Path

log = logging.getLogger(__name__)

class TransformadorBase:
    """Classe base com métodos comuns de leitura e normalização de JSON brutos."""

    def __init__(self, raw_dir):
        """
        Parâmetros:
            raw_dir (Path): caminho para a pasta com os JSONs brutos
        """
        self.raw_dir = Path(raw_dir)

    def _ler_json(self, subpasta, prefixo):
        """Encontra o arquivo JSON mais recente em raw_dir/subpasta."""
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
        """Usa pd.json_normalize() para achatar campos aninhados."""
        if not dados:
            return pd.DataFrame()
        
        # Se os dados vierem encapsulados na chave "dados", extrai a lista interna
        if isinstance(dados, dict) and "dados" in dados:
            dados = dados["dados"]
            
        try:
            if campos_meta:
                return pd.json_normalize(dados, meta=campos_meta)
            return pd.json_normalize(dados)
        except Exception as e:
            log.warning(f"json_normalize falhou, usando pd.DataFrame: {e}")
            return pd.DataFrame(dados)


class TransformadorDeputados(TransformadorBase):
    """Transforma os dados brutos de deputados em dim_deputados (tabela dimensão)."""

    def transformar(self):
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Deputados -> dim_deputados")
        log.info("-" * 50)

        dados = self._ler_json("deputados", "deputados_")
        if dados is None:
            return pd.DataFrame()

        df = self._normalizar(dados)
        log.info(f"  Bruto: {df.shape[0]} linhas x {df.shape[1]} colunas")

        colunas = {
            "id":            "id_deputado",
            "nome":          "nome",
            "siglaPartido": "sigla_partido",
            "siglaUf":      "sigla_uf",
            "idLegislatura": "id_legislatura",
            "urlFoto":       "url_foto",
            "uri":           "uri"
        }
        
        colunas_presentes = {k: v for k, v in colunas.items() if k in df.columns}
        df = df[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

        log.info(f"  Após seleção: {df.shape[0]} linhas x {df.shape[1]} colunas")
        return df


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
            "id":    "id_partido",
            "sigla": "sigla",
            "nome":  "nome",
            "uri":   "uri"
        }
        colunas_presentes = {k: v for k, v in colunas.items() if k in df.columns}
        df = df[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

        log.info(f"  Após seleção: {df.shape[0]} linhas x {df.shape[1]} colunas")
        return df


class TransformadorProposicoes(TransformadorBase):
    """Transforma proposições em fato_proposicoes e tabela de autores."""

    def transformar(self):
        """Retorna um dict contendo os DataFrames 'proposicoes' e 'autores'."""
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Proposicoes -> fato_proposicoes")
        log.info("-" * 50)

        # --- Proposições ---
        pasta = self.raw_dir / "proposicoes"
        arquivos_props = sorted(pasta.glob("proposicoes_20*.json"), reverse=True)
        
        dados_props = None
        if arquivos_props:
            log.info(f"  Lendo: {arquivos_props[0]}")
            with open(arquivos_props[0], encoding="utf-8") as f:
                dados_props = json.load(f)

        if dados_props is not None:
            df_props = self._normalizar(dados_props)
            log.info(f"  Bruto: {df_props.shape[0]} linhas x {df_props.shape[1]} colunas")

            colunas = {
                "id":               "id_proposicao",
                "siglaTipo":        "sigla_tipo",
                "numero":           "numero",
                "ano":              "ano",
                "ementa":           "ementa",
                "dataApresentacao": "data_apresentacao",
            }
            colunas_presentes = {k: v for k, v in colunas.items() if k in df_props.columns}
            df_props = df_props[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

            if "data_apresentacao" in df_props.columns:
                df_props["data_apresentacao"] = pd.to_datetime(
                    df_props["data_apresentacao"], errors="coerce"
                )

            log.info(f"  Após seleção: {df_props.shape[0]} linhas x {df_props.shape[1]} colunas")

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


class TransformadorVotacoes(TransformadorBase):
    """Transforma votações e votos individuais conforme o schema real do banco."""

    def transformar(self):
        """Retorna um dict contendo os DataFrames 'votacoes' e 'votos'."""
        log.info("-" * 50)
        log.info("TRANSFORMANDO: Votacoes -> fato_votacoes")
        log.info("-" * 50)

        # --- 1. Bloco das Votações ---
        dados_vots = self._ler_json("votacoes", "votacoes_")
        df_vots = pd.DataFrame()

        if dados_vots is not None:
            lista_vots = dados_vots if isinstance(dados_vots, list) else dados_vots.get("dados", [])
            df_vots = pd.json_normalize(lista_vots, sep="_")
            log.info(f"  Bruto votações: {df_vots.shape[0]} linhas x {df_vots.shape[1]} colunas")

            # Mapeamento idêntico à estrutura do seu banco
            colunas_vots = {
                "id": "id_votacao",
                "proposicaoObjeto_id": "proposicao_objeto",
                "dataHoraRegistro": "data_hora_registro",
                "descricao": "descricao",
                "aprovacao": "aprovacao"
            }

            colunas_presentes_vots = {k: v for k, v in colunas_vots.items() if k in df_vots.columns}
            if colunas_presentes_vots:
                df_vots = df_vots[list(colunas_presentes_vots.keys())].rename(columns=colunas_presentes_vots)

            # Garante que colunas que faltam no JSON entrem como None/Null
            for col_banco in colunas_vots.values():
                if col_banco not in df_vots.columns:
                    df_vots[col_banco] = None

            if "data_hora_registro" in df_vots.columns:
                df_vots["data_hora_registro"] = pd.to_datetime(
                    df_vots["data_hora_registro"], errors="coerce"
                )

            # Reordena para casar estritamente com a estrutura básica do banco
            df_vots = df_vots[["id_votacao", "descricao", "data_hora_registro", "aprovacao", "proposicao_objeto"]]
            log.info(f"  Após seleção votações: {df_vots.shape[0]} linhas x {df_vots.shape[1]} colunas")

        # --- 2. Bloco dos Votos Individuais ---
        log.info("TRANSFORMANDO: Votos -> fato_votos")
        dados_votos = self._ler_json("votacoes", "votos_")
        df_votos = pd.DataFrame()

        if dados_votos is not None:
            lista_votos = dados_votos if isinstance(dados_votos, list) else dados_votos.get("dados", [])
            df_votos = pd.json_normalize(lista_votos, sep="_")
            log.info(f"  Bruto votos: {df_votos.shape[0]} linhas x {df_votos.shape[1]} colunas")

            # Mapeamento direcionado para as colunas individuais criadas via SQL
            colunas_votos = {
                "id_votacao": "id_votacao",
                "tipoVoto": "tipo_voto",
                "deputado_id": "id_deputado"
            }
            
            # Tratamento caso o separador do json_normalize venha como '__'
            if "deputado__id" in df_votos.columns:
                colunas_votos["deputado__id"] = "id_deputado"

            colunas_presentes_votos = {k: v for k, v in colunas_votos.items() if k in df_votos.columns}
            if colunas_presentes_votos:
                df_votos = df_votos[list(colunas_presentes_votos.keys())].rename(columns=colunas_presentes_votos)

            # Garante a tipagem de inteiro para o ID do deputado, permitindo valores nulos (Int64 com I maiúsculo)
            if "id_deputado" in df_votos.columns:
                df_votos["id_deputado"] = pd.to_numeric(df_votos["id_deputado"], errors="coerce").astype("Int64")

            log.info(f"  Após seleção votos: {df_votos.shape[0]} linhas x {df_votos.shape[1]} colunas")

        return {
            "votacoes": df_vots,
            "votos": df_votos
        }