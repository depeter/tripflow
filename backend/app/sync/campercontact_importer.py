from typing import Dict, Any
from .base_importer import BaseImporter
from app.models import LocationType
import logging

logger = logging.getLogger(__name__)


class CamperContactImporter(BaseImporter):
    """
    Importer for CamperContact data.

    TODO: Customize this based on your actual CamperContact database schema.
    """

    def get_source_name(self) -> str:
        return "campercontact"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from CamperContact database.

        TODO: Update table and column names to match your actual schema.
        """
        return """
            SELECT
                id as source_id,
                name,
                description,
                type,
                latitude,
                longitude,
                address,
                city,
                region,
                country,
                amenities,
                rating,
                reviews,
                price_per_night,
                contact_phone,
                contact_email,
                website_url,
                photo_urls,
                categories,
                is_active
            FROM camper_locations
            WHERE is_active = true
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform CamperContact row to TripFlow Location format.

        TODO: Customize field mapping based on your actual data structure.
        """
        # Map CamperContact type to LocationType
        type_mapping = {
            "campsite": LocationType.CAMPSITE,
            "camperplace": LocationType.PARKING,
            "parking": LocationType.PARKING,
            "rest_stop": LocationType.REST_AREA,
            "attraction": LocationType.ATTRACTION,
        }

        location_type = type_mapping.get(
            row.get("type", "").lower(),
            LocationType.CAMPSITE  # default for camper-related
        )

        # Transform amenities
        amenities = row.get("amenities", [])
        if isinstance(amenities, str):
            amenities = [a.strip() for a in amenities.split(",") if a.strip()]

        # Transform categories to tags
        tags = row.get("categories", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        # Transform photo URLs
        images = row.get("photo_urls", [])
        if isinstance(images, str):
            images = [i.strip() for i in images.split(",") if i.strip()]

        return {
            "external_id": str(row.get("source_id")),
            "name": row.get("name", "Unknown"),
            "description": row.get("description"),
            "location_type": location_type,
            "latitude": float(row.get("latitude")),
            "longitude": float(row.get("longitude")),
            "geom": f"POINT({row.get('longitude')} {row.get('latitude')})",
            "address": row.get("address"),
            "city": row.get("city"),
            "region": row.get("region"),
            "country": row.get("country"),
            "amenities": amenities,
            "rating": row.get("rating"),
            "review_count": row.get("reviews", 0),
            "price": row.get("price_per_night"),
            "currency": "EUR",
            "phone": row.get("contact_phone"),
            "email": row.get("contact_email"),
            "website": row.get("website_url"),
            "images": images,
            "tags": tags,
            "active": row.get("is_active", True),
        }
