# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Front-end Gradio do POC CitizenTech (disciplina Front-end em Sistemas de IA).

Fala só com o back-end FastAPI (``frontend/providers/api_cliente.py``),
nunca com o LLM ou o modelo de visão diretamente. Para rodar localmente
(de dentro de frontend_ia/):

    python -m frontend.app

A navegação é toda pela barra lateral (``features/menu.py``), a faixa
nativa de abas do Gradio fica escondida por CSS (``_css_fundo``), então a
única forma de trocar de tela é pelos botões da lateral.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

import gradio as gr

from .features.chat import construir_aba_perguntar
from .features.chat_flutuante import construir_chat_flutuante
from .features.imagem import construir_aba_imagem
from .features.menu import (
    construir_aba_dashboard,
    construir_aba_dashboard_visao,
    construir_aba_desafio,
    construir_aba_informacoes,
    construir_barra_lateral,
)
from .features.painel import construir_aba_painel, raiz_do_projeto
from .features.voz import construir_aba_voz
from .providers.api_cliente import verificar_saude
from .state.estado import estado_inicial

TITULO = "Sentinela do Território, CitizenTech"

_PASTA_ASSETS = Path(__file__).resolve().parent / "assets"
_IMAGEM_FUNDO = _PASTA_ASSETS / "fundo_terra.jpg"
_IMAGEM_LOGO = _PASTA_ASSETS / "logo_sentinela.png"


def _b64(caminho: Path) -> str | None:
    try:
        return base64.b64encode(caminho.read_bytes()).decode("ascii")
    except OSError:
        return None


def _css_fundo() -> str:
    """Fundo com a foto da Terra (NASA Blue Marble), com uma camada escura

    por cima para o texto continuar legível, e a faixa nativa de abas do
    Gradio escondida, a navegação agora é só pela barra lateral. Cards
    (gráficos, logo) translúcidos por cima, deixando a foto aparecer por
    trás, com texto sempre branco em negrito para continuar legível."""
    dados_fundo = _b64(_IMAGEM_FUNDO)
    if dados_fundo:
        fundo = (
            f"background-image: linear-gradient(rgba(8, 12, 20, 0.72), rgba(8, 12, 20, 0.72)), "
            f"url('data:image/jpeg;base64,{dados_fundo}');"
        )
    else:
        fundo = "background-color: #0b1220;"  # sem a imagem, cor sólida escura em vez de quebrar

    return f"""
    .gradio-container {{
        {fundo}
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }}
    /* Faixa nativa de abas escondida, a navegação é só pela barra lateral.
       O botão "More tabs" (overflow) do Gradio fica fora dessa faixa, por
       isso precisa de uma regra própria, achado real testando a tela. */
    .tab-nav, [role="tablist"], button[aria-label="More tabs"] {{
        display: none !important;
    }}
    .aviso-backend, .aviso-backend * {{
        color: #ffe08a !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 6px rgba(0, 0, 0, 0.8);
    }}
    /* Painel translúcido do logo: fundo escuro semitransparente com
       desfoque, para a foto da Terra continuar visível por trás. */
    .logo-painel {{
        display: flex;
        justify-content: center;
        padding: 14px 0;
        /* Painel claro (não escuro), o logo tem texto verde-escuro, feito
           para fundo claro; um painel escuro deixava o texto quase
           ilegível. "Vidro fosco" claro e translúcido: o globo ainda
           aparece por trás, suavizado, e o texto do logo continua nítido. */
        background: rgba(255, 255, 255, 0.32);
        backdrop-filter: blur(6px);
        border-radius: 12px;
        margin-bottom: 10px;
    }}
    .logo-painel img {{
        max-height: 170px;
    }}
    /* Texto "em destaque" (títulos dos dashboards, Informações do sistema):
       branco em negrito com sombra, para ler bem sobre a foto da Terra. */
    .texto-destaque, .texto-destaque * {{
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 6px rgba(0, 0, 0, 0.85);
    }}
    /* Cards dos gráficos (Plot) translúcidos, no lugar do branco sólido
       padrão do tema, a foto da Terra aparece por trás, só suavizada. */
    .grafico-translucido {{
        background: rgba(8, 12, 20, 0.45) !important;
        backdrop-filter: blur(3px);
        border-color: rgba(255, 255, 255, 0.15) !important;
    }}
    .grafico-translucido .label-wrap, .grafico-translucido .label-wrap * {{
        color: #ffffff !important;
    }}
    /* Chat flutuante: fica fora das abas (direto no gr.Blocks), por isso
       aparece por cima de qualquer tela. O botão (FAB) fica sempre visível
       no canto; o painel só aparece depois de clicado. */
    .chat-fab {{
        position: fixed !important;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        width: 56px !important;
        height: 56px !important;
        min-width: 56px !important;
        border-radius: 50% !important;
        font-size: 24px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
        background: rgba(30, 126, 52, 0.92) !important;
        color: #ffffff !important;
        border: none !important;
    }}
    .chat-painel {{
        position: fixed !important;
        bottom: 92px;
        right: 24px;
        z-index: 999;
        width: 340px !important;
        height: auto !important;
        min-height: 0 !important;
        max-height: 72vh !important;
        overflow-y: auto !important;
        background: rgba(8, 12, 20, 0.88) !important;
        backdrop-filter: blur(8px);
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        padding: 10px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.55);
    }}
    .chat-painel > * {{
        flex-shrink: 0 !important;
    }}
    /* O Gradio duplica a div do Group (a de fora e uma de dentro recebem a
       MESMA classe "chat-painel"), achado real inspecionando o DOM: as
       duas viravam position:fixed, a de dentro saía do fluxo e a de fora
       colapsava para ~22px de altura. A de dentro só precisa preencher a
       de fora, sem fixar posição de novo. */
    .chat-painel .chat-painel {{
        position: static !important;
        width: 100% !important;
        height: auto !important;
        max-height: none !important;
    }}
    /* A regra acima escondeu TODA faixa de abas da página, inclusive a
       miniatura (Texto/Voz/Imagem) de dentro do chat flutuante, essa
       precisa continuar visível, é a navegação interna do próprio
       painel. */
    .chat-painel .tab-nav, .chat-painel [role="tablist"] {{
        display: flex !important;
    }}
    .chat-painel-cabecalho {{
        align-items: center;
        justify-content: space-between;
    }}
    .chat-fechar {{
        max-width: 36px !important;
        min-width: 36px !important;
    }}
    /* Em telas estreitas o painel ocupa quase a largura toda, para não
       ficar espremido nem sair da tela. */
    @media (max-width: 480px) {{
        .chat-painel {{
            width: calc(100vw - 32px);
            right: 16px;
        }}
        .chat-fab {{
            right: 16px;
        }}
    }}
    """


def _html_logo() -> str:
    dados_logo = _b64(_IMAGEM_LOGO)
    if not dados_logo:
        return f'<div class="logo-painel"><h1 style="color:#fff;">🔥 {TITULO}</h1></div>'
    return f'<div class="logo-painel"><img src="data:image/png;base64,{dados_logo}" alt="{TITULO}"></div>'


def construir_app() -> gr.Blocks:
    with gr.Blocks(title=TITULO, css=_css_fundo()) as app:
        estado = gr.State(estado_inicial())

        gr.HTML(_html_logo())
        if not verificar_saude():
            gr.Markdown(
                "⚠️ **O back-end não respondeu agora.** As telas abaixo continuam abrindo, "
                "mas uma pergunta ou imagem enviada pode retornar erro até o serviço voltar.",
                elem_classes=["aviso-backend"],
            )

        with gr.Tabs() as abas:
            construir_aba_dashboard()
            construir_aba_perguntar(estado)
            construir_aba_voz(estado)
            construir_aba_imagem(estado)
            construir_aba_dashboard_visao()
            construir_aba_painel(estado)
            construir_aba_informacoes()
            construir_aba_desafio()

        construir_barra_lateral(abas)
        construir_chat_flutuante(estado)

    return app


if __name__ == "__main__":
    porta = int(os.environ.get("FRONTEND_PORT", "7860"))
    # allowed_paths libera a pasta raiz do projeto (inclui cluster_computing/
    # e computacao_quantica/, fora da árvore de frontend_ia/) para os
    # gr.File dos relatórios na aba "📄 Relatórios" (features/painel.py).
    construir_app().launch(
        server_name="0.0.0.0",
        server_port=porta,
        theme=gr.themes.Soft(),
        allowed_paths=[str(raiz_do_projeto())],
    )
