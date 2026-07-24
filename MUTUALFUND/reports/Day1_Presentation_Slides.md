# Mutual Fund Analytics: Day 1 Presentation

---

## Slide 1: Title Slide
**Title:** Mutual Fund Data Analytics Platform  
**Subtitle:** Day 1: Project Setup & Automated Data Ingestion  
**Presenter:** [Your Name / Team]  

---

## Slide 2: Project Vision & Objectives
**Heading:** Building an End-to-End Analytics Platform
* **Objective:** Ingest, process, and analyze Indian mutual fund data.
* **Core Components:**
  * Automated ETL (Extract, Transform, Load) Pipeline.
  * Robust relational database schema (SQLite/PostgreSQL).
  * Interactive Dashboards (Power BI/Tableau).
* **Goal:** Deliver actionable insights on fund performance, investor demographics, and AUM trends.

---

## Slide 3: Day 1 Milestones Achieved
**Heading:** Setting the Foundation
* **Project Initialization:** Standardized data engineering folder structures created.
* **Version Control:** Local Git repository initialized and successfully linked/pushed to GitHub.
* **Environment Setup:** Dependency management established via `requirements.txt`.
* **Data Ingestion:** Automated Python scripts written to extract live API data.
* **Data Exploration:** Automated loading and profiling of 10 initial datasets.

---

## Slide 4: Project Architecture
**Heading:** Structured Data Organization
* **`data/raw/`**: Immutable storage for downloaded CSVs and API responses.
* **`data/processed/`**: Cleaned, transformed data ready for the database.
* **`sql/`**: Schema definitions and analytic queries.
* **`notebooks/`**: Exploratory Data Analysis (EDA) and prototyping.
* **`dashboard/` & `reports/`**: Final visualizations and PDF summaries.

---

## Slide 5: Live API Integration
**Heading:** Dynamic Data Ingestion (`mfapi.in`)
* **Process:** Created `etl_pipeline.py` using the `requests` and `pandas` libraries.
* **Target:** Automatically fetched live historical NAV data for 6 key schemes.
* **Schemes Included:** 
  * HDFC Top 100
  * SBI Bluechip
  * ICICI Bluechip
  * Nippon Large Cap
  * Axis Bluechip
  * Kotak Bluechip
* **Result:** JSON responses successfully parsed and stored directly as raw CSVs.

---

## Slide 6: Automated Data Exploration
**Heading:** Dataset Profiling
* **Process:** Created `data_exploration.py` to systematically load 10 core CSV files.
* **Metrics Captured:** Data shapes, data types (dtypes), and previewing data headers.
* **Anomaly Detection:** Programmatically checked for missing values across all datasets.
  * *Finding:* `04_monthly_sip_inflows.csv` contained 12 missing values in Year-over-Year growth (expected for first-year data). All other datasets clean.

---

## Slide 7: Deep Dive: Fund Master
**Heading:** Understanding the Core Metadata
* **Analysis:** Targeted extraction on `01_fund_master.csv`.
* **Key Findings:**
  * **AMCs:** 10 major Fund Houses identified (SBI, HDFC, ICICI, etc.).
  * **Categories:** Split broadly into Equity and Debt.
  * **Sub-Categories:** Ranging from Large Cap, Small Cap, to Liquid and Gilt.
  * **Scheme Codes:** AMFI structure validated as strictly numeric (`int64`).

---

## Slide 8: Next Steps
**Heading:** Looking Ahead to Day 2
* **Data Cleaning:** Handle missing values, normalize date formats, and clean string inconsistencies.
* **Database Design:** Establish the Star Schema architecture (Fact and Dimension tables).
* **Database Load:** Use SQLAlchemy to load the processed DataFrames into a local SQLite/PostgreSQL database.
* **Advanced EDA:** Transition to Jupyter Notebooks to plot initial performance metrics.
