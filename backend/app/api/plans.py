"""
Personalized plan suggestions API.

Generates day plan suggestions based on user preferences, location, and driving envelope.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.db.database import get_db
from app.services.plan_service import PlanService
from app.api.schemas import (
    PlanSuggestRequest,
    PlanSuggestResponse,
    UserPreferencesInput,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/suggest", response_model=PlanSuggestResponse)
async def suggest_plans(
    request: PlanSuggestRequest,
    db: AsyncSession = Depends(get_db),
    x_session_id: Optional[str] = Header(None),
):
    """
    Get personalized day plan suggestions.

    This endpoint generates plan suggestions based on:
    - User's current location
    - Optional destination (for transit mode)
    - Driving envelope (how far they want to drive today)
    - User preferences (interests, environment, accommodation, pace)

    If preferences are not provided, returns generic distance-based plans.

    **Request body:**
    - `latitude`, `longitude`: Current position (required)
    - `destination_latitude`, `destination_longitude`: Destination for transit mode (optional)
    - `driving_envelope_km`: Max driving distance today (default: 100km)
    - `preferences`: User preferences object (optional)
    - `date_start`, `date_end`: Date range for events (default: next 7 days)
    - `max_plans`: Maximum plans to return (default: 8)

    **Response:**
    - `plans`: List of suggested plans, sorted by preference score
    - `personalized`: Whether preferences were applied
    - `preferences_applied`: The preferences that were used

    **Plan types:**
    - `themed`: Based on user interests (nature, history, food, etc.)
    - `environment`: Based on preferred environments (coast, villages, cities)
    - `distance`: Based on driving distance (local, day trip, weekend, road trip)
    - `transit`: Optimized for traveling toward destination
    """
    try:
        service = PlanService(db)
        response = await service.suggest_plans(request)
        return response

    except Exception as e:
        logger.exception(f"Failed to generate plan suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan suggestions: {str(e)}"
        )


@router.post("/suggest/quick", response_model=PlanSuggestResponse)
async def suggest_plans_quick(
    latitude: float,
    longitude: float,
    driving_envelope_km: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Quick plan suggestions without preferences (simpler endpoint).

    Returns generic distance-based plans without personalization.
    Use `/suggest` for personalized recommendations.
    """
    request = PlanSuggestRequest(
        latitude=latitude,
        longitude=longitude,
        driving_envelope_km=driving_envelope_km,
        preferences=None,
    )

    try:
        service = PlanService(db)
        response = await service.suggest_plans(request)
        return response

    except Exception as e:
        logger.exception(f"Failed to generate quick plan suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan suggestions: {str(e)}"
        )


@router.get("/interests")
def get_available_interests():
    """
    Get list of available interest categories for personalization.

    These can be used in the preferences.interests field of /suggest.
    """
    return {
        "interests": [
            {"id": "nature", "name": "Nature & Hiking", "icon": "🏔️"},
            {"id": "history", "name": "History & Culture", "icon": "🏛️"},
            {"id": "food", "name": "Local Food", "icon": "🍳"},
            {"id": "photography", "name": "Photography", "icon": "📸"},
            {"id": "music", "name": "Music & Festivals", "icon": "🎵"},
            {"id": "cycling", "name": "Cycling", "icon": "🚴"},
            {"id": "wine", "name": "Wine & Beer", "icon": "🍷"},
            {"id": "architecture", "name": "Architecture", "icon": "🏰"},
        ],
        "environments": [
            {"id": "nature", "name": "Nature", "icon": "🌲"},
            {"id": "cities", "name": "Cities", "icon": "🏙️"},
            {"id": "villages", "name": "Villages", "icon": "🏡"},
            {"id": "coast", "name": "Coastal", "icon": "🌊"},
        ],
        "accommodation_types": [
            {"id": "camping", "name": "Campgrounds", "icon": "⛺"},
            {"id": "wild", "name": "Wild Camping", "icon": "🏕️"},
            {"id": "stellplatz", "name": "Stellplatz", "icon": "🚐"},
            {"id": "hotel", "name": "Hotels", "icon": "🏨"},
        ],
        "travel_paces": [
            {"id": "slow", "name": "Slow", "description": "50-100 km/day"},
            {"id": "moderate", "name": "Moderate", "description": "100-200 km/day"},
            {"id": "fast", "name": "Fast", "description": "200+ km/day"},
        ],
        "budgets": [
            {"id": "budget", "name": "Budget", "description": "Free/low-cost options"},
            {"id": "mid-range", "name": "Mid-range", "description": "Balanced options"},
            {"id": "comfort", "name": "Comfort", "description": "Premium experiences"},
        ],
    }
