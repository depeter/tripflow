-- Migration Automation Database Schema
-- Creates tables for scheduling and tracking Tripflow migrations

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS migration_executions CASCADE;
DROP TABLE IF EXISTS migration_jobs CASCADE;

-- Migration Jobs Table
-- Stores scheduled migration tasks
CREATE TABLE migration_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Which scrapers to migrate
    scraper_ids INTEGER[] NOT NULL,

    -- Scheduling configuration
    schedule_type VARCHAR(50) NOT NULL,  -- 'cron', 'interval', 'once', 'manual'
    schedule_config JSONB NOT NULL,
    -- Example cron: {"expression": "0 2 * * *"}  (2 AM daily)
    -- Example interval: {"seconds": 3600}

    -- Parameters for migration script
    params JSONB DEFAULT '{}',
    -- Example: {"limit": null, "batch_size": 1000}

    -- Status tracking
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,

    -- APScheduler job ID (for scheduler integration)
    scheduler_job_id VARCHAR(255) UNIQUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Migration Executions Table
-- Tracks each migration run with detailed results
CREATE TABLE migration_executions (
    id SERIAL PRIMARY KEY,
    migration_job_id INTEGER REFERENCES migration_jobs(id) ON DELETE CASCADE,

    -- What was migrated
    scraper_ids INTEGER[] NOT NULL,

    -- Execution status
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    -- Values: 'running', 'success', 'failed', 'partial', 'cancelled'

    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Detailed results per scraper
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

    -- Aggregated statistics
    total_locations INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,

    -- Error information
    error_message TEXT,
    logs TEXT,  -- Full migration output logs

    -- Parameters used for this execution
    params JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_migration_jobs_active ON migration_jobs(is_active);
CREATE INDEX idx_migration_jobs_next_run ON migration_jobs(next_run_at);
CREATE INDEX idx_migration_executions_job_id ON migration_executions(migration_job_id);
CREATE INDEX idx_migration_executions_status ON migration_executions(status);
CREATE INDEX idx_migration_executions_started ON migration_executions(started_at DESC);

-- Insert default nightly migration job
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

-- Success message
SELECT 'Migration tables created successfully!' AS status;
SELECT 'Default nightly job created with ID: ' || id AS message FROM migration_jobs LIMIT 1;
