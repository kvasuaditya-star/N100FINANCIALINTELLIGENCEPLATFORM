"""
Day 34 — Batch Tearsheet Generation
Generates tearsheets for all 92 companies in the database.
"""

import os
import sys
import sqlite3
import pandas as pd
import time

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "tearsheets")

sys.path.insert(0, PROJECT_ROOT)
from src.reports.tearsheet import generate_tearsheet


def run_batch_generation():
    """Generate tearsheets for all companies in the DB."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql_query("SELECT id, company_name FROM companies ORDER BY id", conn)
    conn.close()

    company_ids = companies["id"].tolist()
    total = len(company_ids)

    print(f"Starting batch generation for {total} companies...")
    print("=" * 60)

    success_count = 0
    fail_count = 0
    start_time = time.time()

    for i, cid in enumerate(company_ids, 1):
        output_path = os.path.join(REPORTS_DIR, f"{cid}_tearsheet.pdf")
        
        try:
            success = generate_tearsheet(cid, output_path)
            if success:
                success_count += 1
                print(f"[{i:02d}/{total:02d}] [OK] Generated {cid}")
            else:
                fail_count += 1
                print(f"[{i:02d}/{total:02d}] [ERROR] Failed to generate {cid} - No data")
        except Exception as e:
            fail_count += 1
            print(f"[{i:02d}/{total:02d}] [ERROR] Failed {cid}: {e}")

    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("BATCH GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Total companies: {total}")
    print(f"  Successful:      {success_count}")
    print(f"  Failed:          {fail_count}")
    print(f"  Time taken:      {elapsed:.1f} seconds")
    print(f"  Output folder:   {REPORTS_DIR}")


if __name__ == "__main__":
    run_batch_generation()
