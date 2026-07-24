import os
import requests
import pandas as pd
from pathlib import Path

SCHEME_CODES = {
    "HDFC Top 100 Direct": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841
}

# Resolve target directory dynamically
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "raw"

def fetch_nav(scheme_name, scheme_code):
    print(f"Downloading NAV history for {scheme_name} (Code: {scheme_code})...")
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]:
                df = pd.DataFrame(data["data"])
                # Columns in response data are usually 'date' (DD-MM-YYYY) and 'nav'
                df.to_csv(OUTPUT_DIR / f"{scheme_code}_NAV.csv", index=False)
                print(f"Successfully saved {scheme_code}_NAV.csv")
                return True
            else:
                print(f"No NAV data found in API response for code {scheme_code}")
        else:
            print(f"Failed to fetch code {scheme_code}. Status: {response.status_code}")
    except Exception as e:
        print(f"Exception fetching code {scheme_code}: {e}")
    return False

def fetch_all_nav():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    success_count = 0
    for name, code in SCHEME_CODES.items():
        if fetch_nav(name, code):
            success_count += 1
    print(f"NAV Fetching process completed. Success: {success_count}/{len(SCHEME_CODES)}")

if __name__ == "__main__":
    fetch_all_nav()
