# Tripflow Database Migration Guide

## Overview

This guide documents the process of migrating location and event data from the Scraparr database to the Tripflow database. Both databases will be hosted on the scraparr server.

## Architecture

```
Scraparr Server (192.168.1.149)
├── Scraparr Database (Port 5434)
│   ├── scraper_2.places (Park4Night camping/parking locations)
│   ├── scraper_2.reviews (Park4Night reviews)
│   └── scraper_3.events (UiT in Vlaanderen events)
│
└── Tripflow Database (Port 5432)
    ├── tripflow.locations (Consolidated locations)
    ├── tripflow.events (Time-based events)
    ├── tripflow.reviews (User reviews)
    └── tripflow.sync_log (Migration history)
```

## Migration Files

### Core Scripts

1. **`init_tripflow_schema.sql`** - Creates the Tripflow database schema
   - PostGIS extensions for spatial data
   - Tables: locations, events, reviews, sync_log, data_quality_metrics
   - Indexes, functions, triggers, and views

2. **`migrate_scraparr_to_tripflow.py`** - Main migration script
   - Migrates Park4Night locations and reviews
   - Migrates UiT in Vlaanderen events
   - Handles data transformation and mapping
   - Supports batch processing and error recovery

3. **`deploy_to_scraparr.sh`** - Deployment automation script
   - Copies migration files to scraparr server
   - Creates Tripflow database
   - Runs schema initialization
   - Executes data migration

### Supporting Files

4. **`park4night_importer.py`** - Park4Night data importer for sync framework
   - Maps scraparr schema to Tripflow schema
   - Handles amenities, pricing, and location types

## Quick Start

### Deploy to Scraparr Server

```bash
# From your local machine (with this repository)
cd /home/peter/work/tripflow/migrations

# Run deployment (test mode - 100 records)
./deploy_to_scraparr.sh --test

# Run full deployment (all data)
./deploy_to_scraparr.sh
```

## Manual Migration Steps

### 1. Connect to Scraparr Server

```bash
ssh peter@scraparr
# Password: nomansland
```

### 2. Create Tripflow Database

```bash
# Check if database exists
docker exec scraparr-postgres psql -U postgres -c "\l" | grep tripflow

# Create database if not exists
docker exec scraparr-postgres psql -U postgres -c "CREATE DATABASE tripflow WITH OWNER = postgres;"
```

### 3. Initialize Schema

```bash
# Run schema creation script
docker exec -i scraparr-postgres psql -U postgres -d tripflow < /home/peter/tripflow/migrations/init_tripflow_schema.sql
```

### 4. Run Migration

```bash
# Navigate to migrations directory
cd /home/peter/tripflow/migrations

# Test with limited data (100 records)
python3 migrate_scraparr_to_tripflow.py \
  --scraparr-host localhost \
  --scraparr-port 5434 \
  --tripflow-host localhost \
  --tripflow-port 5432 \
  --limit 100

# Run full migration
python3 migrate_scraparr_to_tripflow.py \
  --scraparr-host localhost \
  --scraparr-port 5434 \
  --tripflow-host localhost \
  --tripflow-port 5432
```

### 5. Verify Migration

```bash
# Check record counts
docker exec scraparr-postgres psql -U postgres -d tripflow -c "
SELECT
    'locations' as table_name,
    COUNT(*) as count,
    COUNT(DISTINCT source) as sources
FROM tripflow.locations
UNION ALL
SELECT 'events', COUNT(*), COUNT(DISTINCT source)
FROM tripflow.events
UNION ALL
SELECT 'reviews', COUNT(*), COUNT(DISTINCT source)
FROM tripflow.reviews;
"

# Check sync log
docker exec scraparr-postgres psql -U postgres -d tripflow -c "
SELECT sync_type, source, status, records_processed, records_failed, duration_seconds
FROM tripflow.sync_log
ORDER BY started_at DESC
LIMIT 5;
"
```

## Data Mapping

### Park4Night → Tripflow Locations

| Park4Night Field | Tripflow Field | Transformation |
|-----------------|----------------|----------------|
| `id` | `external_id` | Prefixed with "park4night_" |
| `nom` | `name` | Direct mapping |
| `type_de_lieu` | `location_type` | Mapped to enum (PARKING, CAMPSITE, etc.) |
| `latitude`, `longitude` | `latitude`, `longitude`, `geom` | PostGIS point geometry |
| `pays` | `country` | Direct mapping |
| `ville` | `city` | Direct mapping |
| `note` | `rating` | Float conversion |
| `tarif` | `price_type`, `price_min`, `price_max` | Parsed for pricing info |
| `photos` | `images`, `main_image_url` | JSON array of image URLs |
| `etiquettes` | `tags` | Split comma-separated tags |
| `internet`, `electricite`, etc. | `amenities` | Boolean fields to JSON array |

### UiT Events → Tripflow Events + Locations

| UiT Field | Tripflow Field | Notes |
|-----------|----------------|-------|
| `event_id` | `external_id` | Unique event identifier |
| `name` | `name` | Event name |
| `description` | `description` | Event description |
| `start_date`, `end_date` | `start_date`, `end_date` | Datetime fields |
| `location_name` | Creates location record | Event venue |
| `latitude`, `longitude` | Location coordinates | For event venue |
| `city`, `postal_code` | Location address | Belgium only |
| `organizer` | `organizer` | Event organizer |
| `themes` | `themes` | Array of theme strings |

## Using the Sync Framework

The Tripflow backend includes a sync framework for regular data updates:

```bash
# On scraparr server, after deployment
cd /home/peter/tripflow/backend

# Test connection to scraparr database
python app/sync/sync_cli.py test-connection --source park4night

# Run sync (uses park4night_importer.py)
python app/sync/sync_cli.py sync --source park4night --limit 100

# Run all sources
python app/sync/sync_cli.py sync --all
```

### Environment Variables

Add to `/home/peter/tripflow/backend/.env`:

```env
# Source databases for sync
SOURCE_DB_PARK4NIGHT=postgresql://scraparr:scraparr@localhost:5434/scraparr
SOURCE_DB_CAMPERCONTACT=
SOURCE_DB_LOCAL_SITES=

# Enable sync
SYNC_ENABLED=True
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Error: connection to server at "localhost", port 5434 failed
   ```
   Solution: Ensure scraparr-postgres container is running on port 5434

2. **Permission Denied**
   ```
   Error: must be owner of table locations
   ```
   Solution: Run schema creation as postgres user, not tripflow user

3. **Type Already Exists**
   ```
   ERROR: type "location_type" already exists
   ```
   Solution: Schema already exists, safe to ignore

4. **Module Not Found**
   ```
   ModuleNotFoundError: No module named 'psycopg2'
   ```
   Solution: Install dependencies:
   ```bash
   pip3 install psycopg2-binary
   ```

### Checking Container Status

```bash
# On scraparr server
docker ps | grep postgres

# Expected output:
# scraparr-postgres on port 5434
# tripflow-postgres on port 5432 (if running separately)
```

### Database Access

```bash
# Access Scraparr database
docker exec -it scraparr-postgres psql -U scraparr -d scraparr

# Access Tripflow database
docker exec -it scraparr-postgres psql -U postgres -d tripflow

# List schemas in scraparr
\dn

# List tables in scraper_2 schema
\dt scraper_2.*
```

## Migration Statistics

Expected data volumes (as of Nov 2024):

- **Park4Night Locations**: ~100,000+ camping/parking spots across Europe
- **UiT Events**: ~10,000 cultural events in Belgium
- **Reviews**: Varies based on location popularity

Migration performance:

- **Batch Size**: 1000 records per batch (configurable)
- **Processing Time**: ~10-30 minutes for full migration
- **Memory Usage**: <500MB
- **Disk Space**: ~1-2GB for Tripflow database

## Data Quality

The migration script includes:

- **Deduplication**: Uses `ON CONFLICT` to prevent duplicates
- **Data Validation**: Type checking and null handling
- **Error Recovery**: Continues on individual record failures
- **Logging**: Detailed migration logs in `migration.log`
- **Statistics**: Tracks insertions, updates, and errors

## Next Steps

After successful migration:

1. **Test Tripflow API**: Verify data is accessible via FastAPI endpoints
2. **Update Qdrant**: Index locations for vector search
3. **Schedule Regular Syncs**: Set up cron job for incremental updates
4. **Monitor Data Quality**: Check `data_quality_metrics` table

## Support

For issues or questions:

1. Check migration logs: `tail -f migration.log`
2. Review sync logs in database: `SELECT * FROM tripflow.sync_log`
3. Check container logs: `docker logs scraparr-postgres`

## License

Part of the Tripflow project - Internal use only