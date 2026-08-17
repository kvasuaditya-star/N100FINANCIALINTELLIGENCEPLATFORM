import os

import pandas as pd
from fastapi import APIRouter

router = APIRouter(tags=["Portfolio"])
PORTFOLIO_STATS_CSV = "output/portfolio_stats.csv"


@router.get("/portfolio/stats")
def get_portfolio_percentiles():
    """
    Returns P10 through P90 percentile table for 10 core KPIs across all 92 companies.
    """
    if not os.path.exists(PORTFOLIO_STATS_CSV):
        return {
            "error": "Portfolio stats report not yet generated. Run clustering/analytics first."
        }

    df = pd.read_csv(PORTFOLIO_STATS_CSV)
    return df.to_dict(orient="records")
