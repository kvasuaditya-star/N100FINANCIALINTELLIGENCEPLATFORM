# N100 Financial Intelligence Platform

A production-grade financial analytics platform built on **Nifty 100** data.

## Project Overview

This repository contains the full **Sprint 1 — Data Foundation** implementation:

- ✅ **SQLite database** (`data/nifty100.db`) with 12 tables, 92 companies
- ✅ **ETL pipeline** with normalisation, validation (16 DQ rules), and audit logging
- ✅ **48 unit tests** — all passing
- ✅ **Zero FK violations** after full data load
- ✅ **10 exploratory SQL queries**

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Database | SQLite via `sqlite3` |
| Data Processing | `pandas`, `numpy`, `openpyxl` |
| API | `FastAPI`, `uvicorn` |
| Dashboard | `Streamlit`, `plotly` |
| ML/Analytics | `scikit-learn`, `scipy` |
| Reports | `reportlab` |
| Testing | `pytest` |
| Linting | `black`, `ruff` |

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/kvasuaditya-star/N100FINANCIALINTELLIGENCEPLATFORM.git
cd N100FINANCIALINTELLIGENCEPLATFORM
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download raw data
```bash
python download_data.py
```

### 5. Run ETL pipeline
```bash
make load
# or directly:
.venv\Scripts\python src/etl/loader.py
```

### 6. Run unit tests
```bash
make test
# or:
.venv\Scripts\pytest tests/
```

### 7. Run Streamlit Dashboard
```bash
.venv\Scripts\streamlit run src/dashboard/app.py
# or:
make dashboard
```

### 8. Run Valuation Module
```bash
.venv\Scripts\python src/analytics/valuation.py
```

## Project Structure

```
N100FINANCIALINTELLIGENCEPLATFORM/
├── src/etl/
│   ├── normaliser.py         # normalize_ticker, normalize_year
│   ├── validator.py          # DQ-01 to DQ-16 rules
│   ├── loader.py             # Full ETL orchestration
│   └── schema.sql            # SQLite DDL (12 tables)
├── tests/etl/
│   └── test_normalise.py     # 48 unit tests
├── db/
│   └── schema.sql            # Schema reference copy
├── notebooks/
│   └── exploratory_queries.sql  # 10 analytical queries
├── config/
│   └── .env.template         # Environment variable template
├── download_data.py          # Downloads 12 source Excel files
├── requirements.txt          # Python dependencies
├── Makefile                  # make load | test | clean
└── .env                      # Runtime config (DB_PATH, PORT, LOG_LEVEL)
```

## Database Schema

12 tables with foreign key constraints enforced:

| Table | Description |
|---|---|
| `companies` | 92 Nifty 100 companies (master) |
| `sectors` | Sector classifications |
| `profitandloss` | Annual P&L statements |
| `balancesheet` | Annual balance sheets |
| `cashflow` | Annual cash flow statements |
| `analysis` | Compounded growth & ROE metrics |
| `documents` | Annual report PDF links |
| `prosandcons` | Analyst pros & cons |
| `stock_prices` | Monthly OHLCV price data |
| `market_cap` | Market cap & valuation multiples |
| `financial_ratios` | Pre-computed financial ratios |
| `peer_groups` | Peer group classifications |

## Data Quality Rules

16 DQ rules across CRITICAL, WARNING, and INFO severity levels covering:
PK uniqueness, FK integrity, year format, OPM cross-check, BS balance, net cash consistency, tax rate range, dividend cap, URL validity, EPS sign, coverage checks, and more.

## Makefile Targets

```bash
make load       # Run ETL pipeline
make test       # Run pytest
make ratios     # Sprint 2 — Ratio Engine
make report     # Sprint 5 — PDF Reports
make dashboard  # Sprint 4 — Streamlit Dashboard
make api        # Sprint 6 — FastAPI REST API
make clean      # Clean pycache and temp files
```

## Sprint Roadmap

| Sprint | Theme | Status |
|---|---|---|
| Sprint 1 (Day 01–07) | Data Foundation & ETL | ✅ Complete |
| Sprint 2 (Day 08–14) | Ratio Engine & Analytics | ✅ Complete |
| Sprint 3 (Day 15–21) | Screening & Scoring | ✅ Complete |
| Sprint 4 (Day 22–28) | Streamlit Dashboard & Valuation | ✅ Complete |
| Sprint 5 (Day 29–35) | PDF Reports & Exports | ✅ Complete |
| Sprint 6 (Day 36–42) | REST API & Deployment | 🔜 Planned |

## Dashboard Screens

The platform features an 8-screen Streamlit application accessible via sidebar navigation:

1. **🏠 01 Home Screen**: Displays aggregate market statistics (Average ROE, Median P/E, Median D/E, count of companies, CAGR, and Debt-Free companies), an interactive Plotly donut chart representing sector company counts, and a leaderboard table showing the top-5 companies sorted by composite quality score. All metrics filter dynamically based on a sidebar year selector (2019-2024).
2. **📊 02 Company Profile**: Autocomplete text search box to inspect any of the 92 companies. Shows a profile description card, a KPI metrics grid (latest year), a 10-year Bar Chart comparing Revenue and Net Profit, a dual-axis Line Chart showing ROE vs ROCE (computed dynamically), and analyst pros/cons badges.
3. **🔍 03 Screener Screen**: Multi-metric screening panel with 10 sidebar sliders. Includes 6 preset buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround) that auto-fill the sliders, a live-updating table, and a CSV download button to export the results.
4. **⚖️ 04 Peer Comparison**: benchmarking of any company against its peer group. Displays a Scatterpolar radar chart plotting the company's 8 normalized metrics vs the peer group average, and a side-by-side comparison table highlighting the group's benchmark company row in gold.
5. **📈 05 Trend Analysis**: overlay comparison for up to 3 metrics (e.g. Sales, Net Profit, ROE, ROCE, FCF) over 10 years on an interactive line chart, with automatically calculated YoY % changes annotated on each point.
6. **🍩 06 Sector Analysis**: bubble chart for the selected broad sector (X=Sales, Y=ROE, size=Market Cap, color=Sub-Sector) and a cross-sector median KPI comparison bar chart.
7. **🗺️ 07 Capital Allocation**: treemap grouping the 92 companies by the 8 cash flow patterns (Shareholder Returns, Reinvestor, Liquidating Assets, Distress Signal, etc.) using Plotly treemap. Clicking or selecting a pattern displays its members.
8. **📁 08 Annual Reports**: search-based list of available annual report years with clickable BSE PDF links. Displays a red "Report unavailable" badge for URLs that return 404.

---

*Built with ❤️ — Nifty 100 Financial Intelligence Platform*
