# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Busca na web: segunda fonte de evidência, usada só quando a base local do
INPE não cobre a pergunta (ver ``assistente_rag.py``).

Motor de busca: DuckDuckGo via a biblioteca ``ddgs``, gratuito e sem chave de
API, mesmo critério de "ferramenta gratuita, sem custo e sem chave versionada"
já seguido no resto do projeto.

Qualquer falha (biblioteca ausente, sem internet, limite de uso do motor,
nenhum resultado) devolve lista vazia e nunca lança exceção: é o mesmo padrão
de caminho seguro usado em ``assistente/stt.py`` e ``assistente/tts.py``, se
a busca na web falhar, o assistente simplesmente não ganha essa evidência
extra e segue para a abstenção normal, em vez de travar a pergunta do cidadão.

Cada resultado é transformado em um ``Trecho`` (mesmo formato dos trechos do
INPE), para que o gerador e a verificação de "resposta sustentada" (citação +
números só do contexto, ver ``gerador.verificar``) funcionem exatamente igual,
sem importar se o trecho veio do INPE ou da busca na web. Por vir de uma
fonte externa e não confiável, cada resultado passa pela mesma defesa contra
injeção de instruções já usada na ingestão dos documentos locais
(``ingestao.remover_injecao``).
"""
from __future__ import annotations

import datetime as dt
import logging
from urllib.parse import urlparse

from .chunking import Trecho
from .ingestao import remover_injecao

logger = logging.getLogger(__name__)

MAX_CARACTERES_SNIPPET = 500


def _dominio(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "") or "web"
    except Exception:  # URL mal formada: não deve impedir o resto da busca
        return "web"


def buscar_na_web(consulta: str, max_resultados: int = 3) -> list[Trecho]:
    """Busca ``consulta`` na web e devolve até ``max_resultados`` trechos.

    Nunca lança exceção: qualquer falha (biblioteca ausente, sem internet,
    motor indisponível, nenhum resultado) devolve lista vazia.
    """
    if not consulta.strip() or max_resultados <= 0:
        return []

    try:
        from ddgs import DDGS
    except ImportError:
        logger.warning("busca_web: biblioteca 'ddgs' não instalada; busca na web desativada.")
        return []

    try:
        resultados = DDGS(timeout=8).text(consulta, region="br-pt", max_results=max_resultados)
    except Exception as exc:  # sem internet, limite de uso, motor fora do ar etc.
        logger.warning("busca_web: busca falhou (%s: %s); seguindo sem resultado da web.", type(exc).__name__, exc)
        return []

    hoje = dt.date.today().isoformat()
    trechos: list[Trecho] = []
    for posicao, resultado in enumerate(resultados or [], start=1):
        url = str(resultado.get("href") or resultado.get("url") or "").strip()
        titulo = str(resultado.get("title") or "Resultado de busca").strip()
        corpo = str(resultado.get("body") or resultado.get("snippet") or "").strip()
        if not corpo:
            continue

        corpo, removidas = remover_injecao(corpo[:MAX_CARACTERES_SNIPPET])
        if removidas:
            logger.warning("busca_web: %d frase(s) com tentativa de instrução removida(s) do resultado de %r.",
                            removidas, url or "URL desconhecida")
        if not corpo.strip():
            continue

        trechos.append(Trecho(
            id=f"web/{posicao}", texto=corpo, secao_id="web", fonte_id="web",
            fonte=_dominio(url), url=url or "sem URL", data_consulta=hoje, titulo=titulo,
        ))
    return trechos
