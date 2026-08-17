import logging

logger = logging.getLogger(__name__)


def net_profit_margin(net_profit, sales):
    """
    Computes Net Profit Margin: net_profit / sales * 100
    Returns None if sales == 0 or if inputs are None.
    """
    if net_profit is None or sales is None:
        return None
    if sales == 0:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit, sales, source_opm=None, company_id=None, year=None
):
    """
    Computes Operating Profit Margin: operating_profit / sales * 100
    Returns None if sales == 0 or if inputs are None.
    If source_opm is provided, cross-checks and logs if the absolute difference > 1%.
    """
    if operating_profit is None or sales is None:
        return None
    if sales == 0:
        return None

    computed_opm = (operating_profit / sales) * 100

    if source_opm is not None:
        try:
            diff = abs(computed_opm - float(source_opm))
            if diff > 1.0:
                msg = f"OPM Cross-Check Mismatch for {company_id or 'Unknown'} in {year or 'Unknown'}: Computed={computed_opm:.2f}%, Source={source_opm:.2f}%, Diff={diff:.2f}%"
                logger.warning(msg)
        except (ValueError, TypeError):
            pass

    return computed_opm


def return_on_equity(net_profit, equity_capital, reserves):
    """
    Computes Return on Equity (ROE): net_profit / (equity_capital + reserves) * 100
    Returns None if (equity_capital + reserves) <= 0 or if inputs are None.
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    equity = equity_capital + reserves
    if equity <= 0:
        return None
    return (net_profit / equity) * 100


def return_on_capital_employed(
    profit_before_tax, interest, equity_capital, reserves, borrowings
):
    """
    Computes Return on Capital Employed (ROCE): EBIT / (equity + reserves + borrowings) * 100
    EBIT is calculated as profit_before_tax + interest.
    Returns None if denominator <= 0 or if inputs are None.
    """
    if profit_before_tax is None or equity_capital is None or reserves is None:
        return None

    # Borrowings and interest can default to 0 if None
    borrowings_val = borrowings if borrowings is not None else 0
    interest_val = interest if interest is not None else 0

    ebit = profit_before_tax + interest_val
    capital_employed = equity_capital + reserves + borrowings_val

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    """
    Computes Return on Assets (ROA): net_profit / total_assets * 100
    Returns None if total_assets <= 0 or if inputs are None.
    """
    if net_profit is None or total_assets is None:
        return None
    if total_assets <= 0:
        return None
    return (net_profit / total_assets) * 100


def debt_to_equity(borrowings, equity_capital, reserves):
    """
    Computes Debt-to-Equity: borrowings / (equity_capital + reserves)
    Returns 0 if borrowings is 0 or None.
    Returns None if (equity_capital + reserves) <= 0 and borrowings > 0.
    """
    borrowings_val = borrowings if borrowings is not None else 0
    if borrowings_val == 0:
        return 0.0

    if equity_capital is None or reserves is None:
        return None

    equity = equity_capital + reserves
    if equity <= 0:
        return None

    return borrowings_val / equity


def interest_coverage_ratio(operating_profit, other_income, interest):
    """
    Computes Interest Coverage Ratio: (operating_profit + other_income) / interest
    Returns None if interest == 0 or None.
    """
    if interest is None or interest == 0:
        return None

    op = operating_profit if operating_profit is not None else 0
    oi = other_income if other_income is not None else 0

    return (op + oi) / interest


def net_debt(borrowings, investments):
    """
    Computes Net Debt: borrowings - investments
    """
    b = borrowings if borrowings is not None else 0
    i = investments if investments is not None else 0
    return float(b - i)


def asset_turnover(sales, total_assets):
    """
    Computes Asset Turnover: sales / total_assets
    Returns None if total_assets <= 0 or if inputs are None.
    """
    if sales is None or total_assets is None:
        return None
    if total_assets <= 0:
        return None
    return sales / total_assets
