from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ArbLeg:
    bookmaker: str
    selection: str
    odds: float
    side: str  # "back" or "lay"
    stake: float = 0.0


@dataclass
class ArbResult:
    arb_type: str  # "cross_book", "back_lay", "live_swing"
    profit_pct: float
    legs: list[ArbLeg] = field(default_factory=list)
    total_stake: float = 0.0
    guaranteed_profit: float = 0.0
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def calculate_equal_profit_stakes(total_investment: float, odds: list[float]) -> list[float]:
    """
    Calculate stakes for each outcome that guarantee equal profit regardless of result.

    For N outcomes with best odds [o1, o2, ...oN]:
        stake_i = total_investment / (o_i * sum(1/o_j for all j))
    """
    if not odds or any(o <= 0 for o in odds):
        return [0.0] * len(odds)

    inv_sum = sum(1.0 / o for o in odds)
    return [total_investment / (o * inv_sum) for o in odds]


def detect_cross_book_arb(
    odds_by_selection: dict[str, list[tuple[str, float]]],
    total_stake: float = 1000.0,
) -> ArbResult | None:
    """
    Detect cross-book arbitrage from odds across multiple bookmakers.

    Args:
        odds_by_selection: {
            "India": [("bet365", 2.10), ("pinnacle", 2.05), ("betfair", 2.08)],
            "Australia": [("bet365", 1.85), ("pinnacle", 1.95), ("betfair", 1.90)],
        }
        total_stake: Reference total investment for stake calculation.

    Returns:
        ArbResult if arbitrage exists (arb_pct < 1.0), else None.
    """
    if len(odds_by_selection) < 2:
        return None

    # Find best (highest) odds per selection across all bookmakers
    best_per_selection: dict[str, tuple[str, float]] = {}
    for selection, bookmaker_odds in odds_by_selection.items():
        if not bookmaker_odds:
            return None
        best = max(bookmaker_odds, key=lambda x: x[1])
        best_per_selection[selection] = best

    # Check if arb exists
    arb_pct = sum(1.0 / bo[1] for bo in best_per_selection.values())

    if arb_pct >= 1.0:
        return None  # No arbitrage

    profit_pct = (1.0 - arb_pct) * 100
    best_odds_list = [bo[1] for bo in best_per_selection.values()]
    stakes = calculate_equal_profit_stakes(total_stake, best_odds_list)

    legs = []
    for (selection, (bookmaker, odds)), stake in zip(best_per_selection.items(), stakes):
        legs.append(ArbLeg(
            bookmaker=bookmaker,
            selection=selection,
            odds=odds,
            side="back",
            stake=round(stake, 2),
        ))

    guaranteed_profit = round(total_stake * profit_pct / 100, 2)

    return ArbResult(
        arb_type="cross_book",
        profit_pct=round(profit_pct, 4),
        legs=legs,
        total_stake=total_stake,
        guaranteed_profit=guaranteed_profit,
    )


def detect_back_lay_arb(
    back_bookmaker: str,
    lay_bookmaker: str,
    selection: str,
    back_odds: float,
    lay_odds: float,
    commission: float = 0.05,
    back_stake: float = 100.0,
) -> ArbResult | None:
    """
    Detect back-lay arbitrage between a bookmaker (back) and exchange (lay).

    You BACK on the bookmaker and LAY on the exchange.

    Args:
        back_odds: Best back odds from a bookmaker.
        lay_odds: Lay odds on exchange (e.g., Betfair).
        commission: Exchange commission rate (e.g., 0.05 for 5%).
        back_stake: Reference back stake.

    Returns:
        ArbResult if both outcomes are profitable, else None.
    """
    if back_odds <= 1.0 or lay_odds <= 1.0:
        return None

    # Optimal lay stake formula
    lay_stake = (back_stake * back_odds) / (lay_odds - commission)

    # Profit if selection WINS (you win back bet, lose lay bet)
    profit_if_win = back_stake * (back_odds - 1) - lay_stake * (lay_odds - 1)

    # Profit if selection LOSES (you lose back bet, win lay bet minus commission)
    profit_if_lose = -back_stake + lay_stake * (1 - commission)

    if profit_if_win <= 0 or profit_if_lose <= 0:
        return None

    min_profit = min(profit_if_win, profit_if_lose)
    lay_liability = lay_stake * (lay_odds - 1)
    total_outlay = back_stake + lay_liability
    profit_pct = (min_profit / total_outlay) * 100

    legs = [
        ArbLeg(
            bookmaker=back_bookmaker,
            selection=selection,
            odds=back_odds,
            side="back",
            stake=round(back_stake, 2),
        ),
        ArbLeg(
            bookmaker=lay_bookmaker,
            selection=selection,
            odds=lay_odds,
            side="lay",
            stake=round(lay_stake, 2),
        ),
    ]

    return ArbResult(
        arb_type="back_lay",
        profit_pct=round(profit_pct, 4),
        legs=legs,
        total_stake=round(total_outlay, 2),
        guaranteed_profit=round(min_profit, 2),
    )


def detect_live_hedge(
    original_bookmaker: str,
    original_selection: str,
    original_odds: float,
    original_stake: float,
    hedge_bookmaker: str,
    opposite_selection: str,
    current_odds_opposite: float,
    commission: float = 0.0,
) -> ArbResult | None:
    """
    Detect live swing hedge opportunity.

    You placed a pre-match bet on one team. During live play, odds shifted
    (e.g., wickets fell, run rate changed). Can you now bet on the other
    side to lock in guaranteed profit?

    Args:
        original_odds: Odds when you placed the original bet.
        original_stake: Amount bet originally.
        current_odds_opposite: Current live odds on the OTHER team/outcome.
        commission: Exchange commission if hedging on exchange.

    Returns:
        ArbResult if guaranteed profit is positive, else None.
    """
    if original_odds <= 1.0 or current_odds_opposite <= 1.0:
        return None

    potential_return = original_stake * original_odds
    hedge_stake = potential_return / current_odds_opposite

    if commission > 0:
        # If hedge wins, profit is reduced by commission on the hedge winnings
        hedge_winnings = hedge_stake * (current_odds_opposite - 1)
        hedge_net = hedge_winnings * (1 - commission)
        profit_if_hedge_wins = hedge_net - original_stake
        profit_if_original_wins = original_stake * (original_odds - 1) - hedge_stake
        guaranteed_profit = min(profit_if_hedge_wins, profit_if_original_wins)
    else:
        # No commission — equal profit on both sides
        guaranteed_profit = potential_return - hedge_stake - original_stake

    if guaranteed_profit <= 0:
        return None

    total_outlay = original_stake + hedge_stake
    profit_pct = (guaranteed_profit / total_outlay) * 100

    legs = [
        ArbLeg(
            bookmaker=original_bookmaker,
            selection=original_selection,
            odds=original_odds,
            side="back",
            stake=round(original_stake, 2),
        ),
        ArbLeg(
            bookmaker=hedge_bookmaker,
            selection=opposite_selection,
            odds=current_odds_opposite,
            side="back",
            stake=round(hedge_stake, 2),
        ),
    ]

    return ArbResult(
        arb_type="live_swing",
        profit_pct=round(profit_pct, 4),
        legs=legs,
        total_stake=round(total_outlay, 2),
        guaranteed_profit=round(guaranteed_profit, 2),
    )
