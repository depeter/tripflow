#!/usr/bin/env python3
"""
Migration script to transfer data from Scraparr database to Tripflow database.
Migrates:
- Park4Night locations (scraper_2.places) -> tripflow.locations
- Park4Night reviews (scraper_2.reviews) -> tripflow.reviews
- UiT events (scraper_3.events) -> tripflow.events + tripflow.locations

Usage:
    # Test with limited data
    python migrate_scraparr_to_tripflow.py --limit 100

    # Full migration
    python migrate_scraparr_to_tripflow.py

    # Custom database connections
    python migrate_scraparr_to_tripflow.py --scraparr-host localhost --scraparr-port 5434
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import argparse
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)


class ScraparrToTripflowMigration:
    """Handles migration of data from Scraparr to Tripflow database."""

    def __init__(self, scraparr_config: dict, tripflow_config: dict):
        self.scraparr_config = scraparr_config
        self.tripflow_config = tripflow_config
        self.scraparr_conn = None
        self.tripflow_conn = None
        self.stats = {
            'locations_inserted': 0,
            'locations_updated': 0,
            'events_inserted': 0,
            'reviews_inserted': 0,
            'errors': 0
        }

    def connect_databases(self):
        """Establish connections to both databases."""
        try:
            logger.info(f"Connecting to Scraparr database at {self.scraparr_config['host']}:{self.scraparr_config['port']}...")
            self.scraparr_conn = psycopg2.connect(**self.scraparr_config)
            self.scraparr_conn.autocommit = False

            logger.info(f"Connecting to Tripflow database at {self.tripflow_config['host']}:{self.tripflow_config['port']}...")
            self.tripflow_conn = psycopg2.connect(**self.tripflow_config)
            self.tripflow_conn.autocommit = False

            logger.info("Database connections established successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False

    def close_connections(self):
        """Close database connections."""
        if self.scraparr_conn:
            self.scraparr_conn.close()
        if self.tripflow_conn:
            self.tripflow_conn.close()

    def map_park4night_type(self, type_de_lieu: str) -> str:
        """Map Park4Night location types to Tripflow types."""
        if not type_de_lieu:
            return 'PARKING'

        type_upper = type_de_lieu.upper()

        if 'PARKING' in type_upper:
            return 'PARKING'
        elif 'AIRE DE SERVICE' in type_upper:
            return 'SERVICE_AREA'
        elif 'AIRE DE PIQUE' in type_upper or 'AIRE DE REPOS' in type_upper:
            return 'REST_AREA'
        elif 'CAMPING' in type_upper:
            return 'CAMPSITE'
        elif 'FERME' in type_upper or 'FARM' in type_upper:
            return 'POI'
        elif 'VUE' in type_upper or 'LIEU INSOLITE' in type_upper:
            return 'ATTRACTION'
        elif 'ZONE NATURELLE' in type_upper or 'NATURE' in type_upper:
            return 'POI'
        else:
            return 'PARKING'

    def determine_price_type(self, tarif: str) -> str:
        """Determine price type from Park4Night tarif field."""
        if not tarif:
            return 'unknown'

        tarif_lower = str(tarif).lower()
        if 'gratuit' in tarif_lower or 'free' in tarif_lower or tarif == '0':
            return 'free'
        elif 'donation' in tarif_lower or 'don' in tarif_lower:
            return 'donation'
        elif any(char.isdigit() for char in tarif):
            return 'paid'
        else:
            return 'unknown'

    def extract_price_range(self, tarif: str) -> tuple:
        """Extract min and max price from tarif string."""
        if not tarif:
            return (None, None)

        # Find all numbers in the tarif string
        numbers = re.findall(r'\d+\.?\d*', str(tarif))
        if not numbers:
            return (None, None)

        # Convert to floats
        try:
            prices = [float(n) for n in numbers]
            if len(prices) == 1:
                return (prices[0], prices[0])
            elif len(prices) >= 2:
                return (min(prices), max(prices))
        except:
            return (None, None)

        return (None, None)

    def build_amenities_json(self, row: dict) -> list:
        """Build amenities JSON array from Park4Night fields."""
        amenities = []

        # Map boolean fields to amenities
        if row.get('internet'):
            amenities.append('wifi')
        if row.get('electricite'):
            amenities.append('electricity')
        if row.get('eau_noire'):
            amenities.append('waste_disposal')
        if row.get('camping_car_park'):
            amenities.append('motorhome_parking')
        if row.get('animaux_acceptes'):
            amenities.append('pets_allowed')

        # Parse etiquettes (tags) for additional amenities
        if row.get('etiquettes'):
            tags = str(row['etiquettes']).lower()
            if 'douche' in tags or 'shower' in tags:
                amenities.append('shower')
            if 'toilette' in tags or 'wc' in tags or 'toilet' in tags:
                amenities.append('toilet')
            if 'eau' in tags or 'water' in tags:
                amenities.append('water')
            if 'vidange' in tags:
                amenities.append('waste_disposal')

        return amenities

    def migrate_park4night_locations(self, batch_size: int = 1000, limit: Optional[int] = None):
        """Migrate Park4Night locations to Tripflow."""
        logger.info("Starting Park4Night location migration...")

        with self.scraparr_conn.cursor(cursor_factory=RealDictCursor) as scraparr_cur:
            with self.tripflow_conn.cursor() as tripflow_cur:

                # Count total records
                scraparr_cur.execute("SELECT COUNT(*) as total FROM scraper_1.places")
                total_count = scraparr_cur.fetchone()['total']

                if limit:
                    total_count = min(total_count, limit)

                logger.info(f"Found {total_count} Park4Night locations to migrate")

                # Process in batches
                offset = 0
                while offset < total_count:
                    current_batch_size = min(batch_size, total_count - offset)

                    scraparr_cur.execute("""
                        SELECT * FROM scraper_1.places
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """, (current_batch_size, offset))

                    places = scraparr_cur.fetchall()

                    for place in places:
                        try:
                            # Prepare data for insertion
                            location_type = self.map_park4night_type(place.get('type_de_lieu'))
                            price_type = self.determine_price_type(place.get('tarif'))
                            price_min, price_max = self.extract_price_range(place.get('tarif'))
                            amenities = self.build_amenities_json(place)

                            # Build features array
                            features = []
                            if place.get('stationnement'):
                                features.append(place['stationnement'])

                            # Handle photos
                            images = []
                            main_image = None
                            if place.get('photos'):
                                photo_urls = place['photos'].split(',') if isinstance(place['photos'], str) else []
                                images = [{'url': url.strip()} for url in photo_urls if url.strip()]
                                if images:
                                    main_image = images[0]['url']

                            # Parse tags
                            tags = []
                            if place.get('etiquettes'):
                                tags = [tag.strip() for tag in place['etiquettes'].split(',') if tag.strip()]

                            # Insert or update location (WITHOUT PostGIS geom)
                            tripflow_cur.execute("""
                                INSERT INTO tripflow.locations (
                                    external_id, source, source_url,
                                    name, description, location_type,
                                    latitude, longitude,
                                    city, country,
                                    rating, rating_count,
                                    price_type, price_min, price_max, price_info,
                                    amenities, features, tags,
                                    images, main_image_url,
                                    is_active, raw_data,
                                    created_at, updated_at
                                ) VALUES (
                                    %s, %s, %s,
                                    %s, %s, %s,
                                    %s, %s,
                                    %s, %s,
                                    %s, %s,
                                    %s, %s, %s, %s,
                                    %s, %s, %s,
                                    %s, %s,
                                    %s, %s,
                                    %s, %s
                                )
                                ON CONFLICT (external_id, source)
                                DO UPDATE SET
                                    name = EXCLUDED.name,
                                    description = EXCLUDED.description,
                                    rating = EXCLUDED.rating,
                                    amenities = EXCLUDED.amenities,
                                    features = EXCLUDED.features,
                                    updated_at = EXCLUDED.updated_at
                                RETURNING id
                            """, (
                                str(place['id']),  # external_id
                                'park4night',  # source
                                f"https://park4night.com/lieu/{place['id']}",  # source_url
                                place.get('nom', f"Location {place['id']}")[:500],  # name
                                place.get('description'),  # description
                                location_type,  # location_type
                                float(place['latitude']) if place.get('latitude') else None,  # latitude
                                float(place['longitude']) if place.get('longitude') else None,  # longitude
                                place.get('ville'),  # city
                                place.get('pays'),  # country
                                float(place['note']) if place.get('note') else None,  # rating
                                None,  # rating_count
                                price_type,  # price_type
                                price_min,  # price_min
                                price_max,  # price_max
                                place.get('tarif'),  # price_info
                                json.dumps(amenities),  # amenities
                                json.dumps(features),  # features
                                tags,  # tags
                                json.dumps(images),  # images
                                main_image,  # main_image_url
                                True,  # is_active
                                json.dumps(dict(place), default=str),  # raw_data
                                place.get('scraped_at', datetime.now()),  # created_at
                                place.get('updated_at', datetime.now())  # updated_at
                            ))

                            location_id = tripflow_cur.fetchone()[0]
                            self.stats['locations_inserted'] += 1

                        except Exception as e:
                            logger.error(f"Error migrating place {place.get('id')}: {e}")
                            self.stats['errors'] += 1
                            self.tripflow_conn.rollback()
                            continue

                    # Commit batch
                    self.tripflow_conn.commit()
                    offset += batch_size
                    logger.info(f"Processed {min(offset, total_count)}/{total_count} Park4Night locations")

    def migrate_uit_events(self, batch_size: int = 500, limit: Optional[int] = None):
        """Migrate UiT in Vlaanderen events to Tripflow."""
        logger.info("Starting UiT events migration...")

        with self.scraparr_conn.cursor(cursor_factory=RealDictCursor) as scraparr_cur:
            with self.tripflow_conn.cursor() as tripflow_cur:

                # Count total events
                scraparr_cur.execute("SELECT COUNT(*) as total FROM scraper_2.events")
                total_count = scraparr_cur.fetchone()['total']

                if limit:
                    total_count = min(total_count, limit)

                logger.info(f"Found {total_count} UiT events to migrate")

                # Process in batches
                offset = 0
                while offset < total_count:
                    current_batch_size = min(batch_size, total_count - offset)

                    scraparr_cur.execute("""
                        SELECT * FROM scraper_2.events
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """, (current_batch_size, offset))

                    events = scraparr_cur.fetchall()

                    for event in events:
                        try:
                            # First, create or update the location
                            location_name = event.get('location_name') or event.get('name')

                            if event.get('latitude') and event.get('longitude'):
                                # Insert location for the event (WITHOUT PostGIS geom)
                                tripflow_cur.execute("""
                                    INSERT INTO tripflow.locations (
                                        external_id, source, source_url,
                                        name, description, location_type,
                                        latitude, longitude,
                                        address, city, postal_code, country, country_code,
                                        is_active, raw_data,
                                        created_at, updated_at
                                    ) VALUES (
                                        %s, %s, %s,
                                        %s, %s, %s,
                                        %s, %s,
                                        %s, %s, %s, %s, %s,
                                        %s, %s,
                                        %s, %s
                                    )
                                    ON CONFLICT (external_id, source)
                                    DO UPDATE SET
                                        name = EXCLUDED.name,
                                        description = EXCLUDED.description,
                                        updated_at = EXCLUDED.updated_at
                                    RETURNING id
                                """, (
                                    f"uit_location_{event['event_id']}",  # external_id
                                    'uitinvlaanderen',  # source
                                    event.get('url'),  # source_url
                                    location_name[:500],  # name
                                    None,  # description
                                    'EVENT',  # location_type
                                    float(event['latitude']),  # latitude
                                    float(event['longitude']),  # longitude
                                    event.get('street_address'),  # address
                                    event.get('city'),  # city
                                    event.get('postal_code'),  # postal_code
                                    event.get('country', 'Belgium'),  # country
                                    'BE',  # country_code
                                    True,  # is_active
                                    json.dumps(dict(event), default=str),  # raw_data
                                    event.get('scraped_at', datetime.now()),  # created_at
                                    event.get('updated_at', datetime.now())  # updated_at
                                ))

                                location_id = tripflow_cur.fetchone()[0]

                                # Insert the event
                                tripflow_cur.execute("""
                                    INSERT INTO tripflow.events (
                                        location_id, external_id, source,
                                        name, description, event_type,
                                        start_date, end_date,
                                        organizer, themes,
                                        created_at, updated_at
                                    ) VALUES (
                                        %s, %s, %s,
                                        %s, %s, %s,
                                        %s, %s,
                                        %s, %s,
                                        %s, %s
                                    )
                                    ON CONFLICT (external_id, source)
                                    DO UPDATE SET
                                        name = EXCLUDED.name,
                                        description = EXCLUDED.description,
                                        start_date = EXCLUDED.start_date,
                                        end_date = EXCLUDED.end_date,
                                        updated_at = EXCLUDED.updated_at
                                """, (
                                    location_id,  # location_id
                                    event['event_id'],  # external_id
                                    'uitinvlaanderen',  # source
                                    event['name'][:500],  # name
                                    event.get('description'),  # description
                                    event.get('event_type'),  # event_type
                                    event.get('start_date'),  # start_date
                                    event.get('end_date'),  # end_date
                                    event.get('organizer'),  # organizer
                                    event.get('themes').split(',') if event.get('themes') else None,  # themes
                                    event.get('scraped_at', datetime.now()),  # created_at
                                    event.get('updated_at', datetime.now())  # updated_at
                                ))

                                self.stats['events_inserted'] += 1

                        except Exception as e:
                            logger.error(f"Error migrating event {event.get('event_id')}: {e}")
                            self.stats['errors'] += 1
                            self.tripflow_conn.rollback()
                            continue

                    # Commit batch
                    self.tripflow_conn.commit()
                    offset += batch_size
                    logger.info(f"Processed {min(offset, total_count)}/{total_count} events")

    def update_location_statistics(self):
        """Update rating counts and popularity scores for all locations."""
        logger.info("Updating location statistics...")

        with self.tripflow_conn.cursor() as cur:
            # Update review counts and ratings
            cur.execute("""
                UPDATE tripflow.locations l
                SET
                    review_count = r.count,
                    rating_count = r.count
                FROM (
                    SELECT location_id, COUNT(*) as count, AVG(rating) as avg_rating
                    FROM tripflow.reviews
                    GROUP BY location_id
                ) r
                WHERE l.id = r.location_id
            """)

            # Calculate and update popularity scores
            cur.execute("""
                UPDATE tripflow.locations
                SET popularity_score = tripflow.calculate_popularity_score(
                    rating, rating_count, review_count, is_verified
                )
                WHERE is_active = true
            """)

            self.tripflow_conn.commit()
            logger.info("Location statistics updated")

    def create_sync_log_entry(self, sync_type: str, source: Optional[str] = None):
        """Create a sync log entry for the migration."""
        with self.tripflow_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tripflow.sync_log (
                    sync_type, source, started_at, completed_at,
                    duration_seconds, records_processed, records_inserted,
                    records_updated, records_failed, status, sync_params
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                sync_type,
                source,
                self.start_time,
                datetime.now(),
                (datetime.now() - self.start_time).total_seconds(),
                self.stats['locations_inserted'] + self.stats['events_inserted'] + self.stats['reviews_inserted'],
                self.stats['locations_inserted'] + self.stats['events_inserted'] + self.stats['reviews_inserted'],
                self.stats['locations_updated'],
                self.stats['errors'],
                'completed' if self.stats['errors'] == 0 else 'completed_with_errors',
                json.dumps(self.stats)
            ))

            self.tripflow_conn.commit()

    def run_migration(self, limit: Optional[int] = None):
        """Execute the complete migration process."""
        self.start_time = datetime.now()

        try:
            # Connect to databases
            if not self.connect_databases():
                return False

            # Run migrations
            self.migrate_park4night_locations(limit=limit)
            self.migrate_uit_events(limit=limit)

            # Update statistics
            self.update_location_statistics()

            # Log sync (using 'other' for source since scraparr is not in the enum)
            self.create_sync_log_entry('full', 'other')

            # Print summary
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info("=" * 60)
            logger.info("Migration completed successfully!")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Locations inserted: {self.stats['locations_inserted']}")
            logger.info(f"Events inserted: {self.stats['events_inserted']}")
            logger.info(f"Reviews inserted: {self.stats['reviews_inserted']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if self.tripflow_conn:
                self.tripflow_conn.rollback()
            return False

        finally:
            self.close_connections()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Migrate data from Scraparr to Tripflow database')

    # Scraparr database options
    parser.add_argument('--scraparr-host', default='localhost', help='Scraparr database host')
    parser.add_argument('--scraparr-port', type=int, default=5434, help='Scraparr database port')
    parser.add_argument('--scraparr-db', default='scraparr', help='Scraparr database name')
    parser.add_argument('--scraparr-user', default='scraparr', help='Scraparr database user')
    parser.add_argument('--scraparr-pass', default='scraparr', help='Scraparr database password')

    # Tripflow database options
    parser.add_argument('--tripflow-host', default='localhost', help='Tripflow database host')
    parser.add_argument('--tripflow-port', type=int, default=5432, help='Tripflow database port')
    parser.add_argument('--tripflow-db', default='tripflow', help='Tripflow database name')
    parser.add_argument('--tripflow-user', default='tripflow', help='Tripflow database user')
    parser.add_argument('--tripflow-pass', default='tripflow', help='Tripflow database password')

    # Migration options
    parser.add_argument('--limit', type=int, help='Limit number of records to migrate (for testing)')

    args = parser.parse_args()

    # Database connection configurations
    scraparr_config = {
        'host': args.scraparr_host,
        'port': args.scraparr_port,
        'database': args.scraparr_db,
        'user': args.scraparr_user,
        'password': args.scraparr_pass
    }

    tripflow_config = {
        'host': args.tripflow_host,
        'port': args.tripflow_port,
        'database': args.tripflow_db,
        'user': args.tripflow_user,
        'password': args.tripflow_pass
    }

    logger.info("Starting Scraparr to Tripflow data migration")
    logger.info("=" * 60)
    if args.limit:
        logger.info(f"LIMIT MODE: Migrating only {args.limit} records for testing")

    migration = ScraparrToTripflowMigration(scraparr_config, tripflow_config)
    success = migration.run_migration(limit=args.limit)

    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()