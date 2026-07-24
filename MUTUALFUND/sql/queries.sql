-- queries.sql
-- 10 Analytical SQL Queries for Bluestock Mutual Fund Analytics


-- Query 1: Top 5 funds by AUM (Assets Under Management)
SELECT
    fp.amfi_code,
    fp.scheme_name,
    fp.fund_house,
    fp.aum_crore
FROM fact_performance fp
ORDER BY fp.aum_crore DESC
LIMIT 5;


-- Query 2: Average NAV per month for each fund
SELECT
    fn.amfi_code,
    df.scheme_name,
    SUBSTR(fn.date, 1, 7) AS month,
    ROUND(AVG(fn.nav), 4) AS avg_nav
FROM fact_nav fn
JOIN dim_fund df ON fn.amfi_code = df.amfi_code
GROUP BY fn.amfi_code, df.scheme_name, SUBSTR(fn.date, 1, 7)
ORDER BY fn.amfi_code, month;


-- Query 3: SIP inflow Year-over-Year (YoY) growth
SELECT
    month,
    sip_inflow_crore,
    yoy_growth_pct
FROM monthly_sip_inflows
WHERE yoy_growth_pct IS NOT NULL
ORDER BY month;


-- Query 4: Total transactions by state
SELECT
    state,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- Query 5: Funds with expense ratio less than 1%
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;


-- Query 6: Total Lumpsum amount invested per fund
SELECT
    ft.amfi_code,
    df.scheme_name,
    COUNT(*) AS lumpsum_count,
    ROUND(SUM(ft.amount_inr), 2) AS total_lumpsum_amount
FROM fact_transactions ft
JOIN dim_fund df ON ft.amfi_code = df.amfi_code
WHERE ft.transaction_type = 'Lumpsum'
GROUP BY ft.amfi_code, df.scheme_name
ORDER BY total_lumpsum_amount DESC;


-- Query 7: Top 10 stocks by portfolio weight across all funds
SELECT
    stock_symbol,
    stock_name,
    sector,
    COUNT(DISTINCT amfi_code) AS num_funds_holding,
    ROUND(AVG(weight_pct), 2) AS avg_weight_pct,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM portfolio_holdings
GROUP BY stock_symbol, stock_name, sector
ORDER BY total_market_value_cr DESC
LIMIT 10;


-- Query 8: Best performing funds by 3-year return
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    return_3yr_pct,
    sharpe_ratio,
    risk_grade
FROM fact_performance
WHERE return_3yr_pct IS NOT NULL
ORDER BY return_3yr_pct DESC
LIMIT 10;


-- Query 9: Monthly trend of total SIP accounts (in crores)
SELECT
    month,
    active_sip_accounts_crore,
    new_sip_accounts_lakh,
    sip_aum_lakh_crore
FROM monthly_sip_inflows
ORDER BY month;


-- Query 10: Average transaction amount by age group and gender
SELECT
    age_group,
    gender,
    COUNT(*) AS num_transactions,
    ROUND(AVG(amount_inr), 2) AS avg_amount,
    ROUND(SUM(amount_inr), 2) AS total_amount
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY avg_amount DESC;
