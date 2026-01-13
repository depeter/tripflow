from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, text
from app.core.config import settings
from app.db.database import SessionLocal
from app.sync.sync_manager import create_sync_manager
from app.models.event import Event
from app.models.location import Location, LocationType
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


@celery_app.task(name="cleanup_expired_events")
def cleanup_expired_events_task():
    """
    Celery task to permanently delete expired events.

    Deletes:
    1. Events from the Event model where end_datetime (or start_datetime if no end) has passed
    2. Locations with location_type=EVENT where raw_data end_date (or start_date) has passed

    This is a hard delete - records are permanently removed from the database.
    UserFavorites are cascade deleted automatically via foreign key constraint.
    """
    if not settings.EVENT_CLEANUP_ENABLED:
        logger.info("Event cleanup is disabled, skipping")
        return {"status": "disabled", "deleted_events": 0, "deleted_locations": 0}

    logger.info("Starting expired event cleanup")

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.EVENT_CLEANUP_RETENTION_DAYS)

        # Track deletion counts
        deleted_events = 0
        deleted_locations = 0

        # 1. Delete from Event model
        # Events are expired if:
        # - end_datetime exists and is before cutoff, OR
        # - end_datetime is NULL and start_datetime is before cutoff
        expired_events = db.query(Event).filter(
            or_(
                and_(Event.end_datetime.isnot(None), Event.end_datetime < cutoff_date),
                and_(Event.end_datetime.is_(None), Event.start_datetime < cutoff_date)
            )
        ).all()

        deleted_events = len(expired_events)
        for event in expired_events:
            db.delete(event)

        # 2. Delete from Location model (event type only)
        # Need to handle JSONB raw_data with start_date/end_date
        # Using raw SQL for JSONB date comparison
        expired_locations_query = text("""
            DELETE FROM tripflow.locations
            WHERE location_type = 'EVENT'
            AND (
                (raw_data->>'end_date' IS NOT NULL
                 AND (raw_data->>'end_date')::timestamp < :cutoff_date)
                OR
                (raw_data->>'end_date' IS NULL
                 AND raw_data->>'start_date' IS NOT NULL
                 AND (raw_data->>'start_date')::timestamp < :cutoff_date)
            )
        """)

        result = db.execute(expired_locations_query, {"cutoff_date": cutoff_date})
        deleted_locations = result.rowcount

        db.commit()

        logger.info(
            f"Expired event cleanup completed: "
            f"deleted {deleted_events} events, "
            f"{deleted_locations} event locations"
        )

        return {
            "status": "success",
            "deleted_events": deleted_events,
            "deleted_locations": deleted_locations,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Expired event cleanup failed: {e}")
        raise

    finally:
        db.close()


# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "sync-all-sources-daily": {
        "task": "sync_all_sources",
        "schedule": settings.SYNC_SCHEDULE_HOURS * 3600.0,  # Convert hours to seconds
    },
    "cleanup-expired-events-daily": {
        "task": "cleanup_expired_events",
        "schedule": settings.EVENT_CLEANUP_SCHEDULE_HOURS * 3600.0,
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not picked up
        }
    },
}
