import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.hedge_calculator import (
    calculate_hedge,
    calculate_target_hedge_odds,
    calculate_arb_stakes,
)


class TestCalculateHedge:
    def test_basic_hedge(self):
        """Bet 1000 on India at 2.50, hedge when Australia at 4.00."""
        result = calculate_hedge(
            original_odds=2.50,
            original_stake=1000.0,
            current_odds_opposite=4.00,
        )
        assert result.hedge_stake == 625.0
        assert result.guaranteed_profit == 875.0
        assert result.profit_pct > 0

    def test_no_profit_hedge(self):
        """Odds too tight — negative guaranteed profit."""
        result = calculate_hedge(
            original_odds=1.50,
            original_stake=1000.0,
            current_odds_opposite=1.80,
        )
        assert result.guaranteed_profit < 0

    def test_with_commission(self):
        result = calculate_hedge(
            original_odds=2.50,
            original_stake=1000.0,
            current_odds_opposite=4.00,
            commission=0.05,
        )
        # Commission should reduce profit
        assert result.guaranteed_profit < 875.0
        assert result.guaranteed_profit > 0


class TestTargetHedgeOdds:
    def test_target_profit(self):
        """What odds do I need to guarantee 500 profit?"""
        needed_odds = calculate_target_hedge_odds(
            original_odds=2.50,
            original_stake=1000.0,
            target_profit=500.0,
        )
        # Verify: at these odds, profit should be >= 500
        hedge_stake = (1000 * 2.50) / needed_odds
        profit = 1000 * 2.50 - hedge_stake - 1000
        assert profit >= 499.0  # Allow rounding

    def test_impossible_target(self):
        """Asking for more profit than the bet can return."""
        needed_odds = calculate_target_hedge_odds(
            original_odds=1.50,
            original_stake=100.0,
            target_profit=200.0,  # Can't make 200 from a 100 bet at 1.50
        )
        assert needed_odds == float("inf")


class TestArbStakes:
    def test_two_way(self):
        results = calculate_arb_stakes(1000.0, [2.10, 2.15])
        assert len(results) == 2
        # All payouts should be equal
        assert abs(results[0]["payout"] - results[1]["payout"]) < 0.01
        # All profits should be equal
        assert abs(results[0]["profit"] - results[1]["profit"]) < 0.01

    def test_stakes_sum(self):
        results = calculate_arb_stakes(1000.0, [2.10, 2.15])
        total = sum(r["stake"] for r in results)
        assert abs(total - 1000.0) < 1.0
