"""
Day 34 — Sector Reports
Generates sector summary PDFs (e.g. Financials_Sector_Report.pdf) with aggregated KPIs.
"""

import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "nifty100.db")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "sectors")
INTEL_XLSX = os.path.join(PROJECT_ROOT, "output", "cashflow_intelligence.xlsx")

# ── Styles ─────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()
NAVY = colors.HexColor("#1B2A4A")

STYLE_TITLE = ParagraphStyle(
    "Title",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    textColor=NAVY,
    spaceAfter=12,
)
STYLE_NORMAL = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    textColor=colors.black,
    spaceAfter=6,
)


def run_sector_reports():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    sectors = pd.read_sql_query("SELECT DISTINCT broad_sector FROM sectors", conn)
    broad_sectors = [s for s in sectors["broad_sector"].tolist() if s and s != "N/A"]

    # Load companies with their sectors
    comp_df = pd.read_sql_query(
        "SELECT c.id, c.company_name, s.broad_sector "
        "FROM companies c JOIN sectors s ON c.id = s.company_id",
        conn,
    )

    # Try to load intel
    intel_df = pd.DataFrame()
    if os.path.exists(INTEL_XLSX):
        intel_df = pd.read_excel(INTEL_XLSX)

    conn.close()

    print(f"Generating reports for {len(broad_sectors)} sectors...")

    for sector in broad_sectors:
        sector_comps = comp_df[comp_df["broad_sector"] == sector]
        if sector_comps.empty:
            continue

        safe_sector = str(sector).replace("/", "_").replace(" ", "_")
        out_path = os.path.join(REPORTS_DIR, f"{safe_sector}_Sector_Report.pdf")

        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=50,
            bottomMargin=50,
        )
        elements = []

        # Header
        elements.append(Paragraph(f"{sector} - Sector Summary", STYLE_TITLE))
        elements.append(
            Paragraph(f"Number of Constituents: {len(sector_comps)}", STYLE_NORMAL)
        )
        elements.append(Spacer(1, 15))

        # Table data
        table_data = [
            [
                "Company ID",
                "Company Name",
                "CFO Quality",
                "CapEx Intensity",
                "Capital Allocation",
            ]
        ]

        for _, row in sector_comps.iterrows():
            cid = row["id"]
            name = str(row["company_name"])[:30]

            cfo_qual = "N/A"
            capex = "N/A"
            ca_label = "N/A"

            if not intel_df.empty:
                i_row = intel_df[intel_df["company_id"] == cid]
                if not i_row.empty:
                    i_row = i_row.iloc[0]
                    cfo_qual = str(i_row.get("cfo_quality_label", "N/A"))
                    capex = str(i_row.get("capex_label", "N/A"))
                    ca_label = str(i_row.get("capital_allocation_label", "N/A"))

            table_data.append([cid, name, cfo_qual, capex, ca_label])

        t = Table(table_data, colWidths=[60, 160, 80, 80, 100])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F5F6FA")),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        elements.append(t)
        doc.build(elements)
        print(f"  [OK] Generated {out_path}")


if __name__ == "__main__":
    run_sector_reports()
