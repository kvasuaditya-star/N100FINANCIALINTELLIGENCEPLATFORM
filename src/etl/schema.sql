-- PRAGMA foreign_keys = ON;

-- 1. companies table
CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR PRIMARY KEY,
    company_logo TEXT,
    company_name VARCHAR NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value NUMERIC,
    book_value NUMERIC,
    roce_percentage NUMERIC,
    roe_percentage NUMERIC
);

-- 2. sectors table
CREATE TABLE IF NOT EXISTS sectors (
    company_id VARCHAR PRIMARY KEY,
    broad_sector VARCHAR NOT NULL,
    sub_sector VARCHAR NOT NULL,
    index_weight_pct NUMERIC,
    market_cap_category VARCHAR,
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 3. profitandloss table
CREATE TABLE IF NOT EXISTS profitandloss (
    company_id VARCHAR,
    year VARCHAR,
    sales NUMERIC,
    expenses NUMERIC,
    operating_profit NUMERIC,
    opm_percentage NUMERIC,
    other_income NUMERIC,
    interest NUMERIC,
    depreciation NUMERIC,
    profit_before_tax NUMERIC,
    tax_percentage NUMERIC,
    net_profit NUMERIC,
    eps NUMERIC,
    dividend_payout NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 4. balancesheet table
CREATE TABLE IF NOT EXISTS balancesheet (
    company_id VARCHAR,
    year VARCHAR,
    equity_capital NUMERIC,
    reserves NUMERIC,
    borrowings NUMERIC,
    other_liabilities NUMERIC,
    total_liabilities NUMERIC,
    fixed_assets NUMERIC,
    cwip NUMERIC,
    investments NUMERIC,
    other_asset NUMERIC,
    total_assets NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 5. cashflow table
CREATE TABLE IF NOT EXISTS cashflow (
    company_id VARCHAR,
    year VARCHAR,
    operating_activity NUMERIC,
    investing_activity NUMERIC,
    financing_activity NUMERIC,
    net_cash_flow NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 6. analysis table
CREATE TABLE IF NOT EXISTS analysis (
    company_id VARCHAR PRIMARY KEY,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 7. documents table
CREATE TABLE IF NOT EXISTS documents (
    company_id VARCHAR,
    year INTEGER,
    annual_report TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 8. prosandcons table
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id VARCHAR,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 9. stock_prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    company_id VARCHAR,
    date VARCHAR,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC,
    volume INTEGER,
    adjusted_close NUMERIC,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 10. market_cap table
CREATE TABLE IF NOT EXISTS market_cap (
    company_id VARCHAR,
    year INTEGER,
    market_cap_crore NUMERIC,
    enterprise_value_crore NUMERIC,
    pe_ratio NUMERIC,
    pb_ratio NUMERIC,
    ev_ebitda NUMERIC,
    dividend_yield_pct NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 11. financial_ratios table
CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id VARCHAR,
    year VARCHAR,
    net_profit_margin_pct NUMERIC,
    operating_profit_margin_pct NUMERIC,
    return_on_equity_pct NUMERIC,
    debt_to_equity NUMERIC,
    interest_coverage NUMERIC,
    asset_turnover NUMERIC,
    free_cash_flow_cr NUMERIC,
    capex_cr NUMERIC,
    earnings_per_share NUMERIC,
    book_value_per_share NUMERIC,
    dividend_payout_ratio_pct NUMERIC,
    total_debt_cr NUMERIC,
    cash_from_operations_cr NUMERIC,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);

-- 12. peer_groups table
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name VARCHAR NOT NULL,
    company_id VARCHAR NOT NULL,
    is_benchmark BOOLEAN NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
);
