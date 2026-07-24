import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_PDF_PATH = REPORTS_DIR / "Final_Report.pdf"

# Install reportlab if not available
try:
    import reportlab
except ImportError:
    print("ReportLab not found. Installing via pip...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# NumberedCanvas for professional "Page X of Y" headers/footers
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_elements(self, page_count):
        self.saveState()
        
        # Suppress headers/footers on Slide/Title cover page (page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#00b4d8"))
            self.drawString(54, 750, "BLUESTOCK MUTUAL FUND ANALYTICS")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawRightString(letter[0] - 54, 750, "CAPSTONE TECHNICAL REPORT")
            
            # Header rule
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 742, letter[0] - 54, 742)
            
            # Footer rule
            self.line(54, 60, letter[0] - 54, 60)
            self.drawString(54, 45, "Confidential - For Internal Use Only")
            self.drawRightString(letter[0] - 54, 45, f"Page {self._pageNumber} of {page_count}")
            
        self.restoreState()

def generate_pdf():
    print("Generating Capstone PDF Report...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Establish DB queries
    if not DB_PATH.exists():
        print("Database does not exist. Run ETL pipeline first.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # Load performance rankings
    ranked_funds = pd.read_sql_query("""
        SELECT scheme_name, category, return_3yr_pct, sharpe_ratio, risk_grade, aum_crore
        FROM fact_performance
        ORDER BY return_3yr_pct DESC
        LIMIT 8
    """, conn)
    
    # Load HHI Concentration rankings
    hhi_data = pd.read_sql_query("""
        SELECT scheme_name, category, std_dev_ann_pct, morningstar_rating, risk_grade
        FROM fact_performance
        WHERE category = 'Equity'
        ORDER BY std_dev_ann_pct DESC
        LIMIT 5
    """, conn)
    
    conn.close()
    
    # PDF Setup
    # 0.75in margins = 54 pt
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF_PATH),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor("#12121e")
    secondary_color = colors.HexColor("#00b4d8")
    text_color = colors.HexColor("#2d3748")
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=primary_color,
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#718096"),
        alignment=1, # Center
        spaceAfter=40
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=text_color
    )
    
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    story = []
    
    # ==================== PAGE 1: COVER PAGE ====================
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("BLUESTOCK MUTUAL FUND ANALYTICS", title_style))
    story.append(Paragraph("A Unified Quantitative Evaluation, Data Cleaning Pipeline & Portfolio Optimisation Framework", subtitle_style))
    story.append(Spacer(1, 0.5 * inch))
    
    # Metadata Block Table
    meta_data = [
        [Paragraph("<b>Deliverable Reference:</b> D7 - Final Capstone Technical Report", body_style)],
        [Paragraph("<b>Date:</b> July 10, 2026", body_style)],
        [Paragraph("<b>Platform Config:</b> Python, SQLite, ReportLab, Streamlit, Git", body_style)],
        [Paragraph("<b>GitHub Target:</b> MUTUALFUNDSDATAANALYTICS", body_style)],
        [Paragraph("<b>Author Profile:</b> Quant Engineering Cohort", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[4*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f7fafc")),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#edf2f7")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    story.append(meta_table)
    story.append(PageBreak())
    
    # ==================== PAGE 2: EXECUTIVE SUMMARY & SCHEMA ====================
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "This capstone technical report details the build, calculations, and analytical insights generated for the Bluestock Mutual Fund Capstone Project. "
        "The system coordinates a fully automated weekday ETL data pipeline pulling live mutual fund Net Asset Values (NAV) from the open-source AMFI API "
        "and staging it inside an optimized SQLite relational schema. Trailing returns, risk metrics, and investor transaction statistics are compiled "
        "programmatically. Finally, a responsive web dashboard deployed in Streamlit provides interactive data slicing, automated recommendations, "
        "and advanced portfolio optimization scripts for retail investors.",
        body_style
    ))
    
    story.append(Paragraph("2. Database Schema & Data Models", h1_style))
    story.append(Paragraph(
        "The project database is stored in <b>data/db/bluestock_mf.db</b>. It utilizes five main relational tables designed to ensure 3NF integrity:",
        body_style
    ))
    story.append(Paragraph("• <b>dim_fund</b>: Master dimension table containing AMFI scheme codes, fund houses, categories, benchmarks, and plan structures.", body_style))
    story.append(Paragraph("• <b>fact_nav</b>: Historical daily Net Asset Value database, containing scheme code mapping and reindexed dates.", body_style))
    story.append(Paragraph("• <b>fact_transactions</b>: Investor transaction ledger cataloging transactional sizes, state, KYC, age, and payment types.", body_style))
    story.append(Paragraph("• <b>fact_performance</b>: Compiled analytical metrics tracking trailing return percentages, Alpha, Beta, Sharpe, and Drawdowns.", body_style))
    story.append(Paragraph("• <b>portfolio_holdings</b>: Fund holdings weights and sectors utilized to check portfolio diversification levels.", body_style))
    story.append(PageBreak())
    
    # ==================== PAGE 3: ETL & WEEKEND NAV REINDEXING ====================
    story.append(Paragraph("3. ETL Pipeline & Reindexing Methodology", h1_style))
    story.append(Paragraph(
        "The ETL pipeline script, located in <b>scripts/etl_pipeline.py</b>, runs without manual intervention. "
        "It fetches the latest daily NAV updates from <i>api.mfapi.in</i> for direct and regular plans. "
        "A critical phase in mutual fund analytics is the handling of dates where NAV is not published (weekends and public holidays). "
        "Common analytics mistakes include skipping holiday dates, which biases return time-series, or reindexing to calendar days without forward-filling.",
        body_style
    ))
    
    story.append(Paragraph("<b>Reindexing & ffill() Rules Applied:</b>", h2_style))
    story.append(Paragraph("1. For each fund, the script identifies the minimum and maximum NAV date.", body_style))
    story.append(Paragraph("2. It reindexes the time series to a continuous daily date index (calendar range including Saturday and Sunday).", body_style))
    story.append(Paragraph("3. It applies a forward-fill (<code>ffill()</code>) to carry Friday NAVs over the weekend.", body_style))
    story.append(Paragraph("4. Returns and CAGRs are annualized based on standard trading days: <b>252 business days</b> per calendar year, preventing return bias.", body_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Performance Rankings Scorecard", h1_style))
    story.append(Paragraph(
        "The table below represents the top 8 mutual fund schemes sorted by 3-Year CAGR returns. Data is derived programmatically from the SQLite database:",
        body_style
    ))
    
    # Build Top Funds Table
    table_data = [[Paragraph("Scheme Name", table_hdr_style), 
                   Paragraph("Category", table_hdr_style), 
                   Paragraph("3Yr CAGR", table_hdr_style), 
                   Paragraph("Sharpe", table_hdr_style), 
                   Paragraph("Risk Grade", table_hdr_style)]]
    
    for _, row in ranked_funds.iterrows():
        table_data.append([
            Paragraph(str(row['scheme_name']), table_cell_style),
            Paragraph(str(row['category']), table_cell_style),
            Paragraph(f"{row['return_3yr_pct']:.2f}%", table_cell_style),
            Paragraph(f"{row['sharpe_ratio']:.2f}", table_cell_style),
            Paragraph(str(row['risk_grade']), table_cell_style)
        ])
        
    rank_table = Table(table_data, colWidths=[2.2*inch, 1.2*inch, 1.0*inch, 0.8*inch, 1.3*inch])
    rank_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(rank_table)
    story.append(PageBreak())
    
    # ==================== PAGE 4: ADVANCED FINANCIAL ENGINEERING ====================
    story.append(Paragraph("5. Advanced Financial Engineering & Risk Metrics", h1_style))
    story.append(Paragraph(
        "For deep risk analysis, we calculate <b>95% Historical Value at Risk (VaR)</b> and <b>Conditional Value at Risk (CVaR)</b>. "
        "VaR represents the boundary limit below which daily returns fall with a 5% probability. "
        "CVaR computes the expected average loss given that the return exceeds the VaR threshold (the mean of the 5% tail). "
        "These metrics help investors evaluate downside tail risks during market stress events.",
        body_style
    ))
    
    story.append(Paragraph("<b>Sector Concentration Analysis (Herfindahl-Hirschman Index - HHI):</b>", h2_style))
    story.append(Paragraph(
        "HHI values are computed by squaring sector weights: <code>HHI = sum(Sector_Weight_pct ^ 2)</code>. "
        "This metric is calculated for all equity funds. "
        "A low HHI (below 1,200) denotes well-diversified portfolios (e.g. diversified large-cap funds). "
        "A high HHI (above 2,000) shows thematic or sector-focused funds, representing concentration risks.",
        body_style
    ))
    
    story.append(Paragraph("<b>Top Volatile Funds & Risk Scores:</b>", h2_style))
    
    # Volatility Table
    vol_table_data = [[Paragraph("Scheme Name", table_hdr_style), 
                       Paragraph("Category", table_hdr_style), 
                       Paragraph("Annualised Volatility", table_hdr_style), 
                       Paragraph("Morningstar Rating", table_hdr_style), 
                       Paragraph("Risk Grade", table_hdr_style)]]
    
    for _, row in hhi_data.iterrows():
        vol_table_data.append([
            Paragraph(str(row['scheme_name']), table_cell_style),
            Paragraph(str(row['category']), table_cell_style),
            Paragraph(f"{row['std_dev_ann_pct']:.2f}%", table_cell_style),
            Paragraph(str(row['morningstar_rating']), table_cell_style),
            Paragraph(str(row['risk_grade']), table_cell_style)
        ])
        
    vol_table = Table(vol_table_data, colWidths=[2.2*inch, 1.2*inch, 1.3*inch, 0.8*inch, 1.0*inch])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(vol_table)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Investor Cohort & Retention Analysis", h1_style))
    story.append(Paragraph(
        "We perform demographic cohort splits and retention flags using the transaction ledger. "
        "<b>Cohort analysis</b> segments investors based on their first transaction year (2024 vs 2025). "
        "<b>SIP Continuity analysis</b> tracks accounts with 6 or more monthly transactions. "
        "If the gap between transactions exceeds 35 days, the account is flagged as 'At Risk' of churning. "
        "These flagged customer records are stored inside <code>data/processed/sip_continuity.csv</code> for targeting customer retention email campaigns.",
        body_style
    ))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("Final Capstone PDF Report saved to: reports/Final_Report.pdf")

if __name__ == "__main__":
    generate_pdf()
