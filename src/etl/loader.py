import os
import sys
import time
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# Ensure we can import from src.etl
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.normaliser import normalize_ticker, normalize_year
from etl.validator import DataValidator

# Load environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs("output", exist_ok=True)

def init_db():
    """Initializes the database schema."""
    conn = sqlite3.connect(DB_PATH)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Read schema
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        schema_path = "db/schema.sql"
        
    print(f"Initializing database {DB_PATH} using {schema_path}...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

def load_data():
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    validator = DataValidator()
    
    # Audit log collection
    audit_log = []
    
    def log_audit(table, rows_in, rows_out, rejected, runtime):
        audit_log.append({
            'table': table,
            'rows_in': rows_in,
            'rows_out': rows_out,
            'rejected': rejected,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'runtime_s': round(runtime, 3)
        })

    # --- 1. COMPANIES ---
    t0 = time.time()
    companies_path = "data/raw/companies.xlsx"
    print(f"Loading {companies_path}...")
    df_co_raw = pd.read_excel(companies_path, header=1)
    df_co = df_co_raw.copy()
    df_co.columns = df_co.columns.str.strip()
    
    # Normalise columns
    df_co['id'] = df_co['id'].apply(normalize_ticker)
    df_co['company_name'] = df_co['company_name'].astype(str).str.replace('\n', ' ').str.strip()
    
    # Run DQ validations
    is_valid_pk = validator.validate_dq_01_companies_pk(df_co)
    if not is_valid_pk:
        raise ValueError("CRITICAL: Companies table PK uniqueness check failed (DQ-01). Halting load.")
        
    df_co = validator.validate_dq_08_ticker_format("companies", df_co)
    
    # Insert to DB
    # We map columns to SQLite schema
    cols = ['id', 'company_logo', 'company_name', 'chart_link', 'about_company', 
            'website', 'nse_profile', 'bse_profile', 'face_value', 'book_value', 
            'roce_percentage', 'roe_percentage']
    df_co_insert = df_co[cols]
    
    df_co_insert.to_sql('companies', conn, if_exists='append', index=False)
    valid_companies = set(df_co['id'].unique())
    
    log_audit('companies', len(df_co_raw), len(df_co_insert), len(df_co_raw) - len(df_co_insert), time.time() - t0)

    # --- 2. SECTORS ---
    t0 = time.time()
    sectors_path = "data/supporting/sectors.xlsx"
    print(f"Loading {sectors_path}...")
    df_sec_raw = pd.read_excel(sectors_path, header=0)
    df_sec = df_sec_raw.copy()
    df_sec.columns = df_sec.columns.str.strip()
    df_sec['company_id'] = df_sec['company_id'].apply(normalize_ticker)
    
    df_sec = validator.validate_dq_08_ticker_format("sectors", df_sec)
    df_sec = validator.validate_dq_03_fk_integrity("sectors", df_sec, valid_companies)
    
    cols = ['company_id', 'broad_sector', 'sub_sector', 'index_weight_pct', 'market_cap_category']
    df_sec_insert = df_sec[cols]
    df_sec_insert.to_sql('sectors', conn, if_exists='append', index=False)
    
    log_audit('sectors', len(df_sec_raw), len(df_sec_insert), len(df_sec_raw) - len(df_sec_insert), time.time() - t0)
    
    # Sector reference for DQ-06
    df_sectors_ref = df_sec_insert.copy()

    # --- 3. PROFIT & LOSS ---
    t0 = time.time()
    pl_path = "data/raw/profitandloss.xlsx"
    print(f"Loading {pl_path}...")
    df_pl_raw = pd.read_excel(pl_path, header=1)
    df_pl = df_pl_raw.copy()
    df_pl.columns = df_pl.columns.str.strip()
    df_pl['company_id'] = df_pl['company_id'].apply(normalize_ticker)
    df_pl['year'] = df_pl['year'].apply(normalize_year)
    
    df_pl = validator.validate_dq_08_ticker_format("profitandloss", df_pl)
    df_pl = validator.validate_dq_07_year_format("profitandloss", df_pl)
    df_pl = validator.validate_dq_02_annual_pk("profitandloss", df_pl)
    df_pl = validator.validate_dq_03_fk_integrity("profitandloss", df_pl, valid_companies)
    
    df_pl = validator.validate_dq_05_opm_crosscheck(df_pl)
    df_pl = validator.validate_dq_06_positive_sales(df_pl, df_sectors_ref)
    df_pl = validator.validate_dq_11_tax_rate(df_pl)
    df_pl = validator.validate_dq_12_dividend_cap(df_pl)
    df_pl = validator.validate_dq_14_eps_sign(df_pl)
    
    cols = ['company_id', 'year', 'sales', 'expenses', 'operating_profit', 'opm_percentage',
            'other_income', 'interest', 'depreciation', 'profit_before_tax', 'tax_percentage',
            'net_profit', 'eps', 'dividend_payout']
    df_pl_insert = df_pl[cols]
    df_pl_insert.to_sql('profitandloss', conn, if_exists='append', index=False)
    
    log_audit('profitandloss', len(df_pl_raw), len(df_pl_insert), len(df_pl_raw) - len(df_pl_insert), time.time() - t0)

    # --- 4. BALANCE SHEET ---
    t0 = time.time()
    bs_path = "data/raw/balancesheet.xlsx"
    print(f"Loading {bs_path}...")
    df_bs_raw = pd.read_excel(bs_path, header=1)
    df_bs = df_bs_raw.copy()
    df_bs.columns = df_bs.columns.str.strip()
    df_bs['company_id'] = df_bs['company_id'].apply(normalize_ticker)
    df_bs['year'] = df_bs['year'].apply(normalize_year)
    
    df_bs = validator.validate_dq_08_ticker_format("balancesheet", df_bs)
    df_bs = validator.validate_dq_07_year_format("balancesheet", df_bs)
    df_bs = validator.validate_dq_02_annual_pk("balancesheet", df_bs)
    df_bs = validator.validate_dq_03_fk_integrity("balancesheet", df_bs, valid_companies)
    
    df_bs = validator.validate_dq_04_bs_balance(df_bs)
    df_bs = validator.validate_dq_10_fixed_assets(df_bs)
    df_bs = validator.validate_dq_15_bse_balance(df_bs)
    
    cols = ['company_id', 'year', 'equity_capital', 'reserves', 'borrowings', 'other_liabilities',
            'total_liabilities', 'fixed_assets', 'cwip', 'investments', 'other_asset', 'total_assets']
    df_bs_insert = df_bs[cols]
    df_bs_insert.to_sql('balancesheet', conn, if_exists='append', index=False)
    
    log_audit('balancesheet', len(df_bs_raw), len(df_bs_insert), len(df_bs_raw) - len(df_bs_insert), time.time() - t0)

    # --- 5. CASH FLOW ---
    t0 = time.time()
    cf_path = "data/raw/cashflow.xlsx"
    print(f"Loading {cf_path}...")
    df_cf_raw = pd.read_excel(cf_path, header=1)
    df_cf = df_cf_raw.copy()
    df_cf.columns = df_cf.columns.str.strip()
    df_cf['company_id'] = df_cf['company_id'].apply(normalize_ticker)
    df_cf['year'] = df_cf['year'].apply(normalize_year)
    
    df_cf = validator.validate_dq_08_ticker_format("cashflow", df_cf)
    df_cf = validator.validate_dq_07_year_format("cashflow", df_cf)
    df_cf = validator.validate_dq_02_annual_pk("cashflow", df_cf)
    df_cf = validator.validate_dq_03_fk_integrity("cashflow", df_cf, valid_companies)
    
    df_cf = validator.validate_dq_09_net_cash(df_cf)
    
    cols = ['company_id', 'year', 'operating_activity', 'investing_activity', 'financing_activity', 'net_cash_flow']
    df_cf_insert = df_cf[cols]
    df_cf_insert.to_sql('cashflow', conn, if_exists='append', index=False)
    
    log_audit('cashflow', len(df_cf_raw), len(df_cf_insert), len(df_cf_raw) - len(df_cf_insert), time.time() - t0)

    # --- 6. ANALYSIS ---
    t0 = time.time()
    analysis_path = "data/raw/analysis.xlsx"
    print(f"Loading {analysis_path}...")
    df_an_raw = pd.read_excel(analysis_path, header=1)
    df_an = df_an_raw.copy()
    df_an.columns = df_an.columns.str.strip()
    df_an['company_id'] = df_an['company_id'].apply(normalize_ticker)
    
    df_an = validator.validate_dq_08_ticker_format("analysis", df_an)
    df_an = validator.validate_dq_03_fk_integrity("analysis", df_an, valid_companies)
    
    # Analysis is 1:1 with companies, remove any duplicate company_id rows
    df_an = df_an.drop_duplicates(subset=['company_id'], keep='last')
    
    cols = ['company_id', 'compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']
    df_an_insert = df_an[cols]
    df_an_insert.to_sql('analysis', conn, if_exists='append', index=False)
    
    log_audit('analysis', len(df_an_raw), len(df_an_insert), len(df_an_raw) - len(df_an_insert), time.time() - t0)

    # --- 7. DOCUMENTS ---
    t0 = time.time()
    docs_path = "data/raw/documents.xlsx"
    print(f"Loading {docs_path}...")
    df_doc_raw = pd.read_excel(docs_path, header=1)
    df_doc = df_doc_raw.copy()
    df_doc.columns = df_doc.columns.str.strip()
    df_doc['company_id'] = df_doc['company_id'].apply(normalize_ticker)
    
    # Documents uses Year (integer), let's validate and convert
    df_doc['Year'] = pd.to_numeric(df_doc['Year'], errors='coerce').fillna(0).astype(int)
    
    df_doc = validator.validate_dq_08_ticker_format("documents", df_doc)
    df_doc = validator.validate_dq_03_fk_integrity("documents", df_doc, valid_companies)
    
    # Check duplicate (company_id, Year)
    df_doc = df_doc.drop_duplicates(subset=['company_id', 'Year'], keep='last')
    
    # DQ-13: URL check
    df_doc = validator.validate_dq_13_urls(df_doc)
    
    cols = ['company_id', 'Year', 'Annual_Report']
    df_doc_insert = df_doc[cols].rename(columns={'Year': 'year', 'Annual_Report': 'annual_report'})
    df_doc_insert.to_sql('documents', conn, if_exists='append', index=False)
    
    log_audit('documents', len(df_doc_raw), len(df_doc_insert), len(df_doc_raw) - len(df_doc_insert), time.time() - t0)

    # --- 8. PROS AND CONS ---
    t0 = time.time()
    pc_path = "data/raw/prosandcons.xlsx"
    print(f"Loading {pc_path}...")
    df_pc_raw = pd.read_excel(pc_path, header=1)
    df_pc = df_pc_raw.copy()
    df_pc.columns = df_pc.columns.str.strip()
    df_pc['company_id'] = df_pc['company_id'].apply(normalize_ticker)
    
    df_pc = validator.validate_dq_08_ticker_format("prosandcons", df_pc)
    df_pc = validator.validate_dq_03_fk_integrity("prosandcons", df_pc, valid_companies)
    
    cols = ['company_id', 'pros', 'cons']
    df_pc_insert = df_pc[cols]
    df_pc_insert.to_sql('prosandcons', conn, if_exists='append', index=False)
    
    log_audit('prosandcons', len(df_pc_raw), len(df_pc_insert), len(df_pc_raw) - len(df_pc_insert), time.time() - t0)

    # --- 9. STOCK PRICES ---
    t0 = time.time()
    prices_path = "data/supporting/stock_prices.xlsx"
    print(f"Loading {prices_path}...")
    df_pr_raw = pd.read_excel(prices_path, header=0)
    df_pr = df_pr_raw.copy()
    df_pr.columns = df_pr.columns.str.strip()
    df_pr['company_id'] = df_pr['company_id'].apply(normalize_ticker)
    
    df_pr = validator.validate_dq_08_ticker_format("stock_prices", df_pr)
    
    # Date validation
    invalid_dates = ~df_pr['date'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)
    if invalid_dates.any():
        for idx, row in df_pr[invalid_dates].iterrows():
            validator.log_failure(
                company_id=row['company_id'],
                year=row['date'],
                field='date',
                rule_id='DQ-07',
                issue=f"Invalid stock price date format: {row['date']}",
                severity='CRITICAL'
            )
        df_pr = df_pr[~invalid_dates]
        
    df_pr = validator.validate_dq_03_fk_integrity("stock_prices", df_pr, valid_companies)
    df_pr = df_pr.drop_duplicates(subset=['company_id', 'date'], keep='last')
    
    cols = ['company_id', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'adjusted_close']
    df_pr_insert = df_pr[cols]
    df_pr_insert.to_sql('stock_prices', conn, if_exists='append', index=False)
    
    log_audit('stock_prices', len(df_pr_raw), len(df_pr_insert), len(df_pr_raw) - len(df_pr_insert), time.time() - t0)

    # --- 10. MARKET CAP ---
    t0 = time.time()
    mc_path = "data/supporting/market_cap.xlsx"
    print(f"Loading {mc_path}...")
    df_mc_raw = pd.read_excel(mc_path, header=0)
    df_mc = df_mc_raw.copy()
    df_mc.columns = df_mc.columns.str.strip()
    df_mc['company_id'] = df_mc['company_id'].apply(normalize_ticker)
    df_mc['year'] = pd.to_numeric(df_mc['year'], errors='coerce').fillna(0).astype(int)
    
    df_mc = validator.validate_dq_08_ticker_format("market_cap", df_mc)
    df_mc = validator.validate_dq_03_fk_integrity("market_cap", df_mc, valid_companies)
    df_mc = df_mc.drop_duplicates(subset=['company_id', 'year'], keep='last')
    
    cols = ['company_id', 'year', 'market_cap_crore', 'enterprise_value_crore', 'pe_ratio', 'pb_ratio', 'ev_ebitda', 'dividend_yield_pct']
    df_mc_insert = df_mc[cols]
    df_mc_insert.to_sql('market_cap', conn, if_exists='append', index=False)
    
    log_audit('market_cap', len(df_mc_raw), len(df_mc_insert), len(df_mc_raw) - len(df_mc_insert), time.time() - t0)

    # --- 11. FINANCIAL RATIOS ---
    t0 = time.time()
    ratios_path = "data/supporting/financial_ratios.xlsx"
    print(f"Loading {ratios_path}...")
    df_rat_raw = pd.read_excel(ratios_path, header=0)
    df_rat = df_rat_raw.copy()
    df_rat.columns = df_rat.columns.str.strip()
    df_rat['company_id'] = df_rat['company_id'].apply(normalize_ticker)
    df_rat['year'] = df_rat['year'].apply(normalize_year)
    
    df_rat = validator.validate_dq_08_ticker_format("financial_ratios", df_rat)
    df_rat = validator.validate_dq_07_year_format("financial_ratios", df_rat)
    df_rat = validator.validate_dq_02_annual_pk("financial_ratios", df_rat)
    df_rat = validator.validate_dq_03_fk_integrity("financial_ratios", df_rat, valid_companies)
    
    cols = ['company_id', 'year', 'net_profit_margin_pct', 'operating_profit_margin_pct', 'return_on_equity_pct',
            'debt_to_equity', 'interest_coverage', 'asset_turnover', 'free_cash_flow_cr', 'capex_cr',
            'earnings_per_share', 'book_value_per_share', 'dividend_payout_ratio_pct', 'total_debt_cr', 'cash_from_operations_cr']
    df_rat_insert = df_rat[cols]
    df_rat_insert.to_sql('financial_ratios', conn, if_exists='append', index=False)
    
    log_audit('financial_ratios', len(df_rat_raw), len(df_rat_insert), len(df_rat_raw) - len(df_rat_insert), time.time() - t0)

    # --- 12. PEER GROUPS ---
    t0 = time.time()
    peers_path = "data/supporting/peer_groups.xlsx"
    print(f"Loading {peers_path}...")
    df_pg_raw = pd.read_excel(peers_path, header=0)
    df_pg = df_pg_raw.copy()
    df_pg.columns = df_pg.columns.str.strip()
    df_pg['company_id'] = df_pg['company_id'].apply(normalize_ticker)
    df_pg['is_benchmark'] = df_pg['is_benchmark'].astype(bool).astype(int)
    
    df_pg = validator.validate_dq_08_ticker_format("peer_groups", df_pg)
    df_pg = validator.validate_dq_03_fk_integrity("peer_groups", df_pg, valid_companies)
    
    cols = ['id', 'peer_group_name', 'company_id', 'is_benchmark']
    df_pg_insert = df_pg[cols]
    df_pg_insert.to_sql('peer_groups', conn, if_exists='append', index=False)
    
    log_audit('peer_groups', len(df_pg_raw), len(df_pg_insert), len(df_pg_raw) - len(df_pg_insert), time.time() - t0)

    # --- DATASET-LEVEL VALIDATION: COVERAGE CHECK (DQ-16) ---
    print("Running coverage validation (DQ-16)...")
    validator.validate_dq_16_coverage(df_pl_insert, df_bs_insert, df_cf_insert)

    conn.commit()
    conn.close()
    
    # Save validation failures
    validator.save_failures("output/validation_failures.csv")
    
    # Save load audit log
    df_audit = pd.DataFrame(audit_log)
    df_audit.to_csv("output/load_audit.csv", index=False)
    print(f"Saved load audit log with {len(audit_log)} entries to output/load_audit.csv")

if __name__ == "__main__":
    load_data()
