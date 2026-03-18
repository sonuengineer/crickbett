import logging
import re

import redis.asyncio as aioredis

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.anti_detect import AntiDetectConfig

logger = logging.getLogger(__name__)

PINNACLE_CRICKET_URL = "https://www.pinnacle.com/en/cricket/matchups/"


class PinnacleScraper(BaseScraper):
    """
    Scraper for Pinnacle.
    Known for sharp/low-margin odds. Less anti-bot than Bet365.
    Uses decimal odds by default.
    """

    def __init__(self, redis: aioredis.Redis, anti_detect: AntiDetectConfig | None = None):
        super().__init__(
            bookmaker_name="pinnacle",
            display_name="Pinnacle",
            redis=redis,
            anti_detect=anti_detect,
        )

    async def discover_live_matches(self) -> list[dict]:
        """Discover cricket matches on Pinnacle."""
        matches = []

        try:
            await self.safe_navigate(PINNACLE_CRICKET_URL)
            await self.page.wait_for_selector(
                "[class*='matchup'], [class*='event-row'], .style_row",
                timeout=15000,
            )

            rows = await self.page.query_selector_all(
                "[class*='matchup'], [class*='event-row'], .style_row"
            )

            for row in rows:
                try:
                    text = await row.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    teams = [
                        l for l in lines
                        if not re.match(r"^[\d.+\-]+$", l) and len(l) > 2 and len(l) < 60
                    ]

                    if len(teams) >= 2:
                        is_live = any(
                            kw in text.lower() for kw in ["live", "in-play"]
                        )
                        matches.append({
                            "team_a": teams[0],
                            "team_b": teams[1],
                            "is_live": is_live,
                        })
                except Exception as e:
                    logger.debug(f"[Pinnacle] Error parsing row: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Pinnacle] Failed to discover matches: {e}")

        logger.info(f"[Pinnacle] Discovered {len(matches)} matches")
        return matches

    async def scrape_cricket_odds(self) -> list[dict]:
        """Scrape cricket odds from Pinnacle."""
        all_odds = []

        try:
            await self.safe_navigate(PINNACLE_CRICKET_URL)
            await self.page.wait_for_selector(
                "[class*='matchup'], [class*='event-row']", timeout=15000
            )

            rows = await self.page.query_selector_all(
                "[class*='matchup'], [class*='event-row']"
            )

            for row in rows:
                try:
                    text = await row.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    teams = []
                    odds_values = []

                    for line in lines:
                        try:
                            val = float(line)
                            if 1.01 <= val <= 100.0:
                                odds_values.append(val)
                            else:
                                teams.append(line)
                        except ValueError:
                            if len(line) > 2 and len(line) < 60:
                                teams.append(line)

                    if len(teams) >= 2 and len(odds_values) >= 2:
                        is_live = any(kw in text.lower() for kw in ["live", "in-play"])

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
                    logger.debug(f"[Pinnacle] Error parsing odds row: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Pinnacle] Scrape failed: {e}")

        return all_odds
