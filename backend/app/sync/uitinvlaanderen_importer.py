from typing import Dict, Any, Optional
from .base_importer import BaseImporter
from app.models import LocationType
import logging
import json
import re
import unicodedata

logger = logging.getLogger(__name__)


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


class UiTinVlaanderenImporter(BaseImporter):
    """
    Importer for UiT in Vlaanderen event data from Scraparr database.

    Imports data from scraper_2 schema (UiT in Vlaanderen events).
    """

    def get_source_name(self) -> str:
        return "uitinvlaanderen"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Scraparr's UiT in Vlaanderen scraper_2 schema.
        """
        return """
            SELECT
                id,
                event_id,
                name,
                description,
                start_date,
                end_date,
                location_name,
                street_address,
                city,
                postal_code,
                country,
                latitude,
                longitude,
                organizer,
                event_type,
                themes,
                url,
                image_url,
                scraped_at,
                updated_at
            FROM scraper_2.events
            WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Scraparr UiT in Vlaanderen event row to TripFlow Location format.
        """
        # Parse themes into tags
        tags = []
        if row.get("themes"):
            themes_raw = row["themes"]
            if isinstance(themes_raw, str):
                tags = [theme.strip() for theme in themes_raw.split(',') if theme.strip()]

        # Parse event type
        event_type = row.get("event_type", "")

        # Build features list
        features = []
        if event_type:
            features.append(event_type)
        if row.get("organizer"):
            features.append(f"Organized by {row['organizer']}")

        # Handle images
        images = []
        main_image = None
        if row.get("image_url"):
            images = [{"url": row["image_url"], "type": "photo"}]
            main_image = row["image_url"]

        # Determine amenities based on event type and themes
        amenities = []
        themes_lower = " ".join(tags).lower()
        if "music" in themes_lower or "concert" in themes_lower:
            amenities.append("entertainment")
        if "food" in themes_lower or "restaurant" in themes_lower:
            amenities.append("restaurant")
        if "outdoor" in themes_lower or "nature" in themes_lower:
            amenities.append("outdoor")

        # Create the transformed data
        return {
            "external_id": f"uit_{row.get('event_id')}",
            "name": row.get("name") or f"Event {row.get('event_id')}",
            "description": row.get("description"),
            "location_type": LocationType.EVENT,
            "latitude": float(row.get("latitude")) if row.get("latitude") else None,
            "longitude": float(row.get("longitude")) if row.get("longitude") else None,
            "geom": f"POINT({row.get('longitude')} {row.get('latitude')})" if row.get("longitude") and row.get("latitude") else None,
            "address": row.get("street_address"),
            "city": row.get("city"),
            "region": None,
            "country": row.get("country") or "Belgium",
            "postal_code": row.get("postal_code"),
            "amenities": amenities,
            "features": features,
            "rating": None,  # Events don't have ratings
            "review_count": 0,
            "price_type": "unknown",  # UiT doesn't provide price info
            "price_min": None,
            "price_max": None,
            "price_info": None,
            "currency": "EUR",
            "phone": None,
            "email": None,
            "website": fix_uitinvlaanderen_url(row.get("url"), row.get("name")),
            "images": images,
            "main_image_url": main_image,
            "tags": tags,
            "active": True,
            "source_url": fix_uitinvlaanderen_url(row.get("url"), row.get("name")),
            "raw_data": json.dumps({
                "event_id": row.get("event_id"),
                "event_type": event_type,
                "organizer": row.get("organizer"),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "location_name": row.get("location_name"),
                "scraped_at": row.get("scraped_at").isoformat() if row.get("scraped_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            })
        }
