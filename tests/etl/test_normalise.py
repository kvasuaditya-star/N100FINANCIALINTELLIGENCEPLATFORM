import os
import sys

# Adjust path to import from src
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.etl.normaliser import normalize_ticker, normalize_year


# --- 15 Unit Tests for normalize_ticker ---
def test_ticker_normal():
    assert normalize_ticker("TCS") == "TCS"


def test_ticker_lowercase():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_spaces():
    assert normalize_ticker("  TCS  ") == "TCS"


def test_ticker_hyphen():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"


def test_ticker_ampersand():
    assert normalize_ticker("M&M") == "M&M"


def test_ticker_none():
    assert normalize_ticker(None) == "MISSING"


def test_ticker_empty():
    assert normalize_ticker("") == "MISSING"


def test_ticker_spaces_only():
    assert normalize_ticker("   ") == "MISSING"


def test_ticker_infy():
    assert normalize_ticker("INFY") == "INFY"


def test_ticker_abb():
    assert normalize_ticker("abb") == "ABB"


def test_ticker_numeric():
    assert normalize_ticker(123) == "123"


def test_ticker_single_char():
    assert normalize_ticker("a") == "A"


def test_ticker_longer():
    assert normalize_ticker("longer_ticker") == "LONGER_TICKER"


def test_ticker_dots():
    assert normalize_ticker("T.C.S.") == "T.C.S."


def test_ticker_mixed_case():
    assert normalize_ticker("Reliance") == "RELIANCE"


# --- 22 Unit Tests for normalize_year ---
def test_year_mar_dash():
    assert normalize_year("Mar-23") == "2023-03"


def test_year_mar_space():
    assert normalize_year("Mar 23") == "2023-03"


def test_year_full_month():
    assert normalize_year("March-2023") == "2023-03"


def test_year_int():
    assert normalize_year(2023) == "2023-03"


def test_year_str_int():
    assert normalize_year("2023") == "2023-03"


def test_year_fy_short():
    assert normalize_year("FY23") == "2023-03"


def test_year_fy_space():
    assert normalize_year("FY 23") == "2023-03"


def test_year_fy_long():
    assert normalize_year("FY2023") == "2023-03"


def test_year_dec_dash():
    assert normalize_year("Dec-22") == "2022-12"


def test_year_jun_dash():
    assert normalize_year("Jun-23") == "2023-06"


def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"


def test_year_none():
    assert normalize_year(None) == "PARSE_ERROR"


def test_year_garbage():
    assert normalize_year("garbage") == "PARSE_ERROR"


def test_year_empty():
    assert normalize_year("") == "PARSE_ERROR"


def test_year_sep_dash():
    assert normalize_year("Sep-19") == "2019-09"


def test_year_september_long():
    assert normalize_year("September-2019") == "2019-09"


def test_year_june_space():
    assert normalize_year("June 15") == "2015-06"


def test_year_fy12():
    assert normalize_year("FY12") == "2012-03"


def test_year_2010():
    assert normalize_year("2010") == "2010-03"


def test_year_12_short():
    assert normalize_year("12") == "2012-03"


def test_year_dec_space():
    assert normalize_year("Dec 12") == "2012-12"


def test_year_invalid_month():
    assert normalize_year("invalid_month-23") == "PARSE_ERROR"


# Extra tests for real data formats encountered in Sprint 1


def test_year_dec_space_4digit():
    assert normalize_year("Dec 2012") == "2012-12"


def test_year_mar_space_4digit():
    assert normalize_year("Mar 2023") == "2023-03"


def test_year_jun_space_4digit():
    assert normalize_year("Jun 2013") == "2013-06"


def test_year_sep_space_4digit():
    assert normalize_year("Sep 2024") == "2024-09"


def test_year_ttm_upper():
    assert normalize_year("TTM") == "PARSE_ERROR"


def test_year_ttm_lower():
    assert normalize_year("ttm") == "PARSE_ERROR"


def test_year_suffix_9m():
    assert normalize_year("Mar 2016 9m") == "2016-03"


def test_year_suffix_15m():
    assert normalize_year("Mar 2023 15") == "2023-03"


def test_year_suffix_ttm_combo():
    assert normalize_year("Mar 2023 TTM") == "2023-03"


def test_year_mar_2011():
    assert normalize_year("Mar 2011") == "2011-03"


def test_year_sep_2011():
    assert normalize_year("Sep 2011") == "2011-09"
