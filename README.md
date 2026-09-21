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

## 🧠 Armadilhas de Dados, "Besteiras" & Lições de Engenharia (O que deu errado e como foi corrigido)

Projetos reais de dados nunca são uma linha reta. Abaixo estão documentadas as principais armadilhas, erros de interpretação e desafios técnicos encontrados durante o desenvolvimento:

### 1. A Pegadinha da Escala Monetária da CVM (Vivara com 921 bilhões de lucro?!)
* **O Erro:** Na CVM, quase todas as empresas reportam em milhares de reais (`ESCALA_MOEDA == 'MIL'`). Ao converter para bilhões, dividimos por 1.000.000. Porém, a **Vivara (`VIVA3.SA`)** e a **Metisa (`MTSA4.SA`)** reportaram seus demonstrativos em **unidades** (`ESCALA_MOEDA == 'UNIDADE'`)!
* **A Consequência:** A Vivara aparecia no ranking com **R$ 921 bilhões de lucro líquido** e R$ 2 trilhões de patrimônio (mais que a Petrobras e a Vale juntas!).
* **A Solução:** Criação de um tratamento específico para padronizar as empresas que reportaram em unidades, dividindo seus valores por 1.000 para equipará-las à escala das demais.

### 2. O Bug da "Divisão Infinita" no Jupyter (Falta de Idempotência)
* **O Erro:** No início, escrevi uma célula no notebook assim: `df['LUCRO'] = df['LUCRO'] / 1000`.
* **A Consequência:** Se você rodar a célula uma vez, divide por 1.000. Se rodar de novo para testar outra coisa, divide por mais 1.000 (virou 1 milhão). No terceiro clique, os lucros viraram centavos!
* **A Solução:** Tornar as transformações **idempotentes** usando travas lógicas condicionais (ex: `filtro = df['TICKER'].isin(['VIVA3.SA']) & (df['LUCRO_LIQUIDO_BI'] > 10)`), garantindo que a divisão só ocorra se o dado ainda estiver na escala errada.

### 3. O Paradoxo do ROE Positivo em Empresas Falidas (Americanas 2022)
* **A Armadilha Matemática:** O ROE é calculado como `Lucro Líquido / Patrimônio Líquido`. Se a empresa tem prejuízo (-R$ 5 bi) e patrimônio negativo (-R$ 10 bi), a regra matemática `menos com menos dá mais` resulta em um **ROE positivo de +50%**!
* **A Consequência:** Empresas destruindo valor e à beira da recuperação judicial apareciam no topo dos rankings de rentabilidade.
* **A Solução:** Criação da flag booleana `ROE_ENGANOSO = (LUCRO < 0) & (PL < 0)`. Toda linha nessa condição foi devidamente sinalizada e filtrada das análises de performance.

### 4. O Código de Conta que Engana (`CD_CONTA` 2.03)
* **O Erro:** Enquanto o Lucro Líquido possui código padronizado estável (`CD_CONTA == '3.11'`), o código de Patrimônio Líquido muda dependendo do plano de contas de cada empresa (o código `2.03` em algumas empresas era "Provisões" ou "Passivos Financeiros").
* **A Solução:** O filtro de PL precisou ser feito pela descrição exata (`DS_CONTA == 'Patrimônio Líquido Consolidado'`) combinado com `ORDEM_EXERC == 'ÚLTIMO'`, já que cada arquivo anual DFP repete o exercício anterior para comparação.

### 5. O Filtro de Materialidade (Dividir por quase zero gera ROE de 10.000%)
* **O Erro:** Empresas com Patrimônio Líquido ínfimo (ex: R$ 50 mil de PL) que tinham um lucro de R$ 5 milhões geravam um ROE distorcido de 10.000%.
* **A Solução:** Aplicação de piso de materialidade: empresas com $|PL| < \text{R\$} 10 \text{ milhões}$ foram excluídas dos rankings comparativos.

### 6. Previsão Multiclasse Direta vs Dupla Classificação Binária
* **A Tentativa:** No Machine Learning inicial, tentei treinar um classificador para prever diretamente os 4 cenários (`Crescente`, `Decrescente`, `Oportunidade`, `Especulação`).
* **O Problema:** Como tínhamos ~116 observações anuais válidas, dividir os dados em 4 classes pequenas fez o modelo ter pouquíssima amostra por classe, batendo apenas ~31% de acurácia (pouco melhor que um chute cego de 25%).
* **A Virada de Chave:** Em vez de 1 modelo de 4 classes, treinei dois modelos binários independentes com Random Forest:
  1. `ROE_SOBE` (0 ou 1)
  2. `ACAO_SOBE` (0 ou 1)
  E depois combinei os sinais através de lógica de negócios.

### 7. A "Cegueira" Microeconômica vs O Choque da Selic
* **O Mistério:** Inicialmente, o modelo de Machine Learning utilizava apenas dados contábeis da empresa (Lucro, PL, ROE, Cluster). A acurácia para prever se a ação subiria não passava de **51.72%** (uma moeda).
* **O Diagnóstico:** Entre 2021 e 2023, o Brasil viveu um choque violento de juros: a taxa Selic saltou de **2% para 13.75% a.a.** Com o juro a quase 14%, o dinheiro migrou para a Renda Fixa e a bolsa inteira caiu. Uma empresa excelente podia aumentar o ROE e lucrar mais, mas sua ação caía mesmo assim pela maré macroeconômica.
* **O Resultado:** Ao enriquecer o dataset com variáveis macroeconômicas brasileiras (`SELIC_ANO_%`, `VAR_SELIC_PP`, `IPCA_ANO_%`, `IBOV_RETORNO_%`, `DOLAR_VAR_%`), o modelo finalmente entendeu o regime de mercado:
  * Acurácia da Ação saltou de **51.72% para 82.76%** (+31.04 p.p.)!
  * Acerto do Cenário Combinado quase dobrou: de **31.03% para 55.17%**!

---

## 📌 Estrutura dos Notebooks

| Notebook | Objetivo Principal | Principais Técnicas |
| :--- | :--- | :--- |
| **01 a 05** | Extração CVM (DRE/BPP), saneamento de dados e SQL | Pandas, SQLite, tratamento de escala e regras contábeis |
| **06** | Enriquecimento de Mercado | `yfinance`, download de cotações B3, cálculo de retornos e correção de anomalia de moeda (Vivara/Metisa) |
| **07** | Agrupamento Não Supervisionado | `K-Means`, `StandardScaler`, Método do Cotovelo (Elbow) e Silhouette Score ($k=4$) |
| **08** | Modelagem Preditiva com IA | `RandomForestClassifier`, Engenharia de Features Macroeconômicas (Selic, Ibov, IPCA, Dólar) |
| **app.py** | Produto Final / Web App | `Streamlit`, `Plotly`, `@st.cache_data`, `@st.cache_resource` |

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