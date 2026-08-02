import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import apply_custom_style, get_merged_data

# Set page config
st.set_page_config(page_title="Nifty 100 Analytics - Screener", layout="wide")

apply_custom_style()

st.title("🔍 Stock Screener")

# Initialize slider session states if not present
slider_defaults = {
    'roe_min': 0.0,
    'de_max': 3.0,
    'fcf_min': -100.0,
    'rev_cagr': -10.0,
    'pat_cagr': -10.0,
    'opm_min': 0.0,
    'pe_max': 100.0,
    'pb_max': 20.0,
    'div_yield': 0.0,
    'icr_min': 0.0
}

for key, val in slider_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Callback for preset buttons
def apply_preset(preset_name):
    # Set to defaults first
    for key, val in slider_defaults.items():
        st.session_state[key] = val
        
    if preset_name == "Quality":
        st.session_state['roe_min'] = 15.0
        st.session_state['de_max'] = 1.0
        st.session_state['fcf_min'] = 0.0
        st.session_state['rev_cagr'] = 10.0
    elif preset_name == "Value":
        st.session_state['pe_max'] = 20.0
        st.session_state['pb_max'] = 3.0
        st.session_state['de_max'] = 2.0
        st.session_state['div_yield'] = 1.0
    elif preset_name == "Growth":
        st.session_state['pat_cagr'] = 20.0
        st.session_state['rev_cagr'] = 15.0
        st.session_state['de_max'] = 2.0
    elif preset_name == "Dividend":
        st.session_state['div_yield'] = 2.0
        st.session_state['fcf_min'] = 0.0
    elif preset_name == "Debt-Free":
        st.session_state['de_max'] = 0.0
        st.session_state['roe_min'] = 12.0
    elif preset_name == "Turnaround":
        st.session_state['rev_cagr'] = 10.0
        st.session_state['fcf_min'] = 0.0
        st.session_state['de_max'] = 1.0

# 1. Preset Buttons at the top
st.subheader("Presets")
btn_cols = st.columns(6)
presets = ["Quality", "Value", "Growth", "Dividend", "Debt-Free", "Turnaround"]

for col, name in zip(btn_cols, presets):
    with col:
        # Use key to avoid duplicate buttons, call callbacks
        st.button(name, key=f"btn_{name.lower()}", on_click=apply_preset, args=(name,), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. Sidebar Sliders
st.sidebar.markdown("### Screener Filters")

roe_min_val = st.sidebar.slider("ROE Min (%)", -50.0, 50.0, key='roe_min', step=1.0)
de_max_val = st.sidebar.slider("D/E Max", 0.0, 5.0, key='de_max', step=0.1)
fcf_min_val = st.sidebar.slider("FCF Min (Cr)", -1000.0, 5000.0, key='fcf_min', step=50.0)
rev_cagr_val = st.sidebar.slider("Revenue CAGR 5yr Min (%)", -30.0, 100.0, key='rev_cagr', step=1.0)
pat_cagr_val = st.sidebar.slider("PAT CAGR 5yr Min (%)", -30.0, 100.0, key='pat_cagr', step=1.0)
opm_min_val = st.sidebar.slider("OPM Min (%)", -20.0, 100.0, key='opm_min', step=1.0)
pe_max_val = st.sidebar.slider("P/E Max", 0.0, 200.0, key='pe_max', step=1.0)
pb_max_val = st.sidebar.slider("P/B Max", 0.0, 50.0, key='pb_max', step=0.5)
div_yield_val = st.sidebar.slider("Dividend Yield Min (%)", 0.0, 10.0, key='div_yield', step=0.1)
icr_min_val = st.sidebar.slider("Interest Coverage Min", 0.0, 100.0, key='icr_min', step=1.0)

# Fetch latest year data (2024)
df = get_merged_data(2024)

if df.empty:
    st.error("No data loaded. Please make sure database is populated.")
else:
    # 3. Apply Sliders logic to DataFrame
    filtered = df.copy()
    
    # Track infinite ICR (Debt Free) as high coverage
    filtered['interest_coverage_computed'] = np.where(
        filtered['icr_label'] == 'Debt Free', 
        1000.0, 
        filtered['interest_coverage']
    )
    
    # Filter operations (using safe checks)
    filtered = filtered[
        (filtered['return_on_equity_pct'].fillna(-999) >= roe_min_val) &
        # Financials sector is excluded from D/E max filter
        ((filtered['debt_to_equity'].fillna(999) <= de_max_val) | (filtered['broad_sector'] == 'Financials')) &
        (filtered['free_cash_flow_cr'].fillna(-99999) >= fcf_min_val) &
        (filtered['revenue_cagr_5yr'].fillna(-999) >= rev_cagr_val) &
        (filtered['pat_cagr_5yr'].fillna(-999) >= pat_cagr_val) &
        (filtered['operating_profit_margin_pct'].fillna(-999) >= opm_min_val) &
        (filtered['pe_ratio'].fillna(999) <= pe_max_val) &
        (filtered['pb_ratio'].fillna(999) <= pb_max_val) &
        (filtered['dividend_yield_pct'].fillna(-999) >= div_yield_val) &
        (filtered['interest_coverage_computed'].fillna(-999) >= icr_min_val)
    ]
    
    # Sort results by composite quality score
    filtered = filtered.sort_values(by='composite_quality_score', ascending=False)
    
    # Count Label
    st.markdown(f"#### 📊 **{len(filtered)}** companies match your filters")
    
    if filtered.empty:
        st.info("No companies match the current filter criteria. Adjust the sliders in the sidebar.")
    else:
        # 4. Results Table Columns formatting
        filtered['Composite Score'] = filtered['composite_quality_score'].round(2)
        filtered['ROE %'] = filtered['return_on_equity_pct'].round(2)
        filtered['D/E'] = filtered['debt_to_equity'].round(2)
        filtered['FCF (Cr)'] = filtered['free_cash_flow_cr'].round(2)
        filtered['Rev CAGR 5y %'] = filtered['revenue_cagr_5yr'].round(2)
        filtered['PAT CAGR 5y %'] = filtered['pat_cagr_5yr'].round(2)
        filtered['OPM %'] = filtered['operating_profit_margin_pct'].round(2)
        filtered['P/E'] = filtered['pe_ratio'].round(2)
        filtered['P/B'] = filtered['pb_ratio'].round(2)
        filtered['Div Yield %'] = filtered['dividend_yield_pct'].round(2)
        filtered['ICR'] = filtered['interest_coverage'].apply(lambda x: "Debt Free" if pd.isna(x) else round(x, 2))
        
        display_cols = [
            'company_id', 'company_name', 'broad_sector', 'Composite Score',
            'ROE %', 'D/E', 'FCF (Cr)', 'Rev CAGR 5y %', 'PAT CAGR 5y %',
            'OPM %', 'P/E', 'P/B', 'Div Yield %', 'ICR'
        ]
        
        st.dataframe(
            filtered[display_cols].rename(columns={
                'company_id': 'Ticker',
                'company_name': 'Company Name',
                'broad_sector': 'Sector'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # 5. CSV download button
        csv_data = filtered[display_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_data,
            file_name="screener_results.csv",
            mime="text/csv",
            use_container_width=False
        )
