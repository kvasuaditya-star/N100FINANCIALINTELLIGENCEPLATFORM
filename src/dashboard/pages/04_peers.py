import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import apply_custom_style, get_connection, get_merged_data

# Set page config
st.set_page_config(page_title="Nifty 100 Analytics - Peer Comparison", layout="wide")

apply_custom_style()

st.title("⚖️ Peer Comparison")

# Load peer groups from the database
conn = get_connection()
df_pg_list = pd.read_sql_query(
    "SELECT DISTINCT peer_group_name FROM peer_groups WHERE peer_group_name IS NOT NULL AND peer_group_name != 'No peer group assigned'",
    conn,
)
conn.close()

if df_pg_list.empty:
    st.error("No peer groups found in the database.")
else:
    peer_groups = sorted(df_pg_list["peer_group_name"].tolist())

    # 1. Peer Group Dropdown
    selected_group = st.selectbox("Select Peer Group", peer_groups)

    # Load all merged data for 2024 (latest year) to get current metrics
    df_latest = get_merged_data(2024)

    # Get all companies in this peer group by querying the peer_groups table
    conn = get_connection()
    df_group_mapping = pd.read_sql_query(
        "SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name = ?",
        conn,
        params=(selected_group,),
    )
    conn.close()

    if df_group_mapping.empty or df_latest.empty:
        st.warning("No data available for this peer group.")
    else:
        # Merge mappings with metrics
        group_df = pd.merge(
            df_group_mapping,
            df_latest,
            left_on="company_id",
            right_on="company_id",
            how="inner",
        )

        # 2. Select Company from Group
        company_names = {
            row["company_id"]: f"{row['company_id']} - {row['company_name']}"
            for _, row in group_df.iterrows()
        }
        selected_ticker = st.selectbox(
            "Select Target Company to Analyze",
            list(company_names.keys()),
            format_func=lambda x: company_names[x],
        )

        target_row = group_df[group_df["company_id"] == selected_ticker].iloc[0]

        # 3. Radar Chart Metrics Setup
        metrics_map = {
            "return_on_equity_pct": "ROE",
            "roce": "ROCE",
            "net_profit_margin_pct": "NPM",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF",
            "pat_cagr_5yr": "PAT CAGR 5y",
            "revenue_cagr_5yr": "Rev CAGR 5y",
            "composite_quality_score": "Composite",
        }

        # Get target values and median values
        comp_vals = [
            target_row.get(k, 0) if not pd.isna(target_row.get(k, 0)) else 0
            for k in metrics_map
        ]
        group_medians = [
            group_df[k].median() if not pd.isna(group_df[k].median()) else 0
            for k in metrics_map
        ]

        # Normalize metrics based on global max/min in df_latest (Nifty 100)
        norm_comp = []
        norm_group = []
        for i, k in enumerate(metrics_map.keys()):
            global_max = df_latest[k].max()
            global_min = df_latest[k].min()

            val_c = comp_vals[i]
            val_g = group_medians[i]

            if global_max > global_min:
                nc = (val_c - global_min) / (global_max - global_min)
                ng = (val_g - global_min) / (global_max - global_min)

                # Invert D/E (lower is better)
                if k == "debt_to_equity":
                    nc = 1.0 - nc
                    ng = 1.0 - ng
            else:
                nc = 0.5
                ng = 0.5
            norm_comp.append(nc * 100)  # scale to 100
            norm_group.append(ng * 100)

        # Complete the loop for radar chart
        radar_metrics = list(metrics_map.values()) + [list(metrics_map.values())[0]]
        norm_comp += [norm_comp[0]]
        norm_group += [norm_group[0]]

        # Plot Plotly Radar Chart
        fig = go.Figure()

        # Company Trace
        fig.add_trace(
            go.Scatterpolar(
                r=norm_comp,
                theta=radar_metrics,
                fill="toself",
                name=selected_ticker,
                line_color="#00e5ff",
                fillcolor="rgba(0, 229, 255, 0.15)",
            )
        )

        # Group Median Trace
        fig.add_trace(
            go.Scatterpolar(
                r=norm_group,
                theta=radar_metrics,
                fill="toself",
                name=f"{selected_group} Median",
                line_color="#ff7043",
                fillcolor="rgba(255, 112, 67, 0.15)",
                line=dict(dash="dash"),
            )
        )

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)
            ),
            showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=40, l=40, r=40),
        )

        st.subheader(
            f"📊 Radar Comparison: {selected_ticker} vs Peer Median (Percentile Basis)"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Side-by-Side KPI Table
        st.subheader("⚖️ Peer Group Leaderboard")

        # Columns formatting
        table_df = group_df.copy()
        table_df["Composite"] = table_df["composite_quality_score"].round(2)
        table_df["ROE %"] = table_df["return_on_equity_pct"].round(2)
        table_df["ROCE %"] = table_df["roce"].round(2)
        table_df["NPM %"] = table_df["net_profit_margin_pct"].round(2)
        table_df["D/E"] = table_df["debt_to_equity"].round(2)
        table_df["FCF (Cr)"] = table_df["free_cash_flow_cr"].round(2)
        table_df["PAT CAGR 5y %"] = table_df["pat_cagr_5yr"].round(2)
        table_df["Rev CAGR 5y %"] = table_df["revenue_cagr_5yr"].round(2)

        table_df["Benchmark"] = table_df["is_benchmark"].apply(
            lambda x: "Yes" if x == 1 else "No"
        )

        display_cols = [
            "company_id",
            "company_name",
            "Benchmark",
            "Composite",
            "ROE %",
            "ROCE %",
            "NPM %",
            "D/E",
            "FCF (Cr)",
            "PAT CAGR 5y %",
            "Rev CAGR 5y %",
        ]

        df_display = table_df[display_cols].rename(
            columns={"company_id": "Ticker", "company_name": "Company Name"}
        )

        # Styler function to highlight benchmark company row
        def highlight_benchmark_row(row):
            is_benchmark = row["Benchmark"] == "Yes"
            # Also check if it's the selected company to highlight it differently
            is_selected = row["Ticker"] == selected_ticker

            styles = []
            for val in row:
                if is_benchmark:
                    styles.append(
                        "background-color: rgba(255, 215, 0, 0.15); border: 1.5px solid #ffd700;"
                    )
                elif is_selected:
                    styles.append(
                        "background-color: rgba(0, 229, 255, 0.1); font-weight: bold;"
                    )
                else:
                    styles.append("")
            return styles

        styled_table = df_display.style.apply(highlight_benchmark_row, axis=1)

        st.dataframe(styled_table, use_container_width=True, hide_index=True)
