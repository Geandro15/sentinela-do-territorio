# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Testes do robô de triagem. Usam dados sintéticos (gerados aqui mesmo com

PIL) e simulam falhas de rede/arquivo com monkeypatch, não dependem de
internet nem de um modelo de Visão Computacional treinado para passar.
"""
from __future__ import annotations

import requests
from PIL import Image, ImageDraw, ImageFont

from .. import ocr, planilha, regras, robo_triagem, scraping

_FONTE_TESTE = ImageFont.load_default(size=28)


def _desenhar_formulario(tmp_path, nome: str, linhas: list[str]):
    # Fonte maior (não a bitmap padrão), o Tesseract lê com confiabilidade
    # bem maior assim, inclusive a pontuação (":"); achado real ao testar.
    caminho = tmp_path / f"{nome}.png"
    imagem = Image.new("RGB", (1500, 300), color="white")
    desenho = ImageDraw.Draw(imagem)
    for indice, linha in enumerate(linhas):
        desenho.text((20, 20 + indice * 50), linha, fill="black", font=_FONTE_TESTE)
    imagem.save(caminho)
    return caminho


# --------------------------------------------------------------------------
# OCR
# --------------------------------------------------------------------------

def test_ocr_extrai_os_tres_campos(tmp_path):
    caminho = _desenhar_formulario(tmp_path, "relato", [
        "Local: Zona rural, Municipio X", "Data: 15/11/2026",
        "Descricao: Fumaca e fogo na mata.",
    ])
    relato = ocr.extrair_relato(caminho)
    assert relato.local and "Municipio X" in relato.local
    assert relato.data and "15/11/2026" in relato.data
    assert relato.descricao and "fogo" in relato.descricao.lower()
    assert relato.campos_completos


def test_ocr_campo_ausente_fica_none(tmp_path):
    caminho = _desenhar_formulario(tmp_path, "relato_incompleto", ["Local: Sitio Z", "Data: 17/11/2026"])
    relato = ocr.extrair_relato(caminho)
    assert relato.descricao is None
    assert not relato.campos_completos


def test_ocr_imagem_inexistente_levanta_erro_claro(tmp_path):
    try:
        ocr.extrair_relato(tmp_path / "nao_existe.png")
        assert False, "deveria ter levantado ErroOCR"
    except ocr.ErroOCR as exc:
        assert "não encontrada" in str(exc)


def test_ocr_arquivo_corrompido_levanta_erro_claro_em_vez_de_travar(tmp_path):
    """Caso de falha tratado (barema, seção 5 "Evidências de validação"):

    um arquivo que não é uma imagem de verdade não derruba o processo, só
    gera um erro claro para quem chama decidir o que fazer."""
    caminho = tmp_path / "corrompido.jpg"
    caminho.write_bytes(b"isto nao e uma imagem de verdade")
    try:
        ocr.extrair_relato(caminho)
        assert False, "deveria ter levantado ErroOCR"
    except ocr.ErroOCR:
        pass


# --------------------------------------------------------------------------
# Web scraping (com simulação de falha de rede)
# --------------------------------------------------------------------------

def test_scraping_sucesso_extrai_total_de_focos(monkeypatch):
    class RespostaFalsa:
        content = b"PDF_FALSO"

        def raise_for_status(self):
            return None

    def _get_falso(url, timeout):
        return RespostaFalsa()

    def _texto_falso(conteudo):
        return "O boletim registrou 20.222 detecções de focos de fogo no mês."

    monkeypatch.setattr(scraping.requests, "get", _get_falso)
    monkeypatch.setattr(scraping, "_texto_do_pdf", _texto_falso)

    situacao = scraping.buscar_situacao_atual()
    assert situacao.obtido_com_sucesso
    assert situacao.total_focos_mes == 20222


def test_scraping_site_fora_do_ar_nao_levanta_excecao(monkeypatch):
    """Caso de falha tratado e demonstrado: o site do INPE fora do ar não

    derruba o robô, só faz a situação voltar sem o dado (evidência exigida
    pelo barema, seção 5)."""
    def _get_com_falha(url, timeout):
        raise requests.exceptions.ConnectionError("simulado: site fora do ar")

    monkeypatch.setattr(scraping.requests, "get", _get_com_falha)

    situacao = scraping.buscar_situacao_atual()
    assert situacao.obtido_com_sucesso is False
    assert situacao.total_focos_mes is None


# --------------------------------------------------------------------------
# Regra de decisão
# --------------------------------------------------------------------------

def test_regra_prioridade_alta_com_descricao_e_imagem_de_risco():
    prioridade = regras.classificar_prioridade(
        descricao="Vi fumaça e fogo na mata", imagem_alerta=True, total_focos_mes=None,
    )
    assert prioridade.nivel == "ALTA"


def test_regra_prioridade_baixa_sem_nenhum_sinal():
    prioridade = regras.classificar_prioridade(
        descricao="Tudo tranquilo na área hoje", imagem_alerta=False, total_focos_mes=None,
    )
    assert prioridade.nivel == "BAIXA"


def test_regra_sem_descricao_vira_revisar():
    prioridade = regras.classificar_prioridade(descricao=None, imagem_alerta=True, total_focos_mes=None)
    assert prioridade.nivel == "REVISAR"


def test_regra_total_de_focos_alto_soma_pontuacao():
    prioridade = regras.classificar_prioridade(
        descricao="Área de pastagem normal", imagem_alerta=False, total_focos_mes=50000,
    )
    assert prioridade.pontuacao == 1
    assert prioridade.nivel == "MEDIA"


# --------------------------------------------------------------------------
# Planilha
# --------------------------------------------------------------------------

def test_planilha_cria_e_acrescenta_linhas(tmp_path):
    caminho = tmp_path / "fila.xlsx"
    planilha.registrar_relato(caminho, {"Protocolo": "P1", "Prioridade": "ALTA"})
    planilha.registrar_relato(caminho, {"Protocolo": "P2", "Prioridade": "BAIXA"})

    from openpyxl import load_workbook
    pasta = load_workbook(caminho)
    linhas = list(pasta.active.iter_rows(values_only=True))
    assert linhas[0] == tuple(planilha.COLUNAS)
    assert linhas[1][0] == "P1"
    assert linhas[2][0] == "P2"


# --------------------------------------------------------------------------
# Fluxo completo (integração), sem depender de internet nem de modelo treinado
# --------------------------------------------------------------------------

def test_imagem_satelite_e_encontrada_mesmo_com_extensao_diferente_do_relato(tmp_path):
    """Achado real rodando o robô de ponta a ponta: o relato é .png e a

    imagem de satélite pareada é .jpg, a busca não pode exigir a mesma
    extensão dos dois arquivos."""
    relato = _desenhar_formulario(tmp_path, "relato_x", ["Local: A", "Data: 1/1/2026", "Descricao: teste"])
    satelite = tmp_path / "relato_x_satelite.jpg"
    satelite.write_bytes(b"fake-jpg")

    encontrada = robo_triagem._imagem_satelite_para(relato)
    assert encontrada == satelite


def test_fluxo_completo_processa_lote_sem_travar_no_arquivo_corrompido(tmp_path, monkeypatch):
    """Lote com 1 relato normal, 1 sem descrição (vira REVISAR) e 1 com

    imagem de satélite corrompida, o lote inteiro deve terminar mesmo
    assim (caso de falha tratado e demonstrado, barema seção 5)."""
    monkeypatch.setattr(robo_triagem, "PASTA_SAIDA", tmp_path / "saida")
    monkeypatch.setattr(robo_triagem, "PLANILHA_SAIDA", tmp_path / "saida" / "fila_atendimento.xlsx")
    monkeypatch.setattr(robo_triagem, "PASTA_NOTIFICACOES", tmp_path / "saida" / "notificacoes")
    monkeypatch.setattr(robo_triagem, "PASTA_LOGS", tmp_path / "logs")
    monkeypatch.setattr(robo_triagem, "PASTA_PROCESSADOS", tmp_path / "entrada" / "processados")
    monkeypatch.setattr(
        scraping, "buscar_situacao_atual",
        lambda hoje=None: scraping.SituacaoINPE(None, "indisponível", "", False),
    )

    pasta_entrada = tmp_path / "entrada"
    pasta_entrada.mkdir()
    _desenhar_formulario(pasta_entrada, "relato_ok", [
        "Local: Zona rural", "Data: 15/11/2026", "Descricao: Fumaca visivel na mata.",
    ])
    _desenhar_formulario(pasta_entrada, "relato_sem_descricao", ["Local: Sitio", "Data: 17/11/2026"])
    (pasta_entrada / "relato_imagem_corrompida_satelite.jpg").write_bytes(b"nao e uma imagem")
    _desenhar_formulario(pasta_entrada, "relato_imagem_corrompida", [
        "Local: Fazenda", "Data: 17/11/2026", "Descricao: Possivel incendio.",
    ])

    resultados = robo_triagem.executar(pasta_entrada)

    assert len(resultados) == 3
    protocolos_por_prioridade = {linha["Prioridade"] for linha in resultados}
    assert "REVISAR" in protocolos_por_prioridade  # o relato_sem_descricao
    assert (tmp_path / "saida" / "fila_atendimento.xlsx").exists()
    # a imagem de satélite corrompida não deve ter travado o processamento do relato
    assert any(linha["Arquivo"] == "relato_imagem_corrompida.png" for linha in resultados)
