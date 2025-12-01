from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db_sync
from app.services.trip_service import TripPlanningService
from app.api.schemas import (
    TripCreate,
    TripResponse,
    WaypointAdd,
    TripFinalize,
    TripStats,
    WaypointSuggestionParams,
    LocationWithDistance,
)

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/", response_model=TripResponse)
def create_trip(trip_data: TripCreate, user_id: int = 1, db: Session = Depends(get_db_sync)):
    """
    Create a new trip.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    service = TripPlanningService(db)

    try:
        trip = service.create_trip(
            user_id=user_id,
            start_address=trip_data.start_address,
            end_address=trip_data.end_address,
            max_distance_km=trip_data.max_distance_km,
            duration_days=trip_data.duration_days,
            trip_preferences=trip_data.trip_preferences,
        )
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db_sync)):
    """Get trip by ID"""
    from app.models import Trip

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


@router.get("/", response_model=List[TripResponse])
def list_trips(user_id: int = 1, db: Session = Depends(get_db_sync)):
    """
    List all trips for a user.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    from app.models import Trip

    trips = db.query(Trip).filter(Trip.user_id == user_id).all()
    return trips


@router.post("/{trip_id}/waypoints", response_model=TripResponse)
def add_waypoint(trip_id: int, waypoint: WaypointAdd, db: Session = Depends(get_db_sync)):
    """Add a waypoint to a trip"""
    service = TripPlanningService(db)

    try:
        trip = service.add_waypoint(
            trip_id=trip_id,
            location_id=waypoint.location_id,
            order=waypoint.order,
        )
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trip_id}/waypoints/{location_id}", response_model=TripResponse)
def remove_waypoint(trip_id: int, location_id: int, db: Session = Depends(get_db_sync)):
    """Remove a waypoint from a trip"""
    service = TripPlanningService(db)

    try:
        trip = service.remove_waypoint(trip_id=trip_id, location_id=location_id)
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/suggest-waypoints", response_model=List[LocationWithDistance])
def suggest_waypoints(
    trip_id: int,
    params: WaypointSuggestionParams,
    db: Session = Depends(get_db_sync)
):
    """Get suggested waypoints for a trip"""
    service = TripPlanningService(db)

    try:
        suggestions = service.suggest_waypoints(
            trip_id=trip_id,
            num_stops=params.num_stops,
        )

        return [
            LocationWithDistance(
                **item["location"].__dict__,
                distance_km=item.get("distance_km", item.get("distance_from_start_km", 0)),
                score=item.get("combined_score", item.get("score", 0))
            )
            for item in suggestions
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trip_id}/stats", response_model=TripStats)
def get_trip_stats(trip_id: int, db: Session = Depends(get_db_sync)):
    """Get trip statistics"""
    service = TripPlanningService(db)

    try:
        stats = service.calculate_trip_stats(trip_id)
        return stats

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/finalize", response_model=TripResponse)
def finalize_trip(trip_id: int, data: TripFinalize, db: Session = Depends(get_db_sync)):
    """Finalize trip and set to active"""
    service = TripPlanningService(db)

    try:
        trip = service.finalize_trip(trip_id=trip_id, start_date=data.start_date)
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trip_id}")
def delete_trip(trip_id: int, user_id: int = 1, db: Session = Depends(get_db_sync)):
    """
    Delete a trip.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    service = TripPlanningService(db)

    try:
        service.delete_trip(trip_id=trip_id, user_id=user_id)
        return {"message": "Trip deleted successfully", "trip_id": trip_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
