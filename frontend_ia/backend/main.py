# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Back-end FastAPI do POC CitizenTech (disciplina Front-end em Sistemas de IA).

Roda separado do front-end Gradio. O front-end chama estes endpoints por
HTTP; ele nunca chama o LLM ou o modelo de visão diretamente.

Para rodar localmente (de dentro de frontend_ia/):

    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CONFIG
from .routers.relatos import router as router_relatos

app = FastAPI(
    title="Sentinela do Território, API CitizenTech",
    description="Back-end do POC de Front-end em Sistemas de IA: recebe a pergunta ou a imagem do "
                 "cidadão, chama o modelo de IA e devolve uma resposta estruturada.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.origens_permitidas,  # nunca "*" em produção
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router_relatos)


@app.get("/api/saude")
def saude() -> dict:
    """Checagem simples de disponibilidade, usada pelo front-end antes de habilitar as telas."""
    return {"status": "ok"}
