# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Ingestão: transforma as fontes coletadas em seções de texto com metadados.

Cada seção guarda de onde veio (fonte, URL, data de consulta e nome da seção),
para que toda resposta do assistente possa citar a origem.

    python -m genai.ingestao      # grava genai/indice/secoes.jsonl
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent
PASTA_FONTES = RAIZ / "fontes"
ARQUIVO_SECOES = RAIZ / "indice" / "secoes.jsonl"

# Frases que tentam dar ordens ao modelo. Um documento não deve conter isso;
# se contiver, a linha é removida na ingestão (defesa contra injeção indireta).
PADROES_DE_INJECAO = re.compile(
    r"(ignore|desconsidere|esque[çc]a)\s+(todas\s+)?(as|suas|os|seus)?\s*(instru[çc][õo]es|regras|comandos)"
    r"|revele\s+(o|seu)\s+prompt|voc[êe]\s+agora\s+[ée]|system\s*prompt|aja\s+como", re.IGNORECASE)


@dataclass
class Secao:
    id: str            # exemplo: F1#pergunta-7
    fonte_id: str
    fonte: str
    url: str
    data_consulta: str
    secao: str
    titulo: str
    texto: str


def limpar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def remover_injecao(texto: str) -> tuple[str, int]:
    """Remove frases com ordens ao modelo. Devolve o texto limpo e quantas frases saíram."""
    frases = re.split(r"(?<=[.!?])\s+", texto)
    boas = [f for f in frases if not PADROES_DE_INJECAO.search(f)]
    return " ".join(boas), len(frases) - len(boas)


def _sopa(caminho: Path) -> BeautifulSoup:
    sopa = BeautifulSoup(caminho.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for etiqueta in sopa(["script", "style", "nav", "footer"]):
        etiqueta.decompose()
    return sopa


def _faq(caminho: Path) -> list[tuple[str, str, str]]:
    """Uma seção por pergunta do FAQ (estrutura original da página)."""
    secoes = []
    for bloco in _sopa(caminho).find_all("details"):
        resumo = bloco.find("summary")
        if not resumo:
            continue
        pergunta = limpar(resumo.get_text(" "))
        resumo.extract()
        resposta = limpar(bloco.get_text(" "))
        if resposta:
            secoes.append((bloco.get("id") or f"pergunta-{len(secoes) + 1}", pergunta, resposta))
    return secoes


def _por_titulos(caminho: Path) -> list[tuple[str, str, str]]:
    """Uma seção por título de primeiro nível da página."""
    sopa = _sopa(caminho)
    corpo = sopa.find("main") or sopa.body or sopa
    secoes, titulo, partes = [], "", []
    for no in corpo.find_all(["h1", "h2", "h3", "p", "li", "summary", "td", "th"]):
        texto = limpar(no.get_text(" "))
        if not texto:
            continue
        if no.name == "h1":
            if partes:
                secoes.append((titulo, " ".join(partes)))
            titulo, partes = texto, []
        else:
            partes.append(texto if texto.endswith((".", ":", "?")) else texto + ".")
    if partes:
        secoes.append((titulo, " ".join(partes)))
    return [(f"secao-{i}", t or "Apresentação", x) for i, (t, x) in enumerate(secoes, 1)]


def _bdqueimadas(caminho: Path) -> list[tuple[str, str, str]]:
    """A página do BDQueimadas é um mapa; o texto útil são os filtros, o 'Sobre' e a exportação."""
    sopa = _sopa(caminho)
    texto = limpar(sopa.get_text(" "))
    descricao = sopa.find("meta", attrs={"name": "description"})
    secoes = []
    if descricao and descricao.get("content"):
        secoes.append(("descricao", "O que é o BDQueimadas", limpar(descricao["content"])))
    marcos = [("filtros", "Filtros de consulta do BDQueimadas", "Filtros", "Mapa Inicial"),
              ("sobre", "Sobre o BDQueimadas", "Sobre o BDQueimadas", "PROJETO INPE"),
              ("exportar", "Exportação de dados do BDQueimadas", "Exportar Dados", "Legendas")]
    for chave, titulo, inicio, fim in marcos:
        a = texto.find(inicio)
        b = texto.find(fim, a + 1) if a >= 0 else -1
        if a >= 0 and b > a:
            secoes.append((chave, titulo, texto[a:b].strip()))
    return secoes


def _pdf_em_texto(caminho: Path) -> list[tuple[str, str, str]]:
    """Uma seção por página do boletim. Páginas com pouco texto (capa, sumário) são ignoradas."""
    secoes = []
    for bloco in re.split(r"=== PAGINA (\d+) ===\n", caminho.read_text(encoding="utf-8"))[1:]:
        secoes.append(bloco)
    pares = list(zip(secoes[0::2], secoes[1::2]))
    saida = []
    for numero, texto in pares:
        texto = limpar(re.sub(r"INFOQUEIMA - Boletim Técnico Mensal de Monitoramento de Focos de Fogo agosto \| 2026", "", texto))
        if len(texto) >= 300 and int(numero) > 3:
            saida.append((f"pagina-{numero}", f"InfoQueima agosto/2026, página {numero}", texto))
    return saida


LEITORES = {"faq": _faq, "pagina": _por_titulos, "pdf": _pdf_em_texto}


def ingerir() -> tuple[list[Secao], int]:
    with (PASTA_FONTES / "fontes.csv").open(encoding="utf-8", newline="") as arquivo:
        fontes = list(csv.DictReader(arquivo))
    secoes, removidas = [], 0
    for fonte in fontes:
        caminho = PASTA_FONTES / fonte["arquivo"]
        leitor = _bdqueimadas if fonte["id"] == "F2" else LEITORES[fonte["tipo"]]
        for chave, titulo, texto in leitor(caminho):
            texto, n = remover_injecao(texto)
            removidas += n
            secoes.append(Secao(id=f"{fonte['id']}#{chave}", fonte_id=fonte["id"], fonte=fonte["titulo"],
                                url=fonte["url"], data_consulta=fonte["data_consulta"], secao=chave,
                                titulo=titulo, texto=texto))
    return secoes, removidas


def gravar(secoes: list[Secao], destino: Path = ARQUIVO_SECOES) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as arquivo:
        for secao in secoes:
            arquivo.write(json.dumps(asdict(secao), ensure_ascii=False) + "\n")


def carregar(origem: Path = ARQUIVO_SECOES) -> list[Secao]:
    return [Secao(**json.loads(linha)) for linha in origem.read_text(encoding="utf-8").splitlines() if linha.strip()]


if __name__ == "__main__":
    lista, tiradas = ingerir()
    gravar(lista)
    por_fonte: dict[str, list[int]] = {}
    for s in lista:
        por_fonte.setdefault(s.fonte_id, []).append(len(s.texto))
    for fonte_id, tamanhos in por_fonte.items():
        print(f"{fonte_id}: {len(tamanhos)} seções, {sum(tamanhos)} caracteres (maior: {max(tamanhos)})")
    print(f"Total: {len(lista)} seções. Frases removidas por suspeita de injeção: {tiradas}.")
