# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Painel com os resultados reais do treinamento do classificador de
imagens (disciplina de Visão Computacional), documentados em
``visao/docs/relatorio_visao.md``. Os números abaixo são os mesmos do
relatório (medidos no notebook do Colab), não são recalculados aqui, só
exibidos como gráficos, para não arriscar divergência entre os dois
módulos.

Diferente da aba "Relatórios" (que mostra o histórico de interações ao
vivo), este painel é fixo: mostra o desempenho do modelo já treinado,
sempre com os mesmos 6 gráficos, sem precisar de nenhuma ação do cidadão.

Fundo translúcido e texto branco em negrito (``estilo_grafico``), para
ficar legível em cima da foto da Terra do fundo do app.
"""
from __future__ import annotations

import gradio as gr
import plotly.express as px
import plotly.graph_objects as go

from .estilo_grafico import aplicar_estilo_translucido, negrito

# Números do notebook de Visão Computacional, seção 4 de
# visao/docs/relatorio_visao.md, conjunto de teste, 6.299 imagens.
MATRIZ_CONFUSAO = [[2746, 74], [136, 3343]]  # [real_sem, real_com] x [previsto_sem, previsto_com]
METRICAS = {"Acurácia": 0.967, "Precisão": 0.978, "Recall": 0.961, "F1-score": 0.970}
DATASET = {
    "Treino": {"sem incêndio": 14500, "com incêndio": 15750},
    "Validação": {"sem incêndio": 2820, "com incêndio": 3480},
    "Teste": {"sem incêndio": 2820, "com incêndio": 3480},
}
FALSOS = {"Falsos positivos": 74, "Falsos negativos": 136}
PARAMETROS_MODELO = {"Treináveis (nova camada)": 1281, "Congelados (MobileNetV2)": 2259265 - 1281}
TEMPO_POR_EPOCA_S = {"Mínimo": 50, "Máximo": 109}


def _grafico_matriz_confusao() -> go.Figure:
    figura = px.imshow(
        MATRIZ_CONFUSAO,
        x=["Previsto: sem incêndio", "Previsto: com incêndio"],
        y=["Real: sem incêndio", "Real: com incêndio"],
        text_auto=True, color_continuous_scale="Reds",
        title=negrito("1. Matriz de confusão (conjunto de teste, 6.299 imagens)"),
    )
    figura.update_layout(coloraxis_showscale=False)
    return aplicar_estilo_translucido(figura)


def _grafico_metricas() -> go.Figure:
    figura = px.bar(
        x=list(METRICAS.keys()), y=list(METRICAS.values()), text=[f"{v:.1%}" for v in METRICAS.values()],
        labels={"x": "", "y": "Valor"}, range_y=[0, 1],
        title=negrito("2. Métricas do modelo no conjunto de teste"),
        color=list(METRICAS.keys()),
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    figura.update_layout(showlegend=False)
    return aplicar_estilo_translucido(figura)


def _grafico_dataset() -> go.Figure:
    linhas = [
        {"Conjunto": conjunto, "Classe": classe, "Imagens": quantidade}
        for conjunto, classes in DATASET.items()
        for classe, quantidade in classes.items()
    ]
    figura = px.bar(
        linhas, x="Conjunto", y="Imagens", color="Classe", barmode="group",
        title=negrito("3. Imagens por conjunto e classe (Wildfire Prediction Dataset)"),
        color_discrete_map={"sem incêndio": "#1e7e34", "com incêndio": "#a31515"},
    )
    return aplicar_estilo_translucido(figura)


def _grafico_falsos() -> go.Figure:
    figura = px.bar(
        x=list(FALSOS.keys()), y=list(FALSOS.values()), text=list(FALSOS.values()),
        labels={"x": "", "y": "Quantidade"},
        title=negrito("4. Falsos positivos vs. falsos negativos (teste)"),
        color=list(FALSOS.keys()), color_discrete_sequence=["#d4a017", "#d64545"],
    )
    figura.update_layout(showlegend=False)
    return aplicar_estilo_translucido(figura)


def _grafico_parametros() -> go.Figure:
    figura = px.bar(
        x=list(PARAMETROS_MODELO.values()), y=list(PARAMETROS_MODELO.keys()), orientation="h",
        text=[f"{v:,}".replace(",", ".") for v in PARAMETROS_MODELO.values()],
        labels={"x": "Parâmetros", "y": ""}, log_x=True,
        title=negrito("5. Parâmetros do modelo (escala logarítmica)"),
        color=list(PARAMETROS_MODELO.keys()), color_discrete_sequence=px.colors.qualitative.Set2,
    )
    figura.update_layout(showlegend=False)
    return aplicar_estilo_translucido(figura)


def _grafico_tempo_treino() -> go.Figure:
    figura = px.bar(
        x=list(TEMPO_POR_EPOCA_S.keys()), y=list(TEMPO_POR_EPOCA_S.values()),
        text=[f"{v}s" for v in TEMPO_POR_EPOCA_S.values()],
        labels={"x": "", "y": "Segundos"},
        title=negrito("6. Tempo por época de treino (Colab, GPU T4)"),
        color=list(TEMPO_POR_EPOCA_S.keys()), color_discrete_sequence=["#8a8a8a", "#2fa84f"],
    )
    figura.update_layout(showlegend=False)
    return aplicar_estilo_translucido(figura)


def construir_secao_dashboard_visao() -> None:
    """Mostra os 6 gráficos já prontos (sem precisar de clique nenhum, os valores vêm do relatório, não de uma chamada ao modelo)."""
    gr.Markdown(
        "### 📊 Resultados da Visão Computacional\n"
        "Desempenho do classificador de imagens já treinado (MobileNetV2, transferência de aprendizado), "
        "medido no conjunto de teste do Wildfire Prediction Dataset, ver `visao/docs/relatorio_visao.md`.",
        elem_classes=["texto-destaque"],
    )
    with gr.Row():
        gr.Plot(value=_grafico_matriz_confusao(), elem_classes=["grafico-translucido"])
        gr.Plot(value=_grafico_metricas(), elem_classes=["grafico-translucido"])
    with gr.Row():
        gr.Plot(value=_grafico_dataset(), elem_classes=["grafico-translucido"])
        gr.Plot(value=_grafico_falsos(), elem_classes=["grafico-translucido"])
    with gr.Row():
        gr.Plot(value=_grafico_parametros(), elem_classes=["grafico-translucido"])
        gr.Plot(value=_grafico_tempo_treino(), elem_classes=["grafico-translucido"])
