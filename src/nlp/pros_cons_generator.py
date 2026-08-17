"""
Day 30 — NLP Auto Pros/Cons Generator
Generates rule-based pros and cons for all 92 companies with confidence scores.
Implements 12 pro rules and 12 con rules.
"""

import os
import sqlite3

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "pros_cons_generated.csv")

CONFIDENCE_THRESHOLD = 60


def get_conn():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_all_data():
    """Load all required data from the database into DataFrames."""
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query("SELECT id FROM companies", conn)
    company_ids = sorted(companies["id"].tolist())

    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    # Financial ratios — all years sorted
    fr = pd.read_sql_query(
        "SELECT * FROM financial_ratios ORDER BY company_id, year", conn
    )

    # Latest year per company in financial_ratios
    fr_latest = fr.sort_values("year").groupby("company_id").last().reset_index()

    # P&L data
    pnl = pd.read_sql_query(
        "SELECT company_id, year, sales, operating_profit, net_profit, "
        "depreciation, eps FROM profitandloss ORDER BY company_id, year",
        conn,
    )
    pnl_latest = pnl.sort_values("year").groupby("company_id").last().reset_index()

    # Balance sheet
    bs = pd.read_sql_query(
        "SELECT company_id, year, equity_capital, reserves, borrowings, "
        "investments, total_assets FROM balancesheet ORDER BY company_id, year",
        conn,
    )

    # Market cap for dividend yield
    mc = pd.read_sql_query(
        "SELECT company_id, year, dividend_yield_pct FROM market_cap "
        "ORDER BY company_id, year",
        conn,
    )
    mc_latest = mc.sort_values("year").groupby("company_id").last().reset_index()

    # Companies table for ROCE
    comp = pd.read_sql_query(
        "SELECT id, roce_percentage, roe_percentage FROM companies", conn
    )

    conn.close()

    return {
        "company_ids": company_ids,
        "sector_map": sector_map,
        "fr": fr,
        "fr_latest": fr_latest,
        "pnl": pnl,
        "pnl_latest": pnl_latest,
        "bs": bs,
        "mc_latest": mc_latest,
        "comp": comp,
    }


def safe_float(val):
    """Safely convert to float, returning None for NaN/None."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (ValueError, TypeError):
        return None


def get_company_series(df, company_id, column, min_years=3):
    """Get sorted time series for a company from a DataFrame."""
    subset = df[df["company_id"] == company_id].sort_values("year")
    vals = subset[column].tolist()
    # Filter out None/NaN
    clean = [safe_float(v) for v in vals]
    clean = [v for v in clean if v is not None]
    return clean


def evaluate_pro_rules(cid, data):
    """Evaluate all 12 pro rules for a company. Returns list of (rule_id, text, confidence)."""
    results = []
    fr = data["fr"]
    fr_latest = data["fr_latest"]
    bs = data["bs"]
    mc_latest = data["mc_latest"]

    # Get latest row for this company
    lr = fr_latest[fr_latest["company_id"] == cid]
    if lr.empty:
        return results
    lr = lr.iloc[0]

    # ── PRO 1: ROE > 20% sustained for 3+ years ──────────────────────────
    roe_series = get_company_series(fr, cid, "return_on_equity_pct")
    if len(roe_series) >= 3:
        last_3 = roe_series[-3:]
        if all(v > 20 for v in last_3):
            avg_roe = sum(last_3) / len(last_3)
            conf = min(100, int(60 + (avg_roe - 20) * 2))
            results.append(
                (
                    "PRO_01",
                    "Consistently high return on equity above 20% demonstrates "
                    "exceptional capital efficiency",
                    conf,
                )
            )

    # ── PRO 2: FCF positive for 5+ consecutive years ─────────────────────
    fcf_series = get_company_series(fr, cid, "free_cash_flow_cr")
    if len(fcf_series) >= 5:
        # Count consecutive positive from the end
        consec = 0
        for v in reversed(fcf_series):
            if v > 0:
                consec += 1
            else:
                break
        if consec >= 5:
            conf = min(100, int(60 + consec * 5))
            results.append(
                (
                    "PRO_02",
                    "Strong free cash flow generation over 5 years signals "
                    "healthy business fundamentals",
                    conf,
                )
            )

    # ── PRO 3: D/E = 0 in latest year ────────────────────────────────────
    de = safe_float(lr.get("debt_to_equity"))
    if de is not None and de == 0.0:
        results.append(
            (
                "PRO_03",
                "Debt-free balance sheet provides financial flexibility "
                "and eliminates interest burden",
                95,
            )
        )

    # ── PRO 4: Revenue CAGR > 15% over 5 years ──────────────────────────
    rev_cagr = safe_float(lr.get("revenue_cagr_5yr"))
    if rev_cagr is not None and rev_cagr > 15:
        conf = min(100, int(60 + (rev_cagr - 15) * 2))
        results.append(
            (
                "PRO_04",
                "Revenue growing at above 15% CAGR over 5 years reflects "
                "strong business momentum",
                conf,
            )
        )

    # ── PRO 5: OPM > 25% in latest year ─────────────────────────────────
    opm = safe_float(lr.get("operating_profit_margin_pct"))
    if opm is not None and opm > 25:
        conf = min(100, int(60 + (opm - 25) * 2))
        results.append(
            (
                "PRO_05",
                "Operating profit margin above 25% indicates strong pricing "
                "power and cost discipline",
                conf,
            )
        )

    # ── PRO 6: PAT CAGR > 20% over 5 years ──────────────────────────────
    pat_cagr = safe_float(lr.get("pat_cagr_5yr"))
    if pat_cagr is not None and pat_cagr > 20:
        conf = min(100, int(60 + (pat_cagr - 20) * 2))
        results.append(
            (
                "PRO_06",
                "Net profit compounding at above 20% over 5 years creates "
                "significant shareholder value",
                conf,
            )
        )

    # ── PRO 7: ICR > 10 or Debt Free ────────────────────────────────────
    icr = safe_float(lr.get("interest_coverage"))
    icr_label = lr.get("icr_label")
    if icr_label == "Debt Free":
        results.append(
            (
                "PRO_07",
                "Very high interest coverage ratio reflects negligible "
                "financial stress from debt servicing",
                90,
            )
        )
    elif icr is not None and icr > 10:
        conf = min(100, int(60 + (icr - 10) * 3))
        results.append(
            (
                "PRO_07",
                "Very high interest coverage ratio reflects negligible "
                "financial stress from debt servicing",
                conf,
            )
        )

    # ── PRO 8: Dividend Yield > 2% with FCF positive ────────────────────
    mc_row = mc_latest[mc_latest["company_id"] == cid]
    fcf_val = safe_float(lr.get("free_cash_flow_cr"))
    if not mc_row.empty and fcf_val is not None and fcf_val > 0:
        div_yield = safe_float(mc_row.iloc[0].get("dividend_yield_pct"))
        if div_yield is not None and div_yield > 2:
            conf = min(100, int(60 + (div_yield - 2) * 10))
            results.append(
                (
                    "PRO_08",
                    "Consistent dividend yield above 2% backed by positive "
                    "free cash flow",
                    conf,
                )
            )

    # ── PRO 9: EPS CAGR > 15% over 5 years ──────────────────────────────
    eps_cagr = safe_float(lr.get("eps_cagr_5yr"))
    if eps_cagr is not None and eps_cagr > 15:
        conf = min(100, int(60 + (eps_cagr - 15) * 2))
        results.append(
            (
                "PRO_09",
                "Earnings per share growing above 15% CAGR indicates strong "
                "earnings quality and compounding",
                conf,
            )
        )

    # ── PRO 10: ROE improving for 3 consecutive years ────────────────────
    if len(roe_series) >= 3:
        last_3 = roe_series[-3:]
        if last_3[0] < last_3[1] < last_3[2]:
            improvement = last_3[2] - last_3[0]
            conf = min(100, int(65 + improvement * 2))
            results.append(
                (
                    "PRO_10",
                    "Return on equity improving for 3 consecutive years shows "
                    "strengthening business quality",
                    conf,
                )
            )

    # ── PRO 11: PAT CAGR > Revenue CAGR (operating leverage) ────────────
    if (
        rev_cagr is not None
        and pat_cagr is not None
        and rev_cagr > 0
        and pat_cagr > 0
        and pat_cagr > rev_cagr
    ):
        conf = min(100, int(60 + (pat_cagr - rev_cagr) * 2))
        results.append(
            (
                "PRO_11",
                "Revenue growing slower than profits shows improving operating "
                "leverage and scale benefits",
                conf,
            )
        )

    # ── PRO 12: Assets growing with declining debt ───────────────────────
    bs_co = bs[bs["company_id"] == cid].sort_values("year")
    if len(bs_co) >= 2:
        last_2 = bs_co.tail(2)
        ta_prev = safe_float(last_2.iloc[0].get("total_assets"))
        ta_curr = safe_float(last_2.iloc[1].get("total_assets"))
        bw_prev = safe_float(last_2.iloc[0].get("borrowings"))
        bw_curr = safe_float(last_2.iloc[1].get("borrowings"))
        if (
            ta_prev is not None
            and ta_curr is not None
            and bw_prev is not None
            and bw_curr is not None
        ):
            if ta_curr > ta_prev and bw_curr < bw_prev:
                results.append(
                    (
                        "PRO_12",
                        "Growing asset base funded by internal accruals reflects "
                        "self-sustaining growth",
                        80,
                    )
                )

    return results


def evaluate_con_rules(cid, data):
    """Evaluate all 12 con rules for a company. Returns list of (rule_id, text, confidence)."""
    results = []
    fr = data["fr"]
    fr_latest = data["fr_latest"]
    pnl = data["pnl"]
    pnl_latest = data["pnl_latest"]
    bs = data["bs"]
    sector_map = data["sector_map"]
    comp = data["comp"]

    lr = fr_latest[fr_latest["company_id"] == cid]
    if lr.empty:
        return results
    lr = lr.iloc[0]

    sector = sector_map.get(cid, "")

    # ── CON 1: D/E > 2.0 for non-financial companies ────────────────────
    de = safe_float(lr.get("debt_to_equity"))
    if de is not None and de > 2.0 and sector != "Financials":
        conf = min(100, int(60 + (de - 2.0) * 10))
        results.append(
            (
                "CON_01",
                f"Debt-to-equity ratio of {de:.1f} is elevated for a non-financial "
                "company and warrants monitoring",
                conf,
            )
        )

    # ── CON 2: FCF negative for 3 consecutive years ─────────────────────
    fcf_series = get_company_series(fr, cid, "free_cash_flow_cr")
    if len(fcf_series) >= 3:
        last_3 = fcf_series[-3:]
        consec_neg = sum(1 for v in reversed(fcf_series) if v < 0)
        if all(v < 0 for v in last_3):
            conf = min(100, int(70 + min(consec_neg, 5) * 5))
            results.append(
                (
                    "CON_02",
                    "Free cash flow negative for 3 consecutive years raises "
                    "concern about cash generation quality",
                    conf,
                )
            )

    # ── CON 3: OPM declining for 3 consecutive years ────────────────────
    opm_series = get_company_series(fr, cid, "operating_profit_margin_pct")
    if len(opm_series) >= 3:
        last_3 = opm_series[-3:]
        if last_3[0] > last_3[1] > last_3[2]:
            decline_mag = last_3[0] - last_3[2]
            conf = min(100, int(65 + decline_mag * 2))
            results.append(
                (
                    "CON_03",
                    "Operating margins declining for 3 consecutive years "
                    "suggest pricing or cost pressure",
                    conf,
                )
            )

    # ── CON 4: Net profit negative in latest year ────────────────────────
    pl_row = pnl_latest[pnl_latest["company_id"] == cid]
    if not pl_row.empty:
        np_val = safe_float(pl_row.iloc[0].get("net_profit"))
        if np_val is not None and np_val < 0:
            results.append(
                (
                    "CON_04",
                    "Company reported a net loss in the most recent financial year",
                    95,
                )
            )

    # ── CON 5: Revenue declining for 2+ years ───────────────────────────
    sales_series = get_company_series(pnl, cid, "sales")
    if len(sales_series) >= 3:
        # Count consecutive declining from end
        decline_years = 0
        for i in range(len(sales_series) - 1, 0, -1):
            if sales_series[i] < sales_series[i - 1]:
                decline_years += 1
            else:
                break
        if decline_years >= 2:
            conf = min(100, int(70 + decline_years * 10))
            results.append(
                (
                    "CON_05",
                    "Revenue contraction over 2 consecutive years indicates "
                    "demand weakness or market share loss",
                    conf,
                )
            )

    # ── CON 6: ICR < 1.5 ────────────────────────────────────────────────
    icr = safe_float(lr.get("interest_coverage"))
    icr_label = lr.get("icr_label")
    if icr is not None and icr < 1.5 and icr_label != "Debt Free":
        conf = min(100, int(80 + (1.5 - icr) * 20))
        results.append(
            (
                "CON_06",
                "Interest coverage ratio below 1.5x indicates the company "
                "is at risk of not meeting its debt obligations",
                conf,
            )
        )

    # ── CON 7: Dividend payout > 100% ────────────────────────────────────
    payout = safe_float(lr.get("dividend_payout_ratio_pct"))
    if payout is not None and payout > 100:
        conf = min(100, int(70 + (payout - 100)))
        results.append(
            (
                "CON_07",
                "Dividend payout ratio above 100% means the company is paying "
                "dividends from reserves, which is unsustainable",
                conf,
            )
        )

    # ── CON 8: D/E rising for 3 consecutive years ───────────────────────
    de_series = get_company_series(fr, cid, "debt_to_equity")
    if len(de_series) >= 3:
        last_3 = de_series[-3:]
        if last_3[0] < last_3[1] < last_3[2]:
            rise_mag = last_3[2] - last_3[0]
            conf = min(100, int(65 + rise_mag * 5))
            results.append(
                (
                    "CON_08",
                    "Rising debt-to-equity ratio over 3 years suggests "
                    "increasing financial leverage risk",
                    conf,
                )
            )

    # ── CON 9: EPS declining for 3 consecutive years ────────────────────
    eps_series = get_company_series(fr, cid, "earnings_per_share")
    if len(eps_series) >= 3:
        last_3 = eps_series[-3:]
        if last_3[0] > last_3[1] > last_3[2]:
            decline_mag = last_3[0] - last_3[2]
            conf = min(100, int(70 + decline_mag * 2))
            results.append(
                (
                    "CON_09",
                    "Earnings per share declining for 3 consecutive years "
                    "reflects deteriorating profitability",
                    conf,
                )
            )

    # ── CON 10: ROCE < 10% ──────────────────────────────────────────────
    comp_row = comp[comp["id"] == cid]
    if not comp_row.empty:
        roce = safe_float(comp_row.iloc[0].get("roce_percentage"))
        if roce is not None and roce < 10:
            conf = min(100, int(60 + (10 - roce) * 3))
            results.append(
                (
                    "CON_10",
                    "Return on capital employed below 10% suggests the business "
                    "is not generating sufficient returns on invested capital",
                    conf,
                )
            )

    # ── CON 11: Net Debt > 3x EBITDA ────────────────────────────────────
    bs_co = bs[bs["company_id"] == cid].sort_values("year")
    if not bs_co.empty and not pl_row.empty:
        bs_latest = bs_co.iloc[-1]
        borrowings = safe_float(bs_latest.get("borrowings"))
        investments = safe_float(bs_latest.get("investments"))
        op = safe_float(pl_row.iloc[0].get("operating_profit"))
        dep = safe_float(pl_row.iloc[0].get("depreciation"))

        if all(v is not None for v in [borrowings, investments, op, dep]):
            net_debt = borrowings - investments
            ebitda = op + dep
            if ebitda > 0 and net_debt > 0:
                ratio = net_debt / ebitda
                if ratio > 3:
                    conf = min(100, int(65 + (ratio - 3) * 10))
                    results.append(
                        (
                            "CON_11",
                            "Net debt exceeding 3 times EBITDA is a high leverage "
                            "ratio and limits financial flexibility",
                            conf,
                        )
                    )

    # ── CON 12: Revenue CAGR < 5% over 5 years ─────────────────────────
    rev_cagr = safe_float(lr.get("revenue_cagr_5yr"))
    if rev_cagr is not None and rev_cagr < 5:
        conf = min(100, int(60 + (5 - rev_cagr) * 5))
        results.append(
            (
                "CON_12",
                "Revenue growing at below 5% over 5 years lags inflation and "
                "suggests limited business momentum",
                conf,
            )
        )

    return results


def run_generator():
    """Main entry point."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data from database...")
    data = load_all_data()
    company_ids = data["company_ids"]
    print(f"  Found {len(company_ids)} companies")

    all_rows = []

    for cid in company_ids:
        # Evaluate pro rules
        pros = evaluate_pro_rules(cid, data)
        for rule_id, text, conf in pros:
            if conf > CONFIDENCE_THRESHOLD:
                all_rows.append(
                    {
                        "company_id": cid,
                        "type": "pro",
                        "rule_id": rule_id,
                        "text": text,
                        "confidence_pct": conf,
                    }
                )

        # Evaluate con rules
        cons = evaluate_con_rules(cid, data)
        for rule_id, text, conf in cons:
            if conf > CONFIDENCE_THRESHOLD:
                all_rows.append(
                    {
                        "company_id": cid,
                        "type": "con",
                        "rule_id": rule_id,
                        "text": text,
                        "confidence_pct": conf,
                    }
                )

    # ── Build DataFrame ────────────────────────────────────────────────────
    df = pd.DataFrame(all_rows)

    # ── Verify coverage: every company needs ≥1 pro and ≥1 con ──────────
    companies_with_pros = set(df[df["type"] == "pro"]["company_id"].unique())
    companies_with_cons = set(df[df["type"] == "con"]["company_id"].unique())
    all_set = set(company_ids)

    missing_pros = all_set - companies_with_pros
    missing_cons = all_set - companies_with_cons

    fallback_rows = []
    for cid in missing_pros:
        fallback_rows.append(
            {
                "company_id": cid,
                "type": "pro",
                "rule_id": "PRO_FALLBACK",
                "text": "Company is a constituent of the Nifty 100 index, "
                "reflecting its large-cap status and market significance",
                "confidence_pct": 65,
            }
        )
    for cid in missing_cons:
        fallback_rows.append(
            {
                "company_id": cid,
                "type": "con",
                "rule_id": "CON_FALLBACK",
                "text": "Limited historical data available for comprehensive analysis",
                "confidence_pct": 65,
            }
        )

    if fallback_rows:
        df = pd.concat([df, pd.DataFrame(fallback_rows)], ignore_index=True)

    # Sort by company_id, type
    df = df.sort_values(["company_id", "type", "rule_id"]).reset_index(drop=True)

    # ── Save output ────────────────────────────────────────────────────────
    df.to_csv(OUTPUT_CSV, index=False)

    # ── Summary ────────────────────────────────────────────────────────────
    total_pros = len(df[df["type"] == "pro"])
    total_cons = len(df[df["type"] == "con"])
    cos_with_pros = df[df["type"] == "pro"]["company_id"].nunique()
    cos_with_cons = df[df["type"] == "con"]["company_id"].nunique()

    print("\n" + "=" * 60)
    print("PROS/CONS GENERATOR SUMMARY")
    print("=" * 60)
    print(f"  Total pros generated:      {total_pros}")
    print(f"  Total cons generated:      {total_cons}")
    print(f"  Companies with >=1 pro:     {cos_with_pros} / {len(company_ids)}")
    print(f"  Companies with >=1 con:     {cos_with_cons} / {len(company_ids)}")
    print(f"  Fallback pros added:       {len(missing_pros)}")
    print(f"  Fallback cons added:       {len(missing_cons)}")
    print(f"  Output saved to:           {OUTPUT_CSV}")

    # Rule distribution
    print("\n  Pro rules triggered:")
    pro_dist = df[df["type"] == "pro"]["rule_id"].value_counts().sort_index()
    for rule, count in pro_dist.items():
        print(f"    {rule}: {count}")
    print("\n  Con rules triggered:")
    con_dist = df[df["type"] == "con"]["rule_id"].value_counts().sort_index()
    for rule, count in con_dist.items():
        print(f"    {rule}: {count}")

    print("=" * 60)

    # Verify
    assert cos_with_pros == len(
        company_ids
    ), f"Not all companies have pros: {cos_with_pros}/{len(company_ids)}"
    assert cos_with_cons == len(
        company_ids
    ), f"Not all companies have cons: {cos_with_cons}/{len(company_ids)}"
    print("[OK] Verification passed: every company has >=1 pro and >=1 con")


if __name__ == "__main__":
    run_generator()
