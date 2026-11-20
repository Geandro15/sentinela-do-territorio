# Sentinela do Território, RPA (Robô de Triagem de Relatos)

**Global Solution 2026.2, DESAFIO CITIZENTECH**
**Disciplina: AI for Robotic Process Automation**

Integrantes:
- GEANDRO (RM 562316)
- LUCAS VERO (RM 564202)
- ROBERTO EDUARDO (RM 564537)

## O problema

A Defesa Civil recebe relatos de queimadas de cidadãos em formulários
"escaneados" (foto do papel preenchido à mão ou digitado), às vezes com uma
foto de satélite anexada. Hoje alguém precisa abrir cada arquivo, ler, decidir
a prioridade e organizar isso numa planilha, manual e lento.

Este robô automatiza a **triagem**: lê o formulário por OCR, classifica a
imagem de satélite (reaproveitando o modelo já treinado na disciplina de
Visão Computacional), busca o contexto do boletim mais recente do INPE (web
scraping) e grava tudo numa planilha de fila de atendimento, notificando o
gestor automaticamente nos casos de prioridade alta. Nenhuma decisão é
automática de verdade: toda prioridade ALTA ainda depende de confirmação
humana antes de qualquer ação (mesma regra de governança usada no
classificador de Visão Computacional e no `frontend_ia`).

## Os 3 temas de RPA usados

1. **OCR / extração de documentos** (`rpa/ocr.py`), lê o formulário
   "escaneado" com Tesseract.
2. **Web scraping / automação de navegador** (`rpa/scraping.py`), busca o
   boletim mensal do Programa Queimadas do INPE.
3. **Integração com planilhas e e-mail** (`rpa/planilha.py`,
   `rpa/notificacao.py`), grava a fila de atendimento em `.xlsx` e simula o
   aviso por e-mail ao gestor.

Detalhes de onde cada tema aparece no fluxo, e as evidências reais de teste,
estão em [`docs/relatorio_rpa.md`](docs/relatorio_rpa.md).

## Como está organizado

```
rpa/
├── caminho_projeto.py      # acha genai/ e visao/ a partir deste arquivo
├── ocr.py                  # OCR do formulário (Tesseract)
├── scraping.py             # busca o boletim do INPE (web scraping)
├── regras.py               # combina os 3 sinais e decide a prioridade
├── planilha.py             # grava a fila de atendimento (.xlsx)
├── notificacao.py          # gera o aviso (simulado) ao gestor
├── robo_triagem.py         # ponto de entrada: orquestra tudo
├── gerar_dados_teste.py    # gera 5 relatos sintéticos para testar
├── requirements.txt
├── tests/test_robo.py      # 13 testes automatizados
└── docs/relatorio_rpa.md   # quadro de temas + evidências de validação
```

Este módulo fica **dentro da pasta do projeto principal**, ao lado de
`visao/` e do código do PLN/Generative AI (`assistente/`, `genai/` etc.),
porque ele reaproveita os dois: `caminho_projeto.py` acha essas pastas
automaticamente subindo os diretórios a partir de `rpa/`, não precisa
configurar nenhum caminho manualmente.

## Como configurar as chaves

**Nenhuma chave de API é necessária neste módulo.** O scraping usa uma URL
pública do INPE (sem autenticação), o OCR usa o Tesseract local (programa
gratuito, roda na máquina), e o "e-mail" ao gestor é simulado em arquivo de
texto, de propósito, para não precisar de nenhuma credencial real nem gerar
custo. Se quiserem enviar e-mail de verdade depois, basta trocar o conteúdo
de `notificacao.py` por `smtplib` com um servidor SMTP, mantendo a senha
numa variável de ambiente (nunca no código).

## Como executar

### 1. Instalar as dependências Python

A partir da pasta do projeto (não de dentro de `rpa/`):

```bash
pip install -r rpa/requirements.txt
```

### 2. Instalar o Tesseract OCR (programa do sistema, não é só o pip)

O `pip install pytesseract` instala só a biblioteca Python que *conversa*
com o Tesseract; o programa em si precisa ser instalado separadamente:

- **Windows**: baixe e instale o
  [Tesseract-OCR (UB-Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki)
  e marque a opção de incluir o idioma Português na instalação. Confirme que
  a pasta de instalação (ex. `C:\Program Files\Tesseract-OCR`) está no
  `PATH`, ou configure direto no início do script:
  ```python
  import pytesseract
  pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-por`
- **macOS**: `brew install tesseract tesseract-lang`

### 3. Gerar os relatos de teste (dados sintéticos, nenhum dado real)

```bash
python -m rpa.gerar_dados_teste
```

Isso cria 5 formulários sintéticos em `rpa/entrada/`, incluindo de
propósito um relato com campo faltando (testa a prioridade REVISAR) e um
com imagem de satélite corrompida (testa o tratamento de falha).

### 4. Rodar o robô

```bash
python -m rpa.robo_triagem
```

O resultado fica em `rpa/saida/fila_atendimento.xlsx` (abre no Excel ou
Google Sheets), os avisos de prioridade ALTA em
`rpa/saida/notificacoes/*.txt`, e o log completo em `rpa/logs/robo.log`.

### 5. Rodar os testes automatizados

```bash
python -m pytest rpa/tests -q
```

Os testes não dependem de internet nem do modelo de Visão Computacional
treinado, simulam essas dependências com `monkeypatch`, então passam em
qualquer máquina.

## Decisões e limitações assumidas

- A classificação de imagem de satélite depende do modelo `.keras` da
  disciplina de Visão Computacional já estar configurado (ver `visao/.env`).
  Se o modelo não estiver disponível, o robô **não falha**, processa o
  relato normalmente, só sem esse sinal (ver evidências reais em
  `docs/relatorio_rpa.md`).
- O boletim do INPE só é publicado depois que o mês termina; o robô tenta o
  mês fechado mais recente e, se não encontrar, o anterior a esse.
- A planilha e as notificações ficam em `rpa/saida/` (ignoradas pelo
  controle de versão, pois são saída gerada, não código).
