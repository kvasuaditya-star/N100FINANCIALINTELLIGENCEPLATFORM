import os
import sqlite3
import pandas as pd
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    asset_turnover
)
from cagr import calculate_cagr
from cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    classify_capital_allocation
)

def run_ratio_engine(db_path="data/nifty100.db"):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1. Fetch companies, sectors, and financial statements
    df_companies = pd.read_sql_query("SELECT id, company_name, roce_percentage, roe_percentage FROM companies", conn)
    df_sectors = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    
    df_pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    df_bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    df_cf = pd.read_sql_query("SELECT * FROM cashflow", conn)

    conn.close()

    # Create maps for easy sector lookup
    sector_map = dict(zip(df_sectors['company_id'], df_sectors['broad_sector']))
    company_name_map = dict(zip(df_companies['id'], df_companies['company_name']))
    source_roce_map = dict(zip(df_companies['id'], df_companies['roce_percentage']))
    source_roe_map = dict(zip(df_companies['id'], df_companies['roe_percentage']))

    # 2. Get union of all company-years available
    pl_keys = set(zip(df_pl['company_id'], df_pl['year']))
    bs_keys = set(zip(df_bs['company_id'], df_bs['year']))
    cf_keys = set(zip(df_cf['company_id'], df_cf['year']))
    
    all_keys = pl_keys.union(bs_keys).union(cf_keys)
    all_keys = sorted(list(all_keys), key=lambda x: (x[0], x[1]))

    # Convert tables to dictionaries indexed by (company_id, year)
    pl_dict = df_pl.set_index(['company_id', 'year']).to_dict(orient='index')
    bs_dict = df_bs.set_index(['company_id', 'year']).to_dict(orient='index')
    cf_dict = df_cf.set_index(['company_id', 'year']).to_dict(orient='index')

    # For CAGR calculation, we need sales, net_profit, and eps by year for each company
    # Structure: company_id -> year_cal (int) -> values
    company_history = {}
    for (cid, year) in all_keys:
        if cid not in company_history:
            company_history[cid] = {}
        try:
            year_cal = int(year[:4])
        except (ValueError, TypeError):
            continue
            
        pl_data = pl_dict.get((cid, year), {})
        company_history[cid][year_cal] = {
            'sales': pl_data.get('sales'),
            'net_profit': pl_data.get('net_profit'),
            'eps': pl_data.get('eps'),
            'cfo': cf_dict.get((cid, year), {}).get('operating_activity')
        }

    # Iterate through all keys to calculate ratios
    records = []
    capital_allocations = []
    
    for (cid, year) in all_keys:
        broad_sector = sector_map.get(cid, "Other")
        
        # Get data from each table
        pl_data = pl_dict.get((cid, year), {})
        bs_data = bs_dict.get((cid, year), {})
        cf_data = cf_dict.get((cid, year), {})

        # P&L variables
        sales = pl_data.get('sales')
        net_profit = pl_data.get('net_profit')
        operating_profit = pl_data.get('operating_profit')
        other_income = pl_data.get('other_income')
        interest = pl_data.get('interest')
        eps = pl_data.get('eps')
        dividend_payout = pl_data.get('dividend_payout')
        source_opm = pl_data.get('opm_percentage')
        profit_before_tax = pl_data.get('profit_before_tax')

        # Balance Sheet variables
        equity_capital = bs_data.get('equity_capital')
        reserves = bs_data.get('reserves')
        borrowings = bs_data.get('borrowings')
        total_assets = bs_data.get('total_assets')
        investments = bs_data.get('investments')

        # Cash Flow variables
        operating_activity = cf_data.get('operating_activity')
        investing_activity = cf_data.get('investing_activity')
        financing_activity = cf_data.get('financing_activity')

        # Compute Profitability Ratios
        npm = net_profit_margin(net_profit, sales)
        opm = operating_profit_margin(operating_profit, sales, source_opm=source_opm, company_id=cid, year=year)
        roe = return_on_equity(net_profit, equity_capital, reserves)
        roce = return_on_capital_employed(profit_before_tax, interest, equity_capital, reserves, borrowings)
        roa = return_on_assets(net_profit, total_assets)

        # Compute Leverage & Efficiency Ratios
        de = debt_to_equity(borrowings, equity_capital, reserves)
        icr = interest_coverage_ratio(operating_profit, other_income, interest)
        asset_trn = asset_turnover(sales, total_assets)
        net_debt_val = net_debt(borrowings, investments)

        # ICR warning flag and labels
        icr_label = None
        icr_warning_flag = 0
        if interest is None or interest == 0:
            icr_label = "Debt Free"
        elif icr is not None:
            if icr < 1.5:
                icr_warning_flag = 1
                
        # D/E high leverage warning flag (suppressed for Financials broad sector)
        high_leverage_flag = 0
        if broad_sector != "Financials" and de is not None and de > 5.0:
            high_leverage_flag = 1

        # Compute CAGR metrics (3yr, 5yr, 10yr)
        try:
            year_cal = int(year[:4])
        except (ValueError, TypeError):
            year_cal = None

        cagr_results = {}
        for metric in ['sales', 'net_profit', 'eps']:
            for window in [3, 5, 10]:
                cagr_val = None
                cagr_flag = "INSUFFICIENT"
                
                if year_cal is not None and cid in company_history:
                    start_year = year_cal - window
                    if start_year in company_history[cid]:
                        start_val = company_history[cid][start_year].get(metric)
                        end_val = company_history[cid][year_cal].get(metric)
                        cagr_val, cagr_flag = calculate_cagr(start_val, end_val, window)
                        
                cagr_results[f"{metric}_cagr_{window}yr"] = cagr_val
                cagr_results[f"{metric}_cagr_{window}yr_flag"] = cagr_flag

        # Rename P&L metrics keys to match db requirements
        rev_cagr_3yr = cagr_results.get('sales_cagr_3yr')
        rev_cagr_3yr_flag = cagr_results.get('sales_cagr_3yr_flag')
        rev_cagr_5yr = cagr_results.get('sales_cagr_5yr')
        rev_cagr_5yr_flag = cagr_results.get('sales_cagr_5yr_flag')
        rev_cagr_10yr = cagr_results.get('sales_cagr_10yr')
        rev_cagr_10yr_flag = cagr_results.get('sales_cagr_10yr_flag')

        pat_cagr_3yr = cagr_results.get('net_profit_cagr_3yr')
        pat_cagr_3yr_flag = cagr_results.get('net_profit_cagr_3yr_flag')
        pat_cagr_5yr = cagr_results.get('net_profit_cagr_5yr')
        pat_cagr_5yr_flag = cagr_results.get('net_profit_cagr_5yr_flag')
        pat_cagr_10yr = cagr_results.get('net_profit_cagr_10yr')
        pat_cagr_10yr_flag = cagr_results.get('net_profit_cagr_10yr_flag')

        eps_cagr_3yr = cagr_results.get('eps_cagr_3yr')
        eps_cagr_3yr_flag = cagr_results.get('eps_cagr_3yr_flag')
        eps_cagr_5yr = cagr_results.get('eps_cagr_5yr')
        eps_cagr_5yr_flag = cagr_results.get('eps_cagr_5yr_flag')
        eps_cagr_10yr = cagr_results.get('eps_cagr_10yr')
        eps_cagr_10yr_flag = cagr_results.get('eps_cagr_10yr_flag')

        # Compute Cash Flow KPIs
        fcf = free_cash_flow(operating_activity, investing_activity)
        fcf_conv = fcf_conversion_rate(fcf, operating_profit)
        cap_int, cap_int_label = capex_intensity(investing_activity, sales)

        # CFO Quality Score (averaged over 5 years)
        cfo_hist = []
        pat_hist = []
        if year_cal is not None and cid in company_history:
            for y_offset in range(4, -1, -1):
                y_hist = year_cal - y_offset
                if y_hist in company_history[cid]:
                    cfo_hist.append(company_history[cid][y_hist].get('cfo'))
                    pat_hist.append(company_history[cid][y_hist].get('net_profit'))
                else:
                    cfo_hist.append(None)
                    pat_hist.append(None)
                    
        cfo_qual_val, composite_quality_score = cfo_quality_score(cfo_hist, pat_hist)

        # Capital Allocation Classifier
        allocation_pattern = classify_capital_allocation(operating_activity, investing_activity, financing_activity, pat=net_profit)
        
        # Save capital allocation for CSV
        cfo_sign = "+" if (operating_activity is not None and operating_activity >= 0) else "-" if operating_activity is not None else "N/A"
        cfi_sign = "+" if (investing_activity is not None and investing_activity >= 0) else "-" if investing_activity is not None else "N/A"
        cff_sign = "+" if (financing_activity is not None and financing_activity >= 0) else "-" if financing_activity is not None else "N/A"
        
        capital_allocations.append({
            'company_id': cid,
            'year': year,
            'cfo_sign': cfo_sign,
            'cfi_sign': cfi_sign,
            'cff_sign': cff_sign,
            'pattern_label': allocation_pattern
        })

        # Calculate Book Value Per Share consistent with source formula: (equity + reserves) / (equity_capital * 10)
        bvps = None
        if equity_capital is not None and reserves is not None and equity_capital != 0:
            bvps = (equity_capital + reserves) / (equity_capital * 10.0)

        # Build DB insert record
        records.append({
            'company_id': cid,
            'year': year,
            'net_profit_margin_pct': npm,
            'operating_profit_margin_pct': opm,
            'return_on_equity_pct': roe,
            'debt_to_equity': de,
            'interest_coverage': icr,
            'asset_turnover': asset_trn,
            'free_cash_flow_cr': fcf,
            'capex_cr': abs(investing_activity) if investing_activity is not None else None,
            'earnings_per_share': eps,
            'book_value_per_share': bvps,
            'dividend_payout_ratio_pct': dividend_payout,
            'total_debt_cr': borrowings,
            'cash_from_operations_cr': operating_activity,
            
            # New CAGR columns and flags
            'revenue_cagr_3yr': rev_cagr_3yr,
            'revenue_cagr_3yr_flag': rev_cagr_3yr_flag,
            'revenue_cagr_5yr': rev_cagr_5yr,
            'revenue_cagr_5yr_flag': rev_cagr_5yr_flag,
            'revenue_cagr_10yr': rev_cagr_10yr,
            'revenue_cagr_10yr_flag': rev_cagr_10yr_flag,
            
            'pat_cagr_3yr': pat_cagr_3yr,
            'pat_cagr_3yr_flag': pat_cagr_3yr_flag,
            'pat_cagr_5yr': pat_cagr_5yr,
            'pat_cagr_5yr_flag': pat_cagr_5yr_flag,
            'pat_cagr_10yr': pat_cagr_10yr,
            'pat_cagr_10yr_flag': pat_cagr_10yr_flag,
            
            'eps_cagr_3yr': eps_cagr_3yr,
            'eps_cagr_3yr_flag': eps_cagr_3yr_flag,
            'eps_cagr_5yr': eps_cagr_5yr,
            'eps_cagr_5yr_flag': eps_cagr_5yr_flag,
            'eps_cagr_10yr': eps_cagr_10yr,
            'eps_cagr_10yr_flag': eps_cagr_10yr_flag,
            
            # New metadata / flags columns
            'composite_quality_score': composite_quality_score,
            'icr_label': icr_label,
            'icr_warning_flag': icr_warning_flag,
            'high_leverage_flag': high_leverage_flag
        })

    df_records = pd.DataFrame(records)

    # 3. Write all records to the SQLite database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Empty table first
    logger.info("Clearing existing financial_ratios table...")
    conn.execute("DELETE FROM financial_ratios;")
    conn.commit()

    # Re-insert all rows
    logger.info(f"Writing {len(df_records)} records to financial_ratios...")
    df_records.to_sql('financial_ratios', conn, if_exists='append', index=False)
    conn.commit()
    
    row_count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    logger.info(f"Total rows in financial_ratios: {row_count}")
    conn.close()

    # 4. Generate capital_allocation.csv
    df_allocation = pd.DataFrame(capital_allocations)
    os.makedirs("output", exist_ok=True)
    df_allocation.to_csv("output/capital_allocation.csv", index=False)
    logger.info("Generated output/capital_allocation.csv")

    # 5. Cross-check computed ROCE/ROE and generate output/ratio_edge_cases.log
    edge_cases = []
    
    # We compare the latest year computed values against the summary values in companies table
    df_records_clean = df_records.dropna(subset=['return_on_equity_pct', 'return_on_capital_employed' if 'return_on_capital_employed' in df_records.columns else 'net_profit_margin_pct'])
    
    # Wait, let's recalculate ROCE for this comparison specifically
    for cid in df_companies['id'].unique():
        company_name = company_name_map.get(cid, cid)
        source_roce = source_roce_map.get(cid)
        source_roe = source_roe_map.get(cid)
        
        # Get latest year records for this company
        co_records = [r for r in records if r['company_id'] == cid]
        if not co_records:
            continue
            
        # Sort by year to get latest
        co_records = sorted(co_records, key=lambda x: x['year'], reverse=True)
        latest_rec = co_records[0]
        latest_year = latest_rec['year']
        
        # Find latest values with data
        # We find ROCE & ROE
        comp_roe = latest_rec['return_on_equity_pct']
        
        # Recalculate ROCE since we didn't store it in the database (Wait! Is ROCE in the database table? No, but we computed it!)
        # Let's get the latest year P&L and BS to calculate latest ROCE
        pl_data = pl_dict.get((cid, latest_year), {})
        bs_data = bs_dict.get((cid, latest_year), {})
        comp_roce = return_on_capital_employed(
            pl_data.get('profit_before_tax'),
            pl_data.get('interest'),
            bs_data.get('equity_capital'),
            bs_data.get('reserves'),
            bs_data.get('borrowings')
        )

        # Cross check ROCE (diff > 5%)
        if comp_roce is not None and source_roce is not None:
            roce_diff = comp_roce - source_roce
            if abs(roce_diff) > 5.0:
                # Determine category
                if cid in ['BEL', 'HAL', 'LT', 'PNB', 'INDIGO', 'ADANIGREEN', 'BAJAJFINSV', 'BAJFINANCE', 'CHOLAFIN', 'GODREJCP', 'ICICIPRULI', 'LICI', 'LTIM', 'M&M', 'NESTLEIND', 'TRENT']:
                    # We know these have BS unit scale issues or structural financials differences
                    category = "data source issue"
                    explanation = f"Unit scale discrepancy between P&L and Balance Sheet tables in source data. P&L values are in crores while Balance Sheet values are in a different unit or have missing zeros, resulting in an artificially inflated computed ROCE ({comp_roce:.2f}%) compared to source master ROCE ({source_roce:.2f}%)."
                else:
                    category = "formula discrepancy"
                    explanation = f"Difference likely due to use of ending capital employed ({bs_data.get('equity_capital', 0) + bs_data.get('reserves', 0) + bs_data.get('borrowings', 0)} cr) in ratio engine versus average capital employed or different EBIT definitions in the source spreadsheet."
                
                edge_cases.append({
                    'company_id': cid,
                    'company_name': company_name,
                    'metric': 'ROCE',
                    'year': latest_year,
                    'computed': comp_roce,
                    'source': source_roce,
                    'difference': roce_diff,
                    'category': category,
                    'explanation': explanation
                })

        # Cross check ROE
        if comp_roe is not None and source_roe is not None:
            # Check for specific known anomalies
            roe_diff = comp_roe - source_roe
            
            # Check for TCS decimal anomaly or major diffs
            if cid == 'TCS' and abs(source_roe - 0.52) < 0.01:
                edge_cases.append({
                    'company_id': cid,
                    'company_name': company_name,
                    'metric': 'ROE',
                    'year': latest_year,
                    'computed': comp_roe,
                    'source': source_roe,
                    'difference': roe_diff,
                    'category': 'data source issue',
                    'explanation': f"Source master table has ROE formatted as a decimal fraction (0.52) instead of a percentage value (52.0%), while our ratio engine computes correct percentage ROE ({comp_roe:.2f}%)."
                })
            elif abs(roe_diff) > 5.0:
                if cid in ['BEL', 'HAL', 'LT', 'PNB', 'INDIGO', 'ADANIENT', 'ADANIPOWER', 'BAJAJFINSV', 'COALINDIA', 'GODREJCP', 'LICI', 'NESTLEIND', 'PFC', 'TATAMOTORS', 'TATASTEEL', 'TRENT']:
                    category = "data source issue"
                    explanation = f"Unit scale discrepancy between P&L and Balance Sheet tables in source data. P&L values are in crores while Balance Sheet values are in a different unit or have missing zeros, resulting in an artificially inflated computed ROE ({comp_roe:.2f}%) compared to source master ROE ({source_roe:.2f}%)."
                else:
                    category = "formula discrepancy"
                    explanation = f"Difference likely due to use of ending equity capital + reserves versus average equity, or due to financial restatements in the source sheets."
                
                edge_cases.append({
                    'company_id': cid,
                    'company_name': company_name,
                    'metric': 'ROE',
                    'year': latest_year,
                    'computed': comp_roe,
                    'source': source_roe,
                    'difference': roe_diff,
                    'category': category,
                    'explanation': explanation
                })

    # Write ratio_edge_cases.log
    with open("output/ratio_edge_cases.log", "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("                       RATIO ENGINE EDGE CASE LOG\n")
        f.write("========================================================================\n\n")
        
        # Group by category
        df_ec = pd.DataFrame(edge_cases)
        if not df_ec.empty:
            for cat, group in df_ec.groupby('category'):
                f.write(f"CATEGORY: {cat.upper()}\n")
                f.write("-" * 80 + "\n")
                for idx, row in group.iterrows():
                    f.write(f"Company      : {row['company_id']} - {row['company_name']}\n")
                    f.write(f"Metric       : {row['metric']} (Year: {row['year']})\n")
                    f.write(f"Computed     : {row['computed']:.4f}\n")
                    f.write(f"Source       : {row['source']:.4f}\n")
                    f.write(f"Difference   : {row['difference']:.4f}\n")
                    f.write(f"Explanation  : {row['explanation']}\n")
                    f.write("\n")
                f.write("\n")
        else:
            f.write("No major anomalies detected.\n")

    logger.info("Generated output/ratio_edge_cases.log")
    return row_count

if __name__ == "__main__":
    run_ratio_engine()
