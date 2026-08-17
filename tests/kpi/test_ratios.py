import logging
import os
import sys

import pytest

# Ensure we can import from src
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    capex_intensity,
    cfo_quality_score,
    classify_capital_allocation,
    free_cash_flow,
)
from src.analytics.ratios import (
    asset_turnover,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    return_on_capital_employed,
    return_on_equity,
)

# === DAY 08: Profitability Ratios Tests (8 Tests) ===


def test_npm_normal():
    # Test 1: NPM Normal case
    assert net_profit_margin(10, 100) == 10.0
    assert net_profit_margin(15.5, 50.0) == 31.0


def test_npm_zero_sales():
    # Test 2: NPM Zero denominator
    assert net_profit_margin(10, 0) is None
    assert net_profit_margin(0, 0) is None


def test_npm_none_input():
    # Test 3: NPM None values
    assert net_profit_margin(None, 100) is None
    assert net_profit_margin(10, None) is None


def test_opm_normal():
    # Test 4: OPM Normal case
    assert operating_profit_margin(20, 100) == 20.0


def test_opm_mismatch(caplog):
    # Test 5: OPM cross-check mismatch > 1%
    with caplog.at_level(logging.WARNING):
        val = operating_profit_margin(
            25, 100, source_opm=20, company_id="TESTCO", year="2024"
        )
        assert val == 25.0
        assert any(
            "OPM Cross-Check Mismatch for TESTCO in 2024" in r.message
            for r in caplog.records
        )


def test_roe_normal():
    # Test 6: ROE Normal case
    assert return_on_equity(20, 10, 90) == 20.0


def test_roe_negative_equity():
    # Test 7: ROE Negative/zero equity
    assert return_on_equity(20, -50, 10) is None
    assert return_on_equity(20, 0, 0) is None


def test_roce_and_roa():
    # Test 8: ROCE & ROA calculations
    assert (
        return_on_capital_employed(15, 5, 40, 40, 20) == 20.0
    )  # (15+5)/(40+40+20)*100
    assert return_on_assets(10, 100) == 10.0
    assert return_on_assets(10, 0) is None


# === DAY 09: Leverage & Efficiency Ratios Tests (8 Tests) ===


def test_de_debt_free():
    # Test 9: D/E debt-free returns 0 (not None)
    assert debt_to_equity(0, 100, 100) == 0.0
    assert debt_to_equity(None, 100, 100) == 0.0


def test_de_normal():
    # Test 10: D/E Normal case
    assert debt_to_equity(50, 50, 50) == 0.5


def test_de_negative_denominator():
    # Test 11: D/E negative equity (returns None if borrowings > 0)
    assert debt_to_equity(10, -50, 10) is None
    assert debt_to_equity(0, -50, 10) == 0.0  # borrowings is 0, so should return 0


def test_icr_normal():
    # Test 12: ICR Normal case
    assert interest_coverage_ratio(10, 5, 5) == 3.0


def test_icr_zero_interest():
    # Test 13: ICR interest=0 returns None
    assert interest_coverage_ratio(10, 5, 0) is None
    assert interest_coverage_ratio(10, 5, None) is None


def test_net_debt():
    # Test 14: Net Debt calculation
    assert net_debt(100, 40) == 60.0
    assert net_debt(None, 40) == -40.0


def test_asset_turnover():
    # Test 15: Asset Turnover calculation
    assert asset_turnover(200, 100) == 2.0
    assert asset_turnover(200, 0) is None
    assert asset_turnover(200, None) is None


def test_leverage_flags():
    # Test 16: Leverage & warning thresholds checking in helper or runner logic.
    # High leverage check is tested here.
    de_val = debt_to_equity(600, 50, 50)  # D/E = 6
    assert de_val == 6.0
    assert (de_val > 5.0) is True


# === DAY 10: CAGR Engine Tests (10 Tests) ===


def test_cagr_normal():
    # Test 17: Normal CAGR (Positive + Positive)
    val, flag = calculate_cagr(100, 121, 2)
    assert pytest.approx(val, 0.01) == 10.0
    assert flag is None


def test_cagr_decline_to_loss():
    # Test 18: Positive to Negative
    val, flag = calculate_cagr(100, -50, 5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_turnaround():
    # Test 19: Negative to Positive
    val, flag = calculate_cagr(-50, 100, 5)
    assert val is None
    assert flag == "TURNAROUND"


def test_cagr_both_negative():
    # Test 20: Negative to Negative
    val, flag = calculate_cagr(-50, -100, 5)
    assert val is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    # Test 21: Zero Base
    val, flag = calculate_cagr(0, 100, 5)
    assert val is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_years():
    # Test 22: Less than n years or missing data
    val, flag = calculate_cagr(100, 150, 0)
    assert val is None
    assert flag == "INSUFFICIENT"

    val, flag = calculate_cagr(100, None, 5)
    assert val is None
    assert flag == "INSUFFICIENT"


# === Additional Cash Flow Tests (To complete covering Day 11) ===


def test_fcf_calculation():
    # Test 23: Free Cash Flow
    assert free_cash_flow(100, -40) == 60.0
    assert free_cash_flow(-50, -40) == -90.0


def test_cfo_quality_score():
    # Test 24: CFO Quality Score
    cfos = [100, 120, 110, 130, 150]
    pats = [90, 100, 95, 110, 120]
    avg, label = cfo_quality_score(cfos, pats)
    assert avg > 1.0
    assert label == "High Quality"


def test_capex_intensity():
    # Test 25: CapEx Intensity
    pct, label = capex_intensity(-10, 200)
    assert pct == 5.0
    assert label == "Moderate"


def test_capital_allocation_pattern():
    # Test 26: Capital Allocation Classifier
    assert (
        classify_capital_allocation(100, -50, -30, 80) == "Shareholder Returns"
    )  # (+,-,-) and high CFO/PAT
    assert (
        classify_capital_allocation(100, -50, -30, 200) == "Reinvestor"
    )  # (+,-,-) and low CFO/PAT
    assert classify_capital_allocation(-50, 20, 20) == "Distress Signal"  # (-,+,+)
