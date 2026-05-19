"""
=============================================================================
BUSSOLA PUBLICA - Projeto Integrador | Pos Tech Engenharia de Dados e IA
=============================================================================
Etapa 2: Extracao com Python

Boas praticas aplicadas (Nivelamento + APIs + POO / Prof. Iago Braz / Xperiun):

  POO (Programacao Orientada a Objetos):
    - Classe base CamaraAPI  -> __init__, self, metodos HTTP reutilizaveis
    - Classes extratoras     -> herdam CamaraAPI, responsabilidade unica
    - Classe PipelineService -> orquestra tudo (separacao de responsabilidades)

  Boas praticas de APIs:
    - try/except com excecoes especificas (Timeout, ConnectionError, HTTPError)
    - timeout em todas as requisicoes
    - raise_for_status() para detectar erros 4xx/5xx
    - time.sleep() entre requisicoes (rate limit)
    - Paginacao com while loop e controle manual de saida

  Padroes de dados (Capitulo 8 do curso):
    - Lista vazia -> for -> .append() para acumular registros
    - Dicionario  -> pd.DataFrame() para estruturar tabelas
    - JSON bruto salvo em disco ANTES de qualquer transformacao
    - Logging para rastrear erros em producao

Como usar:
    pip install requests pandas
    python etapa2_extracao.py

Estrutura de saida:
    data/raw/deputados/deputados_YYYYMMDD.json
    data/raw/proposicoes/proposicoes_YYYYMMDD.json
    data/raw/proposicoes/proposicoes_autores_YYYYMMDD.json
    data/raw/votacoes/votacoes_YYYYMMDD.json
    data/raw/votacoes/votos_YYYYMMDD.json
    data/raw/partidos/partidos_YYYYMMDD.json
=============================================================================
"""

# PASSO 1: Importar bibliotecas
import requests       # chamadas HTTP a API
import pandas as pd   # transformar dicionarios em tabelas
import json           # salvar JSON bruto em disco
import time           # time.sleep() - respeitar rate limit da API
import logging        # registrar logs de execucao
from pathlib import Path
from datetime import datetime, timedelta


# PASSO 2: Configuracoes globais
BASE_URL       = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS        = {"Accept": "application/json"}
ITENS_PAG      = 100     # max por pagina na API
MAX_TENTATIVAS = 3       # retries antes de desistir
ESPERA_RETRY   = 5       # segundos entre tentativas

# Janela de 30 dias (proposicoes e votacoes)
HOJE   = datetime.today()
INICIO = (HOJE - timedelta(days=30)).strftime("%Y-%m-%d")
FIM    = HOJE.strftime("%Y-%m-%d")
DATA   = HOJE.strftime("%Y%m%d")  # timestamp para nomear arquivos

# Configuracao de log - console E arquivo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"extracao_{DATA}.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# =============================================================================
# CLASSE BASE: CamaraAPI
#
# Seguindo o modulo de POO:
#   - __init__  -> configura base_url e headers uma unica vez
#   - self      -> cada instancia carrega sua propria configuracao
#   - metodos   -> acoes reutilizaveis por todas as classes filhas
#
# Separacao de responsabilidade: essa classe so sabe BUSCAR dados.
# Nao sabe nada sobre Camara, deputados ou proposicoes - generica por design.
# =============================================================================
class CamaraAPI:
    """
    Classe base que encapsula as chamadas HTTP a API da Camara.
    Qualquer extrator especifico herda daqui - sem repetir codigo de requisicao.
    """

    def __init__(self, base_url, headers, itens_por_pagina=100):
        """
        Inicializa a conexao com a API.

        self = o ponteiro que da identidade unica ao objeto (modulo POO).
        Sem self, o Python nao sabe de qual instancia estamos falando.
        """
        self.base_url         = base_url
        self.headers          = headers
        self.itens_por_pagina = itens_por_pagina

    def _get(self, endpoint, params=None):
        """
        Realiza uma chamada GET com retry automatico e tratamento de erros.

        Boas praticas do curso:
          - timeout em toda requisicao
          - raise_for_status() para detectar erros HTTP
          - try/except com excecoes especificas
          - retorna None em vez de quebrar o programa
        """
        url = f"{self.base_url}{endpoint}"

        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                resposta = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=20   # sem timeout = risco de loop infinito em producao
                )
                resposta.raise_for_status()  # HTTPError se status != 2xx
                return resposta.json()       # .json() -> dicionario Python

            except requests.exceptions.Timeout:
                log.warning(f"Timeout ({tentativa}/{MAX_TENTATIVAS}): {endpoint}")

            except requests.exceptions.ConnectionError:
                log.warning(f"Sem conexao ({tentativa}/{MAX_TENTATIVAS}): {endpoint}")

            except requests.exceptions.HTTPError as e:
                log.error(f"Erro HTTP: {e} | endpoint: {endpoint}")
                return None   # erro HTTP nao adianta tentar de novo

            except Exception as e:
                log.error(f"Erro inesperado: {e}")
                return None

            if tentativa < MAX_TENTATIVAS:
                log.info(f"Aguardando {ESPERA_RETRY}s antes de tentar novamente...")
                time.sleep(ESPERA_RETRY)

        return None  # esgotou as tentativas

    def _get_paginado(self, endpoint, params=None, descricao=""):
        """
        Percorre TODAS as paginas de um endpoint e retorna todos os registros.

        Padrao do curso aplicado:
          - lista vazia criada antes do loop
          - for para iterar cada item dentro da pagina
          - .append() para acumular na lista
          - while para controlar a paginacao (nao sabe quantas paginas ha)
        """
        params = params or {}
        params["itens"] = self.itens_por_pagina

        # Padrao lista vazia (Capitulo 4.1 + 8.2 do curso)
        registros = []
        pagina    = 1

        log.info(f"Extraindo: {descricao or endpoint}")

        # Usa while (nao for) porque nao sabe quantas paginas existem de antemao.
        # O while para quando: (a) pagina vazia, ou (b) sem link "next".
        while True:
            params["pagina"] = pagina
            log.info(f"  Pagina {pagina} | registros acumulados: {len(registros)}")

            resposta = self._get(endpoint, params=params.copy())

            if not resposta:
                log.error(f"Resposta nula na pagina {pagina}. Interrompendo.")
                break

            dados_pagina = resposta.get("dados", [])

            if not dados_pagina:
                log.info(f"  Pagina {pagina} vazia - paginacao encerrada.")
                break

            # For + append para acumular (Capitulo 8.2 do curso)
            for item in dados_pagina:
                registros.append(item)

            # Verifica link "next" para saber se tem proxima pagina
            links    = resposta.get("links", [])
            tem_next = any(
                l.get("rel") == "next"
                for l in links
                if isinstance(l, dict)
            )

            if not tem_next:
                log.info(f"  Sem mais paginas. Total: {len(registros)} registros.")
                break

            pagina += 1
            time.sleep(0.3)   # pausa educada - nao sobrecarrega a API

        return registros


# =============================================================================
# CLASSE: DeputadosExtractor
# Herda CamaraAPI. Responsabilidade unica: extrair deputados.
# Nao sabe nada sobre proposicoes ou votacoes.
# =============================================================================
class DeputadosExtractor(CamaraAPI):
    """Extrai todos os deputados em exercicio na legislatura atual."""

    def extrair(self):
        """
        Busca todos os deputados e retorna como lista de dicionarios.
        A lista esta pronta para virar DataFrame com pd.DataFrame().
        """
        log.info("-" * 50)
        log.info("EXTRATOR: Deputados")
        log.info("-" * 50)

        deputados = self._get_paginado(
            "/deputados",
            params={"ordem": "ASC", "ordenarPor": "nome"},
            descricao="Deputados em exercicio"
        )
        return deputados


# =============================================================================
# CLASSE: ProposicoesExtractor
# Responsabilidade: extrair proposicoes e seus autores.
# Retorna dicionario com duas listas: "proposicoes" e "autores".
# =============================================================================
class ProposicoesExtractor(CamaraAPI):
    """Extrai proposicoes dos ultimos 30 dias e seus respectivos autores."""

    def extrair(self, data_inicio, data_fim):
        """
        Busca proposicoes no periodo informado.
        Para cada proposicao, busca tambem os autores (/autores).

        Retorna:
            dict com chaves "proposicoes" e "autores" (listas de dicionarios)
        """
        log.info("-" * 50)
        log.info(f"EXTRATOR: Proposicoes ({data_inicio} -> {data_fim})")
        log.info("-" * 50)

        proposicoes = self._get_paginado(
            "/proposicoes",
            params={
                "dataInicio": data_inicio,
                "dataFim":    data_fim,
                "ordem":      "DESC",
                "ordenarPor": "id"
            },
            descricao="Proposicoes"
        )

        # Buscar autores de cada proposicao (lista vazia + for + append)
        autores = []   # lista vazia
        erros   = 0

        log.info(f"  Buscando autores de {len(proposicoes)} proposicoes...")

        for i, prop in enumerate(proposicoes):
            id_prop  = prop["id"]
            resposta = self._get(f"/proposicoes/{id_prop}/autores")

            if resposta and resposta.get("dados"):
                for autor in resposta["dados"]:
                    autor["id_proposicao"] = id_prop   # chave de join
                    autores.append(autor)              # append acumula
            else:
                erros += 1

            if (i + 1) % 50 == 0:
                log.info(f"    Progresso autores: {i+1}/{len(proposicoes)} | erros: {erros}")

            time.sleep(0.2)

        log.info(f"  Autores extraidos: {len(autores)} | erros: {erros}")

        # Retorna dicionario - cada chave vira um arquivo JSON/tabela separada
        return {
            "proposicoes": proposicoes,
            "autores":     autores
        }


# =============================================================================
# CLASSE: VotacoesExtractor
# Responsabilidade: extrair votacoes e os votos individuais por deputado.
# =============================================================================
class VotacoesExtractor(CamaraAPI):
    """Extrai votacoes dos ultimos 30 dias e os votos individuais."""

    def extrair(self, data_inicio, data_fim):
        """
        Busca votacoes no periodo informado.
        Para cada votacao, busca o voto de cada deputado (/votos).

        Retorna:
            dict com chaves "votacoes" e "votos"
        """
        log.info("-" * 50)
        log.info(f"EXTRATOR: Votacoes ({data_inicio} -> {data_fim})")
        log.info("-" * 50)

        votacoes = self._get_paginado(
            "/votacoes",
            params={
                "dataInicio": data_inicio,
                "dataFim":    data_fim,
                "ordem":      "DESC",
                "ordenarPor": "dataHoraRegistro"
            },
            descricao="Votacoes"
        )

        if not votacoes:
            log.warning("Nenhuma votacao encontrada no periodo.")
            return {"votacoes": [], "votos": []}

        # Votos individuais por votacao (lista vazia + for + append)
        votos = []   # lista vazia - acumula todos os votos
        erros = 0

        log.info(f"  Buscando votos individuais de {len(votacoes)} votacoes...")

        for i, vot in enumerate(votacoes):
            id_vot   = vot["id"]
            resposta = self._get(f"/votacoes/{id_vot}/votos")

            if resposta and resposta.get("dados"):
                for voto in resposta["dados"]:
                    voto["id_votacao"] = id_vot   # chave de join
                    votos.append(voto)            # .append() acumula
            else:
                erros += 1

            if (i + 1) % 20 == 0:
                log.info(f"    Progresso votos: {i+1}/{len(votacoes)} | erros: {erros}")

            time.sleep(0.2)

        log.info(f"  Votos individuais extraidos: {len(votos)} | erros: {erros}")

        return {
            "votacoes": votacoes,
            "votos":    votos
        }


# =============================================================================
# CLASSE: PartidosExtractor
# Responsabilidade unica: extrair partidos. Simples e focado.
# =============================================================================
class PartidosExtractor(CamaraAPI):
    """Extrai todos os partidos politicos cadastrados."""

    def extrair(self):
        log.info("-" * 50)
        log.info("EXTRATOR: Partidos")
        log.info("-" * 50)

        return self._get_paginado(
            "/partidos",
            params={"ordem": "ASC", "ordenarPor": "sigla"},
            descricao="Partidos politicos"
        )


# =============================================================================
# CLASSE: PipelineService
#
# Responsabilidade: orquestrar os extratores e salvar os JSONs em disco.
# Nao sabe nada sobre HTTP - so sabe coordenar e persistir.
#
# Analogo ao PedidoService ensinado no modulo de POO:
#   entidade (dados) e diferente de servico (acao sobre os dados)
# =============================================================================
class PipelineService:
    """
    Orquestra o pipeline ETL:
      1. Chama cada extrator na ordem correta
      2. Salva o JSON bruto em disco (ANTES de transformar)
      3. Converte para DataFrame para conferencia
      4. Gera um resumo ao final

    Por que salvar JSON antes de transformar?
    Se o transform quebrar, voce nao precisa chamar a API de novo.
    Salvou uma vez, transforma quantas vezes quiser.
    """

    def __init__(self, output_dir="data/raw"):
        """
        Parâmetros:
            output_dir (str): pasta raiz para salvar os JSONs brutos
        """
        self.output_dir = Path(output_dir)

        # Instancia os extratores - cada um com sua responsabilidade
        self.dep_extractor  = DeputadosExtractor(BASE_URL, HEADERS, ITENS_PAG)
        self.prop_extractor = ProposicoesExtractor(BASE_URL, HEADERS, ITENS_PAG)
        self.vot_extractor  = VotacoesExtractor(BASE_URL, HEADERS, ITENS_PAG)
        self.part_extractor = PartidosExtractor(BASE_URL, HEADERS, ITENS_PAG)

    def _salvar_json(self, dados, subpasta, nome_arquivo):
        """
        Persiste uma lista de dicionarios como JSON formatado.
        Cria as pastas automaticamente se nao existirem.
        """
        destino = self.output_dir / subpasta
        destino.mkdir(parents=True, exist_ok=True)

        caminho = destino / nome_arquivo
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        tamanho_kb = caminho.stat().st_size / 1024
        log.info(f"  Salvo: {caminho} ({tamanho_kb:.1f} KB | {len(dados)} registros)")
        return caminho

    def _para_dataframe(self, lista, nome):
        """
        Converte lista de dicionarios em DataFrame.
        Padrao: dict -> pd.DataFrame() (Capitulo 7.4 do curso).
        """
        if not lista:
            log.warning(f"  Lista vazia - DataFrame {nome} nao gerado.")
            return pd.DataFrame()

        df = pd.DataFrame(lista)
        log.info(f"\n  Preview '{nome}' ({df.shape[0]} linhas x {df.shape[1]} colunas):")
        print(df.head(3).to_string())
        print()
        return df

    def executar(self):
        """
        Orquestra o pipeline completo.
        Cada extrator e chamado de forma independente -
        se um falhar, os outros continuam (resiliencia).
        """
        log.info("BUSSOLA PUBLICA - Pipeline ETL | Etapa 2: Extracao")
        log.info(f"  Periodo  : {INICIO} -> {FIM}")
        log.info(f"  Saida    : {self.output_dir.resolve()}")

        inicio  = time.time()
        resumo  = {}   # dicionario para acumular contagens

        # 1. Deputados
        try:
            deputados = self.dep_extractor.extrair()
            self._salvar_json(deputados, "deputados", f"deputados_{DATA}.json")
            self._para_dataframe(deputados, "deputados")
            resumo["deputados"] = len(deputados)
        except Exception as e:
            log.error(f"Falha no extrator de Deputados: {e}")
            resumo["deputados"] = "ERRO"

        # 2. Proposicoes + Autores
        try:
            resultado_props = self.prop_extractor.extrair(INICIO, FIM)
            self._salvar_json(
                resultado_props["proposicoes"],
                "proposicoes",
                f"proposicoes_{DATA}.json"
            )
            self._salvar_json(
                resultado_props["autores"],
                "proposicoes",
                f"proposicoes_autores_{DATA}.json"
            )
            self._para_dataframe(resultado_props["proposicoes"], "proposicoes")
            resumo["proposicoes"] = len(resultado_props["proposicoes"])
            resumo["autores"]     = len(resultado_props["autores"])
        except Exception as e:
            log.error(f"Falha no extrator de Proposicoes: {e}")
            resumo["proposicoes"] = "ERRO"

        # 3. Votacoes + Votos individuais
        try:
            resultado_vots = self.vot_extractor.extrair(INICIO, FIM)
            self._salvar_json(
                resultado_vots["votacoes"],
                "votacoes",
                f"votacoes_{DATA}.json"
            )
            self._salvar_json(
                resultado_vots["votos"],
                "votacoes",
                f"votos_{DATA}.json"
            )
            self._para_dataframe(resultado_vots["votacoes"], "votacoes")
            resumo["votacoes"] = len(resultado_vots["votacoes"])
            resumo["votos"]    = len(resultado_vots["votos"])
        except Exception as e:
            log.error(f"Falha no extrator de Votacoes: {e}")
            resumo["votacoes"] = "ERRO"

        # 4. Partidos
        try:
            partidos = self.part_extractor.extrair()
            self._salvar_json(partidos, "partidos", f"partidos_{DATA}.json")
            self._para_dataframe(partidos, "partidos")
            resumo["partidos"] = len(partidos)
        except Exception as e:
            log.error(f"Falha no extrator de Partidos: {e}")
            resumo["partidos"] = "ERRO"

        # Resumo final
        duracao = time.time() - inicio
        log.info("")
        log.info("EXTRACAO CONCLUIDA - Resumo:")
        for tabela, qtd in resumo.items():
            status = f"{qtd} registros" if isinstance(qtd, int) else qtd
            log.info(f"  {tabela:22s}: {status}")
        log.info(f"  Duracao total        : {duracao:.1f}s")
        log.info(f"  JSONs salvos em      : {self.output_dir.resolve()}")
        log.info("JSONs brutos prontos. Proximo passo -> Etapa 3: Transformacao.")

        return resumo


# =============================================================================
# EXECUCAO PRINCIPAL
# Instancia o PipelineService (separacao de responsabilidades - modulo POO)
# e dispara o pipeline completo com .executar().
# =============================================================================
if __name__ == "__main__":
    pipeline = PipelineService(output_dir="data/raw")
    pipeline.executar()