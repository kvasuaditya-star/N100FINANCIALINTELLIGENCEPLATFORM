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
st.set_page_config(page_title="Nifty 100 Analytics - Capital Allocation Map", layout="wide")

apply_custom_style()

st.title("🗺️ Capital Allocation Map")

# Fetch latest merged data (2024)
df_latest = get_merged_data(2024)

if df_latest.empty:
    st.error("No company cash flow data found.")
else:
    # 1. Classify each company using cashflow_kpis.py logic
    from src.analytics.cashflow_kpis import classify_capital_allocation
    
    patterns = []
    for _, row in df_latest.iterrows():
        cfo = row.get('operating_activity')
        cfi = row.get('investing_activity')
        cff = row.get('financing_activity')
        pat = row.get('net_profit')
        pattern = classify_capital_allocation(cfo, cfi, cff, pat)
        patterns.append(pattern)
        
    df_latest['allocation_pattern'] = patterns
    
    # User option to size by Market Cap or count
    size_option = st.sidebar.selectbox("Size Blocks By", ["Market Cap", "Equal Weight"])
    
    df_latest['size_weight'] = df_latest['market_cap_crore'] if size_option == "Market Cap" else 1.0
    # Handle NaN values for weights
    df_latest['size_weight'] = df_latest['size_weight'].fillna(1.0).apply(lambda x: max(x, 1.0))
    
    st.subheader("Nifty 100 Capital Allocation Treemap")
    st.markdown("""
        *The treemap groups companies into 8 capital allocation patterns based on the signs (+/-) of their cash flow statement lines:*
        * **Shareholder Returns**: Strong cash generator, paying down debt/dividends, high cash generation quality (`CFO > 0, CFI < 0, CFF < 0, CFO/PAT > 1.0`).
        * **Reinvestor**: Cash generator, reinvesting heavily, standard quality (`CFO > 0, CFI < 0, CFF < 0`).
        * **Liquidating Assets**: Asset seller (`CFO > 0, CFI > 0, CFF < 0`).
        * **Distress Signal**: Burning cash, selling assets (`CFO < 0, CFI > 0, CFF > 0`).
        * **Growth Funded by Debt**: Burning cash, investing, borrowing (`CFO < 0, CFI < 0, CFF > 0`).
        * **Cash Accumulator**: Cash collector (`CFO > 0, CFI > 0, CFF > 0`).
        * **Pre-Revenue / Cash Burn**: Burning cash all around (`CFO < 0, CFI < 0, CFF < 0`).
        * **Mixed**: Other mixed cash combinations.
    """)
    
    # 2. Render Plotly Treemap
    fig = px.treemap(
        df_latest,
        path=['allocation_pattern', 'company_id'],
        values='size_weight',
        color='allocation_pattern',
        hover_name='company_name',
        hover_data={
            'market_cap_crore': ':,.1f',
            'operating_activity': ':,.1f',
            'investing_activity': ':,.1f',
            'financing_activity': ':,.1f'
        },
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br><hr style='border: 0.5px solid rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
    
    # 3. Interactive details list based on clicked/selected pattern
    st.subheader("🔍 Inspect Allocation Pattern Constituents")
    
    available_patterns = sorted(df_latest['allocation_pattern'].unique().tolist())
    selected_pattern = st.selectbox("Select Capital Allocation Pattern to view companies:", available_patterns)
    
    df_pattern_list = df_latest[df_latest['allocation_pattern'] == selected_pattern]
    
    st.markdown(f"Found **{len(df_pattern_list)}** companies in the **{selected_pattern}** pattern category:")
    
    if not df_pattern_list.empty:
        # Formatted Columns
        df_pattern_list['Market Cap (Cr)'] = df_pattern_list['market_cap_crore'].apply(lambda x: f"₹{x:,.1f}" if not pd.isna(x) else "N/A")
        df_pattern_list['CFO (Cr)'] = df_pattern_list['operating_activity'].apply(lambda x: f"₹{x:,.1f}" if not pd.isna(x) else "N/A")
        df_pattern_list['CFI (Cr)'] = df_pattern_list['investing_activity'].apply(lambda x: f"₹{x:,.1f}" if not pd.isna(x) else "N/A")
        df_pattern_list['CFF (Cr)'] = df_pattern_list['financing_activity'].apply(lambda x: f"₹{x:,.1f}" if not pd.isna(x) else "N/A")
        df_pattern_list['Net Profit (Cr)'] = df_pattern_list['net_profit'].apply(lambda x: f"₹{x:,.1f}" if not pd.isna(x) else "N/A")
        
        display_cols = [
            'company_id', 'company_name', 'broad_sector', 'Market Cap (Cr)', 
            'CFO (Cr)', 'CFI (Cr)', 'CFF (Cr)', 'Net Profit (Cr)'
        ]
        
        st.dataframe(
            df_pattern_list[display_cols].rename(columns={
                'company_id': 'Ticker',
                'company_name': 'Company Name',
                'broad_sector': 'Sector'
            }),
            use_container_width=True,
            hide_index=True
        )
