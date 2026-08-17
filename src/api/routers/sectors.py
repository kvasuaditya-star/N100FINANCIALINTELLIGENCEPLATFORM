import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Sectors"])
DB_PATH = "data/nifty100.db"


@router.get("/sectors")
def get_sectors_summary():
    """
    Returns all sectors with company count, median roe, median pe, and median debt to equity.
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            s.broad_sector as sector,
            COUNT(c.id) as company_count,
            c.roe_percentage as roe,
            mc.pe_ratio as pe,
            fr.debt_to_equity as de
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN market_cap mc ON c.id = mc.company_id AND mc.year = 2024
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id AND fr.year = '2024-03'
    """
    df = pd.read_sql_query(query, conn)

    # Reload cleaner structure for accurate grouping
    query_raw = """
        SELECT 
            s.broad_sector,
            fr.return_on_equity_pct as roe,
            mc.pe_ratio as pe,
            fr.debt_to_equity as de
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        LEFT JOIN market_cap mc ON c.id = mc.company_id AND mc.year = (SELECT MAX(year) FROM market_cap WHERE company_id = c.id)
    """
    df_raw = pd.read_sql_query(query_raw, conn)
    conn.close()

    if df_raw.empty:
        return []

    summary = []
    for sector, grp in df_raw.groupby("broad_sector"):
        if not sector or sector == "N/A":
            continue
        summary.append(
            {
                "sector": sector,
                "company_count": len(grp),
                "median_roe": (
                    float(grp["roe"].median()) if not grp["roe"].dropna().empty else 0.0
                ),
                "median_pe": (
                    float(grp["pe"].median()) if not grp["pe"].dropna().empty else 0.0
                ),
                "median_de": (
                    float(grp["de"].median()) if not grp["de"].dropna().empty else 0.0
                ),
            }
        )

    return summary


@router.get("/sectors/{sector}/companies")
def get_companies_in_sector(sector: str):
    """
    Returns all companies in a sector with latest year KPIs.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Case insensitive validation of sector
    cursor.execute("SELECT DISTINCT broad_sector FROM sectors")
    sectors = [r[0].lower() for r in cursor.fetchall() if r[0]]
    if sector.lower() not in sectors:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

    query = """
        SELECT 
            c.id, c.company_name, s.broad_sector, s.sub_sector,
            fr.*
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        WHERE s.broad_sector LIKE ?
    """
    df = pd.read_sql_query(query, conn, params=(sector,))
    conn.close()

    return df.fillna(0).to_dict(orient="records")
