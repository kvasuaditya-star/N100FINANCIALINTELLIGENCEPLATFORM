import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import (
    apply_custom_style,
    get_bs,
    get_companies,
    get_connection,
    get_pl,
    get_ratios,
)

# Set page config
st.set_page_config(page_title="Nifty 100 Analytics - Company Profile", layout="wide")

apply_custom_style()

st.title("📊 Company Profile")

# Load company master lists
df_companies = get_companies()

if df_companies.empty:
    st.error("No companies data found in the database.")
else:
    # Format options for selectbox
    company_options = [
        f"{row['id']} - {row['company_name']}" for _, row in df_companies.iterrows()
    ]

    # Autocomplete text search box
    selected_option = st.selectbox("Search Company by Name or Ticker", company_options)

    if selected_option:
        ticker = selected_option.split(" - ")[0].strip()

        # Get target company row
        co_row = df_companies[df_companies["id"] == ticker]

        if co_row.empty:
            st.error("Ticker not found - please try another")
        else:
            co_data = co_row.iloc[0]

            # Display Company Card
            st.markdown(
                f"""
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 25px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="margin: 0; color: #00e5ff;">{co_data['company_name']}</h2>
                        <span style="background: #00e5ff; color: #121212; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9rem;">{co_data['id']}</span>
                    </div>
                    <p style="color: #00e5ff; font-weight: 600; margin-top: 5px; font-size: 0.95rem;">
                        {co_data['broad_sector']} &bull; {co_data['sub_sector']}
                    </p>
                    <p style="color: #b0bec5; font-size: 1rem; line-height: 1.6; margin-top: 15px;">
                        {co_data['about_company'] if co_data['about_company'] else 'No description available.'}
                    </p>
                    <div style="margin-top: 20px; font-size: 0.9rem;">
                        <strong>Website:</strong> <a href="{co_data['website']}" target="_blank" style="color: #00e5ff;">{co_data['website'] if co_data['website'] else 'N/A'}</a>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>NSE Profile:</strong> <a href="{co_data['nse_profile']}" target="_blank" style="color: #00e5ff;">View NSE</a>
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>BSE Profile:</strong> <a href="{co_data['bse_profile']}" target="_blank" style="color: #00e5ff;">View BSE</a>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Fetch statement histories
            df_ratios = get_ratios(ticker)
            df_pl = get_pl(ticker)
            df_bs = get_bs(ticker)

            # Compute ROCE dynamically for all years: EBIT / (Equity + Debt)
            # Alignment on year
            roce_records = []
            for _, r in df_pl.iterrows():
                yr = r["year"]
                pbt = r["profit_before_tax"]
                interest = r["interest"] if r["interest"] is not None else 0

                # Get balance sheet values
                bs_yr = df_bs[df_bs["year"] == yr]
                if not bs_yr.empty:
                    equity_cap = bs_yr.iloc[0]["equity_capital"]
                    reserves = bs_yr.iloc[0]["reserves"]
                    borrowings = (
                        bs_yr.iloc[0]["borrowings"]
                        if bs_yr.iloc[0]["borrowings"] is not None
                        else 0
                    )

                    ebit = (pbt if pbt is not None else 0) + interest
                    capital_employed = (
                        (equity_cap if equity_cap is not None else 0)
                        + (reserves if reserves is not None else 0)
                        + borrowings
                    )

                    if capital_employed > 0:
                        roce = (ebit / capital_employed) * 100.0
                    else:
                        roce = None
                else:
                    roce = None

                roce_records.append({"year": yr, "computed_roce": roce})

            df_computed_roce = pd.DataFrame(roce_records)

            # Merge computed ROCE into ratios
            if not df_ratios.empty and not df_computed_roce.empty:
                df_ratios = pd.merge(df_ratios, df_computed_roce, on="year", how="left")
            elif df_ratios.empty and not df_computed_roce.empty:
                df_ratios = df_computed_roce
                df_ratios["return_on_equity_pct"] = np.nan
                df_ratios["debt_to_equity"] = np.nan
                df_ratios["revenue_cagr_5yr"] = np.nan
                df_ratios["free_cash_flow_cr"] = np.nan
                df_ratios["net_profit_margin_pct"] = np.nan

            # Sort by year descending to get latest year for KPIs
            df_ratios_sorted = df_ratios.sort_values(by="year", ascending=False)

            if not df_ratios_sorted.empty:
                latest_ratio = df_ratios_sorted.iloc[0]

                # Fetch values
                val_roe = latest_ratio.get("return_on_equity_pct")
                val_roce = latest_ratio.get("computed_roce")
                val_npm = latest_ratio.get("net_profit_margin_pct")
                val_de = latest_ratio.get("debt_to_equity")
                val_cagr = latest_ratio.get("revenue_cagr_5yr")
                val_fcf = latest_ratio.get("free_cash_flow_cr")

                # Display 6 KPIs
                kpi_cols = st.columns(6)

                kpis = [
                    ("ROE", f"{val_roe:.2f}%" if not pd.isna(val_roe) else "N/A"),
                    ("ROCE", f"{val_roce:.2f}%" if not pd.isna(val_roce) else "N/A"),
                    (
                        "Net Profit Margin",
                        f"{val_npm:.2f}%" if not pd.isna(val_npm) else "N/A",
                    ),
                    ("D/E Ratio", f"{val_de:.2f}" if not pd.isna(val_de) else "N/A"),
                    (
                        "Revenue CAGR 5yr",
                        f"{val_cagr:.2f}%" if not pd.isna(val_cagr) else "N/A",
                    ),
                    (
                        "FCF (Latest Year)",
                        f"₹{val_fcf:.1f} Cr" if not pd.isna(val_fcf) else "N/A",
                    ),
                ]

                for col, (title, val_str) in zip(kpi_cols, kpis):
                    with col:
                        st.markdown(
                            f"""
                            <div class="kpi-card">
                                <div class="kpi-title">{title}</div>
                                <div class="kpi-value">{val_str}</div>
                            </div>
                        """,
                            unsafe_allow_html=True,
                        )
            else:
                st.warning("No financial ratios data found for this company.")

            st.markdown("<br>", unsafe_allow_html=True)

            # 4. Charts Section
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.subheader("Revenue and Net Profit (10 Years)")
                if not df_pl.empty:
                    fig_bar = go.Figure()
                    fig_bar.add_trace(
                        go.Bar(
                            x=df_pl["year"],
                            y=df_pl["sales"],
                            name="Revenue (Sales)",
                            marker_color="#00e5ff",
                        )
                    )
                    fig_bar.add_trace(
                        go.Bar(
                            x=df_pl["year"],
                            y=df_pl["net_profit"],
                            name="Net Profit",
                            marker_color="#26a69a",
                        )
                    )
                    fig_bar.update_layout(
                        barmode="group",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                        margin=dict(t=30, b=10, l=10, r=10),
                        yaxis=dict(
                            gridcolor="rgba(255,255,255,0.05)", title="Amount (Cr)"
                        ),
                        xaxis=dict(title="Fiscal Year"),
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.write("No Revenue/Profit data available.")

            with chart_col2:
                st.subheader("ROE vs ROCE Line Chart (10 Years)")
                # Sort ratios chronologically for line charts
                df_ratios_chrono = df_ratios.sort_values(by="year", ascending=True)

                if not df_ratios_chrono.empty:
                    fig_line = make_subplots(specs=[[{"secondary_y": True}]])

                    fig_line.add_trace(
                        go.Scatter(
                            x=df_ratios_chrono["year"],
                            y=df_ratios_chrono["return_on_equity_pct"],
                            name="ROE %",
                            line=dict(color="#00e5ff", width=3),
                            mode="lines+markers",
                        ),
                        secondary_y=False,
                    )

                    fig_line.add_trace(
                        go.Scatter(
                            x=df_ratios_chrono["year"],
                            y=df_ratios_chrono["computed_roce"],
                            name="ROCE %",
                            line=dict(color="#ff7043", width=3, dash="dash"),
                            mode="lines+markers",
                        ),
                        secondary_y=True,
                    )

                    fig_line.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                        margin=dict(t=30, b=10, l=10, r=10),
                        xaxis=dict(title="Fiscal Year"),
                    )

                    fig_line.update_yaxes(
                        title_text="ROE (%)",
                        secondary_y=False,
                        gridcolor="rgba(255,255,255,0.05)",
                    )
                    fig_line.update_yaxes(title_text="ROCE (%)", secondary_y=True)

                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.write("No ROE/ROCE data available.")

            st.markdown(
                "<br><hr style='border:0.5px solid rgba(255,255,255,0.1);'><br>",
                unsafe_allow_html=True,
            )

            # 5. Pros and Cons Section
            st.subheader("📋 Analyst Pros & Cons")

            # Fetch from DB
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "SELECT pros, cons FROM prosandcons WHERE company_id = ?", (ticker,)
            )
            pc_row = c.fetchone()
            conn.close()

            pro_col, con_col = st.columns(2)

            with pro_col:
                st.markdown(
                    "<h4 style='color: #26a69a;'>✔️ Key Strengths (Pros)</h4>",
                    unsafe_allow_html=True,
                )
                if pc_row and pc_row[0]:
                    pros_list = [
                        p.strip().lstrip("-").strip()
                        for p in pc_row[0].split("\n")
                        if p.strip()
                    ]
                    for pro in pros_list:
                        st.markdown(
                            f'<div class="pro-badge">✔️ {pro}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.write("No positive key metrics highlighted.")

            with con_col:
                st.markdown(
                    "<h4 style='color: #ef5350;'>❌ Risk Areas (Cons)</h4>",
                    unsafe_allow_html=True,
                )
                if pc_row and pc_row[1]:
                    cons_list = [
                        c.strip().lstrip("-").strip()
                        for c in pc_row[1].split("\n")
                        if c.strip()
                    ]
                    for con in cons_list:
                        st.markdown(
                            f'<div class="con-badge">❌ {con}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.write("No structural/debt risk areas highlighted.")
    else:
        st.info("Please select a company to view its detailed profile.")
