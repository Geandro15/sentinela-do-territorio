# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Estado centralizado da sessão (``gr.State``): o histórico de interações
do cidadão, usado pelo painel (gráfico e filtros) e pela confirmação humana.

Nenhuma tela guarda sua própria cópia da lista, todas leem e escrevem
neste mesmo estado, recebido e devolvido pelos listeners do Gradio.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Literal

TipoInteracao = Literal["pergunta", "imagem"]


@dataclass
class Interacao:
    indice: int
    tipo: TipoInteracao
    entrada: str  # a pergunta, ou o nome do arquivo de imagem
    resumo_saida: str  # resposta curta, ou "wildfire (93%)"
    alerta: bool  # sustentada=False/abstenção conta como alerta de atenção; imagem com risco também
    local: str = ""  # local/região informado pelo cidadão (texto livre, opcional)
    hora: str = field(default_factory=lambda: dt.datetime.now().strftime("%H:%M:%S"))
    avaliacao: str = "sem_avaliacao"  # sem_avaliacao | util | nao_ajudou | confirmado | falso_alarme


def estado_inicial() -> dict:
    return {"historico": [], "proximo_indice": 1}


def adicionar_interacao(
    estado: dict, *, tipo: TipoInteracao, entrada: str, resumo_saida: str, alerta: bool, local: str = "",
) -> dict:
    estado = {**estado, "historico": list(estado["historico"])}
    interacao = Interacao(indice=estado["proximo_indice"], tipo=tipo, entrada=entrada,
                          resumo_saida=resumo_saida, alerta=alerta, local=local)
    estado["historico"].append(asdict(interacao))
    estado["proximo_indice"] += 1
    return estado


def marcar_avaliacao(estado: dict, indice: int, avaliacao: str) -> dict:
    """Ponto de human-in-the-loop: o cidadão ou o gestor confirma, corrige ou
    avalia a última sugestão da IA, antes de qualquer ação final."""
    estado = {**estado, "historico": [dict(i) for i in estado["historico"]]}
    for interacao in estado["historico"]:
        if interacao["indice"] == indice:
            interacao["avaliacao"] = avaliacao
            break
    return estado


def ultima_interacao(estado: dict) -> dict | None:
    historico = estado.get("historico") or []
    return historico[-1] if historico else None
