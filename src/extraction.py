import time
import requests
import logging
from src.config import (
    BASE_URL, HEADERS, ITENS_PAG, MAX_TENTATIVAS, 
    ESPERA_RETRY, INICIO, FIM
)

log = logging.getLogger(__name__)

class CamaraAPI:
    """Classe base que encapsula as chamadas HTTP à API da Câmara."""
    def __init__(self, base_url=BASE_URL, headers=HEADERS, itens_por_pagina=ITENS_PAG):
        self.base_url = base_url
        self.headers = headers
        self.itens_por_pagina = itens_por_pagina

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                resposta = requests.get(
                    url, headers=self.headers, params=params, timeout=20
                )
                resposta.raise_for_status()
                return resposta.json()
            except requests.exceptions.Timeout:
                log.warning(f"Timeout ({tentativa}/{MAX_TENTATIVAS}): {endpoint}")
            except requests.exceptions.ConnectionError:
                log.warning(f"Sem conexão ({tentativa}/{MAX_TENTATIVAS}): {endpoint}")
            except requests.exceptions.HTTPError as e:
                log.error(f"Erro HTTP: {e} | endpoint: {endpoint}")
                return None
            except Exception as e:
                log.error(f"Erro inesperado: {e}")
                return None

            if tentativa < MAX_TENTATIVAS:
                log.info(f"Aguardando {ESPERA_RETRY}s antes de tentar novamente...")
                time.sleep(ESPERA_RETRY)
        return None

    def _get_paginado(self, endpoint, params=None, descricao=""):
        params = params or {}
        params["itens"] = self.itens_por_pagina
        registros = []
        pagina = 1

        log.info(f"Extraindo: {descricao or endpoint}")
        while True:
            params["pagina"] = pagina
            log.info(f"  Página {pagina} | registros acumulados: {len(registros)}")
            resposta = self._get(endpoint, params=params.copy())

            if not resposta:
                log.error(f"Resposta nula na página {pagina}. Interrompendo.")
                break

            dados_pagina = resposta.get("dados", [])
            if not dados_pagina:
                log.info(f"  Página {pagina} vazia - paginação encerrada.")
                break

            for item in dados_pagina:
                registros.append(item)

            links = resposta.get("links", [])
            tem_next = any(l.get("rel") == "next" for l in links if isinstance(l, dict))

            if not tem_next:
                log.info(f"  Sem mais páginas. Total: {len(registros)} registros.")
                break

            pagina += 1
            time.sleep(0.3)
        return registros

class DeputadosExtractor(CamaraAPI):
    """Extrai todos os deputados em exercício na legislatura atual."""
    def extrair(self):
        log.info("-" * 50)
        log.info("EXTRATOR: Deputados")
        log.info("-" * 50)
        return self._get_paginado(
            "/deputados",
            params={"ordem": "ASC", "ordenarPor": "nome"},
            descricao="Deputados em exercício"
        )

class ProposicoesExtractor(CamaraAPI):
    """Extrai proposições do período informado e seus respectivos autores."""
    def extrair(self, data_inicio=INICIO, data_fim=FIM):
        log.info("-" * 50)
        log.info(f"EXTRATOR: Proposições ({data_inicio} -> {data_fim})")
        log.info("-" * 50)
        
        proposicoes = self._get_paginado(
            "/proposicoes",
            params={
                "dataInicio": data_inicio,
                "dataFim": data_fim,
                "ordem": "DESC",
                "ordenarPor": "id"
            },
            descricao="Proposições"
        )

        autores = []
        erros = 0
        log.info(f"  Buscando autores de {len(proposicoes)} proposições...")

        for i, prop in enumerate(proposicoes):
            id_prop = prop["id"]
            resposta = self._get(f"/proposicoes/{id_prop}/autores")

            if resposta and resposta.get("dados"):
                for autor in resposta["dados"]:
                    autor["id_proposicao"] = id_prop
                    autores.append(autor)
            else:
                erros += 1

            if (i + 1) % 50 == 0:
                log.info(f"    Progresso autores: {i+1}/{len(proposicoes)} | erros: {erros}")
            time.sleep(0.2)

        log.info(f"  Autores extraídos: {len(autores)} | erros: {erros}")
        return {"proposicoes": proposicoes, "autores": autores}

class VotacoesExtractor(CamaraAPI):
    """Extrai votações do período informado e os votos individuais."""
    def extrair(self, data_inicio=INICIO, data_fim=FIM):
        log.info("-" * 50)
        log.info(f"EXTRATOR: Votações ({data_inicio} -> {data_fim})")
        log.info("-" * 50)

        votacoes = self._get_paginado(
            "/votacoes",
            params={
                "dataInicio": data_inicio,
                "dataFim": data_fim,
                "ordem": "DESC",
                "ordenarPor": "dataHoraRegistro"
            },
            descricao="Votações"
        )

        if not votacoes:
            log.warning("Nenhuma votação encontrada no período.")
            return {"votacoes": [], "votos": []}

        votos = []
        erros = 0
        log.info(f"  Buscando votos individuais de {len(votacoes)} votações...")

        for i, vot in enumerate(votacoes):
            id_vot = vot["id"]
            resposta = self._get(f"/votacoes/{id_vot}/votos")

            if resposta and resposta.get("dados"):
                for voto in resposta["dados"]:
                    voto["id_votacao"] = id_vot
                    votos.append(voto)
            else:
                erros += 1

            if (i + 1) % 20 == 0:
                log.info(f"    Progresso votos: {i+1}/{len(votacoes)} | erros: {erros}")
            time.sleep(0.2)

        log.info(f"  Votos individuais extraídos: {len(votos)} | erros: {erros}")
        return {"votacoes": votacoes, "votos": votos}

class PartidosExtractor(CamaraAPI):
    """Extrai todos os partidos políticos cadastrados."""
    def extrair(self):
        log.info("-" * 50)
        log.info("EXTRATOR: Partidos")
        log.info("-" * 50)
        return self._get_paginado(
            "/partidos",
            params={"ordem": "ASC", "ordenarPor": "sigla"},
            descricao="Partidos políticos"
        )