# Assistente conversacional com RAG, Sentinela do Território

**Integrantes:** GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

Global Solution CitizenTech. Disciplina: Generative AI & Advanced Nets.

Assistente que responde dúvidas do cidadão sobre queimadas usando primeiro fontes oficiais do Programa Queimadas do INPE, mais um telefones de emergência fixos (Corpo de Bombeiros, Defesa Civil, `contatos_emergencia.py`, não depende de internet) e uma busca na web como segunda fonte quando nem o INPE nem os contatos fixos cobrem o assunto. Cada resposta mostra de onde veio a informação. Quando nenhuma das três cobre o assunto, o assistente diz que não encontrou.

## Como funciona

```
fontes do INPE -> ingestão -> chunking -> índice (BM25 + embeddings)
pergunta -> filtros de entrada -> busca local -> checagem de evidência
         -> (se faltar evidência ou a resposta não se sustentar) busca na web
         -> LLM -> verificação -> resposta com fontes
```

| Etapa | Arquivo | O que faz |
| --- | --- | --- |
| Coleta | `coleta.py` | baixa as fontes e registra URL e data de consulta em `fontes/fontes.csv` |
| Ingestão | `ingestao.py` | separa cada fonte em seções com metadados e remove frases com ordens ao modelo |
| Chunking | `chunking.py` | divide as seções em trechos (por estrutura ou por tamanho fixo) |
| Retriever | `retriever.py` | busca lexical (BM25), vetorial (embeddings) ou híbrida (RRF), sobre a base local do INPE |
| Contatos de emergência | `contatos_emergencia.py` | telefones fixos (Bombeiros 193, Defesa Civil 199), carregados junto da base local, não depende de internet |
| Busca na web | `busca_web.py` | terceira fonte (DuckDuckGo, gratuita, sem chave), usada só quando nem o INPE nem os contatos fixos cobrem a pergunta |
| Generator | `gerador.py` | prompt, chamada ao LLM e verificação da resposta, igual para trechos do INPE e da web |
| Assistente | `assistente_rag.py` | junta tudo, com as proteções e o registro das interações |
| Interface | `aba.py` | aba "Consulta às fontes (INPE e web)" do aplicativo |

## Base de conhecimento

Todas as fontes são do INPE, Programa Queimadas. A lista com data de consulta fica em `fontes/fontes.csv`.

| ID | Fonte | URL |
| --- | --- | --- |
| F1 | Perguntas Frequentes (FAQ) do Programa Queimadas | https://data.inpe.br/queimadas/faq/ |
| F2 | BDQueimadas | https://data.inpe.br/queimadas/bdqueimadas/ |
| F3 | Dados Abertos do Programa Queimadas | https://data.inpe.br/queimadas/dados-abertos/ |
| F4 | Boletim InfoQueima, apresentação | https://data.inpe.br/queimadas/boletim-infoqueima/ |
| F5 | InfoQueima, boletim de agosto de 2026 | https://dataserver-coids.inpe.br/queimadas/queimadas/Infoqueima/2026/2026_08_infoqueima.pdf |

A base tem 68 seções e cerca de 73 mil caracteres.

## Configuração escolhida

| Componente | Escolha |
| --- | --- |
| Chunking | por estrutura: uma pergunta do FAQ ou uma página do boletim; seções longas divididas em frases, até 900 caracteres, com uma frase de sobreposição e o título em cada trecho |
| Retriever | híbrido: BM25 + embeddings `paraphrase-multilingual-MiniLM-L12-v2` (fastembed, CPU), unidos por RRF; top-k = 4 |
| Evidência mínima | semelhança de cosseno de pelo menos 0,50 entre a pergunta e o melhor trecho |
| LLM | `qwen2.5:3b` no Ollama (local), temperatura 0,1 |
| Prompt | papel, regras, contexto numerado, formato e frase fixa de abstenção, em `gerador.py` |

As justificativas e os números estão em `docs/relatorio_genai.md`.

## Como rodar

Na pasta do projeto, com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
python -m genai.coleta        # opcional: baixa as fontes de novo e atualiza a data de consulta
python -m genai.ingestao      # gera genai/indice/secoes.jsonl
python -m genai.assistente_rag "O que é o satélite de referência?"
python app.py                 # aba "Consulta às fontes (INPE e web)"
```

O Ollama precisa estar aberto, com o modelo `qwen2.5:3b`. Na primeira execução, o modelo de embeddings (cerca de 220 MB) é baixado. A busca na web (`BUSCA_WEB_ATIVA=true` por padrão, em `.env.example`) exige internet; sem internet, ou se a biblioteca `ddgs` não estiver instalada, o assistente simplesmente não ganha essa segunda fonte e segue para a abstenção normal, nunca trava nem lança erro.

## Avaliação

```bash
python -m pytest -q tests/test_genai.py                         # 25 testes, sem LLM e sem internet (busca na web simulada)
python -m genai.avaliacao.avaliar_recuperacao                   # chunking e retriever, sem LLM
python -m genai.avaliacao.avaliar_geracao --modo controlado     # só o generator
python -m genai.avaliacao.avaliar_geracao --modo completo       # ponta a ponta
python -m genai.avaliacao.avaliar_seguranca --com-llm           # testes adversariais
```

Os resultados ficam em `avaliacao/resultados/`. As respostas dos modos `controlado` e `completo` recebem julgamento humano na coluna `julgamento`; depois, `--resumir <arquivo.csv>` calcula os totais.

## Proteções

1. CPF, e-mail e telefone da pergunta são mascarados antes de qualquer uso ou registro.
2. Pedidos para mudar as regras ou revelar o prompt recebem uma recusa fixa, sem chamar o LLM.
3. Sem evidência suficiente na busca local, o assistente tenta a busca na web antes de se abster; sem evidência em nenhuma das duas, se abstém sem chamar o LLM.
4. A resposta do LLM é verificada: sem citação válida, ou com número que não está nos trechos, ela é bloqueada, vale igual para trechos do INPE e da web.
5. Na ingestão dos documentos locais e em cada resultado da busca na web, frases com ordens ao modelo são removidas (`remover_injecao`).
6. Nenhuma chave fica no código. O registro (`logs/genai_interacoes.jsonl`) guarda a pergunta já mascarada e qual fonte respondeu (local ou web).
7. A busca na web nunca lança exceção: sem internet, sem a biblioteca `ddgs`, ou sem resultado, o assistente segue para a abstenção normal.

## Limitações

- A base local cobre o monitoramento de queimadas do INPE e os telefones de emergência fixos (`contatos_emergencia.py`). Perguntas fora disso tentam a busca na web (`busca_web.py`); sem resultado da web, a pergunta recebe abstenção.
- Os dois contatos de emergência (Bombeiros, Defesa Civil) compartilham palavras ("telefone", "emergência"); uma pergunta sobre só um dos dois pode trazer o outro no contexto também, e o modelo real precisa ser conferido para não confundir os dois números numa mesma resposta (`docs/relatorio_genai.md`, seção 4.7).
- A busca na web depende de internet e de um motor de busca de terceiros (DuckDuckGo): a qualidade da resposta varia com o que o motor retorna a cada pergunta, e não há como garantir, de antemão, quais páginas serão encontradas.
- O boletim da base local é o de agosto de 2026. Números de outros meses não estão disponíveis.
- Os limiares de evidência foram escolhidos com as mesmas perguntas usadas no teste.
- A verificação confere citações e números, mas não detecta uma frase errada sem números.
- O assistente é uma única instância compartilhada por todas as telas (menu, chat flutuante, voz) e por quem estiver usando o aplicativo ao mesmo tempo, não há conversa separada por usuário ou aba (detalhe e correção de um bug real encontrado nisso: `docs/relatorio_genai.md`, seção 4.5).
