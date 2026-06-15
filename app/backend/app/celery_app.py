from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "mli",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.sync"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "refresh_external_classics_weekly": {
            "task": "app.tasks.sync.refresh_external_classics",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),
        },
        "sync_plex_library_nightly": {
            "task": "app.tasks.sync.sync_plex_library",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
