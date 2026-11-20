# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Endpoints do fluxo CitizenTech: pergunta de texto e verificação por imagem.

Nenhum destes endpoints chama o LLM ou o modelo diretamente a partir do
front-end, toda a chamada de IA acontece aqui, no back-end, e a saída é
sempre um modelo Pydantic (nunca texto livre encaminhado sem estrutura).
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..pipelines.imagem import ErroImagem, classificar
from ..pipelines.rag import perguntar
from ..pipelines.voz import ErroVoz, perguntar_por_voz
from ..schemas.relatos import ImagemSaida, PerguntaEntrada, PerguntaPorVozSaida, PerguntaSaida

log = logging.getLogger("backend.routers.relatos")
router = APIRouter(prefix="/api", tags=["relatos"])

EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png"}
EXTENSOES_AUDIO_PERMITIDAS = {".wav", ".mp3", ".ogg", ".webm", ".m4a"}
TAMANHO_MAXIMO_BYTES = 8 * 1024 * 1024  # 8 MB
TAMANHO_MAXIMO_AUDIO_BYTES = 15 * 1024 * 1024  # 15 MB (áudio de voz, pode durar alguns minutos)


@router.post("/perguntar", response_model=PerguntaSaida)
def rota_perguntar(entrada: PerguntaEntrada) -> PerguntaSaida:
    try:
        return perguntar(entrada.pergunta)
    except Exception as exc:  # modelo fora do ar, índice ausente etc., nunca expõe o traceback ao cidadão
        log.exception("Falha ao responder pergunta")
        raise HTTPException(status_code=503, detail="O assistente não conseguiu responder agora. Tente de novo em instantes.") from exc


@router.post("/perguntar-por-voz", response_model=PerguntaPorVozSaida)
def rota_perguntar_por_voz(arquivo: UploadFile = File(...)) -> PerguntaPorVozSaida:
    sufixo = Path(arquivo.filename or "").suffix.lower()
    if sufixo not in EXTENSOES_AUDIO_PERMITIDAS:
        raise HTTPException(status_code=422, detail="Envie um áudio .wav, .mp3, .ogg, .webm ou .m4a.")

    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as temporario:
        caminho_temporario = Path(temporario.name)
        tamanho = 0
        while bloco := arquivo.file.read(1024 * 1024):
            tamanho += len(bloco)
            if tamanho > TAMANHO_MAXIMO_AUDIO_BYTES:
                caminho_temporario.unlink(missing_ok=True)
                raise HTTPException(status_code=422, detail="Áudio maior que 15 MB.")
            temporario.write(bloco)

    try:
        return perguntar_por_voz(caminho_temporario)
    except ErroVoz as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # modelo de STT/TTS fora do ar etc., nunca expõe o traceback ao cidadão
        log.exception("Falha no fluxo de pergunta por voz")
        raise HTTPException(status_code=503, detail="Não foi possível processar o áudio agora. Tente de novo em instantes.") from exc
    finally:
        caminho_temporario.unlink(missing_ok=True)


@router.post("/classificar-imagem", response_model=ImagemSaida)
def rota_classificar_imagem(arquivo: UploadFile = File(...)) -> ImagemSaida:
    sufixo = Path(arquivo.filename or "").suffix.lower()
    if sufixo not in EXTENSOES_PERMITIDAS:
        raise HTTPException(status_code=422, detail="Envie uma imagem .jpg ou .png.")

    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as temporario:
        caminho_temporario = Path(temporario.name)
        tamanho = 0
        while bloco := arquivo.file.read(1024 * 1024):
            tamanho += len(bloco)
            if tamanho > TAMANHO_MAXIMO_BYTES:
                caminho_temporario.unlink(missing_ok=True)
                raise HTTPException(status_code=422, detail="Imagem maior que 8 MB.")
            temporario.write(bloco)

    try:
        return classificar(caminho_temporario)
    except ErroImagem as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Falha ao classificar imagem")
        raise HTTPException(status_code=503, detail="Não foi possível analisar a imagem agora.") from exc
    finally:
        caminho_temporario.unlink(missing_ok=True)
