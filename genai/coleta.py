# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Coleta das fontes oficiais do Programa Queimadas do INPE.

Baixa cada página ou boletim, guarda uma cópia em genai/fontes/ e registra
título, órgão, URL e data de consulta em genai/fontes/fontes.csv.

    python -m genai.coleta
"""
from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path

import requests

PASTA = Path(__file__).resolve().parent / "fontes"
ORGAO = "INPE - Programa Queimadas"

FONTES = [
    {"id": "F1", "titulo": "Perguntas Frequentes (FAQ) do Programa Queimadas",
     "url": "https://data.inpe.br/queimadas/faq/", "arquivo": "faq.html", "tipo": "faq"},
    {"id": "F2", "titulo": "BDQueimadas - Banco de Dados de Queimadas",
     "url": "https://data.inpe.br/queimadas/bdqueimadas/", "arquivo": "bdqueimadas.html", "tipo": "pagina"},
    {"id": "F3", "titulo": "Dados Abertos do Programa Queimadas",
     "url": "https://data.inpe.br/queimadas/dados-abertos/", "arquivo": "dados_abertos.html", "tipo": "pagina"},
    {"id": "F4", "titulo": "Boletim InfoQueima - apresentação",
     "url": "https://data.inpe.br/queimadas/boletim-infoqueima/", "arquivo": "boletim_infoqueima.html", "tipo": "pagina"},
    {"id": "F5", "titulo": "InfoQueima - boletim mensal de agosto de 2026",
     "url": "https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/2026/2026_08_infoqueima.pdf",
     "arquivo": "infoqueima_2026_08.txt", "tipo": "pdf"},
]


def _texto_do_pdf(conteudo: bytes) -> str:
    """Extrai o texto do PDF, uma página por bloco, separadas por uma linha de marcação."""
    import io

    from pypdf import PdfReader

    paginas = []
    for numero, pagina in enumerate(PdfReader(io.BytesIO(conteudo)).pages, 1):
        texto = re.sub(r"\s+", " ", pagina.extract_text() or "").strip()
        paginas.append(f"=== PAGINA {numero} ===\n{texto}")
    return "\n".join(paginas) + "\n"


def coletar() -> list[dict]:
    PASTA.mkdir(parents=True, exist_ok=True)
    hoje = dt.date.today().isoformat()
    registros = []
    for fonte in FONTES:
        resposta = requests.get(fonte["url"], timeout=120)
        resposta.raise_for_status()
        destino = PASTA / fonte["arquivo"]
        if fonte["tipo"] == "pdf":
            destino.write_text(_texto_do_pdf(resposta.content), encoding="utf-8")
        else:
            destino.write_bytes(resposta.content)
        registros.append({"id": fonte["id"], "titulo": fonte["titulo"], "orgao": ORGAO, "url": fonte["url"],
                          "data_consulta": hoje, "arquivo": fonte["arquivo"], "tipo": fonte["tipo"]})
        print(f"{fonte['id']} {fonte['arquivo']}: {destino.stat().st_size} bytes")
    with (PASTA / "fontes.csv").open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0].keys()))
        escritor.writeheader()
        escritor.writerows(registros)
    return registros


if __name__ == "__main__":
    coletar()
    print(f"Fontes registradas em {PASTA / 'fontes.csv'}")
