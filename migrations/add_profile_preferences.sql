-- Add profile_preferences JSONB column to users table
-- This stores user interests, travel style, vehicle info, etc.

ALTER TABLE tripflow.users
ADD COLUMN IF NOT EXISTS profile_preferences JSONB DEFAULT '{}';

-- Add comment for documentation
COMMENT ON COLUMN tripflow.users.profile_preferences IS 'Stores user preferences as JSON: interests, travelStyle, vehicle, homeBase';
