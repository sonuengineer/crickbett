import logging

from app.websocket.connection_manager import ws_manager

logger = logging.getLogger(__name__)


async def push_arb_to_web(arb_data: dict):
    """
    Push an arbitrage alert to all connected WebSocket clients.
    The frontend handles browser notification + sound playback.
    """
    message = {
        "type": "arb_detected",
        "data": arb_data,
        "sound": True,  # Frontend should play alert sound
    }
    await ws_manager.broadcast(message)
    logger.info(
        f"Web push: {arb_data.get('arb_type')} {arb_data.get('profit_pct', 0):.2f}% "
        f"to {ws_manager.connection_count} clients"
    )


async def push_odds_update(match_key: str, odds_data: dict):
    """Push a live odds update to connected clients."""
    message = {
        "type": "odds_update",
        "match": match_key,
        "data": odds_data,
    }
    await ws_manager.broadcast(message)
