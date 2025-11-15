-- Add Admin Dashboard Tables to Tripflow Schema
-- Run this after init_tripflow_schema_no_postgis.sql

-- =====================================================
-- MIGRATION TRACKING TABLES
-- =====================================================

-- Track individual migration executions
CREATE TABLE IF NOT EXISTS tripflow.migration_runs (
    id BIGSERIAL PRIMARY KEY,

    -- Scraper info
    scraper_id INTEGER NOT NULL,
    scraper_name VARCHAR(255),
    scraper_schema VARCHAR(100),

    -- Execution status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Statistics
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,

    -- Details
    error_message TEXT,
    log_output TEXT,  -- Full migration log
    params JSONB,  -- Migration parameters (limit, filters, etc.)

    -- Metadata
    triggered_by VARCHAR(100),  -- 'admin', 'schedule', 'api', user email
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Configure automatic migration schedules
CREATE TABLE IF NOT EXISTS tripflow.migration_schedules (
    id BIGSERIAL PRIMARY KEY,

    scraper_id INTEGER NOT NULL UNIQUE,
    scraper_name VARCHAR(255),

    -- Schedule
    schedule_cron VARCHAR(100),  -- Cron expression
    is_active BOOLEAN DEFAULT false,

    -- Tracking
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(20),
    next_run_at TIMESTAMP WITH TIME ZONE,

    -- Config
    auto_run_params JSONB,  -- Default params for scheduled runs

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Metadata about scrapers from scraparr database
CREATE TABLE IF NOT EXISTS tripflow.scraper_metadata (
    id BIGSERIAL PRIMARY KEY,
    scraper_id INTEGER UNIQUE NOT NULL,

    -- From scraparr.scrapers table
    name VARCHAR(255),
    schema_name VARCHAR(100),
    module_path VARCHAR(500),
    class_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,

    -- Stats from last sync
    total_records INTEGER,
    last_scraped_at TIMESTAMP WITH TIME ZONE,

    -- Cache/sync
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_migration_runs_scraper ON tripflow.migration_runs(scraper_id);
CREATE INDEX IF NOT EXISTS idx_migration_runs_status ON tripflow.migration_runs(status);
CREATE INDEX IF NOT EXISTS idx_migration_runs_started ON tripflow.migration_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_migration_runs_created ON tripflow.migration_runs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_migration_schedules_scraper ON tripflow.migration_schedules(scraper_id);
CREATE INDEX IF NOT EXISTS idx_migration_schedules_active ON tripflow.migration_schedules(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_scraper_metadata_scraper ON tripflow.scraper_metadata(scraper_id);
CREATE INDEX IF NOT EXISTS idx_scraper_metadata_active ON tripflow.scraper_metadata(is_active) WHERE is_active = true;

-- =====================================================
-- SEED DATA - Populate scraper metadata
-- =====================================================

-- Insert known scrapers from scraparr
INSERT INTO tripflow.scraper_metadata (scraper_id, name, schema_name, is_active)
VALUES
    (1, 'Park4Night Grid Scraper', 'scraper_1', true),
    (2, 'UiTinVlaanderen Events', 'scraper_2', true),
    (3, 'Eventbrite Events Scraper', 'scraper_3', true)
ON CONFLICT (scraper_id) DO UPDATE SET
    name = EXCLUDED.name,
    schema_name = EXCLUDED.schema_name,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE tripflow.migration_runs IS 'Track migration execution history for admin dashboard';
COMMENT ON TABLE tripflow.migration_schedules IS 'Configure automatic migration schedules';
COMMENT ON TABLE tripflow.scraper_metadata IS 'Cached metadata about scrapers from scraparr database';

COMMENT ON COLUMN tripflow.migration_runs.log_output IS 'Full log output from migration execution (last 1000 lines)';
COMMENT ON COLUMN tripflow.migration_runs.params IS 'JSON parameters used for migration (e.g., {"limit": 100})';
COMMENT ON COLUMN tripflow.migration_schedules.schedule_cron IS 'Cron expression for automatic runs (e.g., "0 2 * * *")';
