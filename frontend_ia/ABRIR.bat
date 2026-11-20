@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ..\.venv (
    echo O ambiente ainda nao foi criado. Rode primeiro o 1_INSTALAR.bat
    echo na pasta do projeto (uma pasta acima desta).
    pause
    exit /b 1
)

call ..\.venv\Scripts\activate.bat

echo ============================================================
echo  Sentinela do Territorio - POC CitizenTech (front-end integrado)
echo ============================================================
echo.
echo Isso abre o back-end e o front-end juntos, em um so comando.
echo Quando aparecer "Running on local URL", abra no navegador:
echo   http://127.0.0.1:7860
echo.
echo O Ollama precisa estar aberto para as perguntas (texto e voz)
echo responderem. Para fechar o projeto, feche esta janela ou aperte Ctrl+C.
echo ============================================================
echo.

python app.py

echo.
echo O projeto foi encerrado.
pause
