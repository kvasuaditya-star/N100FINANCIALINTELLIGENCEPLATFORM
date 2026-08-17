import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Output directories
os.makedirs("reports", exist_ok=True)
os.makedirs("output", exist_ok=True)


def run_analytics_and_clustering(db_path="data/nifty100.db"):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)

    # 1. Fetch latest year financial ratios & sector info
    query = """
    WITH LatestYear AS (
        SELECT company_id, MAX(year) as latest_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        fr.company_id,
        fr.year,
        fr.return_on_equity_pct,
        fr.debt_to_equity,
        fr.revenue_cagr_5yr,
        fr.pat_cagr_5yr,
        fr.operating_profit_margin_pct,
        fr.net_profit_margin_pct,
        fr.interest_coverage,
        fr.asset_turnover,
        fr.free_cash_flow_cr,
        fr.earnings_per_share,
        s.broad_sector,
        s.sub_sector
    FROM financial_ratios fr
    JOIN LatestYear ly ON fr.company_id = ly.company_id AND fr.year = ly.latest_year
    LEFT JOIN sectors s ON fr.company_id = s.company_id
    """
    df = pd.read_sql_query(query, conn)

    # Also fetch all historical cashflow data to calculate FCF CAGR 5yr if needed
    df_cf = pd.read_sql_query(
        "SELECT company_id, year, operating_activity, investing_activity FROM cashflow",
        conn,
    )
    conn.close()

    # Calculate fcf_cagr_5yr manually using the cashflow history consistent with composite score logic
    fcf_cagrs = []
    for _, row in df.iterrows():
        cid = row["company_id"]
        year = row["year"]
        try:
            year_num = int(year[:4])
            start_year = str(year_num - 5)

            end_cf = df_cf[
                (df_cf["company_id"] == cid)
                & (df_cf["year"].str.startswith(str(year_num)))
            ]
            start_cf = df_cf[
                (df_cf["company_id"] == cid)
                & (df_cf["year"].str.startswith(start_year))
            ]

            if not end_cf.empty and not start_cf.empty:
                end_fcf = float(
                    end_cf["operating_activity"].values[0]
                    + end_cf["investing_activity"].values[0]
                )
                start_fcf = float(
                    start_cf["operating_activity"].values[0]
                    + start_cf["investing_activity"].values[0]
                )

                if start_fcf > 0 and end_fcf > 0:
                    cagr = ((end_fcf / start_fcf) ** (0.2) - 1.0) * 100
                else:
                    cagr = 0.0
            else:
                cagr = 0.0
        except Exception:
            cagr = 0.0
        fcf_cagrs.append(cagr)
    df["fcf_cagr_5yr"] = fcf_cagrs

    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # --- Day 36: KMeans Clustering ---
    # Impute missing values with sector median for each metric
    df_imputed = df.copy()
    for feat in features:
        # Sector median imputation
        df_imputed[feat] = df_imputed.groupby("broad_sector")[feat].transform(
            lambda x: x.fillna(x.median())
        )
        # If there are still NaNs (e.g. sectors with all NaNs), impute with global median
        df_imputed[feat] = df_imputed[feat].fillna(df_imputed[feat].median())

    # Apply StandardScaler
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_imputed[features])

    # Generate Elbow plot
    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        kmeans.fit(scaled_features)
        inertias.append(kmeans.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(k_range, inertias, "go-", linewidth=2, markersize=8)
    plt.title("KMeans Elbow Plot (Inertia vs. Number of Clusters)")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.savefig("reports/elbow_plot.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Run final KMeans with k=5
    kmeans_5 = KMeans(n_clusters=5, random_state=42, n_init="auto")
    cluster_ids = kmeans_5.fit_predict(scaled_features)
    df_imputed["cluster_id"] = cluster_ids

    # Calculate distance from centroid
    centroids = kmeans_5.cluster_centers_
    distances = []
    for i, row in enumerate(scaled_features):
        c_id = cluster_ids[i]
        centroid = centroids[c_id]
        dist = np.linalg.norm(row - centroid)
        distances.append(dist)
    df_imputed["distance_from_centroid"] = distances

    # Profile clusters to map names
    # Compute median profiles for identification
    profiles = df_imputed.groupby("cluster_id")[features].median()

    # Map clusters to descriptive names based on their profiles
    # Cluster profiling identification rules:
    # 1. High ROE & high margin -> High-Quality Compounders
    # 2. High growth (revenue & fcf) -> Emerging Growth
    # 3. High debt/moderate ROE -> Value Cyclicals / Defensive Dividend Payers
    # Let's dynamically assign based on rank
    cluster_mapping = {}
    remaining_names = [
        "High-Quality Compounders",
        "Emerging Growth",
        "Defensive Dividend Payers",
        "Value Cyclicals",
        "Distressed or Turnaround",
    ]

    # Find Distressed or Turnaround: Lowest ROE or lowest margins or negative growth
    distressed_id = profiles["return_on_equity_pct"].idxmin()
    cluster_mapping[distressed_id] = "Distressed or Turnaround"
    remaining_names.remove("Distressed or Turnaround")

    # Find High-Quality Compounders: Highest ROE from remaining
    available_profiles = profiles.drop(distressed_id)
    hq_id = available_profiles["return_on_equity_pct"].idxmax()
    cluster_mapping[hq_id] = "High-Quality Compounders"
    remaining_names.remove("High-Quality Compounders")

    # Find Emerging Growth: Highest revenue cagr from remaining
    available_profiles = available_profiles.drop(hq_id)
    growth_id = available_profiles["revenue_cagr_5yr"].idxmax()
    cluster_mapping[growth_id] = "Emerging Growth"
    remaining_names.remove("Emerging Growth")

    # Find Value Cyclicals: Highest debt to equity from remaining
    available_profiles = available_profiles.drop(growth_id)
    cyclical_id = available_profiles["debt_to_equity"].idxmax()
    cluster_mapping[cyclical_id] = "Value Cyclicals"
    remaining_names.remove("Value Cyclicals")

    # Last one is Defensive Dividend Payers
    last_id = available_profiles.index.difference([cyclical_id])[0]
    cluster_mapping[last_id] = "Defensive Dividend Payers"

    df_imputed["cluster_name"] = df_imputed["cluster_id"].map(cluster_mapping)

    # Save output/cluster_labels.csv
    labels_csv = df_imputed[
        ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    ]
    labels_csv.to_csv("output/cluster_labels.csv", index=False)
    print("Saved output/cluster_labels.csv")

    # --- Day 37: Statistics, Correlation Heatmap & Outliers ---
    # Correlation heatmap of 10 KPIs
    kpi_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "earnings_per_share",
    ]
    df_kpis = df_imputed[kpi_cols].copy()
    # Replace interest coverage inf/labels for math
    df_kpis["interest_coverage"] = pd.to_numeric(
        df_kpis["interest_coverage"], errors="coerce"
    ).fillna(100.0)

    corr_matrix = df_kpis.corr(method="pearson")
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("Pearson Correlation Heatmap of 10 Core KPIs")
    plt.savefig("reports/correlation_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved reports/correlation_heatmap.png")

    # Outlier detection: Z-score per broad_sector
    outliers = []
    for sector, grp in df_imputed.groupby("broad_sector"):
        if len(grp) < 3:
            # Not enough companies in sector for reliable z-score, skip
            continue
        for feat in features:
            mean = grp[feat].mean()
            std = grp[feat].std()
            if std == 0 or pd.isna(std):
                continue
            for idx, row in grp.iterrows():
                z = (row[feat] - mean) / std
                if abs(z) > 3.0:
                    outliers.append(
                        {
                            "company_id": row["company_id"],
                            "broad_sector": sector,
                            "metric": feat,
                            "value": row[feat],
                            "sector_mean": mean,
                            "z_score": z,
                        }
                    )
    df_outliers = pd.DataFrame(outliers)
    df_outliers.to_csv("output/outlier_report.csv", index=False)
    print("Saved output/outlier_report.csv")

    # Generate output/portfolio_stats.csv
    stats_list = []
    for col in kpi_cols:
        series = df_kpis[col].dropna()
        stats_list.append(
            {
                "KPI": col,
                "P10": series.quantile(0.10),
                "P25": series.quantile(0.25),
                "P50": series.quantile(0.50),
                "P75": series.quantile(0.75),
                "P90": series.quantile(0.90),
                "Mean": series.mean(),
                "Std": series.std(),
            }
        )
    df_stats = pd.DataFrame(stats_list)
    df_stats.to_csv("output/portfolio_stats.csv", index=False)
    print("Saved output/portfolio_stats.csv")


if __name__ == "__main__":
    run_analytics_and_clustering()
