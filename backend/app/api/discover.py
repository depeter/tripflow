from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, select
from typing import List, Optional
from datetime import datetime
from geoalchemy2.types import Geography

from app.db.database import get_db
from app.models.event import Event, EventCategory
from app.models.location import Location
from app.api.schemas import (
    DiscoverySearchParams,
    DiscoveryResponse,
    EventResponse,
    LocationDiscoveryResponse,
)

router = APIRouter(prefix="/discover", tags=["discover"])


@router.post("", response_model=DiscoveryResponse)
async def discover_events(params: DiscoverySearchParams, db: AsyncSession = Depends(get_db)):
    """
    Discover events and/or locations near a point using PostGIS geospatial queries.

    Returns events and locations within the specified radius, sorted by distance.
    Supports filtering by categories, date ranges, price, and text search.
    """
    distance_meters = params.radius_km * 1000
    events = []
    locations = []
    total_count = 0

    # Determine what to fetch based on item_types
    fetch_events = not params.item_types or "events" in params.item_types
    fetch_locations = not params.item_types or "locations" in params.item_types

    # Fetch Events
    if fetch_events:
        # ST_Distance with geography returns meters, divide by 1000 for km
        distance_expr = func.ST_Distance(
            func.cast(Event.geom, Geography),
            func.cast(func.ST_SetSRID(func.ST_MakePoint(params.longitude, params.latitude), 4326), Geography)
        ) / 1000.0

        event_query = select(
            Event,
            distance_expr.label('distance_km')
        ).filter(
            and_(
                Event.active == True,
                Event.cancelled == False,
                # Use ST_DWithin with geography for proper meter-based filtering
                func.ST_DWithin(
                    func.cast(Event.geom, Geography),
                    func.cast(func.ST_SetSRID(func.ST_MakePoint(params.longitude, params.latitude), 4326), Geography),
                    distance_meters
                )
            )
        )

        # Filter by categories if specified
        if params.categories:
            event_query = event_query.filter(Event.category.in_(params.categories))

        # Filter by event types if specified
        if params.event_types:
            event_query = event_query.filter(Event.event_type.in_(params.event_types))

        # Filter by search text if specified
        if params.search_text:
            search_pattern = f"%{params.search_text}%"
            event_query = event_query.filter(
                or_(
                    Event.name.ilike(search_pattern),
                    Event.description.ilike(search_pattern),
                    Event.venue_name.ilike(search_pattern),
                    Event.organizer.ilike(search_pattern)
                )
            )

        # Filter by date range
        now = datetime.now()
        if params.start_date:
            event_query = event_query.filter(
                or_(
                    Event.end_datetime >= params.start_date,
                    and_(Event.end_datetime.is_(None), Event.start_datetime >= params.start_date)
                )
            )
        else:
            # Default: only show upcoming events
            event_query = event_query.filter(
                or_(
                    Event.end_datetime >= now,
                    and_(Event.end_datetime.is_(None), Event.start_datetime >= now)
                )
            )

        if params.end_date:
            event_query = event_query.filter(Event.start_datetime <= params.end_date)

        # Filter by free events if requested
        if params.free_only:
            event_query = event_query.filter(Event.free == True)

        # Sort and limit
        event_query = event_query.order_by(distance_expr).limit(params.limit)

        # Execute
        event_result = await db.execute(event_query)
        event_results = event_result.all()

        for event, distance in event_results:
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

    # Fetch Locations
    if fetch_locations:
        # ST_Distance with geography returns meters, divide by 1000 for km
        distance_expr_loc = func.ST_Distance(
            func.cast(Location.geom, Geography),
            func.cast(func.ST_SetSRID(func.ST_MakePoint(params.longitude, params.latitude), 4326), Geography)
        ) / 1000.0

        location_query = select(
            Location,
            distance_expr_loc.label('distance_km')
        ).filter(
            and_(
                Location.active == True,
                # Use ST_DWithin with geography for proper meter-based filtering
                func.ST_DWithin(
                    func.cast(Location.geom, Geography),
                    func.cast(func.ST_SetSRID(func.ST_MakePoint(params.longitude, params.latitude), 4326), Geography),
                    distance_meters
                )
            )
        )

        # Filter by search text if specified
        if params.search_text:
            search_pattern = f"%{params.search_text}%"
            location_query = location_query.filter(
                or_(
                    Location.name.ilike(search_pattern),
                    Location.description.ilike(search_pattern),
                    Location.city.ilike(search_pattern)
                )
            )

        # Sort and limit
        location_query = location_query.order_by(distance_expr_loc).limit(params.limit)

        # Execute
        location_result = await db.execute(location_query)
        location_results = location_result.all()

        for location, distance in location_results:
            location_dict = {
                'id': location.id,
                'name': location.name,
                'description': location.description,
                'location_type': location.location_type,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address,
                'city': location.city,
                'country': location.country,
                'rating': location.rating,
                'rating_count': location.rating_count,
                'price_type': location.price_type,
                'price_min': location.price_min,
                'price_max': location.price_max,
                'website': location.website,
                'main_image_url': location.main_image_url,
                'images': location.images,
                'tags': location.tags or [],
                'source': location.source,
                'distance_km': round(distance, 2) if distance else None,
            }
            locations.append(LocationDiscoveryResponse(**location_dict))

    total_count = len(events) + len(locations)

    return DiscoveryResponse(
        events=events,
        locations=locations,
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
