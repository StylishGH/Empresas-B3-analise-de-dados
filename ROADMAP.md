# 🗺️ Roadmap de Evolução: Análise de Empresas da B3

> **Filosofia:** Aprender na prática, passo a passo, entendendo cada linha de código e transformando este projeto de uma análise descritiva em um case completo de Ciência de Dados Financeiros.

---

## 📌 Status Atual do Projeto
- [x] **Notebook 01:** Coleta e exploração dos demonstrativos CVM (DFP 2021-2025).
- [x] **Notebook 02:** Limpeza e tratamento de inconsistências contábeis (Lucro Líquido e PL).
- [x] **Notebook 03:** Cálculo do indicador ROE (Return on Equity) por empresa e setor.
- [x] **Notebook 04:** Gráficos e exploração visual da rentabilidade.
- [x] **Notebook 05:** Modelagem relacional e queries analíticas com SQLite.

---

## 🎯 Fase 1: Enriquecimento com Dados de Mercado (`yfinance`)

**Objetivo:** Conectar a saúde contábil interna da empresa (CVM) com o que o mercado financeiro realmente precifica na bolsa.

### 📝 O que fazer no `06_mercado_yfinance.ipynb`:
1. **Instalar e importar a biblioteca:**
   - Instalar via terminal: `pip install yfinance`
   - Testar buscando uma empresa-âncora: `yf.Ticker("PETR4.SA").history(period="5y")`
2. **Mapeamento de Tickers:**
   - Criar uma tabela simples relacionando o nome/CNPJ da CVM com o código de negociação da B3 (ex: PETROBRAS -> `PETR4.SA`, VALE -> `VALE3.SA`, ITAÚ -> `ITUB4.SA`, WEG -> `WEGE3.SA`).
3. **Download Histórico:**
   - Baixar cotações de fechamento anual/mensal para as principais empresas analisadas no período 2021 a 2025.
4. **Cruzamento de Dados:**
   - Juntar em um único DataFrame: `Ano | Empresa | Setor | ROE | Lucro_Liquido | Cotacao_Final_Ano | Retorno_Anual_%`.

### 💡 Pergunta para responder com código:
> *"As empresas com maior ROE contábil na CVM realmente tiveram maior valorização das ações no período 2021-2025?"*

---

## 🤖 Fase 2: Machine Learning — Agrupamento de Empresas (K-Means)

**Objetivo:** Descobrir perfis reais de empresas na B3 com base em dados numéricos, sem depender apenas da classificação oficial de setores.

### 📝 O que fazer no `07_clustering_kmeans.ipynb`:
1. **Seleção de Variáveis (Features):**
   - Escolher métricas como: ROE médio, volatilidade do lucro, crescimento de patrimônio e retorno da ação.
2. **Pré-processamento (Essencial em ML):**
   - Tratar valores nulos / infinitos.
   - Normalizar/Padronizar os dados com `StandardScaler` do `sklearn.preprocessing` (o K-Means é sensível à escala dos dados!).
3. **Definição do Número de Grupos ($k$):**
   - Aplicar o **Método do Cotovelo (Elbow Method)** plotando a Inércia (`inertia_`) de 1 a 10 clusters.
   - Calcular o **Silhouette Score** para validar a qualidade do agrupamento.
4. **Treinamento e Interpretação:**
   - Treinar o modelo: `KMeans(n_clusters=k, random_state=42).fit(X_scaled)`
   - Atribuir o cluster de volta ao DataFrame: `df['Cluster'] = kmeans.labels_`
   - Analisar e nomear os clusters (Exemplo: *Cluster 0 = Alta rentabilidade e estabilidade*, *Cluster 1 = Empresas cíclicas*, *Cluster 2 = Alto risco / prejuízo recorrente*).
5. **Visualização:**
   - Gráficos de dispersão com `seaborn` ou `matplotlib` colorindo os pontos pelos clusters.

---

## 📈 Fase 3: Machine Learning — Modelo Preditivo de Risco / Queda de ROE

**Objetivo:** Treinar um modelo supervisionado para prever se uma empresa tende a piorar seus resultados no ano seguinte.

### 📝 O que fazer no `08_modelos_preditivos.ipynb`:
1. **Definição do Target (Alvo):**
   - Criar uma variável binária: `1` se o ROE do próximo ano caiu mais de 20% (ou ficou negativo), `0` se manteve/subiu.
2. **Divisão de Dados:**
   - Separar em Treino e Teste (`train_test_split`) ou por separação temporal (ex: treinar em 2021-2023 e testar em 2024-2025).
3. **Treinamento de Modelos:**
   - Começar com **Regressão Logística** (baseline simples e explicável).
   - Testar **Random Forest Classifier** (árvores de decisão).
4. **Avaliação das Métricas:**
   - Matriz de Confusão (`confusion_matrix`).
   - Precisão, Recall e F1-Score (`classification_report`).
   - Importância das Variáveis (`feature_importances_`) para ver quais dados mais influenciam o resultado.

---

## 🖥️ Fase 4: O "Substituto do Power BI" (Streamlit)

**Objetivo:** Transformar todos os seus notebooks em um produto web interativo e navegável que qualquer recrutador pode usar pelo celular ou navegador.

### 📝 O que fazer:
1. Aprender a base do **Streamlit** (bastam comandos como `st.title()`, `st.sidebar.selectbox()`, `st.dataframe()` e `st.pyplot()`).
2. Criar um arquivo `app.py`:
   - Barra lateral para o usuário escolher a empresa ou setor da B3.
   - Gráfico de histórico de ROE e cotações.
   - Aba para ver o cluster da empresa no modelo de Machine Learning.
3. Publicar gratuitamente no **Streamlit Community Cloud** e colocar o link no topo do seu `README.md`.

---

## 💼 Dicas para o GitHub & Currículo
- **Commits atômicos:** Sempre que concluir uma pequena etapa (ex: download do yfinance), faça um commit com mensagem clara (`git commit -m "feat: download e limpeza de dados do yfinance"`).
- **README visual:** Conforme gerar os gráficos da Fase 1 e 2, salve as imagens na pasta `reports/` ou `img/` e coloque prints no README.
- **Respeite o seu tempo:** O importante é entender o porquê de cada função, cada parâmetro do Scikit-Learn e cada tratamento de dados. Aprender de verdade é o que garante segurança em entrevistas técnicas!
