from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from geopy.distance import geodesic
import logging

from app.models import Location, LocationType

logger = logging.getLogger(__name__)


class LocationService:
    """Service for location-related operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Get location by ID"""
        return self.db.query(Location).filter(Location.id == location_id).first()

    def search_locations(
        self,
        query: Optional[str] = None,
        location_types: Optional[List[LocationType]] = None,
        amenities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20,
    ) -> List[Location]:
        """
        Search locations with various filters.

        Args:
            query: Text search in name and description
            location_types: Filter by location types
            amenities: Required amenities
            tags: Required tags
            min_rating: Minimum rating
            max_price: Maximum price
            limit: Maximum results

        Returns:
            List of matching locations
        """
        q = self.db.query(Location).filter(Location.active == True)

        # Text search
        if query:
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    Location.name.ilike(search_term),
                    Location.description.ilike(search_term),
                    Location.city.ilike(search_term),
                )
            )

        # Filter by location type
        if location_types:
            q = q.filter(Location.location_type.in_(location_types))

        # Filter by amenities
        if amenities:
            for amenity in amenities:
                q = q.filter(Location.amenities.contains([amenity]))

        # Filter by tags
        if tags:
            for tag in tags:
                q = q.filter(Location.tags.contains([tag]))

        # Filter by rating
        if min_rating is not None:
            q = q.filter(Location.rating >= min_rating)

        # Filter by price
        if max_price is not None:
            q = q.filter(Location.price <= max_price)

        return q.limit(limit).all()

    def find_nearby_locations(
        self,
        latitude: float,
        longitude: float,
        radius_km: int = 50,
        location_types: Optional[List[LocationType]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Find locations within radius of a point.

        Uses PostGIS for efficient geospatial queries.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            location_types: Optional filter by location types
            limit: Maximum results

        Returns:
            List of locations with distance information
        """
        # PostGIS query using ST_DWithin
        # Note: ST_DWithin uses meters for geography type
        radius_meters = radius_km * 1000

        q = self.db.query(
            Location,
            func.ST_Distance(
                Location.geom,
                func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            ).label("distance_meters")
        ).filter(
            and_(
                Location.active == True,
                func.ST_DWithin(
                    func.cast(Location.geom, "geography"),
                    func.cast(
                        func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                        "geography"
                    ),
                    radius_meters
                )
            )
        )

        if location_types:
            q = q.filter(Location.location_type.in_(location_types))

        # Order by distance
        q = q.order_by("distance_meters")

        results = q.limit(limit).all()

        return [
            {
                "location": location,
                "distance_km": distance_meters / 1000,
            }
            for location, distance_meters in results
        ]

    def find_locations_along_route(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        corridor_width_km: int = 20,
        location_types: Optional[List[LocationType]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Find locations along a route (corridor).

        Creates a buffer around the straight line between start and end points.

        Args:
            start_lat: Start latitude
            start_lng: Start longitude
            end_lat: End latitude
            end_lng: End longitude
            corridor_width_km: Width of corridor in km
            location_types: Optional filter by types
            limit: Maximum results

        Returns:
            List of locations along the route
        """
        corridor_width_meters = corridor_width_km * 1000

        # Create a line from start to end
        line = func.ST_MakeLine(
            func.ST_SetSRID(func.ST_MakePoint(start_lng, start_lat), 4326),
            func.ST_SetSRID(func.ST_MakePoint(end_lng, end_lat), 4326),
        )

        # Find locations within buffer of the line
        q = self.db.query(
            Location,
            func.ST_Distance(
                func.cast(Location.geom, "geography"),
                func.cast(line, "geography")
            ).label("distance_from_route")
        ).filter(
            and_(
                Location.active == True,
                func.ST_DWithin(
                    func.cast(Location.geom, "geography"),
                    func.cast(line, "geography"),
                    corridor_width_meters
                )
            )
        )

        if location_types:
            q = q.filter(Location.location_type.in_(location_types))

        # Order by distance from start
        start_point = func.ST_SetSRID(func.ST_MakePoint(start_lng, start_lat), 4326)
        q = q.order_by(
            func.ST_Distance(
                func.cast(Location.geom, "geography"),
                func.cast(start_point, "geography")
            )
        )

        results = q.limit(limit).all()

        return [
            {
                "location": location,
                "distance_from_route_km": distance / 1000,
            }
            for location, distance in results
        ]

    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode an address to coordinates.

        Uses geopy's Nominatim (OpenStreetMap).

        Args:
            address: Address string

        Returns:
            Dictionary with latitude and longitude, or None if not found
        """
        from geopy.geocoders import Nominatim
        from app.core.config import settings

        geolocator = Nominatim(user_agent=settings.NOMINATIM_USER_AGENT)

        try:
            location = geolocator.geocode(address)
            if location:
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "display_name": location.address,
                }
            return None

        except Exception as e:
            logger.error(f"Geocoding failed for address '{address}': {e}")
            return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Reverse geocode coordinates to address.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Address string or None
        """
        from geopy.geocoders import Nominatim
        from app.core.config import settings

        geolocator = Nominatim(user_agent=settings.NOMINATIM_USER_AGENT)

        try:
            location = geolocator.reverse((latitude, longitude))
            if location:
                return location.address
            return None

        except Exception as e:
            logger.error(f"Reverse geocoding failed for ({latitude}, {longitude}): {e}")
            return None
