# Metabase — dashboards sobre os dados da B3

Prova de uso do Metabase (a ferramenta de dashboards do dia a dia em vagas de
Data Analyst, como a BMP) sobre os mesmos dados processados deste repo, em
`data/processed`. O dashboard montado se chama **"B3 — Visão geral (2021–2025)"**.

![Dashboard B3 no Metabase](dashboard-b3.png)

## As 4 perguntas (SQL nativo no Metabase)

Todas rodam sobre o banco `b3` (PostgreSQL), tabelas `dados_consolidados`
(215 empresa-anos), `clusters` (48 empresas) e `roe` (384 linhas), carregadas
dos CSVs com [`load_b3.sql`](load_b3.sql).

1. **ROE médio por ano (2021–2025)** — linha. O ROE médio cai de 0,45 (2021)
   para 0,34 (2025), com pico de 0,51 em 2022.
   ```sql
   SELECT ano, AVG(roe) AS roe_medio FROM dados_consolidados GROUP BY ano ORDER BY ano
   ```
2. **ROE médio por cluster** — barras. JOIN com `clusters` por ticker; o
   Cluster 1 (Titãs da Bolsa, PETR4/VALE3) lidera com folga.
   ```sql
   SELECT c.perfil, AVG(d.roe) AS roe_medio FROM dados_consolidados d
   JOIN clusters c ON c.ticker = d.ticker GROUP BY c.perfil ORDER BY roe_medio DESC
   ```
3. **Top 10 empresas por ROE em 2024** — barras. ENGIE no topo, seguida de
   VIBRA e CPFL.
   ```sql
   SELECT empresa, roe FROM dados_consolidados WHERE ano = 2024 ORDER BY roe DESC LIMIT 10
   ```
4. **Lucro líquido total por setor (2021–2025)** — barras. Petróleo e Gás e
   Extração Mineral dominam o período.
   ```sql
   SELECT setor, SUM(lucro_liquido_bi) AS lucro_total_bi FROM dados_consolidados
   GROUP BY setor ORDER BY lucro_total_bi DESC
   ```

## Como reproduzir

```bash
# 1. Subir um PostgreSQL e criar o banco b3
createdb b3
psql -d b3 -f metabase/load_b3.sql   # ajustando o caminho dos CSVs no script

# 2. Baixar e rodar o Metabase (precisa de Java 21)
java -jar metabase.jar   # abre em http://localhost:3000

# 3. No Metabase: Add database -> PostgreSQL (host, porta, banco b3, usuário
#    com SELECT nas tabelas) e criar as 4 perguntas acima + o dashboard.
```

## Nota honesta

A instância do Metabase usada para este print era local: o link público de um
Metabase local não é permanente. A prova durável é este print, as perguntas
documentadas acima e o script de carga — qualquer pessoa reproduz o mesmo
dashboard seguindo os passos acima.
