import os
import sqlite3
import pandas as pd
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_HTML_PATH = REPORTS_DIR / "weekly_performance_report.html"

def generate_html_report():
    if not DB_PATH.exists():
        return "Error: Database not found. Please run ETL pipeline first."
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Top 5 Funds by 3-Yr Returns
    query_top_returns = """
        SELECT scheme_name, category, return_3yr_pct, sharpe_ratio, risk_grade, aum_crore
        FROM fact_performance
        WHERE return_3yr_pct IS NOT NULL
        ORDER BY return_3yr_pct DESC
        LIMIT 5
    """
    top_returns = pd.read_sql_query(query_top_returns, conn)
    
    # 2. Lowest Expense Ratio Funds
    query_low_expense = """
        SELECT scheme_name, category, expense_ratio_pct, return_3yr_pct
        FROM fact_performance
        WHERE expense_ratio_pct > 0
        ORDER BY expense_ratio_pct ASC
        LIMIT 5
    """
    low_expense = pd.read_sql_query(query_low_expense, conn)
    
    # 3. Market Benchmarks Overview
    query_benchmarks = """
        SELECT index_name, MAX(close_value) as latest_close, MIN(close_value) as base_close
        FROM benchmark_indices
        GROUP BY index_name
    """
    benchmarks = pd.read_sql_query(query_benchmarks, conn)
    
    conn.close()
    
    # Build HTML Content with rich inline styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Weekly Mutual Fund Performance Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #333333;
                background-color: #f4f6f9;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 650px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 10px rgba(0,0,0,0.08);
                border: 1px solid #e0e0e0;
            }}
            .header {{
                background: linear-gradient(135deg, #12121e 0%, #00b4d8 100%);
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .section-title {{
                color: #12121e;
                font-size: 18px;
                font-weight: 600;
                border-bottom: 2px solid #00b4d8;
                padding-bottom: 5px;
                margin-top: 25px;
                margin-bottom: 15px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            th {{
                background-color: #f7fafc;
                color: #4a5568;
                text-align: left;
                padding: 10px;
                font-weight: 600;
                border-bottom: 2px solid #edf2f7;
            }}
            td {{
                padding: 12px 10px;
                border-bottom: 1px solid #edf2f7;
                color: #2d3748;
            }}
            tr:hover {{
                background-color: #f8fafc;
            }}
            .badge {{
                display: inline-block;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
                border-radius: 12px;
                text-transform: uppercase;
            }}
            .badge-high {{ background-color: #fed7d7; color: #9b2c2c; }}
            .badge-mod {{ background-color: #feebc8; color: #9c4221; }}
            .badge-low {{ background-color: #c6f6d5; color: #22543d; }}
            .footer {{
                background-color: #12121e;
                color: #a0aec0;
                text-align: center;
                padding: 20px;
                font-size: 11px;
                border-top: 1px solid #2d3748;
            }}
            .footer a {{
                color: #00b4d8;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bluestock Mutual Fund Analytics</h1>
                <p>Weekly Performance & Risk Summary Report</p>
            </div>
            <div class="content">
                <p>Hello Investor,</p>
                <p>Here is your weekly summary of mutual fund performance, low-cost options, and market index benchmarks compiled by our automated ETL pipeline.</p>
                
                <!-- Section 1: Top 3-Yr returns -->
                <div class="section-title">Top 5 Performing Funds (by 3-Year CAGR)</div>
                <table>
                    <thead>
                        <tr>
                            <th>Scheme Name</th>
                            <th>Category</th>
                            <th>3Yr Return</th>
                            <th>Sharpe</th>
                            <th>Risk Grade</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for _, row in top_returns.iterrows():
        risk_cls = "badge-high"
        if "Low" in str(row['risk_grade']):
            risk_cls = "badge-low"
        elif "Mod" in str(row['risk_grade']):
            risk_cls = "badge-mod"
            
        html_content += f"""
                        <tr>
                            <td style="font-weight: 500;">{row['scheme_name']}</td>
                            <td>{row['category']}</td>
                            <td style="color: #2f855a; font-weight: 600;">{row['return_3yr_pct']:.2f}%</td>
                            <td>{row['sharpe_ratio']:.2f}</td>
                            <td><span class="badge {risk_cls}">{row['risk_grade']}</span></td>
                        </tr>
        """
        
    html_content += """
                    </tbody>
                </table>
                
                <!-- Section 2: Low expense ratio funds -->
                <div class="section-title">Top 5 Cost-Efficient Funds (Lowest Expense Ratios)</div>
                <table>
                    <thead>
                        <tr>
                            <th>Scheme Name</th>
                            <th>Category</th>
                            <th>Expense Ratio</th>
                            <th>3Yr CAGR</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for _, row in low_expense.iterrows():
        ret_val = f"{row['return_3yr_pct']:.2f}%" if pd.notnull(row['return_3yr_pct']) else "N/A"
        html_content += f"""
                        <tr>
                            <td>{row['scheme_name']}</td>
                            <td>{row['category']}</td>
                            <td style="color: #2b6cb0; font-weight: 600;">{row['expense_ratio_pct']:.2f}%</td>
                            <td>{ret_val}</td>
                        </tr>
        """
        
    html_content += """
                    </tbody>
                </table>
                
                <p style="font-size: 13px; color: #718096; margin-top: 25px;">
                    *Note: This performance summary is generated automatically from daily NAV histories. Past performance is not an indicator of future returns.
                </p>
            </div>
            <div class="footer">
                <p>This is an automated performance report. Please do not reply directly to this email.</p>
                <p>&copy; 2026 Bluestock Mutual Fund Analytics. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save file
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Weekly HTML report generated successfully at: {OUTPUT_HTML_PATH}")
    return html_content

def send_email_report(html_body, recipient_email="investor@example.com", smtp_host="localhost", smtp_port=1025):
    print(f"Preparing to email report to {recipient_email}...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Weekly Mutual Fund Performance & Risk Report"
    msg["From"] = "analytics@bluestock.in"
    msg["To"] = recipient_email
    
    msg.attach(MIMEText(html_body, "html"))
    
    # Mock transmission logic (since standard SMTP details are not configured)
    print("SMTP Details: Host={}, Port={}".format(smtp_host, smtp_port))
    print("Mailing status: Simulated sending SUCCESS. (Body written to reports/weekly_performance_report.html)")
    
    # To use in production, uncomment the lines below:
    # try:
    #     with smtplib.SMTP(smtp_host, smtp_port) as server:
    #         server.sendmail(msg["From"], msg["To"], msg.as_string())
    #     print("Email dispatched successfully!")
    # except Exception as e:
    #     print(f"Failed to dispatch email: {e}")

if __name__ == "__main__":
    html_body = generate_html_report()
    if not html_body.startswith("Error"):
        send_email_report(html_body)
