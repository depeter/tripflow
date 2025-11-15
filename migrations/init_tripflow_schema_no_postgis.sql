-- Tripflow Database Schema (WITHOUT PostGIS)
-- This version works without PostGIS extension
-- Uses simple lat/lon fields instead of geometry types

-- Create schema
CREATE SCHEMA IF NOT EXISTS tripflow;

-- Set search path
SET search_path TO tripflow, public;

-- =====================================================
-- ENUM TYPES
-- =====================================================

CREATE TYPE tripflow.location_type AS ENUM (
    'CAMPSITE',
    'PARKING',
    'REST_AREA',
    'SERVICE_AREA',
    'POI',
    'EVENT',
    'ATTRACTION',
    'RESTAURANT',
    'HOTEL',
    'ACTIVITY'
);

CREATE TYPE tripflow.location_source AS ENUM (
    'park4night',
    'campercontact',
    'uitinvlaanderen',
    'openstreetmap',
    'google_places',
    'manual',
    'other'
);

CREATE TYPE tripflow.price_type AS ENUM (
    'free',
    'paid',
    'donation',
    'unknown'
);

-- =====================================================
-- MAIN TABLES
-- =====================================================

-- Main locations table (consolidated from all sources)
CREATE TABLE IF NOT EXISTS tripflow.locations (
    id BIGSERIAL PRIMARY KEY,

    -- Source identification
    external_id VARCHAR(255) NOT NULL,
    source tripflow.location_source NOT NULL,
    source_url VARCHAR(500),

    -- Basic information
    name VARCHAR(500) NOT NULL,
    description TEXT,
    location_type tripflow.location_type NOT NULL,

    -- Geographic data (WITHOUT PostGIS)
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    -- Removed: geom GEOMETRY(Point, 4326)
    altitude INTEGER, -- meters above sea level

    -- Address information
    address VARCHAR(500),
    city VARCHAR(200),
    region VARCHAR(200),
    country VARCHAR(100),
    country_code VARCHAR(2), -- ISO 3166-1 alpha-2
    postal_code VARCHAR(20),

    -- Ratings and reviews
    rating DECIMAL(3,2) CHECK (rating >= 0 AND rating <= 5),
    rating_count INTEGER DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    popularity_score DECIMAL(5,2), -- Calculated score for recommendations

    -- Pricing
    price_type tripflow.price_type DEFAULT 'unknown',
    price_min DECIMAL(10,2),
    price_max DECIMAL(10,2),
    price_currency VARCHAR(3) DEFAULT 'EUR',
    price_info TEXT, -- Free text price information

    -- Capacity (for campsites/parking)
    capacity_total INTEGER,
    capacity_available INTEGER, -- For real-time updates if available

    -- Contact information
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),

    -- Features and amenities (JSONB for flexibility)
    amenities JSONB DEFAULT '[]'::jsonb,
    features JSONB DEFAULT '[]'::jsonb,
    restrictions JSONB DEFAULT '[]'::jsonb,

    -- Images and media
    images JSONB DEFAULT '[]'::jsonb,
    main_image_url VARCHAR(500),

    -- Tags for categorization
    tags TEXT[], -- Array of tags

    -- Opening hours (JSONB for complex schedules)
    opening_hours JSONB,
    is_24_7 BOOLEAN DEFAULT false,
    seasonal_info TEXT,

    -- Status flags
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    requires_booking BOOLEAN DEFAULT false,

    -- Metadata
    raw_data JSONB, -- Original data from source
    last_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_external_source UNIQUE(external_id, source)
);

-- Events table (for time-based activities)
CREATE TABLE IF NOT EXISTS tripflow.events (
    id BIGSERIAL PRIMARY KEY,
    location_id BIGINT REFERENCES tripflow.locations(id) ON DELETE CASCADE,

    -- Event identification
    external_id VARCHAR(255) NOT NULL,
    source tripflow.location_source NOT NULL,

    -- Event information
    name VARCHAR(500) NOT NULL,
    description TEXT,
    event_type VARCHAR(100),

    -- Timing
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    is_recurring BOOLEAN DEFAULT false,
    recurrence_rule TEXT, -- iCal RRULE format

    -- Event specific
    organizer VARCHAR(255),
    performer VARCHAR(255),
    category VARCHAR(100),
    themes TEXT[],

    -- Capacity and booking
    capacity INTEGER,
    tickets_available INTEGER,
    booking_url VARCHAR(500),

    -- Pricing
    price_min DECIMAL(10,2),
    price_max DECIMAL(10,2),
    price_currency VARCHAR(3) DEFAULT 'EUR',

    -- Status
    is_cancelled BOOLEAN DEFAULT false,
    is_sold_out BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_event_external UNIQUE(external_id, source)
);

-- Reviews table (aggregated from sources)
CREATE TABLE IF NOT EXISTS tripflow.reviews (
    id BIGSERIAL PRIMARY KEY,
    location_id BIGINT REFERENCES tripflow.locations(id) ON DELETE CASCADE,

    -- Review source
    external_id VARCHAR(255),
    source tripflow.location_source NOT NULL,

    -- Review data
    author_name VARCHAR(255),
    author_id VARCHAR(255),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(500),
    comment TEXT,

    -- Review metadata
    language VARCHAR(10),
    is_verified BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,

    -- Timestamps
    review_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_review_external UNIQUE(external_id, source)
);

-- Sync log table for ETL tracking
CREATE TABLE IF NOT EXISTS tripflow.sync_log (
    id BIGSERIAL PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL, -- 'full', 'incremental', 'source_specific'
    source tripflow.location_source,

    -- Sync statistics
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Record counts
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,

    -- Status and errors
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT,
    warnings JSONB DEFAULT '[]'::jsonb,

    -- Additional metadata
    sync_params JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data quality metrics table
CREATE TABLE IF NOT EXISTS tripflow.data_quality_metrics (
    id BIGSERIAL PRIMARY KEY,
    source tripflow.location_source NOT NULL,
    metric_date DATE NOT NULL,

    -- Quality metrics
    total_records INTEGER,
    records_with_description INTEGER,
    records_with_images INTEGER,
    records_with_ratings INTEGER,
    records_with_coordinates INTEGER,
    records_with_address INTEGER,
    records_with_price INTEGER,

    -- Calculated percentages
    completeness_score DECIMAL(5,2), -- 0-100

    -- Issues found
    duplicate_count INTEGER DEFAULT 0,
    invalid_coordinates INTEGER DEFAULT 0,
    missing_required_fields INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_source_date UNIQUE(source, metric_date)
);

-- =====================================================
-- INDEXES (Modified for non-PostGIS)
-- =====================================================

-- Location coordinate indexes (replaces spatial index)
CREATE INDEX idx_locations_coords ON tripflow.locations(latitude, longitude);
CREATE INDEX idx_locations_lat ON tripflow.locations(latitude);
CREATE INDEX idx_locations_lon ON tripflow.locations(longitude);

-- Search indexes
CREATE INDEX idx_locations_name ON tripflow.locations(name);
CREATE INDEX idx_locations_description ON tripflow.locations(description);

-- Filter indexes
CREATE INDEX idx_locations_type ON tripflow.locations(location_type);
CREATE INDEX idx_locations_source ON tripflow.locations(source);
CREATE INDEX idx_locations_country ON tripflow.locations(country);
CREATE INDEX idx_locations_city ON tripflow.locations(city);
CREATE INDEX idx_locations_active ON tripflow.locations(is_active) WHERE is_active = true;
CREATE INDEX idx_locations_featured ON tripflow.locations(is_featured) WHERE is_featured = true;

-- Performance indexes
CREATE INDEX idx_locations_rating ON tripflow.locations(rating DESC) WHERE rating IS NOT NULL;
CREATE INDEX idx_locations_popularity ON tripflow.locations(popularity_score DESC) WHERE popularity_score IS NOT NULL;
CREATE INDEX idx_locations_updated ON tripflow.locations(updated_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_locations_country_type_rating ON tripflow.locations(country, location_type, rating DESC);
CREATE INDEX idx_locations_type_active_rating ON tripflow.locations(location_type, is_active, rating DESC);

-- Events indexes
CREATE INDEX idx_events_location ON tripflow.events(location_id);
CREATE INDEX idx_events_dates ON tripflow.events(start_date, end_date);
CREATE INDEX idx_events_type ON tripflow.events(event_type);
CREATE INDEX idx_events_upcoming ON tripflow.events(start_date) WHERE start_date > NOW();

-- Reviews indexes
CREATE INDEX idx_reviews_location ON tripflow.reviews(location_id);
CREATE INDEX idx_reviews_rating ON tripflow.reviews(rating);
CREATE INDEX idx_reviews_date ON tripflow.reviews(review_date DESC);

-- Sync log indexes
CREATE INDEX idx_sync_log_source ON tripflow.sync_log(source);
CREATE INDEX idx_sync_log_status ON tripflow.sync_log(status);
CREATE INDEX idx_sync_log_started ON tripflow.sync_log(started_at DESC);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION tripflow.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_locations_updated_at
    BEFORE UPDATE ON tripflow.locations
    FOR EACH ROW
    EXECUTE FUNCTION tripflow.update_updated_at();

CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON tripflow.events
    FOR EACH ROW
    EXECUTE FUNCTION tripflow.update_updated_at();

-- Function to calculate popularity score
CREATE OR REPLACE FUNCTION tripflow.calculate_popularity_score(
    rating DECIMAL,
    rating_count INTEGER,
    review_count INTEGER,
    is_verified BOOLEAN
) RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL;
BEGIN
    score := 0;

    -- Base score from rating (0-50 points)
    IF rating IS NOT NULL THEN
        score := score + (rating * 10);
    END IF;

    -- Bonus for number of ratings (0-30 points)
    IF rating_count > 0 THEN
        score := score + LEAST(30, rating_count / 10.0);
    END IF;

    -- Bonus for reviews (0-15 points)
    IF review_count > 0 THEN
        score := score + LEAST(15, review_count / 5.0);
    END IF;

    -- Bonus for verification (5 points)
    IF is_verified THEN
        score := score + 5;
    END IF;

    RETURN ROUND(score, 2);
END;
$$ LANGUAGE plpgsql;

-- Simple distance calculation function (without PostGIS)
-- Uses Haversine formula for distance between two points
CREATE OR REPLACE FUNCTION tripflow.calculate_distance_km(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
DECLARE
    R CONSTANT DOUBLE PRECISION := 6371; -- Earth's radius in kilometers
    dlat DOUBLE PRECISION;
    dlon DOUBLE PRECISION;
    a DOUBLE PRECISION;
    c DOUBLE PRECISION;
BEGIN
    dlat := RADIANS(lat2 - lat1);
    dlon := RADIANS(lon2 - lon1);

    a := SIN(dlat/2) * SIN(dlat/2) +
         COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
         SIN(dlon/2) * SIN(dlon/2);

    c := 2 * ATAN2(SQRT(a), SQRT(1-a));

    RETURN R * c;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS
-- =====================================================

-- View for location statistics by country
CREATE OR REPLACE VIEW tripflow.location_stats_by_country AS
SELECT
    country,
    location_type,
    COUNT(*) as count,
    AVG(rating) as avg_rating,
    SUM(review_count) as total_reviews
FROM tripflow.locations
WHERE is_active = true
GROUP BY country, location_type;

-- View for upcoming events
CREATE OR REPLACE VIEW tripflow.upcoming_events AS
SELECT
    e.*,
    l.name as location_name,
    l.city,
    l.country,
    l.latitude,
    l.longitude
FROM tripflow.events e
JOIN tripflow.locations l ON e.location_id = l.id
WHERE e.start_date > NOW()
    AND e.is_cancelled = false
ORDER BY e.start_date;

-- View for top-rated locations
CREATE OR REPLACE VIEW tripflow.top_rated_locations AS
SELECT
    id,
    name,
    location_type,
    city,
    country,
    rating,
    review_count,
    popularity_score
FROM tripflow.locations
WHERE rating >= 4.0
    AND review_count >= 5
    AND is_active = true
ORDER BY popularity_score DESC, rating DESC;

-- =====================================================
-- PERMISSIONS
-- =====================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA tripflow TO scraparr;

-- Grant all privileges on tables to scraparr user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tripflow TO scraparr;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tripflow TO scraparr;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON SCHEMA tripflow IS 'Main schema for Tripflow application containing consolidated location data from multiple sources';
COMMENT ON TABLE tripflow.locations IS 'Consolidated locations from all data sources (Park4Night, CamperContact, UiT, etc.)';
COMMENT ON TABLE tripflow.events IS 'Time-based events linked to locations';
COMMENT ON TABLE tripflow.reviews IS 'Aggregated reviews from all sources';
COMMENT ON TABLE tripflow.sync_log IS 'ETL sync history and statistics';
COMMENT ON TABLE tripflow.data_quality_metrics IS 'Data quality tracking by source';

COMMENT ON COLUMN tripflow.locations.popularity_score IS 'Calculated score based on rating, reviews, and verification status (0-100)';
COMMENT ON COLUMN tripflow.locations.amenities IS 'JSON array of amenities like: wifi, shower, toilet, electricity, water, etc.';
COMMENT ON COLUMN tripflow.locations.features IS 'JSON array of features like: pet-friendly, wheelchair-accessible, family-friendly, etc.';
COMMENT ON COLUMN tripflow.locations.raw_data IS 'Original unprocessed data from source for debugging and data recovery';

COMMENT ON FUNCTION tripflow.calculate_distance_km IS 'Calculate distance between two coordinates using Haversine formula (returns kilometers)';