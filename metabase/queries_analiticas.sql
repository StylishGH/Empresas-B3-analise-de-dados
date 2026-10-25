-- ==============================================================================
-- PROJETO B3: CARGA DDL & QUERIES ANALÍTICAS PARA METABASE / POSTGRESQL
-- Banco: b3 (PostgreSQL 16)
-- Tabelas: dados_consolidados (205 linhas), clusters (46 empresas), roe (348 linhas)
-- Autor: Guilherme Mendes
-- 
-- Este arquivo reúne a estrutura completa de dados (DDL + Carga dos CSVs limpos)
-- e todas as consultas SQL do Metabase, desde agregações clássicas até análises
-- avançadas com CTEs e Window Functions (LAG, LEAD, DENSE_RANK, SUM OVER, AVG OVER).
-- ==============================================================================


-- ==============================================================================
-- PARTE 0: DDL & CARGA DOS DADOS (EXECUTAR A PARTIR DA RAIZ DO REPO)
-- psql -h localhost -U postgres -d b3 -f metabase/queries_analiticas.sql
-- ==============================================================================

DROP TABLE IF EXISTS dados_consolidados CASCADE;
DROP TABLE IF EXISTS clusters CASCADE;
DROP TABLE IF EXISTS roe CASCADE;

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

\copy dados_consolidados FROM 'data/processed/dados_consolidados_b3.csv' WITH (FORMAT csv, HEADER true);
\copy clusters FROM 'data/processed/clusters_empresas.csv' WITH (FORMAT csv, HEADER true);
\copy roe FROM 'data/processed/roe_2021_2025.csv' WITH (FORMAT csv, HEADER true);


-- ==============================================================================
-- PARTE 1: DASHBOARD BÁSICO (AGREGAÇÕES & JOINS RELACIONAIS)
-- ==============================================================================

-- 1.1 Evolução Temporal do ROE Médio da Bolsa (2021–2025)
-- Tipo de Visualização no Metabase: Linha (Line Chart)
-- Insights: Mede a rentabilidade agregada do mercado ao longo dos ciclos econômicos.
SELECT 
    ano,
    ROUND(AVG(roe), 4) AS roe_medio
FROM dados_consolidados
GROUP BY ano
ORDER BY ano;


-- 1.2 Rentabilidade por Cluster de Empresas (Machine Learning -> BI)
-- Tipo de Visualização no Metabase: Barras (Bar Chart)
-- Insights: Conecta a clusterização K-Means (aprendizado não-supervisionado) com SQL analítico.
SELECT 
    c.perfil,
    ROUND(AVG(d.roe), 4) AS roe_medio
FROM dados_consolidados d
JOIN clusters c ON c.ticker = d.ticker
GROUP BY c.perfil
ORDER BY roe_medio DESC;


-- 1.3 Top 10 Empresas por ROE no Ano Mais Recente (2024)
-- Tipo de Visualização no Metabase: Barras Horizontais (Row Chart)
-- Insights: Identifica as companhias com maior eficiência de capital próprio.
SELECT 
    empresa,
    ticker,
    ROUND(roe * 100, 1) AS roe_pct
FROM dados_consolidados
WHERE ano = 2024 AND roe IS NOT NULL
ORDER BY roe DESC
LIMIT 10;


-- 1.4 Lucro Líquido Acumulado por Setor da Economia (2021–2025)
-- Tipo de Visualização no Metabase: Barras (Bar Chart)
-- Insights: Destaca os setores com maior geração de caixa em bilhões de reais.
SELECT 
    setor,
    ROUND(SUM(lucro_liquido_bi), 2) AS lucro_total_bi
FROM dados_consolidados
GROUP BY setor
ORDER BY lucro_total_bi DESC;



-- ==============================================================================
-- PARTE 2: QUERIES AVANÇADAS (WINDOW FUNCTIONS & CTEs)
-- ==============================================================================

-- 2.1 Análise de Séries Temporais: Variação de ROE Ano a Ano (YoY)
-- Técnica: CTE + Window Function LAG()
-- Tipo de Visualização no Metabase: Tabela / Linha
-- Insights de Negócio: Mede a aceleração ou desaceleração do ROE sem colapsar linhas.
WITH serie_temporal_roe AS (
    SELECT 
        ano,
        ticker,
        empresa,
        roe,
        -- Busca o ROE do ano imediatamente anterior da mesma empresa
        LAG(roe, 1) OVER (
            PARTITION BY ticker 
            ORDER BY ano
        ) AS roe_ano_anterior
    FROM dados_consolidados
)
SELECT 
    ano,
    ticker,
    empresa,
    ROUND(roe * 100, 1) AS roe_atual_pct,
    ROUND(roe_ano_anterior * 100, 1) AS roe_anterior_pct,
    ROUND((roe - roe_ano_anterior) * 100, 1) AS aceleracao_yoy_pp
FROM serie_temporal_roe
WHERE ticker IN ('PETR4.SA', 'VALE3.SA', 'WEGE3.SA', 'BBAS3.SA')
ORDER BY ticker, ano;


-- 2.2 Projeção de Target para Machine Learning (Shift Temporal)
-- Técnica: CTE + Window Function LEAD()
-- Insights de Negócio: Idêntico ao 'df.groupby(ticker)[roe].shift(-1)' feito em Pandas
-- para criar o target preditivo de classificação (ROE do próximo ano).
WITH base_features_ml AS (
    SELECT 
        ano,
        ticker,
        empresa,
        roe,
        cotacao_final_ano,
        -- Puxa o ROE do ano futuro t+1
        LEAD(roe, 1) OVER (
            PARTITION BY ticker 
            ORDER BY ano
        ) AS roe_prox_ano
    FROM dados_consolidados
)
SELECT 
    ano,
    ticker,
    ROUND(roe, 4) AS roe_t,
    ROUND(roe_prox_ano, 4) AS roe_t_mais_1,
    CASE 
        WHEN roe_prox_ano > roe THEN 1 
        WHEN roe_prox_ano <= roe THEN 0 
        ELSE NULL 
    END AS target_roe_sobe
FROM base_features_ml
ORDER BY ticker, ano;


-- 2.3 Campeã de Rentabilidade por Setor em 2024 (Top 1 per Group)
-- Técnica: CTE + Window Function DENSE_RANK()
-- Tipo de Visualização no Metabase: Barras Horizontais (Row Chart) ou Tabela
-- Pergunta clássica de entrevista: "Como retornar a melhor linha de cada categoria?"
WITH ranking_setorial AS (
    SELECT 
        ano,
        setor,
        empresa,
        ticker,
        roe,
        -- Ranqueia as empresas dentro de cada setor e ano pelo ROE decrescente
        DENSE_RANK() OVER (
            PARTITION BY ano, setor 
            ORDER BY roe DESC
        ) AS rank_setor
    FROM dados_consolidados
    WHERE roe IS NOT NULL
)
SELECT 
    setor,
    empresa,
    ticker,
    ROUND(roe * 100, 1) AS roe_pct
FROM ranking_setorial
WHERE ano = 2024 AND rank_setor = 1
ORDER BY roe_pct DESC;


-- 2.4 Concentração e Market Share de Lucro dentro do Setor (Bancos)
-- Técnica: CTE + Window Function SUM() OVER ()
-- Tipo de Visualização no Metabase: Gráfico de Pizza (Donut / Pie) ou Barras
-- Insights de Negócio: Revela a dominância de mercado dos grandes bancos listados.
WITH lucro_bancos AS (
    SELECT 
        ticker,
        empresa,
        lucro_liquido_bi,
        -- Soma o lucro total do setor bancário mantendo as linhas individuais
        SUM(lucro_liquido_bi) OVER () AS total_bancos_bi
    FROM dados_consolidados
    WHERE ano = 2024 AND setor = 'Bancos' AND lucro_liquido_bi > 0
)
SELECT 
    ticker,
    empresa,
    ROUND(lucro_liquido_bi, 2) AS lucro_bi,
    ROUND((lucro_liquido_bi / total_bancos_bi) * 100, 1) AS market_share_pct
FROM lucro_bancos
ORDER BY lucro_bi DESC;


-- 2.5 Benchmark Relativo: Empresa vs. Média do seu Setor (Spread de ROE)
-- Técnica: CTE + Window Function AVG() OVER (PARTITION BY ano, setor)
-- Tipo de Visualização no Metabase: Barras / Tabela
-- Insights de Negócio: Mostra se a empresa bateu ou perdeu para a média dos concorrentes.
WITH benchmark_setorial AS (
    SELECT 
        ano,
        setor,
        ticker,
        empresa,
        roe,
        AVG(roe) OVER (PARTITION BY ano, setor) AS roe_medio_setor
    FROM dados_consolidados
    WHERE roe IS NOT NULL
)
SELECT 
    ticker,
    setor,
    ROUND(roe * 100, 1) AS roe_empresa_pct,
    ROUND(roe_medio_setor * 100, 1) AS roe_setor_pct,
    ROUND((roe - roe_medio_setor) * 100, 1) AS spread_vs_setor_pp
FROM benchmark_setorial
WHERE ano = 2024 AND ticker IN ('WEGE3.SA', 'VALE3.SA', 'PETR4.SA', 'BBAS3.SA', 'CMIN3.SA', 'EGIE3.SA')
ORDER BY spread_vs_setor_pp DESC;

