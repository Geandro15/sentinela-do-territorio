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
echo Rodando os testes automaticos...
echo.
python -m pytest -q
echo.
echo Se apareceu "16 passed" em verde, esta tudo certo.
echo Se apareceu algum "FAILED", copie o texto e mande para o Claude.
pause
