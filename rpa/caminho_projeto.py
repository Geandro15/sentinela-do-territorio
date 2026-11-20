# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Acha as pastas do projeto (``genai/`` e ``visao/``) subindo a partir
deste arquivo, aceitando tanto o layout real do grupo (código do PLN
direto na raiz do projeto, sem uma pasta ``pln/`` própria) quanto um
layout alternativo com uma pasta ``pln/`` separada, mesma lógica já
usada e testada em ``frontend_ia/backend/providers/caminhos.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _pasta_do_genai(inicio: Path) -> Path:
    candidato = inicio
    for _ in range(8):
        if (candidato / "genai" / "assistente_rag.py").is_file():
            return candidato
        if (candidato / "pln" / "genai" / "assistente_rag.py").is_file():
            return candidato / "pln"
        if candidato.parent == candidato:
            break
        candidato = candidato.parent
    raise RuntimeError(
        f"Não encontrei a pasta 'genai' (com assistente_rag.py dentro) subindo a partir de '{inicio}'. "
        "Confirme que rpa/ está dentro da pasta do projeto, junto do código do PLN/Generative AI."
    )


def _pasta_da_visao(inicio: Path) -> Path:
    candidato = inicio
    for _ in range(8):
        if (candidato / "visao" / "inferencia" / "classificador.py").is_file():
            return candidato / "visao"
        if candidato.parent == candidato:
            break
        candidato = candidato.parent
    raise RuntimeError(
        f"Não encontrei a pasta 'visao' (com inferencia/classificador.py dentro) subindo a partir de '{inicio}'. "
        "Confirme que rpa/ está dentro da pasta do projeto, junto do código da Visão Computacional."
    )


_INICIO = Path(__file__).resolve().parent
PASTA_PLN = _pasta_do_genai(_INICIO)
PASTA_VISAO = _pasta_da_visao(_INICIO)


def preparar() -> None:
    """Adiciona as pastas do PLN e da Visão ao ``sys.path``, se ainda não

    estiverem lá, depois é possível fazer ``import genai...`` e
    ``import inferencia...`` normalmente."""
    for pasta in (PASTA_PLN, PASTA_VISAO):
        caminho = str(pasta)
        if caminho not in sys.path:
            sys.path.insert(0, caminho)
