# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Pipeline do chat: liga a API ao assistente RAG do módulo de PLN/Generative AI.

Mantém um único assistente carregado (o índice e os embeddings só são lidos
uma vez), igual ao padrão já usado em ``genai/aba.py``.
"""
from __future__ import annotations

from ..providers.caminhos import preparar
from ..schemas.relatos import PerguntaSaida

preparar()

from genai.aba import MOTIVOS  # noqa: E402  (import depende de preparar() ter rodado)
from genai.assistente_rag import AssistenteRAG  # noqa: E402

_ASSISTENTE: AssistenteRAG | None = None


def _assistente() -> AssistenteRAG:
    global _ASSISTENTE
    if _ASSISTENTE is None:
        _ASSISTENTE = AssistenteRAG()
    return _ASSISTENTE


MENSAGEM_LLM_FORA_DO_AR = (
    "O assistente não está disponível agora (o modelo de linguagem não respondeu). "
    "Veja abaixo os trechos das fontes encontrados, ou tente de novo em instantes."
)


def perguntar(pergunta: str) -> PerguntaSaida:
    resposta = _assistente().responder(pergunta)
    # O módulo de genai, em caso de falha do LLM, embute o erro técnico bruto no
    # texto da resposta (ver genai/assistente_rag.py). O cidadão nunca deve ver
    # esse texto, aqui ele é trocado por uma mensagem clara antes de sair da API.
    texto = MENSAGEM_LLM_FORA_DO_AR if resposta.motivo == "erro_llm" else resposta.resposta
    return PerguntaSaida(
        resposta=texto,
        fontes=resposta.fontes(),
        motivo=resposta.motivo,
        motivo_legivel=MOTIVOS.get(resposta.motivo, resposta.motivo),
        sustentada=resposta.verificacao.get("sustentada", resposta.motivo == "respondida"),
    )
