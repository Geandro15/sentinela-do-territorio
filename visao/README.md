# Visão Computacional, Sentinela do Território

**Integrantes:** GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

Módulo de Visão Computacional do projeto **Sentinela do Território** (Global Solution CitizenTech). Classifica imagens de satélite em duas classes, "com incêndio" e "sem incêndio", com um modelo pré-treinado (MobileNetV2) e transferência de aprendizado.

Dataset: [Wildfire Prediction Dataset](https://www.kaggle.com/datasets/abdelghaniaaba/wildfire-prediction-dataset), do Kaggle.

## Resultados

Modelo MobileNetV2, avaliado em 6.299 imagens de teste:

| Métrica | Valor |
| --- | --- |
| Acurácia | 0,967 |
| Precisão | 0,978 |
| Recall | 0,961 |
| F1-score | 0,970 |
| Falsos negativos | 136 |
| Falsos positivos | 74 |

A análise completa está em `docs/relatorio_visao.pdf`.

## O que tem nesta pasta

```
visao/
├── notebooks/
│   └── visao_computacional_sentinela.ipynb   # notebook do Colab
├── modelos/
│   └── queimada_mobilenet_v2.keras           # modelo treinado
├── inferencia/
│   ├── config.py                             # configuração (.env)
│   ├── classificador.py                      # carrega o modelo e classifica uma imagem
│   └── aba_fiscalizacao.py                   # aba opcional de Gradio (envio de foto)
├── tests/
│   └── test_classificador.py                 # 5 testes automatizados
├── docs/
│   ├── relatorio_visao.md
│   └── relatorio_visao.pdf
├── requirements.txt
└── README.md
```

## Como rodar o notebook

O trabalho da disciplina é individual: cada integrante entrega o seu notebook rodado no Google Colab.

1. Abra `notebooks/visao_computacional_sentinela.ipynb` no [Google Colab](https://colab.research.google.com/) (Arquivo → Fazer upload de notebook).
2. Em **Ambiente de execução → Alterar o tipo de ambiente de execução**, escolha **GPU (T4)**.
3. Gere um token no Kaggle (Settings → API → Generate New Token) e guarde nos **Secrets** do Colab (ícone de chave), com o nome `KAGGLE_API_TOKEN` e o acesso do notebook ativado. O token não deve ser escrito no notebook.
4. Na segunda célula de código, a variável `MODELO` define o modelo pré-treinado: `mobilenet_v2`, `efficientnet_b0` ou `resnet50`.
5. Rode as células em ordem, das seções 1 a 13. O treino leva cerca de 15 minutos com GPU.
6. Ao final, o notebook baixa o arquivo `.keras` treinado.

As seções "Extensão para a cidade" e "14. Comparação dos três modelos" são opcionais e não foram executadas nesta entrega.

## Como usar o modelo treinado

```bash
cd visao
pip install -r requirements.txt
python -m inferencia.classificador caminho/da/imagem.jpg --modelo modelos/queimada_mobilenet_v2.keras
```

O modelo treinado fica em `visao/modelos/queimada_mobilenet_v2.keras`. Na interface, o caminho vem da variável `VISAO_MODELO_QUEIMADA` do `.env`.

Para mostrar a classificação na interface do assistente de voz, adicione uma aba no `app.py`:

```python
from visao.inferencia.aba_fiscalizacao import construir_aba_fiscalizacao

with gr.Tab("Fiscalização (foto)"):
    construir_aba_fiscalizacao()
```

Cada sugestão do modelo vai para uma fila de revisão (`logs/fila_revisao_visao.csv`), para um gestor confirmar. Nenhuma classificação aciona algo por conta própria. Essa aba ainda não foi testada junto com o `app.py`.

## Testes automatizados

Os testes usam um modelo pequeno de teste e não precisam do modelo treinado nem de GPU.

```bash
cd visao
pip install -r requirements.txt
python -m pytest -q
```

Resultado esperado: `5 passed`.

## Decisões técnicas

- **Transferência de aprendizado**, e não treino do zero, como pede o enunciado.
- **MobileNetV2**, por ser leve: 2,26 milhões de parâmetros, o que permite usar o modelo em servidores simples.
- **Camadas pré-treinadas congeladas**: só a nova camada de saída é treinada.
- **Confirmação humana sempre**: o modelo sugere, e um gestor decide.

## Limitações

- O recall de 0,961 significa que cerca de 4 em cada 100 áreas com incêndio não seriam sinalizadas.
- Parte dos erros vem da base: o rótulo indica a região do incêndio, e não fogo visível na imagem.
- O tempo de classificação (11,1 ms por imagem) foi medido em GPU. O tempo em CPU não foi medido.
- O modelo não foi testado com imagens de vegetação brasileira.
- A extensão para danos em construções não foi treinada.

## Vídeo da demonstração

Vídeo mostrando o modelo de visão computacional funcionando.

Link: https://www.youtube.com/watch?v=Mbl4AjN_FjA
