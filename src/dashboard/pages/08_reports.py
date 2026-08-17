import os
import sys

import pandas as pd
import requests
import streamlit as st

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import apply_custom_style, get_companies, get_connection

# Set page config
st.set_page_config(page_title="Nifty 100 Analytics - Annual Reports", layout="wide")

apply_custom_style()

st.title("📁 Annual Reports")


# Cached function to check link validity via HEAD request to prevent rendering delays
@st.cache_data(ttl=3600)
def check_pdf_link_exists(url):
    """Sends a fast HTTP request to check if the PDF exists (status 200)."""
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return False
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Use HEAD request for speed, allow redirects
        res = requests.head(url, headers=headers, timeout=2.0, allow_redirects=True)
        if res.status_code == 200:
            return True
        # If HEAD fails or returns method not allowed (some servers block HEAD), retry with a stream GET
        if res.status_code in [403, 405]:
            res_get = requests.get(url, headers=headers, timeout=2.0, stream=True)
            return res_get.status_code == 200
        return False
    except Exception:
        return False


# Load companies
df_companies = get_companies()

if df_companies.empty:
    st.error("No company data found in database.")
else:
    company_options = [
        f"{row['id']} - {row['company_name']}" for _, row in df_companies.iterrows()
    ]
    selected_option = st.selectbox("Search Company by Name or Ticker", company_options)

    if selected_option:
        ticker = selected_option.split(" - ")[0].strip()
        co_name = selected_option.split(" - ")[1].strip()

        # Query documents table for selected company
        conn = get_connection()
        query = "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC"
        df_docs = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()

        st.subheader(f"Available Annual Reports for {co_name} ({ticker})")

        if df_docs.empty:
            st.info("No annual reports registered in the database for this company.")
        else:
            # We want to render a clean, beautifully formatted grid of reports
            # Loop and print
            for _, row in df_docs.iterrows():
                year = row["year"]
                url = row["annual_report"]

                # Check status
                url_is_valid = check_pdf_link_exists(url)

                cols = st.columns([1, 4, 2])
                with cols[0]:
                    st.markdown(f"**FY {year}**")

                with cols[1]:
                    if url:
                        st.markdown(
                            f"<code style='color: #00e5ff; font-size: 0.85rem;'>{url}</code>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write("No Link")

                with cols[2]:
                    if not url:
                        st.markdown(
                            '<span style="background-color: rgba(239, 83, 80, 0.2); color: #ef5350; padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(239, 83, 80, 0.4); font-size: 0.85rem; font-weight: 600;">Report unavailable</span>',
                            unsafe_allow_html=True,
                        )
                    elif url_is_valid:
                        st.markdown(
                            f'<a href="{url}" target="_blank" style="background-color: rgba(0, 229, 255, 0.2); color: #00e5ff; padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(0, 229, 255, 0.4); font-size: 0.9rem; font-weight: 600; text-decoration: none; text-align: center; display: inline-block;">📥 Download Report</a>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<span style="background-color: rgba(239, 83, 80, 0.2); color: #ef5350; padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(239, 83, 80, 0.4); font-size: 0.85rem; font-weight: 600;">Report unavailable</span>',
                            unsafe_allow_html=True,
                        )

                st.markdown(
                    "<hr style='border: 0.5px solid rgba(255,255,255,0.05); margin: 10px 0;'>",
                    unsafe_allow_html=True,
                )
