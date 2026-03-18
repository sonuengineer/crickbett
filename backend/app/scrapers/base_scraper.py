import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import redis.asyncio as aioredis
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.scrapers.anti_detect import AntiDetectConfig, STEALTH_SCRIPT

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base for all bookmaker scrapers.
    Handles Playwright browser lifecycle, anti-detection, and Redis publishing.
    """

    def __init__(
        self,
        bookmaker_name: str,
        display_name: str,
        redis: aioredis.Redis,
        anti_detect: AntiDetectConfig | None = None,
    ):
        self.bookmaker_name = bookmaker_name
        self.display_name = display_name
        self.redis = redis
        self.anti_detect = anti_detect or AntiDetectConfig()
        self._playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def start_browser(self):
        """Launch Playwright browser with anti-detect settings."""
        self._playwright = await async_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]

        proxy = self.anti_detect.get_random_proxy()

        self.browser = await self._playwright.chromium.launch(
            headless=True,
            args=launch_args,
        )

        context_opts = {
            "user_agent": self.anti_detect.get_random_ua(),
            "viewport": self.anti_detect.get_viewport(),
            "locale": "en-US",
            "timezone_id": "Asia/Kolkata",
        }
        if proxy:
            context_opts["proxy"] = proxy

        self.context = await self.browser.new_context(**context_opts)
        self.page = await self.context.new_page()

        # Inject stealth script
        await self.page.add_init_script(STEALTH_SCRIPT)

        logger.info(f"[{self.display_name}] Browser started")

    async def restart_browser(self):
        """Restart browser with fresh fingerprint."""
        await self.close()
        self.anti_detect.reset_count()
        await self.start_browser()

    @abstractmethod
    async def scrape_cricket_odds(self) -> list[dict]:
        """
        Scrape all cricket odds from this bookmaker.

        Returns list of dicts, each containing:
            - match_team_a: str
            - match_team_b: str
            - tournament: str (optional)
            - start_time: str (ISO format, optional)
            - market_type: str
            - selection: str
            - odds_decimal: float
            - odds_original: str
            - odds_format: str
            - is_back: bool
            - lay_odds: float (optional, for exchanges)
            - available_volume: float (optional)
            - is_live: bool
        """
        ...

    @abstractmethod
    async def discover_live_matches(self) -> list[dict]:
        """
        Discover all live/upcoming cricket matches on this bookmaker.

        Returns list of dicts with match info.
        """
        ...

    async def publish_odds(self, odds_list: list[dict]):
        """Publish scraped odds to Redis for the arb engine."""
        for odds in odds_list:
            odds["bookmaker"] = self.bookmaker_name
            odds["scraped_at"] = datetime.now(timezone.utc).isoformat()

            message = json.dumps(odds, default=str)
            await self.redis.publish("cricket:odds:raw", message)

            # Update latest-odds hash for fast lookup
            match_key = f"{odds.get('match_team_a', '')}_{odds.get('match_team_b', '')}"
            market = odds.get("market_type", "unknown")
            redis_key = f"cricket:odds:latest:{match_key}:{market}"
            await self.redis.hset(redis_key, self.bookmaker_name, message)
            await self.redis.expire(redis_key, 300)  # 5 min TTL

        if odds_list:
            logger.info(
                f"[{self.display_name}] Published {len(odds_list)} odds to Redis"
            )

    async def close(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self.page = None
        logger.info(f"[{self.display_name}] Browser closed")

    async def safe_navigate(self, url: str, wait_until: str = "domcontentloaded"):
        """Navigate with anti-detect delay."""
        await self.anti_detect.random_delay()
        await self.page.goto(url, wait_until=wait_until, timeout=30000)

        if self.anti_detect.increment_request():
            logger.info(f"[{self.display_name}] Session limit reached, restarting browser")
            await self.restart_browser()
