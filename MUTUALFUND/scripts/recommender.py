import sys
import os
import pandas as pd
from pathlib import Path

# Resolve path dynamically to avoid hardcoded absolute paths
BASE_DIR = Path(__file__).resolve().parent.parent
PERF_FILE_PATH = BASE_DIR / 'data' / 'processed' / '07_scheme_performance.csv'

def recommend_funds(risk_appetite):
    # Standardise input
    appetite = risk_appetite.strip().lower()
    
    # Validate input
    if appetite not in ['low', 'moderate', 'high']:
        print("Error: Invalid risk appetite. Please choose from: Low, Moderate, High.")
        return None
        
    # Check if performance file exists
    if not PERF_FILE_PATH.exists():
        print(f"Error: Scheme performance file not found at {PERF_FILE_PATH}")
        return None
        
    # Load performance data
    df = pd.read_csv(PERF_FILE_PATH)
    
    # Map risk appetite to risk grades in the dataset
    # Unique values in dataset: Low, Moderate, Moderately High, High, Very High
    if appetite == 'low':
        matched_grades = ['Low']
    elif appetite == 'moderate':
        matched_grades = ['Moderate', 'Moderately High']
    else:  # high
        matched_grades = ['High', 'Very High']
        
    # Filter schemes based on matched risk grades
    filtered_df = df[df['risk_grade'].isin(matched_grades)].copy()
    
    if filtered_df.empty:
        print(f"No funds found for risk grades: {matched_grades}")
        return None
        
    # Sort schemes by Sharpe ratio descending and get the top 3
    top_3 = filtered_df.sort_values(by='sharpe_ratio', ascending=False).head(3)
    
    # Formulate output table
    recommendations = []
    for idx, row in enumerate(top_3.itertuples(), 1):
        recommendations.append({
            'Rank': idx,
            'Scheme Name': row.scheme_name,
            'Category': row.category,
            'Plan': row.plan,
            'Sharpe Ratio': row.sharpe_ratio,
            'Sortino Ratio': getattr(row, 'sortino_ratio', None),
            '3Yr Return (%)': getattr(row, 'return_3yr_pct', None),
            'Risk Grade': row.risk_grade,
            'AUM (Cr)': getattr(row, 'aum_crore', None)
        })
        
    return pd.DataFrame(recommendations)

def main():
    print("=" * 60)
    print("      BLUESTOCK MUTUAL FUND RECOMMENDER (SHARPE-BASED)      ")
    print("=" * 60)
    
    # Read CLI argument if available, else prompt user
    if len(sys.argv) > 1:
        risk_appetite = sys.argv[1]
    else:
        print("Choose your risk appetite:")
        print("  - Low       (Capital preservation focused)")
        print("  - Moderate  (Balanced growth & moderate volatility)")
        print("  - High      (Aggressive returns, high volatility tolerance)")
        risk_appetite = input("\nEnter risk appetite (Low/Moderate/High): ")
        
    print(f"\nSearching top 3 funds for risk appetite: {risk_appetite.capitalize()}...")
    
    recs = recommend_funds(risk_appetite)
    
    if recs is not None:
        print("\n" + "=" * 110)
        print(f"RECOMMENDED FUNDS FOR {risk_appetite.upper()} RISK PROFILE:")
        print("=" * 110)
        # Format the table nicely
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(recs.to_string(index=False))
        print("=" * 110)
        print("\n*Note: Funds are selected based on the highest 3-Year Sharpe Ratio in their risk class.")
    
if __name__ == '__main__':
    main()
