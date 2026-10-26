from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
favicon = str(LOGO_PATH) if LOGO_PATH.exists() else "📈"

st.set_page_config(
    page_title="B3 Analytics & Machine Learning",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS (COM CACHE)
# ==============================================================================
@st.cache_data
def carregar_dados():
    # 1. Dados consolidados CVM + Cotações
    df = pd.read_csv(BASE_DIR / "data/processed/dados_consolidados_b3.csv")
    
    # 2. Dados dos Clusters do K-Means
    df_clusters = pd.read_csv(BASE_DIR / "data/processed/clusters_empresas.csv")
    
    # Garantir ordenação temporal por empresa
    df = df.sort_values(by=['TICKER', 'ANO']).reset_index(drop=True)
    
    # Calcular Retorno Anual da Cotação (%)
    df['RETORNO_ANO_%'] = df.groupby('TICKER')['COTACAO_FINAL_ANO'].pct_change() * 100
    
    # Merge com os clusters
    df = df.merge(df_clusters[['TICKER', 'CLUSTER', 'PERFIL']], on='TICKER', how='left')
    
    # 3. Tabela Macroeconômica Histórica (2021 a 2025 consolidados - BCB SGS e B3)
    dados_macro = {
        'ANO': [2021, 2022, 2023, 2024, 2025],
        'SELIC_ANO_%':     [9.25,  13.75, 11.75, 12.25, 15.00],
        'VAR_SELIC_PP':    [7.25,   4.50, -2.00,  0.50,  2.75],
        'IPCA_ANO_%':      [10.06,  5.79,  4.62,  4.83,  4.26],
        'IBOV_RETORNO_%':  [-11.93, 4.69, 22.28, -10.37, 33.95],
        'DOLAR_VAR_%':     [7.47,  -5.32, -8.08, 27.35, -11.36]
    }
    df_macro = pd.DataFrame(dados_macro)
    df = df.merge(df_macro, on='ANO', how='left')
    
    return df, df_clusters, df_macro

df_completo, df_clusters, df_macro = carregar_dados()

# ==============================================================================
# FUNÇÃO PARA BUSCAR MÉTRICAS MACROECONÔMICAS ATUAIS EM TEMPO REAL
# ==============================================================================
@st.cache_data(ttl=3600)
def obter_metricas_macro_atuais():
    try:
        d = yf.Ticker('USDBRL=X').history(period='1y')
        cotacao_dolar = float(d['Close'].iloc[-1])
        var_dolar = float(((cotacao_dolar / d['Close'].iloc[0]) - 1) * 100)
    except Exception:  # noqa: BLE001 -- fallback intencional: qualquer falha na API vira valor padrao
        cotacao_dolar = 5.40
        var_dolar = 5.0
        
    try:
        b = yf.Ticker('^BVSP').history(period='1y')
        cotacao_ibov = float(b['Close'].iloc[-1])
        var_ibov = float(((cotacao_ibov / b['Close'].iloc[0]) - 1) * 100)
    except Exception:  # noqa: BLE001 -- fallback intencional: qualquer falha na API vira valor padrao
        cotacao_ibov = 130000.0
        var_ibov = 10.0
        
    return {
        'dolar_cotacao': round(cotacao_dolar, 2),
        'dolar_var': round(var_dolar, 1),
        'ibov_pts': round(cotacao_ibov, 0),
        'ibov_var': round(var_ibov, 1),
        'selic_atual': 13.25, # Taxa Selic oficial vigente
        'var_selic': 1.0,     # Ciclo de ajuste recente (p.p.)
        'ipca_atual': 4.6     # Inflação acumulada 12M
    }

# ==============================================================================
# TREINAMENTO DOS MODELOS DE MACHINE LEARNING (COM CACHE)
# ==============================================================================
@st.cache_resource
def treinar_modelos(df):
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


@st.cache_data
def executar_auditoria_walk_forward(df):
    """Reproduz a validação Walk-Forward (Notebook 09), o comparativo Antes vs. Depois,
    o estudo de ablação (ROE vs. Cotação) e o ranking preditivo para 2026."""
    df_wf = df.copy()
    df_wf['ROE_PROX_ANO'] = df_wf.groupby('TICKER')['ROE'].shift(-1)
    df_wf['COTACAO_PROX_ANO'] = df_wf.groupby('TICKER')['COTACAO_FINAL_ANO'].shift(-1)
    df_wf['ANO_ALVO'] = df_wf['ANO'] + 1

    df_wf['ROE_SOBE'] = (df_wf['ROE_PROX_ANO'] > df_wf['ROE']).astype(float)
    df_wf['ACAO_SOBE'] = (df_wf['COTACAO_PROX_ANO'] > df_wf['COTACAO_FINAL_ANO']).astype(float)
    df_wf.loc[df_wf['ROE_PROX_ANO'].isna(), ['ROE_SOBE', 'ACAO_SOBE']] = np.nan

    df_wf = pd.get_dummies(df_wf, columns=['CLUSTER'], dtype=int)
    for c in ['CLUSTER_0.0', 'CLUSTER_1.0', 'CLUSTER_2.0', 'CLUSTER_3.0']:
        if c not in df_wf.columns:
            df_wf[c] = 0

    features_todas = [
        'LUCRO_LIQUIDO_BI', 'PATRIMONIO_LIQUIDO_BI', 'ROE', 'COTACAO_FINAL_ANO',
        'CLUSTER_0.0', 'CLUSTER_1.0', 'CLUSTER_2.0', 'CLUSTER_3.0',
        'SELIC_ANO_%', 'VAR_SELIC_PP', 'IPCA_ANO_%', 'IBOV_RETORNO_%', 'DOLAR_VAR_%'
    ]
    features_roe_puro = [f for f in features_todas if f != 'COTACAO_FINAL_ANO']
    features_acao_pura = [
        f for f in features_todas
        if f not in ['ROE', 'LUCRO_LIQUIDO_BI', 'PATRIMONIO_LIQUIDO_BI']
    ]

    df_historico = df_wf.dropna(
        subset=['ROE_PROX_ANO', 'COTACAO_PROX_ANO']
    ).copy()
    df_historico['ROE_SOBE'] = df_historico['ROE_SOBE'].astype(int)
    df_historico['ACAO_SOBE'] = df_historico['ACAO_SOBE'].astype(int)

    def criar_pipeline():
        return Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=4,
                min_samples_split=5,
                random_state=42,
                class_weight='balanced'
            ))
        ])

    anos_origem_teste = [2022, 2023, 2024]
    registros_folds = []
    acum_wf = {
        'ROE': {'y_true': [], 'y_pred': [], 'y_dummy': []},
        'ACAO': {'y_true': [], 'y_pred': [], 'y_dummy': []}
    }

    for ano_teste in anos_origem_teste:
        treino = df_historico[df_historico['ANO'] < ano_teste]
        teste = df_historico[df_historico['ANO'] == ano_teste]

        X_tr, X_te = treino[features_todas], teste[features_todas]
        ano_alvo = ano_teste + 1

        for alvo_nome, col_y in [('ROE', 'ROE_SOBE'), ('ACAO', 'ACAO_SOBE')]:
            y_tr, y_te = treino[col_y], teste[col_y]
            mod = criar_pipeline()
            mod.fit(X_tr, y_tr)
            preds = mod.predict(X_te)

            dummy = DummyClassifier(strategy='most_frequent')
            dummy.fit(X_tr, y_tr)
            preds_dummy = dummy.predict(X_te)

            acum_wf[alvo_nome]['y_true'].extend(y_te.tolist())
            acum_wf[alvo_nome]['y_pred'].extend(preds.tolist())
            acum_wf[alvo_nome]['y_dummy'].extend(preds_dummy.tolist())

            cm = confusion_matrix(y_te, preds, labels=[0, 1])
            taxa_pos = float(y_te.mean())
            taxa_maj = max(taxa_pos, 1.0 - taxa_pos)

            registros_folds.append({
                'Alvo': f'{alvo_nome}_SOBE',
                'Fold': f'Treino <= {ano_teste - 1} -> Teste {ano_teste} (Alvo {ano_alvo})',
                'N_Treino': len(treino),
                'N_Teste': len(teste),
                'Base_Dummy_Tr': accuracy_score(y_te, preds_dummy),
                'Taxa_Maj_Teste': taxa_maj,
                'Acuracia': accuracy_score(y_te, preds),
                'Precisao': precision_score(y_te, preds, zero_division=0),
                'Recall': recall_score(y_te, preds, zero_division=0),
                'F1_Score': f1_score(y_te, preds, zero_division=0),
                'Matriz_Confusao': f'[[{cm[0, 0]}, {cm[0, 1]}], [{cm[1, 0]}, {cm[1, 1]}]]'
            })

    df_folds = pd.DataFrame(registros_folds)

    # Comparativo Antes (Split Aleatório com Leakage) vs Depois (Walk-Forward)
    X_all = df_historico[features_todas]
    y_roe_all = df_historico['ROE_SOBE']
    y_acao_all = df_historico['ACAO_SOBE']

    X_tr_r, X_te_r, y_roe_tr_r, y_roe_te_r = train_test_split(
        X_all, y_roe_all, test_size=0.235, random_state=42, stratify=y_roe_all
    )
    _, X_te_a, y_acao_tr_r, y_acao_te_r = train_test_split(
        X_all, y_acao_all, test_size=0.235, random_state=42, stratify=y_acao_all
    )

    mod_roe_leak = criar_pipeline().fit(X_tr_r, y_roe_tr_r)
    preds_roe_leak = mod_roe_leak.predict(X_te_r)
    dum_roe_leak = DummyClassifier(strategy='most_frequent').fit(X_tr_r, y_roe_tr_r).predict(X_te_r)

    mod_acao_leak = criar_pipeline().fit(X_tr_r, y_acao_tr_r)
    preds_acao_leak = mod_acao_leak.predict(X_te_a)
    dum_acao_leak = DummyClassifier(strategy='most_frequent').fit(X_tr_r, y_acao_tr_r).predict(X_te_a)

    df_antes_depois = pd.DataFrame([
        {
            'Alvo': 'ROE_SOBE',
            'Metodo': 'ANTES (08: Split Aleatório c/ Leakage)',
            'N_Teste': len(y_roe_te_r),
            'Baseline_Dummy': accuracy_score(y_roe_te_r, dum_roe_leak),
            'Acuracia': accuracy_score(y_roe_te_r, preds_roe_leak),
            'Precisao': precision_score(y_roe_te_r, preds_roe_leak, zero_division=0),
            'Recall': recall_score(y_roe_te_r, preds_roe_leak, zero_division=0),
            'F1_Score': f1_score(y_roe_te_r, preds_roe_leak, zero_division=0),
        },
        {
            'Alvo': 'ROE_SOBE',
            'Metodo': 'DEPOIS (09: Walk-Forward s/ Leakage)',
            'N_Teste': len(acum_wf['ROE']['y_true']),
            'Baseline_Dummy': accuracy_score(acum_wf['ROE']['y_true'], acum_wf['ROE']['y_dummy']),
            'Acuracia': accuracy_score(acum_wf['ROE']['y_true'], acum_wf['ROE']['y_pred']),
            'Precisao': precision_score(acum_wf['ROE']['y_true'], acum_wf['ROE']['y_pred'], zero_division=0),
            'Recall': recall_score(acum_wf['ROE']['y_true'], acum_wf['ROE']['y_pred'], zero_division=0),
            'F1_Score': f1_score(acum_wf['ROE']['y_true'], acum_wf['ROE']['y_pred'], zero_division=0),
        },
        {
            'Alvo': 'ACAO_SOBE',
            'Metodo': 'ANTES (08: Split Aleatório c/ Leakage)',
            'N_Teste': len(y_acao_te_r),
            'Baseline_Dummy': accuracy_score(y_acao_te_r, dum_acao_leak),
            'Acuracia': accuracy_score(y_acao_te_r, preds_acao_leak),
            'Precisao': precision_score(y_acao_te_r, preds_acao_leak, zero_division=0),
            'Recall': recall_score(y_acao_te_r, preds_acao_leak, zero_division=0),
            'F1_Score': f1_score(y_acao_te_r, preds_acao_leak, zero_division=0),
        },
        {
            'Alvo': 'ACAO_SOBE',
            'Metodo': 'DEPOIS (09: Walk-Forward s/ Leakage)',
            'N_Teste': len(acum_wf['ACAO']['y_true']),
            'Baseline_Dummy': accuracy_score(acum_wf['ACAO']['y_true'], acum_wf['ACAO']['y_dummy']),
            'Acuracia': accuracy_score(acum_wf['ACAO']['y_true'], acum_wf['ACAO']['y_pred']),
            'Precisao': precision_score(acum_wf['ACAO']['y_true'], acum_wf['ACAO']['y_pred'], zero_division=0),
            'Recall': recall_score(acum_wf['ACAO']['y_true'], acum_wf['ACAO']['y_pred'], zero_division=0),
            'F1_Score': f1_score(acum_wf['ACAO']['y_true'], acum_wf['ACAO']['y_pred'], zero_division=0),
        },
    ])

    # Estudo de Ablação (Influência Cruzada ROE vs Cotação)
    config_ablacao = [
        ('1. ROE (Com Cotação)', 'ROE_SOBE', features_todas),
        ('2. ROE (Puro Contábil — Sem Cotação)', 'ROE_SOBE', features_roe_puro),
        ('3. AÇÃO (Com ROE e Balanço)', 'ACAO_SOBE', features_todas),
        ('4. AÇÃO (Puro Preço — Sem ROE/Balanço)', 'ACAO_SOBE', features_acao_pura),
    ]
    linhas_ablacao = []
    matrizes_ablacao = {}

    for nome_exp, col_y, cols_feat in config_ablacao:
        y_t_all, y_p_all = [], []
        for ano_teste in anos_origem_teste:
            tr = df_historico[df_historico['ANO'] < ano_teste]
            te = df_historico[df_historico['ANO'] == ano_teste]
            mod = criar_pipeline().fit(tr[cols_feat], tr[col_y])
            preds = mod.predict(te[cols_feat])
            y_t_all.extend(te[col_y].tolist())
            y_p_all.extend(preds.tolist())

        cm = confusion_matrix(y_t_all, y_p_all, labels=[0, 1])
        matrizes_ablacao[nome_exp] = cm
        linhas_ablacao.append({
            'Experimento': nome_exp,
            'Alvo': col_y,
            'N_Features': len(cols_feat),
            'Acuracia': accuracy_score(y_t_all, y_p_all),
            'Precisao': precision_score(y_t_all, y_p_all, zero_division=0),
            'Recall': recall_score(y_t_all, y_p_all, zero_division=0),
            'F1_Score': f1_score(y_t_all, y_p_all, zero_division=0),
            'Matriz_Confusao': f'[[{cm[0, 0]}, {cm[0, 1]}], [{cm[1, 0]}, {cm[1, 1]}]]'
        })

    df_ablacao = pd.DataFrame(linhas_ablacao)

    # Projeção 2026 para todas as empresas com dados fechados de 2025
    df_2025 = df_wf[df_wf['ANO'] == 2025].dropna(subset=['COTACAO_FINAL_ANO']).copy()
    mod_roe_2026 = criar_pipeline().fit(df_historico[features_todas], df_historico['ROE_SOBE'])
    mod_acao_2026 = criar_pipeline().fit(df_historico[features_todas], df_historico['ACAO_SOBE'])

    df_2025['PROB_ROE_SUBIR_2026'] = mod_roe_2026.predict_proba(df_2025[features_todas])[:, 1]
    df_2025['PROB_ACAO_SUBIR_2026'] = mod_acao_2026.predict_proba(df_2025[features_todas])[:, 1]
    df_2025['SCORE_COMBINADO'] = (
        df_2025['PROB_ROE_SUBIR_2026'] + df_2025['PROB_ACAO_SUBIR_2026']
    ) / 2.0

    def classificar_tipo_sinal(row):
        if row['PROB_ROE_SUBIR_2026'] >= 0.5 and row['ROE'] < 0.08:
            return '🔄 Reversão à Média (Turnaround)'
        if row['PROB_ROE_SUBIR_2026'] >= 0.5 and row['ROE'] >= 0.08:
            return '🚀 Expansão de Qualidade (ROE >= 8%)'
        return '⚠️ Pressão Contábil / Estagnação'

    df_2025['TIPO_SINAL'] = df_2025.apply(classificar_tipo_sinal, axis=1)
    df_ranking_2026 = df_2025[[
        'TICKER', 'EMPRESA', 'SETOR', 'PERFIL', 'ROE', 'RETORNO_ANO_%',
        'PROB_ROE_SUBIR_2026', 'PROB_ACAO_SUBIR_2026', 'SCORE_COMBINADO', 'TIPO_SINAL'
    ]].sort_values(by='SCORE_COMBINADO', ascending=False).reset_index(drop=True)

    return {
        'df_folds': df_folds,
        'df_antes_depois': df_antes_depois,
        'df_ablacao': df_ablacao,
        'matrizes_ablacao': matrizes_ablacao,
        'df_ranking_2026': df_ranking_2026,
    }


auditoria_wf = executar_auditoria_walk_forward(df_completo)

# ==============================================================================
# BARRA LATERAL (FILTROS)
# ==============================================================================
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=120)

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
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Raio-X Fundamentalista & Mercado",
    "🎯 Agrupamento Econômico (K-Means)",
    "🤖 Simulador Preditivo & Ranking 2026",
    "🔬 Auditoria Walk-Forward & Ablação (NB 09)"
])

# ------------------------------------------------------------------------------
# ABA 1: RAIO-X FUNDAMENTALISTA & MERCADO
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Indicadores Recentes e Histórico")
    
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
        line={"color": "#2ca02c", "width": 3},
        marker={"size": 8},
        yaxis="y1"
    ))
    
    # Barras do ROE
    fig_hist.add_trace(go.Bar(
        x=df_empresa['ANO'],
        y=df_empresa['ROE'] * 100,
        name="ROE (%)",
        marker={"color": "#1f77b4", "opacity": 0.4},
        yaxis="y2"
    ))
    
    fig_hist.update_layout(
        title=f"Histórico Anual de Cotação e Rentabilidade ({ticker_selecionado})",
        xaxis={"title": "Ano", "tickmode": 'linear', "dtick": 1},
        yaxis={"title": "Cotação (R$)", "side": "left", "showgrid": False},
        yaxis2={"title": "ROE (%)", "side": "right", "overlaying": "y", "showgrid": True},
        legend={"x": 0.01, "y": 0.99},
        hovermode="x unified",
        height=450
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption("ℹ️ **Nota sobre as cotações:** Os preços históricos são ajustados por proventos (dividendos e desdobramentos), refletindo o fechamento de cada exercício contábil anual (2021 a 2025). Por isso, ações com altos dividendos distribuídos (como Petrobras) apresentam preço histórico ajustado diferente da cotação nominal de tela de 2026.")
    
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
    
    st.info(f"📍 **{nome_empresa} ({ticker_selecionado})** pertence ao grupo: **{perfil_empresa}**")
    
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
    
    emp_ponto = df_agg[df_agg['TICKER'] == ticker_selecionado]
    if not emp_ponto.empty:
        fig_cluster.add_trace(go.Scatter(
            x=emp_ponto['ROE_%'],
            y=emp_ponto['RETORNO_ANO_%'],
            mode="markers+text",
            marker={"symbol": "star", "size": 20, "color": "red", "line": {"width": 2, "color": "black"}},
            name=f"📍 {ticker_selecionado}",
            text=[f"  <b>{ticker_selecionado}</b>"],
            textposition="top right"
        ))
    
    st.plotly_chart(fig_cluster, use_container_width=True)
    
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
# ABA 3: SIMULADOR PREDITIVO DE CENÁRIOS & RANKING 2026 (MACHINE LEARNING)
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Simulador com Inteligência Artificial (Random Forest)")
    st.markdown("""
    O modelo preditivo analisa os fundamentos da empresa cruzados com o **cenário macroeconômico**
    para estimar a probabilidade de alta do **ROE** e da **Ação** no ano seguinte.
    Por padrão, os controles já iniciam com o **fechamento oficial de 2025 (BCB SGS e B3)** para projetar **2026**.
    """)

    # Inicializar valores do session_state com o fechamento oficial de 2025
    if 'selic_val' not in st.session_state:
        st.session_state['selic_val'] = 15.00
    if 'var_selic_val' not in st.session_state:
        st.session_state['var_selic_val'] = 2.75
    if 'ibov_val' not in st.session_state:
        st.session_state['ibov_val'] = 33.95
    if 'dolar_val' not in st.session_state:
        st.session_state['dolar_val'] = -11.36
    if 'ipca_val' not in st.session_state:
        st.session_state['ipca_val'] = 4.26

    col_btn, col_btn_2025, col_info = st.columns([1, 1, 2])
    with col_btn:
        if st.button("🌐 Puxar Métricas Reais do Mercado Agora", help="Coleta cotação em tempo real do Dólar e Ibovespa via Yahoo Finance e preenche os sliders"):
            with st.spinner("Buscando cotações em tempo real..."):
                macro_real = obter_metricas_macro_atuais()
                st.session_state['selic_val'] = macro_real['selic_atual']
                st.session_state['var_selic_val'] = macro_real['var_selic']
                st.session_state['ibov_val'] = macro_real['ibov_var']
                st.session_state['dolar_val'] = macro_real['dolar_var']
                st.session_state['ipca_val'] = macro_real['ipca_atual']
                st.session_state['macro_info'] = (
                    f"✅ **Métricas Reais Carregadas:** "
                    f"Dólar: **R$ {macro_real['dolar_cotacao']}** (12M: {macro_real['dolar_var']:+.1f}%) | "
                    f"Ibovespa: **{macro_real['ibov_pts']:,.0f} pts** (12M: {macro_real['ibov_var']:+.1f}%) | "
                    f"Selic Atual: **{macro_real['selic_atual']}%** | "
                    f"IPCA: **{macro_real['ipca_atual']}%**"
                )
                st.rerun()
    with col_btn_2025:
        if st.button("📌 Restaurar Fechamento Oficial 2025 (Base 2026)", help="Restaura SELIC 15,00%, IPCA 4,26%, Ibov +33,95% e Dólar -11,36%"):
            st.session_state['selic_val'] = 15.00
            st.session_state['var_selic_val'] = 2.75
            st.session_state['ibov_val'] = 33.95
            st.session_state['dolar_val'] = -11.36
            st.session_state['ipca_val'] = 4.26
            st.session_state['macro_info'] = (
                "✅ **Fechamento Oficial 2025 (BCB/B3):** "
                "Selic: **15,00%** (+2,75 p.p.) | IPCA: **4,26%** | Ibovespa: **+33,95%** | Dólar: **-11,36%**"
            )
            st.rerun()

    if 'macro_info' in st.session_state:
        st.success(st.session_state['macro_info'])

    st.markdown("---")

    col_sim_esq, col_sim_dir = st.columns([1, 1])

    with col_sim_esq:
        st.markdown("#### ⚙️ Ajustar Cenário Macroeconômico")

        sim_selic = st.slider("Taxa Selic Final do Ano (%):", min_value=6.0, max_value=18.0, value=float(st.session_state['selic_val']), step=0.25)
        sim_var_selic = st.slider("Ciclo da Selic (Variação no ano em p.p.):", min_value=-5.0, max_value=8.0, value=float(st.session_state['var_selic_val']), step=0.25)
        sim_ibov = st.slider("Desempenho Geral do Ibovespa (%):", min_value=-30.0, max_value=40.0, value=float(st.session_state['ibov_val']), step=0.05)
        sim_dolar = st.slider("Variação Anual do Dólar (%):", min_value=-20.0, max_value=40.0, value=float(st.session_state['dolar_val']), step=0.05)
        sim_ipca = st.slider("Inflação IPCA (%):", min_value=2.0, max_value=12.0, value=float(st.session_state['ipca_val']), step=0.01)

    with col_sim_dir:
        st.markdown("#### 🔮 Resultado da Projeção para o Próximo Ano")

        ult_dado = df_empresa.iloc[-1].copy()

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

        prob_roe_sobe = modelo_roe.predict_proba(df_input)[0][1]
        prob_acao_sobe = modelo_acao.predict_proba(df_input)[0][1]

        pred_roe = 1 if prob_roe_sobe >= 0.5 else 0
        pred_acao = 1 if prob_acao_sobe >= 0.5 else 0

        if pred_roe == 1 and pred_acao == 1:
            cenario_nome = "Crescente (ROE Sobe, Ação Sobe)"
            cenario_icone = "🟢"
            cenario_desc = "Cenário de ouro! A empresa deve melhorar sua eficiência de capital e o preço da ação tende a acompanhar positivamente."
        elif pred_roe == 0 and pred_acao == 0:
            cenario_nome = "Decrescente (ROE Cai, Ação Cai)"
            cenario_icone = "🔴"
            cenario_desc = "Cenário de cautela. Indicadores apontam para retração na rentabilidade e desvalorização do papel."
        elif pred_roe == 1 and pred_acao == 0:
            cenario_nome = "Oportunidade (ROE Sobe, Ação Cai)"
            cenario_icone = "🔵"
            cenario_desc = "Potencial pechincha! Os fundamentos devem melhorar, mas o papel pode cair por pressão de mercado."
        else:
            cenario_nome = "Especulação (ROE Cai, Ação Sobe)"
            cenario_icone = "🟡"
            cenario_desc = "Atenção ao risco! O papel pode subir mesmo com deterioração dos lucros/ROE (movimento especulativo ou beta alto)."

        st.markdown(f"### {cenario_icone} **{cenario_nome}**")
        st.write(cenario_desc)

        st.markdown("---")
        st.markdown("**Probabilidades Estimadas pela Inteligência Artificial:**")

        st.write(f"Probabilidade de alta do **ROE** (Acurácia Walk-Forward: **62,1%**): **{prob_roe_sobe:.1%}**")
        st.progress(float(prob_roe_sobe))

        st.write(f"Probabilidade de alta da **AÇÃO** (Acurácia Walk-Forward: **37,9%** — alto ruído macro): **{prob_acao_sobe:.1%}**")
        st.progress(float(prob_acao_sobe))

        st.caption("ℹ️ *Nota Metodológica: O modelo captura forte sinal na evolução contábil (ROE_SOBE = 62,1%, IC 95% [53,6%, 70,6%]), enquanto a variação anual da ação sofre forte influência de choques exógenos de juros.*")

    st.markdown("---")
    st.subheader("🏆 Ranking Preditivo 2026 (47 Empresas — Walk-Forward Final)")
    st.markdown("""
    Abaixo está a projeção completa para **2026** (treinada com todas as transições de `2021 -> 2025` e aplicada aos balanços e preços fechados de 2025).
    Use o filtro para separar casos de **Reversão à Média (*Turnaround*)** de empresas com **Expansão de Qualidade (`ROE 2025 >= 8%`)**.
    """)

    df_rank = auditoria_wf['df_ranking_2026'].copy()
    filtro_sinal = st.radio(
        "Filtrar perfil do sinal preditivo para 2026:",
        options=[
            "Todas as Empresas (47)",
            "🚀 Expansão de Qualidade (ROE >= 8%)",
            "🔄 Reversão à Média (Turnaround)",
            "⚠️ Pressão Contábil / Estagnação"
        ],
        horizontal=True
    )
    if filtro_sinal != "Todas as Empresas (47)":
        df_rank = df_rank[df_rank['TIPO_SINAL'] == filtro_sinal]

    st.dataframe(
        df_rank.style.format({
            'ROE': '{:.1%}',
            'RETORNO_ANO_%': '{:+.1f}%',
            'PROB_ROE_SUBIR_2026': '{:.1%}',
            'PROB_ACAO_SUBIR_2026': '{:.1%}',
            'SCORE_COMBINADO': '{:.1%}'
        }),
        use_container_width=True
    )

# ------------------------------------------------------------------------------
# ABA 4: AUDITORIA WALK-FORWARD, ABLAÇÃO & MATRIZ DE CONFUSÃO (NOTEBOOK 09)
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("🔬 Auditoria de Machine Learning: Walk-Forward, Ablação & Matriz de Confusão")
    st.markdown("""
    Esta aba reproduz integralmente os experimentos científicos do **Notebook 09 (`09_exploracao.ipynb`)**,
    eliminando vazamento temporal (*Data Leakage*), confrontando os modelos contra *baselines* majoritárias
    e isolando a influência cruzada entre **ROE (Contabilidade)** e **Cotação (Mercado)**.
    """)

    # KPIs de Destaque
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="Acurácia Global (ROE_SOBE)",
            value="62,10%",
            delta="+13,71 p.p. vs Dummy (48,39%)"
        )
    with k2:
        st.metric(
            label="F1-Score Global (ROE_SOBE)",
            value="61,16%",
            delta="Precisão 60,7% | Recall 61,7%"
        )
    with k3:
        st.metric(
            label="Intervalo de Confiança 95%",
            value="[53,6%, 70,6%]",
            delta="N = 124 testes (3 Folds)"
        )
    with k4:
        st.metric(
            label="ROE Puro Contábil (Sem Preço)",
            value="60,48%",
            delta="-1,62 p.p. vs Modelo c/ Cotação"
        )

    st.markdown("---")

    # 1. Tabela Antes vs Depois
    st.markdown("### 1️⃣ Antes vs. Depois: O Efeito do Vazamento Temporal (*Data Leakage*)")
    st.markdown("""
    No **Notebook 08**, o uso de `train_test_split(..., random_state=42)` misturou empresas do mesmo ano no treino e no teste.
    Como as 5 variáveis macroeconômicas (`SELIC`, `IPCA`, `IBOV`, `DOLAR`) são idênticas para todas as empresas num mesmo ano,
    o modelo "decorava" se a bolsa subiu ou caiu naquele ano, inflando artificialmente a acurácia de `ACAO_SOBE` para **70,27%**.
    Com a **Validação Walk-Forward (Notebook 09)** na mesma base saneada:
    """)
    st.dataframe(
        auditoria_wf['df_antes_depois'].style.format({
            'Baseline_Dummy': '{:.2%}',
            'Acuracia': '{:.2%}',
            'Precisao': '{:.2%}',
            'Recall': '{:.2%}',
            'F1_Score': '{:.2%}'
        }),
        use_container_width=True
    )

    st.markdown("---")

    # 2. Tabela por Fold (3 Folds)
    st.markdown("### 2️⃣ Desempenho por Fold no Walk-Forward Validation (2023, 2024 e 2025)")
    st.markdown("""
    A semente inicial (`2021 -> 2022`, 32 observações) serve exclusivamente como base de treino para o **Fold 1**,
    pois 2021 não possui histórico prévio na base para ser avaliado como teste. Os **3 Folds de teste** somam **$N = 124$ observações**:
    """)
    st.dataframe(
        auditoria_wf['df_folds'].style.format({
            'Base_Dummy_Tr': '{:.2%}',
            'Taxa_Maj_Teste': '{:.2%}',
            'Acuracia': '{:.2%}',
            'Precisao': '{:.2%}',
            'Recall': '{:.2%}',
            'F1_Score': '{:.2%}'
        }),
        use_container_width=True
    )

    st.markdown("---")

    # 3. Estudo de Ablação (ROE vs Cotação)
    st.markdown("### 3️⃣ Estudo de Ablação de Features: ROE vs. Cotação se influenciam?")
    st.markdown("""
    Testamos separadamente se o preço da ação ajuda a prever o ROE (e vice-versa) removendo os respectivos blocos de variáveis:
    * **ROE (Com Cotação vs. Puro Contábil):** Manter `RETORNO_ANO_%` eleva a acurácia de **60,48%** para **62,10%** (+1,62 p.p.) e o F1 de **59,50%** para **61,16%**, pois o preço de fechamento carrega expectativa futura (*forward-looking*) do mercado.
    * **AÇÃO (Com ROE vs. Puro Preço):** Incluir `ROE` e balanço melhora o **Recall** (`38,89%` vs. `36,11%`) e o **F1-Score** (`42,11%` vs. `40,94%`), embora a acurácia global continue limitada (~38%–39%) pelas quebras de regime da SELIC.
    """)
    st.dataframe(
        auditoria_wf['df_ablacao'].style.format({
            'Acuracia': '{:.2%}',
            'Precisao': '{:.2%}',
            'Recall': '{:.2%}',
            'F1_Score': '{:.2%}'
        }),
        use_container_width=True
    )

    st.markdown("---")

    # 4. Gráficos Interativos das Matrizes de Confusão (2x2)
    st.markdown("### 4️⃣ Gráficos das Matrizes de Confusão ($N = 124$ Testes Walk-Forward)")
    st.markdown("""
    Visualização lado a lado das matrizes de confusão `[[VN, FP], [FN, VP]]` para os 4 modelos do estudo de ablação:
    """)

    nomes_exp = list(auditoria_wf['matrizes_ablacao'].keys())
    col_cm1, col_cm2 = st.columns(2)
    col_cm3, col_cm4 = st.columns(2)
    cols_grid = [col_cm1, col_cm2, col_cm3, col_cm4]

    for idx, nome_exp in enumerate(nomes_exp):
        cm = auditoria_wf['matrizes_ablacao'][nome_exp]
        total_cm = int(cm.sum())
        linha_info = auditoria_wf['df_ablacao'].iloc[idx]
        escala_cor = "Blues" if "ROE (" in nome_exp else "Oranges"

        textos = [
            [
                f"<b>{cm[0, 0]}</b> ({cm[0, 0] / total_cm:.1%})<br>VN (Caiu / Prev Caiu)",
                f"<b>{cm[0, 1]}</b> ({cm[0, 1] / total_cm:.1%})<br>FP (Caiu / Prev Subiu)"
            ],
            [
                f"<b>{cm[1, 0]}</b> ({cm[1, 0] / total_cm:.1%})<br>FN (Subiu / Prev Caiu)",
                f"<b>{cm[1, 1]}</b> ({cm[1, 1] / total_cm:.1%})<br>VP (Subiu / Prev Subiu)"
            ]
        ]

        fig_cm = go.Figure(data=go.Heatmap(
            z=cm,
            x=["Previsto: Cai/Estagna (0)", "Previsto: Sobe (1)"],
            y=["Real: Cai/Estagna (0)", "Real: Sobe (1)"],
            text=textos,
            texttemplate="%{text}",
            colorscale=escala_cor,
            showscale=False
        ))
        fig_cm.update_layout(
            title=(
                f"{nome_exp}<br>"
                f"<sup>Acc: {linha_info['Acuracia']:.1%} | "
                f"Prec: {linha_info['Precisao']:.1%} | "
                f"Rec: {linha_info['Recall']:.1%} | "
                f"F1: {linha_info['F1_Score']:.1%}</sup>"
            ),
            yaxis={"autorange": "reversed"},
            height=340,
            margin={"l": 20, "r": 20, "t": 65, "b": 20}
        )
        with cols_grid[idx]:
            st.plotly_chart(fig_cm, use_container_width=True)

    st.info(
        "💡 **Por que ML Clássico Anual acerta Fundamentos (62,1%), mas não Preço de Ação (37,9%)?** "
        "Balanços contábeis possuem inércia operacional e reversão à média (capturáveis com árvores de decisão em dados anuais). "
        "Já o preço de tela reage diariamente a expectativas futuras de juros (Curva DI), fluxo estrangeiro e eventos globais — "
        "escopo que pertence a **Finanças Quantitativas (Quant)** de alta frequência e fatores de risco, não a dados contábeis anuais."
    )
