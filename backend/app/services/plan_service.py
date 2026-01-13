"""
Plan suggestion service with preference-based scoring.

This service generates personalized day plan suggestions based on:
1. User's interests (nature, history, food, music, etc.)
2. Preferred environments (nature, cities, villages, coast)
3. Accommodation preferences (camping, wild, stellplatz, hotel)
4. Travel pace and budget
5. Current location and driving envelope
6. Optional destination (transit mode)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, select
from geoalchemy2.types import Geography

from app.models.event import Event
from app.models.location import Location
from app.api.schemas import (
    UserPreferencesInput,
    PlanSuggestRequest,
    PlanItemResponse,
    SuggestedPlanResponse,
    PlanSuggestResponse,
)


# ============ Event Quality Filtering ============

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


# ============ Interest to Event/Location Mapping ============

# Maps user interests to event themes, categories, and tags
INTEREST_MAPPINGS = {
    'nature': {
        'event_themes': ['natuur', 'outdoor', 'wandeling', 'hiking', 'nature'],
        'event_categories': ['OUTDOOR'],
        'event_types': ['wandeling', 'fietstocht', 'natuurevenement'],
        'location_types': ['CAMPSITE', 'REST_AREA', 'POI'],
        'location_tags': ['nature', 'hiking', 'forest', 'park', 'scenic', 'countryside'],
    },
    'history': {
        'event_themes': ['erfgoed', 'geschiedenis', 'heritage', 'museum', 'kunst'],
        'event_categories': ['CULTURAL', 'EXHIBITION'],
        'event_types': ['tentoonstelling', 'rondleiding', 'museum'],
        'location_types': ['ATTRACTION', 'POI'],
        'location_tags': ['historic', 'museum', 'castle', 'monument', 'heritage', 'cultural'],
    },
    'food': {
        'event_themes': ['eten', 'koken', 'food', 'culinair', 'gastronomie'],
        'event_categories': ['FOOD', 'MARKET'],
        'event_types': ['kookworkshop', 'markt', 'proeverij'],
        'location_types': ['RESTAURANT', 'POI'],
        'location_tags': ['restaurant', 'food', 'local cuisine', 'market', 'farm'],
    },
    'photography': {
        'event_themes': ['fotografie', 'foto', 'photography', 'kunst'],
        'event_categories': ['EXHIBITION', 'CULTURAL'],
        'event_types': ['tentoonstelling', 'workshop'],
        'location_types': ['ATTRACTION', 'POI'],
        'location_tags': ['scenic', 'viewpoint', 'panorama', 'instagram', 'photogenic'],
    },
    'music': {
        'event_themes': ['muziek', 'concert', 'music', 'festival'],
        'event_categories': ['CONCERT', 'FESTIVAL'],
        'event_types': ['concert', 'festival', 'optreden'],
        'location_types': ['POI', 'ATTRACTION'],
        'location_tags': ['music venue', 'club', 'theater', 'concert hall'],
    },
    'cycling': {
        'event_themes': ['fietsen', 'cycling', 'fiets', 'wielrennen'],
        'event_categories': ['SPORTS', 'OUTDOOR'],
        'event_types': ['fietstocht', 'wielerwedstrijd'],
        'location_types': ['CAMPSITE', 'REST_AREA', 'POI'],
        'location_tags': ['cycling', 'bike friendly', 'bike path', 'bike rental'],
    },
    'wine': {
        'event_themes': ['wijn', 'bier', 'wine', 'beer', 'brouwerij'],
        'event_categories': ['FOOD', 'CULTURAL'],
        'event_types': ['proeverij', 'degustatie', 'brouwerijbezoek'],
        'location_types': ['POI', 'ATTRACTION'],
        'location_tags': ['winery', 'brewery', 'vineyard', 'wine tasting', 'beer'],
    },
    'architecture': {
        'event_themes': ['architectuur', 'erfgoed', 'design', 'gebouwen'],
        'event_categories': ['CULTURAL', 'EXHIBITION'],
        'event_types': ['rondleiding', 'open monumentendag'],
        'location_types': ['ATTRACTION', 'POI'],
        'location_tags': ['architecture', 'historic', 'modern', 'design', 'building'],
    },
}

# Maps environment preferences to location characteristics
ENVIRONMENT_MAPPINGS = {
    'nature': {
        'location_tags': ['nature', 'forest', 'park', 'countryside', 'rural', 'lake', 'mountains'],
        'exclude_tags': ['urban', 'city center'],
    },
    'cities': {
        'location_tags': ['urban', 'city', 'downtown', 'city center'],
        'event_preference': True,  # Cities have more events
    },
    'villages': {
        'location_tags': ['village', 'rural', 'small town', 'countryside', 'quiet'],
    },
    'coast': {
        'location_tags': ['coast', 'beach', 'sea', 'ocean', 'harbor', 'maritime'],
    },
}

# Maps accommodation preferences to location types
ACCOMMODATION_MAPPINGS = {
    'camping': {
        'location_types': ['CAMPSITE'],
        'tags': ['camping', 'campground', 'tent'],
    },
    'wild': {
        'location_types': ['CAMPSITE', 'PARKING', 'REST_AREA'],
        'tags': ['wild camping', 'free camping', 'nature', 'off-grid'],
        'price_type': 'free',
    },
    'stellplatz': {
        'location_types': ['PARKING', 'REST_AREA', 'CAMPSITE'],
        'tags': ['stellplatz', 'camper parking', 'motorhome', 'aire'],
    },
    'hotel': {
        'location_types': ['HOTEL', 'ATTRACTION'],
        'tags': ['hotel', 'b&b', 'guesthouse'],
    },
}

# Plan templates with icons and descriptions
PLAN_TEMPLATES = {
    # Interest-based themed plans
    'nature': {'icon': '🏔️', 'title': 'Nature Escape', 'type': 'themed'},
    'history': {'icon': '🏛️', 'title': 'Historical Journey', 'type': 'themed'},
    'food': {'icon': '🍳', 'title': 'Foodie Adventure', 'type': 'themed'},
    'photography': {'icon': '📸', 'title': 'Photo Tour', 'type': 'themed'},
    'music': {'icon': '🎵', 'title': 'Music Night', 'type': 'themed'},
    'cycling': {'icon': '🚴', 'title': 'Cycling Day', 'type': 'themed'},
    'wine': {'icon': '🍷', 'title': 'Wine & Beer Trail', 'type': 'themed'},
    'architecture': {'icon': '🏰', 'title': 'Architecture Tour', 'type': 'themed'},

    # Environment-based plans
    'coast_day': {'icon': '🌊', 'title': 'Coastal Escape', 'type': 'environment'},
    'village_hopping': {'icon': '🏡', 'title': 'Village Discovery', 'type': 'environment'},
    'city_break': {'icon': '🏙️', 'title': 'City Explorer', 'type': 'environment'},

    # Distance-based plans
    'local': {'icon': '📍', 'title': 'Local Discovery', 'type': 'distance'},
    'day_trip': {'icon': '🚗', 'title': 'Day Trip', 'type': 'distance'},
    'weekend': {'icon': '🏕️', 'title': 'Weekend Getaway', 'type': 'distance'},
    'road_trip': {'icon': '🛣️', 'title': 'Road Trip', 'type': 'distance'},

    # Transit mode plans
    'transit_short': {'icon': '🛤️', 'title': 'Short Transit Day', 'type': 'transit'},
    'transit_full': {'icon': '🚐', 'title': 'Full Transit Day', 'type': 'transit'},
}


@dataclass
class ScoredEvent:
    """Event with preference score"""
    event: Event
    distance_km: float
    score: float
    match_reasons: List[str]


@dataclass
class ScoredLocation:
    """Location with preference score"""
    location: Location
    distance_km: float
    score: float
    match_reasons: List[str]


class PlanService:
    """Service for generating personalized day plans"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def suggest_plans(self, request: PlanSuggestRequest) -> PlanSuggestResponse:
        """
        Generate personalized plan suggestions based on user preferences.
        """
        prefs = request.preferences or UserPreferencesInput()
        is_transit_mode = (
            request.destination_latitude is not None and
            request.destination_longitude is not None
        )

        # 1. Fetch nearby events and locations
        events, locations = await self._fetch_nearby_items(request)

        # 2. Score items based on preferences
        scored_events = self._score_events(events, prefs)
        scored_locations = self._score_locations(locations, prefs)

        # 3. Generate plans
        plans = []

        # Generate interest-based themed plans
        if prefs.interests:
            themed_plans = self._generate_themed_plans(
                scored_events, scored_locations, prefs, request, is_transit_mode
            )
            plans.extend(themed_plans)

        # Generate environment-based plans
        if prefs.preferred_environment:
            env_plans = self._generate_environment_plans(
                scored_events, scored_locations, prefs, request, is_transit_mode
            )
            plans.extend(env_plans)

        # Generate distance-based plans (always include some)
        distance_plans = self._generate_distance_plans(
            scored_events, scored_locations, prefs, request, is_transit_mode
        )
        plans.extend(distance_plans)

        # Transit-specific plans
        if is_transit_mode:
            transit_plans = self._generate_transit_plans(
                scored_events, scored_locations, prefs, request
            )
            plans.extend(transit_plans)

        # 4. Sort by preference score and limit
        plans.sort(key=lambda p: p.preference_score, reverse=True)
        plans = plans[:request.max_plans]

        # 5. Build response
        destination = None
        if is_transit_mode:
            destination = {
                'latitude': request.destination_latitude,
                'longitude': request.destination_longitude,
                'name': request.destination_name,
            }

        return PlanSuggestResponse(
            plans=plans,
            total_plans=len(plans),
            current_location={
                'latitude': request.latitude,
                'longitude': request.longitude,
            },
            destination=destination,
            driving_envelope_km=request.driving_envelope_km,
            personalized=bool(prefs.interests or prefs.preferred_environment),
            preferences_applied=prefs if (prefs.interests or prefs.preferred_environment) else None,
        )

    async def _fetch_nearby_items(
        self, request: PlanSuggestRequest
    ) -> Tuple[List[Tuple[Event, float]], List[Tuple[Location, float]]]:
        """Fetch events and locations near the user's location"""
        start_point = func.ST_SetSRID(
            func.ST_MakePoint(request.longitude, request.latitude), 4326
        )

        # Determine search mode
        is_corridor = (
            request.destination_latitude is not None and
            request.destination_longitude is not None
        )

        if is_corridor:
            end_point = func.ST_SetSRID(
                func.ST_MakePoint(request.destination_longitude, request.destination_latitude), 4326
            )
            route_line = func.ST_MakeLine(start_point, end_point)
            corridor_meters = 30 * 1000  # 30km corridor on each side of route
            # For corridor search, use driving envelope as distance along the route, not from start
            max_distance_meters = request.driving_envelope_km * 1000
        else:
            # Radius search - use driving envelope + buffer
            search_radius_meters = min(request.driving_envelope_km + 50, 300) * 1000

        # Date range for events
        date_start = request.date_start or datetime.now()
        date_end = request.date_end or (date_start + timedelta(days=7))

        # Remove timezone info if present
        if date_start.tzinfo:
            date_start = date_start.replace(tzinfo=None)
        if date_end.tzinfo:
            date_end = date_end.replace(tzinfo=None)

        # Fetch events
        distance_expr = func.ST_Distance(
            func.cast(Event.geom, Geography),
            func.cast(start_point, Geography)
        ) / 1000.0

        event_query = select(Event, distance_expr.label('distance_km')).filter(
            and_(
                Event.active == True,
                Event.cancelled == False,
                or_(
                    Event.end_datetime >= date_start,
                    and_(Event.end_datetime.is_(None), Event.start_datetime >= date_start)
                ),
                Event.start_datetime <= date_end,
            )
        )

        if is_corridor:
            # In corridor mode, find items within 30km of the route
            # Don't filter by distance from start, as we want items along the entire route
            event_query = event_query.filter(
                func.ST_DWithin(
                    func.cast(Event.geom, Geography),
                    func.cast(route_line, Geography),
                    corridor_meters
                )
            )
        else:
            event_query = event_query.filter(
                func.ST_DWithin(
                    func.cast(Event.geom, Geography),
                    func.cast(start_point, Geography),
                    search_radius_meters
                )
            )

        event_query = event_query.order_by(distance_expr).limit(300)
        event_result = await self.db.execute(event_query)
        events = event_result.all()

        # Fetch locations
        loc_distance_expr = func.ST_Distance(
            func.cast(Location.geom, Geography),
            func.cast(start_point, Geography)
        ) / 1000.0

        location_query = select(Location, loc_distance_expr.label('distance_km')).filter(
            Location.active == True
        )

        if is_corridor:
            # In corridor mode, find items within 30km of the route
            # Don't filter by distance from start, as we want items along the entire route
            location_query = location_query.filter(
                func.ST_DWithin(
                    func.cast(Location.geom, Geography),
                    func.cast(route_line, Geography),
                    corridor_meters
                )
            )
        else:
            location_query = location_query.filter(
                func.ST_DWithin(
                    func.cast(Location.geom, Geography),
                    func.cast(start_point, Geography),
                    search_radius_meters
                )
            )

        location_query = location_query.order_by(loc_distance_expr).limit(300)
        location_result = await self.db.execute(location_query)
        locations = location_result.all()

        return events, locations

    def _is_boring_event(self, event: Event) -> bool:
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

    def _is_interesting_event(self, event: Event) -> bool:
        """Check if an event is particularly interesting for travelers"""
        # Interesting category
        if event.category and event.category in INTERESTING_CATEGORIES:
            return True

        # Interesting event type
        if event.event_type and event.event_type in INTERESTING_EVENT_TYPES:
            return True

        return False

    def _score_events(
        self, events: List[Tuple[Event, float]], prefs: UserPreferencesInput
    ) -> List[ScoredEvent]:
        """
        Score events based on user preferences and event quality.

        Filters out boring events (library activities, courses, sold out events)
        and prioritizes interesting events (concerts, festivals, theatre, food events).
        """
        scored = []

        for event, distance in events:
            # Skip boring events entirely
            if self._is_boring_event(event):
                continue

            score = 0.0
            reasons = []

            # Base score: interesting events get a boost
            if self._is_interesting_event(event):
                score += 0.4
                if event.category:
                    reasons.append(f"{event.category} event")

            # Distance score (but less weight - we care more about quality)
            distance_score = max(0, 1 - (distance / 300))  # 0-300km range
            score += distance_score * 0.1  # 10% weight for distance

            # Score based on user interests
            if prefs.interests:
                for interest in prefs.interests:
                    if interest in INTEREST_MAPPINGS:
                        mapping = INTEREST_MAPPINGS[interest]

                        # Check themes
                        event_themes = event.themes or []
                        event_themes_lower = [t.lower() for t in event_themes]
                        for theme in mapping.get('event_themes', []):
                            if any(theme in t for t in event_themes_lower):
                                score += 0.3
                                reasons.append(f"Matches your interest in {interest}")
                                break

                        # Check category
                        if event.category in mapping.get('event_categories', []):
                            score += 0.25
                            if f"Matches your interest in {interest}" not in reasons:
                                reasons.append(f"Matches your interest in {interest}")

                        # Check event type
                        if event.event_type:
                            event_type_lower = event.event_type.lower()
                            for et in mapping.get('event_types', []):
                                if et in event_type_lower:
                                    score += 0.2
                                    break

            # Budget scoring
            if prefs.budget == 'budget' and event.free:
                score += 0.1
                reasons.append("Free event")
            elif prefs.budget == 'comfort' and event.price and event.price > 20:
                score += 0.1
                reasons.append("Premium experience")

            # Normalize score to 0-1
            score = min(1.0, score)

            # Only include events with some relevance (skip very low scores)
            # Unless they're interesting events which we always want to show
            if score >= 0.2 or self._is_interesting_event(event):
                scored.append(ScoredEvent(
                    event=event,
                    distance_km=distance,
                    score=score,
                    match_reasons=reasons if reasons else ["Interesting event along your route"],
                ))

        # Sort by score (quality first, not distance)
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def _score_locations(
        self, locations: List[Tuple[Location, float]], prefs: UserPreferencesInput
    ) -> List[ScoredLocation]:
        """Score locations based on user preferences"""
        scored = []

        for location, distance in locations:
            score = 0.0
            reasons = []

            # Base score from distance
            distance_score = max(0, 1 - (distance / 300))
            score += distance_score * 0.15

            # Base score from rating
            if location.rating:
                rating_score = location.rating / 5.0
                score += rating_score * 0.2
                if location.rating >= 4.0:
                    reasons.append(f"Highly rated ({location.rating}★)")

            location_tags = location.tags or []
            location_tags_lower = [t.lower() for t in location_tags]

            # Score based on interests
            if prefs.interests:
                for interest in prefs.interests:
                    if interest in INTEREST_MAPPINGS:
                        mapping = INTEREST_MAPPINGS[interest]

                        # Check location type
                        if location.location_type in mapping.get('location_types', []):
                            score += 0.15

                        # Check tags
                        for tag in mapping.get('location_tags', []):
                            if any(tag in t for t in location_tags_lower):
                                score += 0.2
                                reasons.append(f"Good for {interest}")
                                break

            # Score based on environment preferences
            if prefs.preferred_environment:
                for env in prefs.preferred_environment:
                    if env in ENVIRONMENT_MAPPINGS:
                        mapping = ENVIRONMENT_MAPPINGS[env]

                        for tag in mapping.get('location_tags', []):
                            if any(tag in t for t in location_tags_lower):
                                score += 0.25
                                reasons.append(f"Matches your {env} preference")
                                break

                        # Check exclusions
                        for tag in mapping.get('exclude_tags', []):
                            if any(tag in t for t in location_tags_lower):
                                score -= 0.2
                                break

            # Score based on accommodation preferences
            if prefs.accommodation_types:
                for acc in prefs.accommodation_types:
                    if acc in ACCOMMODATION_MAPPINGS:
                        mapping = ACCOMMODATION_MAPPINGS[acc]

                        if location.location_type in mapping.get('location_types', []):
                            score += 0.2
                            reasons.append(f"Fits your {acc} preference")

                        if mapping.get('price_type') == 'free' and location.price_type == 'free':
                            score += 0.15
                            reasons.append("Free overnight spot")

            # Budget scoring for locations
            if prefs.budget == 'budget' and location.price_type == 'free':
                score += 0.1
            elif prefs.budget == 'comfort' and location.rating and location.rating >= 4.0:
                score += 0.1

            # Normalize
            score = min(1.0, max(0.0, score))

            scored.append(ScoredLocation(
                location=location,
                distance_km=distance,
                score=score,
                match_reasons=list(set(reasons)),  # Dedupe
            ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def _generate_themed_plans(
        self,
        scored_events: List[ScoredEvent],
        scored_locations: List[ScoredLocation],
        prefs: UserPreferencesInput,
        request: PlanSuggestRequest,
        is_transit_mode: bool,
    ) -> List[SuggestedPlanResponse]:
        """
        Generate plans based on user interests.

        Focus on events "along the way" - within driving envelope distance,
        prioritizing those that match user interests.
        """
        plans = []
        envelope = request.driving_envelope_km

        for interest in prefs.interests:
            if interest not in PLAN_TEMPLATES:
                continue

            template = PLAN_TEMPLATES[interest]
            mapping = INTEREST_MAPPINGS.get(interest, {})

            # Find events matching this interest that are "along the way"
            # (within driving envelope distance)
            matching_events = []
            for se in scored_events:
                # Only include events within driving envelope
                if se.distance_km > envelope:
                    continue

                event_themes = [t.lower() for t in (se.event.themes or [])]
                category_match = se.event.category in mapping.get('event_categories', [])
                theme_match = any(
                    t in ' '.join(event_themes)
                    for t in mapping.get('event_themes', [])
                )

                if category_match or theme_match:
                    matching_events.append(se)
                    if len(matching_events) >= request.max_items_per_plan:
                        break

            # Find locations (POIs) matching this interest
            matching_locations = []
            for sl in scored_locations:
                # Only include locations within driving envelope
                if sl.distance_km > envelope:
                    continue

                # Check if location type matches
                location_type_match = sl.location.location_type in mapping.get('location_types', [])

                # Check if location tags match
                location_tags = [t.lower() for t in (sl.location.tags or [])]
                tag_match = any(
                    t in ' '.join(location_tags)
                    for t in mapping.get('location_tags', [])
                )

                if location_type_match or tag_match:
                    matching_locations.append(sl)
                    if len(matching_locations) >= request.max_items_per_plan:
                        break

            # Skip if no matching events or locations
            if not matching_events and not matching_locations:
                continue

            # Find 3 overnight locations near driving envelope (~5km before/after)
            overnight_locations = self._get_overnight_locations(
                scored_locations, prefs, request, is_transit_mode
            )

            # Calculate plan score from both events and locations
            all_items = matching_events + matching_locations
            plan_score = sum(
                item.score for item in all_items
            ) / max(1, len(all_items))

            # Build plan - use driving envelope as total_km since we're focusing on events along the way
            plan = SuggestedPlanResponse(
                id=f"themed-{interest}",
                plan_type='themed',
                title=template['title'],
                description=self._generate_description(interest, matching_events, is_transit_mode),
                icon=template['icon'],
                total_km=envelope,  # Use driving envelope as total distance
                estimated_hours=envelope / 50,  # ~50km/h average
                events=[self._event_to_response(se) for se in matching_events],
                stops=[self._location_to_response(sl) for sl in matching_locations[:5]],  # Include up to 5 POIs
                overnight=[self._location_to_response(sl) for sl in overnight_locations],  # Now returns 3
                preference_score=plan_score,
                match_reasons=[
                    f"Events matching your interest in {interest} along your route",
                    f"{len(matching_locations)} {interest}-related POIs to visit" if matching_locations else None
                ],
                is_transit_plan=is_transit_mode,
            )
            # Filter out None values from match_reasons
            plan.match_reasons = [r for r in plan.match_reasons if r]
            plans.append(plan)

        return plans

    def _generate_environment_plans(
        self,
        scored_events: List[ScoredEvent],
        scored_locations: List[ScoredLocation],
        prefs: UserPreferencesInput,
        request: PlanSuggestRequest,
        is_transit_mode: bool,
    ) -> List[SuggestedPlanResponse]:
        """Generate plans based on environment preferences"""
        plans = []

        env_plan_mapping = {
            'coast': 'coast_day',
            'villages': 'village_hopping',
            'cities': 'city_break',
        }

        for env in prefs.preferred_environment:
            plan_key = env_plan_mapping.get(env)
            if not plan_key or plan_key not in PLAN_TEMPLATES:
                continue

            template = PLAN_TEMPLATES[plan_key]
            mapping = ENVIRONMENT_MAPPINGS.get(env, {})

            # Find locations matching this environment
            matching_locations = []
            for sl in scored_locations:
                location_tags = [t.lower() for t in (sl.location.tags or [])]
                tag_match = any(
                    t in ' '.join(location_tags)
                    for t in mapping.get('location_tags', [])
                )
                if tag_match:
                    matching_locations.append(sl)
                    if len(matching_locations) >= request.max_items_per_plan:
                        break

            if not matching_locations:
                continue

            # Get events in same area
            area_events = [
                se for se in scored_events
                if se.distance_km <= max(sl.distance_km for sl in matching_locations) + 20
            ][:3]

            plan_score = (
                sum(sl.score for sl in matching_locations) / max(1, len(matching_locations))
            )

            avg_distance = sum(sl.distance_km for sl in matching_locations) / max(1, len(matching_locations))

            plan = SuggestedPlanResponse(
                id=f"env-{env}",
                plan_type='environment',
                title=template['title'],
                description=f"Explore {env} areas with {len(matching_locations)} great stops",
                icon=template['icon'],
                total_km=int(avg_distance * 2),
                estimated_hours=avg_distance / 50,
                events=[self._event_to_response(se) for se in area_events],
                stops=[self._location_to_response(sl) for sl in matching_locations[:3]],
                overnight=[self._location_to_response(sl) for sl in matching_locations[-2:]],
                preference_score=plan_score,
                match_reasons=[f"Based on your preference for {env} areas"],
                is_transit_plan=is_transit_mode,
            )
            plans.append(plan)

        return plans

    def _generate_distance_plans(
        self,
        scored_events: List[ScoredEvent],
        scored_locations: List[ScoredLocation],
        prefs: UserPreferencesInput,
        request: PlanSuggestRequest,
        is_transit_mode: bool,
    ) -> List[SuggestedPlanResponse]:
        """Generate distance-based plans (local, day trip, weekend, road trip)"""
        plans = []
        envelope = request.driving_envelope_km

        # Local discovery (0-30km) - only if not in transit mode
        if not is_transit_mode:
            local_events = [se for se in scored_events if se.distance_km <= 30]
            local_locations = [sl for sl in scored_locations if sl.distance_km <= 30]

            if local_events or local_locations:
                template = PLAN_TEMPLATES['local']
                plan = SuggestedPlanResponse(
                    id='distance-local',
                    plan_type='distance',
                    title=template['title'],
                    description=f"{len(local_events)} events within walking/cycling distance",
                    icon=template['icon'],
                    total_km=0,
                    estimated_hours=0,
                    events=[self._event_to_response(se) for se in local_events[:4]],
                    stops=[self._location_to_response(sl) for sl in local_locations[:2]],
                    overnight=[],
                    preference_score=self._calc_avg_score(local_events, local_locations),
                    match_reasons=["Explore your immediate surroundings"],
                    is_transit_plan=False,
                )
                plans.append(plan)

        # Day trip (30-80km) - now allowed in transit mode for smaller envelopes
        if envelope >= 30 and envelope < 100:
            day_events = [se for se in scored_events if 30 <= se.distance_km <= 80]
            day_locations = [sl for sl in scored_locations if 30 <= sl.distance_km <= 80]

            if day_events or day_locations:
                template = PLAN_TEMPLATES['day_trip']
                description = "Explore a nearby town and return home" if not is_transit_mode else f"Stops on your way to destination"
                plan = SuggestedPlanResponse(
                    id='distance-daytrip',
                    plan_type='distance',
                    title=template['title'],
                    description=description,
                    icon=template['icon'],
                    total_km=100,
                    estimated_hours=2,
                    events=[self._event_to_response(se) for se in day_events[:3]],
                    stops=[self._location_to_response(sl) for sl in day_locations[:2]],
                    overnight=[],
                    preference_score=self._calc_avg_score(day_events, day_locations),
                    match_reasons=["Perfect for a day out"] if not is_transit_mode else ["Interesting stops along your route"],
                    is_transit_plan=is_transit_mode,
                )
                plans.append(plan)

        # Weekend getaway (80-200km)
        if envelope >= 80:
            weekend_events = [se for se in scored_events if 80 <= se.distance_km <= 200]
            weekend_locations = [sl for sl in scored_locations if 80 <= sl.distance_km <= 200]
            overnight = self._get_overnight_locations(scored_locations, prefs, request, False)

            if weekend_events or weekend_locations:
                template = PLAN_TEMPLATES['weekend']
                plan = SuggestedPlanResponse(
                    id='distance-weekend',
                    plan_type='distance',
                    title=template['title'],
                    description="Overnight adventure with scenic camping",
                    icon=template['icon'],
                    total_km=150,
                    estimated_hours=3,
                    events=[self._event_to_response(se) for se in weekend_events[:3]],
                    stops=[self._location_to_response(sl) for sl in weekend_locations[:3]],
                    overnight=[self._location_to_response(sl) for sl in overnight[:2]],
                    preference_score=self._calc_avg_score(weekend_events, weekend_locations),
                    match_reasons=["Great for a weekend escape"],
                    is_transit_plan=False,
                )
                plans.append(plan)

        # Road trip (200km+)
        if envelope >= 200:
            road_events = [se for se in scored_events if se.distance_km >= 150]
            road_locations = [sl for sl in scored_locations if sl.distance_km >= 150]
            far_overnight = [sl for sl in scored_locations if sl.distance_km >= envelope - 50]

            if road_events or road_locations or far_overnight:
                template = PLAN_TEMPLATES['road_trip']
                plan = SuggestedPlanResponse(
                    id='distance-roadtrip',
                    plan_type='distance',
                    title=template['title'],
                    description=f"Long-distance adventure ({envelope}km today)",
                    icon=template['icon'],
                    total_km=envelope,
                    estimated_hours=envelope / 60,
                    events=[self._event_to_response(se) for se in road_events[:3]],
                    stops=[self._location_to_response(sl) for sl in road_locations[:4]],
                    overnight=[self._location_to_response(sl) for sl in far_overnight[:2]],
                    preference_score=self._calc_avg_score(road_events, road_locations),
                    match_reasons=["For the adventurous traveler"],
                    is_transit_plan=False,
                )
                plans.append(plan)

        return plans

    def _generate_transit_plans(
        self,
        scored_events: List[ScoredEvent],
        scored_locations: List[ScoredLocation],
        prefs: UserPreferencesInput,
        request: PlanSuggestRequest,
    ) -> List[SuggestedPlanResponse]:
        """
        Generate plans optimized for transit toward destination.

        Focus on events along the route that match user interests,
        with 3 overnight options near the driving envelope.
        """
        plans = []
        envelope = request.driving_envelope_km

        # Get events that match user interests (along the way)
        def get_matching_events(events: List[ScoredEvent], max_distance: float) -> List[ScoredEvent]:
            """Get events within max_distance that match user interests"""
            matching = []
            for se in events:
                if se.distance_km > max_distance:
                    continue
                # Prioritize events with higher scores (which means they match interests)
                if se.score >= 0.2 or not prefs.interests:  # Include all if no preferences
                    matching.append(se)
            # Sort by score to get best matches first
            matching.sort(key=lambda x: -x.score)
            return matching

        # Short transit day (stop halfway)
        half_distance = envelope * 0.5
        half_events = get_matching_events(scored_events, half_distance + 20)[:3]
        half_locations = [sl for sl in scored_locations if abs(sl.distance_km - half_distance) <= 20]

        # Get 3 overnight locations near halfway point
        half_overnight = [
            sl for sl in scored_locations
            if sl.location.location_type in ['CAMPSITE', 'PARKING', 'REST_AREA']
            and abs(sl.distance_km - half_distance) <= 10
        ]
        half_overnight.sort(key=lambda x: (abs(x.distance_km - half_distance), -x.score))

        if half_events or half_locations:
            template = PLAN_TEMPLATES['transit_short']
            plan = SuggestedPlanResponse(
                id='transit-short',
                plan_type='transit',
                title=template['title'],
                description=f"Shorter drive option • Stop around {int(half_distance)}km",
                icon=template['icon'],
                total_km=int(half_distance),
                estimated_hours=half_distance / 60,
                events=[self._event_to_response(se) for se in half_events],
                stops=[self._location_to_response(sl) for sl in half_locations[:3]],
                overnight=[self._location_to_response(sl) for sl in half_overnight[:3]],
                preference_score=self._calc_avg_score(half_events, half_locations),
                match_reasons=["Take it easy with a shorter drive"],
                is_transit_plan=True,
                progress_toward_destination=0.5,
            )
            plans.append(plan)

        # Full transit day
        target_distance = envelope
        target_events = get_matching_events(scored_events, target_distance)[:5]

        # Get 3 overnight locations near target distance (~5km before/after)
        target_overnight = self._get_overnight_locations(
            scored_locations, prefs, request, True
        )

        if target_events or target_overnight:
            template = PLAN_TEMPLATES['transit_full']
            dest_name = request.destination_name or 'destination'
            plan = SuggestedPlanResponse(
                id='transit-full',
                plan_type='transit',
                title=template['title'],
                description=f"Drive {envelope}km toward {dest_name} with stops matching your interests",
                icon=template['icon'],
                total_km=envelope,
                estimated_hours=envelope / 60,
                events=[self._event_to_response(se) for se in target_events],
                stops=[],  # Events are the main stops
                overnight=[self._location_to_response(sl) for sl in target_overnight],
                preference_score=self._calc_avg_score(target_events, []),
                match_reasons=["Events matching your interests along the route"],
                is_transit_plan=True,
                progress_toward_destination=1.0,
            )
            plans.append(plan)

        return plans

    def _get_overnight_locations(
        self,
        scored_locations: List[ScoredLocation],
        prefs: UserPreferencesInput,
        request: PlanSuggestRequest,
        is_transit_mode: bool,
    ) -> List[ScoredLocation]:
        """
        Get suitable overnight locations based on preferences.

        Returns 3 options near the driving envelope distance (~5km before/after).
        """
        # Filter to camping-type locations
        overnight_types = ['CAMPSITE', 'PARKING', 'REST_AREA']

        # Adjust based on accommodation preferences
        if prefs.accommodation_types:
            for acc in prefs.accommodation_types:
                if acc in ACCOMMODATION_MAPPINGS:
                    overnight_types.extend(ACCOMMODATION_MAPPINGS[acc].get('location_types', []))

        overnight_types = list(set(overnight_types))

        candidates = [
            sl for sl in scored_locations
            if sl.location.location_type in overnight_types
        ]

        # Target distance is the driving envelope
        target = request.driving_envelope_km
        # Allow ~5km before and after the target distance
        tolerance = 5

        # Filter to locations within tolerance of target distance
        # But also include some options if we don't have enough near target
        near_target = [
            sl for sl in candidates
            if abs(sl.distance_km - target) <= tolerance
        ]

        # If not enough near target, expand search to ~15km tolerance
        if len(near_target) < 3:
            near_target = [
                sl for sl in candidates
                if abs(sl.distance_km - target) <= 15
            ]

        # Sort by: closeness to target distance, then by score
        near_target.sort(key=lambda x: (abs(x.distance_km - target), -x.score))

        # Return top 3 overnight options near the driving envelope
        return near_target[:3]

    def _event_to_response(self, se: ScoredEvent) -> PlanItemResponse:
        """Convert scored event to response"""
        event = se.event
        return PlanItemResponse(
            id=f"event-{event.id}",
            item_type='event',
            name=event.name,
            description=event.description,
            latitude=event.latitude,
            longitude=event.longitude,
            distance_km=round(se.distance_km, 1),
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            price=event.price,
            free=event.free,
            category=event.category,
            event_type=event.event_type,
            themes=event.themes or [],
            city=event.city,
            address=event.address or event.venue_name,
            website=event.website,
            image=event.images[0] if event.images else None,
            preference_score=se.score,
            match_reasons=se.match_reasons,
        )

    def _location_to_response(self, sl: ScoredLocation) -> PlanItemResponse:
        """Convert scored location to response"""
        loc = sl.location
        # Ensure amenities is a dict or None (not empty list)
        amenities = loc.amenities if isinstance(loc.amenities, dict) and loc.amenities else None
        return PlanItemResponse(
            id=f"loc-{loc.id}",
            item_type='location',
            name=loc.name,
            description=loc.description,
            latitude=loc.latitude,
            longitude=loc.longitude,
            distance_km=round(sl.distance_km, 1),
            location_type=loc.location_type,
            rating=loc.rating,
            price_type=loc.price_type,
            tags=loc.tags or [],
            amenities=amenities,
            city=loc.city,
            address=loc.address,
            website=loc.website,
            image=loc.main_image_url or (loc.images[0] if isinstance(loc.images, list) and loc.images else None),
            preference_score=sl.score,
            match_reasons=sl.match_reasons,
        )

    def _calc_avg_score(
        self,
        events: List[ScoredEvent],
        locations: List[ScoredLocation]
    ) -> float:
        """Calculate average preference score"""
        all_scores = [e.score for e in events] + [l.score for l in locations]
        if not all_scores:
            return 0.0
        return sum(all_scores) / len(all_scores)

    def _generate_description(
        self, interest: str, events: List[ScoredEvent], is_transit: bool
    ) -> str:
        """Generate a description for the plan"""
        count = len(events)
        if is_transit:
            return f"{count} {interest}-related stops along your route"

        descriptions = {
            'nature': f"{count} outdoor experiences and nature spots",
            'history': f"{count} historical sites and cultural events",
            'food': f"{count} culinary experiences and food events",
            'photography': f"{count} photogenic spots and exhibitions",
            'music': f"{count} concerts and music events",
            'cycling': f"{count} cycling-friendly stops and events",
            'wine': f"{count} wine and beer tasting experiences",
            'architecture': f"{count} architectural highlights and tours",
        }
        return descriptions.get(interest, f"{count} events matching your interests")
