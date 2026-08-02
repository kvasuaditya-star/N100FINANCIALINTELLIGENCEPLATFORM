import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import sys

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import apply_custom_style, get_merged_data

# Set wide layout config for native page execution
st.set_page_config(page_title="Nifty 100 Analytics - Home", layout="wide")

apply_custom_style()

st.title("🏠 Home Dashboard")

# Sidebar Year Selector (2019 to 2024)
selected_year = st.sidebar.selectbox("Select Year", list(range(2024, 2018, -1)), index=0)

# Fetch merged data for selected year
df = get_merged_data(selected_year)

if df.empty:
    st.warning(f"No data available for the year {selected_year}.")
else:
    # 1. Calculate KPI Metrics
    avg_roe = df['return_on_equity_pct'].mean()
    median_pe = df['pe_ratio'].median()
    median_de = df['debt_to_equity'].median()
    total_companies = len(df)
    median_rev_cagr = df['revenue_cagr_5yr'].median()
    
    # Debt-Free definition: D/E <= 0.01 or ICR Label is 'Debt Free'
    debt_free_mask = (df['debt_to_equity'] <= 0.01) | (df['icr_label'] == 'Debt Free')
    debt_free_count = df[debt_free_mask]['company_id'].nunique()

    # 2. Render 6 KPI Tiles in a grid
    kpi_cols = st.columns(6)
    
    kpis = [
        ("Total Companies", f"{total_companies}", "Count of tracked stocks"),
        ("Average ROE", f"{avg_roe:.2f}%" if not pd.isna(avg_roe) else "N/A", "Return on Equity"),
        ("Median P/E", f"{median_pe:.2f}" if not pd.isna(median_pe) else "N/A", "Price to Earnings"),
        ("Median D/E", f"{median_de:.2f}" if not pd.isna(median_de) else "N/A", "Debt to Equity"),
        ("Median Rev CAGR (5y)", f"{median_rev_cagr:.2f}%" if not pd.isna(median_rev_cagr) else "N/A", "Top-line compound growth"),
        ("Debt-Free Companies", f"{debt_free_count}", "Zero/Negligible Debt")
    ]

    for col, (title, value, desc) in zip(kpi_cols, kpis):
        with col:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title" title="{desc}">{title}</div>
                    <div class="kpi-value">{value}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Two columns for charts/tables
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("🍩 Sector Distribution")
        # Sector breakdown
        sector_counts = df.groupby('broad_sector')['company_id'].count().reset_index(name='company_count')
        sector_counts = sector_counts.sort_values(by='company_count', ascending=False)
        
        # Plotly donut chart
        fig = px.pie(
            sector_counts,
            values='company_count',
            names='broad_sector',
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("🏆 Top 5 Companies by Quality Score")
        # Filter and sort
        df_sorted = df.sort_values(by='composite_quality_score', ascending=False)
        top_5 = df_sorted.head(5).copy()
        
        # Formatted fields
        top_5['Composite Score'] = top_5['composite_quality_score'].round(2)
        top_5['ROE %'] = top_5['return_on_equity_pct'].apply(lambda x: f"{x:.2f}%" if not pd.isna(x) else "N/A")
        top_5['D/E'] = top_5['debt_to_equity'].apply(lambda x: f"{x:.2f}" if not pd.isna(x) else "N/A")
        top_5['FCF (Cr)'] = top_5['free_cash_flow_cr'].apply(lambda x: f"₹{x:,.2f}" if not pd.isna(x) else "N/A")
        
        display_df = top_5[['company_id', 'company_name', 'broad_sector', 'Composite Score', 'ROE %', 'D/E', 'FCF (Cr)']].rename(
            columns={
                'company_id': 'Ticker',
                'company_name': 'Company Name',
                'broad_sector': 'Sector'
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
