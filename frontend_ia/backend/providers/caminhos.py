# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Prepara o sys.path para importar os módulos de IA já prontos de outras
disciplinas (o RAG do PLN/Generative AI e o classificador da Visão
Computacional), sem duplicar nem reescrever esse código aqui no back-end.

No repositório do grupo, o código do PLN fica direto na raiz do projeto
(``app.py``, ``config.py``, ``genai/`` etc., sem uma pasta ``pln/`` própria),
com ``visao/`` como uma subpasta ao lado. Esta função procura por esses dois
pontos de referência subindo a partir deste arquivo, em vez de supor uma
profundidade fixa de pastas, assim funciona também se o projeto for
reorganizado com uma pasta ``pln/`` separada.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _pasta_do_genai(inicio: Path) -> Path:
    """Acha a pasta que contém ``genai/`` (com ``assistente_rag.py`` dentro),
    direto na raiz do projeto ou dentro de uma pasta ``pln/``."""
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
        "Não encontrei a pasta 'genai' (com assistente_rag.py dentro) subindo a "
        f"partir de '{inicio}'. Confirme que frontend_ia/ está dentro da pasta do "
        "projeto, junto do código do PLN/Generative AI."
    )


def _pasta_da_visao(inicio: Path) -> Path:
    """Acha a pasta ``visao/`` (com ``inferencia/classificador.py`` dentro)."""
    candidato = inicio
    for _ in range(8):
        if (candidato / "visao" / "inferencia" / "classificador.py").is_file():
            return candidato / "visao"
        if candidato.parent == candidato:
            break
        candidato = candidato.parent
    raise RuntimeError(
        "Não encontrei a pasta 'visao' (com inferencia/classificador.py dentro) "
        f"subindo a partir de '{inicio}'. Confirme que frontend_ia/ está dentro da "
        "pasta do projeto, junto do código da Visão Computacional."
    )


_INICIO = Path(__file__).resolve().parent
PASTA_PLN = _pasta_do_genai(_INICIO)
PASTA_VISAO = _pasta_da_visao(_INICIO)


def preparar() -> None:
    """Adiciona as duas pastas ao sys.path, se ainda não estiverem lá.

    Depois de chamar esta função, é possível fazer ``import genai...`` e
    ``import inferencia...`` normalmente, do mesmo jeito que o app.py do
    PLN e o notebook de Visão já fazem.
    """
    for pasta in (PASTA_PLN, PASTA_VISAO):
        caminho = str(pasta)
        if caminho not in sys.path:
            sys.path.insert(0, caminho)
