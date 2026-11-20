@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  Sentinela do Territorio - instalacao
echo ============================================================
echo.
echo Isso so precisa ser feito uma vez nesta pasta.
echo.

python -m venv .venv
if errorlevel 1 (
    echo.
    echo ERRO: nao consegui criar o ambiente. Confira se o Python esta instalado.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo.
echo Instalando os pacotes do projeto, aguarde...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO na instalacao dos pacotes. Copie a mensagem acima e mande para o Claude.
    pause
    exit /b 1
)

if not exist .env (
    copy .env.example .env >nul
    echo Arquivo .env criado a partir do modelo.
) else (
    echo Arquivo .env ja existia, mantido como estava.
)

echo.
echo ============================================================
echo  Instalacao concluida!
echo ============================================================
echo.
echo Proximo passo: baixar o modelo de linguagem.
echo Abra o aplicativo Ollama (se nao tiver, baixe em https://ollama.com)
echo e depois rode o arquivo 2_BAIXAR_MODELO.bat
echo.
pause
