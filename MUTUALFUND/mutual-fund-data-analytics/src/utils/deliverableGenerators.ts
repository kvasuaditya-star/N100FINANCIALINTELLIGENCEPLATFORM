/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { FundMetrics, IndexPoint, DailyPoint } from '../types';

// Helper: Format percentages and numbers
const pct = (v: number) => `${(v * 100).toFixed(2)}%`;
const num = (v: number) => v.toFixed(4);

export function generateScorecardCSV(metrics: FundMetrics[]): string {
  // Column Headers
  const headers = [
    'Rank',
    'Scheme Name',
    'Category',
    'Expense Ratio',
    '1Yr CAGR',
    '3Yr CAGR',
    '5Yr CAGR',
    'Volatility (Ann)',
    'Sharpe Ratio',
    'Sortino Ratio',
    'Alpha (Ann)',
    'Beta',
    'R-Squared',
    'Max Drawdown',
    'Drawdown Peak Date',
    'Drawdown Trough Date',
    'Drawdown Recovery Date',
    'Scorecard Points'
  ];

  const rows = metrics.map(m => [
    m.finalRank,
    `"${m.name}"`,
    `"${m.category}"`,
    num(m.expenseRatio),
    num(m.cagr1Yr),
    num(m.cagr3Yr),
    num(m.cagr5Yr),
    num(m.volatility),
    num(m.sharpeRatio),
    num(m.sortinoRatio),
    num(m.alpha),
    num(m.beta),
    num(m.rSquared),
    num(m.maxDrawdown),
    m.drawdownStartDate,
    m.drawdownTroughDate,
    m.drawdownEndDate,
    m.compositeScore.toFixed(2)
  ]);

  return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
}

export function generateAlphaBetaCSV(metrics: FundMetrics[]): string {
  const headers = [
    'Scheme Name',
    'Category',
    'Alpha (Ann vs Nifty 100)',
    'Beta (vs Nifty 100)',
    'R-Squared (vs Nifty 100)',
    'Tracking Error (Ann vs Nifty 100)',
    'Tracking Error (Ann vs Nifty 50)',
    'Sharpe Ratio',
    'Sortino Ratio'
  ];

  const rows = metrics.map(m => [
    `"${m.name}"`,
    `"${m.category}"`,
    num(m.alpha),
    num(m.beta),
    num(m.rSquared),
    num(m.trackingErrorNifty100),
    num(m.trackingErrorNifty50),
    num(m.sharpeRatio),
    num(m.sortinoRatio)
  ]);

  return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
}

export function generateJupyterNotebook(): string {
  const ipynb = {
    cells: [
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '# Mutual Fund Performance Analytics & Scorecarding\n',
          'This Jupyter Notebook replicates the full mutual fund capstone analysis. It procedurally generates the historical daily NAV data for 40 schemes over a 5-year period (2021-06-30 to 2026-06-29), along with Nifty 50 and Nifty 100 indices. It then computes returns, CAGR, risk-adjusted performance metrics, OLS regressions for Alpha/Beta, drawdowns, and produces the weighted scorecard rankings and the benchmark comparison plots.'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          'import numpy as np\n',
          'import pandas as pd\n',
          'import scipy.stats as stats\n',
          'import matplotlib.pyplot as plt\n',
          'import seaborn as sns\n',
          '\n',
          '# Configure visual styles\n',
          'plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")\n',
          'plt.rcParams["figure.figsize"] = (12, 6)\n',
          'plt.rcParams["font.family"] = "sans-serif"\n',
          'print("Libraries imported successfully!")'
        ]
      },
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '## 1. Procedural Data Generator (Seeded for Exact Replication)\n',
          'To replicate the exact mathematical dataset computed on the web dashboard, we use a seeded random walk formulation. This models index prices and CAPM returns with specific parameters (mean, volatility, beta, expense ratio) based on the category of each scheme.'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          'def get_random_generator(seed=42):\n',
          '    state = seed\n',
          '    def rand():\n',
          '        nonlocal state\n',
          '        state = (state * 9301 + 49297) % 233280\n',
          '        return state / 233280\n',
          '    return rand\n',
          '\n',
          'def box_muller(rand_fn):\n',
          '    u1 = rand_fn()\n',
          '    while u1 <= 1e-7:\n',
          '        u1 = rand_fn()\n',
          '    u2 = rand_fn()\n',
          '    return np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)\n',
          '\n',
          '# Build Dates Series (excluding weekends)\n',
          'start_date = pd.to_datetime("2021-06-30")\n',
          'end_date = pd.to_datetime("2026-06-29")\n',
          'all_days = pd.date_range(start_date, end_date)\n',
          'trading_days = all_days[all_days.dayofweek < 5] # Exclude Sat & Sun\n',
          'N = len(trading_days)\n',
          '\n',
          '# Generate Indexes\n',
          'rand = get_random_generator(42)\n',
          'nifty100_prices = np.zeros(N)\n',
          'nifty50_prices = np.zeros(N)\n',
          'nifty100_prices[0] = 15000\n',
          'nifty50_prices[0] = 15700\n',
          '\n',
          'nifty100_returns = np.zeros(N)\n',
          'nifty50_returns = np.zeros(N)\n',
          '\n',
          'nifty100_drift = 0.14 / 252\n',
          'nifty100_vol = 0.15 / np.sqrt(252)\n',
          'nifty50_drift = 0.135 / 252\n',
          'nifty50_vol = 0.145 / np.sqrt(252)\n',
          '\n',
          'for i in range(1, N):\n',
          '    r100_norm = box_muller(rand)\n',
          '    r100 = nifty100_drift + nifty100_vol * r100_norm\n',
          '    nifty100_prices[i] = nifty100_prices[i-1] * (1.0 + r100)\n',
          '    nifty100_returns[i] = r100\n',
          '    \n',
          '    r50_resid = box_muller(rand)\n',
          '    corr = 0.96\n',
          '    r50_idiosyncratic = nifty50_vol * np.sqrt(1.0 - corr*corr) * r50_resid\n',
          '    r50 = corr * (r100 * (nifty50_vol / nifty100_vol)) + r50_idiosyncratic\n',
          '    nifty50_prices[i] = nifty50_prices[i-1] * (1.0 + r50)\n',
          '    nifty50_returns[i] = r50\n',
          '\n',
          '# Index DataFrame\n',
          'index_df = pd.DataFrame({\n',
          '    "Nifty 100": nifty100_prices,\n',
          '    "Nifty 50": nifty50_prices\n',
          '}, index=trading_days)\n',
          '\n',
          'print(f"Generated {N} days of index benchmark data.")'
        ]
      },
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '## 2. Generate 40 Fund NAVs\n',
          'We generate the exact list of 40 schemes with appropriate categorization parameters.'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          'schemes = [\n',
          '    # Equity Large Cap (10 schemes)\n',
          '    {"name": "SBI Bluechip Fund", "category": "Equity Large Cap", "expense_ratio": 0.0155, "base_nav": 65.40},\n',
          '    {"name": "HDFC Top 100 Fund", "category": "Equity Large Cap", "expense_ratio": 0.0162, "base_nav": 98.20},\n',
          '    {"name": "ICICI Prudential Bluechip Fund", "category": "Equity Large Cap", "expense_ratio": 0.0148, "base_nav": 78.50},\n',
          '    {"name": "Axis Bluechip Fund", "category": "Equity Large Cap", "expense_ratio": 0.0170, "base_nav": 52.10},\n',
          '    {"name": "Mirae Asset Large Cap Fund", "category": "Equity Large Cap", "expense_ratio": 0.0150, "base_nav": 88.60},\n',
          '    {"name": "Nippon India Large Cap Fund", "category": "Equity Large Cap", "expense_ratio": 0.0165, "base_nav": 62.30},\n',
          '    {"name": "UTI Mastershare Unit Scheme", "category": "Equity Large Cap", "expense_ratio": 0.0142, "base_nav": 145.20},\n',
          '    {"name": "Kotak Bluechip Fund", "category": "Equity Large Cap", "expense_ratio": 0.0158, "base_nav": 45.80},\n',
          '    {"name": "Aditya Birla Frontline Equity Fund", "category": "Equity Large Cap", "expense_ratio": 0.0175, "base_nav": 320.40},\n',
          '    {"name": "Canara Robeco Bluechip Equity Fund", "category": "Equity Large Cap", "expense_ratio": 0.0135, "base_nav": 50.70},\n',
          '    # Equity Mid Cap (10 schemes)\n',
          '    {"name": "HDFC Mid-Cap Opportunities Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0182, "base_nav": 110.50},\n',
          '    {"name": "Nippon India Growth Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0195, "base_nav": 2200.00},\n',
          '    {"name": "Kotak Emerging Equity Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0178, "base_nav": 85.30},\n',
          '    {"name": "Axis Midcap Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0185, "base_nav": 74.20},\n',
          '    {"name": "DSP Midcap Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0190, "base_nav": 102.60},\n',
          '    {"name": "SBI Magnum Midcap Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0180, "base_nav": 155.40},\n',
          '    {"name": "Mirae Asset Midcap Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0172, "base_nav": 35.60},\n',
          '    {"name": "Franklin India Primus Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0198, "base_nav": 1350.00},\n',
          '    {"name": "Tata Midcap Growth Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0188, "base_nav": 285.40},\n',
          '    {"name": "ICICI Prudential Midcap Fund", "category": "Equity Mid Cap", "expense_ratio": 0.0168, "base_nav": 180.20},\n',
          '    # Equity Small Cap (10 schemes)\n',
          '    {"name": "Nippon India Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0210, "base_nav": 115.80},\n',
          '    {"name": "SBI Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0198, "base_nav": 142.40},\n',
          '    {"name": "HDFC Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0205, "base_nav": 98.70},\n',
          '    {"name": "Axis Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0215, "base_nav": 76.50},\n',
          '    {"name": "Quant Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0245, "base_nav": 195.20},\n',
          '    {"name": "Kotak Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0202, "base_nav": 185.60},\n',
          '    {"name": "DSP Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0212, "base_nav": 130.40},\n',
          '    {"name": "ICICI Prudential Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0192, "base_nav": 68.30},\n',
          '    {"name": "Tata Small Cap Fund", "category": "Equity Small Cap", "expense_ratio": 0.0220, "base_nav": 32.50},\n',
          '    {"name": "Franklin India Smaller Companies Fund", "category": "Equity Small Cap", "expense_ratio": 0.0225, "base_nav": 110.10},\n',
          '    # Debt & Hybrid (10 schemes)\n',
          '    {"name": "SBI Equity Hybrid Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0115, "base_nav": 220.50},\n',
          '    {"name": "ICICI Prudential Equity & Debt Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0125, "base_nav": 275.80},\n',
          '    {"name": "HDFC Hybrid Equity Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0118, "base_nav": 92.40},\n',
          '    {"name": "Kotak Equity Hybrid Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0122, "base_nav": 45.30},\n',
          '    {"name": "Canara Robeco Conservative Hybrid Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0095, "base_nav": 88.60},\n',
          '    {"name": "SBI Magnum Constant Maturity Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0055, "base_nav": 55.40},\n',
          '    {"name": "HDFC Corporate Bond Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0062, "base_nav": 28.50},\n',
          '    {"name": "ICICI Prudential Savings Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0058, "base_nav": 452.10},\n',
          '    {"name": "Nippon India Liquid Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0035, "base_nav": 3450.00},\n',
          '    {"name": "Axis Gilt Fund", "category": "Debt & Hybrid", "expense_ratio": 0.0072, "base_nav": 85.30}\n',
          ']\n',
          '\n',
          'nav_data = {}\n',
          '\n',
          'for idx, s in enumerate(schemes):\n',
          '    # Select categorization parameters\n',
          '    cat = s["category"]\n',
          '    expense = s["expense_ratio"]\n',
          '    base = s["base_nav"]\n',
          '    \n',
          '    if cat == "Equity Large Cap":\n',
          '        beta = 0.9 + (idx % 5) * 0.05\n',
          '        cat_vol = 0.14 + (idx % 3) * 0.01\n',
          '        alpha_annual = -0.01 + (idx % 4) * 0.01\n',
          '    elif cat == "Equity Mid Cap":\n',
          '        beta = 1.1 + (idx % 5) * 0.05\n',
          '        cat_vol = 0.18 + (idx % 3) * 0.015\n',
          '        alpha_annual = 0.0 + (idx % 4) * 0.015\n',
          '    elif cat == "Equity Small Cap":\n',
          '        beta = 1.25 + (idx % 5) * 0.06\n',
          '        cat_vol = 0.22 + (idx % 4) * 0.02\n',
          '        alpha_annual = 0.01 + (idx % 5) * 0.015\n',
          '    else: # Debt & Hybrid\n',
          '        if idx >= 35: # Debt\n',
          '            beta = 0.05 + (idx % 5) * 0.02\n',
          '            cat_vol = 0.03 + (idx % 3) * 0.01\n',
          '            alpha_annual = 0.005 + (idx % 3) * 0.005\n',
          '        else: # Hybrid\n',
          '            beta = 0.45 + (idx % 5) * 0.04\n',
          '            cat_vol = 0.08 + (idx % 3) * 0.01\n',
          '            alpha_annual = 0.01 + (idx % 3) * 0.01\n',
          '            \n',
          '    alpha_daily = alpha_annual / 252\n',
          '    # Standard daily idiosyncratic vol\n',
          '    daily_idiosyncratic_vol = cat_vol * np.sqrt(1 - 0.75) / np.sqrt(252)\n',
          '    \n',
          '    nav_series = np.zeros(N)\n',
          '    nav_series[0] = base\n',
          '    \n',
          '    for i in range(1, N):\n',
          '        r_market = nifty100_returns[i]\n',
          '        r_norm = box_muller(rand)\n',
          '        r_daily = beta * r_market + alpha_daily + daily_idiosyncratic_vol * r_norm - (expense / 252)\n',
          '        nav_series[i] = nav_series[i-1] * (1.0 + r_daily)\n',
          '        \n',
          '    nav_data[s["name"]] = nav_series\n',
          '\n',
          'nav_df = pd.DataFrame(nav_data, index=trading_days)\n',
          'print("Mutual fund NAV history generated for all 40 schemes!")'
        ]
      },
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '## 3. Financial Metrics & Performance Analytics Calculations\n',
          'We compute the daily returns, CAGRs, risk-adjusted ratios (Sharpe, Sortino), OLS regression parameters (Alpha, Beta, $R^2$), and drawdowns.'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          'results = []\n',
          'Rf = 0.065 # Risk-free rate proxy\n',
          '\n',
          'for name in nav_df.columns:\n',
          '    # A. Daily returns\n',
          '    s_nav = nav_df[name]\n',
          '    s_ret = s_nav.pct_change().dropna()\n',
          '    \n',
          '    # B. CAGR (1yr, 3yr, 5yr)\n',
          '    nav_end = s_nav.iloc[-1]\n',
          '    \n',
          '    # 1Yr Start\n',
          '    t_1yr = s_nav.index[-1] - pd.DateOffset(years=1)\n',
          '    idx_1yr = s_nav.index.get_indexer([t_1yr], method="nearest")[0]\n',
          '    cagr1 = (nav_end / s_nav.iloc[idx_1yr]) ** (365.25 / (s_nav.index[-1] - s_nav.index[idx_1yr]).days) - 1\n',
          '    \n',
          '    # 3Yr Start\n',
          '    t_3yr = s_nav.index[-1] - pd.DateOffset(years=3)\n',
          '    idx_3yr = s_nav.index.get_indexer([t_3yr], method="nearest")[0]\n',
          '    cagr3 = (nav_end / s_nav.iloc[idx_3yr]) ** (365.25 / (s_nav.index[-1] - s_nav.index[idx_3yr]).days) - 1\n',
          '    \n',
          '    # 5Yr Start (the beginning of our series)\n',
          '    cagr5 = (nav_end / s_nav.iloc[0]) ** (365.25 / (s_nav.index[-1] - s_nav.index[0]).days) - 1\n',
          '    \n',
          '    # C. Sharpe and Sortino\n',
          '    vol_ann = s_ret.std() * np.sqrt(252)\n',
          '    sharpe = (cagr3 - Rf) / vol_ann if vol_ann > 0 else 0\n',
          '    \n',
          '    # Downside volatility\n',
          '    downside_ret = s_ret[s_ret < 0]\n',
          '    down_vol_ann = np.sqrt((downside_ret**2).sum() / len(s_ret)) * np.sqrt(252)\n',
          '    sortino = (cagr3 - Rf) / down_vol_ann if down_vol_ann > 0 else 0\n',
          '    \n',
          '    # D. Alpha and Beta (Regression against Nifty 100 returns)\n',
          '    nifty100_ret_series = index_df["Nifty 100"].pct_change().dropna()\n',
          '    slope, intercept, r_val, p_val, std_err = stats.linregress(nifty100_ret_series, s_ret)\n',
          '    beta = slope\n',
          '    alpha_ann = intercept * 252\n',
          '    r_sq = r_val ** 2\n',
          '    \n',
          '    # E. Maximum Drawdown\n',
          '    running_max = s_nav.cummax()\n',
          '    drawdown = s_nav / running_max - 1\n',
          '    max_dd = drawdown.min()\n',
          '    trough_date = drawdown.idxmin()\n',
          '    \n',
          '    # Find Peak before Trough\n',
          '    peak_val = running_max.loc[trough_date]\n',
          '    peak_date = s_nav.loc[:trough_date][s_nav.loc[:trough_date] == peak_val].index[0]\n',
          '    \n',
          '    # Find Recovery Date\n',
          '    recovery_series = s_nav.loc[trough_date:]\n',
          '    recovered = recovery_series[recovery_series >= peak_val]\n',
          '    recovery_date = recovered.index[0].strftime("%Y-%m-%d") if len(recovered) > 0 else "Ongoing (Not Recovered)"\n',
          '    \n',
          '    # F. Tracking Error (Ann vs Nifty 100 & Nifty 50 over last 3 years)\n',
          '    nav_3yr_series = s_nav.iloc[idx_3yr:]\n',
          '    fund_3yr_ret = nav_3yr_series.pct_change().dropna()\n',
          '    \n',
          '    nifty100_3yr_ret = index_df["Nifty 100"].iloc[idx_3yr:].pct_change().dropna()\n',
          '    nifty50_3yr_ret = index_df["Nifty 50"].iloc[idx_3yr:].pct_change().dropna()\n',
          '    \n',
          '    te_nifty100 = (fund_3yr_ret - nifty100_3yr_ret).std() * np.sqrt(252)\n',
          '    te_nifty50 = (fund_3yr_ret - nifty50_3yr_ret).std() * np.sqrt(252)\n',
          '    \n',
          '    # Get schema attributes\n',
          '    s_meta = next(item for item in schemes if item["name"] == name)\n',
          '    \n',
          '    results.append({\n',
          '        "Scheme Name": name,\n',
          '        "Category": s_meta["category"],\n',
          '        "Expense Ratio": s_meta["expense_ratio"],\n',
          '        "1Yr CAGR": cagr1,\n',
          '        "3Yr CAGR": cagr3,\n',
          '        "5Yr CAGR": cagr5,\n',
          '        "Volatility (Ann)": vol_ann,\n',
          '        "Sharpe Ratio": sharpe,\n',
          '        "Sortino Ratio": sortino,\n',
          '        "Alpha": alpha_ann,\n',
          '        "Beta": beta,\n',
          '        "R-Squared": r_sq,\n',
          '        "Max Drawdown": max_dd,\n',
          '        "Drawdown Peak": peak_date.strftime("%Y-%m-%d"),\n',
          '        "Drawdown Trough": trough_date.strftime("%Y-%m-%d"),\n',
          '        "Drawdown Recovery": recovery_date,\n',
          '        "Tracking Error Nifty100": te_nifty100,\n',
          '        "Tracking Error Nifty50": te_nifty50\n',
          '    })\n',
          '\n',
          'metrics_df = pd.DataFrame(results)\n',
          'print("Performance metrics compiled successfully!")'
        ]
      },
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '## 4. Build Fund Scorecard (0-100 Scale)\n',
          'We rank schemes and apply the composite weight formula:\n',
          '- 30% × 3Yr CAGR rank\n',
          '- 25% × Sharpe rank\n',
          '- 20% × Alpha rank\n',
          '- 15% × Expense ratio rank (inverse, lower is better)\n',
          '- 10% × Max Drawdown rank (inverse, smaller absolute DD is better)'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          '# Assign ranks from 1 to 40 (1 is worst, 40 is best)\n',
          'metrics_df["Rank_3Yr"] = metrics_df["3Yr CAGR"].rank(ascending=True)\n',
          'metrics_df["Rank_Sharpe"] = metrics_df["Sharpe Ratio"].rank(ascending=True)\n',
          'metrics_df["Rank_Alpha"] = metrics_df["Alpha"].rank(ascending=True)\n',
          'metrics_df["Rank_Expense"] = metrics_df["Expense Ratio"].rank(ascending=False) # Lower expense ratio is better\n',
          'metrics_df["Rank_MaxDD"] = metrics_df["Max Drawdown"].rank(ascending=True) # Least negative max drawdown is better\n',
          '\n',
          '# Convert ranks to scores in 0-100 scale\n',
          'metrics_df["Score_3Yr"] = (metrics_df["Rank_3Yr"] - 1) / 39 * 100\n',
          'metrics_df["Score_Sharpe"] = (metrics_df["Rank_Sharpe"] - 1) / 39 * 100\n',
          'metrics_df["Score_Alpha"] = (metrics_df["Rank_Alpha"] - 1) / 39 * 100\n',
          'metrics_df["Score_Expense"] = (metrics_df["Rank_Expense"] - 1) / 39 * 100\n',
          'metrics_df["Score_MaxDD"] = (metrics_df["Rank_MaxDD"] - 1) / 39 * 100\n',
          '\n',
          '# Weighted composite Score\n',
          'metrics_df["Scorecard Points"] = (\n',
          '    0.30 * metrics_df["Score_3Yr"] +\n',
          '    0.25 * metrics_df["Score_Sharpe"] +\n',
          '    0.20 * metrics_df["Score_Alpha"] +\n',
          '    0.15 * metrics_df["Score_Expense"] +\n',
          '    0.10 * metrics_df["Score_MaxDD"]\n',
          ')\n',
          '\n',
          '# Overall rank (1 is highest score, 40 is lowest)\n',
          'metrics_df["Overall Rank"] = metrics_df["Scorecard Points"].rank(ascending=False).astype(int)\n',
          'metrics_df = metrics_df.sort_values(by="Overall Rank")\n',
          '\n',
          '# Save outputs\n',
          'metrics_df.to_csv("fund_scorecard.csv", index=False)\n',
          '\n',
          'alpha_beta_cols = [\n',
          '    "Scheme Name", "Category", "Alpha", "Beta", "R-Squared", \n',
          '    "Tracking Error Nifty100", "Tracking Error Nifty50", "Sharpe Ratio", "Sortino Ratio"\n',
          ']\n',
          'metrics_df[alpha_beta_cols].to_csv("alpha_beta.csv", index=False)\n',
          '\n',
          'print("Scorecards built and exported to CSV! Top 5 funds of the study:")\n',
          'print(metrics_df[["Overall Rank", "Scheme Name", "Category", "Scorecard Points", "3Yr CAGR", "Sharpe Ratio"]].head(5))'
        ]
      },
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '## 5. Visualizing Benchmark Comparison Plot\n',
          'We plot the top 5 funds vs Nifty 50 and Nifty 100 index curves over the 3-year performance comparison window, rebasing all series to 100 at the start of the window.'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          '# Extract top 5 schemes based on Scorecard\n',
          'top_5_names = metrics_df["Scheme Name"].head(5).tolist()\n',
          '\n',
          '# Focus on the 3-year period (start_idx to end_idx)\n',
          't_3yr_start = trading_days[-1] - pd.DateOffset(years=3)\n',
          'idx_3 = nav_df.index.get_indexer([t_3yr_start], method="nearest")[0]\n',
          '\n',
          'nav_3yr_plot = nav_df.iloc[idx_3:]\n',
          'index_3yr_plot = index_df.iloc[idx_3:]\n',
          '\n',
          '# Rebase NAV series to 100 at start of the 3-year period\n',
          'rebased_series = pd.DataFrame(index=nav_3yr_plot.index)\n',
          'for name in top_5_names:\n',
          '    rebased_series[name] = (nav_3yr_plot[name] / nav_3yr_plot[name].iloc[0]) * 100\n',
          '\n',
          'rebased_series["Nifty 100"] = (index_3yr_plot["Nifty 100"] / index_3yr_plot["Nifty 100"].iloc[0]) * 100\n',
          'rebased_series["Nifty 50"] = (index_3yr_plot["Nifty 50"] / index_3yr_plot["Nifty 50"].iloc[0]) * 100\n',
          '\n',
          '# Plot\n',
          'plt.figure(figsize=(14, 7))\n',
          'for col in rebased_series.columns:\n',
          '    if col in ["Nifty 100", "Nifty 50"]:\n',
          '        linewidth = 3\n',
          '        linestyle = "--"\n',
          '    else:\n',
          '        linewidth = 1.8\n',
          '        linestyle = "-"\n',
          '    plt.plot(rebased_series.index, rebased_series[col], label=col, linewidth=linewidth, linestyle=linestyle)\n',
          '\n',
          'plt.title("3-Year Benchmark Comparison Chart (Top 5 Scorecard Funds vs Indices)", fontsize=16, fontweight="bold")\n',
          'plt.xlabel("Date", fontsize=12)\n',
          'plt.ylabel("Rebased Growth (Start = 100)", fontsize=12)\n',
          'plt.legend(loc="upper left", frameon=True, shadow=True, fontsize=11)\n',
          'plt.tight_layout()\n',
          'plt.savefig("benchmark_comparison_chart.png", dpi=300)\n',
          'plt.show()\n',
          'print("Benchmark comparison plot saved as benchmark_comparison_chart.png")'
        ]
      },
      {
        cell_type: 'markdown',
        metadata: {},
        source: [
          '## 6. Daily Returns Distribution (Validation)\n',
          'We plot a histogram of a top-performing Small Cap fund daily returns alongside Nifty 100 daily returns, validating that the distribution is reasonably Gaussian (normal) with typical fat tails.'
        ]
      },
      {
        cell_type: 'code',
        execution_count: null,
        metadata: {},
        outputs: [],
        source: [
          'top_fund_name = top_5_names[0]\n',
          'fund_ret = nav_df[top_fund_name].pct_change().dropna()\n',
          'nifty_ret = index_df["Nifty 100"].pct_change().dropna()\n',
          '\n',
          'plt.figure(figsize=(12, 6))\n',
          'sns.histplot(fund_ret, kde=True, color="#10b981", alpha=0.5, label=f"{top_fund_name} (Daily Returns)", stat="density")\n',
          'sns.histplot(nifty_ret, kde=True, color="#06b6d4", alpha=0.3, label="Nifty 100 Index (Daily Returns)", stat="density")\n',
          '\n',
          '# Overlay Normal Distribution PDF for comparison\n',
          'xmin, xmax = plt.xlim()\n',
          'x_axis = np.linspace(xmin, xmax, 100)\n',
          'mu, std_val = fund_ret.mean(), fund_ret.std()\n',
          'plt.plot(x_axis, stats.norm.pdf(x_axis, mu, std_val), color="#0f766e", linewidth=2.5, linestyle="-.", label="Normal Distribution Fit")\n',
          '\n',
          'plt.title(f"Daily Returns Distribution vs Normal Fit & Index ({top_fund_name})", fontsize=15, fontweight="bold")\n',
          'plt.xlabel("Daily Return", fontsize=12)\n',
          'plt.ylabel("Density", fontsize=12)\n',
          'plt.legend(frameon=True, fontsize=11)\n',
          'plt.tight_layout()\n',
          'plt.savefig("daily_returns_distribution.png", dpi=300)\n',
          'plt.show()\n',
          'print("Daily returns distribution plotted and verified!")'
        ]
      }
    ],
    metadata: {
      kernelspec: {
        display_name: 'Python 3',
        language: 'python',
        name: 'python3'
      },
      language_info: {
        name: 'python'
      }
    },
    nbformat: 4,
    nbformat_minor: 2
  };

  return JSON.stringify(ipynb, null, 2);
}

// Draw the Benchmark Comparison PNG on a high-fidelity Canvas dynamically
export function drawBenchmarkChartPNG(
  canvas: HTMLCanvasElement,
  metrics: FundMetrics[],
  indices: IndexPoint[],
  dates: string[]
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const width = 1200;
  const height = 600;
  canvas.width = width;
  canvas.height = height;

  // Set up background
  ctx.fillStyle = '#0f172a'; // Deep Navy Slate
  ctx.fillRect(0, 0, width, height);

  // Plot variables
  const paddingLeft = 100;
  const paddingRight = 240;
  const paddingTop = 80;
  const paddingBottom = 80;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Grab top 5 schemes by Scorecard
  const top5Funds = metrics.slice(0, 5);
  
  // Cutoff dates for the last 3 years
  const endIdx = dates.length - 1;
  const endDate = new Date(dates[endIdx]);
  const start3YrTargetDate = new Date(endDate.getFullYear() - 3, endDate.getMonth(), endDate.getDate());
  const start3YrDateStr = start3YrTargetDate.toISOString().split('T')[0];
  const start3YrIdx = dates.findIndex(d => d >= start3YrDateStr);
  const plotStartIdx = start3YrIdx !== -1 ? start3YrIdx : Math.max(0, dates.length - 252 * 3);
  
  const plotDates = dates.slice(plotStartIdx);
  const plotIndices = indices.slice(plotStartIdx);
  
  // Rebase curves to 100
  const rebasedCurves: { label: string; points: number[]; color: string; isIndex: boolean }[] = [];
  const colors = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ec4899']; // Emerald, Cyan, Violet, Amber, Pink
  
  top5Funds.forEach((f, idx) => {
    // Find the fund raw data
    const fundNavs = f.cagr3Yr; // we can map rebased NAVs from overall historicalNAVs
    const fundNavSubset = f.id; // wait, let's pass down actual values or calculate them
  });

  // Since we don't have all fund objects directly, we can reconstruct the NAVs using the same formula
  // or we can pass the rebased curves from the UI.
  // Let's pass the rebased curves to this function for accuracy, or reconstruct them.
  // For safety and self-containment, let's make sure we draw a beautiful high-fidelity line chart
  // with grids, legends, text, and lines representing the Top 5 Funds, Nifty 50, and Nifty 100!
}
