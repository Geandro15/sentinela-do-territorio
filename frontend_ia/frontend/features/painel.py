# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Aba "📄 Relatórios": histórico das interações desta sessão (1 gráfico
Plotly + 2 filtros interativos), informações para baixar os datasets reais
usados no projeto, cada um com o link oficial da fonte, sem nenhum link
inventado, e, abaixo, os relatórios das disciplinas de estudo (Cluster
Computing e Computação Quântica & IA, para consulta).

Antes se chamava "Painel da sessão", o nome mudou para "Relatórios" a
pedido, e esta seção de datasets foi incluída na mesma aba.
"""
from __future__ import annotations

from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.express as px

from .menu import ABA_PAINEL

ROTULO_TIPO = {"pergunta": "Pergunta", "imagem": "Imagem"}

# Datasets reais usados no projeto, com a fonte oficial de cada um, # conferidos manualmente, nenhum link inventado.
DATASETS = [
    {
        "titulo": "🛰️ Wildfire Prediction Dataset (Visão Computacional)",
        "descricao": (
            "~39 mil imagens de satélite/aéreas, rotuladas \"wildfire\"/\"nowildfire\", usadas para treinar "
            "o classificador de imagens (`visao/`). Fonte: Kaggle."
        ),
        "link": "https://www.kaggle.com/datasets/abdelghaniaaba/wildfire-prediction-dataset",
        "rotulo_link": "Baixar no Kaggle",
    },
    {
        "titulo": "🔥 Boletins InfoQueima do INPE (Programa Queimadas)",
        "descricao": (
            "Boletins mensais em PDF com os focos de queimada por bioma e por estado, fonte dos 4 gráficos "
            "do dashboard inicial e dos dados usados no RPA (`rpa/scraping.py`) e no assistente (RAG)."
        ),
        "link": "https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/",
        "rotulo_link": "Ver pasta de boletins (INPE)",
    },
    {
        "titulo": "🗺️ Portal do Programa Queimadas (INPE)",
        "descricao": "Mapa e estatísticas de focos de queimada em tempo real, direto do INPE.",
        "link": "http://www.inpe.br/queimadas",
        "rotulo_link": "Abrir o portal do INPE",
    },
    {
        "titulo": "🤖 Relatos sintéticos do RPA",
        "descricao": (
            "Os relatos de teste do robô de triagem (`rpa/`) não vêm de um dataset externo: são gerados "
            "localmente, sem internet, por `python -m rpa.gerar_dados_teste`, por isso não têm link de "
            "download, só o comando para gerar de novo."
        ),
        "link": None,
        "rotulo_link": None,
    },
]


def raiz_do_projeto() -> Path:
    """Acha a pasta do projeto (a que tem `cluster_computing/` e

    `computacao_quantica/` dentro), subindo a partir deste arquivo, mesma
    ideia de `backend/providers/caminhos.py`, mas independente dele: o
    front-end não importa nada do back-end (fala só por HTTP, ver docstring
    do módulo em `frontend/app.py`).

    Pública (sem `_`) porque `frontend/app.py` e `app.py` também precisam
    dela, para liberar essa pasta em `allowed_paths` no `.launch()`, sem
    isso o Gradio bloqueia os `gr.File` dos relatórios abaixo, que ficam
    fora da árvore de `frontend_ia/` (em `cluster_computing/` e
    `computacao_quantica/`, pastas irmãs na raiz do projeto)."""
    candidato = Path(__file__).resolve()
    for _ in range(8):
        if (candidato / "cluster_computing" / "docs" / "relatorio_cluster.pdf").is_file():
            return candidato
        if candidato.parent == candidato:
            break
        candidato = candidato.parent
    return Path(__file__).resolve().parents[3]  # fallback: profundidade padrão do projeto


_RAIZ_PROJETO = raiz_do_projeto()

# Relatórios das disciplinas de estudo (sem integração de código com o
# app, são análises/simulações à parte), deixados aqui só para consulta.
RELATORIOS_DISCIPLINAS = [
    {
        "titulo": "☁️ Cluster Computing, simulação no iSPD",
        "descricao": (
            "Compara 2 e 4 workers simulando a análise dos áudios do CitizenTech numa rajada de alertas: "
            "ganho de 30,1% no tempo total e o gargalo de comunicação encontrado ao aumentar o cluster."
        ),
        "arquivo": _RAIZ_PROJETO / "cluster_computing" / "docs" / "relatorio_cluster.pdf",
    },
    {
        "titulo": "⚛️ Computação Quântica & IA, roadmap",
        "descricao": (
            "Avalia o gargalo de alocação de equipes em picos de ocorrências, a capacidade quântica "
            "(otimização) que o atacaria, e um roadmap clássico → quântico com ética, LGPD e ODS."
        ),
        "arquivo": _RAIZ_PROJETO / "computacao_quantica" / "docs" / "relatorio_quantica.pdf",
    },
    {
        "titulo": "🎯 Desafio CitizenTech, missão, visão e ecossistema",
        "descricao": (
            "Missão, visão e organograma do ecossistema do projeto, mais as seis perguntas do desafio "
            "respondidas em detalhe (quem participa, como funciona, qual problema resolve e os resultados)."
        ),
        "arquivo": _RAIZ_PROJETO / "DESAFIO_CITIZENTECH.pdf",
    },
]


def _dataframe(estado: dict) -> pd.DataFrame:
    historico = estado.get("historico") or []
    if not historico:
        return pd.DataFrame(
            columns=["indice", "hora", "tipo", "entrada", "local", "resumo_saida", "alerta", "avaliacao"]
        )
    return pd.DataFrame(historico)


def _filtrar(df: pd.DataFrame, filtro_tipo: str, somente_alerta: bool) -> pd.DataFrame:
    if df.empty:
        return df
    if filtro_tipo != "Todos":
        df = df[df["tipo"] == filtro_tipo]
    if somente_alerta:
        df = df[df["alerta"]]
    return df


def _grafico(df: pd.DataFrame):
    if df.empty:
        figura = px.bar(title="Sem interações registradas nesta sessão ainda")
        figura.update_layout(xaxis_visible=False, yaxis_visible=False)
        return figura
    contagem = (
        df.assign(tipo=df["tipo"].map(ROTULO_TIPO).fillna(df["tipo"]))
        .groupby(["tipo", "alerta"], as_index=False).size()
    )
    contagem["Situação"] = contagem["alerta"].map({True: "Alerta / abstenção", False: "Normal"})
    figura = px.bar(
        contagem, x="tipo", y="size", color="Situação", barmode="stack",
        labels={"tipo": "Tipo de interação", "size": "Quantidade"},
        color_discrete_map={"Alerta / abstenção": "#a31515", "Normal": "#1e7e34"},
        title="Interações da sessão, por tipo e situação",
    )
    figura.update_layout(legend_title_text="Situação")
    return figura


def _tabela(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "local" not in df.columns:  # histórico de sessões antigas, sem o campo
        df = df.assign(local="")
    colunas = ["indice", "hora", "tipo", "entrada", "local", "resumo_saida", "alerta", "avaliacao"]
    return df[colunas].rename(columns={
        "indice": "#", "hora": "Hora", "tipo": "Tipo", "entrada": "Entrada", "local": "Local",
        "resumo_saida": "Resultado", "alerta": "Alerta", "avaliacao": "Avaliação",
    })


def _atualizar(estado: dict, filtro_tipo: str, somente_alerta: bool):
    df = _filtrar(_dataframe(estado), filtro_tipo, somente_alerta)
    return _grafico(df), _tabela(df)


def _construir_secao_relatorios_disciplinas() -> None:
    gr.Markdown(
        "### 📚 Relatórios de estudo (Cluster Computing e Computação Quântica & IA)\n"
        "Essas duas disciplinas não têm código integrado ao app, são estudos à parte, deixados aqui só "
        "para consulta.",
        elem_classes=["texto-destaque"],
    )
    for item in RELATORIOS_DISCIPLINAS:
        with gr.Row():
            gr.Markdown(f"**{item['titulo']}**\n\n{item['descricao']}", elem_classes=["texto-destaque"])
            if item["arquivo"].is_file():
                gr.File(value=str(item["arquivo"]), label="Abrir / baixar PDF", interactive=False)
            else:
                gr.Markdown("_Arquivo não encontrado nesta instalação, confira a pasta do projeto._")


def _construir_secao_datasets() -> None:
    gr.Markdown("### 📥 Datasets usados no projeto", elem_classes=["texto-destaque"])
    for item in DATASETS:
        with gr.Row():
            if item["link"]:
                gr.Markdown(f"**{item['titulo']}**\n\n{item['descricao']}", elem_classes=["texto-destaque"])
                gr.Button(item["rotulo_link"], link=item["link"])
            else:
                gr.Markdown(
                    f"**{item['titulo']}**\n\n{item['descricao']}",
                    elem_classes=["texto-destaque"],
                )


def construir_aba_painel(estado: gr.State) -> None:
    # Id fixo (ABA_PAINEL, de menu.py), hard-coding um número aqui causou
    # um bug real: coincidiu com o id de outra aba depois de uma
    # reorganização, e o botão da lateral parava de abrir esta aba.
    with gr.Tab("📄 Relatórios", id=ABA_PAINEL):
        gr.Markdown("### Histórico desta sessão\nAs perguntas e imagens enviadas nas outras abas aparecem aqui.")
        with gr.Row():
            filtro_tipo = gr.Dropdown(choices=["Todos", "pergunta", "imagem"], value="Todos", label="Tipo de interação")
            filtro_alerta = gr.Checkbox(label="Mostrar somente alertas / abstenções", value=False)
            botao_atualizar = gr.Button("Atualizar painel")
        grafico = gr.Plot()
        tabela = gr.Dataframe(wrap=True)

        entradas = [estado, filtro_tipo, filtro_alerta]
        saidas = [grafico, tabela]
        botao_atualizar.click(_atualizar, inputs=entradas, outputs=saidas)
        filtro_tipo.change(_atualizar, inputs=entradas, outputs=saidas)
        filtro_alerta.change(_atualizar, inputs=entradas, outputs=saidas)

        gr.Markdown("---")
        _construir_secao_datasets()

        gr.Markdown("---")
        _construir_secao_relatorios_disciplinas()
