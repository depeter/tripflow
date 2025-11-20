from typing import Dict, Any, Optional
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
        Includes multilingual descriptions from place_descriptions table.
        """
        return """
            SELECT
                p.id,
                p.nom as name,
                p.latitude,
                p.longitude,
                p.pays as country,
                p.note as rating,
                p.photos,
                p.internet,
                p.electricite as electricity,
                p.tarif as price_info,
                p.animaux_acceptes as pets_allowed,
                p.eau_noire as waste_disposal,
                p.type_de_lieu as location_type_raw,
                p.stationnement as parking_type,
                p.camping_car_park,
                p.etiquettes as tags_raw,
                p.description,
                p.ville as city,
                p.updated_at,
                p.scraped_at,
                -- Aggregate all language descriptions as JSON
                COALESCE(
                    json_object_agg(
                        pd.language_code,
                        pd.description
                    ) FILTER (WHERE pd.language_code IS NOT NULL),
                    '{}'::json
                ) as descriptions_json
            FROM scraper_2.places p
            LEFT JOIN scraper_2.place_descriptions pd ON p.id = pd.place_id
            GROUP BY p.id, p.nom, p.latitude, p.longitude, p.pays, p.note, p.photos,
                     p.internet, p.electricite, p.tarif, p.animaux_acceptes, p.eau_noire,
                     p.type_de_lieu, p.stationnement, p.camping_car_park, p.etiquettes,
                     p.description, p.ville, p.updated_at, p.scraped_at
            ORDER BY p.id
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

        # Use fallback description field (will be overridden by translations table)
        # Priority: English > French > Dutch > German > Spanish > Italian > fallback
        primary_description = row.get("description")

        # Create the transformed data
        return {
            "external_id": f"park4night_{row.get('id')}",
            "name": row.get("name") or f"Park4Night Location {row.get('id')}",
            "description": primary_description,  # Fallback only, translations handled separately
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
                # Multilingual descriptions now stored in location_translations table
            })
        }

    def get_translations(self, row: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract multilingual descriptions from Park4Night data.

        Returns:
            Dictionary mapping language codes to descriptions:
            {'en': 'English text', 'nl': 'Dutch text', 'fr': 'French text', ...}
        """
        descriptions_json = row.get("descriptions_json", {})
        if isinstance(descriptions_json, str):
            try:
                descriptions_json = json.loads(descriptions_json)
            except:
                return None

        # Return only non-empty descriptions
        translations = {}
        for lang_code in ['en', 'nl', 'fr', 'de', 'es', 'it']:
            desc = descriptions_json.get(lang_code)
            if desc and desc.strip():
                translations[lang_code] = desc.strip()

        return translations if translations else None