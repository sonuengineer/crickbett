import re


def fractional_to_decimal(numerator: int, denominator: int) -> float:
    """Convert fractional odds to decimal. 5/2 -> 3.50"""
    return (numerator / denominator) + 1.0


def american_to_decimal(american: int) -> float:
    """Convert American/moneyline odds to decimal. +150 -> 2.50, -200 -> 1.50"""
    if american > 0:
        return (american / 100) + 1.0
    else:
        return (100 / abs(american)) + 1.0


def decimal_to_implied_probability(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability. 2.00 -> 0.50"""
    if decimal_odds <= 0:
        return 0.0
    return 1.0 / decimal_odds


def implied_probability_to_decimal(prob: float) -> float:
    """Convert implied probability to decimal odds. 0.50 -> 2.00"""
    if prob <= 0:
        return float("inf")
    return 1.0 / prob


def normalize_odds(raw_value: str, format_hint: str = "auto") -> float:
    """
    Auto-detect odds format and convert to decimal.

    Examples:
        "5/2"   -> 3.50  (fractional)
        "+150"  -> 2.50  (american positive)
        "-200"  -> 1.50  (american negative)
        "2.50"  -> 2.50  (decimal)
        "1.50"  -> 1.50  (decimal)
    """
    raw = raw_value.strip()

    if format_hint == "decimal" or (format_hint == "auto" and _is_decimal(raw)):
        return float(raw)

    if format_hint == "fractional" or (format_hint == "auto" and "/" in raw):
        match = re.match(r"(\d+)\s*/\s*(\d+)", raw)
        if match:
            return fractional_to_decimal(int(match.group(1)), int(match.group(2)))

    if format_hint == "american" or (format_hint == "auto" and _is_american(raw)):
        value = int(raw.replace("+", ""))
        return american_to_decimal(value)

    # Fallback: try as decimal
    return float(raw)


def _is_decimal(raw: str) -> bool:
    """Check if string looks like decimal odds (e.g., '2.50', '1.85')"""
    try:
        val = float(raw)
        return val > 0 and "." in raw and "/" not in raw
    except ValueError:
        return False


def _is_american(raw: str) -> bool:
    """Check if string looks like American odds (e.g., '+150', '-200')"""
    return bool(re.match(r"^[+-]\d+$", raw))


def calculate_margin(odds_list: list[float]) -> float:
    """
    Calculate bookmaker margin (overround) from a list of decimal odds for all outcomes.
    Returns margin as a percentage. E.g., 5.0 means 5% overround.
    A fair book has margin 0%. Arb exists when margin < 0%.
    """
    if not odds_list or any(o <= 0 for o in odds_list):
        return float("inf")
    inv_sum = sum(1.0 / o for o in odds_list)
    return (inv_sum - 1.0) * 100
