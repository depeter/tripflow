# Tripflow Migration Automation - Design Document

## Executive Summary

This document outlines the design for automating Scraparr → Tripflow data migrations with scheduling, execution tracking, and a dedicated frontend interface.

**Goals:**
1. Automate migrations to run on a schedule (e.g., nightly at 2 AM)
2. Add a "Migrations" section to Scraparr frontend (separate from scrape jobs)
3. Track migration execution history in a separate table
4. Allow manual triggering of migrations from UI
5. View migration logs and statistics

---

## Current State Analysis

### How Migrations Work Now (Manual)

**Current Process:**
```bash
# Migrations are run manually via SSH
ssh peter@scraparr
cd /home/peter/tripflow/migrations
python3 migrate_all_scrapers.py --scraper-id 4
```

**Migration Script:** `/home/peter/tripflow/migrations/migrate_all_scrapers.py`
- Connects to both Scraparr DB (port 5434) and Tripflow DB (port 5433)
- Uses mapping classes from `scraper_mappings.py`
- Migrates data based on scraper ID
- Logs to console and `migration_all.log`

**Existing Scrapers:**
- Scraper 1: Park4Night (locations)
- Scraper 2: UiT in Vlaanderen (events)
- Scraper 3: Eventbrite (events)
- Scraper 4: Ticketmaster (events) ✅ Migrated (1000 events)
- Scraper 5: CamperContact (locations) ✅ Migrated (19 places)

### How Scraparr Jobs Work

**Scraparr Job System:**
- **Database Tables:**
  - `jobs` - Scheduled tasks (cron/interval)
  - `executions` - Execution logs with status, duration, items_scraped
  - `scrapers` - Scraper definitions

- **Backend:**
  - APScheduler for scheduling
  - `SchedulerService` manages jobs
  - `ScraperRunner` executes scrapers
  - Models: `Job`, `Execution`, `Scraper`

- **Frontend:**
  - Jobs page: Manage scheduled jobs
  - Executions page: View execution history
  - Real-time updates every 5 seconds

---

## Proposed Architecture

### Overview

Create a parallel system for migrations that mirrors the scraper job architecture but keeps migrations separate.

**Key Components:**
1. **Backend:** Migration jobs, execution tracking, scheduler integration
2. **Database:** New tables for migration jobs and executions
3. **Frontend:** New "Migrations" page and menu item
4. **Integration:** Reuse existing APScheduler infrastructure

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Scraparr Frontend                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐             │
│  │ Jobs     │  │Executions│  │ Migrations ✨ │             │
│  │(Scrapers)│  │(Scrapers)│  │   (New)      │             │
│  └──────────┘  └──────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Scraparr Backend                          │
│  ┌──────────────┐         ┌─────────────────┐              │
│  │ Scheduler    │         │ Migration       │              │
│  │ Service      │ ←──────→│ Runner ✨       │              │
│  │(APScheduler) │         │                 │              │
│  └──────────────┘         └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Scraparr PostgreSQL                         │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ jobs        │  │ migration_jobs  │  │ executions      ││
│  │ (scrapers)  │  │     ✨          │  │   (scrapers)    ││
│  └─────────────┘  └─────────────────┘  └─────────────────┘│
│                    ┌─────────────────┐                      │
│                    │ migration_      │                      │
│                    │ executions ✨    │                      │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                 Migration Script                             │
│  /home/peter/tripflow/migrations/migrate_all_scrapers.py    │
│                          ↓                                   │
│  Scraparr DB (5434) ──→ Tripflow DB (5433)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### New Tables

#### 1. `migration_jobs` Table

Scheduled migration tasks (similar to `jobs` but for migrations).

```sql
CREATE TABLE migration_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Which scrapers to migrate
    scraper_ids INTEGER[] NOT NULL,  -- Array of scraper IDs (e.g., [4, 5])

    -- Scheduling
    schedule_type VARCHAR(50) NOT NULL,  -- 'cron', 'interval', 'once', 'manual'
    schedule_config JSONB NOT NULL,
    -- Example: {"expression": "0 2 * * *"}  -- 2 AM daily

    -- Parameters for migration
    params JSONB DEFAULT '{}',
    -- Example: {"limit": null, "batch_size": 1000}

    -- Status
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,

    -- APScheduler job ID
    scheduler_job_id VARCHAR(255) UNIQUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_migration_jobs_active ON migration_jobs(is_active);
CREATE INDEX idx_migration_jobs_next_run ON migration_jobs(next_run_at);
```

#### 2. `migration_executions` Table

Tracks each migration execution (similar to `executions` but for migrations).

```sql
CREATE TABLE migration_executions (
    id SERIAL PRIMARY KEY,
    migration_job_id INTEGER REFERENCES migration_jobs(id) ON DELETE CASCADE,

    -- What was migrated
    scraper_ids INTEGER[] NOT NULL,

    -- Execution details
    status VARCHAR(50) NOT NULL DEFAULT 'running',  -- running, success, failed, partial, cancelled
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Results per scraper
    results JSONB DEFAULT '[]',
    -- Example: [
    --   {
    --     "scraper_id": 4,
    --     "scraper_name": "Ticketmaster Events",
    --     "locations_inserted": 66,
    --     "events_inserted": 1000,
    --     "errors": 0,
    --     "duration_seconds": 0.81
    --   }
    -- ]

    -- Overall stats
    total_locations INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,

    -- Error information
    error_message TEXT,
    logs TEXT,  -- Full migration logs

    -- Metadata
    params JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_migration_executions_job_id ON migration_executions(migration_job_id);
CREATE INDEX idx_migration_executions_status ON migration_executions(status);
CREATE INDEX idx_migration_executions_started ON migration_executions(started_at DESC);
```

#### 3. Updates to Existing Tables

**Optional:** Add a `type` column to distinguish migration jobs from scraper jobs in the UI.

```sql
-- Option 1: Keep separate tables (recommended)
-- No changes needed

-- Option 2: Unified table (not recommended)
ALTER TABLE jobs ADD COLUMN job_type VARCHAR(50) DEFAULT 'scraper';
-- Values: 'scraper', 'migration'
```

---

## Backend Implementation

### File Structure

```
scraparr/backend/app/
├── models/
│   ├── migration_job.py          ✨ New
│   └── migration_execution.py    ✨ New
├── schemas/
│   ├── migration_job.py          ✨ New
│   └── migration_execution.py    ✨ New
├── services/
│   └── migration_runner.py       ✨ New
├── api/
│   └── migrations.py             ✨ New
└── main.py                        (Update to include migration routes)
```

### 1. Models

**`app/models/migration_job.py`:**
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MigrationJob(Base):
    """Scheduled migration job model"""

    __tablename__ = "migration_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Which scrapers to migrate
    scraper_ids = Column(ARRAY(Integer), nullable=False)

    # Scheduling
    schedule_type = Column(String(50), nullable=False)
    schedule_config = Column(JSONB, nullable=False)

    # Parameters
    params = Column(JSONB, nullable=True, default={})

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # APScheduler job ID
    scheduler_job_id = Column(String(255), nullable=True, unique=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    executions = relationship("MigrationExecution", back_populates="migration_job", cascade="all, delete-orphan")
```

**`app/models/migration_execution.py`:**
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MigrationExecution(Base):
    """Migration execution tracking model"""

    __tablename__ = "migration_executions"

    id = Column(Integer, primary_key=True, index=True)
    migration_job_id = Column(Integer, ForeignKey("migration_jobs.id", ondelete="CASCADE"), nullable=True)

    # What was migrated
    scraper_ids = Column(ARRAY(Integer), nullable=False)

    # Execution details
    status = Column(String(50), nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results
    results = Column(JSONB, nullable=True, default=[])
    total_locations = Column(Integer, default=0)
    total_events = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)

    # Error information
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)

    # Metadata
    params = Column(JSONB, nullable=True, default={})

    # Relationships
    migration_job = relationship("MigrationJob", back_populates="executions")
```

### 2. Migration Runner Service

**`app/services/migration_runner.py`:**
```python
"""Service for running Tripflow migrations"""
import subprocess
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import MigrationExecution, MigrationJob

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles execution of Tripflow migrations"""

    MIGRATION_SCRIPT = "/home/peter/tripflow/migrations/migrate_all_scrapers.py"

    @staticmethod
    async def execute_migration(
        db: AsyncSession,
        scraper_ids: List[int],
        migration_job_id: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Execute migration for specified scrapers

        Returns:
            Execution ID
        """
        params = params or {}

        # Create execution record
        execution = MigrationExecution(
            migration_job_id=migration_job_id,
            scraper_ids=scraper_ids,
            status="running",
            started_at=datetime.utcnow(),
            params=params
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        execution_id = execution.id

        # Run migration in background
        asyncio.create_task(
            MigrationRunner._run_migration_process(db, execution_id, scraper_ids, params)
        )

        return execution_id

    @staticmethod
    async def _run_migration_process(
        db: AsyncSession,
        execution_id: int,
        scraper_ids: List[int],
        params: Dict[str, Any]
    ):
        """Run the actual migration subprocess"""
        try:
            results = []
            logs = []

            for scraper_id in scraper_ids:
                # Build command
                cmd = [
                    "python3",
                    MigrationRunner.MIGRATION_SCRIPT,
                    "--scraper-id", str(scraper_id),
                    "--scraparr-host", "localhost",
                    "--scraparr-port", "5434",
                    "--tripflow-host", "localhost",
                    "--tripflow-port", "5433"
                ]

                # Add optional parameters
                if params.get("limit"):
                    cmd.extend(["--limit", str(params["limit"])])

                # Execute
                logger.info(f"Running migration for scraper {scraper_id}")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()
                output = stdout.decode() + stderr.decode()
                logs.append(f"=== Scraper {scraper_id} ===\n{output}")

                # Parse output for stats (basic parsing)
                locations = MigrationRunner._parse_stat(output, "Locations:")
                events = MigrationRunner._parse_stat(output, "Events:")
                errors = MigrationRunner._parse_stat(output, "Errors:")

                results.append({
                    "scraper_id": scraper_id,
                    "locations_inserted": locations,
                    "events_inserted": events,
                    "errors": errors
                })

            # Calculate totals
            total_locations = sum(r["locations_inserted"] for r in results)
            total_events = sum(r["events_inserted"] for r in results)
            total_errors = sum(r["errors"] for r in results)

            # Determine final status
            status = "success"
            if total_errors > 0:
                status = "partial" if (total_locations > 0 or total_events > 0) else "failed"

            # Update execution record
            stmt = update(MigrationExecution).where(
                MigrationExecution.id == execution_id
            ).values(
                status=status,
                completed_at=datetime.utcnow(),
                results=results,
                total_locations=total_locations,
                total_events=total_events,
                total_errors=total_errors,
                logs="\n\n".join(logs)
            )
            await db.execute(stmt)
            await db.commit()

            logger.info(f"Migration execution {execution_id} completed: {status}")

        except Exception as e:
            logger.error(f"Migration execution {execution_id} failed: {e}")

            # Update execution with error
            stmt = update(MigrationExecution).where(
                MigrationExecution.id == execution_id
            ).values(
                status="failed",
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
            await db.execute(stmt)
            await db.commit()

    @staticmethod
    def _parse_stat(output: str, label: str) -> int:
        """Parse stat from migration output"""
        try:
            for line in output.split("\n"):
                if label in line:
                    # Extract number after label
                    parts = line.split(label)
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        return int(num_str)
        except:
            pass
        return 0
```

### 3. API Endpoints

**`app/api/migrations.py`:**
```python
"""Migration management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.core.database import get_db
from app.models import MigrationJob, MigrationExecution, Scraper
from app.schemas.migration_job import MigrationJobCreate, MigrationJobUpdate, MigrationJobResponse
from app.schemas.migration_execution import MigrationExecutionResponse
from app.services.migration_runner import MigrationRunner
from app.services.scheduler import SchedulerService

router = APIRouter(prefix="/migrations", tags=["migrations"])


@router.post("/jobs", response_model=MigrationJobResponse)
async def create_migration_job(
    job: MigrationJobCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new migration job"""
    # Validate scraper IDs exist
    result = await db.execute(
        select(Scraper).where(Scraper.id.in_(job.scraper_ids))
    )
    found_scrapers = result.scalars().all()
    if len(found_scrapers) != len(job.scraper_ids):
        raise HTTPException(400, "Invalid scraper IDs")

    # Create job
    db_job = MigrationJob(**job.dict())
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)

    # Add to scheduler if active
    if db_job.is_active and db_job.schedule_type != "manual":
        scheduler = SchedulerService()
        await scheduler.add_migration_job(
            db, db_job.id, db_job.scraper_ids,
            db_job.schedule_type, db_job.schedule_config, db_job.params
        )

    return db_job


@router.get("/jobs", response_model=List[MigrationJobResponse])
async def list_migration_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all migration jobs"""
    result = await db.execute(
        select(MigrationJob).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/jobs/{job_id}/run")
async def run_migration_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger a migration job"""
    # Get job
    result = await db.execute(
        select(MigrationJob).where(MigrationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # Execute migration
    execution_id = await MigrationRunner.execute_migration(
        db, job.scraper_ids, job.id, job.params
    )

    return {"execution_id": execution_id, "status": "started"}


@router.get("/executions", response_model=List[MigrationExecutionResponse])
async def list_migration_executions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List migration executions"""
    result = await db.execute(
        select(MigrationExecution)
        .order_by(desc(MigrationExecution.started_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/executions/{execution_id}", response_model=MigrationExecutionResponse)
async def get_migration_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get migration execution details"""
    result = await db.execute(
        select(MigrationExecution).where(MigrationExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(404, "Execution not found")
    return execution
```

### 4. Scheduler Integration

Update `app/services/scheduler.py` to add method for migration jobs:

```python
async def add_migration_job(
    self,
    db: AsyncSession,
    job_id: int,
    scraper_ids: List[int],
    schedule_type: str,
    schedule_config: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """Add a migration job to the scheduler"""
    scheduler_job_id = f"migration_job_{job_id}"

    # Remove existing job if it exists
    self.remove_job(scheduler_job_id)

    # Create trigger
    trigger = self._create_trigger(schedule_type, schedule_config)

    # Add job to scheduler
    self._scheduler.add_job(
        func=self._execute_migration,
        trigger=trigger,
        id=scheduler_job_id,
        kwargs={
            "job_id": job_id,
            "scraper_ids": scraper_ids,
            "params": params or {},
        },
        replace_existing=True,
    )

    # Update next run time
    job = self._scheduler.get_job(scheduler_job_id)
    if job:
        next_run = job.next_run_time
        await db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == job_id)
            .values(scheduler_job_id=scheduler_job_id, next_run_at=next_run)
        )
        await db.commit()

    return scheduler_job_id


async def _execute_migration(self, job_id: int, scraper_ids: List[int], params: Dict[str, Any]):
    """Execute a scheduled migration"""
    async with async_session_maker() as db:
        try:
            await MigrationRunner.execute_migration(db, scraper_ids, job_id, params)

            # Update last run time
            await db.execute(
                update(MigrationJob)
                .where(MigrationJob.id == job_id)
                .values(last_run_at=func.now())
            )
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to execute migration job {job_id}: {e}")
```

---

## Frontend Implementation

### 1. Add Menu Item

Update `App.tsx`:

```typescript
import { SyncAlt as MigrationIcon } from '@mui/icons-material';

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Scrapers', icon: <CodeIcon />, path: '/scrapers' },
  { text: 'Jobs', icon: <ScheduleIcon />, path: '/jobs' },
  { text: 'Executions', icon: <HistoryIcon />, path: '/executions' },
  { text: 'Migrations', icon: <MigrationIcon />, path: '/migrations' }, // ✨ NEW
  { text: 'Proxy Capture', icon: <ProxyIcon />, path: '/proxy' },
  { text: 'Database', icon: <DatabaseIcon />, path: '/database' },
];

// Add route
<Route path="/migrations" element={<MigrationsPage />} />
```

### 2. Create Migrations Page

**`frontend/src/pages/MigrationsPage.tsx`:**

```typescript
import React from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
} from '@mui/material';
import MigrationJobsTab from '../components/MigrationJobsTab';
import MigrationExecutionsTab from '../components/MigrationExecutionsTab';

const MigrationsPage: React.FC = () => {
  const [tab, setTab] = React.useState(0);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Tripflow Migrations
      </Typography>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Migration Jobs" />
          <Tab label="Execution History" />
        </Tabs>
      </Paper>

      {tab === 0 && <MigrationJobsTab />}
      {tab === 1 && <MigrationExecutionsTab />}
    </Box>
  );
};

export default MigrationsPage;
```

### 3. Migration Jobs Tab

**`frontend/src/components/MigrationJobsTab.tsx`:**

Shows list of migration jobs with:
- Job name (e.g., "Nightly Ticketmaster + CamperContact Sync")
- Scrapers included
- Schedule (e.g., "Daily at 2:00 AM")
- Last run / Next run
- Status (active/inactive)
- Actions: Run Now, Edit, Delete

### 4. Migration Executions Tab

**`frontend/src/components/MigrationExecutionsTab.tsx`:**

Shows execution history with:
- Execution ID
- Job name (or "Manual")
- Scrapers migrated
- Status (running, success, failed, partial)
- Locations inserted
- Events inserted
- Errors
- Duration
- Started at
- Actions: View Logs

---

## Default Migration Schedule

### Recommended Setup

Create a default nightly migration job that runs all active scrapers:

**Name:** "Nightly Full Migration"
**Scrapers:** All (1, 2, 3, 4, 5)
**Schedule:** Daily at 2:00 AM
**Cron:** `0 2 * * *`

```sql
INSERT INTO migration_jobs (
    name,
    description,
    scraper_ids,
    schedule_type,
    schedule_config,
    is_active
) VALUES (
    'Nightly Full Migration',
    'Migrate all scrapers from Scraparr to Tripflow database',
    ARRAY[1, 2, 3, 4, 5],
    'cron',
    '{"expression": "0 2 * * *"}',
    true
);
```

---

## Deployment Steps

### Phase 1: Database Setup

```bash
# SSH to scraparr server
ssh peter@scraparr

# Create migration tables
docker exec -i scraparr-postgres psql -U scraparr -d scraparr << 'EOF'
-- Create migration_jobs table
CREATE TABLE migration_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scraper_ids INTEGER[] NOT NULL,
    schedule_type VARCHAR(50) NOT NULL,
    schedule_config JSONB NOT NULL,
    params JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    scheduler_job_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_migration_jobs_active ON migration_jobs(is_active);
CREATE INDEX idx_migration_jobs_next_run ON migration_jobs(next_run_at);

-- Create migration_executions table
CREATE TABLE migration_executions (
    id SERIAL PRIMARY KEY,
    migration_job_id INTEGER REFERENCES migration_jobs(id) ON DELETE CASCADE,
    scraper_ids INTEGER[] NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '[]',
    total_locations INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    error_message TEXT,
    logs TEXT,
    params JSONB DEFAULT '{}'
);

CREATE INDEX idx_migration_executions_job_id ON migration_executions(migration_job_id);
CREATE INDEX idx_migration_executions_status ON migration_executions(status);
CREATE INDEX idx_migration_executions_started ON migration_executions(started_at DESC);

-- Insert default nightly job
INSERT INTO migration_jobs (
    name,
    description,
    scraper_ids,
    schedule_type,
    schedule_config,
    is_active
) VALUES (
    'Nightly Full Migration',
    'Migrate all scrapers from Scraparr to Tripflow database',
    ARRAY[1, 2, 3, 4, 5],
    'cron',
    '{"expression": "0 2 * * *"}',
    true
);
EOF
```

### Phase 2: Backend Implementation

```bash
# Copy backend files to scraparr
# (Implement files described above)

# Restart backend
docker restart scraparr-backend
```

### Phase 3: Frontend Implementation

```bash
# Copy frontend files
# (Implement pages/components described above)

# Rebuild frontend
cd /home/peter/scraparr/frontend
npm run build

# Restart frontend
docker restart scraparr-frontend
```

### Phase 4: Testing

1. Visit Scraparr UI → Migrations
2. Verify nightly job is listed
3. Click "Run Now" to test manual execution
4. Check execution logs
5. Verify data appears in Tripflow DB

---

## Benefits

1. **Automation:** No more manual SSH to run migrations
2. **Visibility:** Track all migrations in one place
3. **Scheduling:** Nightly updates keep Tripflow data fresh
4. **Logging:** Detailed execution logs for debugging
5. **Flexibility:** Easy to add/remove scrapers from migration
6. **Separation:** Migrations don't clutter scraper execution logs

---

## Future Enhancements

1. **Incremental Migrations:** Only migrate new/updated records
2. **Data Validation:** Check data quality after migration
3. **Notifications:** Email/Slack alerts on migration failures
4. **Rollback:** Ability to undo a migration
5. **Multi-Destination:** Migrate to multiple Tripflow environments
6. **Monitoring Dashboard:** Charts showing migration trends

---

## Summary

This design creates a comprehensive migration automation system that:
- ✅ Separates migration jobs from scraper jobs
- ✅ Tracks execution history independently
- ✅ Provides a dedicated frontend UI
- ✅ Enables scheduled nightly migrations
- ✅ Allows manual triggering from UI
- ✅ Logs all executions with detailed stats

**Estimated Implementation Time:** 6-8 hours
**Priority:** High (currently all migrations are manual)
