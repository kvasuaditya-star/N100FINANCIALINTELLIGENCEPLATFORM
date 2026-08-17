import os
import sqlite3

import numpy as np
import pandas as pd

DB_PATH = "data/nifty100.db"


def main():
    print("Running valuation module...")

    # 1. Connect to database
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    # Fetch latest year of financial ratios for each company
    query_latest = """
        WITH LatestYear AS (
            SELECT company_id, MAX(year) as latest_year
            FROM financial_ratios
            GROUP BY company_id
        )
        SELECT 
            fr.company_id, c.company_name, s.broad_sector as sector,
            fr.year as ratio_year, fr.free_cash_flow_cr,
            mc.pe_ratio, mc.pb_ratio, mc.ev_ebitda, mc.market_cap_crore
        FROM financial_ratios fr
        JOIN LatestYear ly ON fr.company_id = ly.company_id AND fr.year = ly.latest_year
        JOIN companies c ON fr.company_id = c.id
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND CAST(SUBSTR(fr.year, 1, 4) AS INTEGER) = mc.year
    """
    df_latest = pd.read_sql_query(query_latest, conn)

    # Fetch historical market cap P/E ratios to compute 5-year median P/E
    query_hist_pe = """
        SELECT company_id, year, pe_ratio
        FROM market_cap
        ORDER BY company_id, year DESC
    """
    df_hist_pe = pd.read_sql_query(query_hist_pe, conn)
    conn.close()

    # 2. Compute 5-year median P/E for each company
    # For each company, we get the latest 5 years of P/E ratios and compute their median
    median_5yr_pes = {}
    for cid, group in df_hist_pe.groupby("company_id"):
        # Sort by year descending to get latest years
        group_sorted = group.sort_values(by="year", ascending=False)
        # Take the top 5 years
        top_5 = group_sorted.head(5)
        # Compute median of P/E ratios
        pe_vals = top_5["pe_ratio"].dropna()
        if not pe_vals.empty:
            median_5yr_pes[cid] = pe_vals.median()
        else:
            median_5yr_pes[cid] = np.nan

    df_latest["5yr_median_PE"] = df_latest["company_id"].map(median_5yr_pes)

    # 3. Compute FCF Yield: FCF / market_cap_crore * 100
    df_latest["FCF_yield_pct"] = np.where(
        (df_latest["market_cap_crore"] > 0) & (df_latest["free_cash_flow_cr"].notna()),
        (df_latest["free_cash_flow_cr"] / df_latest["market_cap_crore"]) * 100.0,
        np.nan,
    )

    # 4. Compute Sector Median P/E for each broad_sector in the latest year
    # Ignore negative or null P/E values for median calculation as per financial standards
    sector_medians = {}
    for sector, group in df_latest.groupby("sector"):
        pe_filtered = group[group["pe_ratio"] > 0]["pe_ratio"]
        if not pe_filtered.empty:
            sector_medians[sector] = pe_filtered.median()
        else:
            # Fallback if all P/Es are negative or null
            pe_all = group["pe_ratio"].dropna()
            sector_medians[sector] = pe_all.median() if not pe_all.empty else np.nan

    df_latest["sector_median_pe"] = df_latest["sector"].map(sector_medians)

    # 5. Compute P/E vs Sector Median Percentage Difference: (PE - sector_median) / sector_median * 100
    df_latest["PE_vs_sector_median_pct"] = np.where(
        (df_latest["sector_median_pe"] > 0) & (df_latest["pe_ratio"].notna()),
        (
            (df_latest["pe_ratio"] - df_latest["sector_median_pe"])
            / df_latest["sector_median_pe"]
        )
        * 100.0,
        np.nan,
    )

    # 6. Apply Overvaluation Flags
    # if P/E > sector_median x 1.5 -> Caution
    # if P/E < sector_median x 0.7 -> Discount
    # otherwise -> Fair
    # Loss-makers (PE <= 0) should be Fair/Caution rather than Discount
    flags = []
    for _, row in df_latest.iterrows():
        pe = row["pe_ratio"]
        sec_med = row["sector_median_pe"]

        if pd.isna(pe) or pd.isna(sec_med) or sec_med <= 0:
            flags.append("Fair")
        elif pe <= 0:
            # Loss making is not a discount
            flags.append("Fair")
        elif pe > sec_med * 1.5:
            flags.append("Caution")
        elif pe < sec_med * 0.7:
            flags.append("Discount")
        else:
            flags.append("Fair")

    df_latest["flag"] = flags

    # 7. Write output files
    os.makedirs("output", exist_ok=True)

    # Format and select columns for valuation_summary.xlsx
    summary_cols = [
        "company_id",
        "company_name",
        "sector",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    df_summary = df_latest[summary_cols].rename(
        columns={"pe_ratio": "P/E", "pb_ratio": "P/B", "ev_ebitda": "EV/EBITDA"}
    )

    # Round metrics for readability
    df_summary["FCF_yield_pct"] = df_summary["FCF_yield_pct"].round(2)
    df_summary["5yr_median_PE"] = df_summary["5yr_median_PE"].round(2)
    df_summary["PE_vs_sector_median_pct"] = df_summary["PE_vs_sector_median_pct"].round(
        2
    )
    df_summary["P/E"] = df_summary["P/E"].round(2)
    df_summary["P/B"] = df_summary["P/B"].round(2)
    df_summary["EV/EBITDA"] = df_summary["EV/EBITDA"].round(2)

    summary_excel_path = "output/valuation_summary.xlsx"
    df_summary.to_excel(summary_excel_path, index=False)
    print(
        f"Valuation summary excel generated at: {summary_excel_path} ({len(df_summary)} companies)"
    )

    # Generate output/valuation_flags.csv: only Caution or Discount flagged companies with supporting data
    df_flags = df_latest[df_latest["flag"].isin(["Caution", "Discount"])].copy()

    # Format and select columns for csv
    df_flags_export = df_flags[
        [
            "company_id",
            "company_name",
            "sector",
            "pe_ratio",
            "sector_median_pe",
            "PE_vs_sector_median_pct",
            "flag",
            "FCF_yield_pct",
            "5yr_median_PE",
        ]
    ].rename(
        columns={
            "pe_ratio": "P/E",
            "sector_median_pe": "Sector Median P/E",
            "PE_vs_sector_median_pct": "P/E vs Sector Median %",
        }
    )

    df_flags_export["P/E"] = df_flags_export["P/E"].round(2)
    df_flags_export["Sector Median P/E"] = df_flags_export["Sector Median P/E"].round(2)
    df_flags_export["P/E vs Sector Median %"] = df_flags_export[
        "P/E vs Sector Median %"
    ].round(2)
    df_flags_export["FCF_yield_pct"] = df_flags_export["FCF_yield_pct"].round(2)
    df_flags_export["5yr_median_PE"] = df_flags_export["5yr_median_PE"].round(2)

    flags_csv_path = "output/valuation_flags.csv"
    df_flags_export.to_csv(flags_csv_path, index=False)
    print(
        f"Valuation flags CSV generated at: {flags_csv_path} ({len(df_flags_export)} companies)"
    )


if __name__ == "__main__":
    main()
