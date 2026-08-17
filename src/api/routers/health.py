import os
import sqlite3
import time

from fastapi import APIRouter

router = APIRouter(tags=["Health"])

START_TIME = time.time()
DB_PATH = "data/nifty100.db"


@router.get("/health")
def health_check():
    """
    Returns API status, SQLite database counts, system uptime, and API version.
    """
    uptime = time.time() - START_TIME

    db_counts = {}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # List of all 10 tables
            tables = [
                "companies",
                "sectors",
                "profitandloss",
                "balancesheet",
                "cashflow",
                "analysis",
                "documents",
                "prosandcons",
                "stock_prices",
                "market_cap",
            ]
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                db_counts[table] = cursor.fetchone()[0]

            conn.close()
        except Exception as e:
            db_counts = {"error": str(e)}
    else:
        db_counts = {"error": "Database file not found"}

    return {
        "status": "ok",
        "uptime_seconds": round(uptime, 2),
        "db_row_counts": db_counts,
        "version": "1.0.0",
    }
