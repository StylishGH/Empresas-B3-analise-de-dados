-- Carga dos CSVs processados do B3 no Postgres local (banco b3)
-- Rode com: psql -U postgres -d b3 -f load_b3.sql  (a partir de ~/workspace/b3-metabase)
DROP TABLE IF EXISTS dados_consolidados;
DROP TABLE IF EXISTS clusters;
DROP TABLE IF EXISTS roe;
CREATE TABLE dados_consolidados (
    ano INT,
    empresa TEXT,
    ticker TEXT,
    setor TEXT,
    lucro_liquido_bi NUMERIC,
    patrimonio_liquido_bi NUMERIC,
    roe NUMERIC,
    data DATE,
    cotacao_final_ano NUMERIC
);
CREATE TABLE clusters (
    ticker TEXT,
    cluster INT,
    perfil TEXT
);
CREATE TABLE roe (
    denom_cia TEXT,
    setor_ativ TEXT,
    ano_arquivo INT,
    vl_conta_lucro NUMERIC,
    vl_conta_reais NUMERIC,
    vl_conta_bi NUMERIC,
    vl_conta_pl NUMERIC,
    roe NUMERIC,
    roe_enganoso BOOLEAN
);
\copy dados_consolidados FROM 'repo/data/processed/dados_consolidados_b3.csv' WITH (FORMAT csv, HEADER true);
\copy clusters FROM 'repo/data/processed/clusters_empresas.csv' WITH (FORMAT csv, HEADER true);
\copy roe FROM 'repo/data/processed/roe_2021_2025.csv' WITH (FORMAT csv, HEADER true);
SELECT 'dados_consolidados', COUNT(*) FROM dados_consolidados
UNION ALL SELECT 'clusters', COUNT(*) FROM clusters
UNION ALL SELECT 'roe', COUNT(*) FROM roe;
