from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, select
from typing import List, Optional, Tuple
from datetime import datetime
from geoalchemy2.types import Geography

from app.db.database import get_db
from app.models.event import Event
from app.models.location import Location
from app.api.schemas import (
    DiscoverySearchParams,
    DiscoveryResponse,
    EventResponse,
    LocationDiscoveryResponse,
)

router = APIRouter(prefix="/discover", tags=["discover"])


# ============ Event Quality Scoring (from plan_service.py) ============

# Boring event types to exclude - these are local activities not interesting for travelers
BORING_EVENT_TYPES = {
    'Cursus met open sessies',  # Courses with open sessions
    'Lessenreeks',              # Lesson series
    'Lezing of congres',        # Lectures/conferences
    'Spel of quiz',             # Games/quizzes (usually local pub quizzes)
    'Voorlezing',               # Readings (library activities)
    'Boekvoorstelling',         # Book presentations
    'Workshop',                 # Generic workshops
}

# Boring categories to exclude or deprioritize
BORING_CATEGORIES = {
    'OTHER',                    # Generic "other" category
    'Cursus met open sessies',
    'Lessenreeks',
    'Lezing of congres',
}

# Interesting categories for travelers - these get priority
INTERESTING_CATEGORIES = {
    'CONCERT', 'Concert',
    'Rock', 'Pop', 'Hip-Hop/Rap', 'Alternative', 'Jazz', 'Electronic', 'Metal',
    'Fairs & Festivals', 'FESTIVAL',
    'Theatre', 'THEATER', 'Theatervoorstelling',
    'Comedy',
    'Family',  # Family-friendly events
    'EXHIBITION',  # Art exhibitions
    'SPORTS', 'Sportactiviteit',
}

# Interesting event types
INTERESTING_EVENT_TYPES = {
    'Concert',
    'Festival', 'Festiviteit',
    'Theatervoorstelling',
    'Eet- of drankfestijn',      # Food & drink festival
    'Begeleide uitstap of rondleiding',  # Guided tours
    'Beurs',                     # Trade fairs/markets
    'Film',
    'Tentoonstelling',           # Exhibition
    'Sportactiviteit',
}

# Keywords in event names that indicate boring events
BORING_NAME_KEYWORDS = [
    'volzet',      # Sold out
    'uitverkocht', # Sold out
    'voorlezen',   # Reading aloud (library)
    'boekstart',   # Book start (children's library)
    'babysit',
    'peuter',      # Toddler
    'kleuter',     # Preschool
]


def _is_boring_event(event: Event) -> bool:
    """Check if an event is boring/not interesting for travelers"""
    # Check event type
    if event.event_type and event.event_type in BORING_EVENT_TYPES:
        return True

    # Check category
    if event.category and event.category in BORING_CATEGORIES:
        # Only mark as boring if it's not also an interesting type
        if event.event_type not in INTERESTING_EVENT_TYPES:
            return True

    # Check for boring keywords in name
    if event.name:
        name_lower = event.name.lower()
        for keyword in BORING_NAME_KEYWORDS:
            if keyword in name_lower:
                return True

    return False


def _is_interesting_event(event: Event) -> bool:
    """Check if an event is particularly interesting for travelers"""
    # Interesting category
    if event.category and event.category in INTERESTING_CATEGORIES:
        return True

    # Interesting event type
    if event.event_type and event.event_type in INTERESTING_EVENT_TYPES:
        return True

    return False


def _score_event(event: Event, distance_km: float) -> float:
    """
    Score an event based on quality factors.
    Returns a score between 0 and 1, higher is better.
    """
    score = 0.0

    # Base score: interesting events get a significant boost (40%)
    if _is_interesting_event(event):
        score += 0.4

    # Distance score (10% weight) - closer is better, 0-300km range
    distance_score = max(0, 1 - (distance_km / 300))
    score += distance_score * 0.1

    # Free events get a small boost (5%)
    if event.free:
        score += 0.05

    # Events with prices listed (not unknown) are more reliable (5%)
    if event.price is not None or event.free:
        score += 0.05

    # Category-based scoring (up to 20%)
    if event.category:
        if event.category in {'CONCERT', 'Concert', 'FESTIVAL'}:
            score += 0.2
        elif event.category in {'THEATER', 'Theatre', 'Comedy'}:
            score += 0.15
        elif event.category in {'EXHIBITION', 'CULTURAL'}:
            score += 0.1
        elif event.category in {'FOOD', 'MARKET'}:
            score += 0.1
        elif event.category in {'SPORTS', 'OUTDOOR'}:
            score += 0.1

    # Event type scoring (up to 15%)
    if event.event_type:
        if event.event_type in {'Concert', 'Festival', 'Festiviteit'}:
            score += 0.15
        elif event.event_type in {'Theatervoorstelling', 'Film'}:
            score += 0.1
        elif event.event_type in {'Eet- of drankfestijn', 'Tentoonstelling'}:
            score += 0.1

    # Normalize to 0-1 range
    return min(1.0, score)


def score_and_filter_events(event_results: List[Tuple[Event, float]]) -> List[Tuple[Event, float, float]]:
    """
    Score and filter events, returning (event, distance, score) tuples.
    Filters out boring events and sorts by score descending.
    """
    scored_events = []

    for event, distance in event_results:
        # Skip boring events
        if _is_boring_event(event):
            continue

        score = _score_event(event, distance)

        # Only include events with minimal relevance (or interesting events)
        if score >= 0.1 or _is_interesting_event(event):
            scored_events.append((event, distance, score))

    # Sort by score descending (best first)
    scored_events.sort(key=lambda x: x[2], reverse=True)

    return scored_events


@router.post("", response_model=DiscoveryResponse)
async def discover_events(params: DiscoverySearchParams, db: AsyncSession = Depends(get_db)):
    """
    Discover events and/or locations using PostGIS geospatial queries.

    Two modes:
    1. Point search (default): Returns items within radius_km of the search point
    2. Route search (when destination_latitude/longitude provided): Returns items along
       the corridor between start and destination, up to max_distance_km

    Supports filtering by categories, date ranges, price, and text search.
    """
    events = []
    locations = []
    total_count = 0

    # Determine search mode: corridor (route) vs radius (point)
    is_corridor_search = (
        params.destination_latitude is not None and
        params.destination_longitude is not None
    )

    # Create geometry for the search area
    start_point = func.ST_SetSRID(
        func.ST_MakePoint(params.longitude, params.latitude), 4326
    )

    if is_corridor_search:
        # Route-based search: create a line from start to destination
        end_point = func.ST_SetSRID(
            func.ST_MakePoint(params.destination_longitude, params.destination_latitude), 4326
        )
        route_line = func.ST_MakeLine(start_point, end_point)
        corridor_meters = params.corridor_width_km * 1000
        max_distance_meters = (params.max_distance_km or 300) * 1000
    else:
        # Point-based search
        distance_meters = params.radius_km * 1000

    # Determine what to fetch based on item_types
    fetch_events = not params.item_types or "events" in params.item_types
    fetch_locations = not params.item_types or "locations" in params.item_types

    # Fetch Events
    if fetch_events:
        # Distance from start point (always calculated for sorting and display)
        distance_from_start_expr = func.ST_Distance(
            func.cast(Event.geom, Geography),
            func.cast(start_point, Geography)
        ) / 1000.0

        if is_corridor_search:
            # Corridor search: find events within corridor_width of the route line
            # AND within max_distance from start
            event_query = select(
                Event,
                distance_from_start_expr.label('distance_km')
            ).filter(
                and_(
                    Event.active == True,
                    Event.cancelled == False,
                    # Within corridor of the route
                    func.ST_DWithin(
                        func.cast(Event.geom, Geography),
                        func.cast(route_line, Geography),
                        corridor_meters
                    ),
                    # Within max driving distance from start
                    func.ST_DWithin(
                        func.cast(Event.geom, Geography),
                        func.cast(start_point, Geography),
                        max_distance_meters
                    )
                )
            )
        else:
            # Point search: find events within radius of search point
            event_query = select(
                Event,
                distance_from_start_expr.label('distance_km')
            ).filter(
                and_(
                    Event.active == True,
                    Event.cancelled == False,
                    func.ST_DWithin(
                        func.cast(Event.geom, Geography),
                        func.cast(start_point, Geography),
                        distance_meters
                    )
                )
            )

        # Use new structured filters if provided, otherwise fall back to legacy
        if params.event_filters:
            categories = params.event_filters.categories or params.categories
            event_types = params.event_filters.event_types or params.event_types
            date_start = params.event_filters.date_start or params.start_date
            date_end = params.event_filters.date_end or params.end_date
            free_only = params.event_filters.free_only
            price_min = params.event_filters.price_min
            price_max = params.event_filters.price_max
            time_of_day = params.event_filters.time_of_day
        else:
            categories = params.categories
            event_types = params.event_types
            date_start = params.start_date
            date_end = params.end_date
            free_only = params.free_only
            price_min = None
            price_max = None
            time_of_day = None

        # Convert timezone-aware datetimes to naive (DB uses TIMESTAMP WITHOUT TIME ZONE)
        if date_start and date_start.tzinfo is not None:
            date_start = date_start.replace(tzinfo=None)
        if date_end and date_end.tzinfo is not None:
            date_end = date_end.replace(tzinfo=None)

        # Filter by categories if specified
        if categories:
            event_query = event_query.filter(Event.category.in_(categories))

        # Filter by event types if specified
        if event_types:
            event_query = event_query.filter(Event.event_type.in_(event_types))

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
        if date_start:
            event_query = event_query.filter(
                or_(
                    Event.end_datetime >= date_start,
                    and_(Event.end_datetime.is_(None), Event.start_datetime >= date_start)
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

        if date_end:
            event_query = event_query.filter(Event.start_datetime <= date_end)

        # Filter by price range
        if free_only:
            event_query = event_query.filter(Event.free == True)
        else:
            if price_min is not None:
                event_query = event_query.filter(
                    or_(
                        Event.free == True,
                        Event.price >= price_min
                    )
                )
            if price_max is not None:
                event_query = event_query.filter(
                    or_(
                        Event.free == True,
                        Event.price <= price_max
                    )
                )

        # Filter by time of day (extract hour from start_datetime)
        if time_of_day:
            time_conditions = []
            if 'morning' in time_of_day:
                time_conditions.append(and_(
                    func.extract('hour', Event.start_datetime) >= 6,
                    func.extract('hour', Event.start_datetime) < 12
                ))
            if 'afternoon' in time_of_day:
                time_conditions.append(and_(
                    func.extract('hour', Event.start_datetime) >= 12,
                    func.extract('hour', Event.start_datetime) < 18
                ))
            if 'evening' in time_of_day:
                time_conditions.append(and_(
                    func.extract('hour', Event.start_datetime) >= 18,
                    func.extract('hour', Event.start_datetime) < 24
                ))
            if 'night' in time_of_day:
                time_conditions.append(and_(
                    func.extract('hour', Event.start_datetime) >= 0,
                    func.extract('hour', Event.start_datetime) < 6
                ))
            if time_conditions:
                event_query = event_query.filter(or_(*time_conditions))

        # Sort by distance initially (we'll re-sort by score after filtering)
        # Fetch more events than requested since we'll filter out boring ones
        event_query = event_query.order_by(distance_from_start_expr).limit(params.limit * 3)

        # Execute
        event_result = await db.execute(event_query)
        event_results = event_result.all()

        # Score, filter, and sort events by quality score
        scored_events = score_and_filter_events(event_results)

        # Take only the requested limit after scoring
        for event, distance, score in scored_events[:params.limit]:
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
                'score': round(score, 2),
            }
            events.append(EventResponse(**event_dict))

    # Fetch Locations
    if fetch_locations:
        # Distance from start point (always calculated for sorting and display)
        distance_from_start_loc = func.ST_Distance(
            func.cast(Location.geom, Geography),
            func.cast(start_point, Geography)
        ) / 1000.0

        if is_corridor_search:
            # Corridor search: find locations within corridor_width of the route line
            # AND within max_distance from start
            location_query = select(
                Location,
                distance_from_start_loc.label('distance_km')
            ).filter(
                and_(
                    Location.active == True,
                    # Within corridor of the route
                    func.ST_DWithin(
                        func.cast(Location.geom, Geography),
                        func.cast(route_line, Geography),
                        corridor_meters
                    ),
                    # Within max driving distance from start
                    func.ST_DWithin(
                        func.cast(Location.geom, Geography),
                        func.cast(start_point, Geography),
                        max_distance_meters
                    )
                )
            )
        else:
            # Point search: find locations within radius of search point
            location_query = select(
                Location,
                distance_from_start_loc.label('distance_km')
            ).filter(
                and_(
                    Location.active == True,
                    func.ST_DWithin(
                        func.cast(Location.geom, Geography),
                        func.cast(start_point, Geography),
                        distance_meters
                    )
                )
            )

        # Use new structured location filters if provided
        if params.location_filters:
            location_types = params.location_filters.location_types
            min_rating = params.location_filters.min_rating
            price_types = params.location_filters.price_types
            amenities = params.location_filters.amenities
            features = params.location_filters.features
            open_now = params.location_filters.open_now
            is_24_7 = params.location_filters.is_24_7
            no_booking_required = params.location_filters.no_booking_required
            min_capacity = params.location_filters.min_capacity
        else:
            location_types = None
            min_rating = None
            price_types = None
            amenities = None
            features = None
            open_now = False
            is_24_7 = False
            no_booking_required = False
            min_capacity = None

        # Filter by location types
        if location_types:
            location_query = location_query.filter(Location.location_type.in_(location_types))

        # Filter by minimum rating
        if min_rating is not None:
            location_query = location_query.filter(Location.rating >= min_rating)

        # Filter by price types
        if price_types:
            price_conditions = []
            for price_type in price_types:
                if price_type == 'free':
                    price_conditions.append(Location.price_type == 'free')
                elif price_type == 'paid_low':
                    price_conditions.append(and_(Location.price_min >= 0, Location.price_max <= 10))
                elif price_type == 'paid_medium':
                    price_conditions.append(and_(Location.price_min >= 10, Location.price_max <= 25))
                elif price_type == 'paid_high':
                    price_conditions.append(and_(Location.price_min >= 25, Location.price_max <= 50))
                elif price_type == 'paid_premium':
                    price_conditions.append(Location.price_min >= 50)
            if price_conditions:
                location_query = location_query.filter(or_(*price_conditions))

        # Filter by amenities (check if all required amenities are present in JSONB)
        if amenities:
            for amenity in amenities:
                # JSONB containment check - amenities JSONB should contain the key
                location_query = location_query.filter(
                    Location.amenities.op('?')(amenity)  # PostgreSQL JSONB ? operator
                )

        # Filter by features (check if all required features are present in JSONB)
        if features:
            for feature in features:
                location_query = location_query.filter(
                    Location.features.op('?')(feature)
                )

        # Filter by 24/7 access
        if is_24_7:
            location_query = location_query.filter(Location.is_24_7 == True)

        # Filter by booking requirement
        if no_booking_required:
            location_query = location_query.filter(Location.requires_booking == False)

        # Filter by minimum capacity
        if min_capacity is not None:
            location_query = location_query.filter(Location.capacity_available >= min_capacity)

        # TODO: Implement open_now filter (requires parsing opening_hours JSONB)
        # This would need to check current time against opening_hours structure

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
        location_query = location_query.order_by(distance_from_start_loc).limit(params.limit)

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
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get list of available event categories from database"""
    # Query distinct categories from the database
    from sqlalchemy import select, func
    result = await db.execute(
        select(Event.category).distinct().where(Event.category.isnot(None)).order_by(Event.category)
    )
    categories = [row[0] for row in result.all()]
    return categories


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
