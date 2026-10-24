"""Testes básicos das funções de app.py (Etapa 1: CI verde)."""

import pandas as pd

from app import (
    carregar_dados,
    df_completo,
    features_ml,
    modelo_acao,
    modelo_roe,
    obter_metricas_macro_atuais,
    treinar_modelos,
)


def test_carregar_dados_retorna_tres_dataframes():
    df, df_clusters, df_macro = carregar_dados()
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df_clusters, pd.DataFrame)
    assert isinstance(df_macro, pd.DataFrame)
    assert len(df) == 215
    assert len(df_clusters) == 48
    assert len(df_macro) == 5


def test_carregar_dados_colunas_e_retorno_anual():
    df, _, _ = carregar_dados()
    for coluna in [
        "TICKER",
        "ANO",
        "ROE",
        "COTACAO_FINAL_ANO",
        "RETORNO_ANO_%",
        "CLUSTER",
        "PERFIL",
        "SELIC_ANO_%",
        "IPCA_ANO_%",
    ]:
        assert coluna in df.columns
    # Ordenado por empresa e ano, sem duplicar (empresa, ano)
    ordenado = df.sort_values(["TICKER", "ANO"]).reset_index(drop=True)
    assert ordenado.equals(df)
    assert not df.duplicated(subset=["TICKER", "ANO"]).any()
    # Primeiro ano de cada empresa não tem retorno (não há ano anterior)
    primeiros = df.sort_values(["TICKER", "ANO"]).groupby("TICKER").head(1)
    assert primeiros["RETORNO_ANO_%"].isna().all()
    assert df["RETORNO_ANO_%"].notna().any()


def test_treinar_modelos_retorna_pipelines_e_features():
    modelo_roe_novo, modelo_acao_novo, features = treinar_modelos(df_completo)
    assert len(features) == 13
    assert "ROE" in features and "CLUSTER_0.0" in features
    for modelo in (modelo_roe_novo, modelo_acao_novo):
        assert hasattr(modelo, "predict_proba")


def test_modelos_preveem_probabilidades_validas():
    # Vetor no mesmo formato que a aba do simulador monta em app.py
    ultimo = df_completo.sort_values(["TICKER", "ANO"]).groupby("TICKER").tail(1).iloc[0]
    vetor = {
        "LUCRO_LIQUIDO_BI": ultimo["LUCRO_LIQUIDO_BI"],
        "PATRIMONIO_LIQUIDO_BI": ultimo["PATRIMONIO_LIQUIDO_BI"],
        "ROE": ultimo["ROE"],
        "RETORNO_ANO_%": ultimo["RETORNO_ANO_%"] if pd.notnull(ultimo["RETORNO_ANO_%"]) else 0.0,
        "CLUSTER_0.0": 1 if ultimo["CLUSTER"] == 0 else 0,
        "CLUSTER_1.0": 1 if ultimo["CLUSTER"] == 1 else 0,
        "CLUSTER_2.0": 1 if ultimo["CLUSTER"] == 2 else 0,
        "CLUSTER_3.0": 1 if ultimo["CLUSTER"] == 3 else 0,
        "SELIC_ANO_%": 12.25,
        "VAR_SELIC_PP": 0.5,
        "IPCA_ANO_%": 4.5,
        "IBOV_RETORNO_%": 10.0,
        "DOLAR_VAR_%": 5.0,
    }
    entrada = pd.DataFrame([vetor])[features_ml]
    for modelo in (modelo_roe, modelo_acao):
        proba = modelo.predict_proba(entrada)
        assert proba.shape == (1, 2)
        assert 0.0 <= proba[0][1] <= 1.0
        assert abs(proba[0].sum() - 1.0) < 1e-6


def test_metricas_macro_fallback_sem_rede(monkeypatch):
    monkeypatch.setattr("yfinance.Ticker", lambda *args, **kwargs: _Quebrado())

    class _Quebrado:
        def history(self, *args, **kwargs):
            raise ConnectionError("sem rede")

    metricas = obter_metricas_macro_atuais()
    assert metricas["dolar_cotacao"] == 5.40
    assert metricas["ibov_pts"] == 130000.0
    assert metricas["selic_atual"] == 13.25
    assert metricas["ipca_atual"] == 4.6
