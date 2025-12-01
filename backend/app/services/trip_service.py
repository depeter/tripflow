from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from geopy.distance import geodesic
import logging

from app.models import Trip, TripStatus, Location, LocationType
from app.services.location_service import LocationService
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class TripPlanningService:
    """Service for trip planning and route optimization"""

    def __init__(self, db: Session):
        self.db = db
        self.location_service = LocationService(db)
        self.recommendation_service = RecommendationService(db)

    def create_trip(
        self,
        user_id: int,
        start_address: str,
        end_address: Optional[str] = None,
        max_distance_km: Optional[int] = None,
        duration_days: Optional[int] = None,
        trip_preferences: Optional[Dict[str, Any]] = None,
    ) -> Trip:
        """
        Create a new trip.

        Args:
            user_id: User ID
            start_address: Starting address
            end_address: Optional ending address (None for round trips)
            max_distance_km: Maximum total distance
            duration_days: Expected duration in days
            trip_preferences: Trip-specific preferences

        Returns:
            Created trip object
        """
        # Geocode start address
        start_coords = self.location_service.geocode_address(start_address)
        if not start_coords:
            raise ValueError(f"Could not geocode start address: {start_address}")

        # Geocode end address if provided
        end_coords = None
        if end_address:
            end_coords = self.location_service.geocode_address(end_address)
            if not end_coords:
                raise ValueError(f"Could not geocode end address: {end_address}")

        # Create trip
        trip = Trip(
            user_id=user_id,
            status=TripStatus.PLANNING,
            start_address=start_address,
            start_latitude=start_coords["latitude"],
            start_longitude=start_coords["longitude"],
            end_address=end_address if end_coords else None,
            end_latitude=end_coords["latitude"] if end_coords else None,
            end_longitude=end_coords["longitude"] if end_coords else None,
            max_distance_km=max_distance_km,
            duration_days=duration_days,
            trip_preferences=trip_preferences or {},
        )

        self.db.add(trip)
        self.db.commit()
        self.db.refresh(trip)

        logger.info(f"Created trip {trip.id} for user {user_id}")
        return trip

    def suggest_waypoints(
        self,
        trip_id: int,
        num_stops: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Suggest waypoints for a trip based on route and user preferences.

        Args:
            trip_id: Trip ID
            num_stops: Number of stops to suggest

        Returns:
            List of suggested locations with metadata
        """
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        # Determine route parameters
        if trip.end_latitude and trip.end_longitude:
            # Point-to-point trip
            route_distance = geodesic(
                (trip.start_latitude, trip.start_longitude),
                (trip.end_latitude, trip.end_longitude)
            ).kilometers

            # Find locations along the route
            locations_along_route = self.location_service.find_locations_along_route(
                start_lat=trip.start_latitude,
                start_lng=trip.start_longitude,
                end_lat=trip.end_latitude,
                end_lng=trip.end_longitude,
                corridor_width_km=30,  # 30km corridor on each side
                limit=50,
            )

            # Get personalized recommendations from those locations
            candidates = []
            for item in locations_along_route:
                location = item["location"]

                # Calculate score based on:
                # - User preferences (via recommendation service)
                # - Distance from route (prefer closer)
                # - Location rating
                # - Distribution along route

                distance_score = 1.0 / (1.0 + item["distance_from_route_km"])
                rating_score = (location.rating or 3.0) / 5.0

                # Get position along route (0 = start, 1 = end)
                dist_from_start = geodesic(
                    (trip.start_latitude, trip.start_longitude),
                    (location.latitude, location.longitude)
                ).kilometers
                position_ratio = dist_from_start / route_distance if route_distance > 0 else 0

                candidates.append({
                    "location": location,
                    "distance_from_route_km": item["distance_from_route_km"],
                    "distance_from_start_km": dist_from_start,
                    "position_ratio": position_ratio,
                    "distance_score": distance_score,
                    "rating_score": rating_score,
                    "combined_score": 0.5 * distance_score + 0.5 * rating_score,
                })

            # Select stops distributed along the route
            candidates.sort(key=lambda x: x["combined_score"], reverse=True)

            # Ensure good distribution - divide route into segments
            suggestions = []
            for i in range(num_stops):
                target_position = (i + 1) / (num_stops + 1)  # Evenly space stops

                # Find best location near this position
                best = min(
                    candidates,
                    key=lambda x: abs(x["position_ratio"] - target_position)
                )

                suggestions.append(best)
                candidates.remove(best)  # Don't suggest same location twice

            return suggestions

        else:
            # Round trip from start point
            max_radius = trip.max_distance_km // 2 if trip.max_distance_km else 100

            # Get recommendations near start point
            recommendations = self.recommendation_service.recommend_locations(
                user_id=trip.user_id,
                near_latitude=trip.start_latitude,
                near_longitude=trip.start_longitude,
                radius_km=max_radius,
                limit=num_stops * 3,
            )

            # Select top-rated locations with good distribution
            suggestions = []
            for rec in recommendations[:num_stops]:
                suggestions.append({
                    "location": rec["location"],
                    "score": rec["score"],
                    "distance_km": rec.get("distance_km", 0),
                })

            return suggestions

    def add_waypoint(
        self,
        trip_id: int,
        location_id: int,
        order: Optional[int] = None,
    ) -> Trip:
        """
        Add a waypoint to a trip.

        Args:
            trip_id: Trip ID
            location_id: Location ID
            order: Optional order (if None, appends to end)

        Returns:
            Updated trip
        """
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise ValueError(f"Location {location_id} not found")

        # Initialize waypoints if needed
        if trip.waypoints is None:
            trip.waypoints = []

        # Determine order
        if order is None:
            order = len(trip.waypoints)

        # Add waypoint
        waypoint = {
            "location_id": location_id,
            "order": order,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

        trip.waypoints.append(waypoint)

        # Re-sort waypoints by order
        trip.waypoints = sorted(trip.waypoints, key=lambda x: x["order"])

        self.db.commit()
        self.db.refresh(trip)

        logger.info(f"Added waypoint {location_id} to trip {trip_id}")
        return trip

    def remove_waypoint(self, trip_id: int, location_id: int) -> Trip:
        """Remove a waypoint from a trip"""
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        if trip.waypoints:
            trip.waypoints = [
                wp for wp in trip.waypoints
                if wp["location_id"] != location_id
            ]

            # Re-order
            for i, wp in enumerate(trip.waypoints):
                wp["order"] = i

        self.db.commit()
        self.db.refresh(trip)

        logger.info(f"Removed waypoint {location_id} from trip {trip_id}")
        return trip

    def calculate_trip_stats(self, trip_id: int) -> Dict[str, Any]:
        """
        Calculate trip statistics (total distance, estimated time, etc.)

        Args:
            trip_id: Trip ID

        Returns:
            Dictionary with trip statistics
        """
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        if not trip.waypoints:
            return {
                "total_distance_km": 0,
                "num_stops": 0,
                "estimated_driving_hours": 0,
                "estimated_driving_days": 0,
            }

        # Calculate total distance
        points = [(trip.start_latitude, trip.start_longitude)]

        for waypoint in trip.waypoints:
            points.append((waypoint["latitude"], waypoint["longitude"]))

        if trip.end_latitude and trip.end_longitude:
            points.append((trip.end_latitude, trip.end_longitude))
        else:
            # Round trip - return to start
            points.append((trip.start_latitude, trip.start_longitude))

        total_distance = 0
        for i in range(len(points) - 1):
            distance = geodesic(points[i], points[i + 1]).kilometers
            total_distance += distance

        # Estimate driving time (assume 80 km/h average)
        estimated_hours = total_distance / 80

        return {
            "total_distance_km": round(total_distance, 2),
            "num_stops": len(trip.waypoints),
            "estimated_driving_hours": round(estimated_hours, 2),
            "estimated_driving_days": round(estimated_hours / 6, 1),  # 6 hours driving per day
        }

    def finalize_trip(self, trip_id: int, start_date: datetime) -> Trip:
        """
        Finalize trip planning and set it to active.

        Args:
            trip_id: Trip ID
            start_date: Trip start date

        Returns:
            Updated trip
        """
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        stats = self.calculate_trip_stats(trip_id)

        trip.status = TripStatus.ACTIVE
        trip.start_date = start_date
        trip.end_date = start_date + timedelta(days=stats["estimated_driving_days"])

        self.db.commit()
        self.db.refresh(trip)

        logger.info(f"Finalized trip {trip_id}")
        return trip

    def delete_trip(self, trip_id: int, user_id: int) -> bool:
        """
        Delete a trip.

        Args:
            trip_id: Trip ID
            user_id: User ID (to verify ownership)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If trip not found or user doesn't own it
        """
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        if trip.user_id != user_id:
            raise ValueError("Not authorized to delete this trip")

        self.db.delete(trip)
        self.db.commit()

        logger.info(f"Deleted trip {trip_id}")
        return True
