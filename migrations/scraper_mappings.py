#!/usr/bin/env python3
"""
Scraper Mapping Configuration for Tripflow Migration

This module defines how each scraper's data maps to the Tripflow schema.
Add new scrapers here as they're added to the scraparr system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import re

class DataType(Enum):
    """Types of data that scrapers can provide"""
    LOCATION = "location"  # Camping spots, parking, POIs
    EVENT = "event"        # Time-based events
    REVIEW = "review"      # User reviews
    COMBINED = "combined"  # Both location and event (like UiT)

class ScraperMapping:
    """Base class for scraper-specific mappings"""

    def __init__(self):
        self.scraper_id: int = None
        self.scraper_name: str = None
        self.schema_name: str = None
        self.data_type: DataType = None
        self.source_name: str = None  # For tripflow.location_source enum

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map scraper row to tripflow.locations format"""
        raise NotImplementedError

    def map_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map scraper row to tripflow.events format"""
        raise NotImplementedError

    def get_query(self) -> str:
        """Get SQL query to fetch data from scraper schema"""
        raise NotImplementedError


class Park4NightMapping(ScraperMapping):
    """Mapping for Park4Night camping/parking locations"""

    def __init__(self):
        super().__init__()
        self.scraper_id = 1
        self.scraper_name = "Park4Night Grid Scraper"
        self.schema_name = "scraper_1"
        self.data_type = DataType.LOCATION
        self.source_name = "park4night"

    def get_query(self) -> str:
        return f"""
            SELECT * FROM {self.schema_name}.places
            ORDER BY id
        """

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map Park4Night place to tripflow location"""

        # Map location type
        location_type = self._map_location_type(row.get('type_de_lieu'))

        # Parse amenities
        amenities = self._parse_amenities(row)

        # Parse pricing
        price_type, price_min, price_max = self._parse_pricing(row.get('tarif'))

        # Parse images
        images, main_image = self._parse_images(row.get('photos'))

        # Parse tags
        tags = self._parse_tags(row.get('etiquettes'))

        return {
            "external_id": f"park4night_{row['id']}",
            "source": "park4night",
            "source_url": f"https://park4night.com/lieu/{row['id']}",
            "name": row.get('nom', f"Location {row['id']}")[:500],
            "description": row.get('description'),
            "location_type": location_type,
            "latitude": float(row['latitude']) if row.get('latitude') else None,
            "longitude": float(row['longitude']) if row.get('longitude') else None,
            "city": row.get('ville'),
            "country": row.get('pays'),
            "rating": float(row['note']) if row.get('note') else None,
            "price_type": price_type,
            "price_min": price_min,
            "price_max": price_max,
            "price_info": row.get('tarif'),
            "amenities": amenities,
            "tags": tags,
            "images": images,
            "main_image_url": main_image,
            "is_active": True
        }

    def _map_location_type(self, type_de_lieu: str) -> str:
        """Map Park4Night types to Tripflow location types"""
        if not type_de_lieu:
            return 'PARKING'

        type_upper = type_de_lieu.upper()
        if 'PARKING' in type_upper:
            return 'PARKING'
        elif 'AIRE DE SERVICE' in type_upper:
            return 'SERVICE_AREA'
        elif 'AIRE DE PIQUE' in type_upper or 'AIRE DE REPOS' in type_upper:
            return 'REST_AREA'
        elif 'CAMPING' in type_upper:
            return 'CAMPSITE'
        elif 'FERME' in type_upper:
            return 'POI'
        elif 'VUE' in type_upper or 'LIEU INSOLITE' in type_upper:
            return 'ATTRACTION'
        else:
            return 'PARKING'

    def _parse_amenities(self, row: dict) -> list:
        """Extract amenities from Park4Night fields"""
        amenities = []
        if row.get('internet'):
            amenities.append('wifi')
        if row.get('electricite'):
            amenities.append('electricity')
        if row.get('eau_noire'):
            amenities.append('waste_disposal')
        if row.get('camping_car_park'):
            amenities.append('motorhome_parking')
        if row.get('animaux_acceptes'):
            amenities.append('pets_allowed')
        return amenities

    def _parse_pricing(self, tarif: str) -> tuple:
        """Parse pricing information"""
        if not tarif:
            return ('unknown', None, None)

        tarif_lower = str(tarif).lower()
        if 'gratuit' in tarif_lower or 'free' in tarif_lower or tarif == '0':
            return ('free', 0, 0)
        elif 'donation' in tarif_lower:
            return ('donation', None, None)
        else:
            # Try to extract numbers
            numbers = re.findall(r'\d+\.?\d*', str(tarif))
            if numbers:
                prices = [float(n) for n in numbers]
                return ('paid', min(prices), max(prices) if len(prices) > 1 else min(prices))

        return ('unknown', None, None)

    def _parse_images(self, photos: str) -> tuple:
        """Parse photo URLs"""
        images = []
        main_image = None

        if photos:
            if isinstance(photos, str):
                photo_urls = [url.strip() for url in photos.split(',') if url.strip()]
                images = [{"url": url, "type": "photo"} for url in photo_urls]
                if images:
                    main_image = images[0]["url"]

        return (images, main_image)

    def _parse_tags(self, etiquettes: str) -> list:
        """Parse tags from etiquettes field"""
        if not etiquettes:
            return []
        return [tag.strip() for tag in etiquettes.split(',') if tag.strip()]


class UiTinVlaanderenMapping(ScraperMapping):
    """Mapping for UiT in Vlaanderen cultural events"""

    def __init__(self):
        super().__init__()
        self.scraper_id = 2
        self.scraper_name = "UiTinVlaanderen Events"
        self.schema_name = "scraper_2"
        self.data_type = DataType.COMBINED  # Creates both location and event
        self.source_name = "uitinvlaanderen"

    def get_query(self) -> str:
        return f"""
            SELECT * FROM {self.schema_name}.events
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY id
        """

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map UiT event venue to tripflow location"""
        location_name = row.get('location_name') or row.get('name')

        return {
            "external_id": f"uit_location_{row['event_id']}",
            "source": "uitinvlaanderen",
            "source_url": row.get('url'),
            "name": location_name[:500],
            "description": None,  # Event description goes in event record
            "location_type": "EVENT",
            "latitude": float(row['latitude']),
            "longitude": float(row['longitude']),
            "address": row.get('street_address'),
            "city": row.get('city'),
            "postal_code": row.get('postal_code'),
            "country": row.get('country', 'Belgium'),
            "country_code": 'BE',
            "is_active": True
        }

    def map_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map UiT event to tripflow event"""
        themes = []
        if row.get('themes'):
            themes = row['themes'].split(',') if isinstance(row['themes'], str) else row['themes']

        return {
            "external_id": row['event_id'],
            "source": "uitinvlaanderen",
            "name": row['name'][:500],
            "description": row.get('description'),
            "event_type": row.get('event_type'),
            "start_date": row.get('start_date'),
            "end_date": row.get('end_date'),
            "organizer": row.get('organizer'),
            "themes": themes
        }


class EventbriteMapping(ScraperMapping):
    """Mapping for Eventbrite events"""

    def __init__(self):
        super().__init__()
        self.scraper_id = 3
        self.scraper_name = "Eventbrite Events Scraper"
        self.schema_name = "scraper_3"
        self.data_type = DataType.COMBINED  # Creates both location and event
        self.source_name = "other"  # Eventbrite not in enum yet, using 'other'

    def get_query(self) -> str:
        return f"""
            SELECT * FROM {self.schema_name}.events
            ORDER BY id
        """

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map Eventbrite venue to tripflow location"""
        # Venue name might be in venue_name or location field
        venue_name = row.get('venue_name') or row.get('location') or f"Venue for {row.get('name', 'Event')}"

        # For now, Eventbrite doesn't have coordinates - we'll geocode later
        # Still valuable for text search and event information
        return {
            "external_id": f"eventbrite_venue_{row.get('event_id', row.get('id'))}",
            "source": "other",  # Using 'other' until we add eventbrite to enum
            "source_url": row.get('url'),
            "name": venue_name[:500] if venue_name else "Unknown Venue",
            "description": None,
            "location_type": "EVENT",
            "latitude": None,  # No coordinates in Eventbrite data yet
            "longitude": None,  # Will add geocoding later
            "address": row.get('location'),  # Full address string
            "city": row.get('city'),
            "postal_code": None,
            "country": row.get('country'),
            "country_code": row.get('country_code') or self._get_country_code(row.get('country')),
            "is_active": True
        }

    def map_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map Eventbrite event to tripflow event"""
        # Parse categories/themes
        themes = []
        if row.get('category'):
            themes.append(row['category'])
        if row.get('subcategory'):
            themes.append(row['subcategory'])
        if row.get('tags'):
            if isinstance(row['tags'], str):
                themes.extend([t.strip() for t in row['tags'].split(',') if t.strip()])
            elif isinstance(row['tags'], list):
                themes.extend(row['tags'])

        # Parse pricing
        price_min = None
        price_max = None
        if row.get('price'):
            try:
                price_min = float(row['price'])
                price_max = price_min
            except:
                pass
        elif row.get('price_min'):
            price_min = float(row['price_min']) if row.get('price_min') else None
            price_max = float(row['price_max']) if row.get('price_max') else price_min

        # Handle unparseable dates
        # Eventbrite stores dates as strings like "Tomorrow • 11:00 PM"
        # which can't be parsed. Set to None and include in description.
        raw_start_date = row.get('start_date') or row.get('start_datetime')
        description = row.get('description') or ''
        if raw_start_date and not description:
            description = f"Event time: {raw_start_date}"
        elif raw_start_date and description:
            description = f"Event time: {raw_start_date}\n\n{description}"

        return {
            "external_id": row.get('event_id') or str(row.get('id')),
            "source": "other",  # Using 'other' until we add eventbrite to enum
            "name": row.get('name', 'Untitled Event')[:500],
            "description": description,
            "event_type": row.get('event_type') or row.get('category') or 'Other',
            "start_date": None,  # Can't parse "Tomorrow • 11:00 PM" format
            "end_date": None,
            "organizer": row.get('organizer') or row.get('organizer_name'),
            "themes": themes,
            "capacity": row.get('capacity'),
            "booking_url": row.get('url') or row.get('event_url'),
            "price_min": price_min,
            "price_max": price_max,
            "is_sold_out": row.get('is_sold_out', False)
        }

    def _get_country_code(self, country: str) -> str:
        """Map country name to ISO code"""
        country_codes = {
            'Belgium': 'BE',
            'France': 'FR',
            'Germany': 'DE',
            'Netherlands': 'NL',
            'United Kingdom': 'GB',
            'Spain': 'ES',
            'Italy': 'IT',
            'Portugal': 'PT',
            # Add more as needed
        }
        return country_codes.get(country, '')


class TicketmasterMapping(ScraperMapping):
    """Mapping for Ticketmaster events"""

    def __init__(self):
        super().__init__()
        self.scraper_id = 4
        self.scraper_name = "Ticketmaster Events"
        self.schema_name = "scraper_4"
        self.data_type = DataType.COMBINED  # Creates both location and event
        self.source_name = "other"  # Ticketmaster not in enum yet, using 'other'

    def get_query(self) -> str:
        return f"""
            SELECT * FROM {self.schema_name}.events
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY id
        """

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map Ticketmaster venue to tripflow location"""
        venue_name = row.get('venue_name') or f"Venue {row.get('venue_id', 'Unknown')}"

        return {
            "external_id": f"ticketmaster_venue_{row.get('venue_id', row.get('id'))}",
            "source": "other",
            "source_url": row.get('url'),
            "name": venue_name[:500] if venue_name else "Unknown Venue",
            "description": None,
            "location_type": "EVENT",
            "latitude": float(row['latitude']) if row.get('latitude') else None,
            "longitude": float(row['longitude']) if row.get('longitude') else None,
            "address": row.get('venue_address'),
            "city": row.get('city'),
            "postal_code": row.get('postal_code'),
            "country": row.get('country'),
            "country_code": row.get('country_code'),
            "is_active": True
        }

    def map_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map Ticketmaster event to tripflow event"""
        # Parse themes from genre and segment
        themes = []
        if row.get('genre'):
            themes.append(row['genre'])
        if row.get('segment'):
            themes.append(row['segment'])

        # Parse classifications if available
        if row.get('classifications'):
            # classifications is text field, might need parsing
            pass

        return {
            "external_id": row.get('event_id') or str(row.get('id')),
            "source": "other",
            "name": row.get('name', 'Untitled Event')[:500],
            "description": row.get('description') or row.get('info'),
            "event_type": row.get('genre') or row.get('segment') or 'Other',
            "start_date": row.get('start_date'),
            "end_date": None,  # Ticketmaster doesn't provide end date
            "organizer": row.get('promoter_name'),
            "themes": themes,
            "booking_url": row.get('url'),
            "price_min": row.get('price_min'),
            "price_max": row.get('price_max'),
            "is_cancelled": row.get('status_code') == 'cancelled'
        }


class CamperContactMapping(ScraperMapping):
    """Mapping for CamperContact camping/parking locations"""

    def __init__(self):
        super().__init__()
        self.scraper_id = 5
        self.scraper_name = "CamperContact Grid Scraper"
        self.schema_name = "scraper_5"
        self.data_type = DataType.LOCATION
        self.source_name = "other"  # CamperContact not in enum yet, using 'other'

    def get_query(self) -> str:
        return f"""
            SELECT * FROM {self.schema_name}.places
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY id
        """

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map CamperContact place to tripflow location"""

        # Parse raw_data JSON if available
        raw_data = row.get('raw_data', {})
        if isinstance(raw_data, str):
            import json
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}

        # Map location type
        place_type = row.get('type', '').lower()
        location_type = 'CAMPSITE' if 'camper' in place_type else 'PARKING'

        # Build name from data
        sitecode = row.get('sitecode')
        name = f"CamperContact #{sitecode}" if sitecode else f"CamperContact {row.get('poi_id', row['id'])}"

        # Build source URL
        source_url = f"https://www.campercontact.com/en/campsite/{sitecode}" if sitecode else None

        # Parse features
        features = []
        if row.get('is_bookable'):
            features.append('bookable')
        if row.get('is_claimed'):
            features.append('verified')

        return {
            "external_id": f"campercontact_{row.get('poi_id', row['id'])}",
            "source": "other",
            "source_url": source_url,
            "name": name[:500],
            "description": None,
            "location_type": location_type,
            "latitude": float(row['latitude']) if row.get('latitude') else None,
            "longitude": float(row['longitude']) if row.get('longitude') else None,
            "address": None,
            "city": None,
            "postal_code": None,
            "country": None,
            "country_code": None,
            "rating": None,
            "price_type": 'unknown',
            "price_min": None,
            "price_max": None,
            "amenities": [],
            "features": features,
            "tags": [place_type] if place_type else [],
            "images": [],
            "main_image_url": None,
            "is_active": True,
            "raw_data": raw_data
        }


# Registry of all scraper mappings
SCRAPER_REGISTRY = {
    1: Park4NightMapping(),      # scraper_1: Park4Night places
    2: UiTinVlaanderenMapping(), # scraper_2: UiT events
    3: EventbriteMapping(),      # scraper_3: Eventbrite events
    4: TicketmasterMapping(),    # scraper_4: Ticketmaster events
    5: CamperContactMapping(),   # scraper_5: CamperContact places
    # Add new scrapers here as they're added to scraparr
}

# Easy lookup by schema name
SCHEMA_REGISTRY = {
    'scraper_1': Park4NightMapping(),
    'scraper_2': UiTinVlaanderenMapping(),
    'scraper_3': EventbriteMapping(),
    'scraper_4': TicketmasterMapping(),
    'scraper_5': CamperContactMapping(),
}


def get_scraper_mapping(scraper_id: Optional[int] = None, schema_name: Optional[str] = None) -> ScraperMapping:
    """Get the appropriate scraper mapping by ID or schema name"""
    if scraper_id:
        return SCRAPER_REGISTRY.get(scraper_id)
    elif schema_name:
        return SCHEMA_REGISTRY.get(schema_name)
    return None


def add_new_scraper_mapping(scraper_id: int, mapping: ScraperMapping):
    """Add a new scraper mapping to the registry"""
    SCRAPER_REGISTRY[scraper_id] = mapping
    if mapping.schema_name:
        SCHEMA_REGISTRY[mapping.schema_name] = mapping


# Template for adding new scrapers:
"""
class NewScraperMapping(ScraperMapping):
    def __init__(self):
        super().__init__()
        self.scraper_id = X
        self.scraper_name = "New Scraper Name"
        self.schema_name = "scraper_X"
        self.data_type = DataType.LOCATION  # or EVENT or COMBINED
        self.source_name = "newsource"  # Add to tripflow enum if needed

    def get_query(self) -> str:
        return f"SELECT * FROM {self.schema_name}.your_table ORDER BY id"

    def map_to_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Map to tripflow.locations format
        pass

    def map_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Map to tripflow.events format
        pass

# Then add to registry:
SCRAPER_REGISTRY[X] = NewScraperMapping()
SCHEMA_REGISTRY['scraper_X'] = NewScraperMapping()
"""