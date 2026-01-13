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
import re
import unicodedata


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from an event name."""
    if not name:
        return "event"
    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', name)
    # Convert to ASCII, ignoring non-ASCII characters
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase
    slug = slug.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    slug = slug[:50]
    return slug or "event"


def fix_uitinvlaanderen_url(url: str, name: str) -> str:
    """
    Fix uitinvlaanderen.be URLs by inserting a slug between /e/ and the UUID.

    Bad URL:  https://www.uitinvlaanderen.be/agenda/e/a14e2c14-eff5-4378-8b4d-69effd90b591
    Good URL: https://www.uitinvlaanderen.be/agenda/e/my-event-name/a14e2c14-eff5-4378-8b4d-69effd90b591
    """
    if not url:
        return url

    # Pattern to match uitinvlaanderen URLs with /e/ followed directly by a UUID
    # UUID pattern: 8-4-4-4-12 hex characters
    pattern = r'(https?://(?:www\.)?uitinvlaanderen\.be/agenda/e/)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(.*)$'

    match = re.match(pattern, url, re.IGNORECASE)
    if match:
        base = match.group(1)
        uuid = match.group(2)
        rest = match.group(3)
        slug = generate_slug(name)
        return f"{base}{slug}/{uuid}{rest}"

    return url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connections
# When running inside Docker, use container names. When running on host, use localhost.
import socket
def is_docker():
    """Check if running inside Docker container"""
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return False

if is_docker():
    # Running inside Docker - use container hostnames
    # scraparr-postgres is on a different Docker network, need to use host IP
    SOURCE_DB = "postgresql://scraparr:scraparr@host.docker.internal:5434/scraparr"
    TARGET_DB = "postgresql://postgres:tripflow@postgres:5432/tripflow"
else:
    # Running on host
    SOURCE_DB = "postgresql://scraparr:scraparr@localhost:5434/scraparr"
    TARGET_DB = "postgresql://postgres:tripflow@localhost:5433/tripflow"


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

        # Fix URL by adding slug between /e/ and UUID
        fixed_url = fix_uitinvlaanderen_url(url, name)

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
            fixed_url, None, None, None,  # website, booking_url, contact_email, contact_phone
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
            external_id, fixed_url
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


def geocode_location(venue_name, country, cache={}):
    """
    Geocode a venue name using OpenStreetMap Nominatim.
    Uses caching to avoid repeated API calls.
    """
    import requests
    import time

    # Build search query
    search_query = f"{venue_name}, {country}" if country else venue_name

    # Check cache
    if search_query in cache:
        return cache[search_query]

    try:
        # Nominatim API (respect rate limits - 1 req/sec)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': search_query,
            'format': 'json',
            'limit': 1,
        }
        headers = {
            'User-Agent': 'TripFlow/1.0 (peter@tripflow.app)'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(1.1)  # Rate limit: 1 request per second

        if response.status_code == 200:
            results = response.json()
            if results:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                cache[search_query] = (lat, lon)
                return (lat, lon)

        cache[search_query] = None
        return None

    except Exception as e:
        logger.warning(f"Geocoding failed for '{search_query}': {e}")
        cache[search_query] = None
        return None


def migrate_scraper_3():
    """Migrate scraper_3.events (Eventbrite - needs geocoding)."""
    logger.info("=" * 80)
    logger.info("Migrating scraper_3.events (Eventbrite)")
    logger.info("=" * 80)

    source_conn = psycopg2.connect(SOURCE_DB)
    target_conn = psycopg2.connect(TARGET_DB)

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    # Fetch all physical events
    logger.info("Fetching events from scraper_3.events...")
    source_cur.execute("""
        SELECT
            event_id, name, description, url,
            start_date, location, venue_name,
            city, country, country_code,
            status, image_url, scraped_at, updated_at
        FROM scraper_3.events
        WHERE is_online = false
        ORDER BY id
    """)

    events = source_cur.fetchall()
    logger.info(f"Found {len(events)} physical events in scraper_3.events")
    logger.info("Geocoding will be performed (this may take a while due to rate limits)...")

    inserted = 0
    skipped = 0
    geocode_cache = {}
    errors = []

    for idx, event in enumerate(events, 1):
        (external_id, name, description, url,
         start_date_str, location, venue_name,
         city, country, country_code,
         status, image_url, scraped_at, updated_at) = event

        # Parse dates
        start_datetime = parse_datetime(str(start_date_str)) if start_date_str else None
        if not start_datetime:
            skipped += 1
            continue

        # Geocode the venue
        search_location = venue_name or location or city
        if not search_location:
            skipped += 1
            continue

        coords = geocode_location(search_location, country, geocode_cache)
        if not coords:
            skipped += 1
            if idx % 50 == 0:
                logger.info(f"Progress: {inserted} inserted, {skipped} skipped (processed {idx}/{len(events)})")
            continue

        lat, lng = coords

        # Build tags
        tags = ['eventbrite']
        if status:
            tags.append(status)

        # Build images
        images = [image_url] if image_url else []

        # Insert into tripflow.events
        try:
            target_cur.execute("""
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
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    geom = EXCLUDED.geom,
                    last_scraped_at = EXCLUDED.last_scraped_at,
                    updated_at = NOW()
            """, (
                name, description, 'other',  # category
                start_datetime, None, False,  # end_datetime, all_day
                venue_name, location, city, None, country,  # location
                lat, lng, lng, lat,  # coords for geom
                None,  # location_id
                None, 'EUR', True,  # price, currency, free
                url, url, None, None,  # website, booking_url, contact
                images,
                tags,
                None, None, tags, 'eventbrite',  # organizer, event_type, themes, source
                status == 'live', status == 'cancelled',  # active, cancelled
                scraped_at or datetime.now(),
                f"eb_{external_id}", url
            ))
            target_conn.commit()
            inserted += 1

        except Exception as e:
            logger.warning(f"Error inserting event {external_id}: {e}")
            errors.append(str(e))
            target_conn.rollback()
            skipped += 1

        if idx % 50 == 0:
            logger.info(f"Progress: {inserted} inserted, {skipped} skipped (processed {idx}/{len(events)})")

    source_cur.close()
    target_cur.close()
    source_conn.close()
    target_conn.close()

    logger.info("=" * 80)
    logger.info(f"scraper_3 (Eventbrite) migration complete:")
    logger.info(f"  - Inserted/Updated: {inserted}")
    logger.info(f"  - Skipped (no coords/date): {skipped}")
    logger.info(f"  - Errors: {len(errors)}")
    logger.info("=" * 80)

    return inserted, skipped


def migrate_scraper_4():
    """Migrate scraper_4.events (Ticketmaster - ~9,000 events with lat/lon)."""
    logger.info("=" * 80)
    logger.info("Migrating scraper_4.events (Ticketmaster)")
    logger.info("=" * 80)

    source_conn = psycopg2.connect(SOURCE_DB)
    target_conn = psycopg2.connect(TARGET_DB)

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    # Fetch all events with valid coordinates
    logger.info("Fetching events from scraper_4.events...")
    source_cur.execute("""
        SELECT
            event_id, name, description, info,
            start_date, start_date_local, timezone,
            status_code,
            venue_id, venue_name, venue_address,
            city, postal_code, country, country_code,
            latitude, longitude,
            price_min, price_max, currency,
            genre, segment, classifications,
            promoter_id, promoter_name,
            url, image_url,
            scraped_at, updated_at
        FROM scraper_4.events
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND latitude BETWEEN -90 AND 90
          AND longitude BETWEEN -180 AND 180
        ORDER BY id
    """)

    events = source_cur.fetchall()
    logger.info(f"Found {len(events)} events in scraper_4.events")

    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    batch = []
    batch_size = 100

    for idx, event in enumerate(events, 1):
        (external_id, name, description, info,
         start_date, start_date_local, timezone,
         status_code,
         venue_id, venue_name, venue_address,
         city, postal_code, country, country_code,
         lat, lng,
         price_min, price_max, currency,
         genre, segment, classifications,
         promoter_id, promoter_name,
         url, image_url,
         scraped_at, updated_at) = event

        # Parse dates - prefer start_date, fallback to start_date_local
        start_datetime = None
        if start_date:
            start_datetime = start_date if isinstance(start_date, datetime) else parse_datetime(str(start_date))
        if not start_datetime and start_date_local:
            start_datetime = parse_datetime(str(start_date_local))

        # Skip if no valid start date
        if not start_datetime:
            skipped += 1
            continue

        # Use description or info
        event_description = description or info

        # Build themes from genre, segment, and classifications
        themes = []
        if genre:
            themes.append(genre)
        if segment:
            themes.append(segment)

        # Try to parse classifications JSON for more themes
        if classifications:
            try:
                import json
                if isinstance(classifications, str):
                    class_data = json.loads(classifications)
                else:
                    class_data = classifications

                if isinstance(class_data, list):
                    for c in class_data:
                        if isinstance(c, dict):
                            for key in ['genre', 'subGenre', 'type', 'subType']:
                                if key in c and isinstance(c[key], dict) and 'name' in c[key]:
                                    themes.append(c[key]['name'])
            except:
                pass

        themes = list(set(themes))[:10]  # Dedupe and limit

        # Map to category based on segment/genre
        category = 'other'
        segment_lower = (segment or '').lower()
        genre_lower = (genre or '').lower()

        if 'music' in segment_lower or 'concert' in genre_lower:
            category = 'CONCERT'
        elif 'sports' in segment_lower:
            category = 'SPORTS'
        elif 'theatre' in segment_lower or 'arts' in segment_lower:
            category = 'THEATER'
        elif 'comedy' in genre_lower:
            category = 'Comedy'
        elif 'family' in segment_lower:
            category = 'Family'
        elif 'festival' in genre_lower:
            category = 'Fairs & Festivals'
        else:
            # Use the segment or genre directly as category
            category = segment or genre or 'other'

        # Determine if free
        is_free = (price_min == 0 and price_max == 0) if price_min is not None else False

        # Build images array
        images = [image_url] if image_url else []

        # Prepare row for batch insert
        row = (
            # Basic info
            name, event_description, category,
            # Dates
            start_datetime, None, False,  # end_datetime=None, all_day=False
            # Location
            venue_name, venue_address, city, None, country,  # region=None
            lat, lng, lng, lat,  # lat, lng, then lng/lat for ST_MakePoint
            # Location link
            None,  # location_id
            # Details
            price_min, currency or 'EUR', is_free,
            # Contact
            url, url, None, None,  # website, booking_url, contact_email, contact_phone
            # Media
            images,
            # Tags
            themes,
            # Discovery fields
            promoter_name, genre, themes, 'ticketmaster',
            # Status
            status_code in ('onsale', 'offsale', 'rescheduled'),  # active
            status_code == 'cancelled',  # cancelled
            # Scraping
            scraped_at or datetime.now(),
            # External ref
            f"tm_{external_id}", url
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
                        category = EXCLUDED.category,
                        themes = EXCLUDED.themes,
                        price = EXCLUDED.price,
                        active = EXCLUDED.active,
                        cancelled = EXCLUDED.cancelled,
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
                    category = EXCLUDED.category,
                    themes = EXCLUDED.themes,
                    price = EXCLUDED.price,
                    active = EXCLUDED.active,
                    cancelled = EXCLUDED.cancelled,
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

    source_cur.close()
    target_cur.close()
    source_conn.close()
    target_conn.close()

    logger.info("=" * 80)
    logger.info(f"scraper_4 (Ticketmaster) migration complete:")
    logger.info(f"  - Inserted/Updated: {inserted}")
    logger.info(f"  - Skipped: {skipped}")
    logger.info(f"  - Errors: {len(errors)}")
    if errors:
        logger.info(f"  - First error: {errors[0]}")
    logger.info("=" * 80)

    return inserted, skipped


if __name__ == "__main__":
    logger.info("Starting event migration from Scraparr to Tripflow")
    logger.info(f"Source: {SOURCE_DB}")
    logger.info(f"Target: {TARGET_DB}")
    logger.info("")

    try:
        # Migrate scraper_2 (UiT in Vlaanderen - Belgium events)
        inserted_2, skipped_2 = migrate_scraper_2()

        # Migrate scraper_3 (Eventbrite - needs geocoding)
        # This takes ~17 minutes due to geocoding rate limits (1 req/sec for ~1000 events)
        inserted_3, skipped_3 = migrate_scraper_3()

        # Migrate scraper_4 (Ticketmaster - Europe-wide events with coordinates)
        inserted_4, skipped_4 = migrate_scraper_4()

        logger.info("")
        logger.info("=" * 80)
        logger.info("MIGRATION COMPLETE!")
        logger.info(f"UiT in Vlaanderen: {inserted_2} events")
        logger.info(f"Eventbrite: {inserted_3} events (geocoded)")
        logger.info(f"Ticketmaster: {inserted_4} events")
        logger.info(f"Total events: {inserted_2 + inserted_3 + inserted_4}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
