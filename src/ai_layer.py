import json
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configuração do Logger local caso o arquivo seja chamado diretamente
log = logging.getLogger(__name__)

class LeitorProposicoes:
    """
    Lê proposições pendentes de resumo na tabela fato_proposicoes.

    'Pendente' significa: resumo_executivo IS NULL ou coluna não existe.
    Isso torna a etapa idempotente: pode rodar várias vezes sem
    reprocessar o que já foi feito.
    """

    def __init__(self, engine):
        """
        Parâmetros:
            engine: SQLAlchemy engine conectado ao PostgreSQL (Supabase)
        """
        self.engine = engine

    def ler_pendentes(self, limite=None) -> pd.DataFrame:
        """
        Retorna um DataFrame com proposições que ainda não têm resumo.

        Parâmetros:
            limite (int): máximo de registros a retornar (None = sem limite)

        Retorna:
            DataFrame com colunas: id_proposicao, sigla_tipo, numero, ano, ementa
        """
        log.info("-" * 50)
        log.info("LEITURA: Proposições pendentes de resumo")
        log.info("-" * 50)

        # Verifica se a coluna resumo_executivo já existe na tabela fato_proposicoes
        sql_verifica_coluna = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'fato_proposicoes'
              AND column_name = 'resumo_executivo';
        """

        limite_clause = f"LIMIT {limite}" if limite else ""

        try:
            with self.engine.connect() as conn:
                resultado = conn.execute(text(sql_verifica_coluna)).fetchall()
                coluna_existe = len(resultado) > 0

            if coluna_existe:
                # Busca apenas proposições sem resumo (processamento incremental / idempotente)
                sql = f"""
                    SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                    FROM fato_proposicoes
                    WHERE resumo_executivo IS NULL
                      AND ementa IS NOT NULL
                      AND trim(ementa) <> ''
                    ORDER BY data_apresentacao DESC NULLS LAST
                    {limite_clause};
                """
                log.info("  [IA Layer] Coluna 'resumo_executivo' encontrada - buscando apenas pendentes.")
            else:
                # Primeira execução: busca todas as proposições válidas com ementa
                sql = f"""
                    SELECT id_proposicao, sigla_tipo, numero, ano, ementa
                    FROM fato_proposicoes
                    WHERE ementa IS NOT NULL
                      AND trim(ementa) <> ''
                    ORDER BY data_apresentacao DESC NULLS LAST
                    {limite_clause};
                """
                log.info("  [IA Layer] Primeira execução - coluna 'resumo_executivo' será criada dinamicamente.")

            df = pd.read_sql(text(sql), con=self.engine)
            log.info(f"  [IA Layer] {len(df)} proposições encontradas para processar.")
            return df

        except SQLAlchemyError as e:
            log.error(f"  [Erro Banco] Erro ao ler proposições no PostgreSQL: {e}")
            return pd.DataFrame()
        except Exception as e:
            log.error(f"  [Erro Inesperado] Erro ao identificar registros pendentes: {e}")
            return pd.DataFrame()
        

class GeradorResumoExecutivo:
    """
    Gera resumos executivos de proposições legislativas usando modelos GPT da OpenAI.
    """

    SYSTEM_PROMPT = """Você é um analista legislativo sênior da consultoria Bússola Pública.
Sua função é transformar ementas técnicas de proposições da Câmara dos Deputados
em resumos claros e acionáveis para executivos e áreas de relações governamentais.

Regras para o resumo:
- Máximo 3 frases objetivas
- Linguagem direta, sem jargão jurídico
- Estrutura: (1) O que propõe, (2) Quem/o que é impactado, (3) Ponto de atenção para empresas
- Se a ementa for muito técnica ou vaga, informe isso claramente
- Responda APENAS com o resumo, sem introduções como 'O resumo é:' ou 'Esta proposição...'"""

    USER_PROMPT_TEMPLATE = """Proposição: {sigla_tipo} {numero}/{ano}

Ementa oficial:
{ementa}

Gere o resumo executivo:"""

    # Referência de custos e médias de mercado para controle financeiro
    CUSTO_INPUT_POR_1K_TOKENS = {"gpt-4o": 0.0025, "gpt-4o-mini": 0.000150}
    CUSTO_OUTPUT_POR_1K_TOKENS = {"gpt-4o": 0.010, "gpt-4o-mini": 0.000600}
    TOKENS_MEDIOS_INPUT = 300
    TOKENS_MEDIOS_OUTPUT = 150

    def __init__(self, api_key: str, modelo: str = "gpt-4o-mini"):
        """
        Parâmetros:
            api_key (str): Chave de autenticação da OpenAI API
            modelo (str): Identificador do modelo alvo (ex: gpt-4o-mini)
        """
        self.modelo = modelo
        self.client = OpenAI(api_key=api_key)

    def gerar(self, id_proposicao: int, sigla_tipo: str, numero: str, ano: str, ementa: str) -> str:
        """
        Gera o resumo executivo de uma proposição consumindo a API da OpenAI.
        """
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            sigla_tipo=sigla_tipo or "Proposição",
            numero=numero or "",
            ano=ano or "",
            ementa=ementa.strip()
        )

        try:
            resposta = self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3,
                timeout=30  # Proteção contra travamentos de requisições externas
            )
            resumo = resposta.choices[0].message.content.strip()
            tokens_usados = resposta.usage.total_tokens
            log.info(f"    [ID {id_proposicao}] Resumo gerado com sucesso | {tokens_usados} tokens utilizados.")
            return resumo

        except APITimeoutError:
            log.warning(f"    [ID {id_proposicao}] Timeout na API da OpenAI ao gerar o resumo.")
        except RateLimitError:
            log.warning(f"    [ID {id_proposicao}] Rate limit atingido na OpenAI. Pausando execução por 60s...")
            time.sleep(60)
        except APIConnectionError as e:
            log.error(f"    [ID {id_proposicao}] Falha de conexão de rede com a API da OpenAI: {e}")
        except APIStatusError as e:
            log.error(f"    [ID {id_proposicao}] Resposta de erro HTTP da API OpenAI ({e.status_code}): {e.message}")
        except Exception as e:
            log.error(f"    [ID {id_proposicao}] Erro inesperado ao interagir com o LLM: {e}")

        return None

    def estimar_custo(self, quantidade_proposicoes: int) -> dict:
        """
        Estima custos computacionais da janela de processamento baseando-se no modelo escolhido.
        """
        custo_input = self.CUSTO_INPUT_POR_1K_TOKENS.get(self.modelo, 0.0025)
        custo_output = self.CUSTO_OUTPUT_POR_1K_TOKENS.get(self.modelo, 0.010)

        total_tokens_input = quantidade_proposicoes * self.TOKENS_MEDIOS_INPUT
        total_tokens_output = quantidade_proposicoes * self.TOKENS_MEDIOS_OUTPUT

        custo_usd = (total_tokens_input / 1000 * custo_input) + (total_tokens_output / 1000 * custo_output)
        custo_brl = custo_usd * 5.20  # Cotação base para precificação estimada

        return {
            "modelo": self.modelo,
            "quantidade": quantidade_proposicoes,
            "tokens_estimados": total_tokens_input + total_tokens_output,
            "custo_usd": round(custo_usd, 4),
            "custo_brl": round(custo_brl, 4),
        }


class AtualizadorBanco:
    """
    Persiste os resumos executivos enriquecidos na tabela fato_proposicoes.
    """

    def __init__(self, engine):
        self.engine = engine

    def garantir_colunas(self) -> bool:
        """
        Verifica e injeta as novas colunas necessárias à Etapa 4 de forma idempotente.
        """
        sqls = [
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS resumo_executivo TEXT;",
            "ALTER TABLE fato_proposicoes ADD COLUMN IF NOT EXISTS data_resumo TIMESTAMP;"
        ]
        try:
            with self.engine.begin() as conn:
                for sql in sqls:
                    conn.execute(text(sql))
            log.info("  [DB Update] Colunas estruturais 'resumo_executivo' e 'data_resumo' validadas/criadas.")
            return True
        except SQLAlchemyError as e:
            log.error(f"  [DB Update] Falha ao injetar colunas de IA no PostgreSQL: {e}")
            return False

    def atualizar(self, id_proposicao: int, resumo: str) -> bool:
        """
        Executa o update atômico de uma proposição processada.
        """
        sql = text("""
            UPDATE fato_proposicoes
            SET resumo_executivo = :resumo,
                data_resumo      = :data_resumo
            WHERE id_proposicao  = :id_proposicao;
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {
                    "resumo": resumo,
                    "data_resumo": datetime.now(),
                    "id_proposicao": id_proposicao
                })
            return True
        except SQLAlchemyError as e:
            log.error(f"  [DB Update] [ID {id_proposicao}] Falha no UPDATE: {e}")
            return False

    def salvar_backup_json(self, resultados: list, caminho_arquivo: Path):
        """
        Cria cópia física local dos dados enriquecidos para auditoria ou recuperação ágil.
        """
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
            log.info(f"  [Backup] Dados armazenados preventivamente em: {caminho_arquivo}")
        except Exception as e:
            log.warning(f"  [Backup] Não foi possível salvar backup em JSON: {e}")

class PipelineEtapa4:
    """
    Orquestra o pipeline de IA da Etapa 4:
      1. Lê proposições pendentes do banco (LeitorProposicoes)
      2. Estima o custo antes de processar (GeradorResumoExecutivo.estimar_custo)
      3. Gera resumos executivos via GPT (GeradorResumoExecutivo.gerar)
      4. Persiste os resumos no banco e em JSON (AtualizadorBanco)
    """

    def __init__(self, database_url: str, openai_api_key: str, modelo: str, batch_size: int, dry_run: bool):
        """
        Parâmetros vindos de forma tratada a partir do main.py
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        
        # Parâmetros de data para o backup em disco
        self.timestamp_execucao = datetime.today().strftime("%Y%m%d_%H%M%S")
        self.processed_dir = Path("data/processed")

        # Cria engine SQLAlchemy único reutilizável
        self.engine = create_engine(database_url)

        # Instancia as peças com responsabilidades segregadas (Injeção de Dependência)
        self.leitor = LeitorProposicoes(self.engine)
        self.gerador = GeradorResumoExecutivo(openai_api_key, modelo)
        self.atualizador = AtualizadorBanco(self.engine)

    def _testar_conexao(self) -> bool:
        """Verifica se o banco de dados está acessível antes de acionar a IA."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            log.info("  [Conexão] Comunicação direta com PostgreSQL: OK")
            return True
        except Exception as e:
            log.error(f"  [Conexão] Falha ao alcançar o PostgreSQL antes do loop de IA: {e}")
            return False

    def executar(self) -> dict:
        """
        Executa a governança completa da Etapa 4 de forma idempotente.
        """
        inicio_cronometro = time.time()

        log.info("=" * 60)
        log.info("BÚSSOLA PÚBLICA - Pipeline IA | Etapa 4: Resumo Executivo")
        log.info(f"  Modelo : {self.gerador.modelo}")
        log.info(f"  Batch  : {self.batch_size} proposições")
        log.info(f"  Modo   : {'DRY RUN (Apenas Estimativa)' if self.dry_run else 'PRODUÇÃO (Gravação)'}")
        log.info("=" * 60)

        # 1. Validação de Conexão
        if not self._testar_conexao():
            log.error("Pipeline abortado: banco inacessível.")
            return {}

        # 2. Captura de Registros Pendentes
        df = self.leitor.ler_pendentes(limite=self.batch_size)

        if df.empty:
            log.info("  [INFO] Nenhuma proposição pendente de resumo. Encerrando Etapa 4.")
            return {"processadas": 0, "erros": 0}
        
        log.info(f"  [Volume] Encontradas {len(df)} proposições pendentes para a janela atual (Batch: {self.batch_size}).")

        # 3. Estimativa Orçamentária Obrigatória
        estimativa = self.gerador.estimar_custo(len(df))
        log.info("\n=== ESTIMATIVA DE CUSTO FINANCEIRO ===")
        log.info(f"  Proposições a processar : {estimativa['quantidade']}")
        log.info(f"  Tokens Estimados        : ~{estimativa['tokens_estimados']:,}")
        log.info(f"  Custo Estimado USD      : $ {estimativa['custo_usd']:.4f}")
        log.info(f"  Custo Estimado BRL      : R$ {estimativa['custo_brl']:.4f}")
        log.info(f"  Modelo de IA Alvo       : {estimativa['modelo']}")
        log.info("======================================\n")

        if self.dry_run:
            log.info("  [DRY RUN] Simulação finalizada. Nenhuma linha foi gravada ou consumida.")
            return {"dry_run": True, "estimativa": estimativa}

        # 4. Assegurar Colunas de Persistência
        if not self.atualizador.garantir_colunas():
            log.error("Pipeline abortado: Não foi possível estruturar as colunas de IA no banco.")
            return {}

        # 5. Processamento Linear Incremental
        log.info("-" * 50)
        log.info(f"Iniciando chamadas à OpenAI para {len(df)} registros...")
        log.info("-" * 50)

        resultados = []
        contagem = {"processadas": 0, "erros": 0}

        for i, linha in df.iterrows():
            id_prop = linha["id_proposicao"]
            sigla_tipo = linha.get("sigla_tipo", "")
            numero = linha.get("numero", "")
            ano = linha.get("ano", "")
            ementa = linha.get("ementa", "")

            log.info(f"  [{contagem['processadas'] + contagem['erros'] + 1}/{len(df)}] {sigla_tipo} {numero}/{ano} (ID: {id_prop})")

            # Execução do LLM
            resumo = self.gerador.gerar(id_prop, sigla_tipo, numero, ano, ementa)

            if resumo:
                # Gravação imediata (Resiliência contra perdas)
                if self.atualizador.atualizar(id_prop, resumo):
                    contagem["processadas"] += 1
                    resultados.append({
                        "id_proposicao": id_prop,
                        "sigla_tipo": sigla_tipo,
                        "numero": numero,
                        "ano": ano,
                        "ementa": ementa,
                        "resumo_executivo": resumo,
                        "data_resumo": datetime.now().isoformat()
                    })
                else:
                    contagem["erros"] += 1
            else:
                contagem["erros"] += 1

            # Pausa para prevenção de Rate Limit na API (Rate-limiting control)
            time.sleep(0.5)

        # 6. Salvamento do Backup Local
        if resultados:
            caminho_backup = self.processed_dir / f"resumos_{self.timestamp_execucao}.json"
            self.atualizador.salvar_backup_json(resultados, caminho_backup)

        # 7. Relatório de Encerramento
        duracao = time.time() - inicio_cronometro
        log.info("\n" + "=" * 60)
        log.info("ETAPA 4 CONCLUÍDA COM SUCESSO")
        log.info(f"  Processadas com sucesso : {contagem['processadas']}")
        log.info(f"  Erros de processamento  : {contagem['erros']}")
        log.info(f"  Tempo de Execução       : {duracao:.1f}s")
        log.info(f"  Investimento Estimado   : $ {estimativa['custo_usd']:.4f} USD")
        log.info("=" * 60)

        self.engine.dispose()
        return contagem
