#!/bin/bash
#
# Deploy Tripflow database and migrate data from Scraparr
# This script is designed to run on the scraparr server
#
# Usage: ./deploy_to_scraparr.sh [--test]
#

set -e

# Configuration
SCRAPARR_HOST="scraparr"
SCRAPARR_USER="peter"
SCRAPARR_PASS="nomansland"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
TEST_MODE=false
if [ "$1" == "--test" ]; then
    TEST_MODE=true
    echo -e "${YELLOW}Running in TEST mode - will only migrate 100 records${NC}"
fi

echo -e "${GREEN}=== Tripflow Database Deployment to Scraparr Server ===${NC}"
echo "This script will:"
echo "1. Create the Tripflow database on scraparr server"
echo "2. Initialize the Tripflow schema"
echo "3. Migrate Park4Night data from scraparr database"
echo "4. Migrate UiT events from scraparr database"
echo ""

# Function to run commands on scraparr server
run_on_scraparr() {
    local cmd="$1"
    SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force ssh ${SCRAPARR_USER}@${SCRAPARR_HOST} "$cmd"
}

# Function to copy files to scraparr server
copy_to_scraparr() {
    local src="$1"
    local dest="$2"
    SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force scp "$src" ${SCRAPARR_USER}@${SCRAPARR_HOST}:"$dest"
}

# Create SSH password helper
cat > /tmp/scraparr_pass.sh << 'EOF'
#!/bin/sh
echo "nomansland"
EOF
chmod +x /tmp/scraparr_pass.sh

echo -e "${YELLOW}Step 1: Copy migration files to scraparr server${NC}"
echo "Creating tripflow directory on scraparr..."
run_on_scraparr "mkdir -p /home/peter/tripflow/migrations"

echo "Copying migration files..."
copy_to_scraparr "/home/peter/work/tripflow/backend/db/init_tripflow_schema.sql" "/home/peter/tripflow/migrations/"
copy_to_scraparr "/home/peter/work/tripflow/migrations/02_migrate_scraparr_data.py" "/home/peter/tripflow/migrations/"

echo -e "${YELLOW}Step 2: Create Tripflow database${NC}"
run_on_scraparr "docker exec scraparr-postgres psql -U postgres -c \"SELECT 1 FROM pg_database WHERE datname = 'tripflow';\" | grep -q '1 row' || docker exec scraparr-postgres psql -U postgres -c \"CREATE DATABASE tripflow WITH OWNER = postgres;\""

echo -e "${YELLOW}Step 3: Initialize Tripflow schema${NC}"
run_on_scraparr "docker exec -i scraparr-postgres psql -U postgres -d tripflow < /home/peter/tripflow/migrations/init_tripflow_schema.sql"

echo -e "${YELLOW}Step 4: Run data migration${NC}"
if [ "$TEST_MODE" = true ]; then
    echo "Running migration in TEST mode (limit 100 records)..."
    run_on_scraparr "cd /home/peter/tripflow/migrations && python3 02_migrate_scraparr_data.py --limit 100"
else
    echo "Running FULL migration (this may take several minutes)..."
    run_on_scraparr "cd /home/peter/tripflow/migrations && python3 02_migrate_scraparr_data.py"
fi

echo -e "${YELLOW}Step 5: Verify migration${NC}"
run_on_scraparr "docker exec scraparr-postgres psql -U postgres -d tripflow -c \"
SELECT
    'locations' as table_name,
    COUNT(*) as count,
    COUNT(DISTINCT source) as sources
FROM tripflow.locations
UNION ALL
SELECT
    'events',
    COUNT(*),
    COUNT(DISTINCT source)
FROM tripflow.events
UNION ALL
SELECT
    'reviews',
    COUNT(*),
    COUNT(DISTINCT source)
FROM tripflow.reviews;
\""

# Cleanup
rm /tmp/scraparr_pass.sh

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo "You can now access the Tripflow database on scraparr:5432"
echo "Connection string: postgresql://tripflow:tripflow@scraparr:5432/tripflow"