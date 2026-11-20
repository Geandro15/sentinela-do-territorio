# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Avaliação do chunking e do retriever, sem LLM.

Para cada combinação de chunking e retriever, mede nas perguntas respondíveis:
- acerto@1 e acerto@4: a seção esperada aparece no 1º trecho / entre os 4 primeiros;
- MRR: média de 1/posição do primeiro trecho correto.
Inclui uma variante do BM25 com radicalização (stemming), para comparação.
Também registra os sinais de confiança de todas as perguntas, usados para
escolher os limiares de abstenção.

    python -m genai.avaliacao.avaliar_recuperacao
"""
from __future__ import annotations

import csv
from pathlib import Path

from genai.chunking import CONFIGURACOES, dividir
from genai.ingestao import carregar
from genai.retriever import TIPOS, Retriever

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "resultados"
K = 4


def ler_perguntas() -> list[dict]:
    with (AQUI / "perguntas.csv").open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def main() -> int:
    SAIDA.mkdir(exist_ok=True)
    perguntas = ler_perguntas()
    com_evidencia = [p for p in perguntas if p["evidencia"].strip()]
    secoes = carregar()
    resumo, detalhe, sinais = [], [], []
    for chunking in CONFIGURACOES:
        trechos = dividir(secoes, chunking)
        media = sum(len(t.texto) for t in trechos) / len(trechos)
        variantes = [(tipo, False) for tipo in TIPOS] + ([("bm25", True)] if chunking == "estrutura" else [])
        for tipo, radicalizar in variantes:
            retriever = Retriever(trechos, tipo, radicalizar=radicalizar)
            nome = tipo + (" com radicalização" if radicalizar else "")
            a1 = a4 = mrr = 0.0
            for p in com_evidencia:
                esperadas = set(p["evidencia"].split("|"))
                achados = retriever.buscar(p["pergunta"], K)
                posicao = next((a.posicao for a in achados if a.trecho.secao_id in esperadas), 0)
                a1 += posicao == 1
                a4 += posicao >= 1
                mrr += 1 / posicao if posicao else 0
                detalhe.append({"chunking": chunking, "retriever": nome, "id": p["id"], "pergunta": p["pergunta"],
                                "evidencia_esperada": p["evidencia"], "posicao_do_acerto": posicao,
                                "recuperados": " ; ".join(a.trecho.id for a in achados)})
            n = len(com_evidencia)
            resumo.append({"chunking": chunking, "retriever": nome, "trechos": len(trechos), "tamanho_medio": round(media),
                           "acerto@1": round(a1 / n, 3), f"acerto@{K}": round(a4 / n, 3), "mrr": round(mrr / n, 3)})
            print(resumo[-1])
            if chunking == "estrutura" and tipo == "hibrido" and not radicalizar:
                for p in perguntas:
                    s = retriever.confianca(p["pergunta"])
                    sinais.append({"id": p["id"], "tipo": p["tipo"], "pergunta": p["pergunta"],
                                   "bm25_max": round(s["bm25_max"], 2), "cosseno_max": round(s["cosseno_max"], 3)})

    for nome, linhas in (("recuperacao_resumo.csv", resumo), ("recuperacao_detalhe.csv", detalhe), ("sinais_de_confianca.csv", sinais)):
        with (SAIDA / nome).open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
            escritor.writeheader()
            escritor.writerows(linhas)
    print(f"\nPerguntas com evidência esperada: {len(com_evidencia)}. Resultados em {SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
