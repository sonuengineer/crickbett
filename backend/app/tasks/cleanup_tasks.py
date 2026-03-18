import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.tasks.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.cricket import OddsSnapshot, ArbitrageOpportunity

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_stale_data")
def cleanup_stale_data():
    """Periodic task: purge old odds and expire stale arb opportunities."""
    asyncio.run(_cleanup())


async def _cleanup():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.ODDS_CLEANUP_HOURS)

    async with AsyncSessionLocal() as session:
        # Delete old odds snapshots
        result = await session.execute(
            delete(OddsSnapshot).where(OddsSnapshot.scraped_at < cutoff)
        )
        deleted_odds = result.rowcount

        # Expire active arbs older than 5 minutes
        arb_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        from sqlalchemy import update
        await session.execute(
            update(ArbitrageOpportunity)
            .where(ArbitrageOpportunity.status == "active")
            .where(ArbitrageOpportunity.detected_at < arb_cutoff)
            .values(status="expired", expired_at=datetime.now(timezone.utc))
        )

        await session.commit()
        logger.info(f"Cleanup: deleted {deleted_odds} stale odds snapshots")
