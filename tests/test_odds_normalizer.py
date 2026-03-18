import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.odds_normalizer import (
    fractional_to_decimal,
    american_to_decimal,
    decimal_to_implied_probability,
    normalize_odds,
    calculate_margin,
)


class TestFractionalToDecimal:
    def test_5_2(self):
        assert fractional_to_decimal(5, 2) == 3.5

    def test_1_1(self):
        assert fractional_to_decimal(1, 1) == 2.0

    def test_1_4(self):
        assert fractional_to_decimal(1, 4) == 1.25

    def test_10_1(self):
        assert fractional_to_decimal(10, 1) == 11.0


class TestAmericanToDecimal:
    def test_positive_150(self):
        assert american_to_decimal(150) == 2.5

    def test_positive_100(self):
        assert american_to_decimal(100) == 2.0

    def test_negative_200(self):
        assert american_to_decimal(-200) == 1.5

    def test_negative_100(self):
        assert american_to_decimal(-100) == 2.0

    def test_negative_150(self):
        assert abs(american_to_decimal(-150) - 1.6667) < 0.001


class TestImpliedProbability:
    def test_evens(self):
        assert decimal_to_implied_probability(2.0) == 0.5

    def test_heavy_favorite(self):
        assert abs(decimal_to_implied_probability(1.25) - 0.8) < 0.001

    def test_big_underdog(self):
        assert abs(decimal_to_implied_probability(5.0) - 0.2) < 0.001


class TestNormalizeOdds:
    def test_decimal_string(self):
        assert normalize_odds("2.50") == 2.5

    def test_fractional(self):
        assert normalize_odds("5/2") == 3.5

    def test_american_positive(self):
        assert normalize_odds("+150") == 2.5

    def test_american_negative(self):
        assert normalize_odds("-200") == 1.5

    def test_with_format_hint(self):
        assert normalize_odds("2.50", format_hint="decimal") == 2.5


class TestMargin:
    def test_fair_book(self):
        # Fair odds: 2.0 and 2.0 (50/50 market)
        margin = calculate_margin([2.0, 2.0])
        assert abs(margin) < 0.001

    def test_typical_overround(self):
        # Typical bookmaker: 1.91 and 1.91 (~4.7% margin)
        margin = calculate_margin([1.91, 1.91])
        assert margin > 0

    def test_arb_exists(self):
        # Arb scenario: both odds are generous enough
        margin = calculate_margin([2.10, 2.15])
        assert margin < 0  # Negative margin = arb opportunity

    def test_three_way(self):
        # Three-way market (e.g., Test match with draw)
        margin = calculate_margin([3.0, 3.0, 3.0])
        assert abs(margin) < 0.001
