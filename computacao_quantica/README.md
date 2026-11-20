# Sentinela do Território, Computação Quântica & IA

**Integrantes:** GEANDRO (RM 562316) · LUCAS VERO (RM 564202) · ROBERTO EDUARDO (RM 564537)

Global Solution CitizenTech. Disciplina: Computação Quântica & IA.

Esta disciplina não pede código nem simulação, pede uma análise de viabilidade: identificar um gargalo real do protótipo, escolher a capacidade quântica que o atacaria, e construir um roadmap realista (IA clássica hoje → quântico no futuro → benefício esperado), com ética, LGPD e ODS avaliados ao longo do roadmap.

## Resumo

- **Gargalo escolhido:** alocação de equipes de campo (Bombeiros, Defesa Civil) e suas rotas quando muitos relatos de prioridade ALTA chegam ao mesmo tempo (uma "rajada" de ocorrências), hoje, o RPA (`rpa/regras.py`) só prioriza um relato por vez, sem decidir a melhor distribuição entre várias ocorrências simultâneas e um número limitado de equipes.
- **Capacidade quântica escolhida:** otimização combinatória (recozimento quântico / QAOA), para esse problema de alocação com restrições.
- **Estado real da tecnologia (2024–2026):** pilotos em empresas de logística (D-Wave/Pattison, IonQ/Einride, Telefónica/Würth), sem vantagem quântica comprovada ainda sobre solvers clássicos bem ajustados.
- **Recomendação do roadmap:** investir primeiro num solver clássico de otimização (ganho real, disponível hoje); tratar o quântico como capacidade a monitorar, condicionada a custo, LGPD (dados de localização trafegando para provedores de nuvem quântica estrangeiros) e acesso equitativo (ODS 10).

A análise completa, com as fontes consultadas, a tabela do roadmap e a discussão de ética/LGPD/ODS, está em [`docs/relatorio_quantica.md`](docs/relatorio_quantica.md) / [`docs/relatorio_quantica.pdf`](docs/relatorio_quantica.pdf).

## Como está organizado

```
computacao_quantica/
├── README.md
└── docs/
    ├── relatorio_quantica.md
    └── relatorio_quantica.pdf
```
