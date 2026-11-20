# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Testes do módulo de inferência de Visão Computacional.

Não dependem do modelo real treinado no Colab (isso é tarefa do grupo, com
GPU e o dataset do Kaggle). Em vez disso, criamos um modelo Keras minúsculo
e sem treino real, só para validar que todo o encanamento funciona: salvar,
carregar, abrir uma imagem, redimensionar, prever e devolver um resultado
no formato esperado, incluindo o caso de modelo ausente e de imagem ausente.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inferencia.classificador import ErroClassificador, classificar_imagem
from inferencia.config import ConfigVisao


@pytest.fixture(scope="module")
def modelo_de_teste(tmp_path_factory) -> str:
    """Modelo Keras minúsculo (pesos aleatórios) só para testar o encanamento."""
    import tensorflow as tf
    from tensorflow.keras import layers, models

    entrada = layers.Input(shape=(224, 224, 3))
    x = layers.GlobalAveragePooling2D()(entrada)
    saida = layers.Dense(1, activation="sigmoid")(x)
    modelo = models.Model(entrada, saida)
    modelo.compile(optimizer="adam", loss="binary_crossentropy")

    pasta = tmp_path_factory.mktemp("modelos")
    caminho = pasta / "modelo_teste.keras"
    modelo.save(caminho)
    return str(caminho)


@pytest.fixture
def imagem_de_teste(tmp_path) -> str:
    caminho = tmp_path / "foto.jpg"
    imagem = Image.fromarray((np.random.rand(300, 300, 3) * 255).astype("uint8"))
    imagem.save(caminho)
    return str(caminho)


def test_classifica_e_devolve_resultado_no_formato_esperado(modelo_de_teste, imagem_de_teste):
    resultado = classificar_imagem(imagem_de_teste, modelo_de_teste, ("sem_risco", "com_risco"))
    assert resultado.classe in ("sem_risco", "com_risco")
    assert 0.0 <= resultado.confianca <= 1.0
    assert isinstance(resultado.alerta, bool)
    assert "gestor" in resultado.aviso.lower()


def test_modelo_e_reaproveitado_entre_chamadas(modelo_de_teste, imagem_de_teste):
    from inferencia import classificador

    classificador._MODELOS.clear()
    classificar_imagem(imagem_de_teste, modelo_de_teste, ("sem_risco", "com_risco"))
    assert modelo_de_teste in classificador._MODELOS
    # segunda chamada não deve recarregar o modelo (mesma referência em cache)
    objeto_antes = classificador._MODELOS[modelo_de_teste]
    classificar_imagem(imagem_de_teste, modelo_de_teste, ("sem_risco", "com_risco"))
    assert classificador._MODELOS[modelo_de_teste] is objeto_antes


def test_modelo_ausente_gera_erro_claro(imagem_de_teste):
    with pytest.raises(ErroClassificador, match="não encontrado"):
        classificar_imagem(imagem_de_teste, "caminho/que/nao/existe.keras", ("a", "b"))


def test_imagem_ausente_gera_erro_claro(modelo_de_teste):
    with pytest.raises(ErroClassificador, match="não encontrada"):
        classificar_imagem("imagem/que/nao/existe.jpg", modelo_de_teste, ("a", "b"))


def test_limiar_de_decisao_e_configuravel(modelo_de_teste, imagem_de_teste):
    cfg_permissivo = ConfigVisao(limiar_decisao=0.0)  # tudo acima de 0.0 vira "com_risco"
    resultado = classificar_imagem(imagem_de_teste, modelo_de_teste, ("sem_risco", "com_risco"), cfg_permissivo)
    assert resultado.classe == "com_risco"
