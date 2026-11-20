# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Telefones de emergência relacionados a queimadas e incêndios florestais no Brasil.

São números fixos, oficiais e de conhecimento público (não mudam com o tempo,
diferente dos boletins do INPE), por isso ficam como uma fonte LOCAL própria do
assistente, junto do resto da base, e não dependem da busca na web
(``busca_web.py``), que tem internet e um motor de busca de terceiros como
dependência e pode falhar ou ficar indisponível (ver `docs/relatorio_genai.md`,
seção 4.7). Isso garante uma resposta confiável e imediata para a pergunta mais
comum fora do tema do boletim: "qual o telefone dos bombeiros/da Defesa Civil?".

Fontes consultadas para confirmar os números (16/11/2026):
- https://viva.com.br/cidadania-e-direitos/qual-numero-ligar-em-cada-emergencia-no-brasil-saiba-quando-acionar-190-192-ou-193.html
- https://www.parana.pr.gov.br/servicos/Seguranca/Bombeiros/Acionar-Corpo-de-Bombeiros-193-0A30a4rk
- https://prefeitura.poa.br/carta-de-servicos/incendio-emergencia-ligue-para-o-telefone-193-corpo-de-bombeiros
"""
from __future__ import annotations

from .chunking import Trecho

_DATA_CONSULTA = "2026-11-16"

CONTATOS_EMERGENCIA: list[Trecho] = [
    Trecho(
        id="contatos_emergencia/bombeiros",
        texto=(
            "Em todo o Brasil, o Corpo de Bombeiros é acionado pelo telefone 193, "
            "gratuito, 24 horas por dia, de qualquer telefone fixo ou celular (mesmo "
            "sem crédito). Esse é o número a usar para avisar sobre um incêndio ou "
            "uma queimada em andamento, inclusive incêndio florestal, resgates e "
            "vazamento de produtos perigosos."
        ),
        secao_id="contatos_emergencia/bombeiros", fonte_id="contatos_emergencia",
        fonte="Números de emergência do Brasil",
        url="https://www.parana.pr.gov.br/servicos/Seguranca/Bombeiros/Acionar-Corpo-de-Bombeiros-193-0A30a4rk",
        data_consulta=_DATA_CONSULTA, titulo="Telefone do Corpo de Bombeiros (193)",
    ),
    Trecho(
        id="contatos_emergencia/defesa_civil",
        texto=(
            "A Defesa Civil é acionada, na maior parte do Brasil, pelo telefone 199, "
            "usado para avisar sobre desastres naturais (como deslizamentos, "
            "enchentes e risco de incêndio florestal em área urbana) e também para "
            "receber alertas por mensagem de texto. Em algumas cidades a Defesa Civil "
            "local pode ter um número próprio; na dúvida, o 193 (Corpo de Bombeiros) "
            "também atende emergências de incêndio e queimada em qualquer lugar do país."
        ),
        secao_id="contatos_emergencia/defesa_civil", fonte_id="contatos_emergencia",
        fonte="Números de emergência do Brasil",
        url="https://viva.com.br/cidadania-e-direitos/qual-numero-ligar-em-cada-emergencia-no-brasil-saiba-quando-acionar-190-192-ou-193.html",
        data_consulta=_DATA_CONSULTA, titulo="Telefone da Defesa Civil (199)",
    ),
]
