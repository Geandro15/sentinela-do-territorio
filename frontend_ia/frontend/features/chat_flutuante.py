# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Chat flutuante: um botão fixo no canto da tela, visível em qualquer
aba (fica fora do ``gr.Tabs()``, direto no ``gr.Blocks``), que abre um
painel pequeno com 3 jeitos de falar com o assistente, texto, voz e
imagem de satélite, sem precisar trocar de aba.

Reaproveita as MESMAS funções de ``_responder``/``_analisar``/``_avaliar``/
``_confirmar`` já usadas nas abas "Relatar / Perguntar" (``chat.py``),
"Perguntar por voz" (``voz.py``) e "Verificar imagem" (``imagem.py``), em vez de reimplementar a lógica de resposta aqui, este módulo só monta
componentes de UI próprios (compactos) e os liga a essas mesmas funções.
Isso garante que o chat flutuante mostre exatamente o mesmo conteúdo que
as abas, motivo legível, fontes citadas, o aviso de "sugestão automática,
não uma decisão" da imagem, o campo de local e os botões de feedback/
confirmação de alerta, sem duplicar (e sem desalinhar) a lógica de cada um.

Por usar o mesmo ``estado`` (gr.State) compartilhado com as outras abas, as
interações feitas aqui também entram no histórico de "📄 Relatórios"; como
a função é a mesma usada pela aba, o campo "entrada" do histórico não
diferencia se a pergunta veio da aba ou do atalho flutuante.
"""
from __future__ import annotations

import time

import gradio as gr

from .chat import _avaliar as _avaliar_texto
from .chat import _responder as _responder_texto
from .imagem import _analisar as _analisar_imagem
from .imagem import _confirmar as _confirmar_imagem
from .voz import _responder as _responder_voz


def _alternar(aberto: bool):
    novo = not aberto
    return novo, gr.update(visible=novo)


# Aviso de tempo de espera: ao perguntar (por texto, voz ou imagem), um
# relógio (gr.Timer) conta os segundos em tempo real enquanto o back-end
# responde, assim dá pra saber que está processando, e não travado. Os 3
# jeitos de perguntar (texto/voz/imagem) compartilham o mesmo relógio,
# porque só uma pergunta é feita de cada vez.
def _iniciar_espera():
    return gr.update(value="⏳ Aguardando resposta... 0s", visible=True), gr.Timer(active=True), time.time()


def _atualizar_cronometro(inicio: float):
    decorrido = int(time.time() - inicio)
    return gr.update(value=f"⏳ Aguardando resposta... {decorrido}s")


def _finalizar_espera(inicio: float):
    decorrido = time.time() - inicio
    return gr.update(value=f"✅ Respondido em {decorrido:.1f}s", visible=True), gr.Timer(active=False)


def construir_chat_flutuante(estado: gr.State) -> None:
    """Botão fixo (FAB) + painel que abre por cima de qualquer aba, por

    isso é chamado em app.py fora do ``gr.Tabs()``, direto no ``gr.Blocks``
    principal."""
    aberto = gr.State(False)

    botao_fab = gr.Button("💬", elem_classes=["chat-fab"])

    with gr.Group(visible=False, elem_classes=["chat-painel"]) as painel:
        with gr.Row(elem_classes=["chat-painel-cabecalho"]):
            gr.Markdown("### 💬 Assistente", elem_classes=["texto-destaque"])
            botao_fechar = gr.Button("✕", elem_classes=["chat-fechar"], size="sm")

        # Compartilhados pelas 3 abas (texto/voz/imagem), só uma pergunta
        # é feita de cada vez, então um relógio só já basta.
        status_espera = gr.Markdown(visible=False, elem_classes=["texto-destaque"])
        cronometro = gr.Timer(1, active=False)
        instante_inicio = gr.State(0.0)
        cronometro.tick(_atualizar_cronometro, inputs=[instante_inicio], outputs=[status_espera])

        with gr.Tabs():
            with gr.Tab("⌨️ Texto"):
                caixa_local_texto = gr.Textbox(
                    placeholder="Local / região (opcional)", label=None, show_label=False,
                )
                caixa_pergunta = gr.Textbox(
                    placeholder="Pergunte sobre queimadas...", label=None, show_label=False, lines=2,
                )
                botao_perguntar = gr.Button("Perguntar", size="sm", variant="primary")
                resposta_texto = gr.HTML()
                fontes_texto = gr.Markdown()
                with gr.Row(visible=False) as linha_feedback_texto:
                    gr.Markdown("Essa resposta ajudou?")
                    botao_util = gr.Button("👍", size="sm")
                    botao_nao_ajudou = gr.Button("👎", size="sm")
                mensagem_feedback_texto = gr.HTML()

            with gr.Tab("🎙️ Voz"):
                audio_entrada = gr.Audio(sources=["microphone", "upload"], type="filepath", show_label=False)
                botao_perguntar_voz = gr.Button("Transcrever e perguntar", size="sm", variant="primary")
                transcricao_voz = gr.Markdown()
                resposta_voz = gr.HTML()
                audio_resposta = gr.Audio(type="filepath", show_label=False, autoplay=True)

            with gr.Tab("🛰️ Imagem"):
                caixa_local_imagem = gr.Textbox(
                    placeholder="Local / região (opcional)", label=None, show_label=False,
                )
                gr.Markdown("Anexe uma imagem de satélite da região.")
                imagem_entrada = gr.Image(type="filepath", show_label=False, height=160)
                botao_analisar = gr.Button("Analisar imagem", size="sm", variant="primary")
                resposta_imagem = gr.HTML()
                with gr.Row(visible=False) as linha_confirmar_alerta:
                    gr.Markdown("Confirma o alerta?")
                    botao_confirmar = gr.Button("✅", size="sm")
                    botao_falso_alarme = gr.Button("🚫", size="sm")
                with gr.Row(visible=False) as linha_confirmar_ok:
                    botao_ok = gr.Button("Marcar como revisado", size="sm")
                mensagem_confirmacao_imagem = gr.HTML()

    botao_fab.click(_alternar, inputs=[aberto], outputs=[aberto, painel])
    botao_fechar.click(_alternar, inputs=[aberto], outputs=[aberto, painel])

    entradas_espera = []
    saidas_espera = [status_espera, cronometro, instante_inicio]
    saidas_fim_espera = [status_espera, cronometro]

    # Texto: mesma função _responder de chat.py (motivo legível, fontes
    # citadas, campo de local e visibilidade do feedback inclusos).
    botao_perguntar.click(
        _iniciar_espera, inputs=entradas_espera, outputs=saidas_espera,
    ).then(
        _responder_texto, inputs=[caixa_pergunta, caixa_local_texto, estado],
        outputs=[resposta_texto, fontes_texto, estado, linha_feedback_texto],
    ).then(_finalizar_espera, inputs=[instante_inicio], outputs=saidas_fim_espera)

    caixa_pergunta.submit(
        _iniciar_espera, inputs=entradas_espera, outputs=saidas_espera,
    ).then(
        _responder_texto, inputs=[caixa_pergunta, caixa_local_texto, estado],
        outputs=[resposta_texto, fontes_texto, estado, linha_feedback_texto],
    ).then(_finalizar_espera, inputs=[instante_inicio], outputs=saidas_fim_espera)

    botao_util.click(lambda e: _avaliar_texto(e, "util"), inputs=[estado], outputs=[estado, mensagem_feedback_texto])
    botao_nao_ajudou.click(lambda e: _avaliar_texto(e, "nao_ajudou"), inputs=[estado],
                            outputs=[estado, mensagem_feedback_texto])

    # Voz: mesma função _responder de voz.py (motivo legível incluso).
    botao_perguntar_voz.click(
        _iniciar_espera, inputs=entradas_espera, outputs=saidas_espera,
    ).then(
        _responder_voz, inputs=[audio_entrada, estado],
        outputs=[resposta_voz, transcricao_voz, audio_resposta, estado],
    ).then(_finalizar_espera, inputs=[instante_inicio], outputs=saidas_fim_espera)

    # Imagem: mesma função _analisar de imagem.py (aviso de "sugestão
    # automática", campo de local e as linhas de confirmação incluídos).
    botao_analisar.click(
        _iniciar_espera, inputs=entradas_espera, outputs=saidas_espera,
    ).then(
        _analisar_imagem, inputs=[imagem_entrada, caixa_local_imagem, estado],
        outputs=[resposta_imagem, estado, linha_confirmar_alerta, linha_confirmar_ok],
    ).then(_finalizar_espera, inputs=[instante_inicio], outputs=saidas_fim_espera)

    botao_confirmar.click(lambda e: _confirmar_imagem(e, "confirmado"), inputs=[estado],
                          outputs=[estado, mensagem_confirmacao_imagem])
    botao_falso_alarme.click(lambda e: _confirmar_imagem(e, "falso_alarme"), inputs=[estado],
                             outputs=[estado, mensagem_confirmacao_imagem])
    botao_ok.click(lambda e: _confirmar_imagem(e, "revisado"), inputs=[estado],
                   outputs=[estado, mensagem_confirmacao_imagem])
