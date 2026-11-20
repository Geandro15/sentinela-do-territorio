# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Carrega um modelo treinado no notebook e classifica uma imagem.

Este módulo não decide nada por conta própria: toda classificação volta com
um aviso explícito de que a confirmação final é de um gestor humano, nunca
automática (mesma regra do quadro de Governança do projeto).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import CONFIG, ConfigVisao

log = logging.getLogger("visao.classificador")

AVISO_CONFIRMACAO_HUMANA = (
    "Esta é uma sugestão automática, não uma decisão. "
    "Um gestor humano deve confirmar antes de qualquer ação."
)

_MODELOS: dict[str, object] = {}


class ErroClassificador(RuntimeError):
    """Falha ao carregar o modelo ou classificar a imagem."""


@dataclass
class Resultado:
    classe: str
    confianca: float  # 0 a 1: o quanto o modelo "tem certeza" da classe prevista
    alerta: bool  # True quando a classe prevista é a classe de risco (wildfire / com_dano)
    aviso: str = AVISO_CONFIRMACAO_HUMANA


def _carregar_modelo(caminho: str):
    if caminho not in _MODELOS:
        if not Path(caminho).exists():
            raise ErroClassificador(
                f"Modelo não encontrado em '{caminho}'. "
                "Treine e salve o modelo no notebook (seção 9) e copie o arquivo "
                "para esse caminho, ou ajuste VISAO_MODELO_QUEIMADA / VISAO_MODELO_CIDADE no .env."
            )
        try:
            import tensorflow as tf
        except ImportError as exc:
            raise ErroClassificador(
                "O pacote tensorflow não está instalado. Rode: pip install tensorflow"
            ) from exc
        log.info("Carregando modelo de %s", caminho)
        _MODELOS[caminho] = tf.keras.models.load_model(caminho)
    return _MODELOS[caminho]


def _preparar_imagem(caminho_imagem: str | Path, tamanho: tuple[int, int]) -> np.ndarray:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ErroClassificador("O pacote Pillow não está instalado. Rode: pip install Pillow") from exc

    caminho_imagem = Path(caminho_imagem)
    if not caminho_imagem.exists():
        raise ErroClassificador(f"Imagem não encontrada: {caminho_imagem}")
    try:
        imagem = Image.open(caminho_imagem).convert("RGB").resize(tamanho)
    except Exception as exc:
        raise ErroClassificador(f"Não foi possível abrir a imagem: {exc}") from exc
    vetor = np.asarray(imagem, dtype="float32") / 255.0
    return np.expand_dims(vetor, axis=0)  # adiciona a dimensão de lote (batch)


def classificar_imagem(
    caminho_imagem: str | Path,
    caminho_modelo: str,
    classes: tuple[str, str],
    cfg: ConfigVisao = CONFIG,
) -> Resultado:
    """Classifica uma imagem com o modelo indicado.

    ``classes`` deve ser ``(classe_sem_risco, classe_de_risco)``, na mesma ordem
    usada pelo Keras ao montar o dataset (ordem alfabética das pastas), é a
    mesma ordem salva em ``NOMES_CLASSES`` no notebook.
    """
    modelo = _carregar_modelo(caminho_modelo)
    entrada = _preparar_imagem(caminho_imagem, cfg.tamanho_imagem)
    try:
        probabilidade = float(modelo.predict(entrada, verbose=0)[0][0])
    except Exception as exc:
        raise ErroClassificador(f"Falha ao classificar a imagem: {exc}") from exc

    classe_prevista = classes[1] if probabilidade >= cfg.limiar_decisao else classes[0]
    confianca = probabilidade if classe_prevista == classes[1] else 1 - probabilidade
    return Resultado(classe=classe_prevista, confianca=confianca, alerta=(classe_prevista == classes[1]))


def classificar_queimada(caminho_imagem: str | Path, cfg: ConfigVisao = CONFIG) -> Resultado:
    return classificar_imagem(caminho_imagem, cfg.modelo_queimada, cfg.classes_queimada, cfg)


def classificar_dano_estrutural(caminho_imagem: str | Path, cfg: ConfigVisao = CONFIG) -> Resultado:
    return classificar_imagem(caminho_imagem, cfg.modelo_cidade, cfg.classes_cidade, cfg)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classifica uma imagem com um modelo treinado no notebook.")
    parser.add_argument("imagem", help="Caminho da imagem (.jpg/.png)")
    parser.add_argument("--modelo", required=True, help="Caminho do arquivo .keras treinado")
    parser.add_argument(
        "--tipo", choices=["queimada", "cidade"], default="queimada",
        help="Qual par de classes usar: queimada (nowildfire/wildfire) ou cidade (sem_dano/com_dano)",
    )
    args = parser.parse_args()

    classes = CONFIG.classes_queimada if args.tipo == "queimada" else CONFIG.classes_cidade
    resultado = classificar_imagem(args.imagem, args.modelo, classes)
    print(f"Classe prevista : {resultado.classe}")
    print(f"Confiança       : {resultado.confianca:.1%}")
    print(f"Alerta          : {'sim' if resultado.alerta else 'não'}")
    print(f"Aviso           : {resultado.aviso}")
