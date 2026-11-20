# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Testes da API. Usam pipelines simulados (monkeypatch): não precisam do
Ollama nem do modelo de visão treinado, então rodam em qualquer máquina.
"""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.pipelines.imagem import ErroImagem
from backend.pipelines.voz import ErroVoz
from backend.schemas.relatos import ImagemSaida, PerguntaPorVozSaida, PerguntaSaida

cliente = TestClient(app)


def test_saude():
    resposta = cliente.get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_perguntar_sucesso(monkeypatch):
    saida = PerguntaSaida(
        resposta="O risco de fogo é calculado com base na chuva dos últimos 120 dias. [1]",
        fontes=["[1] F1, FAQ (https://data.inpe.br/queimadas/faq/, consulta em 16/11/2026)"],
        motivo="respondida",
        motivo_legivel="Resposta conferida com os trechos das fontes.",
        sustentada=True,
    )
    monkeypatch.setattr("backend.routers.relatos.perguntar", lambda pergunta: saida)

    resposta = cliente.post("/api/perguntar", json={"pergunta": "Como é calculado o risco de fogo?"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["sustentada"] is True
    assert corpo["motivo"] == "respondida"
    assert corpo["fontes"]


def test_perguntar_nao_vaza_erro_tecnico_do_llm_no_texto(monkeypatch):
    """O genai (genai/assistente_rag.py) embute o erro técnico bruto no texto
    da resposta quando o LLM está fora do ar. A API tem que trocar esse texto
    antes de devolver ao cidadão, sem isso, 'erro técnico' vaza como se fosse
    a resposta do assistente (achado real, visto rodando a interface de ponta a
    ponta com o Ollama desligado)."""
    class FalsoAchado:
        def __init__(self):
            self.trecho = type("T", (), {"url": "https://x", "titulo": "t", "fonte": "F", "data_consulta": "hoje"})()

    class FalsaResposta:
        motivo = "erro_llm"
        resposta = "O modelo de linguagem não respondeu (Connection refused: localhost:11434). Veja os trechos."
        verificacao = {}

        def fontes(self):
            return ["[1] fonte"]

    class FalsoAssistente:
        def responder(self, pergunta):
            return FalsaResposta()

    import backend.pipelines.rag as modulo_rag
    monkeypatch.setattr(modulo_rag, "_ASSISTENTE", FalsoAssistente())

    resposta = cliente.post("/api/perguntar", json={"pergunta": "Como é calculado o risco de fogo?"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert "localhost:11434" not in corpo["resposta"]
    assert "Connection refused" not in corpo["resposta"]
    assert corpo["motivo"] == "erro_llm"


def test_perguntar_rejeita_pergunta_curta():
    resposta = cliente.post("/api/perguntar", json={"pergunta": "oi"})
    assert resposta.status_code == 422


def test_perguntar_modelo_fora_do_ar_nao_expoe_erro_interno(monkeypatch):
    def quebra(pergunta):
        raise RuntimeError("Connection refused: http://localhost:11434")

    monkeypatch.setattr("backend.routers.relatos.perguntar", quebra)

    resposta = cliente.post("/api/perguntar", json={"pergunta": "Qual bioma teve mais focos?"})

    assert resposta.status_code == 503
    assert "localhost:11434" not in resposta.json()["detail"]  # não vaza detalhe técnico ao cidadão


def test_perguntar_por_voz_sucesso(monkeypatch):
    saida = PerguntaPorVozSaida(
        pergunta_transcrita="Como é calculado o risco de fogo?",
        resposta="O risco de fogo é calculado com base na chuva dos últimos 120 dias. [1]",
        fontes=["[1] F1, FAQ (https://data.inpe.br/queimadas/faq/, consulta em 16/11/2026)"],
        motivo="respondida",
        motivo_legivel="Resposta conferida com os trechos das fontes.",
        sustentada=True,
        audio_base64=None,
    )
    monkeypatch.setattr("backend.routers.relatos.perguntar_por_voz", lambda caminho: saida)

    arquivo = io.BytesIO(b"conteudo-de-audio-de-teste")
    resposta = cliente.post("/api/perguntar-por-voz", files={"arquivo": ("fala.wav", arquivo, "audio/wav")})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["pergunta_transcrita"] == "Como é calculado o risco de fogo?"
    assert corpo["sustentada"] is True


def test_perguntar_por_voz_extensao_invalida():
    arquivo = io.BytesIO(b"nao e um audio")
    resposta = cliente.post("/api/perguntar-por-voz", files={"arquivo": ("documento.txt", arquivo, "text/plain")})
    assert resposta.status_code == 422


def test_perguntar_por_voz_nao_entendeu_nao_vaza_erro_tecnico(monkeypatch):
    """Se o STT falhar (ex.: modelo Whisper não instalado), a API devolve uma
    mensagem clara, nunca o erro técnico bruto da biblioteca."""
    def quebra(caminho):
        raise ErroVoz("Não foi possível entender o áudio enviado. Tente gravar de novo, falando perto do microfone.")

    monkeypatch.setattr("backend.routers.relatos.perguntar_por_voz", quebra)

    arquivo = io.BytesIO(b"conteudo-de-audio-de-teste")
    resposta = cliente.post("/api/perguntar-por-voz", files={"arquivo": ("fala.wav", arquivo, "audio/wav")})

    assert resposta.status_code == 422
    assert "Traceback" not in resposta.json()["detail"]


def test_perguntar_por_voz_modelo_stt_fora_do_ar_nao_expoe_erro_interno(monkeypatch):
    def quebra(caminho):
        raise RuntimeError("No module named 'faster_whisper'")

    monkeypatch.setattr("backend.routers.relatos.perguntar_por_voz", quebra)

    arquivo = io.BytesIO(b"conteudo-de-audio-de-teste")
    resposta = cliente.post("/api/perguntar-por-voz", files={"arquivo": ("fala.wav", arquivo, "audio/wav")})

    assert resposta.status_code == 503
    assert "faster_whisper" not in resposta.json()["detail"]


def test_classificar_imagem_sucesso(monkeypatch):
    saida = ImagemSaida(classe="wildfire", confianca=0.93, alerta=True,
                        aviso="Esta é uma sugestão automática, não uma decisão.")
    monkeypatch.setattr("backend.routers.relatos.classificar", lambda caminho: saida)

    arquivo = io.BytesIO(b"conteudo-de-teste")
    resposta = cliente.post("/api/classificar-imagem", files={"arquivo": ("foto.jpg", arquivo, "image/jpeg")})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["classe"] == "wildfire"
    assert corpo["alerta"] is True


def test_classificar_imagem_extensao_invalida():
    arquivo = io.BytesIO(b"nao e uma imagem")
    resposta = cliente.post("/api/classificar-imagem", files={"arquivo": ("documento.txt", arquivo, "text/plain")})
    assert resposta.status_code == 422


def test_classificar_imagem_modelo_ausente(monkeypatch):
    def quebra(caminho):
        raise ErroImagem("Modelo não encontrado em 'modelos/queimada_mobilenet_v2.keras'.")

    monkeypatch.setattr("backend.routers.relatos.classificar", quebra)

    arquivo = io.BytesIO(b"conteudo-de-teste")
    resposta = cliente.post("/api/classificar-imagem", files={"arquivo": ("foto.png", arquivo, "image/png")})

    assert resposta.status_code == 503
    assert "Modelo não encontrado" in resposta.json()["detail"]


@pytest.mark.parametrize("origem", ["http://localhost:7860"])
def test_cors_permite_origem_do_frontend(origem):
    resposta = cliente.options(
        "/api/perguntar",
        headers={"Origin": origem, "Access-Control-Request-Method": "POST"},
    )
    assert resposta.headers.get("access-control-allow-origin") == origem
