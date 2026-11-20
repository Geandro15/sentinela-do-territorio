# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Pipeline de verificação por imagem: liga a API ao classificador da Visão
Computacional. Nunca decide nada por conta própria, toda saída carrega o
aviso de confirmação humana (ver ``visao/inferencia/classificador.py``).
"""
from __future__ import annotations

from pathlib import Path

from ..providers.caminhos import preparar
from ..schemas.relatos import ImagemSaida

preparar()

from inferencia.classificador import ErroClassificador, classificar_queimada  # noqa: E402


class ErroImagem(RuntimeError):
    """Erro ao classificar a imagem enviada; a API transforma isso em HTTP 422/503."""


def classificar(caminho_imagem: str | Path) -> ImagemSaida:
    try:
        resultado = classificar_queimada(caminho_imagem)
    except ErroClassificador as exc:
        raise ErroImagem(str(exc)) from exc
    return ImagemSaida(
        classe=resultado.classe,
        confianca=resultado.confianca,
        alerta=resultado.alerta,
        aviso=resultado.aviso,
    )
