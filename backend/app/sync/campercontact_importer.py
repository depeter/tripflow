from typing import Dict, Any, Optional
from .base_importer import BaseImporter
from app.models import LocationType
import logging
import json

logger = logging.getLogger(__name__)


class CamperContactImporter(BaseImporter):
    """
    Importer for CamperContact data from Scraparr database.

    Imports data from scraper_5 schema (CamperContact places).
    """

    def get_source_name(self) -> str:
        return "campercontact"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Scraparr's CamperContact scraper_5 schema.
        """
        return """
            SELECT
                id,
                poi_id,
                sitecode,
                type,
                latitude,
                longitude,
                is_bookable,
                is_claimed,
                subscription_level,
                raw_data,
                scraped_at,
                updated_at
            FROM scraper_5.places
            WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Scraparr CamperContact row to TripFlow Location format.
        """
        # Parse raw_data JSON for additional details
        raw_data = row.get("raw_data", {})
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}

        # Map CamperContact type to LocationType
        type_mapping = {
            "camperplace": LocationType.PARKING,
            "campsite": LocationType.CAMPSITE,
            "parking": LocationType.PARKING,
            "motorhome_area": LocationType.SERVICE_AREA,
            "rest_stop": LocationType.REST_AREA,
        }

        location_type_raw = row.get("type") or raw_data.get("type", "")
        location_type = type_mapping.get(
            location_type_raw.lower() if location_type_raw else "",
            LocationType.PARKING  # default for camper-related
        )

        # Build amenities based on available data
        amenities = []
        if row.get("is_bookable"):
            amenities.append("online_booking")

        # Build features
        features = []
        if row.get("subscription_level"):
            features.append(f"Subscription Level {row['subscription_level']}")
        if row.get("is_claimed"):
            features.append("Claimed by owner")

        # Build tags
        tags = []
        if location_type_raw:
            tags.append(location_type_raw)

        # Determine price type based on subscription level
        # Higher subscription levels typically mean paid sites
        price_type = "unknown"
        if row.get("subscription_level"):
            if row["subscription_level"] >= 20:
                price_type = "paid"
            elif row["subscription_level"] >= 10:
                price_type = "donation"
            else:
                price_type = "free"

        # Create website URL
        website = f"https://campercontact.com/en/camping/{row.get('sitecode')}" if row.get("sitecode") else None

        # Create the transformed data
        return {
            "external_id": f"campercontact_{row.get('poi_id') or row.get('id')}",
            "name": f"CamperContact {row.get('sitecode') or row.get('id')}",  # CamperContact doesn't provide names
            "description": None,  # Would need to be scraped from detail page
            "location_type": location_type,
            "latitude": float(row.get("latitude")) if row.get("latitude") else None,
            "longitude": float(row.get("longitude")) if row.get("longitude") else None,
            "geom": f"POINT({row.get('longitude')} {row.get('latitude')})" if row.get("longitude") and row.get("latitude") else None,
            "address": None,  # Not provided in grid scraper data
            "city": None,  # Not provided in grid scraper data
            "region": None,
            "country": None,  # Would need reverse geocoding
            "postal_code": None,
            "amenities": amenities,
            "features": features,
            "rating": None,  # Not provided in grid scraper data
            "review_count": 0,
            "price_type": price_type,
            "price_min": None,
            "price_max": None,
            "price_info": None,
            "currency": "EUR",
            "phone": None,
            "email": None,
            "website": website,
            "images": [],
            "main_image_url": None,
            "tags": tags,
            "active": True,  # All scraped locations assumed active
            "source_url": website,
            "raw_data": json.dumps({
                "poi_id": row.get("poi_id"),
                "sitecode": row.get("sitecode"),
                "type": row.get("type"),
                "is_bookable": row.get("is_bookable"),
                "is_claimed": row.get("is_claimed"),
                "subscription_level": row.get("subscription_level"),
                "original_raw_data": raw_data,
                "scraped_at": row.get("scraped_at").isoformat() if row.get("scraped_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            })
        }
