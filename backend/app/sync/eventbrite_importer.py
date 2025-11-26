from typing import Dict, Any, Optional
from .base_importer import BaseImporter
from app.models import LocationType
import logging
import json

logger = logging.getLogger(__name__)


class EventbriteImporter(BaseImporter):
    """
    Importer for Eventbrite event data from Scraparr database.

    Imports data from scraper_3 schema (Eventbrite events).
    """

    def get_source_name(self) -> str:
        return "eventbrite"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Scraparr's Eventbrite scraper_3 schema.
        """
        return """
            SELECT
                id,
                event_id,
                name,
                description,
                url,
                start_date,
                location,
                venue_name,
                city,
                country,
                country_code,
                status,
                image_url,
                is_online,
                scraped_at,
                updated_at
            FROM scraper_3.events
            WHERE is_online = false  -- Only physical events
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Scraparr Eventbrite event row to TripFlow Location format.
        """
        # Parse location string to extract coordinates if possible
        # Eventbrite doesn't provide lat/lon directly, so we may need to geocode
        # For now, we'll skip events without proper location data

        # Extract lat/lon from location field if available (format: "City, Country")
        location_str = row.get("location", "")

        # Build tags from status and venue
        tags = []
        if row.get("status"):
            tags.append(row["status"])
        if row.get("venue_name"):
            tags.append(f"Venue: {row['venue_name']}")

        # Handle images
        images = []
        main_image = None
        if row.get("image_url"):
            images = [{"url": row["image_url"], "type": "photo"}]
            main_image = row["image_url"]

        # Determine amenities
        amenities = []
        if not row.get("is_online"):
            amenities.append("in-person")

        # Create the transformed data
        # NOTE: Eventbrite events without lat/lon will need geocoding
        return {
            "external_id": f"eventbrite_{row.get('event_id')}",
            "name": row.get("name") or f"Event {row.get('event_id')}",
            "description": row.get("description"),
            "location_type": LocationType.EVENT,
            "latitude": None,  # Need geocoding
            "longitude": None,  # Need geocoding
            "geom": None,
            "address": location_str,
            "city": row.get("city"),
            "region": None,
            "country": row.get("country"),
            "postal_code": None,
            "amenities": amenities,
            "features": [row.get("venue_name")] if row.get("venue_name") else [],
            "rating": None,
            "review_count": 0,
            "price_type": "unknown",
            "price_min": None,
            "price_max": None,
            "price_info": None,
            "currency": None,
            "phone": None,
            "email": None,
            "website": row.get("url"),
            "images": images,
            "main_image_url": main_image,
            "tags": tags,
            "active": row.get("status") == "live",
            "source_url": row.get("url"),
            "raw_data": json.dumps({
                "event_id": row.get("event_id"),
                "status": row.get("status"),
                "venue_name": row.get("venue_name"),
                "is_online": row.get("is_online"),
                "start_date": row.get("start_date"),
                "country_code": row.get("country_code"),
                "scraped_at": row.get("scraped_at").isoformat() if row.get("scraped_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            })
        }

    def fetch_source_data(self, limit: Optional[int] = None) -> list:
        """
        Override to skip Eventbrite events without coordinates.

        Note: Eventbrite scraper doesn't capture lat/lon, so these events
        would need geocoding before being useful in TripFlow.
        We'll import them but mark them as needing geocoding.
        """
        logger.warning(
            f"Eventbrite events do not have coordinates. "
            f"Geocoding will be needed before they can be used in TripFlow."
        )
        return super().fetch_source_data(limit=limit)
