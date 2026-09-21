import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="B3 Analytics & Machine Learning",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS (COM CACHE)
# ==============================================================================
@st.cache_data
def carregar_dados():
    # 1. Dados consolidados CVM + Cotações
    df = pd.read_csv("data/processed/dados_consolidados_b3.csv")
    
    # 2. Dados dos Clusters do K-Means
    df_clusters = pd.read_csv("data/processed/clusters_empresas.csv")
    
    # Garantir ordenação temporal por empresa
    df = df.sort_values(by=['TICKER', 'ANO']).reset_index(drop=True)
    
    # Calcular Retorno Anual da Cotação (%)
    df['RETORNO_ANO_%'] = df.groupby('TICKER')['COTACAO_FINAL_ANO'].pct_change() * 100
    
    # Merge com os clusters
    df = df.merge(df_clusters[['TICKER', 'CLUSTER', 'PERFIL']], on='TICKER', how='left')
    
    # 3. Tabela Macroeconômica Histórica
    dados_macro = {
        'ANO': [2021, 2022, 2023, 2024, 2025],
        'SELIC_ANO_%':     [9.25,  13.75, 11.75, 12.25, 14.00],
        'VAR_SELIC_PP':    [7.25,   4.50, -2.00,  0.50,  1.75],
        'IPCA_ANO_%':      [10.06,  5.79,  4.62,  4.83,  4.50],
        'IBOV_RETORNO_%':  [-11.93, 4.69, 22.28, -10.37, 0.00],
        'DOLAR_VAR_%':     [7.47,  -5.32, -8.08, 27.35,  2.00]
    }
    df_macro = pd.DataFrame(dados_macro)
    df = df.merge(df_macro, on='ANO', how='left')
    
    return df, df_clusters, df_macro

df_completo, df_clusters, df_macro = carregar_dados()

# ==============================================================================
# TREINAMENTO DOS MODELOS DE MACHINE LEARNING (COM CACHE)
# ==============================================================================
@st.cache_resource
def treinar_modelos(df):
    # Criar alvos para o próximo ano
    df_ml = df.copy()
    df_ml['ROE_PROX_ANO'] = df_ml.groupby('TICKER')['ROE'].shift(-1)
    df_ml['COTACAO_PROX_ANO'] = df_ml.groupby('TICKER')['COTACAO_FINAL_ANO'].shift(-1)
    
    df_ml = df_ml.dropna(subset=['ROE_PROX_ANO', 'COTACAO_PROX_ANO', 'RETORNO_ANO_%']).copy()
    
    df_ml['ROE_SOBE'] = (df_ml['ROE_PROX_ANO'] > df_ml['ROE']).astype(int)
    df_ml['ACAO_SOBE'] = (df_ml['COTACAO_PROX_ANO'] > df_ml['COTACAO_FINAL_ANO']).astype(int)
    
    # Dummies dos clusters
    df_ml = pd.get_dummies(df_ml, columns=['CLUSTER'], dtype=int)
    for c in ['CLUSTER_0.0', 'CLUSTER_1.0', 'CLUSTER_2.0', 'CLUSTER_3.0']:
        if c not in df_ml.columns:
            df_ml[c] = 0
            
    features = [
        'LUCRO_LIQUIDO_BI', 'PATRIMONIO_LIQUIDO_BI', 'ROE', 'RETORNO_ANO_%',
        'CLUSTER_0.0', 'CLUSTER_1.0', 'CLUSTER_2.0', 'CLUSTER_3.0',
        'SELIC_ANO_%', 'VAR_SELIC_PP', 'IPCA_ANO_%', 'IBOV_RETORNO_%', 'DOLAR_VAR_%'
    ]
    
    X = df_ml[features]
    y_roe = df_ml['ROE_SOBE']
    y_acao = df_ml['ACAO_SOBE']
    
    modelo_roe = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_split=5, random_state=42, class_weight='balanced'))
    ])
    modelo_roe.fit(X, y_roe)
    
    modelo_acao = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_split=5, random_state=42, class_weight='balanced'))
    ])
    modelo_acao.fit(X, y_acao)
    
    return modelo_roe, modelo_acao, features

modelo_roe, modelo_acao, features_ml = treinar_modelos(df_completo)

# ==============================================================================
# BARRA LATERAL (FILTROS)
# ==============================================================================
st.sidebar.title("🔍 Filtros de Análise")

# Filtro de Setor
setores = ["Todos"] + sorted(df_completo['SETOR'].dropna().unique().tolist())
setor_selecionado = st.sidebar.selectbox("Selecione o Setor:", setores)

if setor_selecionado != "Todos":
    df_filtrado_setor = df_completo[df_completo['SETOR'] == setor_selecionado]
else:
    df_filtrado_setor = df_completo

# Filtro de Empresa / Ticker
tickers_disponiveis = sorted(df_filtrado_setor['TICKER'].unique().tolist())
ticker_selecionado = st.sidebar.selectbox("Selecione a Empresa (Ticker):", tickers_disponiveis, index=0)

# Dados da empresa selecionada
df_empresa = df_completo[df_completo['TICKER'] == ticker_selecionado].sort_values(by='ANO')
nome_empresa = df_empresa['EMPRESA'].iloc[0]
setor_empresa = df_empresa['SETOR'].iloc[0]
perfil_empresa = df_empresa['PERFIL'].iloc[0]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Empresa:** {nome_empresa}")
st.sidebar.markdown(f"**Setor:** {setor_empresa}")
st.sidebar.markdown(f"**Perfil:** `{perfil_empresa}`")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Dica:** Navegue pelas abas ao lado para explorar o Raio-X Fundamentalista, os Clusters e o Simulador de IA!")

# ==============================================================================
# CABEÇALHO PRINCIPAL
# ==============================================================================
st.title("📊 Painel B3: Análise Fundamentalista & Machine Learning")
st.markdown(f"### Análise da empresa: **{nome_empresa}** (`{ticker_selecionado}`)")

# ==============================================================================
# ABAS DE NAVEGAÇÃO
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📈 Raio-X Fundamentalista & Mercado",
    "🎯 Agrupamento Econômico (K-Means)",
    "🤖 Simulador Preditivo de Cenários (IA)"
])

# ------------------------------------------------------------------------------
# ABA 1: RAIO-X FUNDAMENTALISTA & MERCADO
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Indicadores Recentes e Histórico")
    
    # Pegar último ano disponível da empresa
    ultimo_registro = df_empresa.iloc[-1]
    ano_ultimo = int(ultimo_registro['ANO'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        retorno = ultimo_registro['RETORNO_ANO_%']
        delta_str = f"{retorno:+.1f}% no ano" if pd.notnull(retorno) else "N/D"
        st.metric(
            label=f"Cotação ({ano_ultimo})",
            value=f"R$ {ultimo_registro['COTACAO_FINAL_ANO']:.2f}",
            delta=delta_str
        )
    with col2:
        roe_val = ultimo_registro['ROE'] * 100
        media_b3 = df_completo[df_completo['ANO'] == ano_ultimo]['ROE'].median() * 100
        delta_roe = roe_val - media_b3
        st.metric(
            label=f"ROE ({ano_ultimo})",
            value=f"{roe_val:.1f}%",
            delta=f"{delta_roe:+.1f}% vs Mediana B3"
        )
    with col3:
        st.metric(
            label=f"Lucro Líquido ({ano_ultimo})",
            value=f"R$ {ultimo_registro['LUCRO_LIQUIDO_BI']:.2f} Bi"
        )
    with col4:
        st.metric(
            label=f"Patrimônio Líquido ({ano_ultimo})",
            value=f"R$ {ultimo_registro['PATRIMONIO_LIQUIDO_BI']:.2f} Bi"
        )
    
    st.markdown("---")
    
    # Gráfico Duplo: Cotação vs ROE ao longo do tempo
    st.markdown("#### Evolução Temporal: Cotação de Fechamento vs ROE")
    
    fig_hist = go.Figure()
    
    # Linha da Cotação
    fig_hist.add_trace(go.Scatter(
        x=df_empresa['ANO'],
        y=df_empresa['COTACAO_FINAL_ANO'],
        name="Cotação (R$)",
        mode="lines+markers",
        line=dict(color="#2ca02c", width=3),
        marker=dict(size=8),
        yaxis="y1"
    ))
    
    # Linha/Barras do ROE
    fig_hist.add_trace(go.Bar(
        x=df_empresa['ANO'],
        y=df_empresa['ROE'] * 100,
        name="ROE (%)",
        marker=dict(color="#1f77b4", opacity=0.4),
        yaxis="y2"
    ))
    
    fig_hist.update_layout(
        title=f"Histórico Anual de Cotação e Rentabilidade ({ticker_selecionado})",
        xaxis=dict(title="Ano", tickmode='linear', dtick=1),
        yaxis=dict(title="Cotação (R$)", side="left", showgrid=False),
        yaxis2=dict(title="ROE (%)", side="right", overlaying="y", showgrid=True),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified",
        height=450
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Tabela detalhada
    with st.expander("Ver Tabela de Dados Históricos"):
        st.dataframe(
            df_empresa[['ANO', 'LUCRO_LIQUIDO_BI', 'PATRIMONIO_LIQUIDO_BI', 'ROE', 'COTACAO_FINAL_ANO', 'RETORNO_ANO_%']]
            .style.format({
                'LUCRO_LIQUIDO_BI': 'R$ {:.2f} Bi',
                'PATRIMONIO_LIQUIDO_BI': 'R$ {:.2f} Bi',
                'ROE': '{:.1%}',
                'COTACAO_FINAL_ANO': 'R$ {:.2f}',
                'RETORNO_ANO_%': '{:+.1f}%'
            }),
            use_container_width=True
        )

# ------------------------------------------------------------------------------
# ABA 2: AGRUPAMENTO ECONÔMICO (K-MEANS)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Classificação da Empresa no Mercado (K-Means)")
    
    # Descrição dos perfis
    st.info(f"📍 **{nome_empresa} ({ticker_selecionado})** pertence ao grupo: **{perfil_empresa}**")
    
    # Resumo por Cluster
    df_agg = df_completo.groupby('TICKER').agg({
        'EMPRESA': 'first',
        'SETOR': 'first',
        'PERFIL': 'first',
        'ROE': 'mean',
        'RETORNO_ANO_%': 'mean',
        'LUCRO_LIQUIDO_BI': 'mean',
        'PATRIMONIO_LIQUIDO_BI': 'mean'
    }).reset_index()
    
    df_agg['ROE_%'] = df_agg['ROE'] * 100
    
    # Gráfico de Dispersão Interativo
    fig_cluster = px.scatter(
        df_agg,
        x="ROE_%",
        y="RETORNO_ANO_%",
        color="PERFIL",
        hover_name="TICKER",
        hover_data={"EMPRESA": True, "SETOR": True, "ROE_%": ":.1f", "RETORNO_ANO_%": ":.1f"},
        title="Mapa de Todas as Empresas: ROE Médio vs Retorno Anual Médio da Ação",
        labels={"ROE_%": "ROE Médio (%)", "RETORNO_ANO_%": "Retorno Anual Médio (%)"},
        height=550
    )
    
    # Destacar a empresa selecionada com um marcador maior e em estrela
    emp_ponto = df_agg[df_agg['TICKER'] == ticker_selecionado]
    if not emp_ponto.empty:
        fig_cluster.add_trace(go.Scatter(
            x=emp_ponto['ROE_%'],
            y=emp_ponto['RETORNO_ANO_%'],
            mode="markers+text",
            marker=dict(symbol="star", size=20, color="red", line=dict(width=2, color="black")),
            name=f"📍 {ticker_selecionado}",
            text=[f"  <b>{ticker_selecionado}</b>"],
            textposition="top right"
        ))
    
    st.plotly_chart(fig_cluster, use_container_width=True)
    
    # Quadro resumo dos 4 clusters
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("""
        **Descrição dos Grupos Econômicos:**
        * **Cluster 0 (Blue Chips & Sólidas):** Empresas grandes, lucros consistentes, ROE médio de ~27% e valorização de +23% a.a.
        * **Cluster 1 (Titãs da Bolsa):** Petrobras e Vale (escala massiva de dezenas de bilhões de lucro).
        """)
    with col_c2:
        st.markdown("""
        * **Cluster 2 (Campeãs de Super ROE):** Empresas com altíssima eficiência de capital (WEG, Ambev, Sabesp) com ROE médio de ~79%.
        * **Cluster 3 (Em Queda / Crise):** Empresas que passaram por forte estresse operacional (Magalu, Hapvida) com rentabilidade baixa e retorno de -19% a.a.
        """)

# ------------------------------------------------------------------------------
# ABA 3: SIMULADOR PREDITIVO DE CENÁRIOS (MACHINE LEARNING)
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Simulador com Inteligência Artificial (Random Forest)")
    st.markdown("""
    O modelo preditivo analisa os fundamentos da empresa cruzados com o **cenário macroeconômico**
    para estimar a probabilidade de alta do **ROE** e da **Ação** no ano seguinte.
    """)
    
    col_sim_esq, col_sim_dir = st.columns([1, 1])
    
    with col_sim_esq:
        st.markdown("#### ⚙️ Configurar Cenário Macroeconômico")
        
        sim_selic = st.slider("Taxa Selic Final do Ano (%):", min_value=6.0, max_value=18.0, value=12.25, step=0.25)
        sim_var_selic = st.slider("Ciclo da Selic (Variação no ano em p.p.):", min_value=-5.0, max_value=8.0, value=0.5, step=0.25)
        sim_ibov = st.slider("Desempenho Geral do Ibovespa (%):", min_value=-30.0, max_value=40.0, value=10.0, step=1.0)
        sim_dolar = st.slider("Variação Anual do Dólar (%):", min_value=-20.0, max_value=40.0, value=5.0, step=1.0)
        sim_ipca = st.slider("Inflação IPCA (%):", min_value=2.0, max_value=12.0, value=4.5, step=0.1)
        
    with col_sim_dir:
        st.markdown("#### 🔮 Resultado da Projeção para o Próximo Ano")
        
        # Obter os dados mais recentes da empresa
        ult_dado = df_empresa.iloc[-1].copy()
        
        # Montar o vetor de entrada
        vetor_teste = {
            'LUCRO_LIQUIDO_BI': ult_dado['LUCRO_LIQUIDO_BI'],
            'PATRIMONIO_LIQUIDO_BI': ult_dado['PATRIMONIO_LIQUIDO_BI'],
            'ROE': ult_dado['ROE'],
            'RETORNO_ANO_%': ult_dado['RETORNO_ANO_%'] if pd.notnull(ult_dado['RETORNO_ANO_%']) else 0.0,
            'CLUSTER_0.0': 1 if ult_dado['CLUSTER'] == 0 else 0,
            'CLUSTER_1.0': 1 if ult_dado['CLUSTER'] == 1 else 0,
            'CLUSTER_2.0': 1 if ult_dado['CLUSTER'] == 2 else 0,
            'CLUSTER_3.0': 1 if ult_dado['CLUSTER'] == 3 else 0,
            'SELIC_ANO_%': sim_selic,
            'VAR_SELIC_PP': sim_var_selic,
            'IPCA_ANO_%': sim_ipca,
            'IBOV_RETORNO_%': sim_ibov,
            'DOLAR_VAR_%': sim_dolar
        }
        df_input = pd.DataFrame([vetor_teste])[features_ml]
        
        # Previsão das probabilidades
        prob_roe_sobe = modelo_roe.predict_proba(df_input)[0][1]
        prob_acao_sobe = modelo_acao.predict_proba(df_input)[0][1]
        
        pred_roe = 1 if prob_roe_sobe >= 0.5 else 0
        pred_acao = 1 if prob_acao_sobe >= 0.5 else 0
        
        # Classificação do Cenário
        if pred_roe == 1 and pred_acao == 1:
            cenario_nome = "Crescente (ROE Sobe, Ação Sobe)"
            cenario_cor = "green"
            cenario_icone = "🟢"
            cenario_desc = "Cenário de ouro! A empresa deve melhorar sua eficiência de capital e o preço da ação tende a acompanhar positivamente."
        elif pred_roe == 0 and pred_acao == 0:
            cenario_nome = "Decrescente (ROE Cai, Ação Cai)"
            cenario_cor = "red"
            cenario_icone = "🔴"
            cenario_desc = "Cenário de cautela. Indicadores apontam para retração na rentabilidade e desvalorização do papel."
        elif pred_roe == 1 and pred_acao == 0:
            cenario_nome = "Oportunidade (ROE Sobe, Ação Cai)"
            cenario_cor = "blue"
            cenario_icone = "🔵"
            cenario_desc = "Potencial pechincha! Os fundamentos devem melhorar, mas o papel pode cair por pressão de mercado."
        else:
            cenario_nome = "Especulação (ROE Cai, Ação Sobe)"
            cenario_cor = "orange"
            cenario_icone = "🟡"
            cenario_desc = "Atenção ao risco! O papel pode subir mesmo com deterioração dos lucros/ROE (movimento especulativo ou beta alto)."
            
        st.markdown(f"### {cenario_icone} **{cenario_nome}**")
        st.write(cenario_desc)
        
        st.markdown("---")
        st.markdown("**Probabilidades Estimadas pela Inteligência Artificial:**")
        
        st.write(f"Probabilidade de alta do **ROE**: **{prob_roe_sobe:.1%}**")
        st.progress(float(prob_roe_sobe))
        
        st.write(f"Probabilidade de alta da **AÇÃO**: **{prob_acao_sobe:.1%}**")
        st.progress(float(prob_acao_sobe))
        
        st.caption("ℹ️ *Modelo treinado com Random Forest Classifier utilizando validação cruzada e métricas macroeconômicas brasileiras.*")
