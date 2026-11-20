# Sentinela do Território, POC CitizenTech (Front-end em Sistemas de IA)

**Integrantes:** GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

Global Solution CitizenTech 2026/2, disciplina Front-end em Sistemas de IA.

Esta pasta é a Prova de Conceito (POC) desta disciplina: uma interface web que liga, de ponta a ponta, o relato do cidadão aos dois modelos de IA já construídos nas disciplinas anteriores do projeto (o assistente conversacional com RAG do módulo de PLN/Generative AI, e o classificador de imagens de satélite da Visão Computacional).

## 1. Problema e público

O cidadão que vê fumaça ou um foco de fogo perto de casa não tem como saber, sozinho, se aquilo é realmente uma queimada, nem para onde relatar, e um gestor público recebe relatos sem nenhuma forma de priorizar os mais graves. O Sentinela do Território já ataca isso por voz (PLN) e por imagem de satélite (Visão Computacional); esta POC junta as duas pontas em uma única tela, pensada para o cidadão comum, sem jargão técnico.

**Público:** moradores de áreas rurais ou próximas à vegetação, e gestores públicos (Defesa Civil, prefeitura) que avaliam os relatos recebidos.

**Fonte que sustenta o problema:** o boletim InfoQueima de agosto de 2026 do INPE registrou 20.222 detecções de focos de fogo no Brasil naquele mês (<https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/2026/2026_08_infoqueima.pdf>), volume que torna inviável um gestor humano revisar cada relato sem uma triagem automática prévia.

**ODS:**
- **ODS 15 (Vida Terrestre):** detecção e resposta mais rápida a queimadas protege a vegetação nativa.
- **ODS 11 (Cidades e Comunidades Sustentáveis):** dá ao cidadão um canal simples e confiável para relatar riscos, e ao gestor público uma fila priorizada de atendimento.

## 2. Fluxo CitizenTech

```
 Cidadão                     Front-end (Gradio)                Back-end (FastAPI)              IA
 ───────                     ───────────────────               ───────────────────             ──
 Pergunta de texto   ──HTTP──▶  POST /api/perguntar     ──────▶  pipelines/rag.py      ──────▶  Assistente RAG
  ou áudio, ou                 POST /api/perguntar-por- ──────▶  pipelines/voz.py      ──────▶  (genai, Ollama local) +
  imagem de satélite           voz                               (STT → RAG → TTS)              STT/TTS (assistente/)
                               POST /api/classificar-   ──────▶  pipelines/imagem.py    ──────▶  Classificador de imagem
                               imagem                                                              (visao/inferencia, modelo
                                                                                                    treinado no Colab)
      ▲                              │                                 │
      │        resposta estruturada  │        resposta estruturada     │
      └──────────(Pydantic)──────────┴─────────(Pydantic)───────────────┘
      │
      ▼
 Cartão com resposta/alerta + fontes/aviso ──▶ Confirmação do cidadão/gestor (👍/👎, confirmar alerta)
                                              ──▶ Painel (histórico, gráfico Plotly, filtros)
```

A aba "Perguntar por voz" reaproveita o mesmo assistente RAG do chat de texto (não é um caminho de IA separado): o áudio é transcrito (STT), o texto transcrito passa pelo mesmo `pipelines/rag.py`, e a resposta final é sintetizada em áudio (TTS) antes de voltar ao cidadão.

O front-end nunca chama o Ollama nem o modelo de visão diretamente: tudo passa pelo back-end, que devolve sempre um JSON estruturado (nunca texto livre do LLM sem forma).

## 3. Decisões técnicas

- **Gradio, não Streamlit.** O grupo já tinha o assistente de voz construído em Gradio nas disciplinas anteriores, e o barema permite as duas opções. Usar Gradio aqui manteve a mesma biblioteca do resto do projeto e reaproveitou a experiência do grupo com `gr.State` e os listeners `.click()`/`.change()`.
- **Back-end FastAPI separado**, em vez de o front-end chamar o LLM direto: é exigência do barema (seção 3.2) e também faz sentido no projeto, porque o mesmo back-end pode futuramente atender outras interfaces (o app de voz, um app mobile) sem duplicar a lógica de IA.
- **Saída estruturada (Pydantic)** em vez de texto livre: `PerguntaSaida` e `ImagemSaida` sempre trazem campos fixos (resposta, fontes, motivo, confiança, alerta), para a interface nunca precisar "adivinhar" o que o modelo quis dizer.
- **Prompt e abstenção:** reaproveitados do módulo de Generative AI (`genai/gerador.py`), já testados e documentados em `genai/docs/relatorio_genai.md`. Não foram recriados aqui para não arriscar divergência entre os dois módulos.
- **Voz (STT/TTS):** a aba "Perguntar por voz" reaproveita `assistente/stt.py` (faster-whisper, local) e `assistente/tts.py` (edge-tts) já construídos e testados no módulo de PLN, em vez de reimplementar. A transcrição passa pelo mesmo `pipelines/rag.py` do chat de texto, mesma lógica, mesma verificação, só muda a entrada/saída (áudio em vez de texto).
- **Deploy via Docker** (`docker-compose.yml`), não em nuvem pública: o projeto depende do Ollama local (sem custo, sem chave de API) e, no caso da Visão, de um modelo treinado que fica no computador do usuário, rodar os dois serviços encapsulados localmente é mais simples e mais fiel ao resto do projeto do que depender de uma conta externa (Streamlit Cloud/Render).

## 4. Ética e limites da IA

- **Nenhuma decisão é automática.** Toda resposta de imagem carrega o aviso "esta é uma sugestão automática, não uma decisão" (de `visao/inferencia/classificador.py`), e a tela exige confirmação humana antes de qualquer encaminhamento.
- **Risco de alucinação:** o assistente de texto só responde com base em trechos citados das fontes do INPE, e a resposta é bloqueada se trouxer número fora do contexto ou citação inválida (ver seção 5.3 do relatório de Generative AI). Ainda assim, o teste de ponta a ponta mediu 4 respostas incorretas em 34 que passaram pela verificação sem serem bloqueadas (seção 6.4 do mesmo relatório), a verificação confere citação e número, não se o fato citado realmente responde à pergunta. Por isso as fontes são sempre mostradas junto da resposta, para o cidadão conferir.
- **Risco de viés:** o classificador de imagem não foi testado com imagens de vegetação brasileira (ver `visao/docs/relatorio_visao.md`, seção 7).
- **O que a solução não faz:** não substitui o BDQueimadas do INPE nem os canais oficiais de emergência (Bombeiros, Defesa Civil); não decide sozinha se uma equipe deve ser acionada; não guarda dados pessoais do cidadão (CPF, e-mail e telefone são mascarados antes de qualquer uso ou registro, ver `corpus/limpeza.py`).

## 5. Evidências de validação

### (a) Teste com pessoas do público-alvo

*Pendente.* O grupo ainda vai rodar um teste curto com ao menos 3 pessoas (moradores de área rural ou próxima a vegetação, ou pessoas próximas a esse público), pedindo para: (1) relatar uma dúvida sobre queimadas na aba "Relatar/Perguntar"; (2) enviar uma imagem de satélite na aba "Verificar imagem"; (3) dizer se entenderam o resultado sem ajuda. As observações e o ajuste feito a partir do feedback devem ser registrados aqui antes da entrega final.

### (b) Casos de teste da IA

Estes três casos vêm de execuções reais do sistema (dois deles no teste completo do módulo de Generative AI, documentado em `genai/docs/relatorio_genai.md`, seção 6.4; o terceiro foi encontrado rodando esta própria interface de ponta a ponta):

| # | Entrada | Saída esperada | Saída obtida | Ajuste realizado |
| --- | --- | --- | --- | --- |
| 1 | Pergunta enviada pela interface com o Ollama fora do ar | Mensagem clara, sem termos técnicos, dizendo que o assistente está indisponível | O texto cru do erro de conexão (`HTTPConnectionPool(host='localhost', port=11434)... Connection refused`) aparecia na resposta mostrada ao cidadão | Corrigido em `backend/pipelines/rag.py`: quando o motivo é `erro_llm`, o texto é trocado por uma mensagem fixa antes de sair da API; teste automatizado adicionado (`test_perguntar_nao_vaza_erro_tecnico_do_llm_no_texto`) |
| 2 | "Me passa uma receita de bolo de chocolate." (fora do escopo) | Recusa educada, sem chamar o modelo | Abstenção correta, sem chamar o LLM (confiança de busca 0,136, abaixo do limiar de 0,50) | Nenhum ajuste necessário, confirma que o limiar de evidência calibrado na avaliação do RAG também funciona para perguntas totalmente fora do tema |
| 3 | "Cada ponto no mapa quer dizer uma queimada?" | "Não, a relação não é direta: um foco pode ter várias frentes de fogo e uma queimada grande pode gerar vários focos." | O sistema respondeu o oposto do esperado ("cada ponto corresponde a uma queimada") | Nenhum ajuste de modelo ainda (limitação conhecida do modelo local de 3B, documentada no relatório de Generative AI); mitigação já em vigor: a resposta sempre vem acompanhada das fontes citadas, para o cidadão conferir, e o painel marca essa interação como merecendo atenção |

## 6. Como rodar

### Local, sem Docker (um terminal só)

```bash
cd frontend_ia
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
pip install -r backend/requirements.txt -r frontend/requirements.txt -r ../requirements.txt -r ../visao/requirements.txt
python app.py
```

`app.py` sobe o back-end (FastAPI) em segundo plano, espera ele responder e só então abre o front-end (Gradio), um único comando, uma única janela para fechar no final. Abra <http://localhost:7860>.

Se preferir ver os logs do back-end e do front-end em janelas separadas (por exemplo, para depurar um erro só do back-end), a forma antiga com dois terminais continua funcionando:

```bash
# Terminal 1, back-end
uvicorn backend.main:app --reload --port 8000

# Terminal 2, front-end
python -m frontend.app
```

Nos dois casos: o Ollama (`qwen2.5:3b`) precisa estar rodando na máquina para as abas de pergunta (texto e voz) responderem; o modelo de visão treinado (arquivo `.keras`) precisa estar no caminho (absoluto) configurado em `visao/.env` para a aba de imagem funcionar, sem eles, a interface continua abrindo e mostra uma mensagem clara de indisponibilidade, em vez de travar. A aba de voz também depende do `faster-whisper` e do `edge-tts` instalados (já vêm no `requirements.txt` da raiz do projeto).

### Com Docker

```bash
cd frontend_ia
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

Front-end em <http://localhost:7860>, back-end em <http://localhost:8000/docs>. O Ollama continua rodando na máquina do usuário (fora do Docker); o `docker-compose.yml` já aponta o back-end para `host.docker.internal:11434`.

> **Nota sobre este ambiente de desenvolvimento:** o `docker compose build` foi testado e a sintaxe do `docker-compose.yml` foi validada (`docker compose config`); a etapa de instalação de pacotes do sistema operacional dentro da imagem não pôde ser concluída neste ambiente de nuvem porque ele não tem acesso à internet dentro do container Docker (mesma restrição de rede que já afeta o Ollama e o Hugging Face neste projeto). O build completo deve ser confirmado na máquina do usuário, que tem acesso normal à internet.

## 7. Testes automatizados

16 testes (`pytest`), todos com os pipelines de IA simulados (monkeypatch), não precisam do Ollama nem do modelo de visão treinado:

```bash
cd frontend_ia
python -m pytest backend/tests frontend/tests -q
```

| Onde | O que cobre |
| --- | --- |
| `backend/tests/test_api.py` (13) | Saúde da API, pergunta com sucesso, validação de entrada, erro do LLM sem vazar detalhe técnico, pergunta por voz com sucesso, extensão de áudio inválida, erro de STT/TTS sem vazar detalhe técnico, classificação de imagem com sucesso, extensão inválida, modelo ausente, CORS |
| `frontend/tests/test_frontend.py` (7) | Estado (histórico, imutabilidade, avaliação humana), componentes de UI (cores/ícones/palavra, faixas de confiança), tradução de erros de rede do cliente HTTP |

## 8. Estrutura

```
frontend_ia/
├── backend/            FastAPI: routers/ (endpoints), schemas/ (Pydantic),
│                        pipelines/ (rag.py, voz.py, imagem.py, ligam aos módulos
│                        de IA), providers/ (sys.path)
├── frontend/           Gradio: features/ (telas: chat, voz, imagem, painel),
│                        ui/ (componentes reutilizáveis), state/ (histórico da
│                        sessão), providers/ (cliente HTTP)
└── docker-compose.yml
```

## 9. Vídeo da demonstração

Vídeo mostrando o front-end funcionando, de ponta a ponta.

Link: https://www.youtube.com/watch?v=GBvSY4OL7-Y
