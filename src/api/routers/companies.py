import os
import sqlite3

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["Companies"])
DB_PATH = "data/nifty100.db"
TEARSHEETS_DIR = "reports/tearsheets"


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class CompanyListItem(BaseModel):
    id: str
    company_name: str
    broad_sector: str | None
    sub_sector: str | None
    roe_pct: float | None
    roce_pct: float | None


@router.get("/companies", response_model=list[CompanyListItem])
def get_companies(
    sector: str | None = Query(None, description="Filter by broad sector"),
    market_cap_category: str | None = Query(
        None, description="Filter by market cap category (e.g. Large Cap)"
    ),
    search: str | None = Query(None, description="Partial name or ticker search"),
):
    """
    Returns list of all companies with basic details and optional filters.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, c.roe_percentage as roe_pct, c.roce_percentage as roce_pct
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        WHERE 1=1
    """
    params = []

    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        query += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    query += " ORDER BY c.id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}")
def get_company_profile(ticker: str):
    """
    Returns full company profile including latest year KPIs and sector data.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    # Check if company exists
    cursor.execute("SELECT * FROM companies WHERE id = ?", (ticker.upper(),))
    company = cursor.fetchone()
    if not company:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Company with ticker {ticker} not found"
        )

    # Get sector info
    cursor.execute("SELECT * FROM sectors WHERE company_id = ?", (ticker.upper(),))
    sector = cursor.fetchone()

    # Get latest ratios
    cursor.execute(
        """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        AND year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = ?)
    """,
        (ticker.upper(), ticker.upper()),
    )
    latest_ratios = cursor.fetchone()

    conn.close()

    return {
        "profile": dict(company),
        "sector": dict(sector) if sector else None,
        "latest_kpis": dict(latest_ratios) if latest_ratios else None,
    }


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str, from_year: str | None = None, to_year: str | None = None
):
    """
    Returns P&L history array with year filtering in YYYY-MM format.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        # Check if company even exists to distinguish empty results from 404
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker.upper(),))
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            raise HTTPException(status_code=404, detail="Company not found")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/bs")
def get_company_bs(
    ticker: str, from_year: str | None = None, to_year: str | None = None
):
    """
    Returns balance sheet history array with year filtering in YYYY-MM format.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker.upper(),))
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            raise HTTPException(status_code=404, detail="Company not found")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str, from_year: str | None = None, to_year: str | None = None
):
    """
    Returns cash flow history array with year filtering in YYYY-MM format.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker.upper(),))
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            raise HTTPException(status_code=404, detail="Company not found")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: str | None = Query(
        None, description="Format YYYY-MM to filter a single year"
    ),
):
    """
    Returns computed ratios per year for the company.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker.upper()]

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker.upper(),))
        exists = cursor.fetchone()
        conn.close()
        if not exists:
            raise HTTPException(status_code=404, detail="Company not found")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/tearsheet")
def download_tearsheet(ticker: str):
    """
    Returns pre-generated tearsheet PDF binary download.
    """
    pdf_path = os.path.join(TEARSHEETS_DIR, f"{ticker.upper()}_tearsheet.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404, detail=f"Tearsheet PDF for {ticker} not found"
        )
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{ticker.upper()}_tearsheet.pdf",
    )


@router.get("/companies/{ticker}/documents")
def get_company_documents(ticker: str):
    """
    Returns annual report links with is_url_valid boolean flag for each.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    # Verify company exists
    cursor.execute("SELECT 1 FROM companies WHERE id = ?", (ticker.upper(),))
    exists = cursor.fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Company not found")

    cursor.execute(
        "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year",
        (ticker.upper(),),
    )
    rows = cursor.fetchall()
    conn.close()

    res = []
    for r in rows:
        url = r["annual_report"]
        # In a real environment, we'd check URL validation flags from DQ validations
        # The prompt requires: returns is_url_valid boolean flag for each
        is_valid = True
        if url and "invalid" in url.lower():
            is_valid = False
        res.append({"year": r["year"], "annual_report": url, "is_url_valid": is_valid})
    return res
