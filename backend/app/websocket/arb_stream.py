import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.websocket.connection_manager import ws_manager

logger = logging.getLogger(__name__)


async def start_arb_stream(redis: aioredis.Redis):
    """
    Subscribe to the Redis 'cricket:arb:detected' channel and push
    arb opportunities to all connected WebSocket clients in real time.
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe("cricket:arb:detected")

    logger.info("Arb stream started — listening for arbitrage opportunities")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    ws_message = {
                        "type": "arb_detected",
                        "data": data,
                    }
                    await ws_manager.broadcast(ws_message)
                    logger.info(
                        f"Arb broadcast: {data.get('arb_type')} "
                        f"{data.get('profit_pct', 0):.2f}% profit — "
                        f"sent to {ws_manager.connection_count} clients"
                    )
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in arb stream")
                except Exception as e:
                    logger.error(f"Arb stream broadcast error: {e}")
    except asyncio.CancelledError:
        logger.info("Arb stream cancelled")
    finally:
        await pubsub.unsubscribe("cricket:arb:detected")
        await pubsub.close()


async def start_hedge_monitor_checker(redis: aioredis.Redis):
    """
    Periodically check all active hedge monitors for profitable opportunities.
    Runs every 5 seconds. Pushes alerts via WebSocket + Redis for Telegram.
    """
    from app.services.hedge_monitor import HedgeMonitor

    monitor = HedgeMonitor(redis)
    logger.info("Hedge monitor checker started — checking every 5 seconds")

    try:
        while True:
            try:
                alerts = await monitor.check_all_monitors()
                for user_id, monitor_id, hedge in alerts:
                    # Push via WebSocket
                    ws_message = {
                        "type": "hedge_available",
                        "monitor_id": monitor_id,
                        "data": {
                            "opposite_selection": hedge.opposite_selection,
                            "opposite_bookmaker": hedge.opposite_bookmaker,
                            "live_odds": hedge.live_odds,
                            "hedge_stake": hedge.hedge_stake,
                            "guaranteed_profit": hedge.guaranteed_profit,
                            "profit_pct": hedge.profit_pct,
                        },
                    }
                    # Send to specific user if connected
                    if user_id in ws_manager.active_connections:
                        await ws_manager.send_personal(ws_message, user_id)
                    else:
                        # Broadcast to all (user filtering on frontend)
                        await ws_manager.broadcast(ws_message)

                    # Also publish to Redis for Telegram
                    hedge_alert = {
                        "type": "hedge_alert",
                        "user_id": user_id,
                        "monitor_id": monitor_id,
                        "opposite_selection": hedge.opposite_selection,
                        "opposite_bookmaker": hedge.opposite_bookmaker,
                        "live_odds": hedge.live_odds,
                        "hedge_stake": hedge.hedge_stake,
                        "guaranteed_profit": hedge.guaranteed_profit,
                        "profit_pct": hedge.profit_pct,
                    }
                    await redis.publish("cricket:arb:detected", json.dumps(hedge_alert))

                    logger.info(
                        f"HEDGE ALERT: {hedge.opposite_selection} @ {hedge.live_odds} "
                        f"on {hedge.opposite_bookmaker} — "
                        f"stake Rs.{hedge.hedge_stake}, profit Rs.{hedge.guaranteed_profit}"
                    )
            except Exception as e:
                logger.error(f"Hedge monitor check error: {e}")

            await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.info("Hedge monitor checker cancelled")


async def start_odds_processor(redis: aioredis.Redis):
    """
    Subscribe to 'cricket:odds:raw' channel, aggregate odds,
    and run arb detection on each incoming odds update.
    """
    from app.services.arb_engine import detect_cross_book_arb, detect_back_lay_arb
    from app.core.config import get_settings

    settings = get_settings()
    pubsub = redis.pubsub()
    await pubsub.subscribe("cricket:odds:raw")

    logger.info("Odds processor started — listening for raw odds")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    odds_data = json.loads(message["data"])
                    await _process_odds(redis, odds_data, settings)
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    logger.error(f"Odds processing error: {e}")
    except asyncio.CancelledError:
        logger.info("Odds processor cancelled")
    finally:
        await pubsub.unsubscribe("cricket:odds:raw")
        await pubsub.close()


async def _process_odds(redis: aioredis.Redis, odds_data: dict, settings):
    """Process a single odds update and check for arb opportunities."""
    from app.services.arb_engine import detect_cross_book_arb, detect_back_lay_arb

    match_key = f"{odds_data.get('match_team_a', '')}_{odds_data.get('match_team_b', '')}"
    market = odds_data.get("market_type", "unknown")
    redis_key = f"cricket:odds:latest:{match_key}:{market}"

    # Get all latest odds for this match+market from Redis
    all_odds_raw = await redis.hgetall(redis_key)
    if len(all_odds_raw) < 2:
        return  # Need at least 2 bookmakers to detect arb

    # Parse odds and group by selection
    odds_by_selection: dict[str, list[tuple[str, float]]] = {}
    betfair_lay: dict[str, float] = {}

    for bookmaker, raw in all_odds_raw.items():
        try:
            data = json.loads(raw)
            selection = data.get("selection", "")
            decimal_odds = float(data.get("odds_decimal", 0))

            if decimal_odds <= 1.0:
                continue

            if selection not in odds_by_selection:
                odds_by_selection[selection] = []
            odds_by_selection[selection].append((bookmaker, decimal_odds))

            # Track Betfair lay odds for back-lay arb
            if bookmaker == "betfair" and data.get("lay_odds"):
                betfair_lay[selection] = float(data["lay_odds"])

        except (json.JSONDecodeError, ValueError):
            continue

    # 1. Check cross-book arb
    arb = detect_cross_book_arb(
        odds_by_selection,
        total_stake=settings.DEFAULT_ARB_STAKE,
    )
    if arb and arb.profit_pct >= settings.MIN_ARB_PROFIT_PCT:
        arb_message = {
            "arb_type": arb.arb_type,
            "profit_pct": arb.profit_pct,
            "match": f"{odds_data.get('match_team_a')} vs {odds_data.get('match_team_b')}",
            "market_type": market,
            "total_stake": arb.total_stake,
            "guaranteed_profit": arb.guaranteed_profit,
            "legs": [
                {
                    "bookmaker": leg.bookmaker,
                    "selection": leg.selection,
                    "odds": leg.odds,
                    "side": leg.side,
                    "stake": leg.stake,
                }
                for leg in arb.legs
            ],
        }
        await redis.publish("cricket:arb:detected", json.dumps(arb_message))
        logger.info(f"CROSS-BOOK ARB: {arb.profit_pct:.2f}% on {match_key}")

    # 2. Check back-lay arb (each selection with betfair lay)
    if betfair_lay:
        commission = settings.BETFAIR_COMMISSION_PCT / 100
        for selection, lay_odds in betfair_lay.items():
            if selection in odds_by_selection:
                for bookmaker, back_odds in odds_by_selection[selection]:
                    if bookmaker == "betfair":
                        continue  # Don't arb betfair vs betfair
                    bl_arb = detect_back_lay_arb(
                        back_bookmaker=bookmaker,
                        lay_bookmaker="betfair",
                        selection=selection,
                        back_odds=back_odds,
                        lay_odds=lay_odds,
                        commission=commission,
                    )
                    if bl_arb and bl_arb.profit_pct >= settings.MIN_ARB_PROFIT_PCT:
                        bl_message = {
                            "arb_type": bl_arb.arb_type,
                            "profit_pct": bl_arb.profit_pct,
                            "match": f"{odds_data.get('match_team_a')} vs {odds_data.get('match_team_b')}",
                            "market_type": market,
                            "total_stake": bl_arb.total_stake,
                            "guaranteed_profit": bl_arb.guaranteed_profit,
                            "legs": [
                                {
                                    "bookmaker": leg.bookmaker,
                                    "selection": leg.selection,
                                    "odds": leg.odds,
                                    "side": leg.side,
                                    "stake": leg.stake,
                                }
                                for leg in bl_arb.legs
                            ],
                        }
                        await redis.publish("cricket:arb:detected", json.dumps(bl_message))
                        logger.info(
                            f"BACK-LAY ARB: {bl_arb.profit_pct:.2f}% "
                            f"back {bookmaker}@{back_odds} lay betfair@{lay_odds}"
                        )
