import json
import logging
import re

import redis.asyncio as aioredis

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.anti_detect import AntiDetectConfig

logger = logging.getLogger(__name__)

# Betfair Exchange cricket section URL
BETFAIR_CRICKET_URL = "https://www.betfair.com/exchange/plus/cricket"


class BetfairScraper(BaseScraper):
    """
    Scraper for Betfair Exchange.
    Betfair provides both BACK and LAY odds, making it critical for back-lay arb.
    """

    def __init__(self, redis: aioredis.Redis, anti_detect: AntiDetectConfig | None = None):
        super().__init__(
            bookmaker_name="betfair",
            display_name="Betfair Exchange",
            redis=redis,
            anti_detect=anti_detect,
        )

    async def discover_live_matches(self) -> list[dict]:
        """Find all live/upcoming cricket matches on Betfair."""
        matches = []

        try:
            await self.safe_navigate(BETFAIR_CRICKET_URL)
            await self.page.wait_for_selector(".event-list, .coupon-content", timeout=15000)

            # Get all match/event links in the cricket section
            event_elements = await self.page.query_selector_all(
                ".event-info, .event-header, [data-eventid]"
            )

            for el in event_elements:
                try:
                    text = await el.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    if len(lines) >= 2:
                        # Try to parse "Team A v Team B" pattern
                        for line in lines:
                            if " v " in line.lower():
                                parts = re.split(r"\s+v\s+", line, flags=re.IGNORECASE)
                                if len(parts) == 2:
                                    href = await el.get_attribute("href") or ""
                                    matches.append({
                                        "team_a": parts[0].strip(),
                                        "team_b": parts[1].strip(),
                                        "url": href if href.startswith("http") else f"https://www.betfair.com{href}",
                                        "is_live": "in-play" in text.lower() or "live" in text.lower(),
                                    })
                                break
                except Exception as e:
                    logger.debug(f"[Betfair] Error parsing match element: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Betfair] Failed to discover matches: {e}")

        logger.info(f"[Betfair] Discovered {len(matches)} matches")
        return matches

    async def scrape_cricket_odds(self) -> list[dict]:
        """Scrape all cricket odds from Betfair Exchange."""
        all_odds = []

        try:
            matches = await self.discover_live_matches()

            for match in matches:
                try:
                    match_odds = await self._scrape_match_odds(match)
                    all_odds.extend(match_odds)
                except Exception as e:
                    logger.error(
                        f"[Betfair] Error scraping {match.get('team_a')} v {match.get('team_b')}: {e}"
                    )

        except Exception as e:
            logger.error(f"[Betfair] Scrape failed: {e}")

        return all_odds

    async def _scrape_match_odds(self, match: dict) -> list[dict]:
        """Scrape odds for a single match on Betfair."""
        odds_list = []
        url = match.get("url", "")

        if not url:
            return odds_list

        try:
            await self.safe_navigate(url)
            await self.page.wait_for_selector(
                ".runner-line, .mv-runner-list, .coupon-content", timeout=15000
            )

            # Betfair shows runners with back/lay prices
            runners = await self.page.query_selector_all(
                ".runner-line, [data-runner-name]"
            )

            for runner in runners:
                try:
                    # Get runner/selection name
                    name_el = await runner.query_selector(
                        ".runner-name, .selection-name, [data-runner-name]"
                    )
                    if not name_el:
                        continue
                    selection = (await name_el.inner_text()).strip()

                    # Get back odds (best available)
                    back_els = await runner.query_selector_all(
                        ".bet-button-price.back-selection-button, .back .odds"
                    )
                    lay_els = await runner.query_selector_all(
                        ".bet-button-price.lay-selection-button, .lay .odds"
                    )

                    back_odds = await self._extract_odds(back_els)
                    lay_odds = await self._extract_odds(lay_els)

                    if back_odds:
                        odds_list.append({
                            "match_team_a": match["team_a"],
                            "match_team_b": match["team_b"],
                            "market_type": "match_winner",
                            "selection": selection,
                            "odds_decimal": back_odds,
                            "odds_original": str(back_odds),
                            "odds_format": "decimal",
                            "is_back": True,
                            "lay_odds": lay_odds,
                            "is_live": match.get("is_live", False),
                        })

                except Exception as e:
                    logger.debug(f"[Betfair] Error parsing runner: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Betfair] Error loading match page: {e}")

        return odds_list

    async def _extract_odds(self, elements) -> float | None:
        """Extract the best odds from a list of price elements."""
        for el in elements:
            try:
                text = (await el.inner_text()).strip()
                if text and text != "-":
                    return float(text)
            except (ValueError, Exception):
                continue
        return None
