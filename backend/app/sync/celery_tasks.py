from celery import Celery
from app.core.config import settings
from app.db.database import SessionLocal
from app.sync.sync_manager import create_sync_manager
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "tripflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="sync_all_sources")
def sync_all_sources_task(batch_size: int = 100, limit: int = None):
    """
    Celery task to sync all source databases.

    This task is scheduled to run periodically (e.g., daily).
    """
    logger.info("Starting scheduled sync of all sources")

    db = SessionLocal()
    try:
        sync_manager = create_sync_manager(db)
        results = sync_manager.sync_all(batch_size=batch_size, limit=limit)

        logger.info(f"Scheduled sync completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")
        raise

    finally:
        db.close()


@celery_app.task(name="sync_source")
def sync_source_task(source_name: str, batch_size: int = 100, limit: int = None):
    """
    Celery task to sync a specific source database.

    Args:
        source_name: One of 'park4night', 'campercontact', 'local_sites'
        batch_size: Batch size for processing
        limit: Optional limit for testing
    """
    logger.info(f"Starting scheduled sync of {source_name}")

    db = SessionLocal()
    try:
        sync_manager = create_sync_manager(db)
        results = sync_manager.sync_source(
            source_name=source_name,
            batch_size=batch_size,
            limit=limit
        )

        logger.info(f"Scheduled sync of {source_name} completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Scheduled sync of {source_name} failed: {e}")
        raise

    finally:
        db.close()


# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "sync-all-sources-daily": {
        "task": "sync_all_sources",
        "schedule": settings.SYNC_SCHEDULE_HOURS * 3600.0,  # Convert hours to seconds
    },
}
