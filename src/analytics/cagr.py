def calculate_cagr(start_val, end_val, n):
    """
    Computes CAGR for a given start and end value over n years.
    Returns: (cagr_value, flag)
    - cagr_value: numeric value of CAGR or None
    - flag: string code representing the edge case, or None

    Edge cases:
    1. Positive to Positive: compute normally.
    2. Positive to Negative: return (None, 'DECLINE_TO_LOSS')
    3. Negative to Positive: return (None, 'TURNAROUND')
    4. Negative to Negative: return (None, 'BOTH_NEGATIVE')
    5. Zero Base: return (None, 'ZERO_BASE') if start_val == 0
    6. Less than n years or missing data: return (None, 'INSUFFICIENT')
    """
    if start_val is None or end_val is None:
        return None, "INSUFFICIENT"

    try:
        start_val = float(start_val)
        end_val = float(end_val)
        n = float(n)
    except (ValueError, TypeError):
        return None, "INSUFFICIENT"

    if n <= 0:
        return None, "INSUFFICIENT"

    # Case 5: Zero Base
    if start_val == 0:
        return None, "ZERO_BASE"

    # Case 2: Positive to Negative
    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"

    # Case 3: Negative to Positive (or Negative to Zero)
    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"
    if start_val < 0 and end_val == 0:
        return None, "TURNAROUND"

    # Case 4: Negative to Negative
    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"

    # Positive to Zero (Standard computation gives -100%)
    if start_val > 0 and end_val == 0:
        return -100.0, None

    # Case 1: Positive to Positive (compute normally)
    if start_val > 0 and end_val > 0:
        try:
            val = ((end_val / start_val) ** (1.0 / n) - 1.0) * 100.0
            return val, None
        except Exception:
            return None, "INSUFFICIENT"

    return None, "INSUFFICIENT"
