from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


# Enums
class LocationTypeEnum(str, Enum):
    CAMPSITE = "campsite"
    PARKING = "parking"
    REST_AREA = "rest_area"
    ATTRACTION = "attraction"
    POI = "poi"
    EVENT_VENUE = "event_venue"


class TripStatusEnum(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Location schemas
class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    location_type: LocationTypeEnum
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    amenities: List[str] = []
    rating: Optional[float] = None
    price: Optional[float] = None
    website: Optional[str] = None
    images: List[str] = []
    tags: List[str] = []


class LocationResponse(LocationBase):
    id: int
    review_count: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LocationWithDistance(LocationResponse):
    distance_km: Optional[float] = None
    score: Optional[float] = None


# Trip schemas
class TripCreate(BaseModel):
    start_address: str
    end_address: Optional[str] = None
    max_distance_km: Optional[int] = Field(None, ge=1, le=10000)
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    trip_preferences: Optional[Dict[str, Any]] = {}


class TripResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str]
    status: TripStatusEnum
    start_address: str
    start_latitude: float
    start_longitude: float
    end_address: Optional[str]
    end_latitude: Optional[float]
    end_longitude: Optional[float]
    max_distance_km: Optional[int]
    duration_days: Optional[int]
    waypoints: Optional[List[Dict[str, Any]]] = None
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class WaypointAdd(BaseModel):
    location_id: int
    order: Optional[int] = None


class TripFinalize(BaseModel):
    start_date: date


class TripStats(BaseModel):
    total_distance_km: float
    num_stops: int
    estimated_driving_hours: float
    estimated_driving_days: float


# User schemas
class UserPreferenceCreate(BaseModel):
    interests: List[str] = []
    preferred_amenities: List[str] = []
    max_price_per_night: Optional[float] = None
    activity_level: str = "moderate"
    preferred_activities: List[str] = []
    preferred_environment: List[str] = []
    avoid_crowded: bool = False


class UserPreferenceResponse(UserPreferenceCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# Search schemas
class LocationSearchParams(BaseModel):
    query: Optional[str] = None
    location_types: Optional[List[LocationTypeEnum]] = None
    amenities: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_price: Optional[float] = Field(None, ge=0)
    limit: int = Field(20, ge=1, le=100)


class NearbySearchParams(BaseModel):
    latitude: float
    longitude: float
    radius_km: int = Field(50, ge=1, le=500)
    location_types: Optional[List[LocationTypeEnum]] = None
    limit: int = Field(20, ge=1, le=100)


class RecommendationParams(BaseModel):
    user_id: Optional[int] = None
    near_latitude: Optional[float] = None
    near_longitude: Optional[float] = None
    radius_km: Optional[int] = Field(50, ge=1, le=500)
    interests: Optional[List[str]] = None
    limit: int = Field(20, ge=1, le=100)


class WaypointSuggestionParams(BaseModel):
    num_stops: int = Field(3, ge=1, le=10)


# Geocoding schemas
class GeocodeRequest(BaseModel):
    address: str


class GeocodeResponse(BaseModel):
    latitude: float
    longitude: float
    display_name: str


class ReverseGeocodeResponse(BaseModel):
    address: str
    city: str
    country: str


# Sync schemas
class SyncRequest(BaseModel):
    source: Optional[str] = None  # 'park4night', 'campercontact', 'local_sites', or None for all
    batch_size: int = Field(100, ge=1, le=1000)
    limit: Optional[int] = None


class SyncResponse(BaseModel):
    source: str
    fetched: int
    inserted: int
    updated: int
    errors: int
    duration_seconds: float


# Event schemas (for Discovery Mode)
class EventCategoryEnum(str, Enum):
    FESTIVAL = "festival"
    CONCERT = "concert"
    SPORTS = "sports"
    MARKET = "market"
    EXHIBITION = "exhibition"
    THEATER = "theater"
    CULTURAL = "cultural"
    FOOD = "food"
    OUTDOOR = "outdoor"
    OTHER = "other"


class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str  # Changed from EventCategoryEnum to str to match DB VARCHAR
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    all_day: bool
    venue_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float
    price: Optional[float] = None
    currency: str = "EUR"
    free: bool
    website: Optional[str] = None
    images: List[str] = []
    tags: List[str] = []
    organizer: Optional[str] = None
    event_type: Optional[str] = None
    themes: List[str] = []
    source: str
    distance_km: Optional[float] = None
    score: Optional[float] = Field(None, description="Quality/relevance score (0-1, higher is better)")

    class Config:
        from_attributes = True


class EventFiltersSchema(BaseModel):
    """Event-specific filters"""
    categories: Optional[List[str]] = Field(None, description="Filter by event categories (FESTIVAL, CONCERT, etc.)")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types (festival, workshop, etc.)")
    date_start: Optional[datetime] = Field(None, description="Only events after this date")
    date_end: Optional[datetime] = Field(None, description="Only events before this date")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    free_only: bool = Field(False, description="Only show free events")
    time_of_day: Optional[List[str]] = Field(None, description="Filter by time periods: morning, afternoon, evening, night")


class LocationFiltersSchema(BaseModel):
    """Location-specific filters"""
    location_types: Optional[List[str]] = Field(None, description="Filter by location types (CAMPSITE, PARKING, etc.)")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum star rating")
    price_types: Optional[List[str]] = Field(None, description="Filter by price types: free, paid_low, paid_medium, paid_high, paid_premium")
    amenities: Optional[List[str]] = Field(None, description="Required amenities (wifi, electricity, showers, etc.)")
    features: Optional[List[str]] = Field(None, description="Required facilities (restaurant, shop, laundry, etc.)")
    open_now: bool = Field(False, description="Only show currently open locations")
    is_24_7: bool = Field(False, description="Only show 24/7 accessible locations")
    no_booking_required: bool = Field(False, description="Only show locations without booking requirement")
    min_capacity: Optional[int] = Field(None, ge=1, description="Minimum available capacity")


class DiscoverySearchParams(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: int = Field(25, ge=1, le=200, description="Search radius in kilometers (used for point search)")
    item_types: Optional[List[str]] = Field(["events", "locations"], description="Types to show: events, locations, or both")
    search_text: Optional[str] = Field(None, description="Search text for name/description/themes")
    limit: int = Field(200, ge=1, le=500, description="Max results per type")

    # Route-based search (corridor mode) - when destination is provided, searches along route instead of radius
    destination_latitude: Optional[float] = Field(None, ge=-90, le=90, description="Destination latitude for route-based search")
    destination_longitude: Optional[float] = Field(None, ge=-180, le=180, description="Destination longitude for route-based search")
    corridor_width_km: int = Field(30, ge=5, le=100, description="Width of search corridor around route in km")
    max_distance_km: Optional[int] = Field(None, ge=1, le=600, description="Max distance along route to search (today's driving range)")

    # Structured filters
    event_filters: Optional[EventFiltersSchema] = Field(None, description="Event-specific filters")
    location_filters: Optional[LocationFiltersSchema] = Field(None, description="Location-specific filters")

    # Legacy fields for backward compatibility (deprecated)
    categories: Optional[List[str]] = Field(None, deprecated=True)
    event_types: Optional[List[str]] = Field(None, deprecated=True)
    start_date: Optional[datetime] = Field(None, deprecated=True)
    end_date: Optional[datetime] = Field(None, deprecated=True)
    free_only: bool = Field(False, deprecated=True)


class LocationDiscoveryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    location_type: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    price_type: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    website: Optional[str] = None
    main_image_url: Optional[str] = None
    images: Optional[Any] = None  # Can be list or dict in JSONB
    tags: List[str] = []
    source: str
    distance_km: Optional[float] = None
    item_type: str = "location"

    class Config:
        from_attributes = True


class DiscoveryResponse(BaseModel):
    events: List[EventResponse] = []
    locations: List[LocationDiscoveryResponse] = []
    total_count: int
    search_center: Dict[str, float]  # {"latitude": x, "longitude": y}
    radius_km: int


# ============ Personalized Plans Schemas ============

class UserPreferencesInput(BaseModel):
    """User preferences for personalized plan generation"""
    # Interests (from profile)
    interests: List[str] = Field(
        default=[],
        description="User interests: nature, history, food, photography, music, cycling, wine, architecture"
    )
    # Environment preferences
    preferred_environment: List[str] = Field(
        default=[],
        description="Preferred environments: nature, cities, villages, coast"
    )
    # Accommodation preferences
    accommodation_types: List[str] = Field(
        default=[],
        description="Preferred accommodation: camping, wild, stellplatz, hotel"
    )
    # Travel pace
    travel_pace: str = Field(
        default="moderate",
        description="Travel pace: slow (50-100km/day), moderate (100-200km/day), fast (200+km/day)"
    )
    # Budget preference
    budget: str = Field(
        default="mid-range",
        description="Budget level: budget, mid-range, comfort"
    )


class PlanSuggestRequest(BaseModel):
    """Request for personalized plan suggestions"""
    # Location
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    # Optional destination for transit mode
    destination_latitude: Optional[float] = Field(None, ge=-90, le=90)
    destination_longitude: Optional[float] = Field(None, ge=-180, le=180)
    destination_name: Optional[str] = None

    # Driving envelope (how far user wants to drive today)
    driving_envelope_km: int = Field(default=100, ge=0, le=600)

    # User preferences (if not provided, returns generic plans)
    preferences: Optional[UserPreferencesInput] = None

    # Date range for events
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None

    # Limits
    max_plans: int = Field(default=8, ge=1, le=20)
    max_items_per_plan: int = Field(default=5, ge=1, le=10)


class PlanItemResponse(BaseModel):
    """A single item (event or location) in a plan"""
    id: str
    item_type: str  # 'event' or 'location'
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    distance_km: float

    # Event-specific
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    price: Optional[float] = None
    free: Optional[bool] = None
    category: Optional[str] = None
    event_type: Optional[str] = None
    themes: List[str] = []

    # Location-specific
    location_type: Optional[str] = None
    rating: Optional[float] = None
    price_type: Optional[str] = None
    tags: List[str] = []
    amenities: Optional[Dict[str, Any]] = None

    # Common
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    image: Optional[str] = None

    # Scoring
    preference_score: float = Field(default=0.0, description="How well this matches user preferences (0-1)")
    match_reasons: List[str] = Field(default=[], description="Why this item matches user preferences")


class SuggestedPlanResponse(BaseModel):
    """A suggested day plan"""
    id: str
    plan_type: str  # 'themed', 'distance', 'transit'
    title: str
    description: str
    icon: str  # emoji

    # Distance info
    total_km: int
    estimated_hours: float

    # Items in the plan
    events: List[PlanItemResponse] = []
    stops: List[PlanItemResponse] = []  # POIs, rest stops along the way
    overnight: List[PlanItemResponse] = []  # Overnight locations

    # Scoring
    preference_score: float = Field(default=0.0, description="Overall plan match score (0-1)")
    match_reasons: List[str] = Field(default=[], description="Why this plan was suggested")

    # For transit mode
    is_transit_plan: bool = False
    progress_toward_destination: Optional[float] = None  # 0-1, how much closer to destination


class PlanSuggestResponse(BaseModel):
    """Response with personalized plan suggestions"""
    plans: List[SuggestedPlanResponse]
    total_plans: int

    # User context
    current_location: Dict[str, float]
    destination: Optional[Dict[str, Any]] = None
    driving_envelope_km: int

    # Whether preferences were applied
    personalized: bool
    preferences_applied: Optional[UserPreferencesInput] = None
