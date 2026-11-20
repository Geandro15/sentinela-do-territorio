# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Testes do front-end. Não sobem a interface nem chamam o back-end de
verdade: testam o estado, os componentes e as funções das telas de forma
isolada (com monkeypatch no lugar do cliente de API).
"""
from __future__ import annotations

import requests

from ..features import dashboard_inpe, dashboard_visao
from ..providers import api_cliente
from ..state.estado import adicionar_interacao, estado_inicial, marcar_avaliacao, ultima_interacao
from ..ui.componentes import badge_confianca, cartao_status


def test_estado_inicial_vazio():
    estado = estado_inicial()
    assert estado["historico"] == []
    assert ultima_interacao(estado) is None


def test_adicionar_interacao_nao_muta_estado_original():
    estado = estado_inicial()
    novo = adicionar_interacao(estado, tipo="pergunta", entrada="oi", resumo_saida="resp", alerta=False)
    assert estado["historico"] == []  # o estado antigo não foi alterado
    assert len(novo["historico"]) == 1
    assert ultima_interacao(novo)["tipo"] == "pergunta"


def test_adicionar_interacao_local_e_opcional():
    estado = estado_inicial()
    sem_local = adicionar_interacao(estado, tipo="pergunta", entrada="oi", resumo_saida="resp", alerta=False)
    assert ultima_interacao(sem_local)["local"] == ""

    com_local = adicionar_interacao(
        estado, tipo="pergunta", entrada="oi", resumo_saida="resp", alerta=False, local="Novo Progresso, PA",
    )
    assert ultima_interacao(com_local)["local"] == "Novo Progresso, PA"


def test_marcar_avaliacao_atualiza_interacao_certa():
    estado = estado_inicial()
    estado = adicionar_interacao(estado, tipo="imagem", entrada="foto.jpg", resumo_saida="wildfire (90%)", alerta=True)
    indice = ultima_interacao(estado)["indice"]
    estado = marcar_avaliacao(estado, indice, "confirmado")
    assert ultima_interacao(estado)["avaliacao"] == "confirmado"


def test_cartao_status_usa_cor_icone_e_palavra():
    html = cartao_status("Título", "Corpo da mensagem", "risco")
    assert "Risco" in html and "🔥" in html and "#a31515" in html


def test_cartao_status_corpo_tem_cor_fixa_no_tema_escuro():
    """Achado real rodando a interface no modo escuro do navegador: sem uma cor

    fixa no texto do corpo, ele herda branco e some sobre o fundo claro do
    cartão. Regressão para a correção em ui/componentes.py."""
    html = cartao_status("Título", "Corpo da mensagem", "sucesso")
    assert "color:#1a1a1a" in html


def test_badge_confianca_faixas():
    assert "alta" in badge_confianca(0.95)
    assert "moderada" in badge_confianca(0.70)
    assert "baixa" in badge_confianca(0.40)


def test_api_cliente_traduz_timeout(monkeypatch):
    def levanta(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(api_cliente.requests, "post", levanta)
    try:
        api_cliente.perguntar("Como é calculado o risco de fogo?")
        assert False, "deveria ter levantado ErroAPI"
    except api_cliente.ErroAPI as exc:
        assert "demorou" in str(exc)


def test_api_cliente_traduz_conexao_recusada(monkeypatch):
    def levanta(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(api_cliente.requests, "post", levanta)
    try:
        api_cliente.perguntar("Qual bioma teve mais focos?")
        assert False, "deveria ter levantado ErroAPI"
    except api_cliente.ErroAPI as exc:
        assert "back-end" in str(exc)


def test_api_cliente_perguntar_por_voz_traduz_erro(monkeypatch, tmp_path):
    def levanta(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    audio = tmp_path / "fala.wav"
    audio.write_bytes(b"conteudo-de-teste")
    monkeypatch.setattr(api_cliente.requests, "post", levanta)
    try:
        api_cliente.perguntar_por_voz(audio)
        assert False, "deveria ter levantado ErroAPI"
    except api_cliente.ErroAPI as exc:
        assert "back-end" in str(exc)


def test_dashboard_visao_gera_os_6_graficos_sem_erro():
    """Os 6 gráficos vêm dos números reais do relatório da Visão Computacional

    (visao/docs/relatorio_visao.md), este teste só confirma que cada um é
    montado sem erro, não que os números batem com o relatório (isso é
    conferido manualmente, já que são constantes copiadas de lá)."""
    graficos = [
        dashboard_visao._grafico_matriz_confusao(),
        dashboard_visao._grafico_metricas(),
        dashboard_visao._grafico_dataset(),
        dashboard_visao._grafico_falsos(),
        dashboard_visao._grafico_parametros(),
        dashboard_visao._grafico_tempo_treino(),
    ]
    assert len(graficos) == 6
    assert all(g is not None for g in graficos)


def test_dashboard_inpe_totais_batem_com_os_dados_mensais():
    """Os totais de 2025 e 2026 (jan-ago) são a soma dos 8 valores mensais

    reais extraídos dos boletins do INPE, este teste garante que a soma
    exibida no gráfico de total não diverge dos valores mês a mês, caso
    algum dos dois seja editado sem atualizar o outro."""
    assert dashboard_inpe.TOTAL_2025 == sum(dashboard_inpe.FOCOS_2025_JAN_AGO)
    assert dashboard_inpe.TOTAL_2026 == sum(dashboard_inpe.FOCOS_2026_JAN_AGO)
    assert len(dashboard_inpe.FOCOS_2025_JAN_AGO) == len(dashboard_inpe.FOCOS_2026_JAN_AGO) == len(dashboard_inpe.MESES)


def test_dashboard_inpe_gera_os_5_graficos_sem_erro():
    graficos = [
        dashboard_inpe._grafico_mensal(),
        dashboard_inpe._grafico_total(),
        dashboard_inpe._grafico_biomas(),
        dashboard_inpe._grafico_estados(),
        dashboard_inpe._grafico_mapa_estados(),
    ]
    assert all(g is not None for g in graficos)


def test_dashboard_inpe_mapa_cobre_os_mesmos_8_estados():
    """O mapa usa a capital de cada estado do ESTADOS_AGOSTO, se faltar

    coordenada de algum estado, o mapa quebra silenciosamente (um estado
    sem marcador), então este teste garante que a lista bate certinho."""
    assert set(dashboard_inpe.CAPITAL_ESTADOS.keys()) == set(dashboard_inpe.ESTADOS_AGOSTO.keys())
    for capital in dashboard_inpe.CAPITAL_ESTADOS.values():
        assert -35 <= capital["lat"] <= 6  # faixa de latitude do Brasil
        assert -74 <= capital["lon"] <= -34  # faixa de longitude do Brasil


def test_dashboard_inpe_biomas_e_estados_tem_os_dois_anos():
    """Cada bioma e cada estado precisa ter os dois anos (2025 e 2026)

    para a comparação do gráfico fazer sentido, valores copiados direto
    das Tabelas 1.1.1 e 1.2 do boletim INPE de agosto/2026."""
    for valores in dashboard_inpe.BIOMAS_AGOSTO.values():
        assert set(valores.keys()) == {"2025", "2026"}
    for valores in dashboard_inpe.ESTADOS_AGOSTO.values():
        assert set(valores.keys()) == {"2025", "2026"}
