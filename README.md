Sobre o projeto

Análise de indicadores financeiros (Lucro Líquido, Patrimônio Líquido, ROE) de companhias abertas brasileiras, usando dados públicos da CVM (2021-2025).

Fontes de dados
CVM DFP (Demonstrações Financeiras Padronizadas): DRE e BPP consolidados, 2021-2025
Cadastro CVM (cad_cia_aberta.csv): setor de atividade (SETOR_ATIV), unido via CD_CVM
Estrutura do projeto
data/raw/DRE, data/raw/BPP, data/raw/TIPO  → dados brutos por tipo de demonstrativo
data/processed/                             → dados tratados (CSV + banco SQLite)
notebooks/01 a 05                           → extração, tratamento, ROE, gráficos, SQL, e obviamente meus erros e acertos.
Decisões e armadilhas de dado encontradas
Lucro Líquido: filtrado por CD_CONTA == "3.11" — código estável entre empresas.
Patrimônio Líquido: o código de conta não é confiável entre empresas diferentes (o mesmo código 2.03 significa "Provisões" numa empresa e "Passivos Financeiros" em outra). Filtro correto: por descrição exata (DS_CONTA == "Patrimônio Líquido Consolidado") combinado com ORDEM_EXERC == "ÚLTIMO", já que cada arquivo DFP traz o ano atual e o anterior lado a lado para comparação.
Inconsistência de fonte: algumas empresas de grande porte (TIM, Rio Paranapanema) apresentaram PL reportado como exatamente zero em determinado ano — provável falha de reapresentação na CVM, não erro de processamento. Essas linhas foram excluídas do cálculo de ROE.
Piso de materialidade: empresas com |PL| < R$ 10 milhões foram excluídas do ranking de ROE, pois um denominador próximo de zero distorce o indicador (gerando ROEs de milhares de %).
ROE enganoso: quando Lucro e PL são ambos negativos, a divisão resulta num ROE positivo, o que é matematicamente correto mas economicamente enganoso (ex: Americanas em 2022, durante o escândalo contábil, com patrimônio líquido negativo). Essas linhas foram sinalizadas com a coluna booleana ROE_ENGANOSO.
Escala monetária: valores da CVM vêm em milhares de reais (ESCALA_MOEDA == "MIL"). Foram criadas colunas derivadas em reais cheios e em bilhões, mantendo a original para rastreabilidade.
Análises realizadas
Evolução do ROE médio por setor (2021-2025)
Top 10 empresas por ROE (melhor ano de cada empresa, sem repetição)
Top 10 empresas por ROE médio (mínimo de 3 anos de histórico, excluindo ROE enganoso)
Top 10 empresas por Lucro Líquido acumulado no período
Stack técnica

Python (Pandas, Matplotlib) para extração, tratamento e visualização; SQLite para replicar as principais agregações em SQL, com validação cruzada dos resultados contra o Pandas.

Utilizei do claude para algumas revisões de lógica ,validação de tecnicas em algumas partes e algumas ideias também.