#!/usr/bin/env python3
"""
Migrate event data from Scraparr database to Tripflow.

Source: scraparr-postgres:5434 (scraper_2.events, scraper_3.events)
Target: tripflow-postgres:5433 (tripflow.events)

Usage:
    cd /home/peter/work/tripflow/backend
    source venv/bin/activate
    python scripts/migrate_scraparr_events.py
"""

import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from dateutil import parser as date_parser
import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connections (adjust if running from scraparr server)
SOURCE_DB = "postgresql://scraparr:scraparr@localhost:5434/scraparr"
TARGET_DB = "postgresql://tripflow:tripflow@localhost:5433/tripflow"


def parse_date(date_str):
    """Parse various date formats to Python date object."""
    if not date_str or not isinstance(date_str, str) or date_str.strip() == '':
        return None

    try:
        # Try parsing various formats
        parsed = date_parser.parse(date_str, fuzzy=True)
        return parsed.date()
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def parse_datetime(date_str, default_time="12:00:00"):
    """Parse date string to datetime. If no time, use default."""
    if not date_str or not isinstance(date_str, str) or date_str.strip() == '':
        return None

    try:
        parsed = date_parser.parse(date_str, fuzzy=True, default=datetime.strptime(default_time, "%H:%M:%S"))
        return parsed
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{date_str}': {e}")
        return None


def normalize_themes(themes_str):
    """Convert comma-separated themes to PostgreSQL array literal."""
    if not themes_str or not isinstance(themes_str, str):
        return []

    # Split by comma and clean
    themes = [t.strip() for t in themes_str.split(',') if t.strip()]
    return themes[:10]  # Limit to 10 themes max


def map_event_category(event_type, themes):
    """
    Map source event_type and themes to our EventCategory enum.

    EventCategory options:
    - festival, concert, sports, market, exhibition, theater, cultural, food, outdoor, other
    """
    if not event_type:
        event_type = ""

    event_type_lower = event_type.lower()
    themes_lower = [t.lower() for t in (themes or [])]

    # Direct mappings
    if 'festival' in event_type_lower or 'festival' in themes_lower:
        return 'festival'
    if 'concert' in event_type_lower or 'muziek' in themes_lower or 'music' in themes_lower:
        return 'concert'
    if 'sport' in event_type_lower or 'sport' in themes_lower:
        return 'sports'
    if 'markt' in event_type_lower or 'market' in event_type_lower:
        return 'market'
    if 'tentoonstelling' in event_type_lower or 'exhibition' in event_type_lower or 'expo' in event_type_lower:
        return 'exhibition'
    if 'theater' in event_type_lower or 'theatre' in event_type_lower or 'voorstelling' in event_type_lower:
        return 'theater'
    if 'eten' in themes_lower or 'food' in themes_lower or 'culinair' in themes_lower:
        return 'food'
    if 'outdoor' in themes_lower or 'buiten' in themes_lower or 'natuur' in themes_lower:
        return 'outdoor'
    if 'cultuur' in themes_lower or 'cultural' in event_type_lower:
        return 'cultural'

    return 'other'


def migrate_scraper_2():
    """Migrate scraper_2.events (UiT in Vlaanderen - ~12,292 events)."""
    logger.info("=" * 80)
    logger.info("Migrating scraper_2.events (UiT in Vlaanderen)")
    logger.info("=" * 80)

    source_conn = psycopg2.connect(SOURCE_DB)
    target_conn = psycopg2.connect(TARGET_DB)

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    # Fetch all events
    logger.info("Fetching events from scraper_2.events...")
    source_cur.execute("""
        SELECT
            event_id, name, description, start_date, end_date,
            location_name, street_address, city, postal_code, country,
            latitude, longitude, organizer, event_type, themes,
            url, image_url, scraped_at, updated_at
        FROM scraper_2.events
        ORDER BY id
    """)

    events = source_cur.fetchall()
    logger.info(f"Found {len(events)} events in scraper_2.events")

    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    batch = []
    batch_size = 100

    for idx, event in enumerate(events, 1):
        (external_id, name, description, start_date_str, end_date_str,
         location_name, street_address, city, postal_code, country,
         lat, lng, organizer, event_type, themes_str,
         url, image_url, scraped_at, updated_at) = event

        # Parse dates
        start_datetime = parse_datetime(start_date_str)
        end_datetime = parse_datetime(end_date_str)

        # Skip if no start date or invalid coordinates
        if not start_datetime:
            skipped += 1
            if idx % 1000 == 0:
                logger.warning(f"Skipping event {external_id}: no valid start date")
            continue

        if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            skipped += 1
            if idx % 1000 == 0:
                logger.warning(f"Skipping event {external_id}: invalid coordinates ({lat}, {lng})")
            continue

        # Normalize themes
        themes = normalize_themes(themes_str)

        # Map to category
        category = map_event_category(event_type, themes)

        # Construct address
        address_parts = [p for p in [street_address, postal_code] if p]
        address = ', '.join(address_parts) if address_parts else None

        # Build images array
        images = [image_url] if image_url else []

        # Prepare row for batch insert
        row = (
            # Basic info
            name, description, category,
            # Dates
            start_datetime, end_datetime, False,  # all_day=False
            # Location
            location_name, address, city, None, country,  # region=None
            lat, lng, lng, lat,  # lat, lng, then lng/lat again for ST_MakePoint
            # Location link
            None,  # location_id
            # Details
            None, 'EUR', True,  # price=None, currency='EUR', free=True (assume free if no price)
            # Contact
            url, None, None, None,  # website, booking_url, contact_email, contact_phone
            # Media
            images,
            # Tags
            themes,  # Use themes as tags too
            # Discovery fields
            organizer, event_type, themes, 'uitinvlaanderen',
            # Status
            True, False,  # active=True, cancelled=False
            # Scraping
            scraped_at or datetime.now(),
            # External ref
            external_id, url
        )

        batch.append(row)

        # Execute batch when full
        if len(batch) >= batch_size:
            try:
                execute_batch(target_cur, """
                    INSERT INTO tripflow.events (
                        name, description, category,
                        start_datetime, end_datetime, all_day,
                        venue_name, address, city, region, country,
                        latitude, longitude, geom,
                        location_id,
                        price, currency, free,
                        website, booking_url, contact_email, contact_phone,
                        images,
                        tags,
                        organizer, event_type, themes, source,
                        active, cancelled,
                        last_scraped_at,
                        external_id, source_url
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                        %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s,
                        %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s,
                        %s, %s
                    )
                    ON CONFLICT (external_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        start_datetime = EXCLUDED.start_datetime,
                        end_datetime = EXCLUDED.end_datetime,
                        themes = EXCLUDED.themes,
                        last_scraped_at = EXCLUDED.last_scraped_at,
                        updated_at = NOW()
                """, batch)

                target_conn.commit()
                inserted += len(batch)
                logger.info(f"Progress: {inserted} inserted, {skipped} skipped (processed {idx}/{len(events)})")
                batch = []

            except Exception as e:
                logger.error(f"Batch insert error: {e}")
                errors.append(str(e))
                target_conn.rollback()
                batch = []
                skipped += batch_size

    # Insert remaining batch
    if batch:
        try:
            execute_batch(target_cur, """
                INSERT INTO tripflow.events (
                    name, description, category,
                    start_datetime, end_datetime, all_day,
                    venue_name, address, city, region, country,
                    latitude, longitude, geom,
                    location_id,
                    price, currency, free,
                    website, booking_url, contact_email, contact_phone,
                    images,
                    tags,
                    organizer, event_type, themes, source,
                    active, cancelled,
                    last_scraped_at,
                    external_id, source_url
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s,
                    %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s,
                    %s, %s
                )
                ON CONFLICT (external_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    start_datetime = EXCLUDED.start_datetime,
                    end_datetime = EXCLUDED.end_datetime,
                    themes = EXCLUDED.themes,
                    last_scraped_at = EXCLUDED.last_scraped_at,
                    updated_at = NOW()
            """, batch)

            target_conn.commit()
            inserted += len(batch)
            logger.info(f"Final batch: {inserted} total inserted")
        except Exception as e:
            logger.error(f"Final batch error: {e}")
            errors.append(str(e))
            target_conn.rollback()

    # Update geom column for all new events
    logger.info("Updating geom column for events without geometry...")
    target_cur.execute("""
        UPDATE tripflow.events
        SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    geom_updated = target_cur.rowcount
    target_conn.commit()
    logger.info(f"Updated geom for {geom_updated} events")

    source_cur.close()
    target_cur.close()
    source_conn.close()
    target_conn.close()

    logger.info("=" * 80)
    logger.info(f"scraper_2 migration complete:")
    logger.info(f"  - Inserted/Updated: {inserted}")
    logger.info(f"  - Skipped: {skipped}")
    logger.info(f"  - Errors: {len(errors)}")
    if errors:
        logger.info(f"  - First error: {errors[0]}")
    logger.info("=" * 80)

    return inserted, skipped


def migrate_scraper_3():
    """Migrate scraper_3.events (Additional source - ~235 events)."""
    logger.info("=" * 80)
    logger.info("Migrating scraper_3.events (Additional source)")
    logger.info("=" * 80)

    logger.info("NOTE: scraper_3 has no latitude/longitude columns - skipping for now")
    logger.info("If this data is needed, we need to geocode the location/venue_name/city")
    logger.info("=" * 80)

    return 0, 0


if __name__ == "__main__":
    logger.info("Starting event migration from Scraparr to Tripflow")
    logger.info(f"Source: {SOURCE_DB}")
    logger.info(f"Target: {TARGET_DB}")
    logger.info("")

    try:
        # Migrate scraper_2 (main events dataset)
        inserted_2, skipped_2 = migrate_scraper_2()

        # Migrate scraper_3 (if needed)
        # inserted_3, skipped_3 = migrate_scraper_3()

        logger.info("")
        logger.info("=" * 80)
        logger.info("MIGRATION COMPLETE!")
        logger.info(f"Total events processed: {inserted_2}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
