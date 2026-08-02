import streamlit as st
import os
import sys

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db import apply_custom_style, get_companies, get_sectors

# Set page config as the very first Streamlit command
st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom visual stylesheet
apply_custom_style()

# Title with gradient effect
st.markdown("""
    <h1 style='text-align: center; color: #00e5ff; font-size: 3rem; margin-bottom: 5px;'>
        Nifty 100 Analytics
    </h1>
    <p style='text-align: center; color: #b0bec5; font-size: 1.2rem; margin-bottom: 40px;'>
        Comprehensive Financial Intelligence & Valuation Platform
    </p>
""", unsafe_allow_html=True)

# Grid Layout for Overview Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Core Focus</div>
            <div class="kpi-value">92 Companies</div>
            <p style='color: #b0bec5; margin-top: 10px; font-size: 0.9rem;'>
                In-depth financial tracking for key Nifty 100 constituents.
            </p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Metrics Evaluated</div>
            <div class="kpi-value">10 Years</div>
            <p style='color: #b0bec5; margin-top: 10px; font-size: 0.9rem;'>
                Historical profit and loss, balance sheet, and cash flow trends.
            </p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Analysis Features</div>
            <div class="kpi-value">8 Screens</div>
            <p style='color: #b0bec5; margin-top: 10px; font-size: 0.9rem;'>
                Screeners, peer groups, trend overlays, and capital maps.
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border: 0.5px solid rgba(255,255,255,0.1); margin: 40px 0;'>", unsafe_allow_html=True)

# Navigation Helper Section
st.subheader("Platform Navigator")
st.markdown("Use the **sidebar** to navigate to any of the following 8 specialized screens:")

nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    st.markdown("""
        - 🏠 **01 Home Screen**: Aggregate market stats, sector breakdown, and quality leaderboard.
        - 📊 **02 Company Profile**: Full 10-year financials, charts, and automated pros/cons badges.
        - 🔍 **03 Screener Screen**: 10 metric filters, preset buttons, and live results CSV exporter.
        - ⚖️ **04 Peer Comparison**: Radar charts and side-by-side benchmarking within 11 groups.
    """)

with nav_col2:
    st.markdown("""
        - 📈 **05 Trend Analysis**: Multi-metric overlays with automated YoY growth annotations.
        - 🍩 **06 Sector Analysis**: Broad sector interactive bubble charts and median bars.
        - 🗺️ **07 Capital Allocation**: Dynamic treemap of the 8 capital allocation cash patterns.
        - 📁 **08 Annual Reports**: Search and download BSE report PDFs with automated 404 validation.
    """)

st.info("💡 **Tip**: Select **01 Home** in the sidebar to get started with the market overview!")
