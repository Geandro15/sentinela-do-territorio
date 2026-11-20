# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Integração com planilha: grava cada relato processado na fila de

atendimento do gestor, um .xlsx comum, que abre no Excel ou no Google
Sheets, sem precisar de nenhuma API paga.
"""
from __future__ import annotations

from pathlib import Path

COLUNAS = [
    "Protocolo", "Processado em", "Arquivo", "Local", "Data do relato", "Descrição",
    "Imagem classificada", "Prioridade", "Pontuação", "Motivos",
]


class ErroPlanilha(RuntimeError):
    """Falha ao abrir, criar ou gravar a planilha de fila de atendimento."""


def _abrir_ou_criar(caminho: Path):
    from openpyxl import Workbook, load_workbook

    if caminho.exists():
        return load_workbook(caminho)
    pasta = Workbook()
    planilha = pasta.active
    planilha.title = "Fila de atendimento"
    planilha.append(COLUNAS)
    return pasta


def registrar_relato(caminho_planilha: str | Path, linha: dict) -> None:
    caminho_planilha = Path(caminho_planilha)
    try:
        caminho_planilha.parent.mkdir(parents=True, exist_ok=True)
        pasta = _abrir_ou_criar(caminho_planilha)
        planilha = pasta.active
        planilha.append([linha.get(coluna, "") for coluna in COLUNAS])
        pasta.save(caminho_planilha)
    except ImportError as exc:
        raise ErroPlanilha("o pacote openpyxl não está instalado (pip install openpyxl)") from exc
    except Exception as exc:
        raise ErroPlanilha(f"falha ao gravar a planilha {caminho_planilha.name}: {exc}") from exc
