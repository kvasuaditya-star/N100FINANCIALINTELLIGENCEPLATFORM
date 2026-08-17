import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import apply_custom_style, get_companies, get_connection

# Set page config
st.set_page_config(page_title="Nifty 100 Analytics - Trend Analysis", layout="wide")

apply_custom_style()

st.title("📈 Trend Analysis")

# Load company list
df_companies = get_companies()

if df_companies.empty:
    st.error("No company data found in the database.")
else:
    # Company search autocomplete
    company_options = [
        f"{row['id']} - {row['company_name']}" for _, row in df_companies.iterrows()
    ]
    selected_option = st.selectbox("Search Company by Name or Ticker", company_options)

    if selected_option:
        ticker = selected_option.split(" - ")[0].strip()
        co_name = selected_option.split(" - ")[1].strip()

        # Load 10-year historical metrics for this company
        conn = get_connection()
        query = """
            SELECT 
                fr.year, 
                fr.return_on_equity_pct as ROE, 
                fr.debt_to_equity as DE, 
                fr.net_profit_margin_pct as NPM, 
                fr.free_cash_flow_cr as FCF, 
                fr.operating_profit_margin_pct as OPM, 
                fr.asset_turnover as Asset_Turnover,
                pl.sales as Revenue, 
                pl.net_profit as Net_Profit
            FROM financial_ratios fr
            LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND pl.year = fr.year
            WHERE fr.company_id = ?
            ORDER BY fr.year ASC
        """
        df_hist = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()

        if df_hist.empty:
            st.warning("No historical trend data available for this company.")
        else:
            # Let user select up to 3 metrics to plot
            metrics_available = {
                "Revenue": "Revenue (Sales) (Cr)",
                "Net_Profit": "Net Profit (Cr)",
                "ROE": "Return on Equity (%)",
                "NPM": "Net Profit Margin (%)",
                "OPM": "Operating Profit Margin (%)",
                "DE": "Debt to Equity (D/E)",
                "FCF": "Free Cash Flow (Cr)",
                "Asset_Turnover": "Asset Turnover",
            }

            st.markdown("### Metric Overlay Options")
            selected_metrics = st.multiselect(
                "Select up to 3 metrics to plot (Historical Trend)",
                options=list(metrics_available.keys()),
                format_func=lambda x: metrics_available[x],
                default=["Revenue", "Net_Profit"],
            )

            if not selected_metrics:
                st.info("Please select at least one metric to visualize the trend.")
            elif len(selected_metrics) > 3:
                st.error(
                    "You can select a maximum of 3 metrics to display on the chart."
                )
            else:
                # Plotly Trend Chart
                fig = go.Figure()

                # Colors for the metrics
                colors = ["#00e5ff", "#ff7043", "#26a69a"]

                for idx, metric in enumerate(selected_metrics):
                    metric_label = metrics_available[metric]
                    metric_color = colors[idx % len(colors)]

                    # Compute YoY percentage change
                    # Ensure series is float
                    series = df_hist[metric].astype(float)
                    yoy_pct = series.pct_change() * 100

                    # Create annotation labels (YoY % change)
                    # Skip YoY annotation for the first data point since there's no previous year
                    annotation_text = []
                    for i, pct in enumerate(yoy_pct):
                        if i == 0 or pd.isna(pct) or np.isinf(pct):
                            annotation_text.append("")
                        else:
                            annotation_text.append(f"{pct:+.1f}%")

                    # Add trace to Plotly chart
                    fig.add_trace(
                        go.Scatter(
                            x=df_hist["year"],
                            y=series,
                            name=metric_label,
                            text=annotation_text,
                            textposition="top center",
                            mode="lines+markers+text",
                            line=dict(color=metric_color, width=3),
                            marker=dict(size=8),
                            # Hover template shows YoY info
                            hovertemplate="<b>%{x}</b><br>"
                            + f"{metric_label}: "
                            + "%{y:.2f}<br>"
                            + "YoY Change: %{text}<extra></extra>",
                        )
                    )

                fig.update_layout(
                    title=f"10-Year Financial Trends for {co_name} ({ticker})",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="closest",
                    margin=dict(t=50, b=10, l=10, r=10),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                    ),
                    xaxis=dict(title="Fiscal Year (YYYY-MM)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Value"),
                )

                st.plotly_chart(fig, use_container_width=True)

                # Show historical data table below
                st.subheader("Historical Data Table")
                df_table = df_hist[["year"] + selected_metrics].copy()
                for m in selected_metrics:
                    df_table[m] = df_table[m].apply(
                        lambda x: round(x, 2) if not pd.isna(x) else "N/A"
                    )
                st.dataframe(df_table, use_container_width=True, hide_index=True)
