import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import sys

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import apply_custom_style, get_merged_data

# Set page config
st.set_page_config(page_title="Nifty 100 Analytics - Sector Analysis", layout="wide")

apply_custom_style()

st.title("🍩 Sector Analysis")

# Fetch latest merged data
df_latest = get_merged_data(2024)

if df_latest.empty:
    st.error("No company data found. Please check database is loaded.")
else:
    # 1. Sector Dropdown
    sectors_list = sorted(df_latest['broad_sector'].dropna().unique().tolist())
    selected_sector = st.selectbox("Select Broad Sector to Analyze", sectors_list)
    
    # Filter for selected sector
    df_sec = df_latest[df_latest['broad_sector'] == selected_sector]
    
    # 2. Bubble Chart: X = Revenue, Y = ROE, bubble size = Market Cap, colour = sub-sector
    # Clean data: drop any rows with NaN in X, Y, Size to prevent Plotly crashes
    df_chart = df_sec.dropna(subset=['sales', 'return_on_equity_pct', 'market_cap_crore'])
    
    if df_chart.empty:
        st.warning(f"No company metrics available in {selected_sector} to plot bubble chart.")
    else:
        st.subheader(f"Bubble Map of {selected_sector} Companies")
        st.markdown("*Bubble size corresponds to **Market Capitalization**. Bubble color corresponds to **Sub-Sector**.*")
        
        # Absolute scaling to ensure bubble sizes fit beautifully
        fig_bubble = px.scatter(
            df_chart,
            x='sales',
            y='return_on_equity_pct',
            size='market_cap_crore',
            color='sub_sector',
            hover_name='company_name',
            hover_data={
                'company_id': True,
                'sales': ':,.1f',
                'return_on_equity_pct': ':.2f',
                'market_cap_crore': ':,.1f'
            },
            size_max=60,
            labels={
                'sales': 'Revenue (Sales) (₹ Cr)',
                'return_on_equity_pct': 'Return on Equity (ROE %)',
                'market_cap_crore': 'Market Cap (₹ Cr)',
                'sub_sector': 'Sub Sector'
            },
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        
        fig_bubble.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=10, l=10, r=10),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("<br><hr style='border: 0.5px solid rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
    
    # 3. Sector Median KPI Bar Chart
    st.subheader("📊 Cross-Sector Median Performance Benchmark")
    
    # Group by broad sector to calculate medians
    sector_medians = df_latest.groupby('broad_sector')[
        ['return_on_equity_pct', 'pe_ratio', 'debt_to_equity', 'operating_profit_margin_pct', 'revenue_cagr_5yr']
    ].median().reset_index()
    
    # Metrics to benchmark
    benchmark_metrics = {
        'return_on_equity_pct': 'Median Return on Equity (ROE %)',
        'pe_ratio': 'Median Price to Earnings (P/E Ratio)',
        'debt_to_equity': 'Median Debt to Equity (D/E Ratio)',
        'operating_profit_margin_pct': 'Median Operating Profit Margin (OPM %)',
        'revenue_cagr_5yr': 'Median 5yr Revenue CAGR (%)'
    }
    
    metric_selected = st.selectbox(
        "Choose Benchmark Metric to Visualize",
        options=list(benchmark_metrics.keys()),
        format_func=lambda x: benchmark_metrics[x]
    )
    
    # Render Bar Chart
    # Highlight the selected sector on the bar chart by giving it a different color scale or just plotting standard bars
    # Let's sort medians for better visual hierarchy
    df_medians_sorted = sector_medians.sort_values(by=metric_selected, ascending=True)
    
    # Plotly bar chart
    fig_bar = px.bar(
        df_medians_sorted,
        x=metric_selected,
        y='broad_sector',
        orientation='h',
        labels={
            metric_selected: benchmark_metrics[metric_selected],
            'broad_sector': 'Sector'
        },
        color=metric_selected,
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=10, l=10, r=10),
        coloraxis_showscale=False,
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
