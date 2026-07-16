import os
import shutil

raw_dir = "data/raw"
supporting_dir = "data/supporting"
docs_dir = "docs"

os.makedirs(supporting_dir, exist_ok=True)
os.makedirs(docs_dir, exist_ok=True)

# Define move operations
# (source_name_in_raw, target_path)
moves = [
    ("sheet_09.xlsx", os.path.join(raw_dir, "companies.xlsx")),
    ("sheet_11.xlsx", os.path.join(raw_dir, "profitandloss.xlsx")),
    ("sheet_07.xlsx", os.path.join(raw_dir, "balancesheet.xlsx")),
    ("sheet_08.xlsx", os.path.join(raw_dir, "cashflow.xlsx")),
    ("sheet_06.xlsx", os.path.join(raw_dir, "analysis.xlsx")),
    ("sheet_10.xlsx", os.path.join(raw_dir, "documents.xlsx")),
    ("sheet_12.xlsx", os.path.join(raw_dir, "prosandcons.xlsx")),
    ("sheet_04.xlsx", os.path.join(supporting_dir, "sectors.xlsx")),
    ("sheet_05.xlsx", os.path.join(supporting_dir, "stock_prices.xlsx")),
    ("sheet_02.xlsx", os.path.join(supporting_dir, "market_cap.xlsx")),
    ("sheet_01.xlsx", os.path.join(supporting_dir, "financial_ratios.xlsx")),
    ("sheet_03.xlsx", os.path.join(supporting_dir, "peer_groups.xlsx")),
    ("document.pdf", os.path.join(docs_dir, "document.pdf"))
]

for src_name, dest_path in moves:
    src_path = os.path.join(raw_dir, src_name)
    if os.path.exists(src_path):
        # Delete destination if it already exists
        if os.path.exists(dest_path):
            os.remove(dest_path)
        shutil.move(src_path, dest_path)
        print(f"Moved {src_path} -> {dest_path}")
    else:
        print(f"Source not found: {src_path}")

# Clean up sheet_*.xlsx or other files if any are left
for file in os.listdir(raw_dir):
    if file.startswith("sheet_") and file.endswith(".xlsx"):
        os.remove(os.path.join(raw_dir, file))
        print(f"Removed unused raw sheet: {file}")
