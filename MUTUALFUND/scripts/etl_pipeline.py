import os
import sqlite3
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
import warnings

# Import live NAV fetcher
from live_nav_fetch import fetch_all_nav, SCHEME_CODES

# Setup dynamic paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"
DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"

def clean_nav_history():
    print("Cleaning NAV history...")
    nav_raw_path = RAW_DIR / "02_nav_history.csv"
    if not nav_raw_path.exists():
        print(f"Error: Raw NAV history file {nav_raw_path} not found.")
        return
        
    df = pd.read_csv(nav_raw_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    df['amfi_code'] = pd.to_numeric(df['amfi_code'], errors='coerce')
    df = df.dropna(subset=['amfi_code', 'date', 'nav'])
    df = df[df['nav'] > 0]
    
    # Merge live NAV files from raw directory (e.g., 118632_NAV.csv)
    live_files = list(RAW_DIR.glob("*_NAV.csv"))
    print(f"Found {len(live_files)} live NAV files to merge...")
    
    live_dfs = []
    for file in live_files:
        try:
            amfi_code = int(file.stem.split('_')[0])
            live_df = pd.read_csv(file)
            # Live API date is DD-MM-YYYY, parse accordingly
            live_df['date'] = pd.to_datetime(live_df['date'], format='%d-%m-%y', errors='coerce')
            if live_df['date'].isnull().all():
                # Try fallback format
                live_df['date'] = pd.to_datetime(live_df['date'], errors='coerce')
                
            live_df['nav'] = pd.to_numeric(live_df['nav'], errors='coerce')
            live_df['amfi_code'] = amfi_code
            live_df = live_df.dropna(subset=['date', 'nav'])
            live_dfs.append(live_df)
        except Exception as e:
            print(f"Error parsing live file {file.name}: {e}")
            
    if live_dfs:
        live_df_all = pd.concat(live_dfs, ignore_index=True)
        # Combine with historical dataframe
        df = pd.concat([df, live_df_all], ignore_index=True)
        
    # Drop duplicates on amfi_code and date
    df = df.drop_duplicates(subset=['amfi_code', 'date'])
    df = df.sort_values(['amfi_code', 'date'])
    
    # Reindex and forward-fill missing dates (weekends/holidays) for each fund
    def fill_missing_dates(group):
        if group.empty:
            return group
        code = group['amfi_code'].iloc[0]
        # Reindex to full date range from min to max date of this fund
        min_date = group['date'].min()
        max_date = group['date'].max()
        full_idx = pd.date_range(min_date, max_date, freq='D')
        
        group = group.set_index('date').reindex(full_idx)
        group['amfi_code'] = code
        group['nav'] = group['nav'].ffill()  # Rubric: always ffill after reindexing
        group = group.rename_axis('date').reset_index()
        return group

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        df = df.groupby('amfi_code', group_keys=False).apply(fill_missing_dates).reset_index(drop=True)
        
    # Format date to YYYY-MM-DD
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Save to processed
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DIR / "02_nav_history.csv", index=False)
    print(f"Cleaned and saved 02_nav_history.csv: {len(df)} rows")

def clean_investor_transactions():
    print("Cleaning investor transactions...")
    tx_raw_path = RAW_DIR / "08_investor_transactions.csv"
    if not tx_raw_path.exists():
        print(f"Warning: Transaction file {tx_raw_path} not found.")
        return
        
    df = pd.read_csv(tx_raw_path)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df = df.dropna(subset=['transaction_date'])
    df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
    
    # Standardise transaction_type
    def std_trans(x):
        x = str(x).upper().strip()
        if 'SIP' in x: return 'SIP'
        if 'LUMP' in x: return 'Lumpsum'
        if 'REDEMP' in x or 'WITHDRAW' in x: return 'Redemption'
        return 'Other'
        
    df['transaction_type'] = df['transaction_type'].apply(std_trans)
    df['amount_inr'] = pd.to_numeric(df['amount_inr'], errors='coerce')
    df = df[df['amount_inr'] > 0]
    
    valid_kyc = ['Verified', 'Pending', 'Rejected']
    df['kyc_status'] = df['kyc_status'].apply(
        lambda x: str(x).strip().title() if pd.notna(x) and str(x).strip().title() in valid_kyc else 'Unknown'
    )
    df = df.drop_duplicates()
    
    df.to_csv(PROCESSED_DIR / "08_investor_transactions.csv", index=False)
    print(f"Cleaned and saved 08_investor_transactions.csv: {len(df)} rows")

def clean_scheme_performance():
    print("Cleaning scheme performance...")
    perf_raw_path = RAW_DIR / "07_scheme_performance.csv"
    if not perf_raw_path.exists():
        print(f"Warning: Performance file {perf_raw_path} not found.")
        return
        
    df = pd.read_csv(perf_raw_path)
    
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct', 'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio']
    for col in return_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    if 'sharpe_ratio' in df.columns:
        df['negative_sharpe_flag'] = (df['sharpe_ratio'] < 0).astype(int)
        
    if 'expense_ratio_pct' in df.columns:
        df['expense_ratio_pct'] = pd.to_numeric(df['expense_ratio_pct'], errors='coerce')
        # Filter realistic expense ratios
        df = df[(df['expense_ratio_pct'] >= 0.0) & (df['expense_ratio_pct'] <= 5.0)]
        
    df = df.drop_duplicates()
    df.to_csv(PROCESSED_DIR / "07_scheme_performance.csv", index=False)
    print(f"Cleaned and saved 07_scheme_performance.csv: {len(df)} rows")

def clean_other_datasets():
    print("Cleaning other files...")
    other_files = [
        '01_fund_master.csv', '03_aum_by_fund_house.csv', '04_monthly_sip_inflows.csv',
        '05_category_inflows.csv', '06_industry_folio_count.csv', '09_portfolio_holdings.csv',
        '10_benchmark_indices.csv'
    ]
    
    for f in other_files:
        path = RAW_DIR / f
        if not path.exists():
            continue
            
        df = pd.read_csv(path)
        df = df.drop_duplicates()
        
        for col in ['date', 'month', 'portfolio_date']:
            if col in df.columns:
                if col == 'month':
                    # Parse as period or date, then format
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m')
                else:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
                df = df.dropna(subset=[col])
                
        df.to_csv(PROCESSED_DIR / f, index=False)
        print(f"Cleaned and saved {f}: {len(df)} rows")

def init_db():
    print(f"Initializing SQLite database at {DB_PATH}...")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    if DB_PATH.exists():
        try:
            os.remove(DB_PATH)
            print("Removed existing database for a clean schema re-run.")
        except Exception as e:
            print(f"Error removing old database: {e}")
            
    with sqlite3.connect(DB_PATH) as conn:
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, 'r') as f:
                schema_script = f.read()
            conn.executescript(schema_script)
            print("Database schema created successfully.")
        else:
            print(f"Error: Schema SQL file {SCHEMA_PATH} not found.")

def load_to_sqlite():
    print("Loading cleaned datasets into SQLite...")
    engine = create_engine(f'sqlite:///{DB_PATH}')
    
    file_table_mapping = {
        '01_fund_master.csv': 'dim_fund',
        '02_nav_history.csv': 'fact_nav',
        '03_aum_by_fund_house.csv': 'fact_aum',
        '04_monthly_sip_inflows.csv': 'monthly_sip_inflows',
        '05_category_inflows.csv': 'category_inflows',
        '06_industry_folio_count.csv': 'industry_folio_count',
        '07_scheme_performance.csv': 'fact_performance',
        '08_investor_transactions.csv': 'fact_transactions',
        '09_portfolio_holdings.csv': 'portfolio_holdings',
        '10_benchmark_indices.csv': 'benchmark_indices'
    }
    
    for filename, table_name in file_table_mapping.items():
        file_path = PROCESSED_DIR / filename
        if not file_path.exists():
            print(f"Warning: {file_path} not found.")
            continue
            
        df = pd.read_csv(file_path)
        print(f"Loading {filename} -> table {table_name} ({len(df)} rows)...")
        # Load data, appending to schema structure
        df.to_sql(table_name, engine, if_exists='append', index=False)
        
    print("All datasets loaded successfully into SQLite.")

def run_etl():
    print("=" * 60)
    print("MUTUAL FUND CAPSTONE ETL PIPELINE")
    print("=" * 60)
    
    # 1. Fetch live NAV
    fetch_all_nav()
    
    # 2. Clean all files
    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()
    clean_other_datasets()
    
    # 3. DB Setup
    init_db()
    load_to_sqlite()
    
    print("\nETL Pipeline Completed Successfully!")
    print("=" * 60)

if __name__ == '__main__':
    run_etl()
