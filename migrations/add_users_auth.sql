-- Add User Authentication Tables to Tripflow Schema
-- Implements email/password and OAuth social logins

-- =====================================================
-- USER TABLES
-- =====================================================

-- Main users table
CREATE TABLE IF NOT EXISTS tripflow.users (
    id BIGSERIAL PRIMARY KEY,

    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    password_hash VARCHAR(255),  -- NULL for OAuth-only users

    -- Profile
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),

    -- OAuth identifiers
    google_id VARCHAR(255) UNIQUE,
    microsoft_id VARCHAR(255) UNIQUE,

    -- Subscription & billing
    subscription_tier VARCHAR(50) DEFAULT 'free',
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    stripe_customer_id VARCHAR(255),

    -- Permissions
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- User sessions for JWT management
CREATE TABLE IF NOT EXISTS tripflow.user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE CASCADE NOT NULL,

    -- Session tokens
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255),

    -- Session metadata
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    device_type VARCHAR(50),

    -- Timing
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OAuth connections (can have multiple per user)
CREATE TABLE IF NOT EXISTS tripflow.oauth_connections (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE CASCADE NOT NULL,

    -- Provider info
    provider VARCHAR(50) NOT NULL,  -- 'google', 'microsoft', 'facebook', etc.
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),

    -- OAuth tokens (encrypted at application level)
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Profile data from provider
    provider_data JSONB,  -- Raw profile data

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_provider_user UNIQUE(provider, provider_user_id)
);

-- Email verification tokens
CREATE TABLE IF NOT EXISTS tripflow.email_verification_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE CASCADE NOT NULL,

    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS tripflow.password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE CASCADE NOT NULL,

    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- USER ACTIVITY TRACKING
-- =====================================================

-- Track trip creations (for analytics)
CREATE TABLE IF NOT EXISTS tripflow.trip_creations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE SET NULL,  -- Allow anonymous

    -- Trip details
    trip_type VARCHAR(50),  -- 'multi_day', 'day_trip'
    duration_days INTEGER,
    duration_hours INTEGER,
    num_waypoints INTEGER,
    total_distance_km DECIMAL(10,2),
    start_country VARCHAR(100),
    end_country VARCHAR(100),

    -- Session
    session_id VARCHAR(255),
    ip_address VARCHAR(45),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Track API usage (for rate limiting and analytics)
CREATE TABLE IF NOT EXISTS tripflow.api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES tripflow.users(id) ON DELETE SET NULL,  -- Allow anonymous

    endpoint VARCHAR(500),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,

    -- Session
    session_id VARCHAR(255),
    ip_address VARCHAR(45),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON tripflow.users(email);
CREATE INDEX IF NOT EXISTS idx_users_google ON tripflow.users(google_id) WHERE google_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_microsoft ON tripflow.users(microsoft_id) WHERE microsoft_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_active ON tripflow.users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_tier ON tripflow.users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_created ON tripflow.users(created_at DESC);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_token ON tripflow.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON tripflow.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON tripflow.user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON tripflow.user_sessions(user_id, expires_at) WHERE expires_at > NOW();

-- OAuth indexes
CREATE INDEX IF NOT EXISTS idx_oauth_user ON tripflow.oauth_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_provider ON tripflow.oauth_connections(provider, provider_user_id);

-- Token indexes
CREATE INDEX IF NOT EXISTS idx_email_verify_token ON tripflow.email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verify_user ON tripflow.email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_token ON tripflow.password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON tripflow.password_reset_tokens(user_id);

-- Activity indexes
CREATE INDEX IF NOT EXISTS idx_trip_creations_user ON tripflow.trip_creations(user_id);
CREATE INDEX IF NOT EXISTS idx_trip_creations_created ON tripflow.trip_creations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_user ON tripflow.api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON tripflow.api_usage(endpoint, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_created ON tripflow.api_usage(created_at DESC);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION tripflow.update_user_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON tripflow.users
    FOR EACH ROW
    EXECUTE FUNCTION tripflow.update_user_updated_at();

CREATE TRIGGER update_oauth_updated_at
    BEFORE UPDATE ON tripflow.oauth_connections
    FOR EACH ROW
    EXECUTE FUNCTION tripflow.update_user_updated_at();

-- Cleanup expired sessions periodically
CREATE OR REPLACE FUNCTION tripflow.cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM tripflow.user_sessions
    WHERE expires_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Cleanup expired tokens
CREATE OR REPLACE FUNCTION tripflow.cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM tripflow.email_verification_tokens
    WHERE expires_at < NOW();

    DELETE FROM tripflow.password_reset_tokens
    WHERE expires_at < NOW() AND used_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SEED DATA - Create admin user
-- =====================================================

-- Create default admin user (password: 'admin123' - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO tripflow.users (
    email,
    password_hash,
    full_name,
    email_verified,
    is_active,
    is_admin,
    subscription_tier
) VALUES (
    'admin@tripflow.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKjGzZ0VG',  -- 'admin123'
    'Admin User',
    true,
    true,
    true,
    'premium'
) ON CONFLICT (email) DO NOTHING;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE tripflow.users IS 'User accounts with email/password and OAuth authentication';
COMMENT ON TABLE tripflow.user_sessions IS 'Active user sessions with JWT tokens';
COMMENT ON TABLE tripflow.oauth_connections IS 'OAuth provider connections (Google, Microsoft, etc.)';
COMMENT ON TABLE tripflow.email_verification_tokens IS 'Tokens for email verification';
COMMENT ON TABLE tripflow.password_reset_tokens IS 'Tokens for password reset flow';
COMMENT ON TABLE tripflow.trip_creations IS 'Track trip planning usage for analytics';
COMMENT ON TABLE tripflow.api_usage IS 'Track API endpoint usage for rate limiting and analytics';

COMMENT ON COLUMN tripflow.users.google_id IS 'Unique identifier from Google OAuth';
COMMENT ON COLUMN tripflow.users.microsoft_id IS 'Unique identifier from Microsoft OAuth';
COMMENT ON COLUMN tripflow.users.subscription_tier IS 'free, basic, premium, enterprise';
COMMENT ON COLUMN tripflow.users.is_verified IS 'Email verification status';
COMMENT ON COLUMN tripflow.oauth_connections.provider_data IS 'Raw profile data from OAuth provider (JSONB)';
