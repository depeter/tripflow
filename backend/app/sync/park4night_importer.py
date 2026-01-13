from typing import Dict, Any, Optional
from .base_importer import BaseImporter
from app.models import LocationType
import logging
import json

logger = logging.getLogger(__name__)


class Park4NightImporter(BaseImporter):
    """
    Importer for Park4Night data from Scraparr database.

    Imports data from scraper_1 schema (Park4Night places).
    Includes multilingual descriptions (en, nl, fr, de, es, it) and photo URLs.
    """

    def get_source_name(self) -> str:
        return "park4night"

    def get_source_query(self) -> str:
        """
        SQL query to fetch data from Scraparr's Park4Night scraper_1 schema.
        Includes:
        - Multilingual descriptions from place_descriptions table (en, nl, fr, de, es, it)
        - Photos as JSONB array with link_large and link_thumb URLs
        - description_en column for direct English description access
        - Rating (note_moyenne stored as 'rating')
        """
        return """
            SELECT
                p.id,
                p.nom as name,
                p.latitude,
                p.longitude,
                p.pays as country,
                p.rating,
                p.photos,
                p.description,
                p.description_en,
                p.ville as city,
                p.prix as price_info,
                p.type as location_type_raw,
                p.services,
                p.nb_comment,
                p.updated_at,
                p.scraped_at,
                -- Aggregate all language descriptions as JSON (en, nl, fr, de, es, it)
                COALESCE(
                    json_object_agg(
                        pd.language_code,
                        pd.description
                    ) FILTER (WHERE pd.language_code IS NOT NULL),
                    '{}'::json
                ) as descriptions_json
            FROM scraper_1.places p
            LEFT JOIN scraper_1.place_descriptions pd ON p.id = pd.place_id
            GROUP BY p.id, p.nom, p.latitude, p.longitude, p.pays, p.rating, p.photos,
                     p.description, p.description_en, p.ville, p.prix, p.type, p.services,
                     p.nb_comment, p.updated_at, p.scraped_at
            ORDER BY p.id
        """

    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Scraparr Park4Night row to TripFlow Location format.

        Handles:
        - Location type mapping (Park4Night codes to TripFlow types)
        - Amenities extraction from services JSON
        - Photos as JSONB array with link_large/link_thumb URLs
        - Price parsing
        - Multilingual descriptions (en, nl, fr, de, es, it)
        """
        # Map Park4Night type codes to LocationType
        type_mapping = {
            # Parking types
            'PJ': LocationType.PARKING,  # Parking jour et nuit
            'PG': LocationType.PARKING,  # Parking gratuit
            'PP': LocationType.PARKING,  # Parking payant
            'PARKING PAYANT JOUR ET NUIT': LocationType.PARKING,
            'PARKING GRATUIT': LocationType.PARKING,
            # Service areas
            'AS': LocationType.SERVICE_AREA,  # Aire de services
            'AIRE DE SERVICE': LocationType.SERVICE_AREA,
            'AIRE DE PIQUE-NIQUE': LocationType.REST_AREA,
            # Camping
            'CA': LocationType.CAMPSITE,  # Camping
            'CM': LocationType.CAMPSITE,  # Camping municipal
            'CP': LocationType.CAMPSITE,  # Camping privé
            'CAMPING': LocationType.CAMPSITE,
            'CAMPING MUNICIPAL': LocationType.CAMPSITE,
            'CAMPING PRIVE': LocationType.CAMPSITE,
            'CAMPING-CAR PARK': LocationType.PARKING,
            # Other
            'FE': LocationType.POI,  # Ferme
            'FERME': LocationType.POI,
            'PV': LocationType.ATTRACTION,  # Point de vue
            'POINT DE VUE': LocationType.ATTRACTION,
            'LI': LocationType.ATTRACTION,  # Lieu insolite
            'LIEU INSOLITE': LocationType.ATTRACTION,
            'ZN': LocationType.POI,  # Zone naturelle
            'ZONE NATURELLE': LocationType.POI,
        }

        raw_type = row.get("location_type_raw", "")
        location_type = type_mapping.get(
            raw_type.upper() if raw_type else "",
            LocationType.PARKING  # default
        )

        # Build amenities list from services JSON field
        amenities = []
        services = row.get("services")
        if services:
            if isinstance(services, dict):
                # Services is a JSON object with boolean values
                service_mapping = {
                    'wifi': 'wifi',
                    'internet': 'wifi',
                    'electricity': 'electricity',
                    'electricite': 'electricity',
                    'water': 'water',
                    'eau': 'water',
                    'point_eau': 'water',
                    'waste_disposal': 'waste_disposal',
                    'eau_noire': 'waste_disposal',
                    'toilet': 'toilet',
                    'wc_public': 'toilet',
                    'shower': 'shower',
                    'douche': 'shower',
                    'pets_allowed': 'pets_allowed',
                    'animaux': 'pets_allowed',
                }
                for service_key, amenity_name in service_mapping.items():
                    if services.get(service_key) and amenity_name not in amenities:
                        amenities.append(amenity_name)
            elif isinstance(services, list):
                # Services is a list of service names
                for service in services:
                    if isinstance(service, str):
                        service_lower = service.lower()
                        if 'wifi' in service_lower or 'internet' in service_lower:
                            if 'wifi' not in amenities:
                                amenities.append('wifi')
                        if 'electric' in service_lower:
                            if 'electricity' not in amenities:
                                amenities.append('electricity')
                        if 'water' in service_lower or 'eau' in service_lower:
                            if 'water' not in amenities:
                                amenities.append('water')
                        if 'wc' in service_lower or 'toilet' in service_lower:
                            if 'toilet' not in amenities:
                                amenities.append('toilet')
                        if 'shower' in service_lower or 'douche' in service_lower:
                            if 'shower' not in amenities:
                                amenities.append('shower')

        # Handle images - photos is now a JSONB array with link_large/link_thumb
        images = []
        main_image = None
        photos = row.get("photos")
        if photos:
            if isinstance(photos, list):
                # JSONB array format: [{"id": "...", "link_large": "...", "link_thumb": "..."}]
                for photo in photos:
                    if isinstance(photo, dict):
                        # Prefer link_large, fallback to link_thumb
                        url = photo.get("link_large") or photo.get("link_thumb")
                        if url:
                            images.append({
                                "url": url,
                                "thumbnail": photo.get("link_thumb"),
                                "type": "photo"
                            })
                if images:
                    main_image = images[0]["url"]
            elif isinstance(photos, str):
                # Legacy format: comma-separated URLs
                photo_urls = [url.strip() for url in photos.split(',') if url.strip()]
                images = [{"url": url, "type": "photo"} for url in photo_urls]
                if images:
                    main_image = images[0]["url"]

        # Determine price type from prix field
        price_type = "unknown"
        price_min = None
        price_max = None

        if row.get("price_info"):
            price_str = str(row["price_info"]).lower()
            if 'gratuit' in price_str or 'free' in price_str or 'gratis' in price_str or price_str == '0':
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

        # Build features/tags list
        tags = []
        features = []

        # Use English description as primary, fallback to description field
        # Priority: English > French > Dutch > generic description
        descriptions_json = row.get("descriptions_json", {})
        if isinstance(descriptions_json, str):
            try:
                descriptions_json = json.loads(descriptions_json)
            except:
                descriptions_json = {}

        primary_description = (
            row.get("description_en") or
            descriptions_json.get("en") or
            descriptions_json.get("fr") or
            descriptions_json.get("nl") or
            row.get("description")
        )

        # Create the transformed data
        return {
            "external_id": f"park4night_{row.get('id')}",
            "name": row.get("name") or f"Park4Night Location {row.get('id')}",
            "description": primary_description,  # Primary description (en > fr > nl > fallback)
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
            "review_count": row.get("nb_comment") or 0,
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
                "park4night_id": row.get("id"),
                "location_type_raw": row.get("location_type_raw"),
                "services": row.get("services"),
                "scraped_at": row.get("scraped_at").isoformat() if row.get("scraped_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
                # Note: Multilingual descriptions (en, nl, fr, de, es, it) stored in location_translations table
                # Note: Photos stored in images field with link_large and link_thumb URLs
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