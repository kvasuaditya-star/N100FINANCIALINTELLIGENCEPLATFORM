"""
Day 35 — Portfolio Summary
Generates a high-level portfolio overview PDF.
"""

import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "portfolio")
INTEL_XLSX = os.path.join(PROJECT_ROOT, "output", "cashflow_intelligence.xlsx")

# ── Styles ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()
NAVY = colors.HexColor("#1B2A4A")

STYLE_TITLE = ParagraphStyle(
    "Title",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=20,
    textColor=NAVY,
    spaceAfter=15,
    alignment=1,
)
STYLE_NORMAL = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    textColor=colors.black,
    spaceAfter=8,
)
STYLE_H2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    textColor=NAVY,
    spaceBefore=15,
    spaceAfter=8,
)


def run_portfolio_summary():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, "Portfolio_Summary.pdf")

    conn = sqlite3.connect(DB_PATH)
    comp_df = pd.read_sql_query("SELECT id FROM companies", conn)
    conn.close()

    intel_df = pd.DataFrame()
    if os.path.exists(INTEL_XLSX):
        intel_df = pd.read_excel(INTEL_XLSX)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
    )
    elements = []

    elements.append(Paragraph("N100 Financial Intelligence Platform", STYLE_TITLE))
    elements.append(Paragraph("Portfolio Summary Report", STYLE_TITLE))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Overview", STYLE_H2))
    elements.append(
        Paragraph(f"Total Companies Monitored: {len(comp_df)}", STYLE_NORMAL)
    )

    if not intel_df.empty:
        elements.append(Paragraph("Cash Flow Intelligence Aggregates", STYLE_H2))

        cfo_dist = intel_df["cfo_quality_label"].value_counts()
        elements.append(
            Paragraph(
                f"High Quality CFO: {cfo_dist.get('High Quality', 0)} companies",
                STYLE_NORMAL,
            )
        )
        elements.append(
            Paragraph(
                f"Accrual Risk: {cfo_dist.get('Accrual Risk', 0)} companies",
                STYLE_NORMAL,
            )
        )

        capex_dist = intel_df["capex_label"].value_counts()
        elements.append(
            Paragraph(
                f"Asset Light: {capex_dist.get('Asset Light', 0)} companies",
                STYLE_NORMAL,
            )
        )
        elements.append(
            Paragraph(
                f"Capital Intensive: {capex_dist.get('Capital Intensive', 0)} companies",
                STYLE_NORMAL,
            )
        )

        distress = intel_df[intel_df["distress_flag"] == True]
        elements.append(
            Paragraph(
                f"Companies showing Distress Signals: {len(distress)}", STYLE_NORMAL
            )
        )

        deleverage = intel_df[intel_df["deleveraging_flag"] == True]
        elements.append(
            Paragraph(
                f"Companies actively Deleveraging: {len(deleverage)}", STYLE_NORMAL
            )
        )

    doc.build(elements)
    print(f"[OK] Generated Portfolio Summary: {out_path}")


if __name__ == "__main__":
    run_portfolio_summary()
