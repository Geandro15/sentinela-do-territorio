# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Web scraping: busca o boletim mensal mais recente do Programa Queimadas

do INPE (mesma fonte já usada e validada em ``genai/coleta.py``) e extrai
o total de focos de calor registrados no Brasil naquele mês, para dar
contexto à triagem do robô.

Nunca levanta exceção para quem chama: se o site estiver fora do ar, o
boletim do mês ainda não tiver sido publicado, ou o texto não puder ser
interpretado, devolve um resultado com ``obtido_com_sucesso=False``, o
robô segue em frente sem esse sinal, em vez de travar (ver barema, seção
"Resiliência e segurança").
"""
from __future__ import annotations

import datetime as dt
import io
import logging
import re
from dataclasses import dataclass

import requests

log = logging.getLogger("rpa.scraping")

URL_BASE = "https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/{ano}/{ano}_{mes:02d}_infoqueima.pdf"
PADRAO_TOTAL_FOCOS = re.compile(r"([\d.]{3,})\s*(?:detec[cç][oõ]es|focos)", re.IGNORECASE)


@dataclass
class SituacaoINPE:
    total_focos_mes: int | None
    mes_referencia: str
    fonte_url: str
    obtido_com_sucesso: bool


def _texto_do_pdf(conteudo: bytes) -> str:
    from pypdf import PdfReader

    # O número total de focos do mês fica na seção 1 (visto na prática: página
    # 4 do boletim de agosto/2026), 6 páginas cobre com folga. Espaços e
    # quebras de linha são normalizados (mesmo padrão de genai/coleta.py):
    # sem isso, "20.222 detecções" pode ficar quebrado em várias linhas e o
    # regex não encontra o número.
    textos = []
    for pagina in PdfReader(io.BytesIO(conteudo)).pages[:6]:
        textos.append(re.sub(r"\s+", " ", pagina.extract_text() or ""))
    return " ".join(textos)


def _extrair_total_focos(texto: str) -> int | None:
    for correspondencia in PADRAO_TOTAL_FOCOS.finditer(texto):
        numero = correspondencia.group(1).replace(".", "")
        if numero.isdigit():
            return int(numero)
    return None


def _meses_candidatos(hoje: dt.date) -> list[dt.date]:
    """O boletim de um mês só sai depois que o mês termina, tenta o mês

    fechado mais recente, e se não achar, o anterior a esse."""
    primeiro_dia_mes_atual = hoje.replace(day=1)
    mes_fechado = primeiro_dia_mes_atual - dt.timedelta(days=1)
    mes_anterior = mes_fechado.replace(day=1) - dt.timedelta(days=1)
    return [mes_fechado, mes_anterior]


def buscar_situacao_atual(hoje: dt.date | None = None) -> SituacaoINPE:
    hoje = hoje or dt.date.today()
    ultimo_erro = None

    for data in _meses_candidatos(hoje):
        url = URL_BASE.format(ano=data.year, mes=data.month)
        try:
            resposta = requests.get(url, timeout=30)
            resposta.raise_for_status()
            total = _extrair_total_focos(_texto_do_pdf(resposta.content))
            if total is not None:
                log.info("Boletim do INPE de %04d-%02d: %d focos.", data.year, data.month, total)
                return SituacaoINPE(
                    total_focos_mes=total, mes_referencia=f"{data.year}-{data.month:02d}",
                    fonte_url=url, obtido_com_sucesso=True,
                )
            ultimo_erro = "número de focos não encontrado no texto do boletim"
        except requests.exceptions.RequestException as exc:
            ultimo_erro = str(exc)
            log.warning("Falha ao buscar boletim do INPE em %s: %s", url, exc)
        except Exception as exc:  # PDF corrompido, biblioteca ausente etc.
            ultimo_erro = str(exc)
            log.warning("Falha ao interpretar boletim do INPE (%s): %s", url, exc)

    log.warning("Não foi possível obter a situação atual do INPE (%s). O robô segue sem esse contexto.", ultimo_erro)
    return SituacaoINPE(total_focos_mes=None, mes_referencia="indisponível", fonte_url=URL_BASE, obtido_com_sucesso=False)
