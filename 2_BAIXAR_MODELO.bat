@echo off
chcp 65001 >nul
echo ============================================================
echo  Baixando o modelo de linguagem (qwen2.5:3b)
echo ============================================================
echo.
echo O aplicativo Ollama precisa estar aberto. Se aparecer erro de
echo conexao, abra o Ollama (icone na bandeja do Windows) e tente de novo.
echo.
echo O download e de alguns gigabytes. So precisa ser feito uma vez.
echo.
ollama pull qwen2.5:3b
if errorlevel 1 (
    echo.
    echo ERRO: nao consegui falar com o Ollama.
    echo 1. Baixe e instale em https://ollama.com se ainda nao tiver.
    echo 2. Abra o programa Ollama e espere o icone aparecer na bandeja.
    echo 3. Rode este arquivo de novo.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo  Modelo baixado! Agora rode o arquivo 3_ABRIR_PROJETO.bat
echo ============================================================
pause
