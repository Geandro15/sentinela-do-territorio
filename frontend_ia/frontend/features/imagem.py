# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Tela "Verificar imagem de satélite": segunda fonte de evidência do
projeto, independente do relato do cidadão. Nenhum alerta é enviado
sozinho, o botão de confirmação é o ponto de human-in-the-loop.
"""
from __future__ import annotations

import gradio as gr

from ..providers.api_cliente import ErroAPI, classificar_imagem
from ..state.estado import adicionar_interacao, marcar_avaliacao, ultima_interacao
from ..ui.componentes import badge_confianca, cartao_status

EXPLICACAO = (
    "Envie uma imagem de satélite da região relatada. O modelo indica se a cena corresponde a uma área "
    "com incêndio, é uma segunda fonte de evidência, independente do relato por voz ou texto."
)


def _analisar(caminho_imagem: str | None, local_texto: str, estado: dict):
    local_texto = (local_texto or "").strip()
    if not caminho_imagem:
        cartao = cartao_status("Nenhuma imagem enviada", "Envie uma imagem .jpg ou .png antes de analisar.", "atencao")
        return cartao, estado, gr.update(visible=False), gr.update(visible=False)

    try:
        resultado = classificar_imagem(caminho_imagem)
    except ErroAPI as exc:
        cartao = cartao_status("Não foi possível analisar a imagem", str(exc), "atencao")
        return cartao, estado, gr.update(visible=False), gr.update(visible=False)

    nivel = "risco" if resultado["alerta"] else "sucesso"
    titulo = "Possível incêndio detectado" if resultado["alerta"] else "Sem indício de incêndio"
    corpo = (f"Confiança: {badge_confianca(resultado['confianca'])}.\n{resultado['aviso']}")
    if local_texto:
        corpo = f"Local informado: {local_texto}.\n{corpo}"
    cartao = cartao_status(titulo, corpo, nivel)
    estado = adicionar_interacao(
        estado, tipo="imagem", entrada="imagem enviada",
        resumo_saida=f"{resultado['classe']} ({resultado['confianca']:.0%})", alerta=resultado["alerta"],
        local=local_texto,
    )
    return cartao, estado, gr.update(visible=resultado["alerta"]), gr.update(visible=not resultado["alerta"])


def _confirmar(estado: dict, avaliacao: str):
    ultima = ultima_interacao(estado)
    if not ultima:
        return estado, ""
    estado = marcar_avaliacao(estado, ultima["indice"], avaliacao)
    if avaliacao == "confirmado":
        mensagem = "Alerta confirmado e encaminhado para a fila de revisão do gestor."
    else:
        mensagem = "Marcado como falso alarme. Nenhum alerta será encaminhado."
    return estado, cartao_status("Registrado", mensagem, "sucesso")


def construir_aba_imagem(estado: gr.State) -> None:
    with gr.Tab("🛰️ Verificar imagem de satélite", id=3):
        gr.Markdown(f"### Segunda fonte de evidência\n{EXPLICACAO}")
        caixa_local = gr.Textbox(
            label="Local / região (opcional)",
            placeholder="Ex.: Zona rural de Novo Progresso, PA",
            info="Fica salvo junto com a análise no histórico (Relatórios).",
        )
        imagem = gr.Image(label="Imagem de satélite", type="filepath", height=280)
        botao_analisar = gr.Button("Analisar imagem", variant="primary")
        cartao_resultado = gr.HTML()

        with gr.Row(visible=False) as linha_confirmar_alerta:
            gr.Markdown("Confirma o alerta antes de encaminhar ao gestor?")
            botao_confirmar = gr.Button("✅ Confirmar alerta", size="sm")
            botao_falso_alarme = gr.Button("🚫 Falso alarme", size="sm")
        with gr.Row(visible=False) as linha_confirmar_ok:
            botao_ok = gr.Button("Marcar como revisado", size="sm")
        mensagem_confirmacao = gr.HTML()

        botao_analisar.click(
            _analisar, inputs=[imagem, caixa_local, estado],
            outputs=[cartao_resultado, estado, linha_confirmar_alerta, linha_confirmar_ok],
        )
        botao_confirmar.click(lambda e: _confirmar(e, "confirmado"), inputs=[estado],
                              outputs=[estado, mensagem_confirmacao])
        botao_falso_alarme.click(lambda e: _confirmar(e, "falso_alarme"), inputs=[estado],
                                 outputs=[estado, mensagem_confirmacao])
        botao_ok.click(lambda e: _confirmar(e, "revisado"), inputs=[estado],
                       outputs=[estado, mensagem_confirmacao])
