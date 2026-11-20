# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Gera relatos sintéticos de teste (formulários "escaneados" desenhados

com PIL, nenhum dado real de cidadão), para validar o robô de ponta a
ponta sem depender de relatos verdadeiros.

Inclui de propósito um caso de campo ausente (testa a prioridade
"REVISAR") e um caso de imagem corrompida (testa o tratamento de falha).

    python -m rpa.gerar_dados_teste
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PASTA = Path(__file__).resolve().parent / "entrada"

# (nome do arquivo, linhas do formulário, imagem de satélite: "alerta" | "normal" | "corrompida" | None)
RELATOS = [
    ("relato_001", [
        "Local: Zona rural, Município X", "Data: 15/11/2026",
        "Descricao: Vi fumaca e fogo na mata atras da fazenda.",
    ], "alerta"),
    ("relato_002", [
        "Local: Bairro Y, area urbana", "Data: 16/11/2026",
        "Descricao: Vizinho queimando lixo no quintal, fumaca pequena.",
    ], "normal"),
    ("relato_003", [
        "Local: Estrada rural km 12", "Data: 16/11/2026",
        "Descricao: Area de pastagem com sinais de queimada recente, sem fogo ativo.",
    ], None),
    ("relato_004_campo_faltando", [
        "Local: Sitio Z", "Data: 17/11/2026",
    ], None),  # sem "Descricao:" de propósito, deve virar prioridade REVISAR
    ("relato_005_imagem_corrompida", [
        "Local: Fazenda W", "Data: 17/11/2026",
        "Descricao: Fumaca densa visivel a distancia, possivel incendio.",
    ], "corrompida"),
]


_FONTE_TITULO = ImageFont.load_default(size=20)
_FONTE_CAMPO = ImageFont.load_default(size=28)


def _desenhar_formulario(linhas: list[str]) -> Image.Image:
    # Fonte maior e mais nítida (load_default com tamanho, em vez da fonte
    # bitmap padrão), o OCR lê com muito mais confiabilidade assim; achado
    # real ao testar o robô de ponta a ponta.
    imagem = Image.new("RGB", (1500, 300), color="white")
    desenho = ImageDraw.Draw(imagem)
    desenho.text((20, 20), "RELATO DE OCORRENCIA - SENTINELA DO TERRITORIO (dado sintetico de teste)",
                 fill="black", font=_FONTE_TITULO)
    for indice, linha in enumerate(linhas):
        desenho.text((20, 60 + indice * 50), linha, fill="black", font=_FONTE_CAMPO)
    return imagem


def _gerar_imagem_satelite_sintetica(tipo: str) -> Image.Image:
    """Imagem sintética simples (não é uma foto de satélite real) só para

    exercitar o caminho de código da classificação de imagem, a cor não
    tem relação com o resultado real do modelo treinado."""
    cor = {"alerta": (180, 70, 30), "normal": (60, 120, 60)}[tipo]
    return Image.new("RGB", (224, 224), color=cor)


def gerar() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    for nome, linhas, tipo_satelite in RELATOS:
        caminho = PASTA / f"{nome}.png"
        _desenhar_formulario(linhas).save(caminho)
        print(f"Gerado: {caminho.name}")

        if tipo_satelite == "corrompida":
            destino = PASTA / f"{nome}_satelite.jpg"
            destino.write_bytes(b"isto-nao-e-uma-imagem-de-verdade--arquivo-corrompido-de-proposito")
            print(f"Gerado (corrompido, de propósito, para testar o tratamento de falha): {destino.name}")
        elif tipo_satelite in ("alerta", "normal"):
            destino = PASTA / f"{nome}_satelite.jpg"
            _gerar_imagem_satelite_sintetica(tipo_satelite).save(destino)
            print(f"Gerado (sintético): {destino.name}")

    print(f"\n{len(RELATOS)} relato(s) de teste gerado(s) em {PASTA}")


if __name__ == "__main__":
    gerar()
