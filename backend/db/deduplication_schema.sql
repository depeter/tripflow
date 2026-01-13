-- Tripflow Deduplication Schema
-- This migration adds support for detecting and merging duplicate locations
-- Run this after init_tripflow_schema.sql

SET search_path TO tripflow, public;

-- =====================================================
-- ADD COLUMNS TO LOCATIONS TABLE
-- =====================================================

-- Add columns for tracking canonical/merged status
ALTER TABLE tripflow.locations ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN DEFAULT true;
ALTER TABLE tripflow.locations ADD COLUMN IF NOT EXISTS canonical_id BIGINT REFERENCES tripflow.locations(id);
ALTER TABLE tripflow.locations ADD COLUMN IF NOT EXISTS merged_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE tripflow.locations ADD COLUMN IF NOT EXISTS source_count INTEGER DEFAULT 1;
ALTER TABLE tripflow.locations ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE;

-- Index for filtering canonical records
CREATE INDEX IF NOT EXISTS idx_locations_canonical ON tripflow.locations(is_canonical) WHERE is_canonical = true;
CREATE INDEX IF NOT EXISTS idx_locations_canonical_id ON tripflow.locations(canonical_id) WHERE canonical_id IS NOT NULL;

COMMENT ON COLUMN tripflow.locations.is_canonical IS 'True if this is the canonical (merged) record, false if merged into another';
COMMENT ON COLUMN tripflow.locations.canonical_id IS 'If merged, points to the canonical location ID that this was merged into';
COMMENT ON COLUMN tripflow.locations.merged_at IS 'Timestamp when this location was merged into another';
COMMENT ON COLUMN tripflow.locations.source_count IS 'Number of sources that contributed data to this canonical record';
COMMENT ON COLUMN tripflow.locations.last_synced_at IS 'Last time this record was updated from external source';

-- =====================================================
-- LOCATION SOURCE MAPPINGS TABLE
-- =====================================================

-- Tracks which external IDs from which sources map to a canonical location
-- This prevents re-duplication when syncing from sources
CREATE TABLE IF NOT EXISTS tripflow.location_source_mappings (
    id BIGSERIAL PRIMARY KEY,
    canonical_location_id BIGINT NOT NULL REFERENCES tripflow.locations(id) ON DELETE CASCADE,
    source tripflow.location_source NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    source_url VARCHAR(500),

    -- Data quality indicators from this source
    has_description BOOLEAN DEFAULT false,
    has_images BOOLEAN DEFAULT false,
    has_rating BOOLEAN DEFAULT false,
    data_quality_score INTEGER DEFAULT 0,  -- 0-100

    -- Metadata
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one mapping per external_id + source
    CONSTRAINT unique_source_external UNIQUE(external_id, source)
);

CREATE INDEX IF NOT EXISTS idx_source_mappings_canonical ON tripflow.location_source_mappings(canonical_location_id);
CREATE INDEX IF NOT EXISTS idx_source_mappings_source ON tripflow.location_source_mappings(source);
CREATE INDEX IF NOT EXISTS idx_source_mappings_external ON tripflow.location_source_mappings(external_id, source);

COMMENT ON TABLE tripflow.location_source_mappings IS 'Maps external IDs from various sources to canonical locations, preventing re-duplication on sync';

-- =====================================================
-- DUPLICATE CANDIDATES TABLE
-- =====================================================

-- Stores potential duplicate pairs for review and processing
CREATE TABLE IF NOT EXISTS tripflow.duplicate_candidates (
    id BIGSERIAL PRIMARY KEY,
    location_id_1 BIGINT NOT NULL REFERENCES tripflow.locations(id) ON DELETE CASCADE,
    location_id_2 BIGINT NOT NULL REFERENCES tripflow.locations(id) ON DELETE CASCADE,

    -- Match confidence scores (0-100)
    geo_proximity_score INTEGER,      -- Based on distance
    name_similarity_score INTEGER,    -- Fuzzy name match (0-100)
    overall_confidence INTEGER,       -- Combined score

    -- Match details
    distance_meters DOUBLE PRECISION,

    -- Resolution status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, confirmed, rejected, merged
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),  -- 'auto' or user email

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate pairs (always store smaller ID first)
    CONSTRAINT unique_duplicate_pair UNIQUE(location_id_1, location_id_2),
    CONSTRAINT ordered_ids CHECK(location_id_1 < location_id_2)
);

CREATE INDEX IF NOT EXISTS idx_duplicates_status ON tripflow.duplicate_candidates(status);
CREATE INDEX IF NOT EXISTS idx_duplicates_confidence ON tripflow.duplicate_candidates(overall_confidence DESC);
CREATE INDEX IF NOT EXISTS idx_duplicates_location1 ON tripflow.duplicate_candidates(location_id_1);
CREATE INDEX IF NOT EXISTS idx_duplicates_location2 ON tripflow.duplicate_candidates(location_id_2);

COMMENT ON TABLE tripflow.duplicate_candidates IS 'Potential duplicate location pairs identified by the deduplication system';

-- =====================================================
-- MERGE HISTORY TABLE
-- =====================================================

-- Audit trail for all merge operations
CREATE TABLE IF NOT EXISTS tripflow.merge_history (
    id BIGSERIAL PRIMARY KEY,
    canonical_location_id BIGINT NOT NULL,
    merged_location_id BIGINT NOT NULL,
    merged_source tripflow.location_source NOT NULL,
    merged_external_id VARCHAR(255) NOT NULL,

    -- What data was taken from merged record
    data_contributed JSONB,  -- {'description': true, 'images': 3, 'amenities': ['wifi', 'shower']}

    -- Metadata
    merged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merged_by VARCHAR(100)  -- 'auto' or user email
);

CREATE INDEX IF NOT EXISTS idx_merge_history_canonical ON tripflow.merge_history(canonical_location_id);
CREATE INDEX IF NOT EXISTS idx_merge_history_merged ON tripflow.merge_history(merged_location_id);
CREATE INDEX IF NOT EXISTS idx_merge_history_date ON tripflow.merge_history(merged_at DESC);

COMMENT ON TABLE tripflow.merge_history IS 'Audit trail of all location merge operations';

-- =====================================================
-- DUPLICATE DETECTION FUNCTION
-- =====================================================

-- Function to find duplicate location candidates
-- Uses PostGIS for geographic proximity and pg_trgm for name similarity
CREATE OR REPLACE FUNCTION tripflow.find_duplicate_candidates(
    distance_threshold_meters INTEGER DEFAULT 100,
    name_similarity_threshold REAL DEFAULT 0.4,
    batch_size INTEGER DEFAULT 1000
) RETURNS TABLE (
    location_id_1 BIGINT,
    location_id_2 BIGINT,
    distance_meters DOUBLE PRECISION,
    name_similarity REAL,
    same_city BOOLEAN,
    geo_score INTEGER,
    name_score INTEGER,
    overall_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH location_pairs AS (
        SELECT
            l1.id AS id1,
            l2.id AS id2,
            ST_Distance(l1.geom::geography, l2.geom::geography) AS dist_m,
            similarity(LOWER(l1.name), LOWER(l2.name)) AS name_sim,
            (COALESCE(l1.city, '') = COALESCE(l2.city, '') AND l1.city IS NOT NULL) AS city_match
        FROM tripflow.locations l1
        INNER JOIN tripflow.locations l2 ON l1.id < l2.id  -- Avoid duplicates and self-matches
        WHERE l1.is_active = true
          AND l2.is_active = true
          AND l1.is_canonical = true
          AND l2.is_canonical = true
          AND l1.source != l2.source  -- Only cross-source duplicates
          AND ST_DWithin(
              l1.geom::geography,
              l2.geom::geography,
              distance_threshold_meters
          )
    )
    SELECT
        lp.id1,
        lp.id2,
        lp.dist_m,
        lp.name_sim,
        lp.city_match,
        -- Geo score: 100 at 0m, 0 at threshold
        GREATEST(0, (100 - (lp.dist_m / distance_threshold_meters * 100)))::INTEGER AS geo_score,
        -- Name score: 0-100 based on similarity
        (lp.name_sim * 100)::INTEGER AS name_score,
        -- Overall: weighted average (geo 40%, name 50%, city 10%)
        (
            GREATEST(0, (100 - (lp.dist_m / distance_threshold_meters * 100))) * 0.4 +
            lp.name_sim * 100 * 0.5 +
            CASE WHEN lp.city_match THEN 10 ELSE 0 END
        )::INTEGER AS overall_score
    FROM location_pairs lp
    WHERE lp.name_sim >= name_similarity_threshold
       OR lp.dist_m < 30  -- Very close locations are always candidates
    ORDER BY overall_score DESC
    LIMIT batch_size;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION tripflow.find_duplicate_candidates IS 'Finds potential duplicate locations across different sources using geographic proximity and name similarity';

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Function to get duplicate statistics
CREATE OR REPLACE FUNCTION tripflow.get_duplicate_stats()
RETURNS TABLE (
    total_locations BIGINT,
    canonical_locations BIGINT,
    merged_locations BIGINT,
    pending_candidates BIGINT,
    confirmed_candidates BIGINT,
    rejected_candidates BIGINT,
    merged_candidates BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM tripflow.locations)::BIGINT AS total_locations,
        (SELECT COUNT(*) FROM tripflow.locations WHERE is_canonical = true)::BIGINT AS canonical_locations,
        (SELECT COUNT(*) FROM tripflow.locations WHERE is_canonical = false)::BIGINT AS merged_locations,
        (SELECT COUNT(*) FROM tripflow.duplicate_candidates WHERE status = 'pending')::BIGINT AS pending_candidates,
        (SELECT COUNT(*) FROM tripflow.duplicate_candidates WHERE status = 'confirmed')::BIGINT AS confirmed_candidates,
        (SELECT COUNT(*) FROM tripflow.duplicate_candidates WHERE status = 'rejected')::BIGINT AS rejected_candidates,
        (SELECT COUNT(*) FROM tripflow.duplicate_candidates WHERE status = 'merged')::BIGINT AS merged_candidates;
END;
$$ LANGUAGE plpgsql;

-- Function to populate duplicate candidates table
CREATE OR REPLACE FUNCTION tripflow.populate_duplicate_candidates(
    distance_threshold_meters INTEGER DEFAULT 100,
    min_confidence INTEGER DEFAULT 60
) RETURNS INTEGER AS $$
DECLARE
    inserted_count INTEGER;
BEGIN
    INSERT INTO tripflow.duplicate_candidates
        (location_id_1, location_id_2, geo_proximity_score,
         name_similarity_score, overall_confidence, distance_meters, status)
    SELECT
        location_id_1, location_id_2, geo_score,
        name_score, overall_score, distance_meters, 'pending'
    FROM tripflow.find_duplicate_candidates(distance_threshold_meters, 0.3, 50000)
    WHERE overall_score >= min_confidence
    ON CONFLICT (location_id_1, location_id_2) DO UPDATE SET
        overall_confidence = EXCLUDED.overall_confidence,
        distance_meters = EXCLUDED.distance_meters;

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION tripflow.populate_duplicate_candidates IS 'Scans for duplicate locations and populates the duplicate_candidates table';

-- =====================================================
-- UPDATE PERMISSIONS
-- =====================================================

GRANT ALL PRIVILEGES ON TABLE tripflow.location_source_mappings TO tripflow;
GRANT ALL PRIVILEGES ON TABLE tripflow.duplicate_candidates TO tripflow;
GRANT ALL PRIVILEGES ON TABLE tripflow.merge_history TO tripflow;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA tripflow TO tripflow;
