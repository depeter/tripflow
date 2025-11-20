-- Add multilingual support to TripFlow
-- Creates translation tables for locations and events
-- Supports: en, nl, fr, de, es, it (extensible for future languages)

-- Location translations table
CREATE TABLE IF NOT EXISTS tripflow.location_translations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES tripflow.locations(id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL,  -- ISO 639-1 codes: en, nl, fr, de, es, it
    name VARCHAR(500),                  -- Translated name (optional, usually same)
    description TEXT,                    -- Translated description
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one translation per language per location
    CONSTRAINT unique_location_translation UNIQUE (location_id, language_code)
);

-- Create indexes for fast lookups
CREATE INDEX idx_location_translations_location_id ON tripflow.location_translations(location_id);
CREATE INDEX idx_location_translations_language ON tripflow.location_translations(language_code);

-- Event translations table
CREATE TABLE IF NOT EXISTS tripflow.event_translations (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES tripflow.events(id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL,  -- ISO 639-1 codes: en, nl, fr, de, es, it
    name VARCHAR(500),                  -- Translated event name
    description TEXT,                    -- Translated description
    short_description TEXT,             -- Translated short summary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one translation per language per event
    CONSTRAINT unique_event_translation UNIQUE (event_id, language_code)
);

-- Create indexes for fast lookups
CREATE INDEX idx_event_translations_event_id ON tripflow.event_translations(event_id);
CREATE INDEX idx_event_translations_language ON tripflow.event_translations(language_code);

-- Grant permissions to tripflow user
GRANT ALL PRIVILEGES ON tripflow.location_translations TO tripflow;
GRANT ALL PRIVILEGES ON tripflow.event_translations TO tripflow;
GRANT USAGE, SELECT ON SEQUENCE tripflow.location_translations_id_seq TO tripflow;
GRANT USAGE, SELECT ON SEQUENCE tripflow.event_translations_id_seq TO tripflow;

-- Add comments for documentation
COMMENT ON TABLE tripflow.location_translations IS 'Multilingual translations for location names and descriptions';
COMMENT ON TABLE tripflow.event_translations IS 'Multilingual translations for event names and descriptions';
COMMENT ON COLUMN tripflow.location_translations.language_code IS 'ISO 639-1 language code (en, nl, fr, de, es, it)';
COMMENT ON COLUMN tripflow.event_translations.language_code IS 'ISO 639-1 language code (en, nl, fr, de, es, it)';
