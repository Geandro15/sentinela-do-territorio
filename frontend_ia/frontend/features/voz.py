# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Tela "Perguntar por voz": o cidadão grava (ou envia) um áudio, o
back-end transcreve, responde pelo mesmo assistente RAG do chat de texto e
devolve a resposta falada. Reaproveita o mesmo ``cartao_status`` das outras
telas.
"""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import gradio as gr

from ..providers.api_cliente import ErroAPI, perguntar_por_voz
from ..state.estado import adicionar_interacao
from ..ui.componentes import cartao_status

EXPLICACAO = (
    "Grave sua dúvida sobre queimadas com o microfone (ou envie um áudio gravado). O assistente "
    "transcreve, responde com base nas fontes do INPE (e na web, quando o INPE não cobrir o assunto), "
    "e fala a resposta de volta."
)


def _responder(caminho_audio: str | None, estado: dict):
    if not caminho_audio:
        cartao = cartao_status("Nenhum áudio enviado", "Grave ou envie um áudio antes de perguntar.", "atencao")
        return cartao, "", None, estado

    try:
        resultado = perguntar_por_voz(caminho_audio)
    except ErroAPI as exc:
        cartao = cartao_status("Não foi possível responder agora", str(exc), "atencao")
        return cartao, "", None, estado

    transcricao_md = f"**Você perguntou:** {resultado['pergunta_transcrita']}"
    nivel = "sucesso" if resultado["sustentada"] else "atencao"
    cartao = cartao_status("Resposta do assistente", f"{resultado['resposta']}\n\n{resultado['motivo_legivel']}", nivel)

    caminho_audio_resposta = None
    if resultado.get("audio_base64"):
        bruto = base64.b64decode(resultado["audio_base64"])
        arquivo_temporario = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        arquivo_temporario.write(bruto)
        arquivo_temporario.close()
        caminho_audio_resposta = arquivo_temporario.name

    estado = adicionar_interacao(
        estado, tipo="pergunta", entrada=f"[voz] {resultado['pergunta_transcrita']}",
        resumo_saida=resultado["resposta"][:80], alerta=not resultado["sustentada"],
    )
    return cartao, transcricao_md, caminho_audio_resposta, estado


def construir_aba_voz(estado: gr.State) -> None:
    with gr.Tab("🎙️ Perguntar por voz", id=2):
        gr.Markdown(f"### Pergunte falando\n{EXPLICACAO}")
        audio_entrada = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Sua pergunta (áudio)")
        botao_perguntar = gr.Button("Transcrever e perguntar", variant="primary")
        transcricao = gr.Markdown()
        cartao_resposta = gr.HTML()
        audio_resposta = gr.Audio(type="filepath", label="Resposta falada", autoplay=True)

        botao_perguntar.click(
            _responder, inputs=[audio_entrada, estado],
            outputs=[cartao_resposta, transcricao, audio_resposta, estado],
        )
