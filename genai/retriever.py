# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Retriever: busca lexical (BM25), vetorial (embeddings) e híbrida.

- ``bm25``: compara palavras. Não precisa de modelo e é fácil de auditar.
- ``vetorial``: compara significado, com embeddings multilíngues (fastembed, roda em CPU).
- ``hibrido``: junta as duas listas por Reciprocal Rank Fusion (RRF).
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .chunking import Trecho

TIPOS = ("bm25", "vetorial", "hibrido")
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
PASTA_INDICE = Path(__file__).resolve().parent / "indice"

PALAVRAS_VAZIAS = set("""a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob sobre e ou que
se ao aos à às é são foi ser como qual quais quando onde quem quanto quantos mais menos muito pelo pela pelos pelas
este esta esse essa isso isto eu me meu minha você seu sua nosso nossa tem há ter já não sim também entre até""".split())


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


_VAZIAS = {_sem_acento(p) for p in PALAVRAS_VAZIAS}
try:  # radicalização (stemming) opcional. Na avaliação ela piorou a busca e por isso fica desligada.
    from py_rust_stemmers import SnowballStemmer

    _RADICAL = SnowballStemmer("portuguese").stem_word
except Exception:  # sem a biblioteca, a busca funciona com as palavras inteiras
    _RADICAL = None


def tokenizar(texto: str, radicalizar: bool = False) -> list[str]:
    palavras = [p for p in re.findall(r"[a-zà-ú0-9]+", texto.lower()) if _sem_acento(p) not in _VAZIAS and len(p) > 1]
    if radicalizar and _RADICAL:
        palavras = [_RADICAL(p) for p in palavras]
    return [_sem_acento(p) for p in palavras]


@dataclass
class Achado:
    trecho: Trecho
    pontuacao: float
    posicao: int


class BM25:
    def __init__(self, trechos: list[Trecho], k1: float = 1.5, b: float = 0.75, radicalizar: bool = False):
        self.trechos, self.k1, self.b, self.radicalizar = trechos, k1, b, radicalizar
        self.documentos = [Counter(tokenizar(t.texto, radicalizar)) for t in trechos]
        self.tamanhos = [sum(d.values()) for d in self.documentos]
        self.media = sum(self.tamanhos) / max(len(self.tamanhos), 1)
        frequencia = Counter(termo for d in self.documentos for termo in d)
        n = len(trechos)
        self.idf = {termo: math.log(1 + (n - f + 0.5) / (f + 0.5)) for termo, f in frequencia.items()}

    def pontuar(self, consulta: str) -> list[float]:
        termos = tokenizar(consulta, self.radicalizar)
        notas = []
        for documento, tamanho in zip(self.documentos, self.tamanhos):
            nota = 0.0
            for termo in termos:
                f = documento.get(termo, 0)
                if f:
                    nota += self.idf[termo] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * tamanho / self.media))
            notas.append(nota)
        return notas


class Vetorial:
    def __init__(self, trechos: list[Trecho], modelo: str = MODELO_EMBEDDINGS):
        import numpy as np
        from fastembed import TextEmbedding

        self._np = np
        self.modelo = TextEmbedding(model_name=modelo)
        # Os vetores dos trechos ficam guardados em disco; só são recalculados se a base ou o modelo mudarem.
        textos = [t.texto for t in trechos]
        marca = hashlib.sha256((modelo + "\x00" + "\x00".join(textos)).encode("utf-8")).hexdigest()[:16]
        arquivo = PASTA_INDICE / f"embeddings_{marca}.npy"
        if arquivo.exists():
            self.matriz = np.load(arquivo)
        else:
            self.matriz = self._normalizar(np.array(list(self.modelo.embed(textos))))
            PASTA_INDICE.mkdir(parents=True, exist_ok=True)
            np.save(arquivo, self.matriz)

    def _normalizar(self, matriz):
        return matriz / self._np.linalg.norm(matriz, axis=1, keepdims=True)

    def pontuar(self, consulta: str) -> list[float]:
        vetor = self._normalizar(self._np.array(list(self.modelo.embed([consulta]))))[0]
        return (self.matriz @ vetor).tolist()


def _ordenar(notas: list[float]) -> list[int]:
    return sorted(range(len(notas)), key=lambda i: notas[i], reverse=True)


class Retriever:
    """Busca os trechos mais relevantes para uma consulta."""

    def __init__(self, trechos: list[Trecho], tipo: str = "hibrido", radicalizar: bool = False):
        if tipo not in TIPOS:
            raise ValueError(f"Tipo de retriever desconhecido: {tipo}. Use {', '.join(TIPOS)}.")
        self.trechos, self.tipo = trechos, tipo
        self.bm25 = BM25(trechos, radicalizar=radicalizar) if tipo in ("bm25", "hibrido") else None
        self.vetorial = Vetorial(trechos) if tipo in ("vetorial", "hibrido") else None

    def buscar(self, consulta: str, k: int = 4) -> list[Achado]:
        """Devolve até k trechos. A pontuação depende do tipo:
        bm25 = nota BM25; vetorial = cosseno (0 a 1); hibrido = soma RRF.
        No híbrido, ``Achado`` não basta para decidir abstenção: use ``confianca``."""
        if not self.trechos or not consulta.strip():
            return []
        if self.tipo == "bm25":
            notas = self.bm25.pontuar(consulta)
        elif self.tipo == "vetorial":
            notas = self.vetorial.pontuar(consulta)
        else:
            notas = [0.0] * len(self.trechos)
            for lista in (self.bm25.pontuar(consulta), self.vetorial.pontuar(consulta)):
                for posicao, indice in enumerate(_ordenar(lista)[:50]):
                    notas[indice] += 1.0 / (60 + posicao + 1)
        ordem = _ordenar(notas)[:k]
        return [Achado(self.trechos[i], notas[i], p) for p, i in enumerate(ordem, 1) if notas[i] > 0]

    def confianca(self, consulta: str) -> dict:
        """Sinais usados para decidir se há evidência suficiente para responder."""
        sinais = {}
        if self.bm25:
            sinais["bm25_max"] = max(self.bm25.pontuar(consulta), default=0.0)
        if self.vetorial:
            sinais["cosseno_max"] = max(self.vetorial.pontuar(consulta), default=0.0)
        return sinais
