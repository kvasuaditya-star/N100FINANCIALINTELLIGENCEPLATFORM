"""
Day 32 — Capital Allocation Report
Verifies capital_allocation.csv completeness, generates distribution summary,
and tracks pattern changes year-over-year.
"""

import os
import sqlite3

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
CAP_ALLOC_CSV = os.path.join(OUTPUT_DIR, "capital_allocation.csv")
PATTERN_CHANGES_CSV = os.path.join(OUTPUT_DIR, "pattern_changes.csv")
INTEL_XLSX = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")


def run_capital_allocation_report():
    """Main entry point."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. Load capital allocation data ────────────────────────────────────
    if not os.path.exists(CAP_ALLOC_CSV):
        print(f"[ERROR] {CAP_ALLOC_CSV} not found!")
        return

    ca = pd.read_csv(CAP_ALLOC_CSV)
    print(f"Loaded {len(ca)} rows from capital_allocation.csv")
    print(f"Columns: {list(ca.columns)}")

    # ── 2. Verify coverage for all 92 companies ───────────────────────────
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql_query("SELECT id FROM companies ORDER BY id", conn)
    conn.close()

    all_ids = set(companies["id"].tolist())
    ca_ids = set(ca["company_id"].unique())

    missing = all_ids - ca_ids
    extra = ca_ids - all_ids

    print("\nCoverage check:")
    print(f"  Companies in DB:            {len(all_ids)}")
    print(f"  Companies in CSV:           {len(ca_ids)}")
    print(f"  Missing from CSV:           {len(missing)}")
    if missing:
        print(f"    Missing tickers: {sorted(missing)}")
    if extra:
        print(f"  Extra in CSV (not in DB):   {sorted(extra)}")

    # ── 3. Latest year distribution ────────────────────────────────────────
    # For each company, get the latest year
    latest = ca.sort_values("year").groupby("company_id").last().reset_index()

    print(f"\n{'=' * 60}")
    print("CAPITAL ALLOCATION DISTRIBUTION (Latest Year)")
    print(f"{'=' * 60}")

    dist = latest["pattern_label"].value_counts().sort_index()
    for pattern, count in dist.items():
        print(f"  {pattern:30s}: {count:3d} companies")
    print(f"  {'TOTAL':30s}: {len(latest):3d}")

    # ── 4. Pattern changes year-over-year ─────────────────────────────────
    change_rows = []

    for cid in sorted(ca_ids):
        co_data = ca[ca["company_id"] == cid].sort_values("year")
        if len(co_data) < 2:
            continue

        # Compare last two years
        prev = co_data.iloc[-2]
        curr = co_data.iloc[-1]

        prev_pattern = prev["pattern_label"]
        curr_pattern = curr["pattern_label"]

        if prev_pattern != curr_pattern:
            change_rows.append(
                {
                    "company_id": cid,
                    "previous_year": prev["year"],
                    "previous_pattern": prev_pattern,
                    "latest_year": curr["year"],
                    "latest_pattern": curr_pattern,
                    "change_description": f"Moved from {prev_pattern} to {curr_pattern}",
                }
            )

    changes_df = pd.DataFrame(change_rows)
    changes_df.to_csv(PATTERN_CHANGES_CSV, index=False)

    print(f"\n{'=' * 60}")
    print("PATTERN CHANGES (Latest vs Previous Year)")
    print(f"{'=' * 60}")
    print(f"  Companies that changed pattern: {len(changes_df)}")

    if not changes_df.empty:
        # Show transition summary
        transitions = (
            changes_df.groupby(["previous_pattern", "latest_pattern"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        print("\n  Top transitions:")
        for _, t in transitions.head(10).iterrows():
            print(f"    {t['previous_pattern']} -> {t['latest_pattern']}: {t['count']}")

    print(f"\n[OK] Saved pattern changes to {PATTERN_CHANGES_CSV}")

    # ── 5. Update cashflow_intelligence.xlsx with capital allocation ──────
    if os.path.exists(INTEL_XLSX):
        intel = pd.read_excel(INTEL_XLSX)
        # Merge latest capital allocation label
        ca_latest = latest[["company_id", "pattern_label"]].rename(
            columns={"pattern_label": "capital_allocation_label_updated"}
        )
        intel = intel.merge(ca_latest, on="company_id", how="left")
        # Update the label column
        intel["capital_allocation_label"] = intel[
            "capital_allocation_label_updated"
        ].fillna(intel["capital_allocation_label"])
        intel = intel.drop(columns=["capital_allocation_label_updated"])
        intel.to_excel(INTEL_XLSX, index=False, engine="openpyxl")
        print(f"[OK] Updated capital allocation labels in {INTEL_XLSX}")


if __name__ == "__main__":
    run_capital_allocation_report()
