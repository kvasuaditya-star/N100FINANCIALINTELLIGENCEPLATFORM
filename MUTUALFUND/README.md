# Bluestock Mutual Fund Analytics Capstone

An end-to-end data engineering and quantitative research platform that fetches, cleans, structures, and analyzes mutual fund daily Net Asset Value (NAV) data. It implements performance metrics, risk engineering, portfolio optimization, and presents results in a high-end Streamlit web application.

---

## 📂 Project Directory Structure

Following the capstone directory guidelines, the repository is structured as follows:

```text
bluestock_mf_capstone/
├── data/
│   ├── raw/                  # Immutable raw datasets and downloaded API NAVs
│   ├── processed/            # Cleaned, standardized, and reindexed CSVs
│   └── db/                   # SQLite database (bluestock_mf.db - git-ignored)
│
├── notebooks/                # Numbered Jupyter Notebooks
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
│
├── scripts/                  # Standalone Python scripts for pipeline & reports
│   ├── etl_pipeline.py       # Core ETL: Ingestion + Cleaning + Database Loading
│   ├── live_nav_fetch.py     # Live AMFI API query script
│   ├── compute_metrics.py    # Math engine: CAGR, Sharpe, Beta, VaR, CVaR, HHI
│   ├── recommender.py        # CLI Sharpe-based fund recommender
│   ├── schedule_etl.py       # Weekday 8 PM background scheduler daemon (Bonus B1)
│   ├── email_report.py       # Automated weekly HTML report generator (Bonus B5)
│   ├── generate_final_ppt.py # python-pptx presentation builder
│   └── generate_pdf_report.py# ReportLab PDF report builder
│
├── sql/                      # Relational database configurations
│   ├── schema.sql            # SQLite schema statements with PK and FK constraints
│   └── queries.sql           # 10 analytical SQL queries
│
├── dashboard/                # Web Dashboard
│   └── app.py                # Premium multi-page Streamlit dashboard app (Bonus B2)
│
├── reports/                  # Exported Deliverables
│   ├── Final_Report.pdf      # Professional Capstone PDF report (D7)
│   └── Presentation.pptx     # Professional slide deck (D7)
│
├── requirements.txt          # Python package requirements
├── .gitignore                # Git-ignored folders (venv, *.db databases)
└── README.md                 # Project README documentation
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Environment Setup
Clone the repository and install the dependencies:
```bash
git clone https://github.com/kvasuaditya-star/MUTUALFUNDSDATAANALYTICS.git
cd MUTUALFUNDSDATAANALYTICS

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
# Additional packages for Streamlit, ReportLab, and pptx:
pip install streamlit plotly reportlab python-pptx
```

---

## 🚀 Execution & Pipeline Flow

Run the project files sequentially to execute the full capstone stack:

### Step 1: Run the ETL Pipeline (D1, D2)
This script fetches live NAV records from the API, reindexes dates, standardizes types, and builds a fresh, verified `data/db/bluestock_mf.db` database.
```bash
python scripts/etl_pipeline.py
```

### Step 2: Compute Ratios and Advanced Metrics (D4, D6)
Calculates CAGR, Sharpe ratios, Betas, Value at Risk (VaR), CVaR, portfolio allocations, and customer retention metrics.
```bash
python scripts/compute_metrics.py
```

### Step 3: Run the Streamlit Dashboard (D5, B2)
Launches the interactive, multi-page dashboard locally:
```bash
streamlit run dashboard/app.py
```

### Step 4: Generate Presentations & PDF Reports (D7)
Produces professional output files inside the `reports/` folder:
```bash
python scripts/generate_final_ppt.py
python scripts/generate_pdf_report.py
```

---

## 📐 Quantitative Formulations

Our scripts use correct mathematical formulas, avoiding common indexing and day-count errors:

1. **Annualised Compound Annual Growth Rate (CAGR)**
   Annualized using **trading days** (252) rather than calendar days:
   $$\text{CAGR} = \left(\frac{\text{Ending NAV}}{\text{Beginning NAV}}\right)^{\frac{252}{n_{\text{trading days}}}} - 1$$

2. **Annualised Sharpe Ratio**
   Uses annualized returns (CAGR) and annualized volatility:
   $$\text{Sharpe Ratio} = \frac{\text{CAGR} - R_f}{\sigma_{\text{ann}}}$$
   $$\text{where } \sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{252} \quad \text{and } R_f = 6\% \text{ (Risk-Free Rate)}$$

3. **CAPM Beta**
   Covariance of fund returns with benchmark (Nifty 100) returns, normalized by benchmark variance:
   $$\beta = \frac{\text{Cov}(R_{\text{fund}}, R_{\text{market}})}{\text{Var}(R_{\text{market}})}$$

4. **Value at Risk (VaR 95%) & Conditional VaR (CVaR)**
   Calculated historically on the 5th percentile of daily returns:
   $$\text{VaR}_{95\%} = P_{5}(R_{\text{daily}})$$
   $$\text{CVaR}_{95\%} = E[R_{\text{daily}} \mid R_{\text{daily}} \le \text{VaR}_{95\%}]$$

5. **Herfindahl-Hirschman Index (Sector HHI)**
   Measures sector concentration of stock weights in the portfolio:
   $$\text{HHI} = \sum_{i=1}^{k} (w_i)^2 \quad \text{where } w_i \text{ is the weight percentage of sector } i$$

---

## 🌟 Deliverables & Bonus Solutions

* **D1 (ETL pipeline script.py)**: Completed in `scripts/etl_pipeline.py` with automatic exception logs.
* **D2 (SQLite database.db)**: Staged at `data/db/bluestock_mf.db`. Created using `sql/schema.sql` and queried in `sql/queries.sql`. Added to `.gitignore` to prevent tracking.
* **D3 (EDA notebook.ipynb)**: Located in `notebooks/03_eda_analysis.ipynb`.
* **D4 (Performance metrics.ipynb + CSVs)**: Metrics calculated via `scripts/compute_metrics.py` and exported to CSV files, with notebook analysis in `notebooks/04_performance_analytics.ipynb`.
* **D5 (Interactive dashboard.pbix)**: Replaced by a high-end multi-page Streamlit web app alternative.
* **D6 (Advanced analytics.ipynb)**: Located in `notebooks/05_advanced_analytics.ipynb` detailing VaR, HHI, and investor retention.
* **D7 (Final report + slides.pdf + .pptx)**: Dynamically generated inside `reports/Final_Report.pdf` and `reports/Presentation.pptx`.
* **B1 (ETL weekday Cron Scheduler)**: Background weekday service in `scripts/schedule_etl.py`.
* **B2 (Streamlit Dashboard)**: Deployed in `dashboard/app.py` with over 2 filters per page.
* **B3 (Monte Carlo NAV Simulation)**: Implemented with Geometric Brownian Motion (GBM) confidence intervals on Page 4 of the Streamlit app and inside Notebook 04.
* **B4 (Markowitz portfolio Optimisation)**: Efficient frontier simulation plotted dynamically on Page 4 of the Streamlit app and inside Notebook 04.
* **B5 (Automated Email Report Generator)**: HTML report generator configured in `scripts/email_report.py`.
