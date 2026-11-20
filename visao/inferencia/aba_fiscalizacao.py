# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Aba opcional de Gradio: upload de foto -> classificação -> confirmação do gestor.

Uso (dentro do app.py do assistente de voz, se o grupo tiver tempo de integrar):

    import gradio as gr
    from visao.inferencia.aba_fiscalizacao import construir_aba_fiscalizacao

    with gr.Blocks() as demo:
        with gr.Tabs():
            ... outras abas do PLN ...
            with gr.Tab("Fiscalização (foto)"):
                construir_aba_fiscalizacao()

Esta aba nunca decide nada por conta própria: toda classificação é uma
sugestão, registrada em uma fila de revisão até um gestor confirmar ou
rejeitar, o mesmo princípio de "confirmação humana" usado no restante do
projeto (corpus da ferramenta de PLN, robô de RPA, etc.).
"""
from __future__ import annotations

import csv
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .classificador import ErroClassificador, classificar_dano_estrutural, classificar_queimada
from .config import CONFIG

log = logging.getLogger("visao.aba_fiscalizacao")

PASTA_FILA = Path("logs")
ARQUIVO_FILA = PASTA_FILA / "fila_revisao_visao.csv"
CABECALHO_FILA = ["id", "data_hora", "tipo", "classe", "confianca", "status"]


def _registrar_na_fila(tipo: str, classe: str, confianca: float) -> str:
    PASTA_FILA.mkdir(exist_ok=True)
    novo = not ARQUIVO_FILA.exists()
    id_registro = uuid.uuid4().hex[:8]
    with open(ARQUIVO_FILA, "a", newline="", encoding="utf-8") as arq:
        escritor = csv.writer(arq)
        if novo:
            escritor.writerow(CABECALHO_FILA)
        escritor.writerow([
            id_registro, datetime.now(timezone.utc).isoformat(timespec="seconds"),
            tipo, classe, f"{confianca:.3f}", "pendente",
        ])
    return id_registro


def processar_foto(caminho_imagem: str | None, tipo: str):
    """Classifica a foto enviada e registra na fila de revisão do gestor."""
    if not caminho_imagem:
        return "Envie uma foto para analisar.", ""

    try:
        if tipo == "Queimada (campo)":
            resultado = classificar_queimada(caminho_imagem)
        else:
            resultado = classificar_dano_estrutural(caminho_imagem)
    except ErroClassificador as exc:
        log.error("Falha na classificação: %s", exc)
        return f"Não foi possível analisar a foto agora: {exc}", ""

    id_registro = _registrar_na_fila(tipo, resultado.classe, resultado.confianca)
    texto = (
        f"Sugestão do modelo: **{resultado.classe}** (confiança {resultado.confianca:.0%}).\n\n"
        f"{resultado.aviso}\n\n"
        f"Registrado na fila de revisão com o código `{id_registro}`."
    )
    return texto, id_registro


def construir_aba_fiscalizacao():
    """Monta os componentes da aba. Chame dentro de um ``gr.Tab(...)`` existente."""
    import gradio as gr

    gr.Markdown(
        "### Fiscalização por foto\n"
        "Envie uma foto para o modelo de Visão Computacional sugerir uma classificação. "
        "**A sugestão não aciona nada automaticamente**, fica registrada em uma fila "
        "para um gestor confirmar ou rejeitar."
    )
    tipo = gr.Radio(
        ["Queimada (campo)", "Dano em estrutura (cidade)"],
        value="Queimada (campo)",
        label="O que a foto mostra?",
    )
    imagem = gr.Image(type="filepath", label="Foto")
    botao = gr.Button("Analisar foto")
    saida_texto = gr.Markdown()
    saida_id = gr.Textbox(visible=False)

    botao.click(processar_foto, inputs=[imagem, tipo], outputs=[saida_texto, saida_id])
    return saida_id
