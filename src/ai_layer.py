import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES CONFIGURÁVEIS DA CAMADA DE IA
# =============================================================================
LIMIAR_TEMA = 0.35  # Limiar de corte para similaridade de cosseno

# Médias e custos estimados para controle financeiro
TOKENS_MEDIOS_INPUT_RESUMO = 300
TOKENS_MEDIOS_OUTPUT_RESUMO = 150
TOKENS_MEDIOS_EMENTA = 250  # Média de tokens por ementa para Embedding

CUSTO_INPUT_POR_1K_TOKENS = {"gpt-4o": 0.0025, "gpt-4o-mini": 0.000150}
CUSTO_OUTPUT_POR_1K_TOKENS = {"gpt-4o": 0.010, "gpt-4o-mini": 0.000600}
CUSTO_EMBED_POR_1K_TOKENS = {"text-embedding-3-small": 0.000020}

# Catálogo Fixo de Temas Legislativos
TEMAS = {
    "Tecnologia e IA": "Tecnologia, inteligencia artificial, dados pessoais, internet, telecomunicacoes, inovacao, startups, software, plataformas digitais e regulacao de algoritmos.",
    "Tributario": "Tributos, impostos, reforma tributaria, carga fiscal, ICMS, IRPF, isencoes, incentivos fiscais e arrecadacao.",
    "Saude": "Saude publica, SUS, medicamentos, planos de saude, vigilancia sanitaria, hospitais, vacinas e profissionais de saude.",
    "Trabalho e Previdencia": "Direitos trabalhistas, CLT, emprego, salario minimo, sindicatos, previdencia social, aposentadoria e relacoes de trabalho.",
    "Meio Ambiente": "Meio ambiente, clima, licenciamento ambiental, desmatamento, saneamento, energia renovavel, residuos e sustentabilidade.",
    "Economia e Financas": "Economia, mercado financeiro, bancos, credito, juros, inflacao, cambio, investimentos e orcamento publico.",
    "Educacao": "Educacao basica e superior, escolas, universidades, FIES, professores, curriculo, financiamento educacional e ensino.",
    "Seguranca Publica": "Seguranca publica, policia, crime, armas, codigo penal, sistema prisional e combate ao trafico.",
    "Agronegocio": "Agronegocio, agricultura, pecuaria, credito rural, defensivos, exportacao de commodities e producao no campo.",
    "Infraestrutura e Transporte": "Infraestrutura, rodovias, portos, aeroportos, mobilidade urbana, concessoes, obras publicas e transporte.",
    "Direitos e Cidadania": "Direitos humanos, igualdade, direitos do consumidor, familia, minorias, acesso a justica e cidadania."
}

# =============================================================================
# CLASSES DE INFRAESTRUTURA DE DADOS
# =============================================================================

class LeitorProposicoes:
    """Lê proposições pendentes de enriquecimento na tabela fato_proposicoes."""
    def __init__(self, engine):
        self.engine = engine

    def _coluna_existe(self, coluna: str) -> bool:
        sql = f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'fato_proposicoes' AND column_name = '{coluna}';
        """
        try:
            with self.engine.connect() as conn:
                return len(conn.execute(text(sql)).fetchall()) > 0
        except Exception:
            return False

    def ler_pendentes_resumo(self, limite=None) -> pd.DataFrame:
        limite_clause = f"LIMIT {limite}" if limite else ""
        filtro = "WHERE resumo_executivo IS NULL" if self._coluna_existe("resumo_executivo") else "WHERE 1=1"
        
        sql = f"""
            SELECT id_proposicao, sigla_tipo, numero, ano, ementa FROM fato_proposicoes
            {filtro} AND ementa IS NOT NULL AND trim(ementa) <> ''
            ORDER BY data_apresentacao DESC NULLS LAST {limite_clause};
        """
        return pd.read_sql(text(sql), con=self.engine)

    def ler_pendentes_tema(self, limite=None) -> pd.DataFrame:
        limite_clause = f"LIMIT {limite}" if limite else ""
        filtro = "WHERE tema IS NULL" if self._coluna_existe("tema") else "WHERE 1=1"
        
        sql = f"""
            SELECT id_proposicao, sigla_tipo, numero, ano, ementa FROM fato_proposicoes
            {filtro} AND ementa IS NOT NULL AND trim(ementa) <> ''
            ORDER BY data_apresentacao DESC NULLS LAST {limite_clause};
        """
        return pd.read_sql(text(sql), con=self.engine)


class AtualizadorBanco:
    """Persiste os dados enriquecidos por IA (Resumos e Temas) na tabela fato_proposicoes."""
    def __init__(self, engine):
        self.engine = engine

    def garantir_colunas(self) -> bool:
        sqls = [
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS resumo_executivo TEXT;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS data_resumo TIMESTAMP;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS tema TEXT;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS tema_score FLOAT8;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS data_tema TIMESTAMPTZ;"
        ]
        try:
            with self.engine.begin() as conn:
                for sql in sqls:
                    conn.execute(text(sql))
            return True
        except SQLAlchemyError as e:
            log.error(f"  [DB Update] Falha ao estruturar colunas de IA: {e}")
            return False

    def atualizar_resumo(self, id_proposicao: int, resumo: str) -> bool:
        sql = text("""
            UPDATE fato_proposicoes SET resumo_executivo = :resumo, data_resumo = :data 
            WHERE id_proposicao = :id;
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {"resumo": resumo, "data": datetime.now(), "id": id_proposicao})
            return True
        except SQLAlchemyError:
            return False

    def atualizar_tema(self, id_proposicao: int, tema: str, score: float) -> bool:
        sql = text("""
            UPDATE fato_proposicoes SET tema = :tema, tema_score = :score, data_tema = :data 
            WHERE id_proposicao = :id;
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {"tema": tema, "score": score, "data": datetime.now(), "id": id_proposicao})
            return True
        except SQLAlchemyError:
            return False

    def salvar_backup_json(self, resultados: list, caminho_arquivo: Path):
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
            log.info(f"  [Backup] Dados salvos localmente em: {caminho_arquivo}")
        except Exception as e:
            log.warning(f"  [Backup] Não foi possível salvar cópia em JSON: {e}")

# =============================================================================
# MOTORES DE INTELIGÊNCIA ARTIFICIAL
# =============================================================================

class GeradorResumoExecutivo:
    """Gera resumos executivos usando modelos GPT da OpenAI."""
    SYSTEM_PROMPT = """Você é um analista legislativo sênior da consultoria Bússola Pública.
Sua função é transformar ementas técnicas em resumos claros para executivos.
Máximo 3 frases diretas, estrutura estruturada sem jargão jurídico."""

    def __init__(self, api_key: str, modelo: str = "gpt-4o-mini"):
        self.modelo = modelo
        self.client = OpenAI(api_key=api_key)

    def gerar(self, id_proposicao: int, sigla_tipo: str, numero: str, ano: str, ementa: str) -> str:
        try:
            resposta = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Proposição: {sigla_tipo} {numero}/{ano}\nEmenta: {ementa}"}
                ],
                max_tokens=300,
                temperature=0.3,
                timeout=30
            )
            return resposta.choices[0].message.content.strip()
        except Exception as e:
            log.error(f"  [Erro LLM] Falha no ID {id_proposicao}: {e}")
            return None

    def estimar_custo(self, quantidade: int) -> dict:
        custo_in = CUSTO_INPUT_POR_1K_TOKENS.get(self.modelo, 0.0025)
        custo_out = CUSTO_OUTPUT_POR_1K_TOKENS.get(self.modelo, 0.010)
        t_in = quantidade * TOKENS_MEDIOS_INPUT_RESUMO
        t_out = quantidade * TOKENS_MEDIOS_OUTPUT_RESUMO
        custo_usd = (t_in / 1000 * custo_in) + (t_out / 1000 * custo_out)
        return {"quantidade": quantidade, "tokens": t_in + t_out, "custo_usd": custo_usd, "custo_brl": custo_usd * 5.20}


class ClassificadorTematico:
    """Mapeia proposições em macrotemas via embeddings e similaridade de cosseno."""
    def __init__(self, api_key: str, modelo: str = "text-embedding-3-small"):
        self.modelo = modelo
        self.client = OpenAI(api_key=api_key)
        self.embeds_temas = {}

    def obter_embedding(self, texto: str) -> list:
        try:
            res = self.client.embeddings.create(input=[texto], model=self.modelo)
            return res.data[0].embedding
        except Exception as e:
            log.error(f"  [Erro Embedding]: {e}")
            return None

    def preparar_temas(self) -> bool:
        for tema, desc in TEMAS.items():
            emb = self.obter_embedding(desc)
            if emb:
                self.embeds_temas[tema] = emb
        return len(self.embeds_temas) > 0

    def calcular_cosseno(self, vec_a, vec_b) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def classificar(self, ementa: str):
        emb_ementa = self.obter_embedding(ementa)
        if not emb_ementa:
            return "Outros", 0.0
        
        melhor_tema, melhor_score = "Outros", 0.0
        for tema, emb_tema in self.embeds_temas.items():
            score = self.calcular_cosseno(emb_ementa, emb_tema)
            if score > melhor_score:
                melhor_score = score
                melhor_tema = tema
        
        if melhor_score < LIMIAR_TEMA:
            return "Outros", melhor_score
        return melhor_tema, melhor_score

    def estimar_custo(self, quantidade: int) -> dict:
        custo_emb = CUSTO_EMBED_POR_1K_TOKENS.get(self.modelo, 0.000020)
        tokens = quantidade * TOKENS_MEDIOS_EMENTA if 'TOKENS_MEDIOS_CHILD_EMENTA' in globals() else quantidade * TOKENS_MEDIOS_EMENTA
        custo_usd = (tokens / 1000) * custo_emb
        return {"quantidade": quantidade, "tokens": tokens, "custo_usd": custo_usd, "custo_brl": custo_usd * 5.20}

# =============================================================================
# ORQUESTRADOR COMPLETO DA CAMADA DE IA
# =============================================================================

class PipelineEtapa4:
    """Orquestrador unificado de Governança com Resiliência e Estimativas Financeiras."""
    def __init__(self, database_url: str, openai_api_key: str, modelo_chat: str, modelo_embed: str, batch_size: int, dry_run: bool):
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
        self.processed_dir = Path("data/processed")
        
        self.engine = create_engine(database_url)
        self.leitor = LeitorProposicoes(self.engine)
        self.atualizador = AtualizadorBanco(self.engine)
        
        self.gerador_resumo = GeradorResumoExecutivo(openai_api_key, modelo_chat)
        self.classificador = ClassificadorTematico(openai_api_key, modelo_embed)

    def _testar_conexao(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            return True
        except Exception as e:
            log.error(f"  [Erro Conexão] Banco inacessível: {e}")
            return False

    def executar(self) -> dict:
        inicio = time.time()
        log.info("=" * 60)
        log.info("BÚSSOLA PÚBLICA - ORQUESTRADOR MASTER DE IA")
        log.info("=" * 60)

        if not self._testar_conexao():
            return {"status": "erro", "motivo": "banco_inacessivel"}

        if not self.atualizador.garantir_colunas():
            return {"status": "erro", "motivo": "falha_estrutura_db"}

        # Captura e tratamento de volumes pendentes
        df_resumos = self.leitor.ler_pendentes_resumo(limite=self.batch_size)
        df_temas = self.leitor.ler_pendentes_tema(limite=self.batch_size)

        # ---------------------------------------------------------------------
        # ESTIMATIVAS DE CUSTO FINANCEIRO
        # ---------------------------------------------------------------------
        custo_resumo = self.gerador_resumo.estimar_custo(len(df_resumos)) if not df_resumos.empty else {"custo_usd": 0, "custo_brl": 0, "tokens": 0}
        custo_tema = self.classificador.estimar_custo(len(df_temas)) if not df_temas.empty else {"custo_usd": 0, "custo_brl": 0, "tokens": 0}

        total_usd = custo_resumo["custo_usd"] + custo_tema["custo_usd"]
        total_brl = custo_resumo["custo_brl"] + custo_tema["custo_brl"]

        log.info("\n=== ESTIMATIVA ORÇAMENTÁRIA DO CICLO ===")
        log.info(f"  Resumos Pendentes   : {len(df_resumos)} | Custo Est.: R$ {custo_resumo['custo_brl']:.4f}")
        log.info(f"  Temas Pendentes     : {len(df_temas)} | Custo Est.: R$ {custo_tema['custo_brl']:.4f}")
        log.info(f"  INVESTIMENTO TOTAL  : USD $ {total_usd:.4f} | BRL R$ {total_brl:.4f}")
        log.info("========================================\n")

        if self.dry_run:
            log.info("  [DRY RUN] Simulação concluída com sucesso. Nenhuma linha gravada.")
            return {"status": "dry_run", "custo_estimado_brl": total_brl}

        # ---------------------------------------------------------------------
        # EXECUÇÃO: RESUMOS EXECUTIVOS
        # ---------------------------------------------------------------------
        resultados_resumos = []
        if not df_resumos.empty:
            log.info(f"Processando {len(df_resumos)} resumos executivos...")
            for idx, linha in df_resumos.iterrows():
                resumo = self.gerador_resumo.gerar(linha["id_proposicao"], linha.get("sigla_tipo"), linha.get("numero"), linha.get("ano"), linha["ementa"])
                if resumo and self.atualizador.atualizar_resumo(linha["id_proposicao"], resumo):
                    resultados_resumos.append({"id": linha["id_proposicao"], "resumo": resumo})
                time.sleep(0.2)
            
            if resultados_resumos:
                self.atualizador.salvar_backup_json(resultados_resumos, self.processed_dir / f"resumos_{self.timestamp}.json")

        # ---------------------------------------------------------------------
        # EXECUÇÃO: CLASSIFICAÇÃO TEMÁTICA
        # ---------------------------------------------------------------------
        resultados_temas = []
        if not df_temas.empty:
            log.info(f"Processando {len(df_temas)} classificações temáticas...")
            if self.classificador.preparar_temas():
                for idx, linha in df_temas.iterrows():
                    tema, score = self.classificador.classificar(linha["ementa"])
                    if self.atualizador.atualizar_tema(linha["id_proposicao"], tema, score):
                        resultados_temas.append({"id": linha["id_proposicao"], "tema": tema, "score": score})
                    time.sleep(0.2)
                
                if resultados_temas:
                    self.atualizador.salvar_backup_json(resultados_temas, self.processed_dir / f"temas_{self.timestamp}.json")

        duracao = time.time() - inicio
        log.info(f"\n[SUCESSO] Pipeline completo de IA executado em {duracao:.1f}s.")
        self.engine.dispose()
        return {"status": "sucesso", "resumos_processados": len(resultados_resumos), "temas_processados": len(resultados_temas)}