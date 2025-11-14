from typing import Dict, Any
from .base_importer import BaseImporter
from app.models import LocationType
import logging
import json

logger = logging.getLogger(__name__)


class Park4NightImporter(BaseImporter):
    """
    Importer for Park4Night data from Scraparr database.

    Imports data from scraper_2 schema (Park4Night places).
    """

    def get_source_name(self) -> str:
        return "park4night"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Scraparr's Park4Night scraper_2 schema.
        """
        return """
            SELECT
                id,
                nom as name,
                latitude,
                longitude,
                pays as country,
                note as rating,
                photos,
                internet,
                electricite as electricity,
                tarif as price_info,
                animaux_acceptes as pets_allowed,
                eau_noire as waste_disposal,
                type_de_lieu as location_type_raw,
                stationnement as parking_type,
                camping_car_park,
                etiquettes as tags_raw,
                description,
                ville as city,
                updated_at,
                scraped_at
            FROM scraper_2.places
            ORDER BY id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Scraparr Park4Night row to TripFlow Location format.
        """
        # Map Park4Night type_de_lieu to LocationType
        type_mapping = {
            'PARKING PAYANT JOUR ET NUIT': LocationType.PARKING,
            'PARKING GRATUIT': LocationType.PARKING,
            'AIRE DE SERVICE': LocationType.SERVICE_AREA,
            'AIRE DE PIQUE-NIQUE': LocationType.REST_AREA,
            'CAMPING': LocationType.CAMPSITE,
            'CAMPING MUNICIPAL': LocationType.CAMPSITE,
            'CAMPING PRIVE': LocationType.CAMPSITE,
            'CAMPING-CAR PARK': LocationType.PARKING,
            'FERME': LocationType.POI,
            'POINT DE VUE': LocationType.ATTRACTION,
            'LIEU INSOLITE': LocationType.ATTRACTION,
            'ZONE NATURELLE': LocationType.POI,
        }

        location_type = type_mapping.get(
            row.get("location_type_raw", "").upper() if row.get("location_type_raw") else "",
            LocationType.PARKING  # default
        )

        # Build amenities list from boolean fields
        amenities = []
        if row.get("internet"):
            amenities.append("wifi")
        if row.get("electricity"):
            amenities.append("electricity")
        if row.get("waste_disposal"):
            amenities.append("waste_disposal")
        if row.get("camping_car_park"):
            amenities.append("motorhome_parking")
        if row.get("pets_allowed"):
            amenities.append("pets_allowed")

        # Parse tags from etiquettes field
        tags = []
        if row.get("tags_raw"):
            tags_raw = row["tags_raw"]
            if isinstance(tags_raw, str):
                # Split by comma and clean
                tags = [tag.strip() for tag in tags_raw.split(',') if tag.strip()]

                # Add additional amenities based on tags
                tags_lower = tags_raw.lower()
                if 'douche' in tags_lower or 'shower' in tags_lower:
                    amenities.append('shower')
                if 'toilette' in tags_lower or 'wc' in tags_lower or 'toilet' in tags_lower:
                    amenities.append('toilet')
                if 'eau' in tags_lower or 'water' in tags_lower:
                    amenities.append('water')

        # Handle images
        images = []
        main_image = None
        if row.get("photos"):
            photos = row["photos"]
            if isinstance(photos, str):
                photo_urls = [url.strip() for url in photos.split(',') if url.strip()]
                images = [{"url": url, "type": "photo"} for url in photo_urls]
                if images:
                    main_image = images[0]["url"]

        # Determine price type
        price_type = "unknown"
        price_min = None
        price_max = None

        if row.get("price_info"):
            price_str = str(row["price_info"]).lower()
            if 'gratuit' in price_str or 'free' in price_str or price_str == '0':
                price_type = "free"
                price_min = 0
                price_max = 0
            elif 'donation' in price_str or 'don' in price_str:
                price_type = "donation"
            else:
                # Try to extract numeric price
                import re
                numbers = re.findall(r'\d+\.?\d*', price_str)
                if numbers:
                    price_type = "paid"
                    prices = [float(n) for n in numbers]
                    price_min = min(prices)
                    price_max = max(prices) if len(prices) > 1 else price_min

        # Build features list
        features = []
        if row.get("parking_type"):
            features.append(row["parking_type"])

        # Create the transformed data
        return {
            "external_id": f"park4night_{row.get('id')}",
            "name": row.get("name") or f"Park4Night Location {row.get('id')}",
            "description": row.get("description"),
            "location_type": location_type,
            "latitude": float(row.get("latitude")) if row.get("latitude") else None,
            "longitude": float(row.get("longitude")) if row.get("longitude") else None,
            "geom": f"POINT({row.get('longitude')} {row.get('latitude')})" if row.get("longitude") and row.get("latitude") else None,
            "address": None,  # Park4Night doesn't provide street address
            "city": row.get("city"),
            "region": None,  # Not provided by Park4Night
            "country": row.get("country"),
            "postal_code": None,  # Not provided by Park4Night
            "amenities": amenities,
            "features": features,
            "rating": float(row.get("rating")) if row.get("rating") else None,
            "review_count": 0,  # Would need to join with reviews table
            "price_type": price_type,
            "price_min": price_min,
            "price_max": price_max,
            "price_info": row.get("price_info"),
            "currency": "EUR",
            "phone": None,  # Not provided by Park4Night
            "email": None,  # Not provided by Park4Night
            "website": f"https://park4night.com/lieu/{row.get('id')}" if row.get("id") else None,
            "images": images,
            "main_image_url": main_image,
            "tags": tags,
            "active": True,  # Assume all scraped locations are active
            "source_url": f"https://park4night.com/lieu/{row.get('id')}" if row.get("id") else None,
            "raw_data": json.dumps({
                "location_type_raw": row.get("location_type_raw"),
                "parking_type": row.get("parking_type"),
                "tags_raw": row.get("tags_raw"),
                "scraped_at": row.get("scraped_at").isoformat() if row.get("scraped_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            })
        }