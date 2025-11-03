from typing import Dict, Any
from .base_importer import BaseImporter
from app.models import LocationType
import logging

logger = logging.getLogger(__name__)


class LocalSitesImporter(BaseImporter):
    """
    Importer for local sites data.

    TODO: Customize this based on your actual local sites database schema.
    """

    def get_source_name(self) -> str:
        return "local_sites"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from local sites database.

        TODO: Update table and column names to match your actual schema.
        """
        return """
            SELECT
                id as source_id,
                site_name,
                description,
                site_type,
                lat,
                lng,
                full_address,
                city,
                state,
                country,
                zip_code,
                features,
                avg_rating,
                total_reviews,
                entry_fee,
                phone_number,
                email_address,
                website,
                image_urls,
                keywords,
                status
            FROM sites
            WHERE status = 'active'
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform local sites row to TripFlow Location format.

        TODO: Customize field mapping based on your actual data structure.
        """
        # Map local site type to LocationType
        type_mapping = {
            "campground": LocationType.CAMPSITE,
            "parking": LocationType.PARKING,
            "rest_area": LocationType.REST_AREA,
            "tourist_attraction": LocationType.ATTRACTION,
            "point_of_interest": LocationType.POI,
        }

        location_type = type_mapping.get(
            row.get("site_type", "").lower().replace(" ", "_"),
            LocationType.POI  # default
        )

        # Transform features to amenities
        amenities = row.get("features", [])
        if isinstance(amenities, str):
            amenities = [a.strip() for a in amenities.split(",") if a.strip()]

        # Transform keywords to tags
        tags = row.get("keywords", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        # Transform images
        images = row.get("image_urls", [])
        if isinstance(images, str):
            images = [i.strip() for i in images.split(",") if i.strip()]

        return {
            "external_id": str(row.get("source_id")),
            "name": row.get("site_name", "Unknown"),
            "description": row.get("description"),
            "location_type": location_type,
            "latitude": float(row.get("lat")),
            "longitude": float(row.get("lng")),
            "geom": f"POINT({row.get('lng')} {row.get('lat')})",
            "address": row.get("full_address"),
            "city": row.get("city"),
            "region": row.get("state"),
            "country": row.get("country"),
            "postal_code": row.get("zip_code"),
            "amenities": amenities,
            "rating": row.get("avg_rating"),
            "review_count": row.get("total_reviews", 0),
            "price": row.get("entry_fee"),
            "currency": "EUR",
            "phone": row.get("phone_number"),
            "email": row.get("email_address"),
            "website": row.get("website"),
            "images": images,
            "tags": tags,
            "active": row.get("status") == "active",
        }
