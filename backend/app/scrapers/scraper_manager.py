import asyncio
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.scrapers.anti_detect import AntiDetectConfig
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.bet365_scraper import Bet365Scraper
from app.scrapers.betfair_scraper import BetfairScraper
from app.scrapers.betway_scraper import BetwayScraper
from app.scrapers.onexbet_scraper import OneXBetScraper
from app.scrapers.pinnacle_scraper import PinnacleScraper

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "bet365": Bet365Scraper,
    "betfair": BetfairScraper,
    "pinnacle": PinnacleScraper,
    "1xbet": OneXBetScraper,
    "betway": BetwayScraper,
}


class ScraperManager:
    """Orchestrates all bookmaker scrapers with health monitoring."""

    def __init__(
        self,
        redis: aioredis.Redis,
        proxy_list: str = "",
        enabled_scrapers: list[str] | None = None,
    ):
        self.redis = redis
        self.anti_detect = AntiDetectConfig(proxy_list=proxy_list)
        self.scrapers: dict[str, BaseScraper] = {}
        self.health: dict[str, dict] = {}

        enabled = enabled_scrapers or list(SCRAPER_REGISTRY.keys())
        for name in enabled:
            if name in SCRAPER_REGISTRY:
                self.scrapers[name] = SCRAPER_REGISTRY[name](
                    redis=redis, anti_detect=self.anti_detect
                )
                self.health[name] = {
                    "status": "idle",
                    "last_success": None,
                    "last_error": None,
                    "error_count": 0,
                    "odds_count": 0,
                }

    async def start_all(self):
        """Start browser instances for all scrapers."""
        tasks = [scraper.start_browser() for scraper in self.scrapers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Started {len(self.scrapers)} scrapers")

    async def stop_all(self):
        """Close all browser instances."""
        tasks = [scraper.close() for scraper in self.scrapers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All scrapers stopped")

    async def scrape_all(self) -> dict[str, list[dict]]:
        """
        Run all scrapers concurrently and collect odds.
        Returns dict of bookmaker_name -> list of odds dicts.
        """
        results = {}

        async def _run_scraper(name: str, scraper: BaseScraper):
            self.health[name]["status"] = "scraping"
            try:
                odds = await scraper.scrape_cricket_odds()
                await scraper.publish_odds(odds)
                self.health[name]["status"] = "ok"
                self.health[name]["last_success"] = datetime.now(timezone.utc).isoformat()
                self.health[name]["odds_count"] = len(odds)
                self.health[name]["error_count"] = 0
                results[name] = odds
                logger.info(f"[{name}] Scraped {len(odds)} odds")
            except Exception as e:
                self.health[name]["status"] = "error"
                self.health[name]["last_error"] = str(e)
                self.health[name]["error_count"] += 1
                logger.error(f"[{name}] Scrape failed: {e}")
                results[name] = []

                # Restart browser after 3 consecutive errors
                if self.health[name]["error_count"] >= 3:
                    logger.warning(f"[{name}] Too many errors, restarting browser")
                    try:
                        await scraper.restart_browser()
                        self.health[name]["error_count"] = 0
                    except Exception as restart_err:
                        logger.error(f"[{name}] Browser restart failed: {restart_err}")

        tasks = [
            _run_scraper(name, scraper)
            for name, scraper in self.scrapers.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def get_health(self) -> dict[str, dict]:
        """Get health status of all scrapers."""
        return self.health.copy()


async def run_api_scraper(redis: aioredis.Redis, api_key: str, regions: str) -> int:
    """Run the Odds API scraper (no Playwright needed). Returns odds count."""
    from app.scrapers.odds_api_scraper import OddsApiScraper

    scraper = OddsApiScraper(api_key=api_key, redis=redis, regions=regions)
    try:
        count = await scraper.scrape_and_publish()
        return count
    finally:
        await scraper.close()


async def run_demo_scraper(redis: aioredis.Redis, arb_frequency: float = 0.3) -> int:
    """Run the demo scraper (generates mock data). Returns odds count."""
    from app.scrapers.demo_scraper import DemoScraper

    scraper = DemoScraper(redis=redis, arb_frequency=arb_frequency)
    count = await scraper.scrape_and_publish()
    return count
