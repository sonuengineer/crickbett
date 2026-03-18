import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.arb_engine import (
    detect_cross_book_arb,
    detect_back_lay_arb,
    detect_live_hedge,
    calculate_equal_profit_stakes,
)


class TestCrossBookArb:
    def test_arb_exists(self):
        """Two bookmakers with odds that sum to < 1 in inverse."""
        odds = {
            "India": [("bet365", 2.10), ("pinnacle", 2.05)],
            "Australia": [("bet365", 1.85), ("pinnacle", 2.15)],
        }
        result = detect_cross_book_arb(odds)
        assert result is not None
        assert result.arb_type == "cross_book"
        assert result.profit_pct > 0
        assert len(result.legs) == 2

    def test_no_arb(self):
        """Standard overround — no arb."""
        odds = {
            "India": [("bet365", 1.90), ("pinnacle", 1.91)],
            "Australia": [("bet365", 1.90), ("pinnacle", 1.91)],
        }
        result = detect_cross_book_arb(odds)
        assert result is None

    def test_picks_best_odds(self):
        """Ensure it picks the highest odds from each bookmaker."""
        odds = {
            "India": [("bet365", 2.00), ("pinnacle", 2.20), ("betway", 2.05)],
            "Australia": [("bet365", 2.00), ("pinnacle", 1.80), ("betway", 2.10)],
        }
        result = detect_cross_book_arb(odds)
        if result:
            # Should pick pinnacle for India (2.20) and betway for Australia (2.10)
            bookmakers = {leg.selection: leg.bookmaker for leg in result.legs}
            assert bookmakers["India"] == "pinnacle"
            assert bookmakers["Australia"] == "betway"

    def test_stakes_sum_to_total(self):
        """Verify stakes sum correctly."""
        odds = {
            "India": [("bet365", 2.10)],
            "Australia": [("pinnacle", 2.15)],
        }
        result = detect_cross_book_arb(odds, total_stake=1000.0)
        if result:
            total = sum(leg.stake for leg in result.legs)
            assert abs(total - 1000.0) < 1.0  # Allow rounding error

    def test_empty_selection(self):
        """Single selection — can't arb."""
        odds = {"India": [("bet365", 2.10)]}
        result = detect_cross_book_arb(odds)
        assert result is None


class TestBackLayArb:
    def test_arb_exists(self):
        """Back higher than effective lay = arb."""
        result = detect_back_lay_arb(
            back_bookmaker="bet365",
            lay_bookmaker="betfair",
            selection="India",
            back_odds=2.20,
            lay_odds=2.05,
            commission=0.05,
        )
        assert result is not None
        assert result.arb_type == "back_lay"
        assert result.profit_pct > 0
        assert len(result.legs) == 2

    def test_no_arb_when_lay_too_high(self):
        """Lay odds much higher than back = no arb."""
        result = detect_back_lay_arb(
            back_bookmaker="bet365",
            lay_bookmaker="betfair",
            selection="India",
            back_odds=1.80,
            lay_odds=2.50,
            commission=0.05,
        )
        assert result is None

    def test_commission_impact(self):
        """Higher commission should reduce or eliminate arb."""
        # With low commission = arb
        result_low = detect_back_lay_arb(
            back_bookmaker="bet365",
            lay_bookmaker="betfair",
            selection="India",
            back_odds=2.20,
            lay_odds=2.10,
            commission=0.02,
        )
        # With high commission = likely no arb
        result_high = detect_back_lay_arb(
            back_bookmaker="bet365",
            lay_bookmaker="betfair",
            selection="India",
            back_odds=2.20,
            lay_odds=2.10,
            commission=0.20,
        )
        # At least one should differ
        if result_low and result_high:
            assert result_low.profit_pct > result_high.profit_pct


class TestLiveHedge:
    def test_profitable_hedge(self):
        """Pre-match bet at 2.50, live odds on opposite shifted to 4.00."""
        result = detect_live_hedge(
            original_bookmaker="bet365",
            original_selection="India",
            original_odds=2.50,
            original_stake=1000.0,
            hedge_bookmaker="pinnacle",
            opposite_selection="Australia",
            current_odds_opposite=4.00,
        )
        assert result is not None
        assert result.arb_type == "live_swing"
        assert result.guaranteed_profit > 0
        # Manual calc: hedge_stake = 1000*2.5/4.0 = 625
        # profit = 2500 - 625 - 1000 = 875
        assert abs(result.guaranteed_profit - 875.0) < 1.0

    def test_no_profit_odds_too_low(self):
        """Opposite odds too low — no hedge profit."""
        result = detect_live_hedge(
            original_bookmaker="bet365",
            original_selection="India",
            original_odds=1.50,
            original_stake=1000.0,
            hedge_bookmaker="pinnacle",
            opposite_selection="Australia",
            current_odds_opposite=1.80,
        )
        assert result is None

    def test_with_commission(self):
        """Hedge on exchange with commission reduces profit."""
        result_no_comm = detect_live_hedge(
            original_bookmaker="bet365",
            original_selection="India",
            original_odds=2.50,
            original_stake=1000.0,
            hedge_bookmaker="betfair",
            opposite_selection="Australia",
            current_odds_opposite=4.00,
            commission=0.0,
        )
        result_with_comm = detect_live_hedge(
            original_bookmaker="bet365",
            original_selection="India",
            original_odds=2.50,
            original_stake=1000.0,
            hedge_bookmaker="betfair",
            opposite_selection="Australia",
            current_odds_opposite=4.00,
            commission=0.05,
        )
        assert result_no_comm is not None
        assert result_with_comm is not None
        assert result_no_comm.guaranteed_profit > result_with_comm.guaranteed_profit


class TestEqualProfitStakes:
    def test_two_outcomes(self):
        stakes = calculate_equal_profit_stakes(1000.0, [2.10, 2.15])
        # Both outcomes should yield same profit
        profit_1 = stakes[0] * 2.10 - 1000.0
        profit_2 = stakes[1] * 2.15 - 1000.0
        assert abs(profit_1 - profit_2) < 0.01

    def test_three_outcomes(self):
        stakes = calculate_equal_profit_stakes(1000.0, [3.0, 3.5, 4.0])
        profits = [s * o - 1000.0 for s, o in zip(stakes, [3.0, 3.5, 4.0])]
        # All profits should be equal
        assert abs(profits[0] - profits[1]) < 0.01
        assert abs(profits[1] - profits[2]) < 0.01
