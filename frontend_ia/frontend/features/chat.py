# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Tela "Relatar / Perguntar": o cidadão pergunta sobre queimadas e o
assistente RAG responde, sempre citando a fonte. Reaproveita o mesmo
``cartao_status`` usado na tela de imagem.
"""
from __future__ import annotations

import gradio as gr

from ..providers.api_cliente import ErroAPI, perguntar
from ..state.estado import adicionar_interacao, marcar_avaliacao, ultima_interacao
from ..ui.componentes import cartao_status

EXPLICACAO = (
    "Pergunte sobre o monitoramento de queimadas por satélite, o risco de fogo, os números do boletim "
    "do INPE ou temas relacionados (como telefones de emergência). As respostas usam primeiro as fontes "
    "oficiais do Programa Queimadas; quando elas não cobrem o assunto, o assistente busca na web. Em "
    "ambos os casos, a resposta mostra de onde veio cada informação."
)


def _responder(pergunta_texto: str, local_texto: str, estado: dict):
    pergunta_texto = (pergunta_texto or "").strip()
    local_texto = (local_texto or "").strip()
    if len(pergunta_texto) < 3:
        cartao = cartao_status("Pergunta muito curta", "Escreva pelo menos 3 caracteres antes de enviar.", "atencao")
        return cartao, "", estado, gr.update(visible=False)

    # O local é só contexto para o assistente e para o histórico, não é
    # uma coordenada de GPS (o navegador não é consultado), é texto livre
    # que o próprio cidadão escreve (ex.: "Zona rural de Novo Progresso/PA").
    pergunta_com_contexto = f"Região informada pelo cidadão: {local_texto}. Pergunta: {pergunta_texto}" \
        if local_texto else pergunta_texto

    try:
        resultado = perguntar(pergunta_com_contexto)
    except ErroAPI as exc:
        cartao = cartao_status("Não foi possível responder agora", str(exc), "atencao")
        return cartao, "", estado, gr.update(visible=False)

    nivel = "sucesso" if resultado["sustentada"] else "atencao"
    cartao = cartao_status("Resposta do assistente", f"{resultado['resposta']}\n\n{resultado['motivo_legivel']}", nivel)
    fontes_md = "\n".join(f"- {f}" for f in resultado["fontes"]) or "_Nenhuma fonte foi citada nesta resposta._"
    estado = adicionar_interacao(
        estado, tipo="pergunta", entrada=pergunta_texto,
        resumo_saida=resultado["resposta"][:80], alerta=not resultado["sustentada"], local=local_texto,
    )
    return cartao, fontes_md, estado, gr.update(visible=True)


def _avaliar(estado: dict, avaliacao: str):
    ultima = ultima_interacao(estado)
    if not ultima:
        return estado, ""
    estado = marcar_avaliacao(estado, ultima["indice"], avaliacao)
    mensagem = "Obrigado! Isso ajuda a melhorar o assistente." if avaliacao == "util" else \
        "Entendido, vamos registrar que esta resposta não ajudou."
    return estado, cartao_status("Feedback registrado", mensagem, "sucesso")


def construir_aba_perguntar(estado: gr.State) -> None:
    with gr.Tab("💬 Relatar / Perguntar", id=1):
        gr.Markdown(f"### Pergunte sobre queimadas\n{EXPLICACAO}")
        caixa_local = gr.Textbox(
            label="Local / região (opcional)",
            placeholder="Ex.: Zona rural de Novo Progresso, PA",
            info="Ajuda o assistente a responder com mais contexto e fica salvo no histórico (Relatórios).",
        )
        with gr.Row():
            caixa_pergunta = gr.Textbox(
                label="Sua pergunta", placeholder="Ex.: Como é calculado o risco de fogo?",
                scale=4,
            )
            botao_perguntar = gr.Button("Perguntar", variant="primary", scale=1)
        cartao_resposta = gr.HTML()
        fontes = gr.Markdown()

        with gr.Row(visible=False) as linha_feedback:
            gr.Markdown("Essa resposta ajudou?")
            botao_util = gr.Button("👍 Útil", size="sm")
            botao_nao_ajudou = gr.Button("👎 Não ajudou", size="sm")
        mensagem_feedback = gr.HTML()

        botao_perguntar.click(
            _responder, inputs=[caixa_pergunta, caixa_local, estado],
            outputs=[cartao_resposta, fontes, estado, linha_feedback],
        )
        caixa_pergunta.submit(
            _responder, inputs=[caixa_pergunta, caixa_local, estado],
            outputs=[cartao_resposta, fontes, estado, linha_feedback],
        )
        botao_util.click(lambda e: _avaliar(e, "util"), inputs=[estado], outputs=[estado, mensagem_feedback])
        botao_nao_ajudou.click(lambda e: _avaliar(e, "nao_ajudou"), inputs=[estado], outputs=[estado, mensagem_feedback])
