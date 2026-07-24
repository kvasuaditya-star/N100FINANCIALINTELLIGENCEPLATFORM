import sqlite3
conn = sqlite3.connect('data/nifty100.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM market_cap')
print('Market Cap rows:', c.fetchone()[0])

c.execute('SELECT company_id, year, market_cap_crore, pe_ratio, pb_ratio, dividend_yield_pct FROM market_cap LIMIT 5')
print('Sample market_cap:')
for r in c.fetchall():
    print(r)

c.execute("SELECT company_id, year, sales FROM profitandloss WHERE year LIKE '2024%' LIMIT 10")
print('\nLatest PL:')
for r in c.fetchall():
    print(r)

c.execute('SELECT pg.company_id, pg.peer_group_name, pg.is_benchmark FROM peer_groups pg WHERE pg.is_benchmark=1')
print('\nBenchmark companies:')
for r in c.fetchall():
    print(r)

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('\nAll tables:', [r[0] for r in c.fetchall()])

# Check latest year for financial_ratios
c.execute("SELECT MAX(year) FROM financial_ratios")
print('\nLatest year in financial_ratios:', c.fetchone()[0])

# Check how many companies have latest year data
c.execute("SELECT COUNT(DISTINCT company_id) FROM financial_ratios WHERE year = (SELECT MAX(year) FROM financial_ratios)")
print('Companies with latest year data:', c.fetchone()[0])

# Get a sample of latest year with all key metrics
c.execute("""
    SELECT fr.company_id, c.company_name, s.broad_sector, fr.year,
           fr.return_on_equity_pct, fr.debt_to_equity, fr.free_cash_flow_cr,
           fr.revenue_cagr_5yr, fr.pat_cagr_5yr, fr.interest_coverage,
           fr.icr_label, fr.net_profit_margin_pct, fr.operating_profit_margin_pct,
           fr.asset_turnover, fr.earnings_per_share, fr.eps_cagr_5yr,
           mc.pe_ratio, mc.pb_ratio, mc.dividend_yield_pct, mc.market_cap_crore
    FROM financial_ratios fr
    JOIN companies c ON fr.company_id = c.id
    LEFT JOIN sectors s ON fr.company_id = s.company_id
    LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(SUBSTR(fr.year, 1, 4) AS INTEGER) = mc.year
    WHERE fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = fr.company_id)
    LIMIT 10
""")
print('\nLatest year merged data:')
for r in c.fetchall():
    print(r)

conn.close()
