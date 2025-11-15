"""
Migration tracking models for admin dashboard
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class MigrationRun(Base):
    """Track individual migration executions"""
    __tablename__ = "migration_runs"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(Integer, primary_key=True, index=True)

    # Scraper info
    scraper_id = Column(Integer, nullable=False, index=True)
    scraper_name = Column(String(255))
    scraper_schema = Column(String(100))

    # Execution status
    status = Column(String(20), default='pending', index=True)  # pending, running, completed, failed, cancelled

    # Timing
    started_at = Column(DateTime(timezone=True), index=True)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Statistics
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)

    # Details
    error_message = Column(Text)
    log_output = Column(Text)  # Full migration log
    params = Column(JSON)  # Migration parameters (limit, filters, etc.)

    # Metadata
    triggered_by = Column(String(100))  # 'admin', 'schedule', 'api', user email
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MigrationSchedule(Base):
    """Configure automatic migration schedules"""
    __tablename__ = "migration_schedules"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(Integer, primary_key=True, index=True)

    scraper_id = Column(Integer, nullable=False, unique=True, index=True)
    scraper_name = Column(String(255))

    # Schedule
    schedule_cron = Column(String(100))  # Cron expression
    is_active = Column(Boolean, default=False)

    # Tracking
    last_run_at = Column(DateTime(timezone=True))
    last_run_status = Column(String(20))
    next_run_at = Column(DateTime(timezone=True))

    # Config
    auto_run_params = Column(JSON)  # Default params for scheduled runs

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScraperMetadata(Base):
    """Metadata about scrapers from scraparr database"""
    __tablename__ = "scraper_metadata"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(Integer, primary_key=True)
    scraper_id = Column(Integer, unique=True, nullable=False, index=True)

    # From scraparr.scrapers table
    name = Column(String(255))
    schema_name = Column(String(100))
    module_path = Column(String(500))
    class_name = Column(String(255))
    is_active = Column(Boolean, default=True)

    # Stats from last sync
    total_records = Column(Integer)
    last_scraped_at = Column(DateTime(timezone=True))

    # Cache/sync
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
