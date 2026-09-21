# 📊 Análise Fundamentalista, Mercado & Machine Learning na B3 (2021-2025)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
![Python](https://img.shields.io/badge/Python-3.14-blue.svg)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard%20Web-FF4B4B.svg)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75.svg)

> **Case completo de Ciência de Dados Financeiros:** Da coleta e saneamento contábil na CVM ao cruzamento com cotações da B3 (Yahoo Finance), agrupamento não supervisionado (K-Means), modelagem preditiva supervisionada com contexto macroeconômico (Random Forest) e deploy em aplicação web interativa com Streamlit.

---

## 🚀 Dashboard Interativo (Streamlit)

A aplicação web interativa reúne todo o pipeline do projeto em uma interface gráfica moderna:

* **📈 Raio-X Fundamentalista & Cotações:** Indicadores de ROE, Lucro Líquido, PL e gráfico com eixo duplo (Preço da Ação vs ROE) de 2021 a 2025.
* **🎯 Agrupamento Econômico (K-Means):** Mapa de dispersão interativo com todas as empresas da B3 classificadas em 4 clusters, destacando a empresa selecionada com uma estrela vermelha.
* **🤖 Simulador Preditivo com IA:** Simulador interativo onde o usuário ajusta as variáveis macroeconômicas (Selic, Ibovespa, Dólar, Inflação) e vê a IA estimar em tempo real a probabilidade de alta da ação e do ROE no ano seguinte.

### Como rodar localmente:
```bash
git clone https://github.com/StylishGH/Empresas-B3-analise-de-dados.git
cd Empresas-B3-analise-de-dados
pip install -r requirements.txt
python -m streamlit run app.py
```

---

## 📌 Estrutura dos Notebooks & Pipeline

| Notebook | Objetivo Principal | Principais Técnicas |
| :--- | :--- | :--- |
| **01 a 05** | Extração CVM (DRE/BPP), saneamento de dados e SQL | Pandas, SQLite, tratamento de escala e regras contábeis |
| **06** | Enriquecimento de Mercado | `yfinance`, download de cotações B3, cálculo de retornos e correção de anomalia de moeda (Vivara/Metisa) |
| **07** | Agrupamento Não Supervisionado | `K-Means`, `StandardScaler`, Método do Cotovelo (Elbow) e Silhouette Score ($k=4$) |
| **08** | Modelagem Preditiva com IA | `RandomForestClassifier`, Engenharia de Features Macroeconômicas (Selic, Ibov, IPCA, Dólar) |
| **app.py** | Produto Final / Web App | `Streamlit`, `Plotly`, `@st.cache_data`, `@st.cache_resource` |

---

## 🤖 Modelagem de Machine Learning

### 1. Agrupamento com K-Means ($k=4$)
As empresas foram agrupadas em 4 perfis econômicos distintos com base em ROE, Retorno da Ação, Lucro Líquido e Patrimônio Líquido:
* **Cluster 0 (Blue Chips & Sólidas):** Lucros consistentes, ROE médio de ~27% e retorno médio de +23% a.a. (ex: BB, Bradesco, Santander, Vivara).
* **Cluster 1 (Titãs da Bolsa):** Petrobras e Vale (escala de dezenas de bilhões de lucro).
* **Cluster 2 (Campeãs de Super ROE):** Altíssima eficiência de capital (WEG, Ambev, Sabesp) com ROE médio de ~79% e retorno de +17% a.a.
* **Cluster 3 (Em Queda / Crise):** Empresas que passaram por estresse operacional (Magalu, Hapvida, Cosan) com rentabilidade comprimida e retorno médio de -19% a.a.

### 2. Random Forest Classifier com Contexto Macroeconômico
O modelo prevê simultaneamente se o **ROE** e o **Preço da Ação** vão subir no ano seguinte, classificando a empresa em 4 quadrantes de decisão:
* 🟢 **Crescente:** ROE Sobe, Ação Sobe
* 🔵 **Oportunidade:** ROE Sobe, Ação Cai (fundamento melhora com desconto de mercado)
* 🟡 **Especulação:** ROE Cai, Ação Sobe
* 🔴 **Decrescente:** ROE Cai, Ação Cai

#### O Impacto das Métricas Macroeconômicas no Teste Out-of-Sample:
Ao incorporar variáveis de regime de mercado (Taxa Selic, Variação da Selic, IPCA, Retorno do Ibovespa e Variação do Dólar), o modelo deu um salto expressivo de performance:
* **Previsão da Ação (`ACAO_SOBE`):** subiu de 51.72% para **82.76%** (+31.04 p.p.)
* **Previsão do ROE (`ROE_SOBE`):** subiu de 51.72% para **62.07%** (+10.35 p.p.)
* **Acerto do Cenário Combinado:** subiu de 31.03% para **55.17%** (vs 25% do chute aleatório)

---

## 🛠️ Stack Técnica
* **Linguagem:** Python 3.14
* **Manipulação de Dados:** Pandas, NumPy, SQLite
* **Visualização:** Streamlit, Plotly Express & Graph Objects, Matplotlib, Seaborn
* **Machine Learning:** Scikit-Learn (Pipelines, StandardScaler, KMeans, RandomForestClassifier)
* **Mercado Financeiro:** Yahoo Finance (`yfinance`), CVM Dados Públicos

---

## 👤 Autor
Desenvolvido por **Guilherme** ([@StylishGH](https://github.com/StylishGH)).