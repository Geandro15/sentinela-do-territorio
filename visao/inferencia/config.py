# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Configuração do módulo de inferência, lida do arquivo .env.

Mantém o mesmo padrão do módulo de PLN: nada de caminho fixo no código,
tudo configurável, para que o módulo funcione tanto no notebook de
treinamento (Colab) quanto depois, rodando junto com o assistente de voz.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Caminho explícito até visao/.env, em vez de deixar o dotenv procurar
    # sozinho: a busca automática depende de como o processo python foi
    # iniciado (ex.: uvicorn rodando a partir de frontend_ia) e pode não
    # encontrar o arquivo certo.
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def _env(nome: str, padrao: str) -> str:
    return os.environ.get(nome, padrao)


@dataclass
class ConfigVisao:
    # Caminho do modelo treinado para queimadas (gerado pelo notebook, seção 9)
    modelo_queimada: str = _env("VISAO_MODELO_QUEIMADA", "modelos/queimada_mobilenet_v2.keras")
    # Caminho do modelo treinado para danos em estrutura (extensão da cidade)
    modelo_cidade: str = _env("VISAO_MODELO_CIDADE", "modelos/cidade_mobilenet_v2.keras")
    tamanho_imagem: tuple[int, int] = (224, 224)
    limiar_decisao: float = float(_env("VISAO_LIMIAR_DECISAO", "0.5"))
    # Nomes das classes, na mesma ordem usada pelo Keras (ordem alfabética das pastas)
    classes_queimada: tuple[str, str] = ("nowildfire", "wildfire")
    classes_cidade: tuple[str, str] = ("sem_dano", "com_dano")


CONFIG = ConfigVisao()


def caminho_existe(caminho: str) -> bool:
    return Path(caminho).exists()
