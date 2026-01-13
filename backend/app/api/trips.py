from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
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
async def create_trip(trip_data: TripCreate, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Create a new trip.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    service = TripPlanningService(db)

    try:
        trip = await service.create_trip(
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


@router.get("/", response_model=List[TripResponse])
async def list_trips(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    List all trips for a user.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    from app.models import Trip
    from sqlalchemy import select

    result = await db.execute(select(Trip).filter(Trip.user_id == user_id))
    trips = result.scalars().all()
    return trips


@router.get("/active", response_model=TripResponse)
async def get_active_trip(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Get the user's active trip.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    from app.models import Trip
    from sqlalchemy import select

    result = await db.execute(
        select(Trip).filter(Trip.user_id == user_id, Trip.status == "active")
    )
    trip = result.scalars().first()

    if not trip:
        raise HTTPException(status_code=404, detail="No active trip found")

    return trip


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    """Get trip by ID"""
    from app.models import Trip
    from sqlalchemy import select

    result = await db.execute(select(Trip).filter(Trip.id == trip_id))
    trip = result.scalars().first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


@router.post("/{trip_id}/waypoints", response_model=TripResponse)
async def add_waypoint(trip_id: int, waypoint: WaypointAdd, db: AsyncSession = Depends(get_db)):
    """Add a waypoint to a trip"""
    service = TripPlanningService(db)

    try:
        trip = await service.add_waypoint(
            trip_id=trip_id,
            location_id=waypoint.location_id,
            order=waypoint.order,
        )
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trip_id}/waypoints/{location_id}", response_model=TripResponse)
async def remove_waypoint(trip_id: int, location_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a waypoint from a trip"""
    service = TripPlanningService(db)

    try:
        trip = await service.remove_waypoint(trip_id=trip_id, location_id=location_id)
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/suggest-waypoints", response_model=List[LocationWithDistance])
async def suggest_waypoints(
    trip_id: int,
    params: WaypointSuggestionParams,
    db: AsyncSession = Depends(get_db)
):
    """Get suggested waypoints for a trip"""
    service = TripPlanningService(db)

    try:
        suggestions = await service.suggest_waypoints(
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
async def get_trip_stats(trip_id: int, db: AsyncSession = Depends(get_db)):
    """Get trip statistics"""
    service = TripPlanningService(db)

    try:
        stats = await service.calculate_trip_stats(trip_id)
        return stats

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trip_id}/finalize", response_model=TripResponse)
async def finalize_trip(trip_id: int, data: TripFinalize, db: AsyncSession = Depends(get_db)):
    """Finalize trip and set to active"""
    service = TripPlanningService(db)

    try:
        trip = await service.finalize_trip(trip_id=trip_id, start_date=data.start_date)
        return trip

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trip_id}")
async def delete_trip(trip_id: int, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Delete a trip.

    Note: user_id is hardcoded for now. Will be extracted from auth token later.
    """
    service = TripPlanningService(db)

    try:
        await service.delete_trip(trip_id=trip_id, user_id=user_id)
        return {"message": "Trip deleted successfully", "trip_id": trip_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
