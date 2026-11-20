# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Assistente conversacional com RAG: junta ingestão, chunking, retriever e generator.

Proteções, na ordem em que atuam:
1. Dados pessoais da pergunta são mascarados antes de qualquer uso ou registro.
2. Tentativas de mudar as regras ou de revelar o prompt recebem uma recusa fixa.
3. Sem evidência suficiente na busca local (INPE), o assistente tenta uma busca
   na web (``busca_web.py``) antes de desistir, por exemplo, para um telefone
   de emergência que o boletim do INPE não traz. Só se a web também não trouxer
   nada é que o assistente se abstém, sem chamar o LLM.
4. A resposta do LLM é verificada: sem citação válida, ou com número que não
   está nos trechos, ela é trocada por um aviso e pelos trechos encontrados.
   Essa verificação vale igual para trechos do INPE e da busca na web.

    python -m genai.assistente_rag "O que é o satélite de referência?"
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from config import CONFIG, Config
from corpus.limpeza import mascarar_dados_pessoais

from . import gerador
from .busca_web import buscar_na_web
from .chunking import PADRAO, dividir
from .contatos_emergencia import CONTATOS_EMERGENCIA
from .ingestao import ARQUIVO_SECOES, carregar
from .retriever import Achado, Retriever

# Limiares de evidência, calibrados na avaliação (ver genai/docs/relatorio_genai.md).
# Com busca vetorial, exige-se semelhança mínima de 0,50 entre a pergunta e o melhor trecho.
# Só com BM25 (sem embeddings), exige-se nota mínima de 2,0.
BM25_MINIMO = 2.0
COSSENO_MINIMO = 0.50
TOP_K = 4
TURNOS_DE_MEMORIA = 3

ATAQUE = re.compile(
    r"(ignore|desconsidere|esque[çc]a)\b.{0,40}(instru[çc][õo]es|regras|orienta[çc][õo]es)"
    r"|(mostre|revele|exiba|repita|qual\s+[ée]|diga)\b.{0,40}(prompt|instru[çc][õo]es\s+(de\s+sistema|iniciais|internas)|system)"
    r"|voc[êe]\s+agora\s+[ée]\b|modo\s+desenvolvedor|\bDAN\b|finja\s+que\s+n[ãa]o\s+tem\s+regras",
    re.IGNORECASE | re.DOTALL)
CONTINUACAO = re.compile(
    r"^\s*(e|mas|então|entao|e\s+se|e\s+o|e\s+a|isso|isto|aquilo|ele|ela|nesse\s+caso|"
    r"nesse|nessa|desse|dessa|e\s+quanto|e\s+sobre)\b", re.IGNORECASE)

# Pergunta pedindo um contato (telefone, e-mail etc.): usadas para notar quando
# uma resposta "respondida" com a base local, mesmo tendo citação válida, não
# trouxe o dado que o cidadão realmente pediu, caso real: um trecho do FAQ
# cita "Bombeiros" de passagem, o modelo responde "procure o Corpo de
# Bombeiros [1]" sem nenhum número, isso passa pela verificação (citação
# válida, nenhum número inventado) e o assistente nunca tenta a busca na web,
# porque só tentava quando a resposta era abstenção ou era bloqueada, não
# quando era "respondida" só que inútil para quem perguntou.
PEDE_CONTATO = re.compile(r"telefone|contato|liga[çc][ãa]o|\bligar\b|disque|whats\s*app|e-?mail\b", re.IGNORECASE)
TEM_NUMERO_DE_CONTATO = re.compile(r"\b\d{3}\b|\(?\d{2}\)?[\s.-]?\d{4,5}[\s.-]?\d{4}\b")


@dataclass
class Resposta:
    pergunta: str
    resposta: str
    achados: list[Achado] = field(default_factory=list)
    motivo: str = "respondida"       # respondida | abstencao_sem_evidencia | recusa_de_seguranca | nao_sustentada | erro_llm
    sinais: dict = field(default_factory=dict)
    verificacao: dict = field(default_factory=dict)
    fonte_evidencia: str = "local"    # local (INPE) | web (busca_web.py, usada quando o INPE não cobre o assunto)

    def fontes(self) -> list[str]:
        vistas, linhas = set(), []
        for numero, a in enumerate(self.achados, 1):
            chave = (a.trecho.url, a.trecho.titulo)
            if chave not in vistas:
                vistas.add(chave)
                linhas.append(f"[{numero}] {a.trecho.fonte}, {a.trecho.titulo} ({a.trecho.url}, consulta em {a.trecho.data_consulta})")
        return linhas


class AssistenteRAG:
    def __init__(self, cfg: Config = CONFIG, chunking: str = PADRAO, retriever: str = "hibrido",
                 secoes_em: Path = ARQUIVO_SECOES, registrar: bool = True):
        self.cfg, self.registrar = cfg, registrar
        # Contatos de emergência (193, 199 etc.) entram como fonte local fixa,
        # junto dos trechos do INPE, não dependem de internet nem da busca na
        # web, porque são números oficiais que não mudam (ver contatos_emergencia.py).
        self.trechos = dividir(carregar(secoes_em), chunking) + CONTATOS_EMERGENCIA
        self.retriever = Retriever(self.trechos, retriever)
        self.historico: list[dict] = []
        self.ultima_pergunta = ""

    def nova_conversa(self) -> None:
        self.historico, self.ultima_pergunta = [], ""

    def tem_evidencia(self, sinais: dict) -> bool:
        if "cosseno_max" in sinais:
            return sinais["cosseno_max"] >= COSSENO_MINIMO
        return sinais.get("bm25_max", 0.0) >= BM25_MINIMO

    # Motivos em que vale a pena tentar a busca na web como segunda fonte:
    # sem evidência local nenhuma, o modelo achou que a base local também não
    # respondia, ou a resposta gerada com a base local não se sustentou (por
    # exemplo, um trecho que só cita "Bombeiros" de passagem, sem o telefone).
    _MOTIVOS_QUE_TENTAM_A_WEB = ("abstencao_sem_evidencia", "abstencao_do_modelo", "nao_sustentada")

    def responder(self, pergunta: str) -> Resposta:
        pergunta = mascarar_dados_pessoais(pergunta.strip())
        if ATAQUE.search(pergunta):
            return self._fechar(Resposta(pergunta, gerador.RECUSA_DE_SEGURANCA, motivo="recusa_de_seguranca"))

        # Pergunta de continuação ("e isso é pago?", "e sobre a defesa civil?"): a
        # busca usa também a pergunta anterior. Só entra aqui com uma marca
        # explícita de continuação (CONTINUACAO), uma pergunta curta sozinha
        # (ex.: "telefone dos bombeiros") NÃO é tratada como continuação: um
        # bug real misturava qualquer pergunta de até 5 palavras com a
        # pergunta anterior, mesmo sem relação nenhuma entre as duas. Como o
        # assistente é uma única instância compartilhada por todas as telas
        # (menu, chat flutuante, voz, ver `_ASSISTENTE` em `aba.py` e no
        # back-end do front-end), isso fazia exatamente perguntas curtas e
        # diretas, como telefones de emergência, saírem erradas ou abstidas
        # dependendo do que tinha sido perguntado antes, em qualquer tela.
        consulta = pergunta
        if self.ultima_pergunta and CONTINUACAO.match(pergunta):
            consulta = f"{self.ultima_pergunta} {pergunta}"

        sinais = self.retriever.confianca(consulta)
        achados = self.retriever.buscar(consulta, TOP_K)
        if achados and self.tem_evidencia(sinais):
            resposta = self._gerar_e_verificar(pergunta, achados, sinais, "local")
        else:
            resposta = Resposta(pergunta, gerador.ABSTENCAO, achados=[], motivo="abstencao_sem_evidencia",
                                sinais=sinais, fonte_evidencia="local")

        # A base local do INPE não respondeu bem à pergunta (sem evidência, sem
        # resposta sustentada, ou o próprio modelo disse que não sabia). Antes
        # de devolver isso ao cidadão, tenta uma segunda fonte: a busca na web
        #, por exemplo, para um telefone de emergência que o INPE não traz.
        if self.cfg.busca_web_ativa and resposta.motivo in self._MOTIVOS_QUE_TENTAM_A_WEB:
            achados_web = self._buscar_web(consulta)
            if achados_web:
                resposta = self._gerar_e_verificar(pergunta, achados_web, {**sinais, "busca_web": True}, "web")

        # A pergunta pedia um contato (telefone etc.) e a resposta local foi
        # aceita pela verificação, mas não trouxe nenhum número, ela cita a
        # fonte certa, só que não responde de fato o que o cidadão quer saber.
        # Tenta a web mesmo assim; só troca a resposta se a tentativa na web
        # também for aceita E trouxer um número, senão mantém a resposta local
        # (ainda útil, só sem o número).
        elif (self.cfg.busca_web_ativa and resposta.motivo == "respondida" and resposta.fonte_evidencia == "local"
              and PEDE_CONTATO.search(pergunta) and not TEM_NUMERO_DE_CONTATO.search(resposta.resposta)):
            achados_web = self._buscar_web(consulta)
            if achados_web:
                tentativa_web = self._gerar_e_verificar(pergunta, achados_web, {**sinais, "busca_web": True}, "web")
                if tentativa_web.motivo == "respondida" and TEM_NUMERO_DE_CONTATO.search(tentativa_web.resposta):
                    resposta = tentativa_web

        if resposta.motivo == "respondida":
            self.historico += [{"role": "user", "content": pergunta}, {"role": "assistant", "content": resposta.resposta}]
        self.ultima_pergunta = pergunta
        return self._fechar(resposta)

    def _gerar_e_verificar(self, pergunta: str, achados: list[Achado], sinais: dict, fonte_evidencia: str) -> Resposta:
        """Chama o LLM com os ``achados`` dados (do INPE ou da web) e confere a resposta.

        Mesma verificação nos dois casos: precisa citar um trecho válido e não
        pode trazer número que não esteja nos trechos (``gerador.verificar``).
        """
        try:
            texto = gerador.gerar(pergunta, achados, self.historico[-2 * TURNOS_DE_MEMORIA:], self.cfg)
        except Exception as exc:  # LLM fora do ar: devolve os trechos, sem inventar resposta
            return Resposta(pergunta, f"O modelo de linguagem não respondeu ({exc}). Veja os trechos encontrados.",
                            achados=achados, motivo="erro_llm", sinais=sinais, fonte_evidencia=fonte_evidencia)
        verificacao = gerador.verificar(texto, achados)
        if verificacao["abstencao"]:
            return Resposta(pergunta, gerador.ABSTENCAO, achados=achados, motivo="abstencao_do_modelo", sinais=sinais,
                            verificacao=verificacao, fonte_evidencia=fonte_evidencia)
        if not verificacao["sustentada"]:
            return Resposta(pergunta, gerador.NAO_SUSTENTADA, achados=achados, motivo="nao_sustentada", sinais=sinais,
                            verificacao={**verificacao, "resposta_bloqueada": texto}, fonte_evidencia=fonte_evidencia)
        return Resposta(pergunta, texto, achados=achados, sinais=sinais, verificacao=verificacao,
                        fonte_evidencia=fonte_evidencia)

    def _buscar_web(self, consulta: str) -> list[Achado]:
        trechos = buscar_na_web(consulta, self.cfg.busca_web_max_resultados)
        return [Achado(trecho=t, pontuacao=0.0, posicao=i) for i, t in enumerate(trechos, 1)]

    def _fechar(self, resposta: Resposta) -> Resposta:
        if self.registrar:
            pasta = Path(self.cfg.pasta_logs)
            pasta.mkdir(parents=True, exist_ok=True)
            registro = {"data_hora": dt.datetime.now().isoformat(timespec="seconds"), "pergunta": resposta.pergunta,
                        "motivo": resposta.motivo, "fonte_evidencia": resposta.fonte_evidencia,
                        "trechos": [a.trecho.id for a in resposta.achados],
                        "sinais": {k: (round(v, 3) if isinstance(v, (int, float)) else v) for k, v in resposta.sinais.items()},
                        "resposta": resposta.resposta}
            with (pasta / "genai_interacoes.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
        return resposta


if __name__ == "__main__":
    import sys

    assistente = AssistenteRAG()
    saida = assistente.responder(" ".join(sys.argv[1:]) or "O que é o satélite de referência?")
    print(saida.resposta, "\n")
    print("\n".join(saida.fontes()))
    print(f"\n({saida.motivo}; sinais: {saida.sinais})")
