# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""OCR: extrai os campos de um relato de incêndio "escaneado" (imagem de um

formulário com local, data e descrição), usando Tesseract (local, grátis,
sem chave de API).
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

# Caminhos onde o instalador do Windows (UB-Mannheim) costuma colocar o
# tesseract.exe. Usados só como fallback: se o programa já estiver no PATH
# do sistema, isso nem é consultado. Isso evita depender de reiniciar o
# terminal/editor depois da instalação para o PATH do Windows "pegar", # achado real ao testar a instalação na máquina do grupo.
_CAMINHOS_WINDOWS_COMUNS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def _configurar_caminho_tesseract() -> None:
    import pytesseract

    if shutil.which("tesseract"):
        return  # já está no PATH, nada a fazer
    for caminho in _CAMINHOS_WINDOWS_COMUNS:
        if Path(caminho).is_file():
            pytesseract.pytesseract.tesseract_cmd = caminho
            return


class ErroOCR(RuntimeError):
    """Falha ao ler ou interpretar a imagem do relato."""


@dataclass
class RelatoExtraido:
    texto_bruto: str
    local: str | None
    data: str | None
    descricao: str | None

    @property
    def campos_completos(self) -> bool:
        return all([self.local, self.data, self.descricao])


_PADRAO_CAMPO = {
    "local": re.compile(r"Local\s*:\s*(.+)", re.IGNORECASE),
    "data": re.compile(r"Data\s*:\s*(.+)", re.IGNORECASE),
    "descricao": re.compile(r"Descri[cç][aã]o\s*:\s*(.+)", re.IGNORECASE),
}


def _primeira_linha(texto: str) -> str:
    texto = texto.strip()
    return texto.splitlines()[0].strip() if texto else ""


def extrair_relato(caminho_imagem: str | Path) -> RelatoExtraido:
    """Lê a imagem com OCR e separa os campos "Local:", "Data:" e

    "Descrição:". Campos não encontrados ficam como ``None``, quem chama
    decide o que fazer (ver ``regras.classificar_prioridade``, que manda o
    relato para revisão manual se a descrição estiver ausente)."""
    caminho_imagem = Path(caminho_imagem)
    if not caminho_imagem.exists():
        raise ErroOCR(f"imagem do relato não encontrada: {caminho_imagem}")

    try:
        import pytesseract
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise ErroOCR("os pacotes pytesseract/Pillow não estão instalados (pip install pytesseract Pillow)") from exc

    _configurar_caminho_tesseract()

    try:
        with Image.open(caminho_imagem) as imagem:
            texto = pytesseract.image_to_string(imagem, lang="por")
    except UnidentifiedImageError as exc:
        raise ErroOCR(f"arquivo não é uma imagem válida: {caminho_imagem.name}") from exc
    except pytesseract.TesseractNotFoundError as exc:
        raise ErroOCR(
            "o programa Tesseract OCR não está instalado nesta máquina "
            "(instale em https://github.com/UB-Mannheim/tesseract/wiki e garanta que está no PATH)"
        ) from exc
    except Exception as exc:
        raise ErroOCR(f"falha ao ler a imagem com OCR ({caminho_imagem.name}): {exc}") from exc

    campos = {}
    for nome, padrao in _PADRAO_CAMPO.items():
        correspondencia = padrao.search(texto)
        campos[nome] = _primeira_linha(correspondencia.group(1)) if correspondencia else None

    return RelatoExtraido(
        texto_bruto=texto, local=campos["local"] or None,
        data=campos["data"] or None, descricao=campos["descricao"] or None,
    )
