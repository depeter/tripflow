from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.services.location_service import LocationService
from app.api.schemas import (
    LocationResponse,
    LocationWithDistance,
    LocationSearchParams,
    NearbySearchParams,
    GeocodeRequest,
    GeocodeResponse,
)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get location by ID"""
    service = LocationService(db)
    location = service.get_location_by_id(location_id)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return location


@router.post("/search", response_model=List[LocationResponse])
def search_locations(params: LocationSearchParams, db: Session = Depends(get_db)):
    """Search locations with filters"""
    service = LocationService(db)

    locations = service.search_locations(
        query=params.query,
        location_types=params.location_types,
        amenities=params.amenities,
        tags=params.tags,
        min_rating=params.min_rating,
        max_price=params.max_price,
        limit=params.limit,
    )

    return locations


@router.post("/nearby", response_model=List[LocationWithDistance])
def find_nearby(params: NearbySearchParams, db: Session = Depends(get_db)):
    """Find locations near a point"""
    service = LocationService(db)

    results = service.find_nearby_locations(
        latitude=params.latitude,
        longitude=params.longitude,
        radius_km=params.radius_km,
        location_types=params.location_types,
        limit=params.limit,
    )

    return [
        LocationWithDistance(
            **item["location"].__dict__,
            distance_km=item["distance_km"]
        )
        for item in results
    ]


@router.post("/geocode", response_model=GeocodeResponse)
def geocode_address(request: GeocodeRequest, db: Session = Depends(get_db)):
    """Geocode an address to coordinates"""
    service = LocationService(db)
    result = service.geocode_address(request.address)

    if not result:
        raise HTTPException(status_code=404, detail="Address not found")

    return result


@router.get("/reverse-geocode", response_model=str)
def reverse_geocode(latitude: float, longitude: float, db: Session = Depends(get_db)):
    """Reverse geocode coordinates to address"""
    service = LocationService(db)
    address = service.reverse_geocode(latitude, longitude)

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    return address
