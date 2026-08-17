import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.screener.engine import apply_filters, compute_composite_score

router = APIRouter(tags=["Screener"])
DB_PATH = "data/nifty100.db"


@router.get("/screener")
def run_screener(
    min_roe: float | None = Query(None, description="Minimum Return on Equity (%)"),
    max_de: float | None = Query(None, description="Maximum Debt to Equity ratio"),
    min_fcf: float | None = Query(None, description="Minimum Free Cash Flow (Cr)"),
    sector: str | None = Query(None, description="Broad sector filter"),
    min_rev_cagr_5yr: float | None = Query(
        None, description="Minimum 5yr Revenue CAGR (%)"
    ),
    min_pat_cagr_5yr: float | None = Query(
        None, description="Minimum 5yr Net Profit CAGR (%)"
    ),
    max_pe: float | None = Query(
        None, description="Maximum Price-to-Earnings Ratio"
    ),
):
    """
    Screener endpoint matching core criteria. Validates params and returns ranked companies.
    """
    # Validation checks
    if min_roe is not None and min_roe < -500:
        raise HTTPException(status_code=400, detail="Invalid min_roe value")
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="Invalid max_de value")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="Invalid max_pe value")

    conn = sqlite3.connect(DB_PATH)

    # We load latest records for screener
    query = """
    WITH LatestYear AS (
        SELECT company_id, MAX(year) as latest_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        fr.*,
        c.company_name, c.roce_percentage as roce, 
        s.broad_sector, s.sub_sector,
        mc.pe_ratio, mc.pb_ratio, mc.dividend_yield_pct, mc.market_cap_crore,
        pl.sales, pl.net_profit,
        cf.operating_activity, cf.investing_activity
    FROM financial_ratios fr
    JOIN LatestYear ly ON fr.company_id = ly.company_id AND fr.year = ly.latest_year
    JOIN companies c ON fr.company_id = c.id
    LEFT JOIN sectors s ON fr.company_id = s.company_id
    LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(SUBSTR(fr.year, 1, 4) AS INTEGER) = mc.year
    LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND fr.year = pl.year
    LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND fr.year = cf.year
    """
    df = pd.read_sql_query(query, conn)
    df_cf = pd.read_sql_query(
        "SELECT company_id, year, operating_activity, investing_activity FROM cashflow",
        conn,
    )
    df_fr_hist = pd.read_sql_query(
        "SELECT company_id, year, debt_to_equity FROM financial_ratios", conn
    )
    conn.close()

    df = compute_composite_score(df, df_cf)

    # Translate API query params to engine filters
    filters = {}
    if min_roe is not None:
        filters["roe_min"] = min_roe
    if max_de is not None:
        filters["de_max"] = max_de
    if min_fcf is not None:
        filters["fcf_min"] = min_fcf
    if min_rev_cagr_5yr is not None:
        filters["revenue_cagr_5yr_min"] = min_rev_cagr_5yr
    if min_pat_cagr_5yr is not None:
        filters["pat_cagr_5yr_min"] = min_pat_cagr_5yr
    if max_pe is not None:
        filters["pe_max"] = max_pe

    filtered_df = apply_filters(df, df_fr_hist, filters)

    # Sector filter (custom string match)
    if sector:
        filtered_df = filtered_df[
            filtered_df["broad_sector"].str.lower() == sector.lower()
        ]

    filtered_df = filtered_df.sort_values(by="composite_quality_score", ascending=False)

    # Format and clean output
    res = filtered_df.fillna(0).to_dict(orient="records")
    return res
