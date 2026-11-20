# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Componentes visuais reutilizáveis. ``cartao_status`` é usado nas duas
telas de IA (perguntar e verificar imagem) e também no painel, mesma
função, parâmetros diferentes, como pede o critério de componentização.

As cores nunca aparecem sozinhas: todo nível de severidade também mostra
um ícone e uma palavra (acessibilidade, cor não é a única pista).
"""
from __future__ import annotations

NIVEL_COR = {
    "sucesso": "#1e7e34",
    "atencao": "#8a6d00",
    "risco": "#a31515",
    "neutro": "#444444",
}
NIVEL_ICONE = {
    "sucesso": "✅",
    "atencao": "⚠️",
    "risco": "🔥",
    "neutro": "ℹ️",
}
NIVEL_PALAVRA = {
    "sucesso": "Confirmado",
    "atencao": "Atenção",
    "risco": "Risco",
    "neutro": "Informação",
}


def cartao_status(titulo: str, corpo: str, nivel: str = "neutro") -> str:
    """Monta um cartão HTML com cor semântica + ícone + palavra, nunca só a cor.

    ``nivel`` é um de: sucesso, atencao, risco, neutro.
    """
    cor = NIVEL_COR.get(nivel, NIVEL_COR["neutro"])
    icone = NIVEL_ICONE.get(nivel, NIVEL_ICONE["neutro"])
    palavra = NIVEL_PALAVRA.get(nivel, NIVEL_PALAVRA["neutro"])
    corpo_html = corpo.replace("\n", "<br>")
    # Fundo e texto do corpo têm cor fixa (não dependem do tema claro/escuro do
    # navegador): sem isso, no modo escuro o texto herda branco e some sobre o
    # fundo claro do cartão (achado real, visto rodando a interface ao vivo).
    return (
        f'<div style="border-left: 6px solid {cor}; padding: 10px 14px; '
        f'background: color-mix(in srgb, {cor} 8%, white); border-radius: 6px; color:#1a1a1a;">'
        f'<div style="color:{cor}; font-weight:600;">{icone} {palavra}, {titulo}</div>'
        f'<div style="margin-top:4px; color:#1a1a1a;">{corpo_html}</div>'
        f"</div>"
    )


def badge_confianca(confianca: float) -> str:
    """Faixa de confiança em texto simples, reaproveitada no cartão de imagem e no painel."""
    percentual = f"{confianca:.0%}"
    if confianca >= 0.85:
        return f"{percentual} (alta)"
    if confianca >= 0.60:
        return f"{percentual} (moderada)"
    return f"{percentual} (baixa)"
