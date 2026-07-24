import sqlite3
import pandas as pd

conn = sqlite3.connect('data/nifty100.db')
companies = ['BEL', 'HAL', 'LT', 'PNB', 'INDIGO']

for cid in companies:
    print(f"\n=================== {cid} ===================")
    df_bs = pd.read_sql_query(f"SELECT year, equity_capital, reserves, borrowings, total_assets FROM balancesheet WHERE company_id='{cid}'", conn)
    df_pl = pd.read_sql_query(f"SELECT year, sales, operating_profit, interest, net_profit, profit_before_tax FROM profitandloss WHERE company_id='{cid}'", conn)
    df_m = df_bs.merge(df_pl, on='year')
    print(df_m.to_string(index=False))

conn.close()
