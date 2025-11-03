from typing import Dict, Any
from .base_importer import BaseImporter
from app.models import LocationType
import logging

logger = logging.getLogger(__name__)


class Park4NightImporter(BaseImporter):
    """
    Importer for Park4Night data.

    TODO: Customize this based on your actual Park4Night database schema.
    """

    def get_source_name(self) -> str:
        return "park4night"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Park4Night database.

        TODO: Update table and column names to match your actual schema.
        Example assumes a table named 'locations' with common fields.
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
                postal_code,
                amenities,
                rating,
                review_count,
                price,
                phone,
                email,
                website,
                images,
                tags,
                active
            FROM locations
            WHERE active = true
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Park4Night row to TripFlow Location format.

        TODO: Customize field mapping based on your actual data structure.
        """
        # Map Park4Night type to LocationType
        type_mapping = {
            "campsite": LocationType.CAMPSITE,
            "parking": LocationType.PARKING,
            "rest_area": LocationType.REST_AREA,
            "poi": LocationType.POI,
        }

        location_type = type_mapping.get(
            row.get("type", "").lower(),
            LocationType.PARKING  # default
        )

        # Transform amenities if they come in different format
        amenities = row.get("amenities", [])
        if isinstance(amenities, str):
            # If amenities are comma-separated string
            amenities = [a.strip() for a in amenities.split(",") if a.strip()]

        # Transform tags similarly
        tags = row.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        # Transform images
        images = row.get("images", [])
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
            "postal_code": row.get("postal_code"),
            "amenities": amenities,
            "rating": row.get("rating"),
            "review_count": row.get("review_count", 0),
            "price": row.get("price"),
            "currency": "EUR",
            "phone": row.get("phone"),
            "email": row.get("email"),
            "website": row.get("website"),
            "images": images,
            "tags": tags,
            "active": row.get("active", True),
        }
