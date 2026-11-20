# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Cliente HTTP do front-end. É o único lugar que fala com o back-end, nenhuma tela chama o LLM ou o modelo diretamente, nem monta a URL da API
na mão.
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

URL_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
TEMPO_LIMITE_S = float(os.environ.get("API_TIMEOUT_S", "60"))


class ErroAPI(RuntimeError):
    """Erro de comunicação com o back-end, já em uma mensagem segura para o cidadão."""


def _tratar_erro(exc: Exception) -> ErroAPI:
    if isinstance(exc, requests.exceptions.Timeout):
        return ErroAPI("O assistente demorou demais para responder. Tente de novo em instantes.")
    if isinstance(exc, requests.exceptions.ConnectionError):
        return ErroAPI("Não foi possível falar com o serviço agora. Verifique se o back-end está no ar.")
    if isinstance(exc, requests.exceptions.HTTPError):
        resposta = exc.response
        detalhe = "Pedido inválido."
        try:
            corpo = resposta.json()
            detalhe = corpo.get("detail") or detalhe
        except ValueError:
            pass
        if isinstance(detalhe, list):  # erro de validação do Pydantic (422)
            detalhe = "Dados inválidos: " + "; ".join(str(d.get("msg", d)) for d in detalhe)
        return ErroAPI(str(detalhe))
    return ErroAPI("Algo deu errado ao falar com o serviço. Tente de novo.")


def verificar_saude() -> bool:
    try:
        resposta = requests.get(f"{URL_BASE}/api/saude", timeout=5)
        resposta.raise_for_status()
        return resposta.json().get("status") == "ok"
    except requests.exceptions.RequestException:
        return False


def perguntar(pergunta: str) -> dict:
    try:
        resposta = requests.post(f"{URL_BASE}/api/perguntar", json={"pergunta": pergunta}, timeout=TEMPO_LIMITE_S)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.RequestException as exc:
        raise _tratar_erro(exc) from exc


def classificar_imagem(caminho_imagem: str | Path) -> dict:
    try:
        with open(caminho_imagem, "rb") as arquivo:
            nome = Path(caminho_imagem).name
            resposta = requests.post(
                f"{URL_BASE}/api/classificar-imagem",
                files={"arquivo": (nome, arquivo, "image/jpeg")},
                timeout=TEMPO_LIMITE_S,
            )
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.RequestException as exc:
        raise _tratar_erro(exc) from exc


def perguntar_por_voz(caminho_audio: str | Path) -> dict:
    """Envia um áudio para o back-end: ele transcreve, responde pelo RAG e

    devolve a resposta também em áudio (se a síntese de voz funcionar).
    """
    try:
        with open(caminho_audio, "rb") as arquivo:
            nome = Path(caminho_audio).name
            resposta = requests.post(
                f"{URL_BASE}/api/perguntar-por-voz",
                files={"arquivo": (nome, arquivo, "audio/wav")},
                # Transcrição + LLM + síntese de voz juntos podem demorar mais que
                # uma pergunta de texto comum.
                timeout=max(TEMPO_LIMITE_S, 90.0),
            )
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.RequestException as exc:
        raise _tratar_erro(exc) from exc
