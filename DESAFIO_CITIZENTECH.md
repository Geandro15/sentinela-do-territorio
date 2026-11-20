# Sentinela do Território, Desafio CitizenTech

**Global Solution 2026.2, Desafio CitizenTech**

**Integrantes:** GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

Visão geral do ecossistema do Sentinela do Território: missão, visão, organograma e as seis perguntas que descrevem a solução, com evidências reais de 2026 que sustentam o problema.

## 1. Missão

Conectar cidadão, poder público e equipes de campo num só ecossistema de triagem de queimadas, usando Inteligência Artificial para transformar relatos dispersos em respostas rápidas, rastreáveis e priorizadas, sem nunca tirar a decisão final das mãos de uma pessoa.

## 2. Visão

Ser uma referência de solução CitizenTech honesta e escalável para o monitoramento de queimadas no Brasil: crescer em volume de atendimento sem perder confiabilidade (toda resposta com fonte, nunca invenção), avaliar com rigor técnico, e não com modismo, quando tecnologias como cluster computing e computação quântica realmente agregam valor, e contribuir de forma mensurável para a proteção da vegetação nativa (ODS 15) e para comunidades mais seguras (ODS 11).

\newpage

## 3. Organograma do ecossistema

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
                                                                         | Defesa Civil / prefeitura |
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

## 4. Quem participará do ecossistema

- **Cidadão relator:** mora em área rural ou perto de vegetação, relata um foco de incêndio ou queimada por texto, voz ou foto de satélite anexada.
- **Gestor público (Defesa Civil, prefeitura):** recebe a fila já priorizada e organizada (`rpa/`), decide a ação final; nenhuma prioridade ALTA vira ação sem essa confirmação humana.
- **Equipes de campo (Corpo de Bombeiros, Defesa Civil):** acionadas quando um relato é confirmado como prioridade ALTA; é a alocação dessas equipes que o estudo de Computação Quântica avalia para picos de ocorrências.
- **INPE (Programa Queimadas):** fonte oficial que alimenta três módulos ao mesmo tempo, a base do assistente (RAG), o scraping do RPA e os dashboards do front-end.
- **Infraestrutura de IA que sustenta a solução:** Ollama (LLM local), modelo de visão (MobileNetV2, treinado no Colab), motores de STT/TTS; e, só como estudo de viabilidade futura, provedores de nuvem quântica (D-Wave, IBM Quantum, IonQ), hoje nenhum deles necessário para o funcionamento real do protótipo.
- **Equipe do grupo:** GEANDRO, LUCAS VERO e ROBERTO EDUARDO, responsáveis pelas 6 disciplinas.

## 5. Como a solução vai funcionar

Fluxo ponta a ponta, do relato à ação:

1. O cidadão abre o front-end (Gradio) e relata por texto, voz ou imagem de satélite.
2. O back-end (FastAPI) encaminha para o módulo certo: assistente RAG (dúvidas), pipeline STT para RAG para TTS (voz) ou classificador de imagem (Visão Computacional).
3. Para um formulário "escaneado" recebido fora do app, o RPA faz OCR do formulário, classifica a imagem anexada (reaproveitando o mesmo modelo de visão), busca o boletim mensal do INPE para dar contexto numérico, e grava tudo numa fila de atendimento em planilha, com notificação automática ao gestor quando a prioridade é ALTA.
4. O gestor abre a fila já priorizada e confirma manualmente a ação; é aqui que entra a Defesa Civil ou o Corpo de Bombeiros.
5. Dois estudos de infraestrutura e futuro completam o quadro sem entrar no fluxo de produção: a simulação de Cluster Computing mostra como o sistema escalaria sob uma rajada de relatos, e o roadmap de Computação Quântica & IA avalia se e quando valeria a pena otimizar a alocação de equipes com computação quântica, hoje ainda sem vantagem comprovada.

## 6. Quem é o cidadão beneficiado

O morador de área rural ou próxima a vegetação, muitas vezes sem acesso fácil a canais técnicos de denúncia, que:

- pode relatar por voz, sem precisar digitar ou preencher formulário;
- recebe respostas confiáveis e rastreáveis (o assistente sempre cita a fonte, e nunca inventa números, o que inclusive motivou a correção dos telefones de emergência fixos durante o desenvolvimento);
- se beneficia indiretamente de uma resposta mais rápida da Defesa Civil ou do Corpo de Bombeiros, porque o relato dele entra numa fila já priorizada em vez de empilhado manualmente.

## 7. Quais tecnologias serão usadas

| Disciplina | Tecnologias |
| --- | --- |
| PLN / Generative AI | RAG híbrido (BM25 + embeddings `fastembed`), LLM `qwen2.5:3b` via Ollama local, STT (Whisper), TTS (Piper local), base fixa de contatos de emergência |
| Visão Computacional | MobileNetV2 com transferência de aprendizado (Keras/TensorFlow), Wildfire Prediction Dataset (Kaggle) |
| RPA | Tesseract (OCR), web scraping do boletim INPE, planilha `.xlsx`, notificação simulada por e-mail |
| Front-end em Sistemas de IA | Gradio (interface), FastAPI (back-end), Pydantic (contratos), Plotly (dashboard) |
| Cluster Computing | Simulador iSPD, escalonador Round Robin (só estudo, sem código no app) |
| Computação Quântica & IA | Recozimento quântico e QAOA avaliados em roadmap (D-Wave, IBM Quantum, IonQ), só análise, nada implementado |
| Dados reais | Boletins InfoQueima e FAQ do INPE, BDQueimadas, Wildfire Prediction Dataset |

## 8. Qual problema será resolvido

O boletim InfoQueima de agosto de 2026 do INPE registrou 20.222 detecções de foco de fogo em um único mês no Brasil, volume que torna inviável um gestor humano revisar e priorizar cada relato manualmente. Ao mesmo tempo, o cidadão comum não tem como saber sozinho se o que vê é realmente uma queimada, nem para onde relatar. O Sentinela do Território ataca os dois lados: dá ao cidadão um canal simples e confiável (voz, texto ou foto), e ao gestor uma triagem automática que já prioriza, classifica e organiza os relatos.

Dois achados recentes, de 2026, reforçam a urgência do problema:

- No Pará, o INPE registrou 30.015 focos de incêndio entre 1º de janeiro e 14 de novembro de 2026, um aumento de 142% sobre o mesmo período de 2025 (12.388 focos), média de 94 focos por dia. O governo federal já reconheceu situação de emergência em 61 municípios paraenses (mais 50 em análise), com R$ 24 milhões aprovados em planos de assistência humanitária.
- Em nível nacional, o Brasil já somava 29.618 focos de incêndio entre 1º de janeiro e 12 de agosto de 2026 (INPE, Terra Brasilis), concentrados em Mato Grosso, Tocantins, Bahia, Maranhão e Pará (62% do total), num cenário agravado pelo El Niño, com risco elevado apontado pelo próprio Ministério do Meio Ambiente para Amazonas, Pará, Tocantins, Maranhão e Mato Grosso.

Os dois estudos adicionais do projeto olham para o problema de escala: Cluster Computing mostra onde a infraestrutura emperra ao crescer, e Computação Quântica & IA avalia o gargalo de alocação de equipes quando muitas ocorrências de prioridade ALTA chegam ao mesmo tempo.

## 9. Quais resultados pode gerar

Resultados já medidos no projeto:

- **Visão Computacional:** 96,7% de acurácia, 97,8% de precisão, 96,1% de recall (6.299 imagens de teste).
- **PLN / Generative AI:** respostas sempre citando fonte, nunca inventando números; 25 testes automatizados cobrindo os casos reais de falha já corrigidos durante o desenvolvimento.
- **RPA:** triagem automática organiza relatos numa fila priorizada e avisa o gestor em prioridade ALTA, sem revisão manual de cada arquivo.
- **Cluster Computing:** dobrar os workers reduziu o tempo de processamento em 30,1% (abaixo do ganho ideal de 50%), achado que orienta onde investir antes de simplesmente comprar mais máquinas.
- **Computação Quântica & IA:** um roadmap honesto mostrando que, hoje, o ganho real vem de um solver clássico de otimização, não do quântico, mas já mapeando o que mudaria se a tecnologia avançar, com ética, LGPD e ODS avaliados.

No conjunto, o resultado esperado é uma resposta mais rápida e confiável a queimadas (ODS 15, Vida Terrestre) e um canal acessível entre cidadão e poder público (ODS 11, Cidades e Comunidades Sustentáveis), com evidência real por trás de cada afirmação, não promessas.

## 10. Fontes

- INPE, Programa Queimadas, Boletim InfoQueima de agosto de 2026: <https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/2026/2026_08_infoqueima.pdf>
- O Liberal, "Focos de incêndio no Pará aumentam 142% em 2026, aponta Inpe": <https://www.oliberal.com/para/focos-de-incendio-no-para-aumentam-142-em-2026-aponta-inpe-1.1194643>
- Brasil61, "Brasil registra quase 30 mil focos de incêndio em 2026": <https://brasil61.com/n/brasil-registra-quase-30-mil-focos-de-incendio-em-2026-aumento-de-temperatura-levanta-alerta-de-risco-para-amazonia-cerrado-e-caatinga-bras2616925>
- Relatórios internos do projeto: `visao/docs/relatorio_visao.md`, `genai/docs/relatorio_genai.md`, `rpa/docs/relatorio_rpa.md`, `cluster_computing/docs/relatorio_cluster.pdf`, `computacao_quantica/docs/relatorio_quantica.md`
