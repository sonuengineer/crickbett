"""
Demo data source that generates realistic mock cricket odds.

Use this when:
- You don't have an Odds API key yet
- You want to test the full pipeline (scraper → Redis → arb engine → WS → Telegram)
- You want to see arb detection in action without live data

MONITOR-AWARE: Reads active hedge monitors from Redis and generates
odds specifically for those matches, simulating realistic live drift
that can trigger hedge alerts.
"""

import json
import logging
import random
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Realistic cricket match scenarios (for general arb detection)
DEMO_MATCHES = [
    {"team_a": "India", "team_b": "Australia", "tournament": "ICC World Cup 2025"},
    {"team_a": "England", "team_b": "South Africa", "tournament": "T20 World Cup"},
    {"team_a": "Mumbai Indians", "team_b": "Chennai Super Kings", "tournament": "IPL 2025"},
    {"team_a": "Royal Challengers Bangalore", "team_b": "Kolkata Knight Riders", "tournament": "IPL 2025"},
    {"team_a": "Pakistan", "team_b": "New Zealand", "tournament": "ODI Series"},
]

BOOKMAKERS = ["bet365", "betfair", "pinnacle", "1xbet", "betway"]

# Base odds ranges (realistic for cricket match winner)
BASE_ODDS = {
    "favourite": (1.45, 1.95),
    "underdog": (2.10, 3.50),
    "draw": (8.0, 15.0),  # Only for Tests
}


class DemoScraper:
    """
    Generates realistic mock cricket odds with occasional arb opportunities.

    MONITOR-AWARE: Also generates odds specifically for matches the user
    is monitoring via the Hedge Monitor, with realistic live-match drift
    that progressively moves toward (and sometimes past) breakeven odds
    to trigger hedge alerts.
    """

    def __init__(self, redis: aioredis.Redis, arb_frequency: float = 0.3):
        self.redis = redis
        self.arb_frequency = arb_frequency
        self._cycle_count = 0
        # Track cumulative odds drift per monitored match for realism
        # Key: monitor_id, Value: {"drift": float, "base_odds": float}
        self._match_drift: dict[str, dict] = {}

    async def scrape_and_publish(self) -> int:
        """Generate demo odds and publish to Redis. Returns count published."""
        self._cycle_count += 1
        total = 0

        # 1. Generate odds for MONITORED matches (hedge monitor feature)
        total += await self._generate_monitored_match_odds()

        # 2. Generate regular demo odds (for general arb detection)
        total += await self._generate_regular_odds()

        return total

    async def _generate_monitored_match_odds(self) -> int:
        """
        Read active hedge monitors from Redis and generate live odds
        for those specific matches. Simulates realistic live-match drift:
        - Underdog odds gradually increase as match progresses
        - Occasional spikes (simulating wickets/run-outs)
        - Eventually crosses breakeven threshold → triggers hedge alert
        """
        count = 0

        try:
            # Read all active monitors from Redis
            monitors_raw = await self.redis.hgetall("cricket:hedge:monitors")
            if not monitors_raw:
                return 0

            active_monitors = []
            for mid, mdata in monitors_raw.items():
                monitor = json.loads(mdata)
                if monitor.get("status") == "monitoring":
                    monitor["_id"] = mid if isinstance(mid, str) else mid.decode()
                    active_monitors.append(monitor)

            if not active_monitors:
                return 0

            logger.info(f"[Demo] Generating odds for {len(active_monitors)} monitored match(es)")

            for monitor in active_monitors:
                team_a = monitor["match_team_a"]
                team_b = monitor["match_team_b"]
                tournament = monitor.get("tournament", "Live Match")
                selection = monitor["selection"]
                original_odds = monitor["odds"]
                breakeven = monitor.get("breakeven_odds", original_odds / (original_odds - 1))
                monitor_id = monitor["_id"]

                # Determine the opposite team
                opposite = team_b if selection == team_a else team_a

                # Initialize or update drift state for this monitor
                if monitor_id not in self._match_drift:
                    # Start opposite odds slightly below breakeven
                    start_odds = breakeven * random.uniform(0.75, 0.92)
                    self._match_drift[monitor_id] = {
                        "opposite_odds": start_odds,
                        "selection_odds": original_odds * random.uniform(0.85, 1.1),
                        "cycles": 0,
                    }

                drift = self._match_drift[monitor_id]
                drift["cycles"] += 1

                # Simulate live odds movement
                # Opposite team odds trend upward (simulating match momentum shifts)
                base_change = random.uniform(0.02, 0.12)

                # Occasional big spike (wicket fell, big over, etc.) — ~15% chance
                if random.random() < 0.15:
                    base_change += random.uniform(0.25, 0.70)
                    logger.info(f"[Demo] WICKET EVENT for {team_a} vs {team_b}! Odds spike +{base_change:.2f}")

                # Small chance of odds dropping (opposite team hits back) — ~20% chance
                if random.random() < 0.20:
                    base_change = -random.uniform(0.05, 0.15)

                drift["opposite_odds"] = max(1.10, drift["opposite_odds"] + base_change)
                # Selection odds move inversely (if opposite goes up, your pick goes down)
                drift["selection_odds"] = max(1.05, drift["selection_odds"] - base_change * 0.3)

                current_opposite_odds = round(drift["opposite_odds"], 2)
                current_selection_odds = round(drift["selection_odds"], 2)

                # Log comparison with breakeven
                above_breakeven = current_opposite_odds > breakeven
                logger.info(
                    f"[Demo] {team_a} vs {team_b}: "
                    f"{opposite} odds = {current_opposite_odds} "
                    f"(breakeven = {breakeven:.2f}) "
                    f"{'→ HEDGE AVAILABLE!' if above_breakeven else '→ monitoring...'}"
                )

                # Publish odds for EACH bookmaker (with slight variations)
                for bk in BOOKMAKERS:
                    bk_noise = random.uniform(-0.08, 0.08)

                    # Publish opposite team odds (this is what hedge monitor checks)
                    opp_odds = max(1.10, round(current_opposite_odds + bk_noise, 2))
                    await self._publish_odds(
                        bookmaker=bk,
                        team_a=team_a,
                        team_b=team_b,
                        tournament=tournament,
                        selection=opposite,
                        odds=opp_odds,
                        is_live=True,
                    )
                    count += 1

                    # Publish selection odds too (for completeness)
                    sel_odds = max(1.05, round(current_selection_odds + bk_noise * 0.5, 2))
                    await self._publish_odds(
                        bookmaker=bk,
                        team_a=team_a,
                        team_b=team_b,
                        tournament=tournament,
                        selection=selection,
                        odds=sel_odds,
                        is_live=True,
                    )
                    count += 1

        except Exception as e:
            logger.error(f"[Demo] Error generating monitored odds: {e}")

        return count

    async def _generate_regular_odds(self) -> int:
        """Generate standard demo odds for general arb detection."""
        count = 0
        inject_arb = random.random() < self.arb_frequency

        # Pick 2-3 matches for this cycle
        active_matches = random.sample(DEMO_MATCHES, min(3, len(DEMO_MATCHES)))

        for match in active_matches:
            team_a = match["team_a"]
            team_b = match["team_b"]
            tournament = match["tournament"]

            fav_odds_base = random.uniform(*BASE_ODDS["favourite"])
            dog_odds_base = random.uniform(*BASE_ODDS["underdog"])

            if random.random() < 0.5:
                team_a_base = fav_odds_base
                team_b_base = dog_odds_base
            else:
                team_a_base = dog_odds_base
                team_b_base = fav_odds_base

            for bk in BOOKMAKERS:
                noise_a = random.uniform(-0.15, 0.15)
                noise_b = random.uniform(-0.15, 0.15)
                odds_a = round(team_a_base + noise_a, 2)
                odds_b = round(team_b_base + noise_b, 2)

                odds_a = max(1.05, odds_a)
                odds_b = max(1.05, odds_b)

                # Inject arb: one bookmaker offers unusually high odds
                if inject_arb and bk == random.choice(BOOKMAKERS):
                    if random.random() < 0.5:
                        odds_a = round(odds_a * random.uniform(1.08, 1.15), 2)
                    else:
                        odds_b = round(odds_b * random.uniform(1.08, 1.15), 2)
                    inject_arb = False

                is_live = random.random() < 0.4

                for selection, odds_val in [(team_a, odds_a), (team_b, odds_b)]:
                    await self._publish_odds(
                        bookmaker=bk,
                        team_a=team_a,
                        team_b=team_b,
                        tournament=tournament,
                        selection=selection,
                        odds=odds_val,
                        is_live=is_live,
                    )
                    count += 1

        logger.info(
            f"[Demo] Cycle #{self._cycle_count}: Published {count} regular demo odds "
            f"({len(active_matches)} matches, {'with arb injection' if not inject_arb else 'normal'})"
        )
        return count

    async def _publish_odds(
        self,
        bookmaker: str,
        team_a: str,
        team_b: str,
        tournament: str,
        selection: str,
        odds: float,
        is_live: bool = False,
    ) -> None:
        """Publish a single odds entry to Redis pub/sub and latest hash."""
        odds_dict = {
            "bookmaker": bookmaker,
            "match_team_a": team_a,
            "match_team_b": team_b,
            "tournament": tournament,
            "start_time": (datetime.now(timezone.utc) + timedelta(hours=random.randint(-1, 4))).isoformat(),
            "market_type": "match_winner",
            "selection": selection,
            "odds_decimal": odds,
            "odds_original": str(odds),
            "odds_format": "decimal",
            "is_back": True,
            "lay_odds": round(odds + random.uniform(0.02, 0.08), 2) if bookmaker == "betfair" else None,
            "available_volume": round(random.uniform(500, 50000), 2) if bookmaker == "betfair" else None,
            "is_live": is_live,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": "demo",
        }

        message = json.dumps(odds_dict, default=str)
        await self.redis.publish("cricket:odds:raw", message)

        match_key = f"{team_a}_{team_b}"
        redis_key = f"cricket:odds:latest:{match_key}:match_winner"
        await self.redis.hset(redis_key, bookmaker, message)
        await self.redis.expire(redis_key, 300)

    async def close(self):
        self._match_drift.clear()
