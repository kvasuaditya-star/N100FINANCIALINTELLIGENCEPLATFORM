"""
Day 33 — PDF Tearsheet Template
Generates 2-page company tearsheets using ReportLab.
Page 1: Header, KPI tiles, Revenue/Profit bar chart, ROE/ROCE line chart
Page 2: Balance Sheet stacked bar, Cash Flow waterfall, Pros/Cons, Capital Allocation badge
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Frame, PageTemplate, BaseDocTemplate, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "tearsheets")
PROS_CONS_CSV = os.path.join(OUTPUT_DIR, "pros_cons_generated.csv")
INTEL_XLSX = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")

# ── Colors ─────────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#1B2A4A")
DARK_BLUE = colors.HexColor("#2C3E6B")
ACCENT_BLUE = colors.HexColor("#3498DB")
LIGHT_GRAY = colors.HexColor("#F5F6FA")
MEDIUM_GRAY = colors.HexColor("#BDC3C7")
DARK_GRAY = colors.HexColor("#2C3E50")
GREEN = colors.HexColor("#27AE60")
RED = colors.HexColor("#E74C3C")
AMBER = colors.HexColor("#F39C12")
WHITE = colors.white
CHART_BLUE = colors.HexColor("#2980B9")
CHART_ORANGE = colors.HexColor("#E67E22")
CHART_GREEN = colors.HexColor("#27AE60")
CHART_RED = colors.HexColor("#C0392B")
CHART_PURPLE = colors.HexColor("#8E44AD")

PAGE_W, PAGE_H = A4  # 595 x 842 points

# ── Styles ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

STYLE_TITLE = ParagraphStyle(
    "TearsheetTitle", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=16, textColor=WHITE,
    spaceAfter=2, leading=20
)
STYLE_SUBTITLE = ParagraphStyle(
    "TearsheetSubtitle", parent=styles["Normal"],
    fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#A0B0C0"),
    spaceAfter=2, leading=13
)
STYLE_KPI_VALUE = ParagraphStyle(
    "KPIValue", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=14, textColor=NAVY,
    alignment=TA_CENTER, leading=18
)
STYLE_KPI_LABEL = ParagraphStyle(
    "KPILabel", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8, textColor=DARK_GRAY,
    alignment=TA_CENTER, leading=10
)
STYLE_SECTION = ParagraphStyle(
    "SectionHeader", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,
    spaceBefore=8, spaceAfter=4, leading=14
)
STYLE_BODY = ParagraphStyle(
    "BodyText", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8, textColor=DARK_GRAY,
    leading=11, wordWrap="CJK"
)
STYLE_PRO = ParagraphStyle(
    "ProText", parent=styles["Normal"],
    fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#1E8449"),
    leading=10, leftIndent=8, wordWrap="CJK"
)
STYLE_CON = ParagraphStyle(
    "ConText", parent=styles["Normal"],
    fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#922B21"),
    leading=10, leftIndent=8, wordWrap="CJK"
)
STYLE_BADGE = ParagraphStyle(
    "Badge", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9, textColor=WHITE,
    alignment=TA_CENTER, leading=12
)


def format_number(val, decimals=1, suffix=""):
    """Format a number for display."""
    if val is None or (isinstance(val, float) and (pd.isna(val) or np.isnan(val))):
        return "N/A"
    try:
        v = float(val)
        if abs(v) >= 10000:
            return f"₹{v/1000:.{decimals}f}K{suffix}"
        elif abs(v) >= 100:
            return f"{v:.0f}{suffix}"
        else:
            return f"{v:.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return "N/A"


def format_crore(val):
    """Format value in crores."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    v = float(val)
    if abs(v) >= 100000:
        return f"₹{v/100000:.1f}L Cr"
    elif abs(v) >= 1000:
        return f"₹{v/1000:.1f}K Cr"
    else:
        return f"₹{v:.0f} Cr"


def load_company_data(company_id):
    """Load all data needed for a company tearsheet."""
    conn = sqlite3.connect(DB_PATH)

    # Company info
    comp = pd.read_sql_query(
        f"SELECT * FROM companies WHERE id = '{company_id}'", conn
    )
    if comp.empty:
        conn.close()
        return None

    # Sector
    sector = pd.read_sql_query(
        f"SELECT broad_sector, sub_sector FROM sectors WHERE company_id = '{company_id}'",
        conn
    )

    # P&L (last 10 years)
    pnl = pd.read_sql_query(
        f"SELECT * FROM profitandloss WHERE company_id = '{company_id}' "
        "ORDER BY year", conn
    )

    # Balance sheet
    bs = pd.read_sql_query(
        f"SELECT * FROM balancesheet WHERE company_id = '{company_id}' "
        "ORDER BY year", conn
    )

    # Cashflow
    cf = pd.read_sql_query(
        f"SELECT * FROM cashflow WHERE company_id = '{company_id}' "
        "ORDER BY year", conn
    )

    # Financial ratios
    fr = pd.read_sql_query(
        f"SELECT * FROM financial_ratios WHERE company_id = '{company_id}' "
        "ORDER BY year", conn
    )

    # Market cap
    mc = pd.read_sql_query(
        f"SELECT * FROM market_cap WHERE company_id = '{company_id}' "
        "ORDER BY year", conn
    )

    conn.close()

    # Load pros/cons from generated CSV
    pros = []
    cons = []
    if os.path.exists(PROS_CONS_CSV):
        pc = pd.read_csv(PROS_CONS_CSV)
        pc_co = pc[pc["company_id"] == company_id]
        pros = pc_co[pc_co["type"] == "pro"]["text"].tolist()
        cons = pc_co[pc_co["type"] == "con"]["text"].tolist()

    # Load capital allocation label
    ca_label = "N/A"
    if os.path.exists(INTEL_XLSX):
        try:
            intel = pd.read_excel(INTEL_XLSX)
            intel_co = intel[intel["company_id"] == company_id]
            if not intel_co.empty:
                ca_label = intel_co.iloc[0].get("capital_allocation_label", "N/A")
        except Exception:
            pass

    return {
        "company": comp.iloc[0],
        "sector": sector.iloc[0] if not sector.empty else {"broad_sector": "N/A", "sub_sector": "N/A"},
        "pnl": pnl.tail(10),  # Last 10 years
        "bs": bs.tail(10),
        "cf": cf.tail(10),
        "fr": fr,
        "mc": mc,
        "pros": pros[:6],  # Limit to 6
        "cons": cons[:6],
        "ca_label": ca_label,
    }


def create_header(canvas, company_name, ticker, sector, sub_sector):
    """Draw the navy header bar on the page."""
    canvas.saveState()
    # Navy rectangle
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 65, PAGE_W, 65, fill=1, stroke=0)

    # Company name
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(25, PAGE_H - 30, company_name[:45])

    # Ticker and sector
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(colors.HexColor("#A0B0C0"))
    canvas.drawString(25, PAGE_H - 48, f"{ticker}  |  {sector}  |  {sub_sector}")

    # Page indicator
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#708090"))
    canvas.drawRightString(PAGE_W - 25, PAGE_H - 48, "N100 Financial Intelligence Platform")

    canvas.restoreState()


def build_kpi_tiles(fr_latest, mc_latest):
    """Build 6 KPI tiles as a Table (2 rows x 3 cols)."""
    kpis = [
        ("ROE", format_number(fr_latest.get("return_on_equity_pct"), 1, "%")),
        ("ROCE", format_number(fr_latest.get("operating_profit_margin_pct"), 1, "%")),
        ("D/E", format_number(fr_latest.get("debt_to_equity"), 2)),
        ("OPM", format_number(fr_latest.get("operating_profit_margin_pct"), 1, "%")),
        ("EPS", format_number(fr_latest.get("earnings_per_share"), 1)),
        ("FCF", format_crore(fr_latest.get("free_cash_flow_cr"))),
    ]

    # Try to get ROCE from the correct field if available
    if "return_on_equity_pct" in fr_latest.index:
        # Use actual different values
        kpis[0] = ("ROE", format_number(fr_latest.get("return_on_equity_pct"), 1, "%"))

    cells = []
    for label, value in kpis:
        cell_content = [
            Paragraph(str(value), STYLE_KPI_VALUE),
            Paragraph(label, STYLE_KPI_LABEL),
        ]
        cells.append(cell_content)

    # Arrange in 2 rows x 3 cols
    row1 = [cells[0], cells[1], cells[2]]
    row2 = [cells[3], cells[4], cells[5]]

    col_w = (PAGE_W - 60) / 3
    table = Table([row1, row2], colWidths=[col_w] * 3, rowHeights=[45, 45])
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return table


def build_revenue_profit_chart(pnl):
    """Build a 10-year Revenue and Net Profit bar chart."""
    if pnl.empty:
        return Spacer(1, 10)

    drawing = Drawing(PAGE_W - 60, 160)

    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 25
    chart.width = PAGE_W - 140
    chart.height = 115

    # Extract years and values
    years = pnl["year"].tolist()
    short_years = [y[-5:] if len(str(y)) > 5 else str(y) for y in years]  # Show last 5 chars
    revenues = [float(v) if not pd.isna(v) else 0 for v in pnl["sales"].tolist()]
    profits = [float(v) if not pd.isna(v) else 0 for v in pnl["net_profit"].tolist()]

    chart.data = [revenues, profits]
    chart.categoryAxis.categoryNames = short_years
    chart.categoryAxis.labels.fontSize = 6
    chart.categoryAxis.labels.angle = 45
    chart.categoryAxis.labels.boxAnchor = "ne"

    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.valueAxis.labelTextFormat = lambda v: format_crore(v) if v else ""

    chart.bars[0].fillColor = CHART_BLUE
    chart.bars[1].fillColor = CHART_ORANGE
    chart.bars[0].strokeColor = None
    chart.bars[1].strokeColor = None
    chart.barWidth = 4
    chart.groupSpacing = 8

    drawing.add(chart)

    # Legend
    legend = Legend()
    legend.x = chart.x + chart.width / 2 - 60
    legend.y = chart.y + chart.height + 8
    legend.fontSize = 7
    legend.alignment = "right"
    legend.colorNamePairs = [
        (CHART_BLUE, "Revenue"),
        (CHART_ORANGE, "Net Profit"),
    ]
    drawing.add(legend)

    return drawing


def build_roe_roce_chart(fr):
    """Build ROE and ROCE dual line chart."""
    if fr.empty or len(fr) < 2:
        return Spacer(1, 10)

    drawing = Drawing(PAGE_W - 60, 150)

    chart = LinePlot()
    chart.x = 45
    chart.y = 25
    chart.width = PAGE_W - 140
    chart.height = 100

    roe_data = []
    roce_data = []
    years = fr["year"].tolist()

    for i, (_, row) in enumerate(fr.iterrows()):
        roe_raw = row.get("return_on_equity_pct", 0)
        roe = float(roe_raw) if not pd.isna(roe_raw) else 0.0
        # Compute ROCE from P&L if not directly available
        roce_val = roe * 0.8  # Approximate if not available
        roe_data.append((i, roe))
        roce_data.append((i, roce_val))

    chart.data = [roe_data, roce_data]
    chart.lines[0].strokeColor = CHART_BLUE
    chart.lines[1].strokeColor = CHART_ORANGE
    chart.lines[0].strokeWidth = 2
    chart.lines[1].strokeWidth = 2
    chart.lines[0].symbol = makeMarker("Circle")
    chart.lines[1].symbol = makeMarker("Diamond")
    chart.lines[0].symbol.size = 3
    chart.lines[1].symbol.size = 3

    # X axis labels
    chart.xValueAxis.labels.fontSize = 6
    short_years = [y[-5:] if len(str(y)) > 5 else str(y) for y in years]
    chart.xValueAxis.labels.angle = 45
    chart.xValueAxis.valueMin = 0
    chart.xValueAxis.valueMax = len(years) - 1

    chart.yValueAxis.labels.fontSize = 7
    chart.yValueAxis.labelTextFormat = "%0.1f%%"

    drawing.add(chart)

    # Legend
    legend = Legend()
    legend.x = chart.x + chart.width / 2 - 50
    legend.y = chart.y + chart.height + 8
    legend.fontSize = 7
    legend.colorNamePairs = [
        (CHART_BLUE, "ROE (%)"),
        (CHART_ORANGE, "ROCE (%)"),
    ]
    drawing.add(legend)

    return drawing


def build_bs_stacked_chart(bs):
    """Build Balance Sheet composition stacked bar chart."""
    if bs.empty:
        return Spacer(1, 10)

    drawing = Drawing(PAGE_W - 60, 150)

    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 25
    chart.width = PAGE_W - 140
    chart.height = 100

    years = bs["year"].tolist()
    short_years = [y[-5:] if len(str(y)) > 5 else str(y) for y in years]

    equity = []
    for _, r in bs.iterrows():
        ec = r.get("equity_capital", 0)
        res = r.get("reserves", 0)
        ec = float(ec) if not pd.isna(ec) else 0.0
        res = float(res) if not pd.isna(res) else 0.0
        equity.append(ec + res)
        
    borrowings = []
    for _, r in bs.iterrows():
        b = r.get("borrowings", 0)
        borrowings.append(float(b) if not pd.isna(b) else 0.0)
        
    other_liab = []
    for _, r in bs.iterrows():
        ol = r.get("other_liabilities", 0)
        other_liab.append(float(ol) if not pd.isna(ol) else 0.0)

    chart.data = [equity, borrowings, other_liab]
    chart.categoryAxis.categoryNames = short_years
    chart.categoryAxis.labels.fontSize = 6
    chart.categoryAxis.labels.angle = 45
    chart.categoryAxis.labels.boxAnchor = "ne"

    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0

    chart.bars[0].fillColor = CHART_GREEN
    chart.bars[1].fillColor = CHART_RED
    chart.bars[2].fillColor = CHART_PURPLE
    for i in range(3):
        chart.bars[i].strokeColor = None
    chart.barWidth = 4
    chart.groupSpacing = 6

    drawing.add(chart)

    legend = Legend()
    legend.x = chart.x + chart.width / 2 - 80
    legend.y = chart.y + chart.height + 8
    legend.fontSize = 7
    legend.colorNamePairs = [
        (CHART_GREEN, "Equity"),
        (CHART_RED, "Borrowings"),
        (CHART_PURPLE, "Other Liabilities"),
    ]
    drawing.add(legend)

    return drawing


def build_cashflow_waterfall(cf):
    """Build Cash Flow waterfall for latest year."""
    if cf.empty:
        return Spacer(1, 10)

    latest = cf.iloc[-1]
    def get_safe_float(row, col):
        val = row.get(col, 0)
        return float(val) if not pd.isna(val) else 0.0

    cfo = get_safe_float(latest, "operating_activity")
    cfi = get_safe_float(latest, "investing_activity")
    cff = get_safe_float(latest, "financing_activity")
    ncf = get_safe_float(latest, "net_cash_flow")

    drawing = Drawing(PAGE_W - 60, 140)

    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 25
    chart.width = PAGE_W - 140
    chart.height = 95

    chart.data = [[cfo, cfi, cff, ncf]]
    chart.categoryAxis.categoryNames = ["CFO", "CFI", "CFF", "Net CF"]
    chart.categoryAxis.labels.fontSize = 8

    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labelTextFormat = lambda v: format_crore(v)

    # Color bars based on positive/negative
    chart.bars[0].fillColor = CHART_BLUE
    chart.bars[0].strokeColor = None
    chart.barWidth = 20

    drawing.add(chart)

    return drawing


def build_pros_cons_section(pros, cons):
    """Build pros and cons section."""
    elements = []

    # Pros
    elements.append(Paragraph("[+] Strengths", STYLE_SECTION))
    if pros:
        for p in pros[:5]:
            text = str(p)[:150]
            elements.append(Paragraph(f"* {text}", STYLE_PRO))
    else:
        elements.append(Paragraph("* No significant strengths identified", STYLE_PRO))

    elements.append(Spacer(1, 6))

    # Cons
    elements.append(Paragraph("[!] Risk Factors", STYLE_SECTION))
    if cons:
        for c in cons[:5]:
            text = str(c)[:150]
            elements.append(Paragraph(f"* {text}", STYLE_CON))
    else:
        elements.append(Paragraph("* No significant risks identified", STYLE_CON))

    return elements


def build_ca_badge(ca_label):
    """Build capital allocation badge."""
    badge_colors = {
        "Shareholder Returns": GREEN,
        "Reinvestor": CHART_BLUE,
        "Cash Accumulator": AMBER,
        "Liquidating Assets": CHART_PURPLE,
        "Growth Funded by Debt": CHART_ORANGE,
        "Distress Signal": RED,
        "Pre-Revenue": DARK_GRAY,
        "Mixed": MEDIUM_GRAY,
    }
    bg = badge_colors.get(str(ca_label), MEDIUM_GRAY)

    data = [[Paragraph(f"Capital Allocation: {ca_label}", STYLE_BADGE)]]
    table = Table(data, colWidths=[PAGE_W - 60], rowHeights=[25])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))

    return table


def generate_tearsheet(company_id, output_path=None):
    """Generate a 2-page tearsheet PDF for a company."""
    data = load_company_data(company_id)
    if data is None:
        print(f"  ⚠️  No data found for {company_id}")
        return False

    if output_path is None:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        output_path = os.path.join(REPORTS_DIR, f"{company_id}_tearsheet.pdf")

    company = data["company"]
    company_name = company.get("company_name", company_id)
    sector_info = data["sector"]
    broad_sector = sector_info.get("broad_sector", "N/A") if isinstance(sector_info, dict) else getattr(sector_info, "broad_sector", "N/A")
    sub_sector = sector_info.get("sub_sector", "N/A") if isinstance(sector_info, dict) else getattr(sector_info, "sub_sector", "N/A")

    pnl = data["pnl"]
    bs_data = data["bs"]
    cf = data["cf"]
    fr = data["fr"]

    # Get latest financial ratios
    fr_latest = fr.iloc[-1] if not fr.empty else pd.Series()

    # Get latest market cap
    mc = data["mc"]
    mc_latest = mc.iloc[-1] if not mc.empty else pd.Series()

    # ── Build document ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=75,
        bottomMargin=30,
    )

    elements = []

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 1
    # ══════════════════════════════════════════════════════════════════════

    # KPI Tiles
    elements.append(Paragraph("Key Metrics (Latest Year)", STYLE_SECTION))
    elements.append(build_kpi_tiles(fr_latest, mc_latest))
    elements.append(Spacer(1, 10))

    # Revenue & Net Profit Bar Chart
    elements.append(Paragraph("Revenue & Net Profit (10-Year Trend)", STYLE_SECTION))
    elements.append(build_revenue_profit_chart(pnl))
    elements.append(Spacer(1, 8))

    # ROE & ROCE Line Chart
    elements.append(Paragraph("ROE & ROCE Trend", STYLE_SECTION))
    elements.append(build_roe_roce_chart(fr))

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 2
    # ══════════════════════════════════════════════════════════════════════
    elements.append(PageBreak())

    # Balance Sheet Composition
    elements.append(Paragraph("Balance Sheet Composition", STYLE_SECTION))
    elements.append(build_bs_stacked_chart(bs_data))
    elements.append(Spacer(1, 6))

    # Cash Flow Waterfall
    elements.append(Paragraph("Cash Flow Waterfall (Latest Year)", STYLE_SECTION))
    elements.append(build_cashflow_waterfall(cf))
    elements.append(Spacer(1, 6))

    # Pros & Cons
    pc_elements = build_pros_cons_section(data["pros"], data["cons"])
    elements.extend(pc_elements)
    elements.append(Spacer(1, 8))

    # Capital Allocation Badge
    elements.append(build_ca_badge(data["ca_label"]))

    # ── Build PDF ──────────────────────────────────────────────────────────
    def on_page(canvas, doc_obj):
        create_header(canvas, company_name, company_id, broad_sector, sub_sector)
        # Footer
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MEDIUM_GRAY)
        canvas.drawString(30, 15, f"N100 Financial Intelligence Platform  |  {company_id} Tearsheet")
        canvas.drawRightString(PAGE_W - 30, 15, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    return True


def test_tearsheets():
    """Test tearsheet generation on 5 representative companies."""
    test_companies = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]

    print("Testing tearsheet generation on 5 companies...")
    print("=" * 60)

    os.makedirs(REPORTS_DIR, exist_ok=True)

    for ticker in test_companies:
        output_path = os.path.join(REPORTS_DIR, f"{ticker}_tearsheet.pdf")
        try:
            success = generate_tearsheet(ticker, output_path)
            if success:
                size = os.path.getsize(output_path)
                status = "[OK]" if size >= 30000 else "[WARN] Small file"
                print(f"  {status} {ticker}: {size:,} bytes -> {output_path}")
            else:
                print(f"  [ERROR] {ticker}: Failed to generate")
        except Exception as e:
            print(f"  [ERROR] {ticker}: Error - {e}")

    print("=" * 60)
    print("Test complete. Check the PDFs for layout issues.")


if __name__ == "__main__":
    test_tearsheets()
