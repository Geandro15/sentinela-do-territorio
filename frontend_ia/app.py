# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Abre o projeto inteiro (back-end FastAPI + front-end Gradio) com um único comando:

    cd frontend_ia
    python app.py

Antes, isso exigia dois terminais (um com ``uvicorn backend.main:app``, outro
com ``python -m frontend.app``, ver README, seção 6). Este script sobe o
back-end em segundo plano, espera ele responder ao ``/api/saude``, e só então
abre o front-end no processo principal. Fechar esta janela (ou Ctrl+C)
encerra os dois juntos.

O Ollama (para as abas de pergunta) e o modelo de visão treinado continuam
precisando estar prontos separadamente, sem eles, o front-end ainda abre
normalmente, só mostra uma mensagem clara de indisponibilidade nessas abas
(ver README).
"""
from __future__ import annotations

import atexit
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
PORTA_BACKEND = int(os.environ.get("BACKEND_PORT", "8000"))
PORTA_FRONTEND = int(os.environ.get("FRONTEND_PORT", "7860"))
SEGUNDOS_DE_ESPERA = 30


def _backend_respondeu() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA_BACKEND}/api/saude", timeout=1) as resposta:
            return resposta.status == 200
    except Exception:
        return False


def _subir_backend() -> subprocess.Popen:
    """Sobe o back-end como um processo separado, na mesma pasta deste arquivo."""
    processo = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(PORTA_BACKEND)],
        cwd=RAIZ,
    )
    atexit.register(processo.terminate)
    return processo


def main() -> None:
    print("Subindo o back-end (FastAPI) em segundo plano...")
    processo_backend = _subir_backend()

    print("Esperando o back-end responder...")
    for _ in range(SEGUNDOS_DE_ESPERA * 2):
        if _backend_respondeu():
            print("Back-end no ar em http://127.0.0.1:%d/docs" % PORTA_BACKEND)
            break
        if processo_backend.poll() is not None:
            print("O back-end encerrou sozinho durante a inicialização (veja o erro acima). "
                  "Front-end não vai abrir.")
            sys.exit(1)
        time.sleep(0.5)
    else:
        print(f"O back-end não respondeu em {SEGUNDOS_DE_ESPERA}s; abrindo o front-end assim mesmo "
              "(ele mostra um aviso se o back-end não estiver disponível).")

    import gradio as gr

    from frontend.app import construir_app
    from frontend.features.painel import raiz_do_projeto

    print(f"Abrindo o front-end em http://127.0.0.1:{PORTA_FRONTEND}")
    # allowed_paths libera a pasta raiz do projeto (cluster_computing/ e
    # computacao_quantica/, fora da árvore de frontend_ia/) para os gr.File
    # dos relatórios na aba "📄 Relatórios" (features/painel.py).
    construir_app().launch(
        server_name="0.0.0.0",
        server_port=PORTA_FRONTEND,
        theme=gr.themes.Soft(),
        allowed_paths=[str(raiz_do_projeto())],
    )


if __name__ == "__main__":
    main()
