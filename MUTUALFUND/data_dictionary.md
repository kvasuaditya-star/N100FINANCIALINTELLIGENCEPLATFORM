# Data Dictionary — Bluestock Mutual Fund Analytics

This document describes all tables and columns in the `bluestock_mf.db` SQLite database.

---

## 1. dim_fund (Fund Master)

| Column | Data Type | Description |
|---|---|---|
| `amfi_code` | TEXT (PK) | Unique AMFI code assigned to each mutual fund scheme |
| `fund_house` | TEXT | Name of the Asset Management Company (e.g., SBI Mutual Fund) |
| `scheme_name` | TEXT | Full name of the mutual fund scheme |
| `category` | TEXT | Broad category (Equity, Debt, Hybrid, etc.) |
| `sub_category` | TEXT | Sub-category (Large Cap, Mid Cap, etc.) |
| `plan` | TEXT | Plan type — Direct or Regular |
| `launch_date` | DATE | Date when the scheme was launched |
| `benchmark` | TEXT | Benchmark index used for performance comparison |
| `expense_ratio_pct` | REAL | Annual expense ratio as a percentage |
| `exit_load_pct` | REAL | Exit load charged on early redemption (%) |
| `min_sip_amount` | REAL | Minimum SIP investment amount in INR |
| `min_lumpsum_amount` | REAL | Minimum lumpsum investment amount in INR |
| `fund_manager` | TEXT | Name of the fund manager |
| `risk_category` | TEXT | Risk classification (Low, Moderate, High, Very High) |
| `sebi_category_code` | TEXT | SEBI classification code |

**Source:** `01_fund_master.csv`

---

## 2. fact_nav (NAV History)

| Column | Data Type | Description |
|---|---|---|
| `amfi_code` | TEXT (PK, FK → dim_fund) | AMFI code of the scheme |
| `date` | DATE (PK) | Date of the NAV record |
| `nav` | REAL | Net Asset Value on that date |

**Source:** `02_nav_history.csv`
**Cleaning:** Dates parsed, sorted by amfi_code + date, NAV forward-filled for holidays/weekends, duplicates removed, NAV > 0 validated.

---

## 3. fact_aum (AUM by Fund House)

| Column | Data Type | Description |
|---|---|---|
| `date` | DATE | Reporting date (typically quarter-end) |
| `fund_house` | TEXT | Name of the fund house |
| `aum_lakh_crore` | REAL | AUM in lakh crores (₹) |
| `aum_crore` | REAL | AUM in crores (₹) |
| `num_schemes` | INTEGER | Number of active schemes |

**Source:** `03_aum_by_fund_house.csv`

---

## 4. monthly_sip_inflows

| Column | Data Type | Description |
|---|---|---|
| `month` | TEXT | Month in YYYY-MM format |
| `sip_inflow_crore` | REAL | Total SIP inflow for the month in crores (₹) |
| `active_sip_accounts_crore` | REAL | Number of active SIP accounts in crores |
| `new_sip_accounts_lakh` | REAL | New SIP accounts registered in lakhs |
| `sip_aum_lakh_crore` | REAL | SIP AUM in lakh crores (₹) |
| `yoy_growth_pct` | REAL | Year-over-year growth percentage |

**Source:** `04_monthly_sip_inflows.csv`

---

## 5. category_inflows

| Column | Data Type | Description |
|---|---|---|
| `month` | TEXT | Month in YYYY-MM format |
| `category` | TEXT | Fund category (Large Cap, Mid Cap, Small Cap, etc.) |
| `net_inflow_crore` | REAL | Net inflow for the category in crores (₹) |

**Source:** `05_category_inflows.csv`

---

## 6. industry_folio_count

| Column | Data Type | Description |
|---|---|---|
| `month` | TEXT | Month in YYYY-MM format |
| `total_folios_crore` | REAL | Total investor folios in crores |
| `equity_folios_crore` | REAL | Equity fund folios in crores |
| `debt_folios_crore` | REAL | Debt fund folios in crores |
| `hybrid_folios_crore` | REAL | Hybrid fund folios in crores |
| `others_folios_crore` | REAL | Other fund folios in crores |

**Source:** `06_industry_folio_count.csv`

---

## 7. fact_performance (Scheme Performance)

| Column | Data Type | Description |
|---|---|---|
| `amfi_code` | TEXT (PK, FK → dim_fund) | AMFI code of the scheme |
| `scheme_name` | TEXT | Full scheme name |
| `fund_house` | TEXT | Fund house name |
| `category` | TEXT | Fund category |
| `plan` | TEXT | Direct or Regular plan |
| `return_1yr_pct` | REAL | 1-year trailing return (%) |
| `return_3yr_pct` | REAL | 3-year annualised return (%) |
| `return_5yr_pct` | REAL | 5-year annualised return (%) |
| `benchmark_3yr_pct` | REAL | Benchmark 3-year return (%) |
| `alpha` | REAL | Alpha (excess return over benchmark) |
| `beta` | REAL | Beta (market sensitivity) |
| `sharpe_ratio` | REAL | Sharpe ratio (risk-adjusted return) |
| `sortino_ratio` | REAL | Sortino ratio (downside risk-adjusted return) |
| `std_dev_ann_pct` | REAL | Annualised standard deviation (%) |
| `max_drawdown_pct` | REAL | Maximum drawdown from peak (%) |
| `aum_crore` | REAL | Assets under management in crores (₹) |
| `expense_ratio_pct` | REAL | Expense ratio (%) — validated range: 0.1%–2.5% |
| `morningstar_rating` | TEXT | Morningstar star rating |
| `risk_grade` | TEXT | Risk grade (Low, Moderate, High) |
| `negative_sharpe_flag` | INTEGER | 1 if Sharpe ratio is negative, 0 otherwise |

**Source:** `07_scheme_performance.csv`
**Cleaning:** Return columns forced to numeric, negative Sharpe flagged, expense ratio filtered to 0.1%–2.5%.

---

## 8. fact_transactions (Investor Transactions)

| Column | Data Type | Description |
|---|---|---|
| `investor_id` | TEXT | Unique investor identifier |
| `transaction_date` | DATE | Date of the transaction |
| `amfi_code` | TEXT (FK → dim_fund) | AMFI code of the scheme |
| `transaction_type` | TEXT | Type: SIP, Lumpsum, or Redemption |
| `amount_inr` | REAL | Transaction amount in INR |
| `state` | TEXT | Indian state of the investor |
| `city` | TEXT | City of the investor |
| `city_tier` | TEXT | City tier classification (Tier 1, Tier 2, Tier 3) |
| `age_group` | TEXT | Age bracket of the investor |
| `gender` | TEXT | Gender of the investor |
| `annual_income_lakh` | TEXT | Annual income bracket in lakhs |
| `payment_mode` | TEXT | Payment method (UPI, NetBanking, Cheque, etc.) |
| `kyc_status` | TEXT | KYC verification status: Verified, Pending, Rejected, or Unknown |

**Source:** `08_investor_transactions.csv`
**Cleaning:** Transaction types standardised, amount > 0 validated, dates parsed, KYC enum validated.

---

## 9. portfolio_holdings

| Column | Data Type | Description |
|---|---|---|
| `amfi_code` | TEXT (FK → dim_fund) | AMFI code of the scheme |
| `stock_symbol` | TEXT | Stock ticker symbol (e.g., HDFCBANK) |
| `stock_name` | TEXT | Full stock name |
| `sector` | TEXT | Industry sector |
| `weight_pct` | REAL | Weight of the stock in the portfolio (%) |
| `market_value_cr` | REAL | Market value of the holding in crores (₹) |
| `current_price_inr` | REAL | Current stock price in INR |
| `portfolio_date` | DATE | Date of the portfolio snapshot |

**Source:** `09_portfolio_holdings.csv`

---

## 10. benchmark_indices

| Column | Data Type | Description |
|---|---|---|
| `date` | DATE | Trading date |
| `index_name` | TEXT | Index name (e.g., NIFTY50, SENSEX) |
| `close_value` | REAL | Closing value of the index |

**Source:** `10_benchmark_indices.csv`
