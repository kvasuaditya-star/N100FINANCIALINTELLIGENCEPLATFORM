import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "nifty100.db")
if not os.path.exists(DB_PATH):
    DB_PATH = "data/nifty100.db"

# Add project root to sys.path to allow importing from src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@st.cache_data(ttl=600)
def get_companies():
    """Returns all companies joined with their sector information."""
    conn = get_connection()
    query = """
        SELECT c.*, s.broad_sector, s.sub_sector, s.index_weight_pct, s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        ORDER BY c.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """Returns financial ratios for a given company. Filters by year if provided."""
    conn = get_connection()
    if year:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ? ORDER BY year"
        df = pd.read_sql_query(query, conn, params=(ticker, str(year)))
    else:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker):
    """Returns P&L statement for a company, sorted by year."""
    conn = get_connection()
    query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_bs(ticker):
    """Returns balance sheet for a company, sorted by year."""
    conn = get_connection()
    query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker):
    """Returns cash flow statement for a company, sorted by year."""
    conn = get_connection()
    query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors():
    """Returns unique sectors and company counts."""
    conn = get_connection()
    query = """
        SELECT broad_sector, sub_sector, COUNT(company_id) as company_count
        FROM sectors
        GROUP BY broad_sector, sub_sector
        ORDER BY broad_sector, sub_sector
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name):
    """Returns all companies and their ratios inside a specific peer group."""
    conn = get_connection()
    query = """
        SELECT pg.peer_group_name, pg.is_benchmark, c.company_name, fr.*
        FROM peer_groups pg
        JOIN companies c ON pg.company_id = c.id
        LEFT JOIN financial_ratios fr ON pg.company_id = fr.company_id
        WHERE pg.peer_group_name = ?
        AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = pg.company_id)
    """
    df = pd.read_sql_query(query, conn, params=(group_name,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """Returns valuation multiples and market cap history for a company."""
    conn = get_connection()
    query = "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_merged_data(year):
    """Fetches merged financial data for all companies in a single year and computes composite scores."""
    conn = get_connection()
    query = """
        SELECT 
            fr.*,
            c.company_name, c.roce_percentage as roce, c.about_company, c.website, c.nse_profile, c.bse_profile,
            s.broad_sector, s.sub_sector, s.index_weight_pct, s.market_cap_category,
            mc.pe_ratio, mc.pb_ratio, mc.dividend_yield_pct, mc.market_cap_crore, mc.enterprise_value_crore, mc.ev_ebitda,
            pl.sales, pl.net_profit, pl.operating_profit, pl.other_income, pl.interest as pl_interest, pl.expenses,
            cf.operating_activity, cf.investing_activity, cf.financing_activity
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND mc.year = ?
        LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND pl.year = fr.year
        LEFT JOIN cashflow cf ON fr.company_id = cf.company_id AND cf.year = fr.year
        WHERE fr.year LIKE ?
    """
    year_str = str(year)
    df = pd.read_sql_query(query, conn, params=(int(year_str), f"{year_str}-%"))
    conn.close()
    
    if not df.empty:
        # Load cashflow for FCF CAGR calculations in compute_composite_score
        conn = get_connection()
        df_cf = pd.read_sql_query("SELECT company_id, year, operating_activity, investing_activity FROM cashflow", conn)
        conn.close()
        
        # Import the scoring engine
        from src.screener.engine import compute_composite_score
        df = compute_composite_score(df, df_cf)
        
    return df

def apply_custom_style():
    """Injects high-end, premium styling (dark mode, glassmorphism elements, clean typography)."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        /* Font styling */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Modern Cards for KPIs */
        .kpi-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            margin: 10px 0;
            transition: transform 0.2s ease-in-out, border-color 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 229, 255, 0.4);
        }
        .kpi-title {
            font-size: 0.9rem;
            color: #b0bec5;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #00e5ff;
        }
        
        /* Headers styling */
        h1, h2, h3 {
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }
        
        /* Badges */
        .pro-badge {
            background-color: rgba(38, 166, 154, 0.2);
            color: #26a69a;
            padding: 6px 12px;
            border-radius: 20px;
            border: 1px solid rgba(38, 166, 154, 0.4);
            display: inline-block;
            margin: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .con-badge {
            background-color: rgba(239, 83, 80, 0.2);
            color: #ef5350;
            padding: 6px 12px;
            border-radius: 20px;
            border: 1px solid rgba(239, 83, 80, 0.4);
            display: inline-block;
            margin: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        /* Sidebar layout modifications */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
