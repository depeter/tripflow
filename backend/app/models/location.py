from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from enum import Enum
from .base import Base, TimestampMixin


class LocationType(str, Enum):
    CAMPSITE = "campsite"
    PARKING = "parking"
    REST_AREA = "rest_area"
    ATTRACTION = "attraction"
    POI = "poi"
    EVENT_VENUE = "event_venue"


class LocationSource(str, Enum):
    PARK4NIGHT = "park4night"
    CAMPERCONTACT = "campercontact"
    LOCAL_SITES = "local_sites"
    MANUAL = "manual"


class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)

    # External reference
    external_id = Column(String, index=True, nullable=True)  # ID from source database
    source = Column(SQLEnum(LocationSource), nullable=False, index=True)

    # Basic info
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    location_type = Column(SQLEnum(LocationType), nullable=False, index=True)

    # Geographic data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', srid=4326), nullable=False)  # PostGIS geometry

    address = Column(String)
    city = Column(String, index=True)
    region = Column(String, index=True)
    country = Column(String, index=True)
    postal_code = Column(String)

    # Amenities and features
    amenities = Column(ARRAY(String), default=[])  # ["wifi", "water", "electricity", "toilet", "shower"]
    features = Column(JSON, default={})  # Flexible structure for location-specific features

    # Ratings and reviews
    rating = Column(Float)  # Average rating
    review_count = Column(Integer, default=0)

    # Practical information
    price = Column(Float)  # Price per night or visit
    currency = Column(String, default="EUR")
    capacity = Column(Integer)  # Number of spots/spaces

    # Availability
    open_year_round = Column(Boolean, default=False)
    opening_hours = Column(JSON)  # Flexible structure for opening hours

    # Contact
    phone = Column(String)
    email = Column(String)
    website = Column(String)

    # Media
    images = Column(ARRAY(String), default=[])  # URLs to images

    # Categorization (for recommendations)
    tags = Column(ARRAY(String), default=[], index=True)  # ["nature", "beach", "family-friendly", "hiking"]
    categories = Column(ARRAY(String), default=[])  # ["outdoor", "cultural", "sports"]

    # Status
    active = Column(Boolean, default=True, index=True)
    verified = Column(Boolean, default=False)

    # Sync metadata
    last_synced_at = Column(DateTime)

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', type={self.location_type})>"
