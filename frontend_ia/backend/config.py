# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Configuração do back-end, lida do .env. Nenhuma chave no código."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Caminho explícito até backend/.env, em vez de deixar o dotenv procurar
    # sozinho (a busca automática depende de como o processo foi iniciado e
    # pode não achar o arquivo certo, mesmo problema visto e corrigido em
    # visao/inferencia/config.py).
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


def _lista_env(nome: str, padrao: str) -> list[str]:
    valor = os.environ.get(nome, padrao)
    return [item.strip() for item in valor.split(",") if item.strip()]


@dataclass
class ConfigBackend:
    # Nunca "*": só os endereços do front-end que de fato vão chamar esta API.
    origens_permitidas: list[str] = field(default_factory=lambda: _lista_env(
        "BACKEND_CORS_ORIGINS", "http://localhost:7860,http://127.0.0.1:7860"
    ))


CONFIG = ConfigBackend()
