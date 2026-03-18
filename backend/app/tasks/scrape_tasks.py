import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(name="app.tasks.scrape_tasks.scrape_all_bookmakers")
def scrape_all_bookmakers():
    """Periodic task: scrape odds using configured data source mode."""
    asyncio.run(_scrape_all())


async def _scrape_all():
    from app.core.redis import get_redis

    redis = await get_redis()
    mode = settings.DATA_SOURCE_MODE.lower()

    if mode == "api":
        # Real data via The Odds API (recommended)
        if not settings.THE_ODDS_API_KEY:
            logger.error("THE_ODDS_API_KEY not set — switch to 'demo' mode or add your key")
            return

        from app.scrapers.scraper_manager import run_api_scraper

        count = await run_api_scraper(
            redis=redis,
            api_key=settings.THE_ODDS_API_KEY,
            regions=settings.ODDS_API_REGIONS,
        )
        logger.info(f"[API mode] Scrape cycle complete: {count} odds")

    elif mode == "demo":
        # Mock data for testing the full pipeline
        from app.scrapers.scraper_manager import run_demo_scraper

        count = await run_demo_scraper(redis=redis, arb_frequency=0.3)
        logger.info(f"[Demo mode] Scrape cycle complete: {count} demo odds")

    elif mode == "playwright":
        # Playwright browser scrapers (requires calibrated CSS selectors)
        from app.scrapers.scraper_manager import ScraperManager

        manager = ScraperManager(
            redis=redis,
            proxy_list=settings.PROXY_LIST,
        )
        try:
            await manager.start_all()
            results = await manager.scrape_all()
            total_odds = sum(len(odds) for odds in results.values())
            logger.info(f"[Playwright mode] Scrape cycle: {total_odds} odds from {len(results)} bookmakers")
        except Exception as e:
            logger.error(f"[Playwright mode] Scrape cycle failed: {e}")
        finally:
            await manager.stop_all()

    else:
        logger.error(f"Unknown DATA_SOURCE_MODE: {mode}. Use 'api', 'demo', or 'playwright'")


@celery_app.task(name="app.tasks.scrape_tasks.discover_matches")
def discover_matches():
    """Periodic task: discover new cricket matches."""
    asyncio.run(_discover())


async def _discover():
    mode = settings.DATA_SOURCE_MODE.lower()

    if mode in ("api", "demo"):
        # API and demo modes discover matches during the scrape cycle itself
        logger.info(f"[{mode} mode] Match discovery happens during scrape — skipping")
        return

    # Playwright mode: use scrapers to discover
    from app.core.redis import get_redis
    from app.scrapers.scraper_manager import ScraperManager

    redis = await get_redis()
    manager = ScraperManager(
        redis=redis,
        proxy_list=settings.PROXY_LIST,
    )

    try:
        await manager.start_all()
        for name, scraper in manager.scrapers.items():
            try:
                matches = await scraper.discover_live_matches()
                logger.info(f"[{name}] Discovered {len(matches)} matches")
            except Exception as e:
                logger.error(f"[{name}] Discovery failed: {e}")
    finally:
        await manager.stop_all()
