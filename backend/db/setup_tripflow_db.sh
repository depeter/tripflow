#!/bin/bash

# Setup script for Tripflow database
# This script creates the Tripflow database and schema

set -e

# Configuration
DB_HOST="${TRIPFLOW_DB_HOST:-localhost}"
DB_PORT="${TRIPFLOW_DB_PORT:-5432}"
DB_NAME="${TRIPFLOW_DB_NAME:-tripflow}"
DB_USER="${TRIPFLOW_DB_USER:-tripflow}"
DB_PASSWORD="${TRIPFLOW_DB_PASSWORD:-tripflow}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo "=================================================="
echo "Tripflow Database Setup"
echo "=================================================="
echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Function to run psql commands
run_psql() {
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -c "$1"
}

# Function to run psql file
run_psql_file() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$1"
}

# Step 1: Create user if not exists
echo "Step 1: Creating user '$DB_USER'..."
run_psql "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
    run_psql "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Step 2: Create database if not exists
echo "Step 2: Creating database '$DB_NAME'..."
run_psql "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    run_psql "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Step 3: Grant privileges
echo "Step 3: Granting privileges..."
run_psql "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
run_psql "ALTER USER $DB_USER CREATEDB;"  # Allow user to create test databases

# Step 4: Install extensions
echo "Step 4: Installing PostgreSQL extensions..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS postgis;"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# Step 5: Run schema initialization
echo "Step 5: Creating Tripflow schema..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
run_psql_file "$SCRIPT_DIR/init_tripflow_schema.sql"

echo ""
echo "=================================================="
echo "Database setup completed successfully!"
echo "=================================================="
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "To verify the setup, run:"
echo "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c '\\dn'"
echo ""
echo "To run the ETL pipeline:"
echo "cd /home/peter/work/scraparr/etl"
echo "python tripflow_etl.py"
echo ""