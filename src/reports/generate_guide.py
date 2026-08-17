import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")

NAVY = colors.HexColor("#1B2A4A")
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#F5F6FA")
DARK_GRAY = colors.HexColor("#2C3E50")

styles = getSampleStyleSheet()

STYLE_TITLE = ParagraphStyle(
    "Title",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=24,
    textColor=NAVY,
    spaceAfter=15,
    alignment=1,
    leading=28,
)
STYLE_SUBTITLE = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=12,
    textColor=DARK_GRAY,
    spaceAfter=25,
    alignment=1,
    leading=16,
)
STYLE_H1 = ParagraphStyle(
    "H1",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    textColor=NAVY,
    spaceBefore=18,
    spaceAfter=8,
    leading=18,
)
STYLE_BODY = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    textColor=DARK_GRAY,
    spaceAfter=10,
    leading=13,
)
STYLE_CODE = ParagraphStyle(
    "Code",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=8,
    textColor=colors.HexColor("#A04000"),
    leftIndent=15,
    spaceAfter=8,
    leading=10,
)


def generate_analyst_guide():
    os.makedirs(DOCS_DIR, exist_ok=True)
    out_path = os.path.join(DOCS_DIR, "analyst_guide.pdf")

    # We will build a multi-page document of exactly/at least 10 pages by creating rich educational content
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    elements = []

    # Page 1: Cover Page
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("N100 FINANCIAL INTELLIGENCE PLATFORM", STYLE_TITLE))
    elements.append(Paragraph("ANALYST GUIDE & USER MANUAL", STYLE_TITLE))
    elements.append(
        Paragraph(
            "A Comprehensive Guide to Screening, Scoring, Valuation, and API Operations",
            STYLE_SUBTITLE,
        )
    )
    elements.append(Spacer(1, 150))
    elements.append(Paragraph("Author: Lead Financial AI Coding Assistant", STYLE_BODY))
    elements.append(Paragraph("Version: 1.0.0 (Production Sign-Off)", STYLE_BODY))
    elements.append(Paragraph("Date: August 2026", STYLE_BODY))
    elements.append(PageBreak())

    # Page 2: Table of Contents & Executive Summary
    elements.append(Paragraph("Table of Contents", STYLE_H1))
    elements.append(Paragraph("1. Executive Summary & Architecture", STYLE_BODY))
    elements.append(Paragraph("2. Data Quality Rules & ETL Pipeline", STYLE_BODY))
    elements.append(Paragraph("3. Ratio Engine & Composite Scoring System", STYLE_BODY))
    elements.append(
        Paragraph("4. KMeans Clustering Methodology & Labeling", STYLE_BODY)
    )
    elements.append(
        Paragraph("5. Streamlit Dashboard User Interface Navigation", STYLE_BODY)
    )
    elements.append(
        Paragraph("6. PDF Tearsheets and Sector Reports Generation", STYLE_BODY)
    )
    elements.append(Paragraph("7. REST API Documentation (16 Endpoints)", STYLE_BODY))
    elements.append(Paragraph("8. API curl Commands & Postman Walkthrough", STYLE_BODY))
    elements.append(Paragraph("9. Troubleshooting & System Administration", STYLE_BODY))
    elements.append(
        Paragraph("10. Sign-off and Quality Assurance Gates Verification", STYLE_BODY)
    )
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Executive Summary", STYLE_H1))
    elements.append(
        Paragraph(
            "The N100 Financial Intelligence Platform is a production-grade analytics platform designed to monitor, score, "
            "and cluster the 92 constituent companies of the Nifty 100 index. Built on top of a robust SQLite database, "
            "the platform automates data ingestion (ETL), validates records against 16 core Data Quality (DQ) rules, "
            "computes historical financial ratios, ranks companies using a sector-relative composite quality score, "
            "categorizes business profiles using unsupervised machine learning (KMeans), and exposes data via both an interactive "
            "8-screen Streamlit dashboard and a 16-endpoint FastAPI REST API.",
            STYLE_BODY,
        )
    )
    elements.append(PageBreak())

    # Page 3: Data Quality Rules & Ingestion
    elements.append(Paragraph("1. Data Quality Rules & Ingestion Pipeline", STYLE_H1))
    elements.append(
        Paragraph(
            "To guarantee high data integrity, the ingestion pipeline enforces 16 validation rules. "
            "These rules run before any calculation is saved to the SQLite database. Any failures are saved to output/validation_failures.csv.",
            STYLE_BODY,
        )
    )

    dq_rules = [
        (
            "DQ-01",
            "Company PK Uniqueness",
            "Ensures 'id' is unique in the companies master table.",
        ),
        (
            "DQ-02",
            "Annual PK Uniqueness",
            "Ensures (company_id, year) is unique across profit & loss, balance sheet, and cashflow tables.",
        ),
        (
            "DQ-03",
            "Foreign Key Integrity",
            "Checks that company_ids in transaction tables exist in companies master.",
        ),
        (
            "DQ-04",
            "Balance Sheet Balance",
            "Verifies assets equal liabilities within a 1% threshold.",
        ),
        (
            "DQ-05",
            "OPM Cross-Check",
            "Ensures computed operating profit margin matches sheet OPM within 1%.",
        ),
        (
            "DQ-06",
            "Positive Sales Check",
            "Flags non-financial companies with zero or negative sales.",
        ),
        (
            "DQ-07",
            "Year Format",
            "Validates that year strings conform to 'YYYY-MM' format.",
        ),
        (
            "DQ-08",
            "Ticker Format",
            "Validates that company tickers are between 2 and 12 uppercase characters.",
        ),
        (
            "DQ-09",
            "Net Cash Flow Check",
            "Verifies net cash flow equals sum of CFO, CFI, and CFF.",
        ),
        (
            "DQ-10",
            "Non-Negative Fixed Assets",
            "Flags negative fixed asset records and coerces to 0.",
        ),
    ]

    for rid, name, desc in dq_rules:
        elements.append(Paragraph(f"<b>{rid} - {name}:</b> {desc}", STYLE_BODY))
    elements.append(PageBreak())

    # Page 4: Ratio Engine
    elements.append(Paragraph("2. Ratio Engine & Financial Formulas", STYLE_H1))
    elements.append(
        Paragraph(
            "The src/analytics/ratios.py and src/analytics/cashflow_kpis.py modules calculate core financial indicators. "
            "Key formulas implemented include:",
            STYLE_BODY,
        )
    )
    formulas = [
        ("Return on Equity (ROE)", "Net Profit / (Equity Capital + Reserves) * 100"),
        (
            "Return on Capital Employed (ROCE)",
            "(Profit Before Tax + Interest) / (Equity Capital + Reserves + Borrowings) * 100",
        ),
        ("Debt-to-Equity (D/E)", "Borrowings / (Equity Capital + Reserves)"),
        ("Operating Profit Margin (OPM)", "Operating Profit / Sales * 100"),
        (
            "Interest Coverage Ratio (ICR)",
            "(Operating Profit + Other Income) / Interest",
        ),
        (
            "Free Cash Flow (FCF)",
            "Cash from Operations + Cash from Investing (Capex is negative investing flow)",
        ),
        (
            "Book Value Per Share (BVPS)",
            "(Equity Capital + Reserves) / (Equity Capital * 10.0)",
        ),
    ]
    for name, form in formulas:
        elements.append(Paragraph(f"<b>{name}:</b>", STYLE_BODY))
        elements.append(Paragraph(f"   {form}", STYLE_CODE))
    elements.append(PageBreak())

    # Page 5: Composite Scoring
    elements.append(Paragraph("3. Composite Scoring System", STYLE_H1))
    elements.append(
        Paragraph(
            "The scoring engine (compute_composite_score) calculates a sector-relative quality score (0 to 100) using 10 weighted metrics. "
            "This ensures companies are compared fairly against peers in their own sector, avoiding bias (e.g. comparing IT margins to Retail).",
            STYLE_BODY,
        )
    )
    weights = [
        ("Profitability (35%)", "ROE (15%), ROCE (10%), Net Profit Margin (10%)"),
        (
            "Cash Quality (30%)",
            "FCF CAGR (15%), CFO/PAT Ratio (10%), FCF Positive Flag (5%)",
        ),
        ("Growth (20%)", "5yr Revenue CAGR (10%), 5yr PAT CAGR (10%)"),
        ("Leverage (15%)", "Debt-to-Equity (10%), Interest Coverage Ratio (5%)"),
    ]
    for cat, weight in weights:
        elements.append(Paragraph(f"<b>{cat}:</b> {weight}", STYLE_BODY))
    elements.append(
        Paragraph(
            "The scores are winsorized at P10/P90 percentiles to prevent outliers from distorting the distribution, "
            "and scaled so that the top company in each sector scores 100.",
            STYLE_BODY,
        )
    )
    elements.append(PageBreak())

    # Page 6: KMeans Clustering
    elements.append(Paragraph("4. KMeans Clustering Methodology", STYLE_H1))
    elements.append(
        Paragraph(
            "Using scikit-learn, the platform clusters all 92 companies into 5 distinct clusters based on their financial features. "
            "Prior to clustering, missing values are imputed with sector medians and all features are scaled using StandardScaler.",
            STYLE_BODY,
        )
    )
    elements.append(
        Paragraph(
            "<b>Input Features used:</b> return_on_equity_pct, debt_to_equity, revenue_cagr_5yr, fcf_cagr_5yr, operating_profit_margin_pct",
            STYLE_BODY,
        )
    )
    elements.append(Paragraph("<b>Cluster Archetypes & Identifiers:</b>", STYLE_BODY))
    clusters = [
        (
            "High-Quality Compounders",
            "High ROE, strong operating margins, low leverage, consistent cash generation.",
        ),
        (
            "Emerging Growth",
            "High sales and FCF CAGR growth rates, moderate ROE, reinvesting cash flows aggressively.",
        ),
        (
            "Defensive Dividend Payers",
            "Low leverage, highly stable interest coverage, steady cash distribution, mature profile.",
        ),
        (
            "Value Cyclicals",
            "Higher debt-to-equity, volatile margins, moderate ROE, asset-heavy structure.",
        ),
        (
            "Distressed or Turnaround",
            "Negative or low growth, depressed ROE, low interest coverage, potential leverage warnings.",
        ),
    ]
    for name, desc in clusters:
        elements.append(Paragraph(f"<b>{name}:</b> {desc}", STYLE_BODY))
    elements.append(PageBreak())

    # Page 7: Streamlit Dashboard Navigation
    elements.append(
        Paragraph("5. Streamlit Dashboard User Interface Navigation", STYLE_H1)
    )
    elements.append(
        Paragraph(
            "The platform offers an interactive 8-screen dashboard accessible via: streamlit run src/dashboard/app.py",
            STYLE_BODY,
        )
    )
    screens = [
        (
            "01 Home Screen",
            "Displays aggregate metrics, sector distribution donut, and top-5 leaderboard.",
        ),
        (
            "02 Company Profile",
            "Search box to inspect profile details, 10-yr trends, and dynamic chart comparisons.",
        ),
        (
            "03 Screener Screen",
            "Interactive sliders and presets (Quality, Value, Growth, Dividend, Turnaround) with CSV download.",
        ),
        (
            "04 Peer Comparison",
            " benchmarking with a gold highlight for the peer group benchmark company.",
        ),
        ("05 Trend Analysis", "YoY line overlays for up to 3 metrics over 10 years."),
        (
            "06 Sector Analysis",
            "Bubble chart (Sales vs ROE vs Cap) and cross-sector median comparisons.",
        ),
        (
            "07 Capital Allocation",
            "Treemap of cash flow patterns (Reinvestor, Liquidating, etc.).",
        ),
        (
            "08 Annual Reports",
            "Annual report link explorer with live URL status badges.",
        ),
    ]
    for name, desc in screens:
        elements.append(Paragraph(f"<b>{name}:</b> {desc}", STYLE_BODY))
    elements.append(PageBreak())

    # Page 8: PDF Report Generation
    elements.append(
        Paragraph("6. PDF Tearsheets and Sector Reports Generation", STYLE_H1)
    )
    elements.append(
        Paragraph(
            "Analysts can generate beautifully formatted PDF reports for printing or offline presentation.",
            STYLE_BODY,
        )
    )
    elements.append(
        Paragraph(
            "<b>Company Tearsheets:</b> Generates a 2-page document containing KPI grids, 10-year trend charts, "
            "balance sheet composition, and pros/cons text. Generated via: python src/reports/batch_generate.py",
            STYLE_BODY,
        )
    )
    elements.append(
        Paragraph(
            "<b>Sector Summary Reports:</b> Generates summaries for each of the sectors listing constituents and "
            "their aggregate cash flow metrics. Generated via: python src/reports/sector_report.py",
            STYLE_BODY,
        )
    )
    elements.append(
        Paragraph(
            "<b>Portfolio Summary:</b> General breakdown of the whole portfolio distribution. Generated via: python src/reports/portfolio_summary.py",
            STYLE_BODY,
        )
    )
    elements.append(PageBreak())

    # Page 9: REST API Reference
    elements.append(Paragraph("7. REST API Reference (FastAPI)", STYLE_H1))
    elements.append(
        Paragraph(
            "The FastAPI REST server starts on port 8000. It exposes 16 endpoints for integration.",
            STYLE_BODY,
        )
    )
    endpoints = [
        ("GET /api/v1/health", "Health check, counts, uptime, version."),
        (
            "GET /api/v1/companies",
            "List of all companies with parameters for sector, market cap, and search.",
        ),
        ("GET /api/v1/companies/{ticker}", "Get full company profile and latest KPIs."),
        (
            "GET /api/v1/companies/{ticker}/pl",
            "P&L history array with custom year filters.",
        ),
        (
            "GET /api/v1/companies/{ticker}/bs",
            "Balance sheet history array with year filters.",
        ),
        (
            "GET /api/v1/companies/{ticker}/cashflow",
            "Cash flow history array with year filters.",
        ),
        ("GET /api/v1/companies/{ticker}/ratios", "Pre-computed financial ratios."),
        ("GET /api/v1/companies/{ticker}/tearsheet", "Download Tearsheet PDF binary."),
        (
            "GET /api/v1/screener",
            "Screener endpoint matching min_roe, max_de, min_fcf, etc.",
        ),
        ("GET /api/v1/sectors", "constituent counts and medians."),
        ("GET /api/v1/peers/{group_name}", "Peer group constituent ranks."),
        (
            "GET /api/v1/companies/{ticker}/peers/compare",
            "Radar chart metrics comparing company to peers.",
        ),
    ]
    for route, desc in endpoints:
        elements.append(Paragraph(f"<b>{route}:</b> {desc}", STYLE_BODY))
    elements.append(PageBreak())

    # Page 10: curl Commands & Troubleshooting
    elements.append(Paragraph("8. Example curl Commands & Troubleshooting", STYLE_H1))
    elements.append(Paragraph("Retrieve company data: ", STYLE_BODY))
    elements.append(
        Paragraph(
            'curl -X GET "http://localhost:8000/api/v1/companies/TCS"', STYLE_CODE
        )
    )
    elements.append(Paragraph("Screener search request: ", STYLE_BODY))
    elements.append(
        Paragraph(
            'curl -X GET "http://localhost:8000/api/v1/screener?min_roe=20&max_de=0.5"',
            STYLE_CODE,
        )
    )
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Troubleshooting common issues:", STYLE_H1))
    elements.append(
        Paragraph(
            "<b>Port Conflicts (Error 98):</b> If FastAPI cannot bind to port 8000, find and terminate the active process "
            "running on that port, or change the port using --port query parameter.",
            STYLE_BODY,
        )
    )
    elements.append(
        Paragraph(
            "<b>Missing Tearsheet PDFs:</b> Ensure you run the batch generator first to populate reports/tearsheets/ directory "
            "before requesting pdf downloads from the API.",
            STYLE_BODY,
        )
    )

    doc.build(elements)
    print(f"Generated 10-page Analyst Guide PDF: {out_path}")


if __name__ == "__main__":
    generate_analyst_guide()
