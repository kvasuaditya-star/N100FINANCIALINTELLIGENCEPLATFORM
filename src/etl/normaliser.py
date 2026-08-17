import re

MONTH_MAP = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}


def normalize_ticker(ticker) -> str:
    """Normalises NSE tickers to uppercase and strips whitespace."""
    if ticker is None:
        return "MISSING"
    ticker_str = str(ticker).strip()
    if not ticker_str:
        return "MISSING"
    return ticker_str.upper()


def normalize_year(year) -> str:
    """Standardises multiple year formats into 'YYYY-MM'.

    Supported formats:
        - 'YYYY-MM'              already normalised
        - 'Mar 2023'             month name + 4-digit year (with space or dash)
        - 'Dec 2012'             month name + 4-digit year
        - 'Mar-23'               month name + 2-digit year (with dash)
        - 'Mar 23'               month name + 2-digit year (with space)
        - 'March-2023'           full month name + 4-digit year
        - 'FY23', 'FY 23'       fiscal year prefix
        - 'FY2023'               fiscal year prefix (4 digits)
        - 2023 (int)             plain year → defaults to March (Indian FY end)
        - '2023'                 string year
        - '2023-Mar'             year-month reversed
        - 'Mar 2016 9m'         partial year suffix → strip '9m' → 'Mar 2016'
        - 'Mar 2023 15'         partial year suffix → strip '15' → 'Mar 2023'
        - 'Mar 2023 TTM'        TTM annotation → strip → 'Mar 2023'
        - 'TTM'                  trailing twelve months → PARSE_ERROR
    """
    if year is None:
        return "PARSE_ERROR"

    # Convert to string and clean
    year_str = str(year).strip()

    # Pure TTM → not a fiscal year
    if year_str.upper() == "TTM":
        return "PARSE_ERROR"

    # Already normalised check
    if re.match(r"^\d{4}-\d{2}$", year_str):
        return year_str

    # Strip trailing annotation suffixes: only after a 4-digit year
    # Handles "Mar 2016 9m", "Mar 2023 15", "Mar 2023 TTM", "2023 TTM"
    # Pattern: strip " 9m", " 15", " TTM", " (TTM)" after the year
    year_str = re.sub(
        r"(\d{4})\s+(?:\d{1,2}m?|TTM|\(TTM\))$", r"\1", year_str, flags=re.IGNORECASE
    ).strip()
    # Also handle 2-digit suffix: "Mar 23 TTM"
    year_str = re.sub(
        r"(\d{2})\s+(?:TTM|\(TTM\))$", r"\1", year_str, flags=re.IGNORECASE
    ).strip()

    # Re-check already normalised after stripping
    if re.match(r"^\d{4}-\d{2}$", year_str):
        return year_str

    # Re-check for pure TTM after stripping (shouldn't happen, but safety)
    if year_str.upper() == "TTM":
        return "PARSE_ERROR"

    # Strip FY prefix: FY23, FY2023, FY 23
    fy_match = re.match(r"^FY\s*(\d{2,4})$", year_str, re.IGNORECASE)
    if fy_match:
        val = fy_match.group(1)
        if len(val) == 2:
            return f"20{val}-03"
        elif len(val) == 4:
            return f"{val}-03"
        return "PARSE_ERROR"

    # Pure integer check (e.g. 2023 or 23)
    if re.match(r"^\d+$", year_str):
        val = int(year_str)
        if 2000 <= val <= 2099:
            return f"{val}-03"
        elif 0 <= val <= 99:
            return f"20{val:02d}-03"
        return "PARSE_ERROR"

    # Pattern: Month-Year (e.g. Mar-23, March-2023, Mar 23, Dec 2012, Mar 2023)
    # Group 1: Month Name, Group 2: Year (2 or 4 digits)
    m1 = re.match(r"^([a-zA-Z]+)[-\s]+(\d{2,4})$", year_str)
    if m1:
        month_part = m1.group(1).lower()
        year_part = m1.group(2)
        if month_part in MONTH_MAP:
            mm = MONTH_MAP[month_part]
            if len(year_part) == 2:
                yyyy = f"20{year_part}"
            else:
                yyyy = year_part
            return f"{yyyy}-{mm}"

    # Pattern: Year-Month (e.g. 2023-Mar, 23-Dec, 2023 Mar)
    m2 = re.match(r"^(\d{2,4})[-\s]+([a-zA-Z]+)$", year_str)
    if m2:
        year_part = m2.group(1)
        month_part = m2.group(2).lower()
        if month_part in MONTH_MAP:
            mm = MONTH_MAP[month_part]
            if len(year_part) == 2:
                yyyy = f"20{year_part}"
            else:
                yyyy = year_part
            return f"{yyyy}-{mm}"

    return "PARSE_ERROR"
