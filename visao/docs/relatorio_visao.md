---
title: "Sentinela do Território: classificação de imagens de satélite"
subtitle: "Global Solution CitizenTech. Visão Computacional"
author:
  - "GEANDRO (RM 562316)"
  - "LUCAS VERO (RM 564202)"
  - "ROBERTO EDUARDO (RM 564537)"
lang: pt-BR
---

# 1. Problema e público beneficiado

O projeto Sentinela do Território recebe relatos de cidadãos, por voz, sobre riscos no território. Um relato pode estar errado, exagerado ou já resolvido. A Visão Computacional dá uma segunda fonte de evidência, independente do relato: uma imagem de satélite da região é classificada como "com incêndio" ou "sem incêndio" antes de uma equipe ser acionada.

Imagens de satélite cobrem grandes áreas de forma rápida e repetida, o que ajuda a monitorar queimadas, áreas de risco e regiões de preservação onde não há ninguém para avisar. Um classificador automático permite priorizar as áreas que merecem verificação humana, em ações de prevenção, fiscalização e resposta rápida.

**Público beneficiado:** moradores de áreas rurais próximas à vegetação e os gestores públicos (Defesa Civil, prefeitura) que recebem os alertas com uma validação adicional.

**ODS:** 15 (Vida Terrestre), pela proteção de áreas de vegetação, e 11 (Cidades e Comunidades Sustentáveis), pela resposta mais rápida a riscos.

# 2. Base de dados

Foi usado o Wildfire Prediction Dataset, do Kaggle, indicado no enunciado. As imagens de satélite têm cerca de 350×350 pixels e já vêm separadas em treino, validação e teste.

| Conjunto | Sem incêndio (`nowildfire`) | Com incêndio (`wildfire`) | Total |
| --- | --- | --- | --- |
| Treino | 14.500 | 15.750 | 30.250 |
| Validação | 2.820 | 3.480 | 6.300 |
| Teste | 2.820 | 3.480 | 6.300 |

Antes do treino, o notebook verifica todas as imagens e remove as que não abrem. Foram removidas 2 imagens corrompidas: 1 do treino e 1 do teste. Sem essa etapa, o treinamento parava com erro na leitura do arquivo.

Ao olhar exemplos das duas classes, não aparecem fogo nem fumaça visíveis nas imagens. As diferenças são de padrão de vegetação e de ocupação do solo.

# 3. Arquitetura e metodologia

Foi usada transferência de aprendizado. O MobileNetV2, pré-treinado na ImageNet, entra sem a camada de classificação original e com os pesos congelados. Sobre ele foi adicionada uma nova saída: média global, dropout de 0,3 e uma camada densa com uma saída sigmoide, que indica a probabilidade de incêndio.

| Item | Valor |
| --- | --- |
| Modelo pré-treinado | MobileNetV2 (ImageNet) |
| Parâmetros | 2.259.265 no total, 1.281 treináveis |
| Pré-processamento | redimensionamento para 224×224 e normalização dos pixels para o intervalo de 0 a 1 |
| Treino | 15 épocas, com parada antecipada (paciência de 3 épocas) |
| Ambiente | Google Colab com GPU T4 |
| Tempo de treino | cerca de 15 minutos (de 50 a 109 segundos por época) |

O conjunto de teste foi usado só na avaliação final.

# 4. Resultados

| Métrica | Valor |
| --- | --- |
| Acurácia | 0,967 |
| Precisão | 0,978 |
| Recall | 0,961 |
| F1-score | 0,970 |

Matriz de confusão no conjunto de teste (6.299 imagens):

| | Previsto: sem incêndio | Previsto: com incêndio |
| --- | --- | --- |
| **Real: sem incêndio** | 2.746 | 74 |
| **Real: com incêndio** | 136 | 3.343 |

## 4.1 Discussão dos falsos negativos

O falso negativo, quando o modelo diz "sem incêndio" e há incêndio, é o erro mais grave neste contexto, porque uma área de risco deixa de ser identificada. O falso positivo custa menos: gera uma verificação humana desnecessária.

O modelo teve 136 falsos negativos, 3,9% das 3.479 imagens com incêndio, contra 74 falsos positivos. Nos três exemplos de erro observados, nenhuma imagem mostra fogo, fumaça ou área queimada: aparecem um terreno exposto, uma plantação e um bairro residencial, todos com vegetação verde. Isso sugere que o rótulo "wildfire" do dataset se refere à região onde houve incêndio, e não a uma evidência visível na cena. Parte do erro, portanto, vem da própria base, e não só do modelo.

Por esse motivo, o recall é a métrica mais importante para este problema, e o resultado de 0,961 indica que cerca de 4 em cada 100 áreas com incêndio passariam sem alerta.

## 4.2 Tempo de resposta

O tempo médio de classificação foi de 11,1 ms por imagem, medido na GPU T4 do Colab. O MobileNetV2 foi escolhido por ser leve, o que permite usá-lo em servidores simples. O tempo em CPU não foi medido.

# 5. Proposta de aplicação real

No Sentinela do Território, o classificador funciona como segunda confirmação: quando um cidadão relata uma queimada pelo assistente de voz, uma imagem de satélite da região passa pelo modelo. Se as duas fontes concordam, o alerta ganha prioridade na fila do gestor.

A mesma técnica pode alimentar um painel de monitoramento periódico de áreas de preservação, com integração a mapas de focos de queimadas, como o BDQueimadas do INPE.

Nenhuma classificação aciona uma equipe por conta própria. O módulo `inferencia/` do projeto carrega o modelo treinado e registra cada sugestão em uma fila de revisão, para um gestor confirmar.

A extensão para a cidade, que usaria a mesma técnica para detectar rachaduras em fotos de construções, está preparada no código, mas não foi treinada nem avaliada nesta entrega.

# 6. Testes automatizados

O módulo `inferencia/` tem 5 testes automatizados (`python -m pytest -q`), que usam um modelo pequeno de teste e não dependem do modelo treinado. Os 5 passaram.

| Caso de teste | O que verifica |
| --- | --- |
| Formato do resultado | classe, confiança de 0 a 1, alerta e aviso de confirmação humana |
| Reaproveitamento do modelo | o arquivo `.keras` não é recarregado a cada classificação |
| Modelo ausente | a mensagem de erro diz onde colocar o arquivo treinado |
| Imagem ausente | a mensagem de erro indica o caminho que faltou |
| Limiar de decisão | mudar o limiar muda a classe prevista |

# 7. Ética e limites

- O protótipo é educacional. Ele não substitui sistemas oficiais de monitoramento de queimadas, como os do INPE.
- Toda sugestão do modelo passa por revisão humana antes de qualquer ação.
- Os falsos negativos são o risco mais sério deste módulo e estão declarados na seção 4.1.
- O desempenho do modelo em imagens de vegetação brasileira não foi testado.

# 8. Conclusão

O MobileNetV2 com transferência de aprendizado atingiu 96,7% de acurácia, 97,8% de precisão e 96,1% de recall no conjunto de teste, treinando só a nova camada de saída em cerca de 15 minutos. O resultado mostra que um modelo pré-treinado e leve resolve bem a classificação entre áreas com e sem incêndio nesta base.

A principal limitação está nos 136 falsos negativos. A análise dos exemplos indica que parte deles vem da forma como a base foi rotulada, por região e não por fogo visível na imagem. Por isso o modelo deve ser usado como evidência de apoio, junto com o relato do cidadão e os dados oficiais, e sempre com confirmação humana.

Os próximos passos são fazer o ajuste fino das últimas camadas da rede, hoje totalmente congelada, testar o modelo com imagens de vegetação brasileira e treinar a extensão para danos em construções.
