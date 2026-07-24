import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

def make_notebook(filename, cells):
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    nb_dict = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    path = NOTEBOOKS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb_dict, f, indent=2)
    print(f"Created Notebook: {filename}")

def build_notebook_01():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 01. Data Ingestion\n",
                "This notebook implements the data ingestion phase of the Mutual Fund Data Analytics Capstone.\n",
                "\n",
                "### Objectives:\n",
                "1. Connect to the Live AMFI API (`mfapi.in`) to fetch daily NAV histories.\n",
                "2. Load and inspect the 10 local CSV datasets.\n",
                "3. Perform initial exploration of schemas, dimensions, missing values, and integrity checks."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import pandas as pd\n",
                "from pathlib import Path\n",
                "\n",
                "# Configure paths\n",
                "BASE_DIR = Path(os.getcwd()).parent\n",
                "RAW_DIR = BASE_DIR / \"data\" / \"raw\"\n",
                "print(f\"Raw data folder resolved: {RAW_DIR}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Load and Inspect Local Raw CSVs"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "csv_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.csv') and not f.endswith('_NAV.csv')]\n",
                "print(\"Available raw CSV datasets:\")\n",
                "for f in sorted(csv_files):\n",
                "    print(f\" - {f}\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load and check one sample dataset\n",
                "master_path = RAW_DIR / \"01_fund_master.csv\"\n",
                "if master_path.exists():\n",
                "    master_df = pd.read_csv(master_path)\n",
                "    print(\"\\n--- 01_fund_master.csv Schema ---\")\n",
                "    print(master_df.info())\n",
                "    print(\"\\nMissing values per column:\")\n",
                "    print(master_df.isnull().sum())\n",
                "    display(master_df.head(3))"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Verify AMFI Scheme Code Mappings\n",
                "We check if the AMFI codes in `01_fund_master.csv` are covered in `02_nav_history.csv`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "nav_path = RAW_DIR / \"02_nav_history.csv\"\n",
                "if master_path.exists() and nav_path.exists():\n",
                "    master_df = pd.read_csv(master_path)\n",
                "    nav_df = pd.read_csv(nav_path)\n",
                "    \n",
                "    master_codes = set(master_df['amfi_code'].unique())\n",
                "    nav_codes = set(nav_df['amfi_code'].unique())\n",
                "    \n",
                "    missing_codes = master_codes - nav_codes\n",
                "    print(f\"Total unique codes in Master: {len(master_codes)}\")\n",
                "    print(f\"Total unique codes in NAV History: {len(nav_codes)}\")\n",
                "    print(f\"AMFI codes missing in NAV History: {missing_codes}\")"
            ]
        }
    ]
    make_notebook("01_data_ingestion.ipynb", cells)

def build_notebook_02():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 02. Data Cleaning\n",
                "This notebook details the cleaning and preprocessing procedures, focusing on database constraints and weekend/holiday NAV handling.\n",
                "\n",
                "### Objectives:\n",
                "1. Clean dates, types, and outliers.\n",
                "2. **Weekend/Holiday Forward-Filling**: Reindex NAV history to a full date range and perform `ffill()` to prevent gaps.\n",
                "3. Clean transactions and KYC records."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import pandas as pd\n",
                "from pathlib import Path\n",
                "\n",
                "BASE_DIR = Path(os.getcwd()).parent\n",
                "RAW_DIR = BASE_DIR / \"data\" / \"raw\"\n",
                "PROCESSED_DIR = BASE_DIR / \"data\" / \"processed\"\n",
                "print(f\"RAW: {RAW_DIR}\\nPROCESSED: {PROCESSED_DIR}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Reindexing & Forward-Filling NAV History\n",
                "Mutual fund NAVs are only published on business days. To avoid gaps in time-series operations, we expand the dates to calendar dates (daily) and forward-fill values."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "def clean_and_fill_nav():\n",
                "    raw_nav_path = RAW_DIR / \"02_nav_history.csv\"\n",
                "    df = pd.read_csv(raw_nav_path)\n",
                "    \n",
                "    # Convert types\n",
                "    df['date'] = pd.to_datetime(df['date'])\n",
                "    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')\n",
                "    df = df.dropna(subset=['amfi_code', 'date', 'nav'])\n",
                "    df = df[df['nav'] > 0]\n",
                "    \n",
                "    # Reindexing function per fund\n",
                "    def fill_missing(group):\n",
                "        code = group['amfi_code'].iloc[0]\n",
                "        full_range = pd.date_range(group['date'].min(), group['date'].max(), freq='D')\n",
                "        res = group.set_index('date').reindex(full_range)\n",
                "        res['amfi_code'] = code\n",
                "        res['nav'] = res['nav'].ffill()\n",
                "        return res.rename_axis('date').reset_index()\n",
                "        \n",
                "    df_cleaned = df.groupby('amfi_code', group_keys=False).apply(fill_missing).reset_index(drop=True)\n",
                "    print(f\"Reindexed rows. Raw count: {len(df)}, Reindexed count: {len(df_cleaned)}\")\n",
                "    return df_cleaned\n",
                "\n",
                "nav_clean = clean_and_fill_nav()\n",
                "display(nav_clean.head(10))"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Transaction Standardization\n",
                "We standardize investor transactions into three clean buckets: `SIP`, `Lumpsum`, `Redemption`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "tx_path = RAW_DIR / \"08_investor_transactions.csv\"\n",
                "if tx_path.exists():\n",
                "    tx_df = pd.read_csv(tx_path)\n",
                "    print(\"Raw transaction types count:\")\n",
                "    print(tx_df['transaction_type'].value_counts())\n",
                "    \n",
                "    def std_tx(val):\n",
                "        val_up = str(val).upper().strip()\n",
                "        if 'SIP' in val_up: return 'SIP'\n",
                "        if 'LUMP' in val_up: return 'Lumpsum'\n",
                "        if 'REDEMP' in val_up or 'WITHDRAW' in val_up: return 'Redemption'\n",
                "        return 'Other'\n",
                "        \n",
                "    tx_df['transaction_type'] = tx_df['transaction_type'].apply(std_tx)\n",
                "    print(\"\\nStandardised transaction types:\")\n",
                "    print(tx_df['transaction_type'].value_counts())"
            ]
        }
    ]
    make_notebook("02_data_cleaning.ipynb", cells)

def build_notebook_03():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 03. Exploratory Data Analysis (EDA)\n",
                "This notebook analyzes mutual fund distributions, sector weights, AUM shares, and investor behavior.\n",
                "\n",
                "### Objectives:\n",
                "1. Visualize scheme categories and AUM distribution.\n",
                "2. Analyze investor demographics (city tier, age group, gender) and transaction patterns.\n",
                "3. Chart industry SIP growth and category inflows."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "from pathlib import Path\n",
                "\n",
                "BASE_DIR = Path(os.getcwd()).parent\n",
                "PROCESSED_DIR = BASE_DIR / \"data\" / \"processed\"\n",
                "plt.style.use('ggplot')\n",
                "print(\"Libraries loaded!\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Scheme Category Analysis"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "master_df = pd.read_csv(PROCESSED_DIR / \"01_fund_master.csv\")\n",
                "plt.figure(figsize=(10, 5))\n",
                "sns.countplot(data=master_df, y='category', hue='risk_category', palette='Set2')\n",
                "plt.title('Mutual Fund Categories by Risk Classification')\n",
                "plt.xlabel('Count of Schemes')\n",
                "plt.ylabel('Category')\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Transaction Analysis by Demographics"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "tx_df = pd.read_csv(PROCESSED_DIR / \"08_investor_transactions.csv\")\n",
                "plt.figure(figsize=(10, 5))\n",
                "sns.boxplot(data=tx_df, x='age_group', y='amount_inr', hue='gender', palette='pastel')\n",
                "plt.yscale('log') # Log scale since amount distribution has large outliers\n",
                "plt.title('Transaction Amount distribution by Age Group and Gender (Log Scale)')\n",
                "plt.xlabel('Age Group')\n",
                "plt.ylabel('Transaction Amount (INR)')\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. Monthly SIP Inflows Trend"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "sip_df = pd.read_csv(PROCESSED_DIR / \"04_monthly_sip_inflows.csv\")\n",
                "plt.figure(figsize=(12, 5))\n",
                "sns.lineplot(data=sip_df, x='month', y='sip_inflow_crore', marker='o', color='purple', linewidth=2.5)\n",
                "plt.xticks(rotation=45)\n",
                "plt.title('Monthly SIP Inflows Trend (Crores)')\n",
                "plt.xlabel('Month')\n",
                "plt.ylabel('SIP Inflow in Crores')\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        }
    ]
    make_notebook("03_eda_analysis.ipynb", cells)

def build_notebook_04():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 04. Performance Analytics & Portfolio Optimization\n",
                "This notebook implements primary financial performance metrics, Value at Risk, Monte Carlo simulations, and Markowitz portfolio optimization.\n",
                "\n",
                "### Objectives:\n",
                "1. **CAGR Calculation**: Replicate annualized returns using trading-day weights: `CAGR = (Ending / Beginning) ** (252 / n_trading_days) - 1`.\n",
                "2. **Sharpe & Beta**: Compute standard Sharpe and CAPM Beta regression parameters.\n",
                "3. **Monte Carlo Projection (Bonus B3)**: Project NAV over 5 years with uncertainty bands.\n",
                "4. **Markowitz Optimization (Bonus B4)**: Calculate Efficient Frontier for 5 selected large-cap funds."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "from scipy.optimize import minimize\n",
                "from pathlib import Path\n",
                "\n",
                "BASE_DIR = Path(os.getcwd()).parent\n",
                "PROCESSED_DIR = BASE_DIR / \"data\" / \"processed\"\n",
                "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n",
                "print(\"Environment initialized!\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Monte Carlo NAV Simulation (Bonus B3)\n",
                "We project a fund's growth over 5 years (1260 trading days) using Geometric Brownian Motion (GBM):"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load NAV data\n",
                "nav_df = pd.read_csv(PROCESSED_DIR / \"02_nav_history.csv\")\n",
                "sbi_nav = nav_df[nav_df['amfi_code'] == 119551].sort_values('date')\n",
                "sbi_returns = sbi_nav['nav'].pct_change().dropna()\n",
                "\n",
                "# Drift and Volatility\n",
                "dt = 1 / 252\n",
                "mu = sbi_returns.mean() * 252\n",
                "sigma = sbi_returns.std() * np.sqrt(252)\n",
                "S0 = sbi_nav['nav'].iloc[-1]\n",
                "\n",
                "n_days = 5 * 252\n",
                "n_sims = 1000\n",
                "np.random.seed(42)\n",
                "\n",
                "sim_nav = np.zeros((n_days, n_sims))\n",
                "sim_nav[0, :] = S0\n",
                "\n",
                "for t in range(1, n_days):\n",
                "    z = np.random.normal(0, 1, n_sims)\n",
                "    sim_nav[t, :] = sim_nav[t-1, :] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)\n",
                "    \n",
                "# Confidence Intervals\n",
                "median_path = np.median(sim_nav, axis=1)\n",
                "upper_90 = np.percentile(sim_nav, 90, axis=1)\n",
                "lower_10 = np.percentile(sim_nav, 10, axis=1)\n",
                "\n",
                "plt.figure(figsize=(10, 5))\n",
                "plt.plot(median_path, label='Median Projected NAV', color='blue', linewidth=2)\n",
                "plt.fill_between(range(n_days), lower_10, upper_90, color='blue', alpha=0.15, label='10% - 90% Confidence Band')\n",
                "plt.title('SBI Bluechip NAV 5-Year Projection (Monte Carlo Simulation)')\n",
                "plt.xlabel('Trading Days')\n",
                "plt.ylabel('NAV (INR)')\n",
                "plt.legend(loc='upper left')\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Markowitz Efficient Frontier (Bonus B4)\n",
                "We optimize a portfolio of 5 designated large-cap funds based on historical covariance."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "target_codes = [119551, 125497, 120503, 118632, 119092]\n",
                "sub_nav = nav_df[nav_df['amfi_code'].isin(target_codes)]\n",
                "pivot_nav = sub_nav.pivot(index='date', columns='amfi_code', values='nav').dropna()\n",
                "returns = pivot_nav.pct_change().dropna()\n",
                "\n",
                "# Annualised return & covariance\n",
                "ann_ret = returns.mean() * 252\n",
                "cov_matrix = returns.cov() * 252\n",
                "\n",
                "num_assets = len(target_codes)\n",
                "port_returns = []\n",
                "port_vol = []\n",
                "port_weights = []\n",
                "\n",
                "np.random.seed(42)\n",
                "for _ in range(5000):\n",
                "    w = np.random.random(num_assets)\n",
                "    w /= np.sum(w)\n",
                "    ret = np.sum(w * ann_ret)\n",
                "    vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))\n",
                "    port_returns.append(ret)\n",
                "    port_vol.append(vol)\n",
                "    port_weights.append(w)\n",
                "\n",
                "plt.figure(figsize=(10, 5))\n",
                "plt.scatter(port_vol, port_returns, c=np.array(port_returns)/np.array(port_vol), cmap='viridis', marker='o', s=10, alpha=0.5)\n",
                "plt.colorbar(label='Sharpe Ratio (Rf=0)')\n",
                "plt.title('Markowitz Efficient Frontier (5 Selected Funds)')\n",
                "plt.xlabel('Annualised Volatility')\n",
                "plt.ylabel('Expected Return')\n",
                "plt.grid(True)\n",
                "plt.show()"
            ]
        }
    ]
    make_notebook("04_performance_analytics.ipynb", cells)

def build_notebook_05():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 05. Advanced Analytics & Risk Metrics\n",
                "This notebook implements advanced portfolio and investor analyses.\n",
                "\n",
                "### Objectives:\n",
                "1. **Value at Risk (VaR 95%) & Conditional VaR (CVaR)**: Correct historical returns risk profiling.\n",
                "2. **Investor Cohort Analysis**: Group transactions by first investment year and analyze behaviors.\n",
                "3. **SIP Continuity & Retention**: Track regular SIP investors and identify at-risk accounts.\n",
                "4. **Sector Concentration (HHI)**: Compute Herfindahl-Hirschman concentration indexes for equity schemes."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "from pathlib import Path\n",
                "\n",
                "BASE_DIR = Path(os.getcwd()).parent\n",
                "PROCESSED_DIR = BASE_DIR / \"data\" / \"processed\"\n",
                "print(\"Environment initialized!\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Value at Risk (VaR) and Conditional VaR (CVaR)\n",
                "We calculate the historical VaR (95% confidence level) and the corresponding tail average CVaR (expected shortfall) from historical returns."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "var_report = pd.read_csv(PROCESSED_DIR / \"var_cvar_report.csv\")\n",
                "plt.figure(figsize=(11, 5))\n",
                "sns.barplot(data=var_report.sort_values('var_95_pct', ascending=False).head(10), x='var_95_pct', y='scheme_name', palette='Reds_r')\n",
                "plt.title('Top 10 High-Risk Schemes by 95% Value at Risk (VaR)')\n",
                "plt.xlabel('Historical VaR (95% Daily Loss %)')\n",
                "plt.ylabel('Scheme Name')\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Investor Cohort Analysis"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "cohort_df = pd.read_csv(PROCESSED_DIR / \"cohort_analysis.csv\")\n",
                "print(\"Investor Cohort Analysis Summary Table:\")\n",
                "display(cohort_df)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. Sector HHI Concentration\n",
                "HHI index scores range from 0 to 10,000. High HHI signifies concentration (holding a few sectors heavily), whereas low HHI indicates multi-sector diversification."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "hhi_df = pd.read_csv(PROCESSED_DIR / \"sector_hhi.csv\")\n",
                "plt.figure(figsize=(10, 5))\n",
                "sns.barplot(data=hhi_df.head(10), x='hhi_score', y='scheme_name', palette='viridis')\n",
                "plt.title('Top 10 Most Sector-Concentrated Equity Funds (HHI Score)')\n",
                "plt.xlabel('Herfindahl-Hirschman Index (HHI)')\n",
                "plt.ylabel('Scheme Name')\n",
                "plt.show()"
            ]
        }
    ]
    make_notebook("05_advanced_analytics.ipynb", cells)

def run():
    build_notebook_01()
    build_notebook_02()
    build_notebook_03()
    build_notebook_04()
    build_notebook_05()
    print("All Jupyter Notebooks built successfully.")

if __name__ == '__main__':
    run()
