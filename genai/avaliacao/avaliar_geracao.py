# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Avaliação do generator e do sistema completo (precisa do LLM ligado).

Modo ``controlado`` (só o generator): o contexto é entregue pronto, sem busca.
  - perguntas respondíveis recebem os trechos da seção esperada;
  - perguntas sem resposta recebem trechos que não respondem, para testar a abstenção.
Modo ``completo`` (ponta a ponta): pergunta -> busca -> geração -> verificação,
  com todas as perguntas do arquivo e duas conversas de três turnos.

Passo 1, gerar:      python -m genai.avaliacao.avaliar_geracao --modo controlado
                     python -m genai.avaliacao.avaliar_geracao --modo completo
Passo 2, julgar:     preencher a coluna "julgamento" de cada CSV com
                     correta | parcial | incorreta | abstencao_adequada | abstencao_indevida | recusa_adequada
Passo 3, resumir:    python -m genai.avaliacao.avaliar_geracao --resumir genai/avaliacao/resultados/e2e.csv
"""
from __future__ import annotations

import argparse
import csv
import time
from collections import Counter
from pathlib import Path

from genai import gerador
from genai.assistente_rag import TOP_K, AssistenteRAG
from genai.avaliacao.avaliar_recuperacao import SAIDA, ler_perguntas
from genai.retriever import Achado

JULGAMENTOS = {"correta", "parcial", "incorreta", "abstencao_adequada", "abstencao_indevida", "recusa_adequada"}
CONVERSAS = [
    ["O que é o satélite de referência?", "E qual é ele hoje?", "Por que não usam os geoestacionários?"],
    ["Quantos focos o Brasil teve em agosto de 2026?", "E qual bioma teve mais?", "E isso foi acima ou abaixo da média?"],
]


def _gravar(nome: str, linhas: list[dict]) -> Path:
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / nome
    with destino.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)
    return destino


def _contexto(achados: list[Achado]) -> str:
    return " || ".join(f"[{i}] {a.trecho.id}: {a.trecho.texto[:300]}" for i, a in enumerate(achados, 1))


def controlado() -> Path:
    assistente = AssistenteRAG(registrar=False)
    linhas = []
    for p in [q for q in ler_perguntas() if q["tipo"] in ("respondivel", "sem_resposta")]:
        if p["evidencia"].strip():
            esperadas = set(p["evidencia"].split("|"))
            trechos = [t for t in assistente.trechos if t.secao_id in esperadas][:TOP_K]
            achados = [Achado(t, 1.0, i) for i, t in enumerate(trechos, 1)]
        else:
            achados = assistente.retriever.buscar(p["pergunta"], TOP_K)
        inicio = time.perf_counter()
        try:
            texto, erro = gerador.gerar(p["pergunta"], achados), ""
        except Exception as exc:
            texto, erro = "", str(exc)
        v = gerador.verificar(texto, achados) if texto else {}
        linhas.append({"id": p["id"], "tipo": p["tipo"], "pergunta": p["pergunta"], "resposta_esperada": p["resposta_esperada"],
                       "contexto_fornecido": _contexto(achados), "resposta": texto, "abstencao": v.get("abstencao", ""),
                       "citacoes": v.get("citacoes", ""), "numeros_fora_do_contexto": v.get("numeros_fora_do_contexto", ""),
                       "sustentada": v.get("sustentada", ""), "tempo_s": round(time.perf_counter() - inicio, 2),
                       "erro": erro, "julgamento": ""})
        print(f"{p['id']} [{p['tipo']}] sustentada={v.get('sustentada')} -> {texto[:100]}")
    return _gravar("generator_controlado.csv", linhas)


def completo() -> Path:
    assistente = AssistenteRAG(registrar=False)
    linhas = []

    def rodar(identificador: str, tipo: str, pergunta: str, esperada: str, evidencia: str) -> None:
        inicio = time.perf_counter()
        r = assistente.responder(pergunta)
        esperadas = set(evidencia.split("|")) if evidencia.strip() else set()
        linhas.append({"id": identificador, "tipo": tipo, "pergunta": r.pergunta, "resposta_esperada": esperada,
                       "contexto_recuperado": _contexto(r.achados),
                       "evidencia_recuperada": bool(esperadas & {a.trecho.secao_id for a in r.achados}) if esperadas else "",
                       "resposta": r.resposta, "motivo": r.motivo,
                       "bm25_max": round(r.sinais.get("bm25_max", 0), 2), "cosseno_max": round(r.sinais.get("cosseno_max", 0), 3),
                       "resposta_bloqueada": r.verificacao.get("resposta_bloqueada", ""),
                       "tempo_s": round(time.perf_counter() - inicio, 2), "julgamento": ""})
        print(f"{identificador} [{tipo}] {r.motivo} -> {r.resposta[:100]}")

    for p in ler_perguntas():
        assistente.nova_conversa()
        rodar(p["id"], p["tipo"], p["pergunta"], p["resposta_esperada"], p["evidencia"])
    for numero, turnos in enumerate(CONVERSAS, 1):
        assistente.nova_conversa()
        for turno, pergunta in enumerate(turnos, 1):
            rodar(f"C{numero}.{turno}", "conversa", pergunta, "Coerente com o turno anterior e com as fontes.", "")
    return _gravar("e2e.csv", linhas)


def resumir(caminho: Path) -> int:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    pendentes = [l["id"] for l in linhas if l["julgamento"].strip().lower() not in JULGAMENTOS]
    if pendentes:
        print(f"Faltam julgamentos válidos em: {', '.join(pendentes)}\nValores aceitos: {', '.join(sorted(JULGAMENTOS))}")
        return 1
    md = [f"# Resultado ({caminho.stem})", "", "| Tipo de pergunta | Total | " + " | ".join(sorted(JULGAMENTOS)) + " |",
          "| --- | --- | " + " | ".join("---" for _ in JULGAMENTOS) + " |"]
    for tipo in dict.fromkeys(l["tipo"] for l in linhas):
        grupo = [l for l in linhas if l["tipo"] == tipo]
        conta = Counter(l["julgamento"].strip().lower() for l in grupo)
        md.append(f"| {tipo} | {len(grupo)} | " + " | ".join(str(conta.get(j, 0)) for j in sorted(JULGAMENTOS)) + " |")
    if "motivo" in linhas[0]:
        nao = sum(l["julgamento"].strip().lower() == "incorreta" for l in linhas)
        md += ["", f"- Respostas não sustentadas que chegaram ao usuário (julgadas incorretas): {nao} de {len(linhas)}",
               f"- Respostas bloqueadas pela verificação: {sum(l['motivo'] == 'nao_sustentada' for l in linhas)}",
               f"- Abstenções sem chamar o LLM: {sum(l['motivo'] == 'abstencao_sem_evidencia' for l in linhas)}",
               f"- Recusas de segurança: {sum(l['motivo'] == 'recusa_de_seguranca' for l in linhas)}"]
    tempo = sum(float(l.get("tempo_s") or 0) for l in linhas) / len(linhas)
    md += ["", f"- Tempo médio por resposta: {tempo:.2f} s"]
    destino = caminho.with_name(caminho.stem + "_resumo.md")
    destino.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md), f"\n\nResumo gravado em {destino}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Avalia o generator e o sistema completo.")
    parser.add_argument("--modo", choices=["controlado", "completo"], default="completo")
    parser.add_argument("--resumir", help="CSV já julgado")
    args = parser.parse_args(argv)
    if args.resumir:
        return resumir(Path(args.resumir))
    destino = controlado() if args.modo == "controlado" else completo()
    print(f"\nRespostas gravadas em {destino}. Preencha a coluna 'julgamento' e rode com --resumir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
