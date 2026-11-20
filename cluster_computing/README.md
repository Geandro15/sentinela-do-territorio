# Sentinela do Território, Cluster Computing, Computação Neuromórfica e Supercomputadores

**Integrantes:** GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

Global Solution CitizenTech. Disciplina: Cluster Computing, Computação Neuromórfica e Supercomputadores.

Esta disciplina não pede código nem integração com o protótipo, pede uma simulação de infraestrutura no simulador **iSPD**, comparando duas configurações de cluster para uma tarefa real do Sentinela do Território.

## O que foi simulado

**Tarefa escolhida:** a análise de um trecho de áudio recebido (reconhecimento de fala + classificação "aviso de incêndio ou não"), repetida a cada trecho e independente entre si, por isso pode ser distribuída entre workers. Em períodos de queimada, esses áudios chegam em rajada, e é esse pico de demanda que a simulação investiga.

**Comparação:** o mesmo cluster (mesma carga, mesma capacidade por worker, mesmo escalonador Round Robin, mesma banda e latência), variando só o número de workers, 2 (cenário A) e 4 (cenário B).

| Indicador | 2 workers (A) | 4 workers (B) |
| --- | --- | --- |
| Total Simulated Time (s) | 484,100 | 338,524 |
| Tarefas por worker | 200 | 100 |
| Ociosidade dos recursos de processamento (%) | 0,85 | 29,10 |

**Resultado:** dobrar os workers reduziu o tempo em 30,1% (bem abaixo do ganho ideal de 50%), porque o envio dos áudios pelo mestre (comunicação) não escala com o número de workers, no cenário de 4 workers, eles ficam ociosos quase 30% do tempo esperando os dados chegarem. A análise completa, com as justificativas dos parâmetros, as capturas de tela e a discussão do gargalo, está em [`docs/relatorio_cluster.pdf`](docs/relatorio_cluster.pdf).

## Como está organizado

```
cluster_computing/
├── README.md
├── docs/
│   └── relatorio_cluster.pdf   # relatório completo (parâmetros, resultados, discussão, anexo)
└── ispd/
    ├── cenario_A.imsx          # 2 workers, abrir no iSPD para conferir/reproduzir
    └── cenario_B.imsx          # 4 workers
```

## Como reproduzir

1. Baixe o [iSPD](https://sourceforge.net/projects/ispd1/) (gratuito).
2. Abra `ispd/cenario_A.imsx` ou `ispd/cenario_B.imsx` no iSPD.
3. Rode a simulação (Simulate) e confira a aba **Global** da janela de resultados: o `Total Simulated Time` deve bater com a tabela acima (484,100 s para o cenário A, 338,524 s para o B).

## Nota de correção

Ao organizar esta entrega, percebemos que o arquivo `cenario_A.imsx` recebido estava salvo com `nodes="4"` no XML (igual ao cenário B), em vez dos 2 workers usados para gerar o resultado reportado (484,100 s e 200 tarefas por worker só fecham a conta com 2 workers, não com 4). Corrigimos o arquivo para `nodes="2"`, a única mudança que o próprio relatório diz ter feito entre os dois cenários, para que ele reproduza de fato o resultado do cenário A. Vale abrir o arquivo corrigido no iSPD antes da entrega final para confirmar que o resultado bate com a tabela do relatório.
