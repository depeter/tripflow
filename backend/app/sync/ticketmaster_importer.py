from typing import Dict, Any, Optional
from .base_importer import BaseImporter
from app.models import LocationType
import logging
import json

logger = logging.getLogger(__name__)


class TicketmasterImporter(BaseImporter):
    """
    Importer for Ticketmaster event data from Scraparr database.

    Imports data from scraper_4 schema (Ticketmaster events).
    """

    def get_source_name(self) -> str:
        return "ticketmaster"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Scraparr's Ticketmaster scraper_4 schema.
        """
        return """
            SELECT
                id,
                event_id,
                name,
                description,
                url,
                info,
                start_date,
                start_date_local,
                timezone,
                status_code,
                venue_id,
                venue_name,
                venue_address,
                city,
                postal_code,
                country,
                country_code,
                latitude,
                longitude,
                price_min,
                price_max,
                currency,
                genre,
                segment,
                classifications,
                promoter_id,
                promoter_name,
                image_url,
                image_ratio,
                external_links,
                scraped_at,
                updated_at
            FROM scraper_4.events
            WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Scraparr Ticketmaster event row to TripFlow Location format.
        """
        # Parse genre and segment into tags
        tags = []
        if row.get("genre"):
            tags.append(row["genre"])
        if row.get("segment"):
            tags.append(row["segment"])

        # Parse classifications JSON
        classifications = []
        if row.get("classifications"):
            try:
                if isinstance(row["classifications"], str):
                    classifications_data = json.loads(row["classifications"])
                else:
                    classifications_data = row["classifications"]

                if isinstance(classifications_data, list):
                    for classification in classifications_data:
                        if isinstance(classification, dict):
                            for key in ["genre", "subGenre", "type", "subType"]:
                                if key in classification and classification[key]:
                                    if isinstance(classification[key], dict) and "name" in classification[key]:
                                        tags.append(classification[key]["name"])
            except Exception as e:
                logger.warning(f"Error parsing classifications for event {row.get('event_id')}: {e}")

        # Remove duplicates from tags
        tags = list(set(tags))

        # Build features list
        features = []
        if row.get("venue_name"):
            features.append(f"Venue: {row['venue_name']}")
        if row.get("promoter_name"):
            features.append(f"Promoter: {row['promoter_name']}")

        # Handle images
        images = []
        main_image = None
        if row.get("image_url"):
            images = [{"url": row["image_url"], "type": "photo", "ratio": row.get("image_ratio")}]
            main_image = row["image_url"]

        # Determine price type
        price_type = "unknown"
        if row.get("price_min") is not None and row.get("price_max") is not None:
            if row["price_min"] == 0 and row["price_max"] == 0:
                price_type = "free"
            else:
                price_type = "paid"

        # Determine amenities based on segment/genre
        amenities = []
        segment_lower = (row.get("segment") or "").lower()
        genre_lower = (row.get("genre") or "").lower()

        if "music" in segment_lower or "concert" in genre_lower:
            amenities.append("entertainment")
        if "sports" in segment_lower:
            amenities.append("sports")
        if "theatre" in segment_lower or "arts" in segment_lower:
            amenities.append("arts")

        # Build price info string
        price_info = None
        if row.get("price_min") is not None and row.get("price_max") is not None:
            if row["price_min"] == row["price_max"]:
                price_info = f"{row['currency']} {row['price_min']}"
            else:
                price_info = f"{row['currency']} {row['price_min']} - {row['price_max']}"

        # Create the transformed data
        return {
            "external_id": f"ticketmaster_{row.get('event_id')}",
            "name": row.get("name") or f"Event {row.get('event_id')}",
            "description": row.get("description") or row.get("info"),
            "location_type": LocationType.EVENT,
            "latitude": float(row.get("latitude")) if row.get("latitude") else None,
            "longitude": float(row.get("longitude")) if row.get("longitude") else None,
            "geom": f"POINT({row.get('longitude')} {row.get('latitude')})" if row.get("longitude") and row.get("latitude") else None,
            "address": row.get("venue_address"),
            "city": row.get("city"),
            "region": None,
            "country": row.get("country"),
            "postal_code": row.get("postal_code"),
            "amenities": amenities,
            "features": features,
            "rating": None,  # Ticketmaster doesn't provide ratings
            "review_count": 0,
            "price_type": price_type,
            "price_min": float(row["price_min"]) if row.get("price_min") is not None else None,
            "price_max": float(row["price_max"]) if row.get("price_max") is not None else None,
            "price_info": price_info,
            "currency": row.get("currency"),
            "phone": None,
            "email": None,
            "website": row.get("url"),
            "images": images,
            "main_image_url": main_image,
            "tags": tags,
            "active": row.get("status_code") in ["onsale", "offsale", "rescheduled"],
            "source_url": row.get("url"),
            "raw_data": json.dumps({
                "event_id": row.get("event_id"),
                "start_date": row.get("start_date").isoformat() if row.get("start_date") else row.get("start_date_local"),
                "timezone": row.get("timezone"),
                "status_code": row.get("status_code"),
                "venue_id": row.get("venue_id"),
                "venue_name": row.get("venue_name"),
                "genre": row.get("genre"),
                "segment": row.get("segment"),
                "classifications": row.get("classifications"),
                "promoter_id": row.get("promoter_id"),
                "promoter_name": row.get("promoter_name"),
                "external_links": row.get("external_links"),
                "scraped_at": row.get("scraped_at").isoformat() if row.get("scraped_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            })
        }
