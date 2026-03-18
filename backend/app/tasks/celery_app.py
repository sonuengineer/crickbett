from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "cricket_arb",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.scrape_tasks",
        "app.tasks.cleanup_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "scrape-all-bookmakers": {
            "task": "app.tasks.scrape_tasks.scrape_all_bookmakers",
            "schedule": settings.SCRAPE_INTERVAL_SECONDS,
        },
        "discover-new-matches": {
            "task": "app.tasks.scrape_tasks.discover_matches",
            "schedule": settings.MATCH_DISCOVERY_INTERVAL_SECONDS,
        },
        "cleanup-stale-odds": {
            "task": "app.tasks.cleanup_tasks.cleanup_stale_data",
            "schedule": 3600,  # Every hour
        },
    },
)
