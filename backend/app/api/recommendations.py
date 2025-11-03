from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.services.recommendation_service import RecommendationService
from app.api.schemas import LocationWithDistance, RecommendationParams

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/", response_model=List[LocationWithDistance])
def get_recommendations(params: RecommendationParams, db: Session = Depends(get_db)):
    """
    Get personalized location recommendations.

    Supports:
    - User-based personalization (if user_id provided)
    - Interest-based recommendations (if interests provided)
    - Geographic filtering (if coordinates and radius provided)
    """
    service = RecommendationService(db)

    try:
        recommendations = service.recommend_locations(
            user_id=params.user_id,
            near_latitude=params.near_latitude,
            near_longitude=params.near_longitude,
            radius_km=params.radius_km,
            interests=params.interests,
            limit=params.limit,
        )

        return [
            LocationWithDistance(
                **rec["location"].__dict__,
                distance_km=rec.get("distance_km"),
                score=rec.get("score", 0)
            )
            for rec in recommendations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.post("/index-location/{location_id}")
def index_location(location_id: int, db: Session = Depends(get_db)):
    """Index a specific location in Qdrant for recommendations"""
    from app.models import Location

    service = RecommendationService(db)
    location = db.query(Location).filter(Location.id == location_id).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    try:
        service.index_location(location)
        return {"message": f"Location {location_id} indexed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/index-all")
def index_all_locations(batch_size: int = 100, db: Session = Depends(get_db)):
    """
    Index all locations in Qdrant.

    This should be run after initial data sync or periodically.
    Note: This can be a long-running operation for large datasets.
    """
    service = RecommendationService(db)

    try:
        service.index_all_locations(batch_size=batch_size)
        return {"message": "All locations indexed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
