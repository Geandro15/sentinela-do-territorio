# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Aba do aplicativo: chat com RAG sobre as fontes do Programa Queimadas do INPE."""
from __future__ import annotations

import gradio as gr

from .assistente_rag import AssistenteRAG

EXPLICACAO = (
    "Pergunte sobre o monitoramento de queimadas por satélite, o BDQueimadas, o risco de fogo, os números do "
    "boletim InfoQueima ou temas relacionados (como telefones de emergência). As respostas usam primeiro as fontes "
    "oficiais do Programa Queimadas do INPE; quando elas não cobrem o assunto, o assistente busca na web, e sempre "
    "mostra de onde veio cada informação. Quando nada é encontrado, o assistente diz que não encontrou."
)
MOTIVOS = {
    "respondida": "Resposta conferida com os trechos das fontes.",
    "abstencao_sem_evidencia": "Nenhum trecho das fontes trata desse assunto. O modelo não foi consultado.",
    "abstencao_do_modelo": "Os trechos encontrados não respondem à pergunta.",
    "nao_sustentada": "A resposta gerada não pôde ser confirmada nas fontes e foi bloqueada.",
    "recusa_de_seguranca": "Pedido para mudar as regras ou revelar instruções. O modelo não foi consultado.",
    "erro_llm": "O modelo de linguagem não respondeu.",
}

_ASSISTENTE: AssistenteRAG | None = None


def _assistente() -> AssistenteRAG:
    global _ASSISTENTE
    if _ASSISTENTE is None:
        _ASSISTENTE = AssistenteRAG()
    return _ASSISTENTE


def responder(pergunta: str, conversa: list | None):
    conversa = list(conversa or [])
    if not (pergunta or "").strip():
        return conversa, "", "", ""
    resposta = _assistente().responder(pergunta)
    conversa += [{"role": "user", "content": resposta.pergunta}, {"role": "assistant", "content": resposta.resposta}]
    fontes = "\n".join(f"- {linha}" for linha in resposta.fontes()) or "Nenhum trecho usado."
    trechos = "\n\n".join(f"**[{i}] {a.trecho.titulo}**\n\n{a.trecho.texto[:600]}" for i, a in enumerate(resposta.achados, 1))
    sinais = ", ".join(f"{nome}: {valor:.2f}" for nome, valor in resposta.sinais.items())
    situacao = MOTIVOS.get(resposta.motivo, resposta.motivo) + (f" ({sinais})" if sinais else "")
    return conversa, "", f"**Situação:** {situacao}\n\n**Fontes:**\n{fontes}", trechos


def nova_conversa():
    if _ASSISTENTE is not None:
        _ASSISTENTE.nova_conversa()
    return [], "", "", ""


def construir_aba_genai() -> None:
    gr.Markdown(EXPLICACAO)
    conversa = gr.Chatbot(label="Conversa", height=340)
    pergunta = gr.Textbox(label="Sua pergunta", placeholder="Exemplo: o que é o satélite de referência?")
    with gr.Row():
        enviar = gr.Button("Perguntar", variant="primary")
        limpar = gr.Button("Nova conversa")
    fontes = gr.Markdown()
    with gr.Accordion("Trechos recuperados (evidências)", open=False):
        trechos = gr.Markdown()
    saidas = [conversa, pergunta, fontes, trechos]
    enviar.click(responder, [pergunta, conversa], saidas)
    pergunta.submit(responder, [pergunta, conversa], saidas)
    limpar.click(nova_conversa, None, saidas)
