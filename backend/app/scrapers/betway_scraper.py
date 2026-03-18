import logging
import re

import redis.asyncio as aioredis

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.anti_detect import AntiDetectConfig

logger = logging.getLogger(__name__)

BETWAY_CRICKET_URL = "https://www.betway.com/en/sports/grp/cricket"


class BetwayScraper(BaseScraper):
    """Scraper for Betway. Popular in India for cricket betting."""

    def __init__(self, redis: aioredis.Redis, anti_detect: AntiDetectConfig | None = None):
        super().__init__(
            bookmaker_name="betway",
            display_name="Betway",
            redis=redis,
            anti_detect=anti_detect,
        )

    async def discover_live_matches(self) -> list[dict]:
        """Discover cricket matches on Betway."""
        matches = []

        try:
            await self.safe_navigate(BETWAY_CRICKET_URL)
            await self.page.wait_for_selector(
                "[class*='event'], [class*='match'], [data-testid*='event']",
                timeout=15000,
            )

            items = await self.page.query_selector_all(
                "[class*='eventCard'], [class*='match-row'], [data-testid*='event']"
            )

            for item in items:
                try:
                    text = await item.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    teams = [
                        l for l in lines
                        if not re.match(r"^[\d.+\-:]+$", l) and len(l) > 2 and len(l) < 60
                    ]

                    if len(teams) >= 2:
                        is_live = any(kw in text.lower() for kw in ["live", "in-play"])
                        matches.append({
                            "team_a": teams[0],
                            "team_b": teams[1],
                            "is_live": is_live,
                        })
                except Exception as e:
                    logger.debug(f"[Betway] Error parsing item: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Betway] Failed to discover matches: {e}")

        logger.info(f"[Betway] Discovered {len(matches)} matches")
        return matches

    async def scrape_cricket_odds(self) -> list[dict]:
        """Scrape cricket odds from Betway."""
        all_odds = []

        try:
            await self.safe_navigate(BETWAY_CRICKET_URL)
            await self.page.wait_for_selector(
                "[class*='event'], [class*='match']", timeout=15000
            )

            items = await self.page.query_selector_all(
                "[class*='eventCard'], [class*='match-row']"
            )

            for item in items:
                try:
                    text = await item.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    teams = []
                    odds_values = []

                    for line in lines:
                        try:
                            val = float(line)
                            if 1.01 <= val <= 100.0:
                                odds_values.append(val)
                            else:
                                if len(line) > 2:
                                    teams.append(line)
                        except ValueError:
                            if len(line) > 2 and len(line) < 60 and not re.match(r"^[\d.+\-:]+$", line):
                                teams.append(line)

                    if len(teams) >= 2 and len(odds_values) >= 2:
                        is_live = any(kw in text.lower() for kw in ["live"])
                        for team, odds in zip(teams[:2], odds_values[:2]):
                            all_odds.append({
                                "match_team_a": teams[0],
                                "match_team_b": teams[1],
                                "market_type": "match_winner",
                                "selection": team,
                                "odds_decimal": odds,
                                "odds_original": str(odds),
                                "odds_format": "decimal",
                                "is_back": True,
                                "is_live": is_live,
                            })

                except Exception as e:
                    logger.debug(f"[Betway] Error parsing odds: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Betway] Scrape failed: {e}")

        return all_odds
