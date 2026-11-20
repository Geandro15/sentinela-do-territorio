# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Chunking: divide as seções em trechos que cabem no prompt.

Três configurações, para comparação na avaliação:

- ``estrutura``: respeita a estrutura da fonte (uma pergunta do FAQ, uma página
  do boletim). Seções longas são divididas em frases, até 900 caracteres, com
  uma frase de sobreposição. O título da seção acompanha cada trecho.
- ``fixo_500``: janelas de 500 caracteres com 100 de sobreposição, sem olhar a estrutura.
- ``fixo_1000``: janelas de 1000 caracteres com 200 de sobreposição.

Todo trecho guarda os metadados da seção de origem (fonte, URL, data, seção).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .ingestao import Secao

CONFIGURACOES = ("estrutura", "fixo_500", "fixo_1000")
PADRAO = "estrutura"


@dataclass
class Trecho:
    id: str
    texto: str          # o que é indexado e mostrado ao modelo
    secao_id: str       # exemplo: F1#pergunta-7
    fonte_id: str
    fonte: str
    url: str
    data_consulta: str
    titulo: str


def _novo(secao: Secao, numero: int, texto: str) -> Trecho:
    return Trecho(id=f"{secao.id}/{numero}", texto=texto, secao_id=secao.id, fonte_id=secao.fonte_id,
                  fonte=secao.fonte, url=secao.url, data_consulta=secao.data_consulta, titulo=secao.titulo)


def _por_estrutura(secao: Secao, tamanho: int = 900) -> list[Trecho]:
    frases = re.split(r"(?<=[.!?;])\s+", secao.texto)
    blocos, atual = [], []
    for frase in frases:
        if atual and sum(len(f) + 1 for f in atual) + len(frase) > tamanho:
            blocos.append(atual)
            atual = atual[-1:]          # sobreposição de uma frase
        atual.append(frase)
    if atual:
        blocos.append(atual)
    return [_novo(secao, i, f"{secao.titulo}\n{' '.join(bloco)}") for i, bloco in enumerate(blocos, 1)]


def _fixo(secao: Secao, tamanho: int, sobreposicao: int) -> list[Trecho]:
    texto, trechos, inicio = secao.texto, [], 0
    while inicio < len(texto):
        trechos.append(_novo(secao, len(trechos) + 1, texto[inicio:inicio + tamanho]))
        if inicio + tamanho >= len(texto):
            break
        inicio += tamanho - sobreposicao
    return trechos


def dividir(secoes: list[Secao], configuracao: str = PADRAO) -> list[Trecho]:
    if configuracao == "estrutura":
        funcao = _por_estrutura
    elif configuracao == "fixo_500":
        funcao = lambda s: _fixo(s, 500, 100)  # noqa: E731
    elif configuracao == "fixo_1000":
        funcao = lambda s: _fixo(s, 1000, 200)  # noqa: E731
    else:
        raise ValueError(f"Configuração de chunking desconhecida: {configuracao}. Use {', '.join(CONFIGURACOES)}.")
    return [trecho for secao in secoes for trecho in funcao(secao)]
