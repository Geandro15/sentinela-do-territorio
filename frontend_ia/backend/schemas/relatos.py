# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Modelos Pydantic de entrada e saída da API.

A saída nunca é texto livre do LLM: é sempre um destes modelos, com campos
fixos que o front-end sabe exibir (resposta, fontes, alerta, confiança).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PerguntaEntrada(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500, description="Dúvida do cidadão sobre queimadas, em português.")


class PerguntaSaida(BaseModel):
    resposta: str
    fontes: list[str] = Field(default_factory=list)
    motivo: str  # respondida | abstencao_sem_evidencia | abstencao_do_modelo | nao_sustentada | recusa_de_seguranca | erro_llm
    motivo_legivel: str
    sustentada: bool


class PerguntaPorVozSaida(BaseModel):
    pergunta_transcrita: str
    resposta: str
    fontes: list[str] = Field(default_factory=list)
    motivo: str
    motivo_legivel: str
    sustentada: bool
    audio_base64: str | None = None  # resposta falada (mp3), se a síntese de voz funcionou


class ImagemSaida(BaseModel):
    classe: str
    confianca: float = Field(ge=0.0, le=1.0)
    alerta: bool
    aviso: str


class ErroSaida(BaseModel):
    detalhe: str
