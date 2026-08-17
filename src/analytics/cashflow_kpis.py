def free_cash_flow(operating_activity, investing_activity):
    """
    Computes Free Cash Flow: operating_activity + investing_activity
    Negative values are allowed.
    """
    if operating_activity is None or investing_activity is None:
        return None
    return float(operating_activity + investing_activity)


def cfo_quality_score(cfo_history, pat_history):
    """
    Computes CFO Quality Score: CFO / PAT ratio averaged over 5 years.
    cfo_history: list of CFO values for past 5 years [Y-4, Y-3, Y-2, Y-1, Y]
    pat_history: list of PAT (net profit) values for past 5 years [Y-4, Y-3, Y-2, Y-1, Y]

    Returns: (score_value, label)
    - score_value: average ratio or None
    - label: 'High Quality', 'Moderate', 'Accrual Risk', or None
    """
    if (
        not cfo_history
        or not pat_history
        or len(cfo_history) < 5
        or len(pat_history) < 5
    ):
        return None, None

    ratios = []
    for cfo, pat in zip(cfo_history[-5:], pat_history[-5:]):
        if cfo is None or pat is None or pat == 0:
            return None, None
        ratios.append(cfo / pat)

    avg_ratio = sum(ratios) / 5.0

    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_ratio, label


def capex_intensity(investing_activity, sales):
    """
    Computes CapEx Intensity: abs(investing_activity) / sales * 100
    Returns: (intensity_pct, label)
    - intensity_pct: CapEx intensity percentage or None
    - label: 'Asset Light', 'Moderate', 'Capital Intensive', or None
    """
    if investing_activity is None or sales is None or sales == 0:
        return None, None

    intensity = (abs(investing_activity) / sales) * 100.0

    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def fcf_conversion_rate(fcf, operating_profit):
    """
    Computes FCF Conversion Rate: FCF / operating_profit * 100
    Returns None if operating_profit == 0 or if inputs are None.
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100.0


def classify_capital_allocation(cfo, cfi, cff, pat=None):
    """
    Classifies capital allocation based on the signs of CFO, CFI, and CFF.
    Signs are defined as positive (+) if >= 0, negative (-) if < 0.

    Patterns:
    - (+, -, -) with CFO/PAT > 1.0 = 'Shareholder Returns'
    - (+, -, -) otherwise = 'Reinvestor'
    - (+, +, -) = 'Liquidating Assets'
    - (-, +, +) = 'Distress Signal'
    - (-, -, +) = 'Growth Funded by Debt'
    - (+, +, +) = 'Cash Accumulator'
    - (-, -, -) = 'Pre-Revenue'
    - (+, -, +) = 'Mixed'
    - Any other combination = 'Mixed'
    """
    if cfo is None or cfi is None or cff is None:
        return "Mixed"

    s_cfo = "+" if cfo >= 0 else "-"
    s_cfi = "+" if cfi >= 0 else "-"
    s_cff = "+" if cff >= 0 else "-"

    pattern = (s_cfo, s_cfi, s_cff)

    if pattern == ("+", "-", "-"):
        if pat is not None and pat > 0 and (cfo / pat) > 1.0:
            return "Shareholder Returns"
        return "Reinvestor"
    elif pattern == ("+", "+", "-"):
        return "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        return "Distress Signal"
    elif pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        return "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        return "Pre-Revenue"
    elif pattern == ("+", "-", "+"):
        return "Mixed"
    else:
        return "Mixed"
