import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import streamlit as st

# Setup dynamic paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"

# Configure Page Layout & Styling
st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling (Glassmorphism, curated dark palettes, clean fonts)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #0d0e15;
        color: #ffffff;
    }
    
    .stApp {
        background-color: #0d0e15;
    }
    
    h1, h2, h3 {
        color: #00b4d8 !important;
        font-weight: 700 !important;
    }
    
    .card {
        background-color: #161824;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        border: 1px solid #23273a;
        margin-bottom: 20px;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #00b4d8;
    }
    
    .metric-label {
        font-size: 14px;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to connect to SQLite
def get_db_connection():
    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}. Please run the ETL pipeline first.")
        st.stop()
    return sqlite3.connect(DB_PATH)

# Title & Sidebar
st.sidebar.markdown("<h2 style='text-align: center; color: #00b4d8;'>BLUESTOCK MF</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #a0aec0; font-size: 12px;'>Capstone Analytics & Optimization Engine</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate Dashboard",
    ["📊 Executive Scorecard", "📈 NAV & Benchmark Comparative", "💼 Sector Concentration & HHI", "⚙️ Financial Engineering"]
)

# ----------------- PAGE 1: EXECUTIVE SCORECARD -----------------
if page == "📊 Executive Scorecard":
    st.markdown("<h1>Executive Performance Scorecard</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    conn = get_db_connection()
    # Load fact_performance
    query = """
        SELECT fp.amfi_code, fp.scheme_name, fp.fund_house, fp.category, 
               fp.return_1yr_pct, fp.return_3yr_pct, fp.return_5yr_pct, 
               fp.sharpe_ratio, fp.sortino_ratio, fp.beta, fp.aum_crore, fp.risk_grade
        FROM fact_performance fp
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 2 functioning slicers on Page 1 (Fund House & Category)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fund_houses = ["All"] + sorted(list(df['fund_house'].unique()))
        selected_fh = st.selectbox("Filter by Fund House", fund_houses)
        
    with col_f2:
        categories = ["All"] + sorted(list(df['category'].unique()))
        selected_cat = st.selectbox("Filter by Category", categories)
        
    # Apply filters
    filtered_df = df.copy()
    if selected_fh != "All":
        filtered_df = filtered_df[filtered_df['fund_house'] == selected_fh]
    if selected_cat != "All":
        filtered_df = filtered_df[filtered_df['category'] == selected_cat]
        
    # Headline KPIs
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">Total Schemes</div>
            <div class="metric-value">{len(filtered_df)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_k2:
        total_aum = filtered_df['aum_crore'].sum()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">Total Category AUM</div>
            <div class="metric-value">₹{total_aum:,.2f} Cr</div>
        </div>
        """, unsafe_allow_html=True)
    with col_k3:
        avg_sharpe = filtered_df['sharpe_ratio'].mean()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">Average Sharpe Ratio</div>
            <div class="metric-value">{avg_sharpe:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_k4:
        avg_3yr = filtered_df['return_3yr_pct'].mean()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">Average 3Yr CAGR</div>
            <div class="metric-value">{avg_3yr:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Performance Plot
    st.markdown("### Top Funds by 3-Year Return")
    top_10 = filtered_df.sort_values('return_3yr_pct', ascending=False).head(10)
    fig = px.bar(
        top_10,
        x='return_3yr_pct',
        y='scheme_name',
        orientation='h',
        color='sharpe_ratio',
        color_continuous_scale='teal',
        labels={'return_3yr_pct': '3-Year Return (CAGR %)', 'scheme_name': 'Scheme Name', 'sharpe_ratio': 'Sharpe Ratio'},
        title="Top 10 Schemes Return vs Risk Profile"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Data Table
    st.markdown("### Comprehensive Rankings")
    st.dataframe(
        filtered_df[['scheme_name', 'category', 'return_3yr_pct', 'return_5yr_pct', 'sharpe_ratio', 'beta', 'risk_grade', 'aum_crore']]
        .rename(columns={
            'scheme_name': 'Scheme Name',
            'category': 'Category',
            'return_3yr_pct': '3Yr CAGR (%)',
            'return_5yr_pct': '5Yr CAGR (%)',
            'sharpe_ratio': 'Sharpe Ratio',
            'beta': 'CAPM Beta',
            'risk_grade': 'Risk Grade',
            'aum_crore': 'Scheme AUM (Cr)'
        }),
        use_container_width=True,
        hide_index=True
    )

# ----------------- PAGE 2: NAV & BENCHMARK COMPARATIVE -----------------
elif page == "📈 NAV & Benchmark Comparative":
    st.markdown("<h1>NAV & Benchmark Visualizer</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    conn = get_db_connection()
    # Get master codes
    funds_df = pd.read_sql_query("SELECT amfi_code, scheme_name, benchmark FROM dim_fund", conn)
    
    # 2 functioning slicers on Page 2 (Scheme Selector & Date Range Filter)
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        selected_scheme = st.selectbox("Select Scheme to Analyse", funds_df['scheme_name'].unique())
    
    code = funds_df[funds_df['scheme_name'] == selected_scheme]['amfi_code'].iloc[0]
    bench_name = funds_df[funds_df['scheme_name'] == selected_scheme]['benchmark'].iloc[0]
    
    # Load NAV & Benchmark histories
    nav_history = pd.read_sql_query(
        "SELECT date, nav FROM fact_nav WHERE amfi_code = ? ORDER BY date", conn, params=(str(code),)
    )
    nav_history['date'] = pd.to_datetime(nav_history['date'])
    
    # Map raw benchmark name to file index names
    # e.g., 'NIFTY 100 TRI' maps to 'NIFTY100' or similar
    index_map = "NIFTY50"
    if "100" in str(bench_name).upper():
        index_map = "NIFTY100"
    elif "MID" in str(bench_name).upper():
        index_map = "NIFTY_MIDCAP_150"
    elif "SMALL" in str(bench_name).upper():
        index_map = "BSE_SMALLCAP_250"
    elif "GILT" in str(bench_name).upper():
        index_map = "CRISIL_DYNAMIC_GILT"
        
    bench_history = pd.read_sql_query(
        "SELECT date, close_value FROM benchmark_indices WHERE index_name = ? ORDER BY date", conn, params=(index_map,)
    )
    bench_history['date'] = pd.to_datetime(bench_history['date'])
    
    conn.close()
    
    # Join on Date
    merged = pd.merge(nav_history, bench_history, on='date', how='inner')
    
    with col_f2:
        min_date = merged['date'].min().to_pydatetime()
        max_date = merged['date'].max().to_pydatetime()
        date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        
    if len(date_range) == 2:
        start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        merged = merged[(merged['date'] >= start_dt) & (merged['date'] <= end_dt)]
        
    # Compute relative growth (indexing to 100 at start of series)
    if not merged.empty:
        merged['fund_indexed'] = (merged['nav'] / merged['nav'].iloc[0]) * 100
        merged['bench_indexed'] = (merged['close_value'] / merged['close_value'].iloc[0]) * 100
        
        # Plot Plotly Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=merged['date'], y=merged['fund_indexed'],
            mode='lines', name=selected_scheme,
            line=dict(color='#00b4d8', width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=merged['date'], y=merged['bench_indexed'],
            mode='lines', name=f"{bench_name} (Benchmark)",
            line=dict(color='#7209b7', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f"Relative Performance Growth: Fund vs Benchmark ({bench_name})",
            xaxis_title="Date",
            yaxis_title="Indexed Growth (Base 100)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for selected date range.")

# ----------------- PAGE 3: SECTOR CONCENTRATION & HHI -----------------
elif page == "💼 Sector Concentration & HHI":
    st.markdown("<h1>Portfolio Holdings & Sector Concentration</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    conn = get_db_connection()
    # Load equity portfolio holdings
    holdings_query = """
        SELECT ph.amfi_code, df.scheme_name, ph.stock_name, ph.sector, ph.weight_pct, ph.market_value_cr
        FROM portfolio_holdings ph
        JOIN dim_fund df ON ph.amfi_code = df.amfi_code
    """
    holdings_df = pd.read_sql_query(holdings_query, conn)
    
    # Load pre-computed sector HHI concentrations
    hhi_df = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    conn.close()
    
    # 2 functioning slicers on Page 3 (Scheme Name & Sector Slicers)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_scheme = st.selectbox("Select Equity Scheme", holdings_df['scheme_name'].unique())
        
    scheme_holdings = holdings_df[holdings_df['scheme_name'] == selected_scheme]
    
    with col_f2:
        sectors = ["All"] + sorted(list(scheme_holdings['sector'].unique()))
        selected_sec = st.selectbox("Select Holding Sector Filter", sectors)
        
    filtered_holdings = scheme_holdings.copy()
    if selected_sec != "All":
        filtered_holdings = filtered_holdings[filtered_holdings['sector'] == selected_sec]
        
    # Herfindahl-Hirschman Concentration Index metrics
    # HHI = sum(Sector_Weights_pct ** 2)
    sector_weights = scheme_holdings.groupby('sector')['weight_pct'].sum()
    hhi_score = (sector_weights ** 2).sum()
    
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">HHI Concentration Score</div>
            <div class="metric-value">{hhi_score:,.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_k2:
        top_sector = sector_weights.idxmax()
        top_sec_wt = sector_weights.max()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">Top Sector ({top_sector})</div>
            <div class="metric-value">{top_sec_wt:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_k3:
        num_stocks = len(scheme_holdings)
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">Total Stocks Held</div>
            <div class="metric-value">{num_stocks}</div>
        </div>
        """, unsafe_allow_html=True)
        
    col_c1, col_c2 = st.columns([1, 1])
    
    with col_c1:
        # Donut Chart for Sectors
        sec_df = sector_weights.reset_index()
        fig_donut = px.pie(
            sec_df, values='weight_pct', names='sector', hole=0.4,
            title='Sector Weights Distribution',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_donut.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            height=400
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with col_c2:
        # Holdings List Treemap
        fig_tree = px.treemap(
            scheme_holdings, path=['sector', 'stock_name'], values='weight_pct',
            title='Portfolio Treemap of Stock Holdings',
            color='weight_pct', color_continuous_scale='Viridis'
        )
        fig_tree.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            height=400
        )
        st.plotly_chart(fig_tree, use_container_width=True)
        
    st.markdown("### Stock-level Asset Weights")
    st.dataframe(
        filtered_holdings[['stock_name', 'sector', 'weight_pct', 'market_value_cr']]
        .rename(columns={
            'stock_name': 'Stock Name',
            'sector': 'Sector',
            'weight_pct': 'Weight (%)',
            'market_value_cr': 'Market Value (Cr)'
        }),
        use_container_width=True,
        hide_index=True
    )

# ----------------- PAGE 4: ADVANCED FINANCIAL ENGINEERING -----------------
else:
    st.markdown("<h1>Financial Engineering & Recommender Engine</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Tab layout
    tab_rec, tab_sim, tab_opt = st.tabs(["🎯 Sharpe Recommender", "🎲 Monte Carlo Simulator", "📈 Efficient Frontier"])
    
    # TAB 1: Fund Recommender
    with tab_rec:
        st.write("#### Recommender engine based on Sharpe Ratio & Risk Appetite")
        
        # Slicer: Risk Appetite selector
        risk_appetite = st.selectbox("Select Your Risk Appetite", ["Low", "Moderate", "High"])
        
        conn = get_db_connection()
        perf_df = pd.read_sql_query("SELECT * FROM fact_performance", conn)
        conn.close()
        
        # Risk appetite mapping
        if risk_appetite == 'Low':
            matched_grades = ['Low']
        elif risk_appetite == 'Moderate':
            matched_grades = ['Moderate', 'Moderately High']
        else:  # High
            matched_grades = ['High', 'Very High']
            
        filtered_recs = perf_df[perf_df['risk_grade'].isin(matched_grades)].copy()
        
        if not filtered_recs.empty:
            top_3 = filtered_recs.sort_values(by='sharpe_ratio', ascending=False).head(3)
            
            st.markdown(f"**Top Recommended Funds for {risk_appetite} Risk Profile:**")
            
            for idx, row in enumerate(top_3.itertuples(), 1):
                st.markdown(f"""
                <div class="card">
                    <h4>Rank {idx}: {row.scheme_name}</h4>
                    <p><b>Category:</b> {row.category} | <b>Plan:</b> {row.plan} | <b>Risk Grade:</b> {row.risk_grade}</p>
                    <p><b>3Yr CAGR:</b> {row.return_3yr_pct:.2f}% | <b>Sharpe Ratio:</b> {row.sharpe_ratio:.2f} | <b>AUM:</b> ₹{row.aum_crore:.2f} Cr</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No matching funds found in this database.")

    # TAB 2: Monte Carlo Simulation
    with tab_sim:
        st.write("#### 5-Year Geometric Brownian Motion NAV Projections (Bonus B3)")
        
        conn = get_db_connection()
        funds_list = pd.read_sql_query("SELECT amfi_code, scheme_name FROM dim_fund", conn)
        selected_sim_scheme = st.selectbox("Select Scheme to Simulate", funds_list['scheme_name'].unique())
        
        sim_code = funds_list[funds_list['scheme_name'] == selected_sim_scheme]['amfi_code'].iloc[0]
        
        nav_history = pd.read_sql_query(
            "SELECT date, nav FROM fact_nav WHERE amfi_code = ? ORDER BY date", conn, params=(str(sim_code),)
        )
        conn.close()
        
        if not nav_history.empty:
            nav_history['date'] = pd.to_datetime(nav_history['date'])
            returns = nav_history['nav'].pct_change().dropna()
            
            # Slicers: Sim runs & Drift tuning
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                n_sims = st.slider("Number of Simulations", min_value=100, max_value=2000, value=500, step=100)
            with col_s2:
                confidence = st.selectbox("Projected Bands Coverage", [80, 90, 95])
                
            # Drift & Vol
            dt = 1 / 252
            mu = returns.mean() * 252
            sigma = returns.std() * np.sqrt(252)
            S0 = nav_history['nav'].iloc[-1]
            
            n_days = 5 * 252  # 5 years
            
            # Run GBM simulations
            np.random.seed(42)
            sim_paths = np.zeros((n_days, n_sims))
            sim_paths[0, :] = S0
            for t in range(1, n_days):
                z = np.random.normal(0, 1, n_sims)
                sim_paths[t, :] = sim_paths[t-1, :] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
                
            median_path = np.median(sim_paths, axis=1)
            lower_pct = (100 - confidence) / 2
            upper_pct = 100 - lower_pct
            
            lower_band = np.percentile(sim_paths, lower_pct, axis=1)
            upper_band = np.percentile(sim_paths, upper_pct, axis=1)
            
            # Plot
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                y=median_path, mode='lines', name='Median Projection', line=dict(color='#00b4d8', width=3)
            ))
            fig_sim.add_trace(go.Scatter(
                y=upper_band, mode='lines', name='Upper Bound', line=dict(color='#2a9d8f', width=1, dash='dot'), showlegend=False
            ))
            fig_sim.add_trace(go.Scatter(
                y=lower_band, mode='lines', name='Lower Bound', fill='tonexty', fillcolor='rgba(0,180,216,0.15)',
                line=dict(color='#e76f51', width=1, dash='dot')
            ))
            fig_sim.update_layout(
                title=f"{selected_sim_scheme} 5-Year NAV Path Projections (Current NAV: ₹{S0:.2f})",
                xaxis_title="Trading Days",
                yaxis_title="NAV (INR)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                height=450
            )
            st.plotly_chart(fig_sim, use_container_width=True)
            
            st.info(f"Summary metrics: Initial NAV = ₹{S0:.2f} | Median projected NAV in 5 years = ₹{median_path[-1]:.2f}")
        else:
            st.warning("Insufficient history for this fund.")

    # TAB 3: Markowitz Optimization
    with tab_opt:
        st.write("#### Markowitz Efficient Frontier: Risk-Return Optimization (Bonus B4)")
        
        target_codes = [119551, 125497, 120503, 118632, 120841] # SBI, HDFC, ICICI, Nippon, Kotak
        conn = get_db_connection()
        funds_mapping = pd.read_sql_query(
            "SELECT amfi_code, scheme_name FROM dim_fund WHERE amfi_code IN (119551, 125497, 120503, 118632, 120841)", conn
        )
        nav_data = pd.read_sql_query(
            "SELECT amfi_code, date, nav FROM fact_nav WHERE amfi_code IN ('119551', '125497', '120503', '118632', '120841') ORDER BY date", conn
        )
        conn.close()
        
        if len(nav_data) > 100:
            pivot_nav = nav_data.pivot(index='date', columns='amfi_code', values='nav').dropna()
            returns = pivot_nav.pct_change().dropna()
            
            # Slicer: risk-Free Rate tuning & Portfolio simulations size
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                opt_rf = st.slider("Risk-Free Rate (Annual %)", min_value=0.0, max_value=12.0, value=6.0, step=0.5) / 100
            with col_o2:
                sim_count = st.slider("Efficient Frontier Scenarios", min_value=1000, max_value=10000, value=3000, step=1000)
                
            ann_ret = returns.mean() * 252
            cov_matrix = returns.cov() * 252
            num_assets = len(ann_ret)
            
            # Simulation
            port_ret = []
            port_vol = []
            port_sharpe = []
            all_weights = []
            
            np.random.seed(42)
            for _ in range(sim_count):
                w = np.random.random(num_assets)
                w /= np.sum(w)
                ret = np.sum(w * ann_ret)
                vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                sharpe = (ret - opt_rf) / vol if vol > 0 else 0
                port_ret.append(ret)
                port_vol.append(vol)
                port_sharpe.append(sharpe)
                all_weights.append(w)
                
            # Convert
            port_ret = np.array(port_ret)
            port_vol = np.array(port_vol)
            port_sharpe = np.array(port_sharpe)
            
            max_sharpe_idx = port_sharpe.argmax()
            best_vol = port_vol[max_sharpe_idx]
            best_ret = port_ret[max_sharpe_idx]
            best_weights = all_weights[max_sharpe_idx]
            
            # Plotly
            fig_opt = go.Figure()
            fig_opt.add_trace(go.Scatter(
                x=port_vol, y=port_ret, mode='markers',
                marker=dict(color=port_sharpe, colorscale='Plasma', showscale=True, colorbar=dict(title="Sharpe")),
                name='Portfolios'
            ))
            fig_opt.add_trace(go.Scatter(
                x=[best_vol], y=[best_ret], mode='markers',
                marker=dict(color='red', size=15, symbol='star'),
                name='Max Sharpe Portfolio'
            ))
            
            fig_opt.update_layout(
                title='Efficient Frontier: Simulated Portfolios',
                xaxis_title='Annualised Volatility',
                yaxis_title='Expected Return',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                height=450
            )
            st.plotly_chart(fig_opt, use_container_width=True)
            
            # Display weights
            st.write("##### Max Sharpe Optimal Weights Allocation:")
            cols = st.columns(num_assets)
            for idx, col in enumerate(cols):
                code_name = funds_mapping[funds_mapping['amfi_code'].astype(str) == str(returns.columns[idx])]['scheme_name'].iloc[0]
                col.metric(code_name, f"{best_weights[idx]*100:.1f}%")
        else:
            st.warning("Insufficient database rows to compute Markowitz Efficient Frontier.")
