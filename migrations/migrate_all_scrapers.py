#!/usr/bin/env python3
"""
Universal Migration Script for All Scraparr Scrapers to Tripflow

This script automatically migrates data from all active scrapers in scraparr
to the tripflow database using the mapping definitions in scraper_mappings.py

Usage:
    # Migrate all scrapers
    python migrate_all_scrapers.py

    # Migrate specific scraper
    python migrate_all_scrapers.py --scraper-id 3

    # Test migration with limit
    python migrate_all_scrapers.py --limit 100

    # Migrate only new scrapers not yet in tripflow
    python migrate_all_scrapers.py --new-only
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import argparse
from scraper_mappings import (
    SCRAPER_REGISTRY,
    DataType,
    get_scraper_mapping,
    EventbriteMapping,
    Park4NightMapping,
    UiTinVlaanderenMapping
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration_all.log')
    ]
)
logger = logging.getLogger(__name__)


class UniversalScraperMigration:
    """Universal migration handler for all scrapers"""

    def __init__(self, scraparr_config: dict, tripflow_config: dict):
        self.scraparr_config = scraparr_config
        self.tripflow_config = tripflow_config
        self.scraparr_conn = None
        self.tripflow_conn = None
        self.stats = {}

    def connect_databases(self):
        """Establish connections to both databases"""
        try:
            logger.info(f"Connecting to Scraparr database...")
            self.scraparr_conn = psycopg2.connect(**self.scraparr_config)
            self.scraparr_conn.autocommit = False

            logger.info(f"Connecting to Tripflow database...")
            self.tripflow_conn = psycopg2.connect(**self.tripflow_config)
            self.tripflow_conn.autocommit = False

            logger.info("Database connections established successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False

    def close_connections(self):
        """Close database connections"""
        if self.scraparr_conn:
            self.scraparr_conn.close()
        if self.tripflow_conn:
            self.tripflow_conn.close()

    def get_active_scrapers(self, scraper_id: Optional[int] = None) -> List[Dict]:
        """Get list of active scrapers from scraparr database"""
        with self.scraparr_conn.cursor(cursor_factory=RealDictCursor) as cur:
            if scraper_id:
                cur.execute("""
                    SELECT id, name, schema_name, module_path, class_name
                    FROM scrapers
                    WHERE id = %s AND is_active = true
                """, (scraper_id,))
            else:
                cur.execute("""
                    SELECT id, name, schema_name, module_path, class_name
                    FROM scrapers
                    WHERE is_active = true
                    ORDER BY id
                """)
            return cur.fetchall()

    def check_already_migrated(self, scraper_id: int) -> bool:
        """Check if scraper data already exists in tripflow"""
        mapping = get_scraper_mapping(scraper_id=scraper_id)
        if not mapping:
            return False

        with self.tripflow_conn.cursor() as cur:
            # Check for existing data from this source
            if mapping.source_name:
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM tripflow.locations
                    WHERE source = %s
                """, (mapping.source_name,))
                result = cur.fetchone()
                if result[0] > 0:
                    return True

        return False

    def migrate_scraper(self, scraper_info: Dict, limit: Optional[int] = None, batch_size: int = 1000):
        """Migrate data from a single scraper"""
        scraper_id = scraper_info['id']
        scraper_name = scraper_info['name']
        schema_name = scraper_info['schema_name']

        logger.info(f"Starting migration for {scraper_name} (ID: {scraper_id}, Schema: {schema_name})")

        # Get mapping for this scraper
        mapping = get_scraper_mapping(scraper_id=scraper_id)
        if not mapping:
            logger.warning(f"No mapping found for scraper {scraper_name} (ID: {scraper_id})")
            logger.warning(f"Please add mapping to scraper_mappings.py")
            return {
                'scraper_id': scraper_id,
                'scraper_name': scraper_name,
                'status': 'skipped',
                'reason': 'no_mapping'
            }

        # Initialize stats for this scraper
        stats = {
            'scraper_id': scraper_id,
            'scraper_name': scraper_name,
            'locations_inserted': 0,
            'events_inserted': 0,
            'reviews_inserted': 0,
            'errors': 0
        }

        try:
            # Get data from scraper
            query = mapping.get_query()
            if limit:
                query += f" LIMIT {limit}"

            with self.scraparr_conn.cursor(cursor_factory=RealDictCursor) as scraparr_cur:
                with self.tripflow_conn.cursor() as tripflow_cur:

                    scraparr_cur.execute(query)
                    total_rows = scraparr_cur.rowcount
                    logger.info(f"Found {total_rows} records to migrate from {scraper_name}")

                    rows = scraparr_cur.fetchall()
                    for row in rows:
                        # Use savepoint so errors don't abort entire transaction
                        tripflow_cur.execute("SAVEPOINT row_savepoint")
                        try:
                            # Handle based on data type
                            if mapping.data_type == DataType.LOCATION:
                                # Just locations (like Park4Night)
                                location_data = mapping.map_to_location(row)
                                self._insert_location(tripflow_cur, location_data)
                                stats['locations_inserted'] += 1

                            elif mapping.data_type == DataType.EVENT:
                                # Just events (rare, usually events need locations)
                                event_data = mapping.map_to_event(row)
                                # You'd need a location_id here
                                logger.warning("Pure EVENT type not fully implemented")

                            elif mapping.data_type == DataType.COMBINED:
                                # Both location and event (like UiT, Eventbrite)
                                location_data = mapping.map_to_location(row)
                                location_id = self._insert_location(tripflow_cur, location_data)

                                if location_id:
                                    event_data = mapping.map_to_event(row)
                                    event_data['location_id'] = location_id
                                    self._insert_event(tripflow_cur, event_data)
                                    stats['events_inserted'] += 1
                                    stats['locations_inserted'] += 1

                            # Release savepoint on success
                            tripflow_cur.execute("RELEASE SAVEPOINT row_savepoint")

                        except Exception as e:
                            logger.error(f"Error processing row {row.get('id')}: {e}")
                            stats['errors'] += 1
                            # Rollback to savepoint (not entire transaction)
                            tripflow_cur.execute("ROLLBACK TO SAVEPOINT row_savepoint")
                            continue

                    # Commit the batch
                    self.tripflow_conn.commit()
                    logger.info(f"Migration completed for {scraper_name}: {stats}")

        except Exception as e:
            logger.error(f"Failed to migrate {scraper_name}: {e}")
            stats['status'] = 'failed'
            stats['error'] = str(e)
            if self.tripflow_conn:
                self.tripflow_conn.rollback()

        return stats

    def _insert_location(self, cursor, data: Dict) -> Optional[int]:
        """Insert or update a location in tripflow"""
        try:
            cursor.execute("""
                INSERT INTO tripflow.locations (
                    external_id, source, source_url,
                    name, description, location_type,
                    latitude, longitude,
                    address, city, postal_code, country, country_code,
                    rating, price_type, price_min, price_max, price_info,
                    amenities, features, tags,
                    images, main_image_url,
                    is_active, raw_data,
                    created_at, updated_at
                ) VALUES (
                    %(external_id)s, %(source)s, %(source_url)s,
                    %(name)s, %(description)s, %(location_type)s,
                    %(latitude)s, %(longitude)s,
                    %(address)s, %(city)s, %(postal_code)s, %(country)s, %(country_code)s,
                    %(rating)s, %(price_type)s, %(price_min)s, %(price_max)s, %(price_info)s,
                    %(amenities)s, %(features)s, %(tags)s,
                    %(images)s, %(main_image_url)s,
                    %(is_active)s, %(raw_data)s,
                    NOW(), NOW()
                )
                ON CONFLICT (external_id, source)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    updated_at = NOW()
                RETURNING id
            """, {
                'external_id': data.get('external_id'),
                'source': data.get('source'),
                'source_url': data.get('source_url'),
                'name': data.get('name'),
                'description': data.get('description'),
                'location_type': data.get('location_type'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'address': data.get('address'),
                'city': data.get('city'),
                'postal_code': data.get('postal_code'),
                'country': data.get('country'),
                'country_code': data.get('country_code'),
                'rating': data.get('rating'),
                'price_type': data.get('price_type'),
                'price_min': data.get('price_min'),
                'price_max': data.get('price_max'),
                'price_info': data.get('price_info'),
                'amenities': json.dumps(data.get('amenities', [])),
                'features': json.dumps(data.get('features', [])),
                'tags': data.get('tags', []),
                'images': json.dumps(data.get('images', [])),
                'main_image_url': data.get('main_image_url'),
                'is_active': data.get('is_active', True),
                'raw_data': json.dumps(data.get('raw_data', {}))
            })

            result = cursor.fetchone()
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error inserting location: {e}")
            raise

    def _insert_event(self, cursor, data: Dict):
        """Insert or update an event in tripflow"""
        try:
            cursor.execute("""
                INSERT INTO tripflow.events (
                    location_id, external_id, source,
                    name, description, category,
                    start_datetime, end_datetime,
                    organizer, themes,
                    booking_url,
                    price,
                    cancelled,
                    created_at, updated_at
                ) VALUES (
                    %(location_id)s, %(external_id)s, %(source)s,
                    %(name)s, %(description)s, %(category)s,
                    %(start_datetime)s, %(end_datetime)s,
                    %(organizer)s, %(themes)s,
                    %(booking_url)s,
                    %(price)s,
                    %(cancelled)s,
                    NOW(), NOW()
                )
                ON CONFLICT (external_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    start_datetime = EXCLUDED.start_datetime,
                    end_datetime = EXCLUDED.end_datetime,
                    updated_at = NOW()
            """, {
                'location_id': data.get('location_id'),
                'external_id': data.get('external_id'),
                'source': data.get('source'),
                'name': data.get('name'),
                'description': data.get('description'),
                'category': data.get('event_type', 'Other'),
                'start_datetime': data.get('start_date'),
                'end_datetime': data.get('end_date'),
                'organizer': data.get('organizer'),
                'themes': data.get('themes', []),
                'booking_url': data.get('booking_url'),
                'price': data.get('price_min'),
                'cancelled': data.get('is_cancelled', False)
            })

        except Exception as e:
            logger.error(f"Error inserting event: {e}")
            raise

    def run_migration(self, scraper_id: Optional[int] = None, new_only: bool = False, limit: Optional[int] = None):
        """Execute the migration process"""
        self.start_time = datetime.now()

        try:
            if not self.connect_databases():
                return False

            # Get scrapers to migrate
            scrapers = self.get_active_scrapers(scraper_id)
            logger.info(f"Found {len(scrapers)} active scraper(s)")

            all_stats = []
            for scraper in scrapers:
                # Check if already migrated (if new_only flag is set)
                if new_only and self.check_already_migrated(scraper['id']):
                    logger.info(f"Skipping {scraper['name']} - already migrated")
                    all_stats.append({
                        'scraper_id': scraper['id'],
                        'scraper_name': scraper['name'],
                        'status': 'skipped',
                        'reason': 'already_migrated'
                    })
                    continue

                # Migrate this scraper
                stats = self.migrate_scraper(scraper, limit=limit)
                all_stats.append(stats)

            # Print summary
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info("=" * 60)
            logger.info("Migration Summary")
            logger.info("=" * 60)

            for stat in all_stats:
                logger.info(f"{stat['scraper_name']}:")
                if stat.get('status') == 'skipped':
                    logger.info(f"  Status: Skipped ({stat.get('reason', 'unknown')})")
                else:
                    logger.info(f"  Locations: {stat.get('locations_inserted', 0)}")
                    logger.info(f"  Events: {stat.get('events_inserted', 0)}")
                    logger.info(f"  Errors: {stat.get('errors', 0)}")

            logger.info(f"Total duration: {duration:.2f} seconds")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

        finally:
            self.close_connections()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Migrate all scrapers from Scraparr to Tripflow')

    # Database options
    parser.add_argument('--scraparr-host', default='localhost', help='Scraparr database host')
    parser.add_argument('--scraparr-port', type=int, default=5434, help='Scraparr database port')
    parser.add_argument('--tripflow-host', default='localhost', help='Tripflow database host')
    parser.add_argument('--tripflow-port', type=int, default=5435, help='Tripflow database port')

    # Migration options
    parser.add_argument('--scraper-id', type=int, help='Migrate specific scraper only')
    parser.add_argument('--new-only', action='store_true', help='Only migrate scrapers not yet in tripflow')
    parser.add_argument('--limit', type=int, help='Limit records per scraper (for testing)')

    args = parser.parse_args()

    # Database configurations
    scraparr_config = {
        'host': args.scraparr_host,
        'port': args.scraparr_port,
        'database': 'scraparr',
        'user': 'scraparr',
        'password': 'scraparr'
    }

    tripflow_config = {
        'host': args.tripflow_host,
        'port': args.tripflow_port,
        'database': 'tripflow',
        'user': 'postgres',
        'password': 'tripflow'
    }

    logger.info("Starting Universal Scraper Migration")
    logger.info("=" * 60)

    migration = UniversalScraperMigration(scraparr_config, tripflow_config)
    success = migration.run_migration(
        scraper_id=args.scraper_id,
        new_only=args.new_only,
        limit=args.limit
    )

    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()