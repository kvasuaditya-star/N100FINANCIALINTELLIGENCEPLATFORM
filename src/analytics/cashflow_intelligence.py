"""
Day 31 — Cash Flow Intelligence Module
Computes CFO quality, CapEx intensity, distress signals, deleveraging flags,
and capital allocation patterns for all 92 companies.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
CAP_ALLOC_CSV = os.path.join(OUTPUT_DIR, "capital_allocation.csv")
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")
DISTRESS_CSV = os.path.join(OUTPUT_DIR, "distress_alerts.csv")

# Add project root so we can import from src
sys.path.insert(0, PROJECT_ROOT)


def safe_float(val):
    """Safely convert to float."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (ValueError, TypeError):
        return None


def compute_cagr(start_val, end_val, n):
    """Compute CAGR. Returns None if inputs are invalid."""
    if n <= 0 or start_val is None or end_val is None:
        return None
    if start_val <= 0 or end_val <= 0:
        return None
    try:
        return ((end_val / start_val) ** (1.0 / n) - 1.0) * 100
    except (ZeroDivisionError, ValueError):
        return None


def run_cashflow_intelligence():
    """Main entry point."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # ── Load data ──────────────────────────────────────────────────────────
    companies = pd.read_sql_query("SELECT id FROM companies ORDER BY id", conn)
    company_ids = companies["id"].tolist()

    sectors = pd.read_sql_query(
        "SELECT company_id, broad_sector FROM sectors", conn
    )
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    cashflow = pd.read_sql_query(
        "SELECT company_id, year, operating_activity, investing_activity, "
        "financing_activity, net_cash_flow FROM cashflow "
        "ORDER BY company_id, year", conn
    )

    pnl = pd.read_sql_query(
        "SELECT company_id, year, sales, operating_profit, net_profit "
        "FROM profitandloss ORDER BY company_id, year", conn
    )

    bs = pd.read_sql_query(
        "SELECT company_id, year, borrowings FROM balancesheet "
        "ORDER BY company_id, year", conn
    )

    conn.close()

    # ── Load capital allocation CSV ────────────────────────────────────────
    cap_alloc = pd.DataFrame()
    if os.path.exists(CAP_ALLOC_CSV):
        cap_alloc = pd.read_csv(CAP_ALLOC_CSV)

    print(f"Loaded data for {len(company_ids)} companies")
    print(f"Cashflow rows: {len(cashflow)}")
    print(f"P&L rows: {len(pnl)}")
    print(f"Balance sheet rows: {len(bs)}")

    # ── Compute metrics per company ────────────────────────────────────────
    results = []

    for cid in company_ids:
        cf = cashflow[cashflow["company_id"] == cid].sort_values("year")
        pl = pnl[pnl["company_id"] == cid].sort_values("year")
        bsheet = bs[bs["company_id"] == cid].sort_values("year")

        sector = sector_map.get(cid, "Unknown")

        # ── 1. CFO Quality Score ───────────────────────────────────────────
        cfo_score = None
        cfo_label = None

        # Match cashflow and P&L by year for last 5 years
        if len(cf) >= 5 and len(pl) >= 5:
            # Get last 5 years of both
            cf_last5 = cf.tail(5)
            # Match P&L years to cashflow years
            cfo_list = []
            pat_list = []
            for _, cfrow in cf_last5.iterrows():
                yr = cfrow["year"]
                pl_match = pl[pl["year"] == yr]
                cfo_val = safe_float(cfrow["operating_activity"])
                if not pl_match.empty and cfo_val is not None:
                    pat_val = safe_float(pl_match.iloc[0]["net_profit"])
                    if pat_val is not None and pat_val != 0:
                        cfo_list.append(cfo_val)
                        pat_list.append(pat_val)

            if len(cfo_list) >= 3:  # Need at least 3 matched years
                ratios = [c / p for c, p in zip(cfo_list, pat_list)]
                cfo_score = sum(ratios) / len(ratios)
                if cfo_score > 1.0:
                    cfo_label = "High Quality"
                elif cfo_score >= 0.5:
                    cfo_label = "Moderate"
                else:
                    cfo_label = "Accrual Risk"

        # ── 2. CapEx Intensity ─────────────────────────────────────────────
        capex_pct = None
        capex_label = None

        if not cf.empty and not pl.empty:
            latest_cf = cf.iloc[-1]
            latest_yr = latest_cf["year"]
            pl_match = pl[pl["year"] == latest_yr]

            inv_act = safe_float(latest_cf["investing_activity"])
            sales_val = None
            if not pl_match.empty:
                sales_val = safe_float(pl_match.iloc[0]["sales"])

            if inv_act is not None and sales_val is not None and sales_val > 0:
                capex_pct = abs(inv_act) / sales_val * 100
                if capex_pct < 3:
                    capex_label = "Asset Light"
                elif capex_pct <= 8:
                    capex_label = "Moderate"
                else:
                    capex_label = "Capital Intensive"

        # ── 3. FCF CAGR 5yr ───────────────────────────────────────────────
        fcf_cagr = None
        if len(cf) >= 6:  # Need 6 rows to compute 5-year CAGR
            cf_sorted = cf.sort_values("year")
            fcf_vals = []
            for _, row in cf_sorted.iterrows():
                oa = safe_float(row["operating_activity"])
                ia = safe_float(row["investing_activity"])
                if oa is not None and ia is not None:
                    fcf_vals.append(oa + ia)
                else:
                    fcf_vals.append(None)

            if len(fcf_vals) >= 6:
                start_fcf = fcf_vals[-6]  # 5 years ago
                end_fcf = fcf_vals[-1]    # latest
                fcf_cagr = compute_cagr(start_fcf, end_fcf, 5)

        # ── 4. FCF Conversion % ───────────────────────────────────────────
        fcf_conversion = None
        if not cf.empty and not pl.empty:
            latest_cf_row = cf.iloc[-1]
            latest_yr = latest_cf_row["year"]
            oa = safe_float(latest_cf_row["operating_activity"])
            ia = safe_float(latest_cf_row["investing_activity"])
            pl_match = pl[pl["year"] == latest_yr]

            if oa is not None and ia is not None and not pl_match.empty:
                op = safe_float(pl_match.iloc[0]["operating_profit"])
                if op is not None and op != 0:
                    fcf = oa + ia
                    fcf_conversion = fcf / op * 100

        # ── 5. Distress Signal ─────────────────────────────────────────────
        distress_flag = False
        cfo_value = None
        cff_value = None

        if not cf.empty:
            latest = cf.iloc[-1]
            cfo_value = safe_float(latest["operating_activity"])
            cff_value = safe_float(latest["financing_activity"])
            if cfo_value is not None and cff_value is not None:
                if cfo_value < 0 and cff_value > 0:
                    distress_flag = True

        # ── 6. Deleveraging Flag ───────────────────────────────────────────
        deleveraging_flag = False
        if not cf.empty and len(bsheet) >= 2:
            latest = cf.iloc[-1]
            cff = safe_float(latest["financing_activity"])
            bw_latest = safe_float(bsheet.iloc[-1]["borrowings"])
            bw_prev = safe_float(bsheet.iloc[-2]["borrowings"])
            if (cff is not None and cff < 0 and
                    bw_latest is not None and bw_prev is not None and
                    bw_latest < bw_prev):
                deleveraging_flag = True

        # ── 7. Capital Allocation Label ────────────────────────────────────
        ca_label = "N/A"
        if not cap_alloc.empty:
            ca_co = cap_alloc[cap_alloc["company_id"] == cid]
            if not ca_co.empty:
                ca_latest = ca_co.sort_values("year").iloc[-1]
                ca_label = ca_latest.get("pattern_label", "N/A")

        # ── Get latest net profit for distress alerts ──────────────────────
        latest_np = None
        if not pl.empty:
            latest_np = safe_float(pl.iloc[-1]["net_profit"])

        results.append({
            "company_id": cid,
            "sector": sector,
            "cfo_quality_score": round(cfo_score, 3) if cfo_score is not None else None,
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": round(capex_pct, 2) if capex_pct is not None else None,
            "capex_label": capex_label,
            "fcf_cagr_5yr": round(fcf_cagr, 2) if fcf_cagr is not None else None,
            "fcf_conversion_pct": round(fcf_conversion, 2) if fcf_conversion is not None else None,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": ca_label,
            # Extra fields for distress alerts
            "_cfo_value": cfo_value,
            "_cff_value": cff_value,
            "_latest_np": latest_np,
        })

    # ── Build output DataFrame ─────────────────────────────────────────────
    df = pd.DataFrame(results)

    # ── Save cashflow_intelligence.xlsx ─────────────────────────────────────
    out_cols = [
        "company_id", "sector", "cfo_quality_score", "cfo_quality_label",
        "capex_intensity_pct", "capex_label", "fcf_cagr_5yr",
        "fcf_conversion_pct", "distress_flag", "deleveraging_flag",
        "capital_allocation_label",
    ]
    df[out_cols].to_excel(OUTPUT_XLSX, index=False, engine="openpyxl")
    print(f"\n[OK] Saved {len(df)} rows to {OUTPUT_XLSX}")

    # ── Save distress_alerts.csv ───────────────────────────────────────────
    distressed = df[df["distress_flag"] == True].copy()
    distress_out = pd.DataFrame({
        "company_id": distressed["company_id"],
        "sector": distressed["sector"],
        "cfo_value": distressed["_cfo_value"],
        "cff_value": distressed["_cff_value"],
        "latest_net_profit": distressed["_latest_np"],
        "distress_flag": True,
        "notes": "CFO < 0 AND CFF > 0 - raising cash from financing while operations burn cash",
    })
    distress_out.to_csv(DISTRESS_CSV, index=False)
    print(f"[OK] Saved {len(distress_out)} distress alerts to {DISTRESS_CSV}")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CASH FLOW INTELLIGENCE SUMMARY")
    print("=" * 60)
    print(f"  Total companies:        {len(df)}")

    print("\n  CFO Quality Distribution:")
    for label in ["High Quality", "Moderate", "Accrual Risk", None]:
        count = len(df[df["cfo_quality_label"] == label]) if label else len(df[df["cfo_quality_label"].isna()])
        lbl = label if label else "N/A (insufficient data)"
        print(f"    {lbl}: {count}")

    print("\n  CapEx Intensity Distribution:")
    for label in ["Asset Light", "Moderate", "Capital Intensive", None]:
        count = len(df[df["capex_label"] == label]) if label else len(df[df["capex_label"].isna()])
        lbl = label if label else "N/A"
        print(f"    {lbl}: {count}")

    print(f"\n  Distress signals:       {len(distressed)}")
    print(f"  Deleveraging flags:     {len(df[df['deleveraging_flag'] == True])}")
    print("=" * 60)


if __name__ == "__main__":
    run_cashflow_intelligence()
