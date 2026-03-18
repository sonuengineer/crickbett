"""
Odds Capture API — receives odds from Chrome extension or manual entry.
Publishes to Redis so the arb engine can process them.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.cricket import CaptureRequest, CaptureResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cricket/capture", tags=["capture"])


@router.post("/", response_model=CaptureResponse)
async def capture_odds(
    payload: CaptureRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Receive odds from Chrome extension or manual entry.
    Publishes to Redis for arb engine processing.
    """
    redis = await get_redis()
    now = datetime.now(timezone.utc).isoformat()

    for odds_item in payload.odds:
        odds_dict = {
            "bookmaker": payload.bookmaker,
            "match_team_a": payload.match_team_a,
            "match_team_b": payload.match_team_b,
            "market_type": payload.market_type,
            "selection": odds_item.selection,
            "odds_decimal": odds_item.odds_decimal,
            "odds_original": odds_item.odds_original or str(odds_item.odds_decimal),
            "odds_format": odds_item.odds_format,
            "is_back": odds_item.is_back,
            "is_live": odds_item.is_live,
            "scraped_at": now,
            "source": "extension" if payload.source_url else "manual",
            "source_url": payload.source_url,
            "user_id": str(user.id),
        }

        message = json.dumps(odds_dict, default=str)
        await redis.publish("cricket:odds:raw", message)

        # Store in latest hash for arb engine
        match_key = f"{payload.match_team_a}_{payload.match_team_b}"
        redis_key = f"cricket:odds:latest:{match_key}:{payload.market_type}"
        await redis.hset(redis_key, payload.bookmaker, message)
        await redis.expire(redis_key, 300)

    logger.info(
        f"[Capture] User {user.username} sent {len(payload.odds)} odds "
        f"for {payload.match_team_a} vs {payload.match_team_b} from {payload.bookmaker}"
    )

    return CaptureResponse(
        message=f"Received {len(payload.odds)} odds from {payload.bookmaker}",
        odds_received=len(payload.odds),
        arbs_found=0,  # Arb detection happens async via Redis
    )
