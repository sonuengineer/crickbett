import logging
import re

import redis.asyncio as aioredis

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.anti_detect import AntiDetectConfig
from app.services.odds_normalizer import normalize_odds

logger = logging.getLogger(__name__)

BET365_CRICKET_URL = "https://www.bet365.com/#/AC/B3/C20604979/D50/E2/F50/"


class Bet365Scraper(BaseScraper):
    """
    Scraper for Bet365.
    Most popular bookmaker — heavy anti-bot protection.
    Uses fractional odds by default in UK, decimal in other regions.
    """

    def __init__(self, redis: aioredis.Redis, anti_detect: AntiDetectConfig | None = None):
        super().__init__(
            bookmaker_name="bet365",
            display_name="Bet365",
            redis=redis,
            anti_detect=anti_detect,
        )

    async def discover_live_matches(self) -> list[dict]:
        """Discover live/upcoming cricket matches on Bet365."""
        matches = []

        try:
            await self.safe_navigate(BET365_CRICKET_URL)
            # Bet365 uses dynamic class names that change — use general selectors
            await self.page.wait_for_selector(
                "[class*='participant'], [class*='event'], .sl-MarketCouponFixture",
                timeout=20000,
            )

            # Look for match containers
            event_elements = await self.page.query_selector_all(
                "[class*='Fixture'], [class*='event-'], .sl-MarketCouponFixture"
            )

            for el in event_elements:
                try:
                    text = await el.inner_text()
                    # Bet365 typically shows teams on separate lines
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    # Look for a pair of team names
                    team_lines = [
                        l for l in lines
                        if not re.match(r"^[\d./:]+$", l) and len(l) > 2 and len(l) < 50
                    ]

                    if len(team_lines) >= 2:
                        is_live = any(
                            kw in text.lower()
                            for kw in ["in-play", "live", "in play"]
                        )
                        matches.append({
                            "team_a": team_lines[0],
                            "team_b": team_lines[1],
                            "is_live": is_live,
                        })
                except Exception as e:
                    logger.debug(f"[Bet365] Error parsing event: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Bet365] Failed to discover matches: {e}")

        logger.info(f"[Bet365] Discovered {len(matches)} matches")
        return matches

    async def scrape_cricket_odds(self) -> list[dict]:
        """Scrape cricket odds from Bet365."""
        all_odds = []

        try:
            await self.safe_navigate(BET365_CRICKET_URL)
            await self.page.wait_for_selector(
                "[class*='Participant'], [class*='odds'], .sl-MarketCouponFixture",
                timeout=20000,
            )

            # Find all match containers with odds
            fixtures = await self.page.query_selector_all(
                "[class*='Fixture'], .sl-MarketCouponFixture"
            )

            for fixture in fixtures:
                try:
                    odds_data = await self._parse_fixture(fixture)
                    all_odds.extend(odds_data)
                except Exception as e:
                    logger.debug(f"[Bet365] Error parsing fixture: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Bet365] Scrape failed: {e}")

        return all_odds

    async def _parse_fixture(self, fixture) -> list[dict]:
        """Parse a single fixture element for team names and odds."""
        odds_list = []

        text = await fixture.inner_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Separate team names from odds values
        teams = []
        odds_values = []

        for line in lines:
            try:
                val = float(line)
                odds_values.append(line)
            except ValueError:
                if "/" in line and all(p.strip().isdigit() for p in line.split("/")):
                    odds_values.append(line)
                elif len(line) > 2 and len(line) < 50 and not re.match(r"^[\d./:]+$", line):
                    teams.append(line)

        if len(teams) >= 2 and len(odds_values) >= 2:
            is_live = any(kw in text.lower() for kw in ["in-play", "live", "in play"])

            for i, (team, raw_odds) in enumerate(zip(teams[:2], odds_values[:2])):
                try:
                    decimal_odds = normalize_odds(raw_odds)
                    odds_list.append({
                        "match_team_a": teams[0],
                        "match_team_b": teams[1],
                        "market_type": "match_winner",
                        "selection": team,
                        "odds_decimal": decimal_odds,
                        "odds_original": raw_odds,
                        "odds_format": "auto",
                        "is_back": True,
                        "is_live": is_live,
                    })
                except Exception:
                    continue

        return odds_list
