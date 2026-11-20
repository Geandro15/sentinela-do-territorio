# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Robô de triagem automática de relatos de queimadas (disciplina de RPA).

Processa cada relato em ``rpa/entrada/``: lê o formulário "escaneado" por
OCR, classifica a imagem de satélite associada (se houver, reaproveitando
o modelo já treinado na Visão Computacional), busca o contexto do boletim
mais recente do INPE (web scraping) e grava o resultado numa planilha de
fila de atendimento do gestor, com notificação automática para os casos
de prioridade alta.

Ponto de entrada único, executado a partir da raiz do projeto:

    python -m rpa.robo_triagem
"""
from __future__ import annotations

import datetime as dt
import logging
import shutil
import uuid
from pathlib import Path

from .caminho_projeto import preparar
from .notificacao import notificar_gestor
from .ocr import ErroOCR, extrair_relato
from .planilha import registrar_relato
from .regras import classificar_prioridade
from .scraping import SituacaoINPE, buscar_situacao_atual

preparar()

RAIZ = Path(__file__).resolve().parent
PASTA_ENTRADA = RAIZ / "entrada"
PASTA_PROCESSADOS = PASTA_ENTRADA / "processados"
PASTA_SAIDA = RAIZ / "saida"
PLANILHA_SAIDA = PASTA_SAIDA / "fila_atendimento.xlsx"
PASTA_NOTIFICACOES = PASTA_SAIDA / "notificacoes"
PASTA_LOGS = RAIZ / "logs"
EXTENSOES_RELATO = {".png", ".jpg", ".jpeg"}
SUFIXO_SATELITE = "_satelite"

log = logging.getLogger("rpa.robo_triagem")


def _configurar_log() -> None:
    PASTA_LOGS.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(PASTA_LOGS / "robo.log", encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )


def _relatos_a_processar(pasta_entrada: Path) -> list[Path]:
    return sorted(
        arquivo for arquivo in pasta_entrada.glob("*")
        if arquivo.suffix.lower() in EXTENSOES_RELATO and SUFIXO_SATELITE not in arquivo.stem
    )


def _imagem_satelite_para(relato: Path) -> Path | None:
    """Acha a imagem de satélite pareada com o relato, em qualquer extensão

    aceita, não necessariamente a mesma do arquivo do relato (ex.:
    ``relato_001.png`` pareia com ``relato_001_satelite.jpg``; achado real
    rodando o robô de ponta a ponta: a classificação nunca acontecia porque
    a busca exigia a extensão errada)."""
    for extensao in EXTENSOES_RELATO:
        candidata = relato.with_name(relato.stem + SUFIXO_SATELITE + extensao)
        if candidata.exists():
            return candidata
    return None


def _classificar_imagem_satelite(caminho: Path | None) -> bool | None:
    """Reaproveita o classificador já treinado na Visão Computacional. Se o

    modelo não estiver disponível, o TensorFlow não estiver instalado, ou a
    imagem for ilegível, devolve ``None`` em vez de travar o robô, o
    relato ainda é processado, só sem esse sinal."""
    if caminho is None:
        return None
    try:
        from inferencia.classificador import ErroClassificador, classificar_queimada

        return classificar_queimada(caminho).alerta
    except ErroClassificador as exc:
        log.warning("Classificador de imagem não disponível para %s: %s", caminho.name, exc)
        return None
    except Exception as exc:  # TensorFlow ausente, imagem corrompida etc.
        log.warning("Falha ao classificar a imagem de satélite de %s: %s", caminho.name, exc)
        return None


def _agora() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def processar_relato(caminho: Path, situacao_inpe: SituacaoINPE) -> dict:
    protocolo = f"{caminho.stem}-{uuid.uuid4().hex[:6]}"
    imagem_satelite = _imagem_satelite_para(caminho)

    try:
        relato = extrair_relato(caminho)
        campos = {"local": relato.local, "data": relato.data, "descricao": relato.descricao}
    except ErroOCR as exc:
        log.error("Falha de OCR em %s: %s", caminho.name, exc)
        campos = {"local": None, "data": None, "descricao": None}

    alerta_imagem = _classificar_imagem_satelite(imagem_satelite)
    prioridade = classificar_prioridade(
        descricao=campos["descricao"], imagem_alerta=alerta_imagem,
        total_focos_mes=situacao_inpe.total_focos_mes,
    )

    rotulo_imagem = {True: "alerta", False: "sem alerta", None: "não enviada/indisponível"}[alerta_imagem]
    linha = {
        "Protocolo": protocolo,
        "Processado em": _agora(),
        "Arquivo": caminho.name,
        "Local": campos["local"] or "",
        "Data do relato": campos["data"] or "",
        "Descrição": campos["descricao"] or "",
        "Imagem classificada": rotulo_imagem,
        "Prioridade": prioridade.nivel,
        "Pontuação": prioridade.pontuacao,
        "Motivos": " | ".join(prioridade.motivos),
    }
    registrar_relato(PLANILHA_SAIDA, linha)

    if prioridade.nivel == "ALTA":
        resumo = f"Relato {protocolo} ({caminho.name}): {campos['descricao']}\nMotivos: {linha['Motivos']}"
        notificar_gestor(PASTA_NOTIFICACOES, protocolo, resumo)
        log.info("Notificação gerada para %s (prioridade ALTA).", protocolo)

    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    shutil.move(str(caminho), str(PASTA_PROCESSADOS / caminho.name))
    if imagem_satelite:
        shutil.move(str(imagem_satelite), str(PASTA_PROCESSADOS / imagem_satelite.name))

    return linha


def executar(pasta_entrada: Path | None = None) -> list[dict]:
    pasta_entrada = pasta_entrada or PASTA_ENTRADA
    _configurar_log()
    log.info("Iniciando robô de triagem (entrada: %s).", pasta_entrada)

    situacao_inpe = buscar_situacao_atual()
    if situacao_inpe.obtido_com_sucesso:
        log.info("Contexto do INPE obtido: %s focos no mês de referência %s.",
                 situacao_inpe.total_focos_mes, situacao_inpe.mes_referencia)
    else:
        log.warning("Contexto do INPE indisponível (site fora do ar ou boletim não publicado), seguindo sem esse sinal.")

    resultados: list[dict] = []
    falhas = 0
    for caminho in _relatos_a_processar(pasta_entrada):
        try:
            resultados.append(processar_relato(caminho, situacao_inpe))
        except Exception:  # nunca deixa um relato com problema travar o lote inteiro
            falhas += 1
            log.exception("Falha inesperada ao processar %s", caminho.name)

    log.info("Robô concluído: %d relato(s) processado(s), %d falha(s) não recuperável(is). Planilha: %s",
              len(resultados), falhas, PLANILHA_SAIDA)
    print(f"{len(resultados)} relato(s) processado(s), {falhas} falha(s). Veja {PLANILHA_SAIDA}")
    return resultados


if __name__ == "__main__":
    executar()
