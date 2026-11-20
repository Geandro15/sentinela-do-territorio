# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Notificação: para relatos de prioridade ALTA, gera um arquivo de

"e-mail" simulado (texto puro) em vez de enviar de verdade, sem
credencial real, sem custo, só dado sintético. Para enviar de verdade,
troque por ``smtplib`` com um servidor SMTP de testes, mantendo a senha
fora do código (variável de ambiente, nunca no repositório).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path


def notificar_gestor(pasta_saida: str | Path, protocolo: str, resumo: str) -> Path:
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    destino = pasta_saida / f"notificacao_{protocolo}.txt"
    agora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    destino.write_text(
        "Para: gestor@defesacivil.exemplo (simulado, nenhum e-mail real é enviado)\n"
        f"Assunto: [Sentinela do Território] Relato de prioridade ALTA, {protocolo}\n"
        f"Data: {agora}\n\n"
        f"{resumo}\n",
        encoding="utf-8",
    )
    return destino
