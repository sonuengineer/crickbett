"""
Live Hedge Monitor Service

Core flow:
1. User places a pre-match bet (e.g., India @ 2.50 for Rs.1000)
2. This service monitors live odds for the OPPOSITE selection
3. When opposite odds are good enough → alert with exact hedge stake + guaranteed profit

Math:
  Original bet: stake S on Team A at odds O_a
  Potential return: R = S * O_a

  Hedge bet: stake H on Team B at odds O_b
  For guaranteed profit: both outcomes must return more than total invested

  H = R / O_b = (S * O_a) / O_b

  If Team A wins:  R - S - H = S*O_a - S - (S*O_a)/O_b
  If Team B wins:  H*O_b - S - H = S*O_a - S - (S*O_a)/O_b  (same!)

  Guaranteed profit = S * O_a - S - (S * O_a) / O_b
                    = S * (O_a - 1 - O_a/O_b)

  Breakeven: profit > 0 when O_b > O_a / (O_a - 1)
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from app.schemas.cricket import HedgeMonitorCreate, HedgeMonitorResponse, HedgeOpportunity

logger = logging.getLogger(__name__)


class HedgeMonitor:
    """
    Manages active hedge monitors per user.
    Stores state in Redis for fast access during live monitoring.
    """

    MONITORS_KEY = "cricket:hedge:monitors"  # Hash: monitor_id -> JSON
    USER_MONITORS_KEY = "cricket:hedge:user:{user_id}"  # Set of monitor_ids

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def create_monitor(
        self, user_id: str, bet: HedgeMonitorCreate
    ) -> HedgeMonitorResponse:
        """Record a pre-match bet and start monitoring for hedge opportunities."""
        monitor_id = str(uuid.uuid4())
        potential_return = bet.stake * bet.odds
        breakeven_odds = bet.odds / (bet.odds - 1) if bet.odds > 1 else float("inf")

        # Determine opposite selection
        opposite = bet.match_team_b if bet.selection == bet.match_team_a else bet.match_team_a

        monitor_data = {
            "id": monitor_id,
            "user_id": user_id,
            "match_team_a": bet.match_team_a,
            "match_team_b": bet.match_team_b,
            "tournament": bet.tournament,
            "bookmaker": bet.bookmaker,
            "selection": bet.selection,
            "opposite_selection": opposite,
            "odds": bet.odds,
            "stake": bet.stake,
            "potential_return": potential_return,
            "market_type": bet.market_type,
            "status": "monitoring",
            "breakeven_odds": round(breakeven_odds, 4),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store in Redis
        await self.redis.hset(
            self.MONITORS_KEY, monitor_id, json.dumps(monitor_data)
        )
        await self.redis.sadd(
            self.USER_MONITORS_KEY.format(user_id=user_id), monitor_id
        )
        # TTL: 24 hours (auto-expire old monitors)
        await self.redis.expire(
            self.USER_MONITORS_KEY.format(user_id=user_id), 86400
        )

        logger.info(
            f"[HedgeMonitor] Created monitor {monitor_id}: "
            f"{bet.selection} @ {bet.odds} for Rs.{bet.stake} "
            f"({bet.match_team_a} vs {bet.match_team_b}). "
            f"Breakeven opposite odds: {breakeven_odds:.2f}"
        )

        return self._to_response(monitor_data, best_hedge=None)

    async def get_user_monitors(
        self, user_id: str
    ) -> list[HedgeMonitorResponse]:
        """Get all active monitors for a user, with current hedge opportunities."""
        monitor_ids = await self.redis.smembers(
            self.USER_MONITORS_KEY.format(user_id=user_id)
        )

        monitors = []
        for mid in monitor_ids:
            mid_str = mid if isinstance(mid, str) else mid.decode()
            raw = await self.redis.hget(self.MONITORS_KEY, mid_str)
            if not raw:
                continue
            data = json.loads(raw)

            # Check current live odds for hedge opportunity
            best_hedge = await self._check_hedge_opportunity(data)
            monitors.append(self._to_response(data, best_hedge))

        # Sort by created_at desc
        monitors.sort(key=lambda m: m.created_at, reverse=True)
        return monitors

    async def get_monitor(
        self, monitor_id: str
    ) -> Optional[HedgeMonitorResponse]:
        """Get a specific monitor with current hedge opportunity."""
        raw = await self.redis.hget(self.MONITORS_KEY, monitor_id)
        if not raw:
            return None
        data = json.loads(raw)
        best_hedge = await self._check_hedge_opportunity(data)
        return self._to_response(data, best_hedge)

    async def mark_hedged(self, monitor_id: str) -> Optional[HedgeMonitorResponse]:
        """Mark a monitor as hedged (user placed the hedge bet)."""
        raw = await self.redis.hget(self.MONITORS_KEY, monitor_id)
        if not raw:
            return None
        data = json.loads(raw)
        data["status"] = "hedged"
        await self.redis.hset(self.MONITORS_KEY, monitor_id, json.dumps(data))
        return self._to_response(data, None)

    async def delete_monitor(self, monitor_id: str, user_id: str) -> bool:
        """Delete a monitor."""
        await self.redis.hdel(self.MONITORS_KEY, monitor_id)
        await self.redis.srem(
            self.USER_MONITORS_KEY.format(user_id=user_id), monitor_id
        )
        return True

    async def check_all_monitors(self) -> list[tuple[str, str, HedgeOpportunity]]:
        """
        Check ALL active monitors for hedge opportunities.
        Called periodically by the background task.
        Returns list of (user_id, monitor_id, hedge_opportunity) tuples.
        """
        all_monitors = await self.redis.hgetall(self.MONITORS_KEY)
        alerts = []

        for mid, raw in all_monitors.items():
            mid_str = mid if isinstance(mid, str) else mid.decode()
            raw_str = raw if isinstance(raw, str) else raw.decode()
            data = json.loads(raw_str)

            if data.get("status") != "monitoring":
                continue

            hedge = await self._check_hedge_opportunity(data)
            if hedge and hedge.guaranteed_profit > 0:
                alerts.append((data["user_id"], mid_str, hedge))

        return alerts

    async def _check_hedge_opportunity(
        self, monitor_data: dict
    ) -> Optional[HedgeOpportunity]:
        """
        Check if current live odds offer a hedge opportunity for this monitor.
        Looks up latest odds in Redis.
        """
        match_key = f"{monitor_data['match_team_a']}_{monitor_data['match_team_b']}"
        market = monitor_data["market_type"]
        redis_key = f"cricket:odds:latest:{match_key}:{market}"

        # Get all bookmaker odds for this match
        all_odds = await self.redis.hgetall(redis_key)
        if not all_odds:
            return None

        opposite = monitor_data["opposite_selection"]
        original_stake = monitor_data["stake"]
        original_odds = monitor_data["odds"]
        potential_return = original_stake * original_odds
        breakeven = monitor_data["breakeven_odds"]

        best_hedge = None
        best_profit = 0

        for bk_name, odds_json in all_odds.items():
            bk_str = bk_name if isinstance(bk_name, str) else bk_name.decode()
            raw_str = odds_json if isinstance(odds_json, str) else odds_json.decode()

            try:
                odds_data = json.loads(raw_str)
            except json.JSONDecodeError:
                continue

            # Only look at odds for the opposite selection
            if odds_data.get("selection") != opposite:
                continue

            live_odds = odds_data.get("odds_decimal", 0)
            if live_odds <= 1.0 or live_odds < breakeven:
                continue  # Not profitable

            # Calculate hedge
            hedge_stake = potential_return / live_odds
            total_invested = original_stake + hedge_stake
            guaranteed_profit = potential_return - total_invested
            profit_pct = (guaranteed_profit / total_invested) * 100

            if guaranteed_profit > best_profit:
                best_profit = guaranteed_profit
                best_hedge = HedgeOpportunity(
                    opposite_selection=opposite,
                    opposite_bookmaker=bk_str,
                    live_odds=live_odds,
                    hedge_stake=round(hedge_stake, 2),
                    guaranteed_profit=round(guaranteed_profit, 2),
                    profit_pct=round(profit_pct, 2),
                    breakeven_odds=round(breakeven, 4),
                    source=odds_data.get("source", "live"),
                )

        return best_hedge

    def _to_response(
        self, data: dict, best_hedge: Optional[HedgeOpportunity]
    ) -> HedgeMonitorResponse:
        status = data.get("status", "monitoring")
        if best_hedge and best_hedge.guaranteed_profit > 0 and status == "monitoring":
            status = "hedge_available"

        return HedgeMonitorResponse(
            id=data["id"],
            match_team_a=data["match_team_a"],
            match_team_b=data["match_team_b"],
            tournament=data.get("tournament"),
            bookmaker=data["bookmaker"],
            selection=data["selection"],
            odds=data["odds"],
            stake=data["stake"],
            potential_return=data.get("potential_return", data["stake"] * data["odds"]),
            market_type=data.get("market_type", "match_winner"),
            status=status,
            breakeven_odds=data.get("breakeven_odds", 0),
            best_hedge=best_hedge,
            created_at=datetime.fromisoformat(data["created_at"]),
        )
