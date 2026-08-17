import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Valuation"])
DB_PATH = "data/nifty100.db"


@router.get("/market-cap/{ticker}")
def get_historical_valuation(ticker: str):
    """
    Returns historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield) from 2019 to 2024.
    """
    conn = sqlite3.connect(DB_PATH)

    # Verify company exists
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker.upper(),))
    exists = cursor.fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Company not found")

    query = """
        SELECT year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
        AND year >= 2019 AND year <= 2024
        ORDER BY year
    """
    df = pd.read_sql_query(query, conn, params=(ticker.upper(),))
    conn.close()

    return df.fillna(0).to_dict(orient="records")
