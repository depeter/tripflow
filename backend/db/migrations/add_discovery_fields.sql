-- Migration: Add discovery mode fields to events and create user_favorites table
-- Date: 2025-11-16
-- Description: Enhance events table for discovery mode and add favorites functionality

-- Add new columns to events table
ALTER TABLE tripflow.events
  ADD COLUMN IF NOT EXISTS organizer VARCHAR(300),
  ADD COLUMN IF NOT EXISTS event_type VARCHAR(100),
  ADD COLUMN IF NOT EXISTS themes TEXT[],
  ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';

-- Ensure geom column exists (should already be there, but just in case)
ALTER TABLE tripflow.events
  ADD COLUMN IF NOT EXISTS geom GEOMETRY(Point, 4326);

-- Update geom for existing rows if null
UPDATE tripflow.events
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;

-- Create indexes for discovery queries
CREATE INDEX IF NOT EXISTS idx_events_geom ON tripflow.events USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_events_start_datetime ON tripflow.events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_events_source ON tripflow.events(source);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON tripflow.events(event_type);

-- Create user_favorites table
CREATE TABLE IF NOT EXISTS tripflow.user_favorites (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES tripflow.users(id) ON DELETE CASCADE,
  event_id INTEGER NOT NULL REFERENCES tripflow.events(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT unique_user_event_favorite UNIQUE(user_id, event_id)
);

-- Create indexes for favorites
CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON tripflow.user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_event ON tripflow.user_favorites(event_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_created ON tripflow.user_favorites(created_at DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE tripflow.user_favorites TO tripflow;
GRANT USAGE, SELECT ON SEQUENCE tripflow.user_favorites_id_seq TO tripflow;

COMMENT ON TABLE tripflow.user_favorites IS 'User saved/favorite events for discovery mode';
COMMENT ON COLUMN tripflow.events.organizer IS 'Event organizer name';
COMMENT ON COLUMN tripflow.events.event_type IS 'Original event type from data source';
COMMENT ON COLUMN tripflow.events.themes IS 'Event themes/topics as array';
COMMENT ON COLUMN tripflow.events.source IS 'Data source: uitinvlaanderen, manual, etc';
