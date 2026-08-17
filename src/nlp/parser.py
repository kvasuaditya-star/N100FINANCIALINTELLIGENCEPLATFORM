"""
Day 29 — NLP Analysis Text Parser
Parses text fields in analysis.xlsx using regex to extract CAGR values.
Cross-validates parsed values against computed CAGR from the Ratio Engine.
"""

import os
import re
import sqlite3

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
RAW_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "analysis.xlsx")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

PARSED_CSV = os.path.join(OUTPUT_DIR, "analysis_parsed.csv")
FAILURES_CSV = os.path.join(OUTPUT_DIR, "parse_failures.csv")
DIVERGENCE_CSV = os.path.join(OUTPUT_DIR, "cagr_divergence.csv")

# ── Regex patterns ─────────────────────────────────────────────────────────
# Primary: "10 Years: 21%" or "5 Year: 15.2%"
PAT_YEARS = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)\s*%", re.IGNORECASE)
# TTM pattern: "TTM: 14%" or "TTM:14%"
PAT_TTM = re.compile(r"TTM:?\s*([\d.]+)\s*%", re.IGNORECASE)
# Last Year pattern: "Last Year: 15%"
PAT_LAST_YEAR = re.compile(r"Last\s*Year:?\s*([\d.]+)\s*%", re.IGNORECASE)

METRIC_COLUMNS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]

# ── Cross-validation mapping ──────────────────────────────────────────────
# Maps (metric_type, period_years) → financial_ratios column name
CROSS_VAL_MAP = {
    ("compounded_sales_growth", 3): "revenue_cagr_3yr",
    ("compounded_sales_growth", 5): "revenue_cagr_5yr",
    ("compounded_sales_growth", 10): "revenue_cagr_10yr",
    ("compounded_profit_growth", 3): "pat_cagr_3yr",
    ("compounded_profit_growth", 5): "pat_cagr_5yr",
    ("compounded_profit_growth", 10): "pat_cagr_10yr",
}

DIVERGENCE_THRESHOLD = 5.0  # percentage points


def parse_text_field(text):
    """
    Parse a text field containing CAGR-style values.
    Returns list of (period_years, value_pct) tuples.
    Returns (failures, parsed) where failures is a list of unmatched lines.
    """
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return [], ["Empty or NaN field"]

    text = str(text).strip()
    if not text:
        return [], ["Empty string"]

    parsed = []
    lines = text.split("\n")
    unmatched_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        matched = False

        # Try N Years pattern
        m = PAT_YEARS.search(line)
        if m:
            period = int(m.group(1))
            value = float(m.group(2))
            parsed.append((period, value))
            matched = True

        # Try TTM pattern
        if not matched:
            m = PAT_TTM.search(line)
            if m:
                value = float(m.group(1))
                parsed.append((0, value))  # TTM → period 0
                matched = True

        # Try Last Year pattern
        if not matched:
            m = PAT_LAST_YEAR.search(line)
            if m:
                value = float(m.group(1))
                parsed.append((1, value))  # Last Year → period 1
                matched = True

        if not matched:
            unmatched_lines.append(line)

    return parsed, unmatched_lines


def load_computed_cagrs():
    """Load latest-year CAGR values from financial_ratios for cross-validation."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT fr.company_id,
               fr.revenue_cagr_3yr, fr.revenue_cagr_5yr, fr.revenue_cagr_10yr,
               fr.pat_cagr_3yr, fr.pat_cagr_5yr, fr.pat_cagr_10yr
        FROM financial_ratios fr
        INNER JOIN (
            SELECT company_id, MAX(year) AS max_year
            FROM financial_ratios
            GROUP BY company_id
        ) latest ON fr.company_id = latest.company_id AND fr.year = latest.max_year
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def run_parser():
    """Main parser entry point."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. Read raw Excel ──────────────────────────────────────────────────
    print(f"Reading {RAW_FILE} ...")
    df = pd.read_excel(RAW_FILE, header=1)
    # Normalize column names — raw Excel may have 'id' instead of 'company_id'
    if "id" in df.columns and "company_id" not in df.columns:
        df = df.rename(columns={"id": "company_id"})
    elif "id" in df.columns and "company_id" in df.columns:
        # Both exist — use company_id, drop extra id
        df = df.drop(columns=["id"], errors="ignore")

    print(f"  Found {len(df)} rows, columns: {list(df.columns)}")

    # Also read from DB analysis table for companies not in Excel
    conn = sqlite3.connect(DB_PATH)
    db_analysis = pd.read_sql_query("SELECT * FROM analysis", conn)
    conn.close()
    print(f"  DB analysis table has {len(db_analysis)} rows")

    # Merge: prefer Excel data, supplement with DB rows for missing companies
    excel_ids = set(df["company_id"].dropna().str.strip().str.upper())
    db_extra = db_analysis[~db_analysis["company_id"].isin(excel_ids)]
    if len(db_extra) > 0:
        print(f"  Adding {len(db_extra)} companies from DB not in Excel")
        df = pd.concat([df, db_extra], ignore_index=True)

    # ── 2. Parse all text fields ───────────────────────────────────────────
    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():
        company_id = str(row.get("company_id", "")).strip().upper()
        if not company_id or company_id == "NAN":
            continue

        for metric in METRIC_COLUMNS:
            raw_text = row.get(metric)
            parsed, unmatched = parse_text_field(raw_text)

            for period, value in parsed:
                parsed_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "period_years": period,
                        "value_pct": value,
                    }
                )

            for reason in unmatched:
                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "raw_text": str(raw_text).strip()[:200],
                        "reason": f"No regex match: {reason}",
                    }
                )

    # ── 3. Save parsed CSV ─────────────────────────────────────────────────
    parsed_df = pd.DataFrame(parsed_rows)
    parsed_df.to_csv(PARSED_CSV, index=False)
    print(f"\n[OK] Saved {len(parsed_df)} parsed entries to {PARSED_CSV}")
    print(f"   Unique companies: {parsed_df['company_id'].nunique()}")
    print("   Metrics breakdown:")
    for metric in METRIC_COLUMNS:
        count = len(parsed_df[parsed_df["metric_type"] == metric])
        print(f"     {metric}: {count} entries")

    # ── 4. Save failures CSV ───────────────────────────────────────────────
    failures_df = pd.DataFrame(failure_rows)
    failures_df.to_csv(FAILURES_CSV, index=False)
    print(f"\n[WARN] Saved {len(failures_df)} parse failures to {FAILURES_CSV}")

    # -- 5. Cross-validate against computed CAGRs --
    print("\n-- Cross-Validation --")
    computed = load_computed_cagrs()
    print(f"  Loaded computed CAGRs for {len(computed)} companies")

    divergence_rows = []

    for (metric_type, period), col_name in CROSS_VAL_MAP.items():
        subset = parsed_df[
            (parsed_df["metric_type"] == metric_type)
            & (parsed_df["period_years"] == period)
        ]

        for _, prow in subset.iterrows():
            cid = prow["company_id"]
            parsed_val = prow["value_pct"]

            comp_row = computed[computed["company_id"] == cid]
            if comp_row.empty:
                continue

            computed_val = comp_row.iloc[0][col_name]
            if computed_val is None or pd.isna(computed_val):
                continue

            divergence = abs(parsed_val - computed_val)
            if divergence > DIVERGENCE_THRESHOLD:
                divergence_rows.append(
                    {
                        "company_id": cid,
                        "metric_type": f"{metric_type}_{period}yr",
                        "parsed_value": parsed_val,
                        "computed_value": round(computed_val, 2),
                        "divergence_pct": round(divergence, 2),
                    }
                )

    divergence_df = pd.DataFrame(divergence_rows)
    divergence_df.to_csv(DIVERGENCE_CSV, index=False)
    print(f"  Found {len(divergence_df)} divergences > {DIVERGENCE_THRESHOLD}%")
    print(f"  Saved to {DIVERGENCE_CSV}")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PARSER SUMMARY")
    print("=" * 60)
    print(f"  Total parsed entries:  {len(parsed_df)}")
    print(f"  Total failures:        {len(failures_df)}")
    print(f"  CAGR divergences:      {len(divergence_df)}")
    print(f"  Companies in parsed:   {parsed_df['company_id'].nunique()}")
    print("=" * 60)


if __name__ == "__main__":
    run_parser()
