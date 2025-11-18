from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, select
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.event import Event, EventCategory
from app.api.schemas import (
    DiscoverySearchParams,
    DiscoveryResponse,
    EventResponse,
)

router = APIRouter(prefix="/discover", tags=["discover"])


@router.post("", response_model=DiscoveryResponse)
async def discover_events(params: DiscoverySearchParams, db: AsyncSession = Depends(get_db)):
    """
    Discover events near a location using PostGIS geospatial queries.

    Returns events within the specified radius, sorted by distance from the search point.
    Supports filtering by categories, date ranges, and price.
    """
    # Build base query with distance calculation
    # ST_DWithin is more efficient than ST_Distance for radius searches
    # We convert kilometers to meters (PostGIS uses meters for geography)
    distance_meters = params.radius_km * 1000

    # Calculate distance in kilometers for sorting and response
    distance_expr = func.ST_Distance(
        Event.geom,
        func.ST_SetSRID(func.ST_MakePoint(params.longitude, params.latitude), 4326)
    ) / 1000.0  # Convert meters to kilometers

    # Base query: events within radius
    query = select(
        Event,
        distance_expr.label('distance_km')
    ).filter(
        and_(
            Event.active == True,
            Event.cancelled == False,
            func.ST_DWithin(
                Event.geom,
                func.ST_SetSRID(func.ST_MakePoint(params.longitude, params.latitude), 4326),
                distance_meters
            )
        )
    )

    # Filter by categories if specified
    if params.categories:
        # Convert enum values to strings for comparison
        category_values = [cat.value for cat in params.categories]
        query = query.filter(Event.category.in_(category_values))

    # Filter by date range
    now = datetime.now()

    if params.start_date:
        # Event must end after start_date (or if no end_date, start after start_date)
        query = query.filter(
            or_(
                Event.end_datetime >= params.start_date,
                and_(Event.end_datetime.is_(None), Event.start_datetime >= params.start_date)
            )
        )
    else:
        # Default: only show upcoming events (not past events)
        query = query.filter(
            or_(
                Event.end_datetime >= now,
                and_(Event.end_datetime.is_(None), Event.start_datetime >= now)
            )
        )

    if params.end_date:
        # Event must start before end_date
        query = query.filter(Event.start_datetime <= params.end_date)

    # Filter by free events if requested
    if params.free_only:
        query = query.filter(Event.free == True)

    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()

    # Sort by distance and apply limit
    query = query.order_by(distance_expr).limit(params.limit)

    # Execute query
    result = await db.execute(query)
    results = result.all()

    # Build response
    events = []
    for event, distance in results:
        # Convert SQLAlchemy model to dict and add distance
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
            'distance_km': round(distance, 2) if distance else None,
        }
        events.append(EventResponse(**event_dict))

    return DiscoveryResponse(
        events=events,
        total_count=total_count,
        search_center={
            "latitude": params.latitude,
            "longitude": params.longitude
        },
        radius_km=params.radius_km
    )


@router.get("/categories", response_model=List[str])
def get_categories():
    """Get list of available event categories"""
    return [category.value for category in EventCategory]


@router.get("/stats")
async def get_discovery_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics about available events for discovery mode"""

    # Total active events
    total_result = await db.execute(
        select(func.count(Event.id)).filter(
            and_(Event.active == True, Event.cancelled == False)
        )
    )
    total_events = total_result.scalar()

    # Upcoming events (not past)
    now = datetime.now()
    upcoming_result = await db.execute(
        select(func.count(Event.id)).filter(
            and_(
                Event.active == True,
                Event.cancelled == False,
                or_(
                    Event.end_datetime >= now,
                    and_(Event.end_datetime.is_(None), Event.start_datetime >= now)
                )
            )
        )
    )
    upcoming_events = upcoming_result.scalar()

    # Events by category
    category_result = await db.execute(
        select(
            Event.category,
            func.count(Event.id).label('count')
        ).filter(
            and_(Event.active == True, Event.cancelled == False)
        ).group_by(Event.category)
    )
    category_counts = category_result.all()

    # Events by source
    source_result = await db.execute(
        select(
            Event.source,
            func.count(Event.id).label('count')
        ).filter(
            and_(Event.active == True, Event.cancelled == False)
        ).group_by(Event.source)
    )
    source_counts = source_result.all()

    # Free vs paid
    free_result = await db.execute(
        select(func.count(Event.id)).filter(
            and_(Event.active == True, Event.cancelled == False, Event.free == True)
        )
    )
    free_count = free_result.scalar()

    paid_result = await db.execute(
        select(func.count(Event.id)).filter(
            and_(Event.active == True, Event.cancelled == False, Event.free == False)
        )
    )
    paid_count = paid_result.scalar()

    return {
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "categories": {cat: count for cat, count in category_counts},
        "sources": {source: count for source, count in source_counts},
        "free_events": free_count,
        "paid_events": paid_count,
    }
