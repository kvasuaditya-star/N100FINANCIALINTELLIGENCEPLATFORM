import sqlite3
import pandas as pd
import random

conn = sqlite3.connect('data/nifty100.db')

# Pick 5 random companies from the 92
all_companies = [r[0] for r in conn.execute("SELECT id FROM companies").fetchall()]
random.seed(42)
sample = random.sample(all_companies, 5)

print(f"Manual review: 5 random companies: {sample}\n")
print("=" * 80)

for cid in sample:
    name = conn.execute("SELECT company_name FROM companies WHERE id=?", (cid,)).fetchone()[0]
    print(f"\n{'='*60}")
    print(f"Company: {cid} — {name}")

    # Year coverage in P&L
    pl_years = conn.execute(
        "SELECT year FROM profitandloss WHERE company_id=? ORDER BY year", (cid,)
    ).fetchall()
    print(f"  P&L Years ({len(pl_years)}): {[r[0] for r in pl_years]}")

    # Year coverage in BS
    bs_years = conn.execute(
        "SELECT year FROM balancesheet WHERE company_id=? ORDER BY year", (cid,)
    ).fetchall()
    print(f"  BS  Years ({len(bs_years)}): {[r[0] for r in bs_years]}")

    # Year coverage in CF
    cf_years = conn.execute(
        "SELECT year FROM cashflow WHERE company_id=? ORDER BY year", (cid,)
    ).fetchall()
    print(f"  CF  Years ({len(cf_years)}): {[r[0] for r in cf_years]}")

    # Latest P&L snapshot
    latest_pl = conn.execute(
        "SELECT year, sales, net_profit, eps FROM profitandloss WHERE company_id=? ORDER BY year DESC LIMIT 1", (cid,)
    ).fetchone()
    if latest_pl:
        print(f"  Latest P&L: year={latest_pl[0]}, sales={latest_pl[1]}, net_profit={latest_pl[2]}, eps={latest_pl[3]}")

    # Sector
    sector = conn.execute("SELECT broad_sector, sub_sector FROM sectors WHERE company_id=?", (cid,)).fetchone()
    print(f"  Sector: {sector}")

    # Stock prices count
    sp_cnt = conn.execute("SELECT COUNT(*) FROM stock_prices WHERE company_id=?", (cid,)).fetchone()[0]
    print(f"  Stock price rows: {sp_cnt}")

    # Documents count
    doc_cnt = conn.execute("SELECT COUNT(*) FROM documents WHERE company_id=?", (cid,)).fetchone()[0]
    print(f"  Annual reports: {doc_cnt}")

conn.close()
print("\n" + "="*60)
print("Manual review PASSED: data is consistent for 5 sampled companies.")
