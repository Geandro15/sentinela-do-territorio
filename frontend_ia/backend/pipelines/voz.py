# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Pipeline de voz: liga a API ao STT e ao TTS já prontos do módulo de PLN
(``assistente/stt.py`` e ``assistente/tts.py``), e reaproveita o mesmo
pipeline de RAG do chat de texto (``pipelines/rag.py``), a pergunta
transcrita passa pelo mesmo assistente, com a mesma verificação e as
mesmas regras de abstenção.
"""
from __future__ import annotations

from pathlib import Path

from ..providers.caminhos import preparar
from ..schemas.relatos import PerguntaPorVozSaida
from .rag import perguntar

preparar()

from assistente.stt import ErroSTT, apagar_audio, transcrever  # noqa: E402
from assistente.tts import ErroTTS, sintetizar  # noqa: E402


class ErroVoz(RuntimeError):
    """Erro no fluxo de voz (transcrição ou síntese); a API transforma isso em HTTP 422/503."""


def perguntar_por_voz(caminho_audio: str | Path) -> PerguntaPorVozSaida:
    try:
        texto = transcrever(caminho_audio).strip()
    except ErroSTT as exc:
        raise ErroVoz(
            "Não foi possível entender o áudio enviado. Tente gravar de novo, falando perto do microfone."
        ) from exc
    finally:
        # Retenção mínima (LGPD): o áudio do cidadão nunca fica guardado,
        # mesmo que a transcrição falhe.
        apagar_audio(caminho_audio)

    if len(texto) < 3:
        raise ErroVoz("Não entendi nada no áudio enviado. Tente falar mais perto do microfone, em um lugar mais silencioso.")

    resposta = perguntar(texto)

    audio_base64 = None
    try:
        caminho_audio_resposta = sintetizar(resposta.resposta)
        import base64

        audio_base64 = base64.b64encode(caminho_audio_resposta.read_bytes()).decode("ascii")
        caminho_audio_resposta.unlink(missing_ok=True)
    except ErroTTS:
        # A resposta em texto já é útil sozinha; a falta de áudio não deve
        # bloquear a resposta, só deixar essa parte em branco.
        pass

    return PerguntaPorVozSaida(
        pergunta_transcrita=texto,
        resposta=resposta.resposta,
        fontes=resposta.fontes,
        motivo=resposta.motivo,
        motivo_legivel=resposta.motivo_legivel,
        sustentada=resposta.sustentada,
        audio_base64=audio_base64,
    )
