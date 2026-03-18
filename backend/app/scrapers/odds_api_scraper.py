"""
Real data source using The Odds API (https://the-odds-api.com).

Free tier: 500 requests/month.
Returns real aggregated odds from 70+ bookmakers worldwide.
No Playwright needed — simple REST API.

Sign up at: https://the-odds-api.com/#get-access
"""

import json
import logging
from datetime import datetime, timezone

import httpx
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"

# The Odds API bookmaker keys → our bookmaker names
BOOKMAKER_MAP = {
    "bet365": "bet365",
    "betfair_ex_uk": "betfair",
    "betfair": "betfair",
    "pinnacle": "pinnacle",
    "onexbet": "1xbet",
    "1xbet": "1xbet",
    "betway": "betway",
    "unibet": "unibet",
    "williamhill": "william_hill",
    "marathonbet": "marathonbet",
    "betsson": "betsson",
    "betonlineag": "betonline",
    "matchbook": "matchbook",
    "smarkets": "smarkets",
    "betclic": "betclic",
    "coolbet": "coolbet",
    "sport888": "888sport",
    "bwin": "bwin",
    "ladbrokes_au": "ladbrokes",
}

# Market type mapping: The Odds API → our constants
MARKET_MAP = {
    "h2h": "match_winner",
    "totals": "total_runs",
    "spreads": "handicap",
}


class OddsApiScraper:
    """
    Fetches real cricket odds from The Odds API.
    Works immediately — no browser automation or anti-detect needed.
    """

    def __init__(self, api_key: str, redis: aioredis.Redis, regions: str = "uk,eu,au"):
        self.api_key = api_key
        self.redis = redis
        self.regions = regions
        self._client = httpx.AsyncClient(timeout=30.0)
        self._requests_used = 0
        self._requests_remaining = None

    async def close(self):
        await self._client.aclose()

    async def fetch_cricket_events(self) -> list[dict]:
        """Get all upcoming + live cricket events."""
        url = f"{BASE_URL}/sports/cricket/odds"
        params = {
            "apiKey": self.api_key,
            "regions": self.regions,
            "markets": "h2h,totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }

        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()

            # Track API usage
            self._requests_used = resp.headers.get("x-requests-used", "?")
            self._requests_remaining = resp.headers.get("x-requests-remaining", "?")
            logger.info(
                f"[OddsAPI] Requests used: {self._requests_used}, "
                f"remaining: {self._requests_remaining}"
            )

            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("[OddsAPI] Invalid API key")
            elif e.response.status_code == 429:
                logger.error("[OddsAPI] Rate limit exceeded — wait or upgrade plan")
            else:
                logger.error(f"[OddsAPI] HTTP {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"[OddsAPI] Request failed: {e}")
            return []

    async def scrape_and_publish(self) -> int:
        """
        Fetch all cricket odds and publish to Redis.
        Returns total number of odds published.
        """
        events = await self.fetch_cricket_events()
        total_odds = 0

        for event in events:
            team_a = event.get("home_team", "")
            team_b = event.get("away_team", "")
            start_time = event.get("commence_time", "")
            sport_title = event.get("sport_title", "Cricket")
            is_live = event.get("commence_time", "") <= datetime.now(timezone.utc).isoformat()

            for bookmaker_data in event.get("bookmakers", []):
                bk_key = bookmaker_data.get("key", "")
                bk_name = BOOKMAKER_MAP.get(bk_key, bk_key)
                last_update = bookmaker_data.get("last_update", "")

                for market in bookmaker_data.get("markets", []):
                    market_key = market.get("key", "h2h")
                    market_type = MARKET_MAP.get(market_key, market_key)

                    for outcome in market.get("outcomes", []):
                        selection = outcome.get("name", "")
                        odds_decimal = outcome.get("price", 0)

                        if odds_decimal <= 1.0:
                            continue  # Skip invalid odds

                        odds_dict = {
                            "bookmaker": bk_name,
                            "match_team_a": team_a,
                            "match_team_b": team_b,
                            "tournament": sport_title,
                            "start_time": start_time,
                            "market_type": market_type,
                            "selection": selection,
                            "odds_decimal": odds_decimal,
                            "odds_original": str(odds_decimal),
                            "odds_format": "decimal",
                            "is_back": True,
                            "lay_odds": None,
                            "available_volume": None,
                            "is_live": is_live,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "source": "the_odds_api",
                            "last_update": last_update,
                        }

                        # Publish to Redis
                        message = json.dumps(odds_dict, default=str)
                        await self.redis.publish("cricket:odds:raw", message)

                        # Update latest-odds hash
                        match_key = f"{team_a}_{team_b}"
                        redis_key = f"cricket:odds:latest:{match_key}:{market_type}"
                        await self.redis.hset(redis_key, bk_name, message)
                        await self.redis.expire(redis_key, 300)

                        total_odds += 1

        if total_odds:
            logger.info(f"[OddsAPI] Published {total_odds} odds from {len(events)} events")
        else:
            logger.warning("[OddsAPI] No cricket odds found (may be no live/upcoming matches)")

        return total_odds

    async def get_live_scores(self) -> list[dict]:
        """Get live scores for in-play matches."""
        url = f"{BASE_URL}/sports/cricket/scores"
        params = {
            "apiKey": self.api_key,
            "daysFrom": 1,
        }

        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[OddsAPI] Scores fetch failed: {e}")
            return []

    def get_usage(self) -> dict:
        return {
            "requests_used": self._requests_used,
            "requests_remaining": self._requests_remaining,
        }
