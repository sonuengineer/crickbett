import asyncio
import json
import logging

import redis.asyncio as aioredis
from telegram import Bot
from telegram.constants import ParseMode

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def format_arb_message(arb: dict) -> str:
    """Format an arbitrage opportunity as a rich Telegram message."""
    arb_type_labels = {
        "cross_book": "CROSS-BOOK",
        "back_lay": "BACK-LAY",
        "live_swing": "LIVE HEDGE",
    }

    type_label = arb_type_labels.get(arb.get("arb_type", ""), "ARB")
    profit = arb.get("profit_pct", 0)
    match = arb.get("match", "Unknown")
    market = arb.get("market_type", "").replace("_", " ").title()
    total_stake = arb.get("total_stake", 0)
    guaranteed = arb.get("guaranteed_profit", 0)
    legs = arb.get("legs", [])

    lines = [
        f"🚨 <b>ARBITRAGE ALERT — {type_label}</b>",
        f"",
        f"🏏 <b>Match:</b> {match}",
        f"📊 <b>Market:</b> {market}",
        f"💰 <b>Profit:</b> {profit:.2f}%",
        f"",
    ]

    for i, leg in enumerate(legs, 1):
        side = leg.get("side", "back").upper()
        lines.append(
            f"  Leg {i}: {side} <b>{leg.get('selection')}</b> "
            f"@ {leg.get('odds', 0):.2f} on {leg.get('bookmaker', '').upper()} "
            f"(₹{leg.get('stake', 0):,.0f})"
        )

    lines.extend([
        f"",
        f"💵 <b>Total Outlay:</b> ₹{total_stake:,.0f}",
        f"✅ <b>Guaranteed Return:</b> ₹{total_stake + guaranteed:,.0f}",
        f"📈 <b>Guaranteed Profit:</b> ₹{guaranteed:,.0f}",
        f"",
        f"⚡ <i>Act fast — odds may shift!</i>",
    ])

    return "\n".join(lines)


class TelegramNotifier:
    """Sends arb alerts to Telegram users."""

    def __init__(self):
        self.bot: Bot | None = None
        self.chat_ids: list[int] = []

    async def initialize(self):
        if settings.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            logger.info("Telegram bot initialized")

    async def send_arb_alert(self, arb: dict, chat_ids: list[int] | None = None):
        """Send arb alert to specified chat IDs or all registered users."""
        if not self.bot:
            return

        message = format_arb_message(arb)
        targets = chat_ids or self.chat_ids

        for chat_id in targets:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logger.error(f"Failed to send Telegram to {chat_id}: {e}")

    async def start_listener(self, redis: aioredis.Redis):
        """Listen for arb detections on Redis and send Telegram alerts."""
        if not self.bot:
            logger.warning("Telegram bot token not configured, skipping listener")
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe("cricket:arb:detected")

        logger.info("Telegram listener started")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        arb = json.loads(message["data"])
                        await self.send_arb_alert(arb)
                    except Exception as e:
                        logger.error(f"Telegram notification error: {e}")
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe("cricket:arb:detected")
            await pubsub.close()


# Singleton
telegram_notifier = TelegramNotifier()
