import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.redis import close_redis, get_redis
from app.core.security import decode_token
from app.websocket.connection_manager import ws_manager
from app.websocket.arb_stream import start_arb_stream, start_odds_processor, start_hedge_monitor_checker
from app.notifications.telegram_bot import telegram_notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Background tasks
_background_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    redis = await get_redis()

    # Start Telegram bot
    await telegram_notifier.initialize()

    # Start background Redis subscribers
    _background_tasks.append(asyncio.create_task(start_arb_stream(redis)))
    _background_tasks.append(asyncio.create_task(start_odds_processor(redis)))
    _background_tasks.append(asyncio.create_task(start_hedge_monitor_checker(redis)))
    _background_tasks.append(asyncio.create_task(telegram_notifier.start_listener(redis)))

    logger.info("Cricket Arb backend started")
    yield

    # Shutdown
    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()

    await close_redis()
    await close_db()
    logger.info("Cricket Arb backend stopped")


app = FastAPI(
    title="Cricket Arb Detector",
    description="Real-time cricket betting arbitrage detection system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.websocket("/ws/arb-stream")
async def websocket_arb_stream(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time arb alerts."""
    # Authenticate via JWT
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub", "anonymous")
    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            # Keep connection alive, handle pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)


@app.get("/health")
async def health_check():
    redis = await get_redis()
    redis_ok = await redis.ping()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "data_source": settings.DATA_SOURCE_MODE,
        "redis": "connected" if redis_ok else "disconnected",
        "websocket_clients": ws_manager.connection_count,
    }


@app.get("/health/scrapers")
async def scraper_health():
    """Get health status of data source and recent odds."""
    redis = await get_redis()

    # Count recent odds keys in Redis
    keys = []
    async for key in redis.scan_iter("cricket:odds:latest:*"):
        keys.append(key)

    return {
        "data_source_mode": settings.DATA_SOURCE_MODE,
        "active_odds_keys": len(keys),
        "hint": (
            "Switch DATA_SOURCE_MODE in .env: 'demo' for mock data, "
            "'api' for The Odds API (real data), 'playwright' for browser scraping"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
