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
    waypoints: List[Dict[str, Any]] = []
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
