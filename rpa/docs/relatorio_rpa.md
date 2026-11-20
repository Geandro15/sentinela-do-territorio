# Sentinela do Território, Relatório do módulo de RPA

**Global Solution 2026.2, DESAFIO CITIZENTECH | AI for Robotic Process Automation**

Integrantes: GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

## 1. Quadro de temas

O barema exige pelo menos 3 temas do curso de RPA. Escolhemos estes três:

| Tema | Onde é usado no fluxo | O que resolve |
|---|---|---|
| **OCR / extração de documentos** | `rpa/ocr.py`, chamado por `robo_triagem.processar_relato()` como primeiro passo de cada relato | Lê o formulário "escaneado" (imagem) e extrai os campos `Local`, `Data` e `Descrição` com Tesseract, sem precisar que o cidadão preencha um formulário digital; funciona com uma foto do papel. |
| **Web scraping / automação de navegador** | `rpa/scraping.py`, chamado uma vez por execução em `robo_triagem.executar()`, antes de processar os relatos | Busca o boletim mensal mais recente do Programa Queimadas do INPE (mesma fonte já validada em `genai/coleta.py`) e extrai o total de focos de calor do mês, dando contexto numérico à triagem (ex.: mês com volume de focos muito acima do normal eleva a prioridade). |
| **Integração com planilhas e e-mail** | `rpa/planilha.py` (grava cada relato em `.xlsx`) e `rpa/notificacao.py` (gera o aviso ao gestor), ambos chamados em `robo_triagem.processar_relato()` | Organiza os relatos processados numa fila de atendimento (`.xlsx`, sem precisar de API paga) e avisa automaticamente o gestor quando um relato é prioridade ALTA, sem depender de alguém checar manualmente. |

Um quarto sinal é reaproveitado dos módulos de **Visão Computacional** (o
classificador `.keras` já treinado, chamado em
`robo_triagem._classificar_imagem_satelite()`), não é um tema novo de RPA
em si, mas mostra o robô **orquestrando** um modelo de IA de outra
disciplina do grupo dentro do fluxo automatizado, que é o espírito da
disciplina (RPA *com* IA).

## 2. Como a prioridade é decidida

`rpa/regras.py` combina até 3 sinais independentes num placar simples (ver
código para o detalhe exato):

1. a descrição (OCR) contém uma palavra de risco (fogo, fumaça, queimada,
   incêndio, chamas);
2. a imagem de satélite foi classificada com alerta pelo modelo de Visão
   Computacional (quando disponível);
3. o boletim do INPE aponta um mês com mais de 15.000 focos no Brasil.

0 ou 1 ponto com descrição presente → MEDIA/BAIXA. 2+ pontos → ALTA (gera
notificação). Sem descrição nenhuma (OCR não achou o campo) → **REVISAR**,
sempre, independente dos outros sinais, um relato ilegível não deve virar
nem alta nem baixa prioridade sozinho, precisa de um humano olhando. Nenhuma
notificação ou decisão é automática no sentido de "sem revisão humana": é
uma sugestão de fila, igual ao resto do projeto.

## 3. Evidências de validação (execução real, não só testes unitários)

Além dos **13 testes automatizados** (`python -m pytest rpa/tests -q` →
`13 passed`), o robô foi executado de ponta a ponta de duas formas: primeiro
no ambiente de build (container Linux), depois **na máquina real do
grupo** (Windows, com o `.venv` do projeto), com
`python -m rpa.gerar_dados_teste` seguido de `python -m rpa.robo_triagem`,
sobre 5 relatos sintéticos (dados fictícios, nenhuma informação real de
cidadão, ver seção 4). Resultado real medido na máquina do grupo,
depois de corrigido o bug 5 (abaixo):

```
5 relato(s) processado(s), 0 falha(s) não recuperável(is).
```

Linha a linha, o que a planilha `fila_atendimento.xlsx` realmente registrou
na execução final na máquina do grupo (13:17, OCR e classificador de
imagem já funcionando de ponta a ponta):

| Arquivo | Local (OCR) | Descrição (OCR) | Imagem classificada | Prioridade | Pontos |
|---|---|---|---|---|---|
| `relato_001.png` | "Zona rural, Munickpio X" | "Vi fumaca e fogo na mata atras da fazenda." | sem alerta | MEDIA | 1 |
| `relato_002.png` | "Bairro Y, area urbana" | "Vizinho queimando lixo no quintal, fumaca pequena." | sem alerta | MEDIA | 1 |
| `relato_003.png` | "Estrada rural km 12" | "Area de pastagem com sinais de queimada recente, sem fogo ativo." | não enviada/indisponível (sem par de satélite, de propósito) | MEDIA | 1 |
| `relato_004_campo_faltando.png` | "Sitio Z" | *(vazio, OCR não achou "Descrição:")* | não enviada/indisponível | **REVISAR** | 0 |
| `relato_005_imagem_corrompida.png` | "Fazenda W" | "Fumaca densa visivel a distancia, possivel incendio." | não enviada/indisponível (imagem corrompida de propósito) | MEDIA | 1 |

O OCR leu os campos corretamente em todos os 5 relatos (uma pequena
imprecisão visual, "Munickpio" em vez de "Município" no relato 001, é
ruído normal de OCR sobre uma fonte sintética, não afeta a lógica de
decisão, já que a regra só verifica a presença de palavras de risco na
*descrição*, não no campo "Local"). O caso projetado para cair em
REVISAR (relato 004, sem descrição) caiu exatamente em REVISAR, e nenhum
dos dois casos de falha de propósito (satélite corrompido, campo ausente)
travou o lote.

**Caso de falha tratado 1, boletim do INPE indisponível.** Nesta execução,
os boletins de setembro e outubro de 2026 ainda não tinham sido publicados
(404 do servidor do INPE para os dois meses tentados). O robô registrou o
aviso no log e **seguiu em frente sem esse sinal**, em vez de travar:
```
WARNING rpa.scraping: Não foi possível obter a situação atual do INPE
(404 Client Error ...). O robô segue sem esse contexto.
```
Em teste isolado contra um mês com boletim já publicado (agosto/2026), a
extração funcionou corretamente e encontrou o número real do boletim
(20.222 focos), confirmando que o scraping funciona quando o PDF existe, o que falhou nesta execução foi apenas a disponibilidade do boletim mais
recente, tratada sem erro.

**Caso de falha tratado 2, modelo de Visão Computacional indisponível
neste ambiente.** As 3 imagens de satélite "boas" desta execução (dos
relatos 001, 002 e 005) não puderam ser classificadas porque o arquivo
`.keras` do modelo não está configurado nesta máquina de teste
(`Modelo não encontrado em 'modelos/queimada_mobilenet_v2.keras'`). O robô
registrou o aviso e seguiu, marcando a coluna "Imagem classificada" como
"não enviada/indisponível" em vez de travar, exatamente o comportamento
testado por `rpa/tests/test_robo.py`. Quando o módulo roda na máquina do
grupo (onde o `.env` da Visão Computacional já aponta para o `.keras`
treinado, ver `frontend_ia`), esse sinal passa a contar normalmente para a
prioridade.

**Caso de falha tratado 3, imagem de satélite corrompida.** O arquivo
`relato_005_imagem_corrompida_satelite.jpg` foi gerado de propósito como um
arquivo que não é uma imagem de verdade. O robô tentou classificá-lo,
recebeu uma falha ao abrir o arquivo, registrou o aviso no log e **continuou
processando o relato normalmente** (ele aparece na planilha com prioridade
MEDIA, não travou o lote), o mesmo teste está automatizado em
`test_fluxo_completo_processa_lote_sem_travar_no_arquivo_corrompido`.

**Caso de falha tratado 4, campo obrigatório ausente no formulário.** O
`relato_004_campo_faltando.png` foi gerado sem a linha "Descrição:" de
propósito. O OCR não encontrou o campo, devolveu `None`, e a regra de
prioridade mandou o relato direto para REVISAR, nenhuma tentativa de
adivinhar ou inventar uma descrição.

**Bug real 5, Tesseract instalado, mas fora do alcance do robô na
primeira tentativa na máquina do grupo.** Na primeira execução na máquina
real, o Tesseract OCR já tinha sido instalado (confirmado em
`C:\Program Files\Tesseract-OCR\tesseract.exe`), mas o robô continuava
avisando "o programa Tesseract OCR não está instalado nesta máquina", o
instalador do Windows não atualiza o `PATH` do processo já aberto (o
terminal/editor precisa ser reaberto para o Windows propagar a mudança),
e mesmo reabrir o terminal nem sempre bastou no ambiente testado. Em vez de
depender disso, `rpa/ocr.py` foi ajustado para primeiro checar o `PATH`
(`shutil.which("tesseract")`) e, se não encontrar, tentar automaticamente o
caminho padrão de instalação do Windows (`_configurar_caminho_tesseract()`), corrigido e confirmado funcionando na mesma execução real que gerou a
tabela acima, sem precisar reiniciar nada.

Esses 5 casos, junto com os 13 testes automatizados que simulam falha de
rede/arquivo com `monkeypatch`, cobrem a exigência do barema de
"Resiliência e segurança": nenhuma falha de uma fonte externa (INPE, modelo
de IA, arquivo de imagem, configuração local do Tesseract) derruba o
processamento dos outros relatos do lote.

## 4. Proteção de dados, ética e ODS

- **Nenhum dado real de cidadão foi usado neste módulo.** Os 5 relatos de
  teste são sintéticos, gerados por `rpa/gerar_dados_teste.py` com `PIL`, nomes, locais e descrições fictícios, criados só para exercitar o
  pipeline.
- **Nenhuma decisão é automática de verdade.** Mesmo a prioridade ALTA
  (que gera notificação) é uma sugestão de fila para o gestor humano
  confirmar, a mesma regra de governança usada no classificador de
  Visão Computacional e no `frontend_ia` ("esta é uma sugestão automática,
  não uma decisão").
- **Nenhuma credencial real é usada.** O aviso ao gestor é simulado em
  arquivo de texto (sem envio de e-mail de verdade, sem senha, sem custo).
  O scraping usa uma URL pública do INPE, sem autenticação.
- **ODS 15 (Vida Terrestre)** é o eixo principal, o robô acelera a triagem
  de relatos de queimadas, apoiando a resposta mais rápida à degradação de
  vegetação e biomas. **ODS 11 (Cidades e Comunidades Sustentáveis)**
  também se aplica, pela participação do cidadão (relato) na gestão de
  risco urbano/rural, consistente com o eixo de ODS já usado no resto do
  projeto (Visão Computacional e Generative AI/PLN).
