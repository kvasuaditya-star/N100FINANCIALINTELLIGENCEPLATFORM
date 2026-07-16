import pandas as pd
import numpy as np
import re
import requests
from concurrent.futures import ThreadPoolExecutor

class DataValidator:
    def __init__(self):
        self.failures = []  # list of dict: {company_id, year, field, rule_id, issue, severity}
        self.info_counters = {}

    def log_failure(self, company_id, year, field, rule_id, issue, severity):
        self.failures.append({
            'company_id': company_id if company_id is not None else 'UNKNOWN',
            'year': year if year is not None else 'UNKNOWN',
            'field': field if field is not None else 'UNKNOWN',
            'rule_id': rule_id,
            'issue': issue,
            'severity': severity
        })

    def validate_dq_01_companies_pk(self, df_companies):
        """DQ-01: Company PK Uniqueness"""
        dupes = df_companies[df_companies['id'].duplicated(keep=False)]
        if not dupes.empty:
            for idx, row in dupes.iterrows():
                self.log_failure(
                    company_id=row['id'],
                    year='N/A',
                    field='id',
                    rule_id='DQ-01',
                    issue=f"Duplicate company ID found: {row['id']}",
                    severity='CRITICAL'
                )
            return False
        return True

    def validate_dq_02_annual_pk(self, table_name, df):
        """DQ-02: Annual PK Uniqueness"""
        if df.empty or 'company_id' not in df.columns or 'year' not in df.columns:
            return df
        
        dupe_mask = df.duplicated(subset=['company_id', 'year'], keep=False)
        dupes = df[dupe_mask]
        
        if not dupes.empty:
            for idx, row in dupes.iterrows():
                self.log_failure(
                    company_id=row['company_id'],
                    year=row['year'],
                    field='company_id,year',
                    rule_id='DQ-02',
                    issue=f"Duplicate PK (company_id, year) in table {table_name}",
                    severity='CRITICAL'
                )
            # Action: Keep last occurrence
            df = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
        return df

    def validate_dq_03_fk_integrity(self, table_name, df, valid_company_ids):
        """DQ-03: FK Integrity"""
        if df.empty or 'company_id' not in df.columns:
            return df
            
        orphan_mask = ~df['company_id'].isin(valid_company_ids)
        orphans = df[orphan_mask]
        
        if not orphans.empty:
            for idx, row in orphans.iterrows():
                year_val = row.get('year', 'N/A')
                self.log_failure(
                    company_id=row['company_id'],
                    year=year_val,
                    field='company_id',
                    rule_id='DQ-03',
                    issue=f"Orphan company_id '{row['company_id']}' in table {table_name} - not present in companies",
                    severity='CRITICAL'
                )
            # Action: Reject orphan rows
            df = df[~orphan_mask]
        return df

    def validate_dq_04_bs_balance(self, df_bs):
        """DQ-04: Balance Sheet Balance"""
        if df_bs.empty:
            return df_bs
            
        for idx, row in df_bs.iterrows():
            assets = float(row.get('total_assets', 0))
            liab = float(row.get('total_liabilities', 0))
            
            if assets == 0:
                if liab != 0:
                    self.log_failure(
                        company_id=row['company_id'],
                        year=row['year'],
                        field='total_assets',
                        rule_id='DQ-04',
                        issue=f"Unbalanced Balance Sheet: total_assets=0, total_liabilities={liab}",
                        severity='WARNING'
                    )
            else:
                diff_pct = abs(assets - liab) / assets
                if diff_pct >= 0.01:
                    self.log_failure(
                        company_id=row['company_id'],
                        year=row['year'],
                        field='total_assets,total_liabilities',
                        rule_id='DQ-04',
                        issue=f"Unbalanced Balance Sheet: assets={assets}, liabilities={liab} (diff={diff_pct:.2%})",
                        severity='WARNING'
                    )
        return df_bs

    def validate_dq_05_opm_crosscheck(self, df_pl):
        """DQ-05: OPM Cross-Check"""
        if df_pl.empty:
            return df_pl
            
        for idx, row in df_pl.iterrows():
            sales = float(row.get('sales', 0))
            op = float(row.get('operating_profit', 0))
            opm = float(row.get('opm_percentage', 0))
            
            if sales != 0:
                computed_opm = (op / sales) * 100
                if abs(opm - computed_opm) >= 1.0:
                    self.log_failure(
                        company_id=row['company_id'],
                        year=row['year'],
                        field='opm_percentage',
                        rule_id='DQ-05',
                        issue=f"OPM mismatch: source opm={opm}%, computed opm={computed_opm:.2f}%",
                        severity='WARNING'
                    )
        return df_pl

    def validate_dq_06_positive_sales(self, df_pl, df_sectors):
        """DQ-06: Positive Sales (non-financials/banks)"""
        if df_pl.empty:
            return df_pl
            
        # Get financial companies
        financials = set()
        if not df_sectors.empty:
            fin_df = df_sectors[
                df_sectors['broad_sector'].str.lower().str.contains('financial', na=False) |
                df_sectors['sub_sector'].str.lower().str.contains('bank', na=False)
            ]
            financials = set(fin_df['company_id'].unique())
            
        for idx, row in df_pl.iterrows():
            co_id = row['company_id']
            sales = float(row.get('sales', 0))
            
            if co_id not in financials and sales <= 0:
                self.log_failure(
                    company_id=co_id,
                    year=row['year'],
                    field='sales',
                    rule_id='DQ-06',
                    issue=f"Non-financial company '{co_id}' has non-positive sales: {sales}",
                    severity='WARNING'
                )
        return df_pl

    def validate_dq_07_year_format(self, table_name, df):
        """DQ-07: Year Format"""
        if df.empty or 'year' not in df.columns:
            return df
            
        invalid_mask = ~df['year'].str.match(r'^\d{4}-\d{2}$', na=False)
        invalids = df[invalid_mask]
        
        if not invalids.empty:
            for idx, row in invalids.iterrows():
                self.log_failure(
                    company_id=row.get('company_id', 'UNKNOWN'),
                    year=row['year'],
                    field='year',
                    rule_id='DQ-07',
                    issue=f"Invalid year format '{row['year']}' in table {table_name}",
                    severity='CRITICAL'
                )
            # Action: Reject invalid rows
            df = df[~invalid_mask]
        return df

    def validate_dq_08_ticker_format(self, table_name, df):
        """DQ-08: Ticker Format"""
        if df.empty or 'company_id' not in df.columns:
            return df
            
        invalid_mask = (df['company_id'] == 'MISSING') | \
                       (df['company_id'].isnull()) | \
                       (df['company_id'].str.len() < 2) | \
                       (df['company_id'].str.len() > 12)
                       
        invalids = df[invalid_mask]
        if not invalids.empty:
            for idx, row in invalids.iterrows():
                year_val = row.get('year', 'N/A')
                self.log_failure(
                    company_id=row['company_id'],
                    year=year_val,
                    field='company_id',
                    rule_id='DQ-08',
                    issue=f"Invalid company_id format '{row['company_id']}' in table {table_name}",
                    severity='CRITICAL'
                )
            # Action: Reject invalid rows
            df = df[~invalid_mask]
        return df

    def validate_dq_09_net_cash(self, df_cf):
        """DQ-09: Net Cash Check"""
        if df_cf.empty:
            return df_cf
            
        for idx, row in df_cf.iterrows():
            cfo = float(row.get('operating_activity', 0))
            cfi = float(row.get('investing_activity', 0))
            cff = float(row.get('financing_activity', 0))
            net_cf = float(row.get('net_cash_flow', 0))
            
            sum_cf = cfo + cfi + cff
            if abs(net_cf - sum_cf) > 10.0:
                self.log_failure(
                    company_id=row['company_id'],
                    year=row['year'],
                    field='net_cash_flow',
                    rule_id='DQ-09',
                    issue=f"Net cash flow mismatch: net_cash_flow={net_cf}, sum(CFO,CFI,CFF)={sum_cf}",
                    severity='WARNING'
                )
                # Action: Compute net_cash_flow from components
                df_cf.at[idx, 'net_cash_flow'] = sum_cf
        return df_cf

    def validate_dq_10_fixed_assets(self, df_bs):
        """DQ-10: Non-Negative Fixed Assets"""
        if df_bs.empty:
            return df_bs
            
        for idx, row in df_bs.iterrows():
            fa = float(row.get('fixed_assets', 0))
            if fa < 0:
                self.log_failure(
                    company_id=row['company_id'],
                    year=row['year'],
                    field='fixed_assets',
                    rule_id='DQ-10',
                    issue=f"Negative fixed assets: {fa}",
                    severity='WARNING'
                )
                # Action: Coerce to 0
                df_bs.at[idx, 'fixed_assets'] = 0.0
        return df_bs

    def validate_dq_11_tax_rate(self, df_pl):
        """DQ-11: Tax Rate Range"""
        if df_pl.empty:
            return df_pl
            
        for idx, row in df_pl.iterrows():
            tax = row.get('tax_percentage', None)
            if tax is not None:
                tax_val = float(tax)
                if tax_val < 0 or tax_val > 60:
                    self.log_failure(
                        company_id=row['company_id'],
                        year=row['year'],
                        field='tax_percentage',
                        rule_id='DQ-11',
                        issue=f"Tax rate out of range: {tax_val}%",
                        severity='WARNING'
                    )
        return df_pl

    def validate_dq_12_dividend_cap(self, df_pl):
        """DQ-12: Dividend Payout Cap"""
        if df_pl.empty:
            return df_pl
            
        for idx, row in df_pl.iterrows():
            div = row.get('dividend_payout', None)
            if div is not None:
                div_val = float(div)
                if div_val > 200:
                    self.log_failure(
                        company_id=row['company_id'],
                        year=row['year'],
                        field='dividend_payout',
                        rule_id='DQ-12',
                        issue=f"Dividend payout exceeds cap: {div_val}%",
                        severity='WARNING'
                    )
        return df_pl

    def validate_dq_13_urls(self, df_doc):
        """DQ-13: URL Validity (documents)"""
        if df_doc.empty:
            return df_doc
            
        urls = df_doc['Annual_Report'].dropna().tolist()
        
        # Check URLs in parallel to save time
        def check_url(url):
            try:
                # 1 second timeout to keep load fast
                r = requests.head(url, allow_redirects=True, timeout=1.0)
                if r.status_code != 200:
                    return url, f"Status code {r.status_code}"
                return url, None
            except Exception as e:
                return url, str(e)

        url_issues = {}
        with ThreadPoolExecutor(max_workers=30) as executor:
            results = executor.map(check_url, urls)
            for url, err in results:
                if err:
                    url_issues[url] = err
                    
        for idx, row in df_doc.iterrows():
            url = row['Annual_Report']
            if pd.isna(url):
                continue
            if url in url_issues:
                self.log_failure(
                    company_id=row['company_id'],
                    year=str(row['Year']),  # documents.xlsx uses capital Year
                    field='Annual_Report',
                    rule_id='DQ-13',
                    issue=f"Invalid URL: {url} - {url_issues[url]}",
                    severity='WARNING'
                )
        return df_doc

    def validate_dq_14_eps_sign(self, df_pl):
        """DQ-14: EPS Sign Consistency"""
        if df_pl.empty:
            return df_pl
            
        for idx, row in df_pl.iterrows():
            net_profit = float(row.get('net_profit', 0))
            eps = float(row.get('eps', 0))
            
            if net_profit > 0 and eps <= 0:
                self.log_failure(
                    company_id=row['company_id'],
                    year=row['year'],
                    field='eps',
                    rule_id='DQ-14',
                    issue=f"EPS sign mismatch: net_profit={net_profit} (positive) but eps={eps} (non-positive)",
                    severity='WARNING'
                )
        return df_pl

    def validate_dq_15_bse_balance(self, df_bs):
        """DQ-15: BSE/ASE Balance (ext.)"""
        if df_bs.empty:
            return df_bs
            
        strict_equal_count = 0
        for idx, row in df_bs.iterrows():
            assets = float(row.get('total_assets', 0))
            liab = float(row.get('total_liabilities', 0))
            if assets == liab:
                strict_equal_count += 1
                
        self.info_counters['DQ-15_strict_balanced_rows'] = strict_equal_count
        return df_bs

    def validate_dq_16_coverage(self, df_pl, df_bs, df_cf):
        """DQ-16: Coverage Check"""
        # Count records per company
        co_counts = {}
        
        # P&L
        if not df_pl.empty:
            for co, count in df_pl['company_id'].value_counts().items():
                co_counts[co] = co_counts.get(co, 0) + count
        # BS
        if not df_bs.empty:
            for co, count in df_bs['company_id'].value_counts().items():
                co_counts[co] = co_counts.get(co, 0) + count
        # CF
        if not df_cf.empty:
            for co, count in df_cf['company_id'].value_counts().items():
                co_counts[co] = co_counts.get(co, 0) + count
                
        # Each company needs at least 5 years of P&L, BS, CF.
        # Average records per company across all three should be at least 15 (5 years * 3 tables)
        for co, total_records in co_counts.items():
            # Check individual table counts if we want to be strict
            pl_cnt = len(df_pl[df_pl['company_id'] == co]) if not df_pl.empty else 0
            bs_cnt = len(df_bs[df_bs['company_id'] == co]) if not df_bs.empty else 0
            cf_cnt = len(df_cf[df_cf['company_id'] == co]) if not df_cf.empty else 0
            
            min_years = min(pl_cnt, bs_cnt, cf_cnt)
            if min_years < 5:
                self.log_failure(
                    company_id=co,
                    year='ALL',
                    field='coverage',
                    rule_id='DQ-16',
                    issue=f"Company has insufficient year coverage: P&L={pl_cnt}yrs, BS={bs_cnt}yrs, CF={cf_cnt}yrs (min required: 5)",
                    severity='WARNING'
                )
        return

    def save_failures(self, filepath):
        """Saves collected failures to output/validation_failures.csv"""
        if not self.failures:
            # Write empty file with headers
            df = pd.DataFrame(columns=['company_id', 'year', 'field', 'rule_id', 'issue', 'severity'])
        else:
            df = pd.DataFrame(self.failures)
            
        df.to_csv(filepath, index=False)
        print(f"Saved {len(self.failures)} DQ validation failures to {filepath}")
