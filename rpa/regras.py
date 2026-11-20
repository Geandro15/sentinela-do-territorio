# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Regra de decisão: combina o relato (OCR), a classificação de imagem de

satélite (Visão Computacional, quando houver) e o contexto do boletim do
INPE (web scraping) para decidir a prioridade na fila do gestor.

A regra é simples e documentada de propósito. Nenhum alerta é automático:
todo relato de prioridade ALTA ainda passa por confirmação humana (mesma
regra de governança usada no classificador de imagem e no front-end).
"""
from __future__ import annotations

from dataclasses import dataclass, field

PALAVRAS_RISCO = ("fogo", "fumaça", "fumaca", "queimada", "incêndio", "incendio", "chamas")
LIMIAR_FOCOS_ALTO = 15000  # acima disso, o mês é considerado de atenção (ver docs/relatorio_rpa.md)


@dataclass
class Prioridade:
    nivel: str  # ALTA | MEDIA | BAIXA | REVISAR
    pontuacao: int
    motivos: list[str] = field(default_factory=list)


def classificar_prioridade(
    *, descricao: str | None, imagem_alerta: bool | None,
    total_focos_mes: int | None, limiar_focos_alto: int = LIMIAR_FOCOS_ALTO,
) -> Prioridade:
    if not descricao:
        return Prioridade(
            nivel="REVISAR", pontuacao=0,
            motivos=["Descrição não encontrada no relato (falha de OCR ou campo em branco), precisa de revisão manual."],
        )

    pontuacao = 0
    motivos: list[str] = []

    descricao_lower = descricao.lower()
    if any(palavra in descricao_lower for palavra in PALAVRAS_RISCO):
        pontuacao += 1
        motivos.append("Relato menciona termo de risco (fogo/fumaça/queimada/incêndio).")

    if imagem_alerta is True:
        pontuacao += 1
        motivos.append("Imagem de satélite classificada com indício de incêndio (Visão Computacional).")
    elif imagem_alerta is False:
        motivos.append("Imagem de satélite não indicou incêndio.")
    else:
        motivos.append("Sem imagem de satélite classificada (não enviada ou modelo indisponível).")

    if total_focos_mes is not None and total_focos_mes >= limiar_focos_alto:
        pontuacao += 1
        motivos.append(f"Boletim do INPE: {total_focos_mes} focos no mês de referência, acima do limiar de atenção ({limiar_focos_alto}).")

    if pontuacao >= 2:
        nivel = "ALTA"
    elif pontuacao == 1:
        nivel = "MEDIA"
    else:
        nivel = "BAIXA"
        motivos.append("Nenhum sinal de risco encontrado nas fontes consultadas.")

    return Prioridade(nivel=nivel, pontuacao=pontuacao, motivos=motivos)
