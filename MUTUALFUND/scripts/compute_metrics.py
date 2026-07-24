import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Setup dynamic paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def run_calculations():
    print("=" * 60)
    print("COMPUTING MATHEMATICAL PERFORMANCE METRICS")
    print("=" * 60)
    
    if not DB_PATH.exists():
        print(f"Error: Database {DB_PATH} not found. Please run etl_pipeline.py first.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load data
    nav_df = pd.read_sql_query("SELECT * FROM fact_nav", conn)
    fund_df = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    perf_df = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    tx_df = pd.read_sql_query("SELECT * FROM fact_transactions", conn)
    holdings_df = pd.read_sql_query("SELECT * FROM portfolio_holdings", conn)
    benchmark_df = pd.read_sql_query("SELECT * FROM benchmark_indices", conn)
    
    # Convert dates to datetime
    nav_df['date'] = pd.to_datetime(nav_df['date'])
    tx_df['transaction_date'] = pd.to_datetime(tx_df['transaction_date'])
    benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
    
    print("Data loaded successfully from SQLite.")
    
    # Sort NAV data
    nav_sorted = nav_df.sort_values(['amfi_code', 'date'])
    nav_sorted['daily_return'] = nav_sorted.groupby('amfi_code')['nav'].pct_change()
    
    # 2. Compute Benchmark Returns (Nifty 50 and Nifty 100)
    bench_pivoted = benchmark_df.pivot(index='date', columns='index_name', values='close_value')
    bench_pivoted = bench_pivoted.ffill()
    bench_returns = bench_pivoted.pct_change().dropna()
    
    # Risk-free rate (6% annual)
    Rf = 0.06
    daily_rf = Rf / 252
    
    results = []
    
    for idx, row in fund_df.iterrows():
        amfi = row['amfi_code']
        scheme_name = row['scheme_name']
        category = row['category']
        sub_category = row['sub_category']
        
        fund_nav = nav_sorted[nav_sorted['amfi_code'] == amfi].dropna(subset=['nav'])
        if len(fund_nav) < 30:
            continue
            
        first_nav = fund_nav['nav'].iloc[0]
        last_nav = fund_nav['nav'].iloc[-1]
        n_trading_days = len(fund_nav)
        
        # CAGR based on trading days: (Ending/Beginning) ** (252 / n_trading_days) - 1
        cagr = (last_nav / first_nav) ** (252 / n_trading_days) - 1
        
        # 1Yr CAGR, 3Yr CAGR, 5Yr CAGR if data allows
        # We can also approximate with actual windows in trading days:
        # 1Yr ~ 252 trading days, 3Yr ~ 756 trading days, 5Yr ~ 1260 trading days
        cagr1 = None
        cagr3 = None
        cagr5 = cagr  # Total period CAGR
        
        if n_trading_days >= 252:
            cagr1 = (last_nav / fund_nav['nav'].iloc[-252]) ** (252 / 252) - 1
        if n_trading_days >= 756:
            cagr3 = (last_nav / fund_nav['nav'].iloc[-756]) ** (252 / 756) - 1
            
        fund_returns = fund_nav['daily_return'].dropna()
        vol_daily = fund_returns.std()
        vol_ann = vol_daily * np.sqrt(252)
        
        # Sharpe ratio: (CAGR - Rf) / Annualized Volatility
        # If CAGR is not available, we can compute it on excess returns
        sharpe = (cagr - Rf) / vol_ann if vol_ann > 0 else 0
        
        # Downside Volatility and Sortino
        downside_returns = fund_returns[fund_returns < 0]
        downside_vol_daily = np.sqrt((downside_returns ** 2).mean())
        downside_vol_ann = downside_vol_daily * np.sqrt(252)
        sortino = (cagr - Rf) / downside_vol_ann if downside_vol_ann > 0 else 0
        
        # OLS Regression for Beta against Nifty 100
        # Realign fund returns and index returns
        aligned_df = pd.DataFrame({'fund': fund_returns}).join(bench_returns['NIFTY100'] if 'NIFTY100' in bench_returns.columns else bench_returns.iloc[:,0], how='inner')
        if len(aligned_df) >= 30:
            slope, intercept, r_val, p_val, std_err = stats.linregress(aligned_df.iloc[:, 1], aligned_df['fund'])
            beta = slope
            alpha_ann = intercept * 252
            r_sq = r_val ** 2
        else:
            beta, alpha_ann, r_sq = 1.0, 0.0, 0.0
            
        # Maximum Drawdown
        running_max = fund_nav['nav'].cummax()
        drawdown = fund_nav['nav'] / running_max - 1
        max_dd = drawdown.min()
        
        # 95% Historical VaR and CVaR
        var_95 = np.percentile(fund_returns, 5)
        cvar_95 = fund_returns[fund_returns <= var_95].mean()
        
        results.append({
            'amfi_code': amfi,
            'scheme_name': scheme_name,
            'category': category,
            'sub_category': sub_category,
            'cagr_5yr': cagr5,
            'cagr_3yr': cagr3 if cagr3 is not None else cagr,
            'cagr_1yr': cagr1 if cagr1 is not None else cagr,
            'volatility_ann': vol_ann,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'alpha_ann': alpha_ann,
            'beta': beta,
            'r_squared': r_sq,
            'max_drawdown': max_dd,
            'var_95_pct': -var_95 * 100,
            'cvar_95_pct': -cvar_95 * 100
        })
        
    metrics_df = pd.DataFrame(results)
    
    # Save files to root and processed directory
    metrics_df.to_csv(PROCESSED_DIR / "fund_scorecard.csv", index=False)
    metrics_df.to_csv(BASE_DIR / "fund_scorecard.csv", index=False)
    
    alpha_beta_df = metrics_df[['scheme_name', 'category', 'alpha_ann', 'beta', 'r_squared', 'sharpe_ratio']]
    alpha_beta_df.to_csv(PROCESSED_DIR / "alpha_beta.csv", index=False)
    alpha_beta_df.to_csv(BASE_DIR / "alpha_beta.csv", index=False)
    
    var_cvar_df = metrics_df[['amfi_code', 'scheme_name', 'category', 'var_95_pct', 'cvar_95_pct']]
    var_cvar_df.to_csv(PROCESSED_DIR / "var_cvar_report.csv", index=False)
    var_cvar_df.to_csv(BASE_DIR / "var_cvar_report.csv", index=False)
    
    print("Performance metric CSVs exported successfully.")
    
    # 3. Update SQLite Database fact_performance table with correct values
    c = conn.cursor()
    for idx, row in metrics_df.iterrows():
        # Map values to the fact_performance columns
        c.execute("""
            UPDATE fact_performance
            SET return_1yr_pct = ?,
                return_3yr_pct = ?,
                return_5yr_pct = ?,
                alpha = ?,
                beta = ?,
                sharpe_ratio = ?,
                sortino_ratio = ?,
                std_dev_ann_pct = ?,
                max_drawdown_pct = ?
            WHERE amfi_code = ?
        """, (
            float(row['cagr_1yr'] * 100),
            float(row['cagr_3yr'] * 100),
            float(row['cagr_5yr'] * 100),
            float(row['alpha_ann']),
            float(row['beta']),
            float(row['sharpe_ratio']),
            float(row['sortino_ratio']),
            float(row['volatility_ann'] * 100),
            float(row['max_drawdown'] * 100),
            str(row['amfi_code'])
        ))
    conn.commit()
    print("Database fact_performance table updated.")
    
    # 4. Sector HHI Calculation (concentration)
    equity_amfis = fund_df[fund_df['category'] == 'Equity']['amfi_code'].unique()
    equity_holdings = holdings_df[holdings_df['amfi_code'].isin(equity_amfis)]
    
    hhi_results = []
    for amfi in equity_holdings['amfi_code'].unique():
        fund_name = fund_df[fund_df['amfi_code'] == amfi]['scheme_name'].iloc[0]
        fund_hold = equity_holdings[equity_holdings['amfi_code'] == amfi]
        
        # Sector weights sum
        sector_weights = fund_hold.groupby('sector')['weight_pct'].sum()
        hhi = (sector_weights ** 2).sum()
        
        max_sector = "None"
        max_sector_weight = 0
        if not sector_weights.empty:
            max_sector = sector_weights.idxmax()
            max_sector_weight = sector_weights.max()
            
        hhi_results.append({
            'amfi_code': amfi,
            'scheme_name': fund_name,
            'hhi_score': hhi,
            'unique_sectors_count': len(sector_weights),
            'top_sector': max_sector,
            'top_sector_weight_pct': max_sector_weight
        })
        
    hhi_df = pd.DataFrame(hhi_results).sort_values('hhi_score', ascending=False)
    hhi_df.to_csv(PROCESSED_DIR / "sector_hhi.csv", index=False)
    hhi_df.to_csv(BASE_DIR / "sector_hhi.csv", index=False)
    print("Sector HHI concentration computed and saved.")
    
    # 5. Cohort Analysis
    # Get first transaction date for each investor
    first_tx = tx_df.groupby('investor_id')['transaction_date'].min().reset_index()
    first_tx['cohort_year'] = first_tx['transaction_date'].dt.year
    tx_cohort = pd.merge(tx_df, first_tx[['investor_id', 'cohort_year']], on='investor_id')
    tx_cohort = pd.merge(tx_cohort, fund_df[['amfi_code', 'scheme_name']], on='amfi_code')
    
    cohort_results = []
    for cohort in tx_cohort['cohort_year'].unique():
        cohort_tx = tx_cohort[tx_cohort['cohort_year'] == cohort]
        investor_count = cohort_tx['investor_id'].nunique()
        
        # Average SIP
        sip_tx = cohort_tx[cohort_tx['transaction_type'] == 'SIP']
        avg_sip = sip_tx['amount_inr'].mean() if not sip_tx.empty else 0
        
        # Total invested
        invested_tx = cohort_tx[cohort_tx['transaction_type'].isin(['SIP', 'Lumpsum'])]
        total_invested = invested_tx['amount_inr'].sum()
        
        # Top fund
        fund_sums = invested_tx.groupby('scheme_name')['amount_inr'].sum()
        top_fund = fund_sums.idxmax() if not fund_sums.empty else "None"
        top_fund_amt = fund_sums.max() if not fund_sums.empty else 0
        
        cohort_results.append({
            'cohort_year': int(cohort),
            'investors_count': investor_count,
            'avg_sip_amount': avg_sip,
            'total_invested': total_invested,
            'top_fund_preference_by_amount': top_fund,
            'top_fund_amount': top_fund_amt
        })
        
    cohort_df = pd.DataFrame(cohort_results)
    cohort_df.to_csv(PROCESSED_DIR / "cohort_analysis.csv", index=False)
    cohort_df.to_csv(BASE_DIR / "cohort_analysis.csv", index=False)
    print("Cohort analysis completed and saved.")
    
    # 6. SIP Continuity Analysis
    # Filter SIP transactions and find gaps
    sip_tx = tx_df[tx_df['transaction_type'] == 'SIP'].sort_values(['investor_id', 'transaction_date'])
    sip_counts = sip_tx.groupby('investor_id').size()
    investors_6plus = sip_counts[sip_counts >= 6].index
    
    continuity_results = []
    for inv_id in investors_6plus:
        dates = sip_tx[sip_tx['investor_id'] == inv_id]['transaction_date'].sort_values().tolist()
        gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        avg_gap = np.mean(gaps) if gaps else 0
        max_gap = np.max(gaps) if gaps else 0
        
        # Flag as at-risk if max gap > 35 days (i.e. missed a monthly cycle)
        is_at_risk = 1 if max_gap > 35 else 0
        
        continuity_results.append({
            'investor_id': inv_id,
            'total_sip_transactions': len(dates),
            'avg_gap_days': avg_gap,
            'max_gap_days': max_gap,
            'is_at_risk': is_at_risk
        })
        
    continuity_df = pd.DataFrame(continuity_results)
    continuity_df.to_csv(PROCESSED_DIR / "sip_continuity.csv", index=False)
    continuity_df.to_csv(BASE_DIR / "sip_continuity.csv", index=False)
    print("SIP continuity analysis completed and saved.")
    
    conn.close()
    print("=" * 60)
    print("ALL CALCULATIONS COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == '__main__':
    run_calculations()
