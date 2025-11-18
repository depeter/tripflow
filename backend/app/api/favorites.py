from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models.event import Event
from app.models.user import User
from app.api.auth import get_current_user
from app.api.schemas import EventResponse
from pydantic import BaseModel

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteCreate(BaseModel):
    event_id: int


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an event to user's favorites.

    Requires authentication. Returns error if event doesn't exist or already favorited.
    """
    # Check if event exists
    result = await db.execute(select(Event).filter(Event.id == favorite.event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if already favorited
    from app.models.user import UserFavorite
    result = await db.execute(
        select(UserFavorite).filter(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.event_id == favorite.event_id
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event already in favorites"
        )

    # Create favorite
    new_favorite = UserFavorite(
        user_id=current_user.id,
        event_id=favorite.event_id
    )
    db.add(new_favorite)
    await db.commit()
    await db.refresh(new_favorite)

    return new_favorite


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an event from user's favorites.

    Requires authentication. Returns 404 if not in favorites.
    """
    from app.models.user import UserFavorite
    result = await db.execute(
        select(UserFavorite).filter(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.event_id == event_id
            )
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    await db.delete(favorite)
    await db.commit()

    return None


@router.get("", response_model=List[EventResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all favorited events for the current user.

    Returns events with full details, sorted by when they were favorited (newest first).
    """
    from app.models.user import UserFavorite

    # Join UserFavorite with Event to get full event details
    result = await db.execute(
        select(Event, UserFavorite.created_at).join(
            UserFavorite,
            UserFavorite.event_id == Event.id
        ).filter(
            UserFavorite.user_id == current_user.id
        ).order_by(
            UserFavorite.created_at.desc()
        )
    )
    favorites = result.all()

    # Convert to EventResponse objects
    events = []
    for event, favorited_at in favorites:
        event_dict = {
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'category': event.category,
            'start_datetime': event.start_datetime,
            'end_datetime': event.end_datetime,
            'all_day': event.all_day,
            'venue_name': event.venue_name,
            'address': event.address,
            'city': event.city,
            'country': event.country,
            'latitude': event.latitude,
            'longitude': event.longitude,
            'price': event.price,
            'currency': event.currency,
            'free': event.free,
            'website': event.website,
            'images': event.images or [],
            'tags': event.tags or [],
            'organizer': event.organizer,
            'event_type': event.event_type,
            'themes': event.themes or [],
            'source': event.source,
            'distance_km': None,  # No distance calculation for favorites list
        }
        events.append(EventResponse(**event_dict))

    return events


@router.get("/check/{event_id}", response_model=bool)
async def check_favorite(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if an event is in user's favorites.

    Returns True if favorited, False otherwise.
    """
    from app.models.user import UserFavorite
    result = await db.execute(
        select(UserFavorite).filter(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.event_id == event_id
            )
        )
    )
    favorite = result.scalar_one_or_none()

    return favorite is not None


@router.get("/ids", response_model=List[int])
async def get_favorite_ids(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of favorited event IDs for the current user.

    Useful for checking multiple events at once in the frontend.
    """
    from app.models.user import UserFavorite
    result = await db.execute(
        select(UserFavorite.event_id).filter(
            UserFavorite.user_id == current_user.id
        )
    )
    favorite_ids = result.all()

    return [fav_id for (fav_id,) in favorite_ids]
