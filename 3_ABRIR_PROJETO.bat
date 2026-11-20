@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv (
    echo A instalacao ainda nao foi feita nesta pasta.
    echo Rode primeiro o arquivo 1_INSTALAR.bat
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo ============================================================
echo  Abrindo o Sentinela do Territorio
echo ============================================================
echo.
echo Depois que aparecer "Running on local URL", abra no navegador:
echo   http://127.0.0.1:7860
echo.
echo Para fechar o projeto, feche esta janela ou aperte Ctrl+C.
echo ============================================================
echo.

python app.py

echo.
echo O projeto foi encerrado.
pause
