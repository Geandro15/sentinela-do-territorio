# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Estilo visual compartilhado pelos gráficos do app: fundo transparente

(para o card translúcido por cima da foto da Terra aparecer por trás) e
texto branco em negrito, para ficar legível sobre o fundo escuro, usado
por ``dashboard_visao.py`` e ``dashboard_inpe.py``, para não duplicar essa
configuração em cada gráfico.
"""
from __future__ import annotations

import plotly.graph_objects as go

COR_TEXTO = "#ffffff"
COR_GRADE = "rgba(255, 255, 255, 0.18)"


def aplicar_estilo_translucido(figura: go.Figure) -> go.Figure:
    """Deixa o fundo do gráfico transparente e o texto branco em negrito

    (negrito via tags ``<b>`` no próprio texto, que o Plotly interpreta,
    já que a propriedade de fonte não tem um "bold" nativo)."""
    figura.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COR_TEXTO, size=13),
        title_font=dict(color=COR_TEXTO, size=15),
        legend=dict(font=dict(color=COR_TEXTO)),
        margin=dict(t=60),
    )
    figura.update_xaxes(
        tickfont=dict(color=COR_TEXTO), title_font=dict(color=COR_TEXTO), gridcolor=COR_GRADE, zerolinecolor=COR_GRADE
    )
    figura.update_yaxes(
        tickfont=dict(color=COR_TEXTO), title_font=dict(color=COR_TEXTO), gridcolor=COR_GRADE, zerolinecolor=COR_GRADE
    )
    # Textos de dados desenhados em cima das barras (text_auto, text=...)
    # também em branco e negrito, senão herdam a cor escura padrão do Plotly.
    figura.update_traces(selector=dict(type="bar"), textfont=dict(color=COR_TEXTO))
    return figura


def negrito(texto: str) -> str:
    """Envolve um texto em ``<b>``, usado nos títulos dos gráficos, já que

    é assim que o Plotly reconhece negrito dentro de ``title``/``text``."""
    return f"<b>{texto}</b>"
