-- Create the Tripflow database and user if they don't exist
-- Run this script as the postgres superuser

-- Create database
CREATE DATABASE tripflow WITH OWNER = postgres;

-- Connect to tripflow database
\c tripflow;

-- Create user if not exists
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE usename = 'tripflow') THEN

      CREATE USER tripflow WITH PASSWORD 'tripflow';
   END IF;
END
$$;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE tripflow TO tripflow;
GRANT USAGE ON SCHEMA public TO tripflow;
GRANT CREATE ON SCHEMA public TO tripflow;