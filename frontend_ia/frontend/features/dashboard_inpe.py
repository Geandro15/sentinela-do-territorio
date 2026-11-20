# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Comparação 2025 vs. 2026 dos focos de queimada no Brasil, com números
reais extraídos dos boletins mensais do Programa Queimadas do INPE (o
mesmo boletim e a mesma extração já usados e validados em
``genai/coleta.py`` e ``rpa/scraping.py``).

Os números abaixo foram medidos uma única vez (fora da aplicação, com um
script de coleta) e guardados aqui como constantes, mesmo padrão do
``dashboard_visao.py``, para o app não depender de internet, nem de o
site do INPE estar no ar, toda vez que a tela inicial carrega.

4 gráficos, todos de dados reais e públicos do INPE:

1. e 2. Focos por mês e total, Brasil, jan–ago/2025 vs. jan–ago/2026, medido em 17/11/2026, buscando cada boletim mensal de 2025_01 a
   2026_12 em
   ``https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/``:
   todos os 12 meses de 2025 têm boletim publicado; em 2026, só até
   agosto (setembro a dezembro de 2026 ainda não haviam sido publicados
   nessa data, por isso a comparação usa só janeiro–agosto dos dois
   anos, o período que os dois têm em comum).
3. e 4. Focos por bioma e por estado, agosto/2026 vs. agosto/2025, copiados
   diretamente das Tabelas 1.1.1 e 1.2 do próprio boletim de agosto/2026
   (``2026_08_infoqueima.pdf``), que já trazem os dois anos lado a lado
   para o mesmo mês, não são uma comparação calculada aqui, é a
   comparação que o INPE já publica.

Para atualizar esses números depois que o INPE publicar os boletins
seguintes, rode de novo o mesmo método de extração usado em
``rpa/scraping.py`` (ou peça para o assistente repetir a coleta) e troque
as constantes abaixo.
"""
from __future__ import annotations

import gradio as gr
import plotly.express as px
import plotly.graph_objects as go

from .estilo_grafico import aplicar_estilo_translucido, negrito

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago"]

# 1. e 2. Focos de calor por mês, Brasil, boletins mensais do INPE (ver docstring acima).
FOCOS_2025_JAN_AGO = [3137, 1819, 2357, 1641, 4263, 6060, 9803, 18451]
FOCOS_2026_JAN_AGO = [4560, 1860, 1967, 2035, 3831, 5209, 6284, 20222]

TOTAL_2025 = sum(FOCOS_2025_JAN_AGO)
TOTAL_2026 = sum(FOCOS_2026_JAN_AGO)
VARIACAO_PCT = (TOTAL_2026 - TOTAL_2025) / TOTAL_2025 * 100

# 3. Focos por bioma em agosto, Tabela 1.1.1 do boletim INPE 2026_08_infoqueima.pdf.
BIOMAS_AGOSTO = {
    "Amazônia": {"2025": 6094, "2026": 9206},
    "Cerrado": {"2025": 8615, "2026": 8343},
    "Mata Atlântica": {"2025": 2384, "2026": 1275},
    "Caatinga": {"2025": 1188, "2026": 1242},
    "Pantanal": {"2025": 48, "2026": 132},
    "Pampa": {"2025": 122, "2026": 24},
}

# 4. Top 8 estados por focos em agosto/2026, Tabela 1.2 do mesmo boletim.
ESTADOS_AGOSTO = {
    "Pará": {"2025": 1314, "2026": 3962},
    "Mato Grosso": {"2025": 2322, "2026": 3691},
    "Amazonas": {"2025": 1842, "2026": 2231},
    "Maranhão": {"2025": 2493, "2026": 1937},
    "Tocantins": {"2025": 1541, "2026": 1925},
    "Bahia": {"2025": 1345, "2026": 1351},
    "Minas Gerais": {"2025": 1469, "2026": 1048},
    "Piauí": {"2025": 1472, "2026": 1024},
}

# Coordenadas reais da capital de cada estado (fonte: localização geográfica
# pública das capitais), usadas só para posicionar o marcador no mapa; o
# ponto fica na capital, não no centro exato do estado, até o projeto ter
# coordenadas por foco (o boletim do INPE não publica isso, só por estado).
CAPITAL_ESTADOS = {
    "Pará": {"cidade": "Belém", "lat": -1.4558, "lon": -48.4902},
    "Mato Grosso": {"cidade": "Cuiabá", "lat": -15.6014, "lon": -56.0979},
    "Amazonas": {"cidade": "Manaus", "lat": -3.1190, "lon": -60.0217},
    "Maranhão": {"cidade": "São Luís", "lat": -2.5307, "lon": -44.3068},
    "Tocantins": {"cidade": "Palmas", "lat": -10.1689, "lon": -48.3317},
    "Bahia": {"cidade": "Salvador", "lat": -12.9777, "lon": -38.5016},
    "Minas Gerais": {"cidade": "Belo Horizonte", "lat": -19.9167, "lon": -43.9345},
    "Piauí": {"cidade": "Teresina", "lat": -5.0892, "lon": -42.8019},
}


def _grafico_mensal() -> go.Figure:
    linhas = [
        {"Mês": mes, "Ano": "2025", "Focos": valor} for mes, valor in zip(MESES, FOCOS_2025_JAN_AGO)
    ] + [
        {"Mês": mes, "Ano": "2026", "Focos": valor} for mes, valor in zip(MESES, FOCOS_2026_JAN_AGO)
    ]
    figura = px.bar(
        linhas, x="Mês", y="Focos", color="Ano", barmode="group",
        title=negrito("1. Focos por mês, 2025 vs. 2026 (jan–ago, boletins INPE)"),
        color_discrete_map={"2025": "#5aa9e6", "2026": "#e65a5a"},
        text="Focos",
    )
    figura.update_traces(texttemplate="%{text:,}".replace(",", "."))
    return aplicar_estilo_translucido(figura)


def _grafico_total() -> go.Figure:
    figura = px.bar(
        x=["2025 (jan–ago)", "2026 (jan–ago)"], y=[TOTAL_2025, TOTAL_2026],
        text=[f"{TOTAL_2025:,}".replace(",", "."), f"{TOTAL_2026:,}".replace(",", ".")],
        labels={"x": "", "y": "Total de focos"},
        title=negrito(f"2. Total jan–ago: {VARIACAO_PCT:+.1f}% em 2026 vs. 2025"),
        color=["2025 (jan–ago)", "2026 (jan–ago)"], color_discrete_sequence=["#5aa9e6", "#e65a5a"],
    )
    figura.update_layout(showlegend=False)
    return aplicar_estilo_translucido(figura)


def _grafico_biomas() -> go.Figure:
    linhas = [
        {"Bioma": bioma, "Ano": ano, "Focos": valores[ano]}
        for bioma, valores in BIOMAS_AGOSTO.items() for ano in ("2025", "2026")
    ]
    figura = px.bar(
        linhas, x="Bioma", y="Focos", color="Ano", barmode="group",
        title=negrito("3. Focos por bioma, agosto/2026 vs. agosto/2025"),
        color_discrete_map={"2025": "#5aa9e6", "2026": "#e65a5a"},
        text="Focos",
    )
    figura.update_traces(texttemplate="%{text:,}".replace(",", "."))
    return aplicar_estilo_translucido(figura)


def _grafico_estados() -> go.Figure:
    estados_ordenados = sorted(ESTADOS_AGOSTO.items(), key=lambda item: item[1]["2026"], reverse=True)
    linhas = [
        {"Estado": estado, "Ano": ano, "Focos": valores[ano]}
        for estado, valores in estados_ordenados for ano in ("2025", "2026")
    ]
    figura = px.bar(
        linhas, x="Estado", y="Focos", color="Ano", barmode="group",
        title=negrito("4. Top 8 estados em agosto/2026, vs. agosto/2025"),
        color_discrete_map={"2025": "#5aa9e6", "2026": "#e65a5a"},
        text="Focos",
    )
    figura.update_traces(texttemplate="%{text:,}".replace(",", "."))
    figura.update_xaxes(tickangle=-30)
    return aplicar_estilo_translucido(figura)


def _grafico_mapa_estados() -> go.Figure:
    """Mapa do Brasil com um marcador na capital de cada um dos 8 estados

    com mais focos em agosto/2026, tamanho e cor pelo número de focos.
    Mapa leve (scattergeo nativo do Plotly, sem geojson nem dependência
    nova), pensado para rodar bem dentro do app."""
    estados = list(ESTADOS_AGOSTO.keys())
    figura = go.Figure(
        go.Scattergeo(
            lon=[CAPITAL_ESTADOS[e]["lon"] for e in estados],
            lat=[CAPITAL_ESTADOS[e]["lat"] for e in estados],
            text=[
                f"{e} ({CAPITAL_ESTADOS[e]['cidade']}): {ESTADOS_AGOSTO[e]['2026']} focos em ago/2026"
                for e in estados
            ],
            hoverinfo="text",
            marker=dict(
                size=[8 + (ESTADOS_AGOSTO[e]["2026"] / 120) for e in estados],
                color=[ESTADOS_AGOSTO[e]["2026"] for e in estados],
                colorscale=[[0, "#f4b183"], [1, "#a31515"]],
                line=dict(width=1, color="#ffffff"),
                sizemode="diameter",
            ),
        )
    )
    figura.update_geos(
        scope="south america", center=dict(lat=-12, lon=-53), projection_scale=3.2,
        showcountries=True, countrycolor="rgba(255,255,255,0.35)",
        showland=True, landcolor="rgba(255,255,255,0.08)",
        showocean=True, oceancolor="rgba(0,0,0,0)",
        bgcolor="rgba(0,0,0,0)",
    )
    figura.update_layout(
        title=negrito("5. Mapa, marcador na capital dos 8 estados com mais focos (ago/2026)"),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff", size=13),
        title_font=dict(color="#ffffff", size=15), margin=dict(t=60, l=0, r=0, b=0),
    )
    return figura


def construir_secao_destaque_inpe() -> None:
    """Seção em destaque na tela inicial, com 4 gráficos + 1 mapa reais do

    INPE (mês a mês, total, bioma, estado e mapa das capitais), sempre
    translúcidos e com texto branco em negrito, como o resto do dashboard."""
    gr.Markdown(
        "## 🔥 Queimadas no Brasil, 2025 vs. 2026\n"
        "Números reais dos boletins mensais do Programa Queimadas do INPE. Os dois primeiros "
        "gráficos comparam **janeiro a agosto** dos dois anos (o período que ambos já têm "
        "publicado); os dois seguintes vêm das tabelas de bioma e estado do próprio boletim de "
        "**agosto/2026**, que já traz o comparativo com agosto/2025; o mapa localiza os mesmos 8 "
        "estados, com um marcador na capital de cada um.",
        elem_classes=["texto-destaque"],
    )
    with gr.Row():
        gr.Plot(value=_grafico_mensal(), elem_classes=["grafico-translucido"])
        gr.Plot(value=_grafico_total(), elem_classes=["grafico-translucido"])
    with gr.Row():
        gr.Plot(value=_grafico_biomas(), elem_classes=["grafico-translucido"])
        gr.Plot(value=_grafico_estados(), elem_classes=["grafico-translucido"])
    with gr.Row():
        gr.Plot(value=_grafico_mapa_estados(), elem_classes=["grafico-translucido"])
