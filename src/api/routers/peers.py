import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Peers"])
DB_PATH = "data/nifty100.db"


@router.get("/peers/{group_name}")
def get_peer_group_ratios(group_name: str):
    """
    Returns all companies in a peer group with percentile rank for each of 10 metrics.
    """
    conn = sqlite3.connect(DB_PATH)
    # Check if peer group exists
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT peer_group_name FROM peer_groups")
    groups = [r[0].lower() for r in cursor.fetchall()]
    if group_name.lower() not in groups:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Peer group '{group_name}' not found"
        )

    query = """
        SELECT pg.peer_group_name, pg.is_benchmark, c.company_name, fr.*
        FROM peer_groups pg
        JOIN companies c ON pg.company_id = c.id
        LEFT JOIN financial_ratios fr ON pg.company_id = fr.company_id
        WHERE pg.peer_group_name LIKE ?
        AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = pg.company_id)
    """
    df = pd.read_sql_query(query, conn, params=(group_name,))
    conn.close()

    if df.empty:
        return []

    metrics = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
    ]

    # Calculate percentiles for each metric within peer group
    for col in metrics:
        if col in df.columns:
            # We rank (lower is better for D/E and debt, higher is better for others)
            ascending = True if col in ["debt_to_equity", "total_debt_cr"] else False
            df[f"{col}_percentile"] = (
                df[col].rank(pct=True, ascending=not ascending) * 100.0
            )

    return df.fillna(0).to_dict(orient="records")


@router.get("/companies/{ticker}/peers/compare")
def compare_company_peers(ticker: str):
    """
    Returns radar data: 8 axis metric values for the company + peer group average + benchmark company.
    """
    conn = sqlite3.connect(DB_PATH)
    # Find peer group of the company
    cursor = conn.cursor()
    cursor.execute(
        "SELECT peer_group_name FROM peer_groups WHERE company_id = ?",
        (ticker.upper(),),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"No peer group found for company {ticker}"
        )

    group_name = row[0]

    # Fetch all group members with ratios
    query = """
        SELECT pg.peer_group_name, pg.is_benchmark, pg.company_id, fr.*
        FROM peer_groups pg
        LEFT JOIN financial_ratios fr ON pg.company_id = fr.company_id
        WHERE pg.peer_group_name = ?
        AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = pg.company_id)
    """
    df = pd.read_sql_query(query, conn, params=(group_name,))
    conn.close()

    if df.empty:
        raise HTTPException(status_code=404, detail="No ratio records found for group")

    metrics = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
    ]

    # Normalize metrics to 0-100 scale within the peer group for radar chart
    normalized_df = df.copy()
    for col in metrics:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:
                normalized_df[col] = (df[col] - min_val) / (max_val - min_val) * 100.0
            else:
                normalized_df[col] = 50.0

            if col == "debt_to_equity":
                normalized_df[col] = 100.0 - normalized_df[col]  # Invert debt

    # Extract target company
    target_row = normalized_df[normalized_df["company_id"] == ticker.upper()]
    if target_row.empty:
        raise HTTPException(
            status_code=404, detail="Target company ratio record not found"
        )

    # Extract benchmark company
    benchmark_row = normalized_df[normalized_df["is_benchmark"] == 1]
    if benchmark_row.empty:
        benchmark_row = normalized_df.iloc[0:1]  # Fallback

    # Calculate group average
    avg_profile = normalized_df[metrics].mean().to_dict()

    return {
        "company": target_row.iloc[0][metrics].to_dict(),
        "benchmark": benchmark_row.iloc[0][metrics].to_dict(),
        "peer_average": avg_profile,
        "peer_group_name": group_name,
    }
