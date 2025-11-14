-- Initialize Tripflow Database
-- This script runs first when creating the Docker container

-- Create tripflow user
CREATE USER tripflow WITH PASSWORD 'tripflow';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tripflow TO tripflow;
ALTER USER tripflow CREATEDB;

-- Connect to tripflow database
\c tripflow

-- Install extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Grant schema creation privilege
GRANT CREATE ON DATABASE tripflow TO tripflow;