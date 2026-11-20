# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)

"""Navegação do app: uma barra lateral (gr.Sidebar) com os atalhos e os
links externos, no lugar da antiga aba "Menu" no topo, e duas abas sem
cabeçalho visível na faixa de abas (a faixa nativa do Gradio fica oculta
por CSS em app.py; a navegação passa a ser só pela lateral):

  - a aba que abre por padrão ao carregar a página: a comparação real
    2025 vs. 2026 dos focos de queimada (INPE), com 4 gráficos em
    destaque;
  - a aba "Dashboard Visão Computacional", com os 6 gráficos do
    classificador de imagens, separada do dashboard do INPE e alcançada
    pelo botão da lateral logo abaixo de "🛰️ Verificar imagem";
  - a aba de "Informações do sistema", alcançada só pelo botão da
    lateral, com o que cada uma das 4 disciplinas faz e por que importa
    aqui dentro.
"""
from __future__ import annotations

import base64
from pathlib import Path

import gradio as gr

from .dashboard_inpe import construir_secao_destaque_inpe
from .dashboard_visao import construir_secao_dashboard_visao

# Logo da FIAP, usada só na aba "Desafio CitizenTech" (agradecimento). Helper
# próprio, independente do _b64/_html_logo de app.py, pelo mesmo motivo de
# painel.py ter seu próprio _raiz_do_projeto: cada módulo resolve os próprios
# caminhos, sem depender da ordem de import de outro arquivo.
_PASTA_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_IMAGEM_LOGO_FIAP = _PASTA_ASSETS / "logo_fiap.png"


def _html_logo_fiap() -> str:
    try:
        dados = base64.b64encode(_IMAGEM_LOGO_FIAP.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return (
        '<div style="text-align:center; margin: 1.2rem 0;">'
        f'<img src="data:image/png;base64,{dados}" alt="Logo da FIAP" '
        'style="max-width:280px; width:60%; background:#fff; padding:14px 20px; '
        'border-radius:10px;">'
        "</div>"
    )

# Links externos confiáveis, conferidos manualmente, não inventados.
LINK_INPE_QUEIMADAS = "http://www.inpe.br/queimadas"
LINK_NASA_FIRMS = "https://firms.modaps.eosdis.nasa.gov"

# Ordem/ids das abas em app.py, usados pelos botões da lateral para saber
# para onde ir (gr.Tabs(selected=N)). A Visão Computacional agora é uma aba
# própria (ABA_DASHBOARD_VISAO), separada do dashboard do INPE, com o botão
# da lateral posicionado logo abaixo de "🛰️ Verificar imagem".
ABA_DASHBOARD, ABA_PERGUNTAR, ABA_VOZ, ABA_IMAGEM, ABA_DASHBOARD_VISAO, ABA_PAINEL, ABA_INFO, ABA_DESAFIO = (
    0, 1, 2, 3, 4, 5, 6, 7,
)

_TEXTO_INFORMACOES = """
## ℹ️ Informações do sistema

Projeto CitizenTech que junta **seis disciplinas** da Global Solution: quatro integradas e
rodando dentro deste app, para apoiar a triagem de queimadas, e duas de estudo/análise
(Cluster Computing e Computação Quântica & IA) que avaliam a infraestrutura e o futuro da
solução, sem código ligado ao app, disponíveis para consulta na aba "📄 Relatórios":

- **🗣️ PLN / Generative AI**
  - O que é: assistente conversacional com RAG (Retrieval-Augmented Generation), um LLM
    (via Ollama, local) conversa com uma base vetorial montada a partir de fontes oficiais do
    INPE (FAQ do Programa Queimadas, boletins mensais).
  - Como funciona aqui: a pergunta do cidadão é comparada por similaridade com os trechos da
    base; só os trechos relevantes entram no prompt do LLM, que responde citando de onde tirou
    cada informação. Se a base não tem nada relevante sobre o assunto, o sistema diz que não
    sabe, em vez de inventar uma resposta.
  - Importância no app: é o canal pelo qual o cidadão tira dúvidas com respostas confiáveis e
    rastreáveis, usado nas abas "Relatar / Perguntar" e "Perguntar por voz" (que reaproveita o
    mesmo RAG depois de transcrever o áudio).

- **🛰️ Visão Computacional**
  - O que é: um classificador de imagens (MobileNetV2 pré-treinado + uma camada final treinada
    por transferência de aprendizado) sobre o Wildfire Prediction Dataset (cerca de 39 mil
    imagens de satélite/aéreas).
  - Resultado medido (conjunto de teste, 6.299 imagens, ver `visao/docs/relatorio_visao.md`):
    96,7% de acurácia, 97,8% de precisão, 96,1% de recall, 97,0% de F1-score.
  - Importância no app: é a segunda fonte de evidência, independente do relato em texto do
    cidadão, usada na aba "Verificar imagem" e também dentro do robô de RPA, ao classificar a
    imagem de satélite anexada a um relato recebido.

- **🖥️ Front-end em Sistemas de IA**
  - O que é: esta própria interface (Gradio) conversando só com um back-end único em FastAPI, nunca diretamente com o LLM ou com o modelo de visão.
  - Como funciona aqui: reúne as telas de chat, voz, verificação de imagem e o painel da sessão,
    todas chamando a mesma API; nenhuma chave ou modelo fica exposto no navegador.
  - Importância no app: é a porta de entrada única do sistema para o cidadão, e o ponto em que
    toda sugestão da IA (resposta, classificação de imagem) é mostrada para confirmação, nenhuma delas vira ação automática.

- **🤖 AI for Robotic Process Automation (RPA)**
  - O que é: um robô de triagem (`rpa/`) que combina 3 automações, OCR (Tesseract, lê o
    formulário "escaneado" do relato), web scraping (busca o boletim mensal do INPE) e
    integração com planilha/e-mail (organiza tudo numa fila de atendimento em `.xlsx` e simula
    o aviso ao gestor).
  - Como funciona aqui: ao processar um relato, o robô também aciona o classificador de Visão
    Computacional acima (se houver imagem de satélite anexada) e usa o contexto do boletim do
    INPE para ajudar a decidir a prioridade (ALTA/MÉDIA/BAIXA/REVISAR).
  - Importância no app: é o que transforma uma pilha de relatos recebidos numa fila já
    priorizada e auditável para o gestor humano, sem exigir que alguém leia um relato de cada
    vez, e, como nas outras três partes, sem decidir nada sozinho: toda prioridade ALTA ainda
    depende de confirmação humana antes de qualquer ação.

- **☁️ Cluster Computing, Computação Neuromórfica e Supercomputadores**
  - O que é: um estudo de infraestrutura, fora do código deste app, uma simulação no
    simulador iSPD de como o Sentinela do Território escalaria se tivesse que processar, em
    cluster, uma rajada de áudios de triagem (reconhecimento de fala + classificação "aviso de
    incêndio ou não") chegando ao mesmo tempo, num pico de queimada.
  - O que o grupo fez: comparou o mesmo cluster com 2 e com 4 workers, dobrar os workers reduziu
    o tempo total em 30,1% (bem abaixo do ganho ideal de 50%), porque o envio dos áudios pelo
    mestre não escala com o número de workers; relatório completo em
    `cluster_computing/docs/relatorio_cluster.pdf`.
  - Importância para sistemas de informação: mostra, com números, por que simplesmente "colocar
    mais máquinas" não resolve um gargalo sozinho, a comunicação entre as partes do sistema
    também precisa escalar, um cuidado de arquitetura que vale para qualquer sistema de
    informação que cresça em volume de dados ou de usuários, não só para este projeto.

- **⚛️ Computação Quântica & IA**
  - O que é: um estudo de viabilidade, também fora do código deste app, avalia se e quando a
    computação quântica ajudaria um gargalo real do protótipo.
  - O que o grupo fez: identificou a alocação de equipes de campo (Bombeiros, Defesa Civil) em
    picos de ocorrências como o gargalo, escolheu otimização combinatória como a capacidade
    quântica que o atacaria, e montou um roadmap (IA clássica hoje → quântico no futuro →
    benefício esperado) com ética, LGPD e ODS avaliados em cada etapa; relatório completo em
    `computacao_quantica/docs/relatorio_quantica.pdf`.
  - Importância para sistemas de informação: reforça que decidir **se** e **quando** adotar uma
    tecnologia nova é, em si, uma decisão de sistemas de informação, hoje (2024-2026) nem os
    pilotos de otimização quântica em empresas reais provam vantagem sobre bons solvers
    clássicos, e enviar dados de localização de cidadãos a uma nuvem quântica estrangeira
    levanta uma questão concreta de LGPD (transferência internacional de dados) que qualquer
    sistema público que avalie essa tecnologia vai precisar resolver antes de adotá-la.

"""

# Texto da aba "Desafio CitizenTech": missão, visão e organograma do
# ecossistema do projeto (resumo do relatório `DESAFIO_CITIZENTECH.md`, na
# raiz do projeto, que tem a versão completa com as seis perguntas
# respondidas e as fontes), seguido do agradecimento final à FIAP.
_TEXTO_DESAFIO = """
## 🎯 Desafio CitizenTech

**Global Solution 2026.2, Desafio CitizenTech.** O Sentinela do Território nasceu desse desafio: usar
Inteligência Artificial para criar uma solução real de impacto social, ligando cidadão, poder público
e tecnologia num só ecossistema. O relatório completo, com as seis perguntas do desafio respondidas em
detalhe e as fontes usadas, está em `DESAFIO_CITIZENTECH.md` / `DESAFIO_CITIZENTECH.pdf`, na raiz do
projeto, e também disponível para consulta na aba "📄 Relatórios".

### Missão

Conectar cidadão, poder público e equipes de campo num só ecossistema de triagem de queimadas, usando
Inteligência Artificial para transformar relatos dispersos em respostas rápidas, rastreáveis e
priorizadas, sem nunca tirar a decisão final das mãos de uma pessoa.

### Visão

Ser uma referência de solução CitizenTech honesta e escalável para o monitoramento de queimadas no
Brasil: crescer em volume de atendimento sem perder confiabilidade (toda resposta com fonte, nunca
invenção), avaliar com rigor técnico, e não com modismo, quando tecnologias como cluster computing e
computação quântica realmente agregam valor, e contribuir de forma mensurável para a proteção da
vegetação nativa (ODS 15) e para comunidades mais seguras (ODS 11).

### Organograma do ecossistema

```
                           +----------------------------+
                           |  INPE (Programa Queimadas) |
                           |  dados oficiais             |
                           +--------------+--------------+
                                          |
                                          v
+-----------+  texto / voz /   +-------------------------------+
|  Cidadão   |  imagem ------->|  Front-end + Back-end          |
| (morador)  |                 |  (Gradio + FastAPI)            |
+-----------+                 +----------------+----------------+
                                               |
              +---------------------------------+---------------------------------+
              v                                 v                                 v
   +--------------------+          +------------------------+          +--------------------------+
   | Assistente RAG       |        | Classificador de         |        | RPA (triagem)             |
   | PLN / Generative AI  |        | imagem, Visão Comp.      |        | OCR + scraping + fila    |
   +--------------------+          +------------------------+          +------------+-------------+
                                                                                     | fila priorizada
                                                                                     v
                                                                         +--------------------------+
                                                                         | Gestor público            |
                                                                         | Defesa Civil / prefeitura|
                                                                         +------------+-------------+
                                                                                     | aciona
                                                                                     v
                                                                         +--------------------------+
                                                                         | Equipes de campo          |
                                                                         | Bombeiros / Defesa Civil  |
                                                                         +--------------------------+

  Estudos de apoio à decisão (não entram no fluxo de produção):
  +------------------------+          +---------------------------------+
  | Cluster Computing        |        | Computação Quântica & IA          |
  | escala de infraestrutura |        | otimização de alocação de equipes |
  +------------------------+          +---------------------------------+
```

### Quem participará do ecossistema

- **Cidadão relator:** mora em área rural ou perto de vegetação, relata um foco de incêndio ou
  queimada por texto, voz ou foto de satélite anexada.
- **Gestor público (Defesa Civil, prefeitura):** recebe a fila já priorizada e organizada (`rpa/`),
  decide a ação final; nenhuma prioridade ALTA vira ação sem essa confirmação humana.
- **Equipes de campo (Corpo de Bombeiros, Defesa Civil):** acionadas quando um relato é confirmado
  como prioridade ALTA; é a alocação dessas equipes que o estudo de Computação Quântica avalia para
  picos de ocorrências.
- **INPE (Programa Queimadas):** fonte oficial que alimenta três módulos ao mesmo tempo, a base do
  assistente (RAG), o scraping do RPA e os dashboards do front-end.
- **Infraestrutura de IA que sustenta a solução:** Ollama (LLM local), modelo de visão (MobileNetV2,
  treinado no Colab), motores de STT/TTS; e, só como estudo de viabilidade futura, provedores de
  nuvem quântica (D-Wave, IBM Quantum, IonQ), hoje nenhum deles necessário para o funcionamento real
  do protótipo.
- **Equipe do grupo:** GEANDRO, LUCAS VERO e ROBERTO EDUARDO, responsáveis pelas 6 disciplinas.

### Como a solução vai funcionar

Fluxo ponta a ponta, do relato à ação:

1. O cidadão abre o front-end (Gradio) e relata por texto, voz ou imagem de satélite.
2. O back-end (FastAPI) encaminha para o módulo certo: assistente RAG (dúvidas), pipeline STT para
   RAG para TTS (voz) ou classificador de imagem (Visão Computacional).
3. Para um formulário "escaneado" recebido fora do app, o RPA faz OCR do formulário, classifica a
   imagem anexada (reaproveitando o mesmo modelo de visão), busca o boletim mensal do INPE para dar
   contexto numérico, e grava tudo numa fila de atendimento em planilha, com notificação automática
   ao gestor quando a prioridade é ALTA.
4. O gestor abre a fila já priorizada e confirma manualmente a ação; é aqui que entra a Defesa Civil
   ou o Corpo de Bombeiros.
5. Dois estudos de infraestrutura e futuro completam o quadro sem entrar no fluxo de produção: a
   simulação de Cluster Computing mostra como o sistema escalaria sob uma rajada de relatos, e o
   roadmap de Computação Quântica & IA avalia se e quando valeria a pena otimizar a alocação de
   equipes com computação quântica, hoje ainda sem vantagem comprovada.

### Quem é o cidadão beneficiado

O morador de área rural ou próxima a vegetação, muitas vezes sem acesso fácil a canais técnicos de
denúncia, que:

- pode relatar por voz, sem precisar digitar ou preencher formulário;
- recebe respostas confiáveis e rastreáveis (o assistente sempre cita a fonte, e nunca inventa
  números, o que inclusive motivou a correção dos telefones de emergência fixos durante o
  desenvolvimento);
- se beneficia indiretamente de uma resposta mais rápida da Defesa Civil ou do Corpo de Bombeiros,
  porque o relato dele entra numa fila já priorizada em vez de empilhado manualmente.

### Quais tecnologias serão usadas

| Disciplina | Tecnologias |
| --- | --- |
| PLN / Generative AI | RAG híbrido (BM25 + embeddings `fastembed`), LLM `qwen2.5:3b` via Ollama local, STT (Whisper), TTS (Piper local), base fixa de contatos de emergência |
| Visão Computacional | MobileNetV2 com transferência de aprendizado (Keras/TensorFlow), Wildfire Prediction Dataset (Kaggle) |
| RPA | Tesseract (OCR), web scraping do boletim INPE, planilha `.xlsx`, notificação simulada por e-mail |
| Front-end em Sistemas de IA | Gradio (interface), FastAPI (back-end), Pydantic (contratos), Plotly (dashboard) |
| Cluster Computing | Simulador iSPD, escalonador Round Robin (só estudo, sem código no app) |
| Computação Quântica & IA | Recozimento quântico e QAOA avaliados em roadmap (D-Wave, IBM Quantum, IonQ), só análise, nada implementado |
| Dados reais | Boletins InfoQueima e FAQ do INPE, BDQueimadas, Wildfire Prediction Dataset |

### Qual problema será resolvido

O boletim InfoQueima de agosto de 2026 do INPE registrou 20.222 detecções de foco de fogo em um único
mês no Brasil, volume que torna inviável um gestor humano revisar e priorizar cada relato manualmente.
Ao mesmo tempo, o cidadão comum não tem como saber sozinho se o que vê é realmente uma queimada, nem
para onde relatar. O Sentinela do Território ataca os dois lados: dá ao cidadão um canal simples e
confiável (voz, texto ou foto), e ao gestor uma triagem automática que já prioriza, classifica e
organiza os relatos.

Dois achados recentes, de 2026, reforçam a urgência do problema:

- No Pará, o INPE registrou 30.015 focos de incêndio entre 1º de janeiro e 14 de novembro de 2026, um
  aumento de 142% sobre o mesmo período de 2025 (12.388 focos), média de 94 focos por dia. O governo
  federal já reconheceu situação de emergência em 61 municípios paraenses (mais 50 em análise), com
  R$ 24 milhões aprovados em planos de assistência humanitária.
- Em nível nacional, o Brasil já somava 29.618 focos de incêndio entre 1º de janeiro e 12 de agosto de
  2026 (INPE, Terra Brasilis), concentrados em Mato Grosso, Tocantins, Bahia, Maranhão e Pará (62% do
  total), num cenário agravado pelo El Niño, com risco elevado apontado pelo próprio Ministério do
  Meio Ambiente para Amazonas, Pará, Tocantins, Maranhão e Mato Grosso.

Os dois estudos adicionais do projeto olham para o problema de escala: Cluster Computing mostra onde a
infraestrutura emperra ao crescer, e Computação Quântica & IA avalia o gargalo de alocação de equipes
quando muitas ocorrências de prioridade ALTA chegam ao mesmo tempo.

### Quais resultados pode gerar

Resultados já medidos no projeto:

- **Visão Computacional:** 96,7% de acurácia, 97,8% de precisão, 96,1% de recall (6.299 imagens de
  teste).
- **PLN / Generative AI:** respostas sempre citando fonte, nunca inventando números; 25 testes
  automatizados cobrindo os casos reais de falha já corrigidos durante o desenvolvimento.
- **RPA:** triagem automática organiza relatos numa fila priorizada e avisa o gestor em prioridade
  ALTA, sem revisão manual de cada arquivo.
- **Cluster Computing:** dobrar os workers reduziu o tempo de processamento em 30,1% (abaixo do ganho
  ideal de 50%), achado que orienta onde investir antes de simplesmente comprar mais máquinas.
- **Computação Quântica & IA:** um roadmap honesto mostrando que, hoje, o ganho real vem de um solver
  clássico de otimização, não do quântico, mas já mapeando o que mudaria se a tecnologia avançar, com
  ética, LGPD e ODS avaliados.

No conjunto, o resultado esperado é uma resposta mais rápida e confiável a queimadas (ODS 15, Vida
Terrestre) e um canal acessível entre cidadão e poder público (ODS 11, Cidades e Comunidades
Sustentáveis), com evidência real por trás de cada afirmação, não promessas.

---

### Agradecimento

Chegar até aqui não foi só entregar mais um projeto de faculdade. São quase dois anos de aprendizado,
de noites virando código, de aulas que pareciam pesadas no começo e que hoje fazem todo sentido juntas,
num projeto só. Esse tempo todo teve nome e rosto: foram os professores da FIAP que nos ensinaram, aula
após aula, disciplina após disciplina, a pensar como quem resolve problema de verdade, e não só a
decorar tecnologia.

Agradecemos de coração a cada professor que teve paciência para explicar de novo, que cobrou qualidade
quando podia deixar passar, e que acreditou que um grupo de alunos conseguiria juntar seis disciplinas
tão diferentes, PLN, Visão Computacional, RPA, Front-end, Cluster Computing e Computação Quântica, numa
solução só, coerente e honesta sobre o que entrega hoje e o que ainda é promessa para o futuro. Isso só
foi possível porque, antes de qualquer linha de código, tivemos uma base sólida de ensino para construir
em cima.

A FIAP, conhecida como "a melhor faculdade de tecnologia", desde 1993 forma profissionais de tecnologia
no Brasil, e nós sentimos isso na prática: no empenho de quem ensina, na exigência dos projetos, e na
cobrança para que cada entrega fosse de verdade, não só para cumprir tabela. Estamos nos formando com a
certeza de que levamos daqui muito mais do que um diploma: levamos a forma de pensar e de resolver
problemas que esses dois anos de FIAP nos ensinaram.

Com gratidão, GEANDRO, LUCAS VERO e ROBERTO EDUARDO.
"""


def construir_aba_dashboard() -> None:
    """Aba que abre por padrão ao carregar a página: os 4 gráficos reais do

    INPE (2025 vs. 2026) em destaque. Os gráficos da Visão Computacional
    ficam em aba própria, ver ``construir_aba_dashboard_visao``."""
    with gr.Tab("📊 Dashboards", id=ABA_DASHBOARD):
        construir_secao_destaque_inpe()


def construir_aba_dashboard_visao() -> None:
    """Aba própria para os 6 gráficos da Visão Computacional, separada do

    dashboard do INPE, alcançada pelo botão da lateral logo abaixo de
    "🛰️ Verificar imagem"."""
    with gr.Tab("🛰️ Dashboard Visão Computacional", id=ABA_DASHBOARD_VISAO):
        construir_secao_dashboard_visao()


def construir_aba_informacoes() -> None:
    with gr.Tab("ℹ️ Informações do sistema", id=ABA_INFO):
        gr.Markdown(_TEXTO_INFORMACOES, elem_classes=["texto-destaque"])


def construir_aba_desafio() -> None:
    """Aba "Desafio CitizenTech": missão, visão e organograma do

    ecossistema, seguidos do agradecimento final à FIAP e aos professores
    (com o logo da FIAP, `frontend/assets/logo_fiap.png`)."""
    with gr.Tab("🎯 Desafio CitizenTech", id=ABA_DESAFIO):
        gr.Markdown(_TEXTO_DESAFIO, elem_classes=["texto-destaque"])
        gr.HTML(_html_logo_fiap())


def construir_barra_lateral(abas: gr.Tabs) -> None:
    """Menu de navegação na lateral (gr.Sidebar), no lugar da antiga aba

    "Menu" no topo. A faixa nativa de abas do Gradio fica oculta (ver CSS
    em app.py), a navegação passa a ser só por aqui."""
    with gr.Sidebar():
        gr.Markdown("## 🔥 Menu")

        gr.Markdown("### Ir para")
        botao_dashboard = gr.Button("📊 Dashboards")
        botao_perguntar = gr.Button("💬 Relatar / Perguntar")
        botao_voz = gr.Button("🎙️ Perguntar por voz")
        botao_imagem = gr.Button("🛰️ Verificar imagem")
        botao_dashboard_visao = gr.Button("📊 Dashboard Visão Computacional")
        botao_painel = gr.Button("📄 Relatórios")

        gr.Markdown("### Fontes oficiais externas")
        gr.Button("🗺️ Mapa de queimadas do INPE", link=LINK_INPE_QUEIMADAS)
        gr.Button("🛰️ Imagens de satélite (NASA FIRMS)", link=LINK_NASA_FIRMS)
        gr.Markdown("_Esses links abrem o site oficial em outra aba do navegador._")

        gr.Markdown("---")
        botao_info = gr.Button("ℹ️ Informações do sistema")
        botao_desafio = gr.Button("🎯 Desafio CitizenTech")

    botao_dashboard.click(lambda: gr.Tabs(selected=ABA_DASHBOARD), outputs=abas)
    botao_perguntar.click(lambda: gr.Tabs(selected=ABA_PERGUNTAR), outputs=abas)
    botao_voz.click(lambda: gr.Tabs(selected=ABA_VOZ), outputs=abas)
    botao_imagem.click(lambda: gr.Tabs(selected=ABA_IMAGEM), outputs=abas)
    botao_dashboard_visao.click(lambda: gr.Tabs(selected=ABA_DASHBOARD_VISAO), outputs=abas)
    botao_painel.click(lambda: gr.Tabs(selected=ABA_PAINEL), outputs=abas)
    botao_info.click(lambda: gr.Tabs(selected=ABA_INFO), outputs=abas)
    botao_desafio.click(lambda: gr.Tabs(selected=ABA_DESAFIO), outputs=abas)
