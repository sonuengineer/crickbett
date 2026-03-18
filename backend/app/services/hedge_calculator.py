from dataclasses import dataclass


@dataclass
class HedgeCalcResult:
    hedge_stake: float
    profit_if_original_wins: float
    profit_if_hedge_wins: float
    guaranteed_profit: float
    profit_pct: float
    total_outlay: float


def calculate_hedge(
    original_odds: float,
    original_stake: float,
    current_odds_opposite: float,
    commission: float = 0.0,
) -> HedgeCalcResult:
    """
    Calculate optimal hedge stake and expected profits.

    Given an existing bet, calculate how much to bet on the opposite
    outcome at current odds to guarantee profit (or minimize loss).
    """
    potential_return = original_stake * original_odds
    hedge_stake = potential_return / current_odds_opposite

    profit_if_original_wins = original_stake * (original_odds - 1) - hedge_stake

    if commission > 0:
        hedge_winnings = hedge_stake * (current_odds_opposite - 1)
        hedge_net = hedge_winnings * (1 - commission)
        profit_if_hedge_wins = hedge_net - original_stake
    else:
        profit_if_hedge_wins = hedge_stake * (current_odds_opposite - 1) - original_stake

    guaranteed_profit = min(profit_if_original_wins, profit_if_hedge_wins)
    total_outlay = original_stake + hedge_stake
    profit_pct = (guaranteed_profit / total_outlay) * 100 if total_outlay > 0 else 0.0

    return HedgeCalcResult(
        hedge_stake=round(hedge_stake, 2),
        profit_if_original_wins=round(profit_if_original_wins, 2),
        profit_if_hedge_wins=round(profit_if_hedge_wins, 2),
        guaranteed_profit=round(guaranteed_profit, 2),
        profit_pct=round(profit_pct, 4),
        total_outlay=round(total_outlay, 2),
    )


def calculate_target_hedge_odds(
    original_odds: float,
    original_stake: float,
    target_profit: float,
) -> float:
    """
    Calculate what odds you need on the opposite side to achieve a target profit.

    Returns the minimum decimal odds needed on the hedge side.
    """
    potential_return = original_stake * original_odds
    needed_return = original_stake + target_profit
    # hedge_stake * current_odds = potential_return
    # hedge_stake = potential_return / current_odds
    # profit = potential_return - hedge_stake - original_stake >= target_profit
    # potential_return - (potential_return / odds) - original_stake >= target_profit
    # potential_return / odds <= potential_return - original_stake - target_profit
    # odds >= potential_return / (potential_return - needed_return)
    denominator = potential_return - needed_return
    if denominator <= 0:
        return float("inf")  # impossible
    return round(potential_return / denominator, 4)


def calculate_arb_stakes(
    total_investment: float,
    odds: list[float],
) -> list[dict]:
    """
    For a multi-outcome market, calculate stakes per outcome to guarantee equal profit.

    Returns list of {"stake": float, "payout": float, "profit": float} per outcome.
    """
    if not odds or any(o <= 0 for o in odds):
        return []

    inv_sum = sum(1.0 / o for o in odds)
    results = []

    for o in odds:
        stake = total_investment / (o * inv_sum)
        payout = stake * o
        profit = payout - total_investment
        results.append({
            "stake": round(stake, 2),
            "payout": round(payout, 2),
            "profit": round(profit, 2),
        })

    return results
