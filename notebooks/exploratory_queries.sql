-- Nifty 100 Financial Intelligence Platform
-- Sprint 1: Exploratory Queries

-- Query 1: Database Row Counts for All 12 Tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- Query 2: Year Coverage per Company (Number of years in financial statements)
SELECT 
    company_id,
    COUNT(DISTINCT year) AS years_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year
FROM profitandloss
GROUP BY company_id
ORDER BY years_count ASC, company_id;

-- Query 3: Companies with Insufficient Year Coverage (< 5 Years)
SELECT 
    company_id,
    COUNT(DISTINCT year) AS years_count
FROM profitandloss
GROUP BY company_id
HAVING years_count < 5
ORDER BY years_count;

-- Query 4: Top 10 ROE Companies in the Latest Available Year (from pre-computed financial_ratios)
WITH LatestYear AS (
    SELECT MAX(year) AS max_yr FROM financial_ratios
)
SELECT 
    r.company_id, 
    c.company_name, 
    r.year, 
    r.return_on_equity_pct
FROM financial_ratios r
JOIN companies c ON r.company_id = c.id
WHERE r.year = (SELECT max_yr FROM LatestYear)
ORDER BY r.return_on_equity_pct DESC
LIMIT 10;

-- Query 5: Debt-Free Companies in the Latest Year
WITH LatestYear AS (
    SELECT MAX(year) AS max_yr FROM financial_ratios
)
SELECT 
    company_id, 
    year, 
    debt_to_equity,
    total_debt_cr
FROM financial_ratios
WHERE year = (SELECT max_yr FROM LatestYear) AND debt_to_equity = 0
ORDER BY company_id;

-- Query 6: Sector Breakdown & Company Counts
SELECT 
    broad_sector, 
    COUNT(*) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- Query 7: Missing Annual Reports (Companies with gaps in their document lists)
SELECT 
    c.id, 
    c.company_name, 
    2024 - COUNT(d.year) AS missing_report_count
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
GROUP BY c.id, c.company_name
ORDER BY missing_report_count DESC
LIMIT 10;

-- Query 8: Peer Group Rankings by ROE (Latest Year)
WITH LatestYear AS (
    SELECT MAX(year) AS max_yr FROM financial_ratios
)
SELECT 
    pg.peer_group_name, 
    r.company_id, 
    r.return_on_equity_pct, 
    RANK() OVER (PARTITION BY pg.peer_group_name ORDER BY r.return_on_equity_pct DESC) AS peer_rank,
    pg.is_benchmark
FROM financial_ratios r
JOIN peer_groups pg ON r.company_id = pg.company_id
WHERE r.year = (SELECT max_yr FROM LatestYear)
ORDER BY pg.peer_group_name, peer_rank;

-- Query 9: Average Valuation Multiples by Sector (Latest Year)
WITH LatestYear AS (
    SELECT MAX(year) AS max_yr FROM market_cap
)
SELECT 
    s.broad_sector,
    ROUND(AVG(m.pe_ratio), 2) AS avg_pe_ratio,
    ROUND(AVG(m.pb_ratio), 2) AS avg_pb_ratio,
    ROUND(AVG(m.ev_ebitda), 2) AS avg_ev_ebitda,
    COUNT(DISTINCT m.company_id) AS company_count
FROM market_cap m
JOIN sectors s ON m.company_id = s.company_id
WHERE m.year = (SELECT max_yr FROM LatestYear)
GROUP BY s.broad_sector
ORDER BY avg_pe_ratio DESC;

-- Query 10: Null Values and Completeness Scan across Companies Table
SELECT 
    COUNT(*) AS total_rows,
    SUM(CASE WHEN company_logo IS NULL THEN 1 ELSE 0 END) AS logo_nulls,
    SUM(CASE WHEN website IS NULL THEN 1 ELSE 0 END) AS website_nulls,
    SUM(CASE WHEN face_value IS NULL THEN 1 ELSE 0 END) AS face_value_nulls,
    SUM(CASE WHEN book_value IS NULL THEN 1 ELSE 0 END) AS book_value_nulls,
    SUM(CASE WHEN roce_percentage IS NULL THEN 1 ELSE 0 END) AS roce_nulls
FROM companies;
