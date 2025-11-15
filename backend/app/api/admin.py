"""
Admin API endpoints for managing migrations, users, and system
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.models.migration import MigrationRun, ScraperMetadata
from app.models.location import Location
from app.models.event import Event
from app.services.migration_runner import MigrationRunner

router = APIRouter(prefix="/admin", tags=["admin"])


# ===== Schemas =====

class MigrationRunCreate(BaseModel):
    scraper_id: int
    limit: Optional[int] = None
    triggered_by: str = "admin"


class MigrationRunResponse(BaseModel):
    id: int
    scraper_id: int
    scraper_name: Optional[str]
    scraper_schema: Optional[str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    records_processed: int
    records_inserted: int
    records_updated: int
    records_failed: int
    records_skipped: int
    error_message: Optional[str]
    triggered_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MigrationLogResponse(BaseModel):
    id: int
    status: str
    log_output: Optional[str]


class ScraperResponse(BaseModel):
    id: int
    scraper_id: int
    name: Optional[str]
    schema_name: Optional[str]
    is_active: bool
    total_records: Optional[int]
    last_scraped_at: Optional[datetime]
    synced_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_locations: int
    total_events: int
    total_users: int
    locations_by_source: List[dict]
    recent_migrations: List[MigrationRunResponse]
    system_health: dict


# ===== Migration Endpoints =====

@router.post("/migrations/run", response_model=MigrationRunResponse)
async def trigger_migration(
    data: MigrationRunCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a new migration run for a specific scraper

    - **scraper_id**: ID of the scraper to migrate
    - **limit**: Optional limit for number of records (for testing)
    - **triggered_by**: Who/what triggered this migration
    """
    runner = MigrationRunner(db)

    try:
        run_id = await runner.run_migration(
            scraper_id=data.scraper_id,
            limit=data.limit,
            triggered_by=data.triggered_by
        )

        # Fetch the created run
        migration = await runner.get_migration_status(run_id)
        return migration

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start migration: {str(e)}")


@router.get("/migrations", response_model=List[MigrationRunResponse])
async def list_migrations(
    limit: int = Query(50, le=200),
    scraper_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List recent migration runs

    - **limit**: Maximum number of runs to return (max 200)
    - **scraper_id**: Filter by scraper ID
    - **status**: Filter by status (pending, running, completed, failed, cancelled)
    """
    runner = MigrationRunner(db)
    migrations = await runner.list_migrations(
        limit=limit,
        scraper_id=scraper_id,
        status=status
    )
    return migrations


@router.get("/migrations/{run_id}", response_model=MigrationRunResponse)
async def get_migration(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific migration run"""
    runner = MigrationRunner(db)
    migration = await runner.get_migration_status(run_id)

    if not migration:
        raise HTTPException(status_code=404, detail="Migration run not found")

    return migration


@router.get("/migrations/{run_id}/logs", response_model=MigrationLogResponse)
async def get_migration_logs(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get full logs for a migration run"""
    result = await db.execute(
        select(MigrationRun).where(MigrationRun.id == run_id)
    )
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(status_code=404, detail="Migration run not found")

    return {
        "id": migration.id,
        "status": migration.status,
        "log_output": migration.log_output or ""
    }


@router.delete("/migrations/{run_id}")
async def cancel_migration(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running migration"""
    runner = MigrationRunner(db)
    cancelled = await runner.cancel_migration(run_id)

    if not cancelled:
        raise HTTPException(status_code=400, detail="Migration not running or already completed")

    return {"message": "Migration cancelled successfully"}


# ===== Scraper Endpoints =====

@router.get("/scrapers", response_model=List[ScraperResponse])
async def list_scrapers(
    db: AsyncSession = Depends(get_db)
):
    """List all configured scrapers from metadata"""
    result = await db.execute(
        select(ScraperMetadata).order_by(ScraperMetadata.scraper_id)
    )
    return result.scalars().all()


@router.post("/scrapers/sync")
async def sync_scrapers(
    db: AsyncSession = Depends(get_db)
):
    """Sync scraper metadata from scraparr database"""
    runner = MigrationRunner(db)
    await runner.sync_scraper_metadata()
    return {"message": "Scrapers synced successfully"}


# ===== Dashboard/Stats Endpoints =====

@router.get("/stats/overview", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get overview statistics for admin dashboard"""

    # Total locations
    result = await db.execute(select(func.count(Location.id)))
    total_locations = result.scalar()

    # Total events
    result = await db.execute(select(func.count(Event.id)))
    total_events = result.scalar()

    # TODO: Total users (when user table exists)
    total_users = 0

    # Locations by source
    result = await db.execute(
        select(
            Location.source,
            func.count(Location.id).label('count')
        )
        .group_by(Location.source)
        .order_by(desc('count'))
    )
    locations_by_source = [
        {"source": row[0], "count": row[1]}
        for row in result.all()
    ]

    # Recent migrations
    runner = MigrationRunner(db)
    recent_migrations = await runner.list_migrations(limit=10)

    # System health
    system_health = {
        "database": "healthy",  # Could ping DB
        "migrations": "healthy",  # Check if any failed recently
        "api": "healthy"
    }

    return {
        "total_locations": total_locations,
        "total_events": total_events,
        "total_users": total_users,
        "locations_by_source": locations_by_source,
        "recent_migrations": recent_migrations,
        "system_health": system_health
    }


@router.get("/stats/locations")
async def get_location_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get detailed location statistics"""

    # By source and type
    result = await db.execute(
        select(
            Location.source,
            Location.location_type,
            func.count(Location.id).label('count'),
            func.avg(Location.rating).label('avg_rating')
        )
        .group_by(Location.source, Location.location_type)
        .order_by(desc('count'))
    )

    by_source_and_type = [
        {
            "source": row[0],
            "location_type": row[1],
            "count": row[2],
            "avg_rating": float(row[3]) if row[3] else None
        }
        for row in result.all()
    ]

    # By country
    result = await db.execute(
        select(
            Location.country,
            func.count(Location.id).label('count')
        )
        .where(Location.country.isnot(None))
        .group_by(Location.country)
        .order_by(desc('count'))
        .limit(20)
    )

    by_country = [
        {"country": row[0], "count": row[1]}
        for row in result.all()
    ]

    return {
        "by_source_and_type": by_source_and_type,
        "by_country": by_country
    }
