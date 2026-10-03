# Contributing to Empresas-B3-analise-de-dados

Obrigado por considerar contribuir! 📊

## Como contribuir

1. **Fork** o repositório
2. Crie uma branch: `git checkout -b feat/minha-feature` ou `fix/meu-fix`
3. Faça suas alterações com commits semânticos (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
4. Rode os testes localmente: `pytest`
5. Abra um **Pull Request** para `main`

## Estrutura do projeto

```
├── src/                    # Código reutilizável (módulos Python)
│   ├── data_pipeline.py    # ETL: CVM → SQLite → features
│   ├── modeling.py         # K-Means, Random Forest, feature engineering
│   └── visualization.py    # Plotly charts, dashboard components
├── notebook/               # Exploração e prototipação (Jupyter)
├── app.py                  # Streamlit dashboard (produção)
├── data/                   # Dados processados (CSV/Parquet)
└── assets/                 # Logo, favicon, imagens estáticas
```

## Padrões de código

- **Lint:** `ruff check src/ notebook/`
- **Testes:** `pytest --cov=src`
- **Type hints:** preferidos em código novo
- **Docstrings:** estilo Google/NumPy para funções públicas

## Reportando bugs / sugerindo features

- Abra uma **Issue** com template (Bug Report / Feature Request)
- Inclua: passos para reproduzir, comportamento esperado, logs/erros, ambiente

## Código de conduta

Este projeto segue o [Contributor Covenant](CODE_OF_CONDUCT.md). Ao participar, você concorda em manter um ambiente respeitoso e inclusivo.

## Dúvidas?

Abra uma Issue com label `question` ou me chame no LinkedIn: [ghmendes02](https://linkedin.com/in/ghmendes02)