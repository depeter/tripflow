from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, ENUM as PG_ENUM
from geoalchemy2 import Geometry
from enum import Enum
from .base import Base, TimestampMixin


class LocationType(str, Enum):
    CAMPSITE = "CAMPSITE"
    PARKING = "PARKING"
    REST_AREA = "REST_AREA"
    SERVICE_AREA = "SERVICE_AREA"
    POI = "POI"
    EVENT = "EVENT"
    ATTRACTION = "ATTRACTION"
    RESTAURANT = "RESTAURANT"
    HOTEL = "HOTEL"
    ACTIVITY = "ACTIVITY"


class LocationSource(str, Enum):
    PARK4NIGHT = "park4night"
    CAMPERCONTACT = "campercontact"
    UITINVLAANDEREN = "uitinvlaanderen"
    OPENSTREETMAP = "openstreetmap"
    GOOGLE_PLACES = "google_places"
    MANUAL = "manual"
    OTHER = "other"


class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)

    # External reference
    external_id = Column(String, index=True, nullable=True)  # ID from source database
    source = Column(
        PG_ENUM('park4night', 'campercontact', 'uitinvlaanderen', 'openstreetmap',
                'google_places', 'manual', 'other',
                name='location_source', schema='tripflow', create_type=False),
        nullable=False, index=True
    )

    # Basic info
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    location_type = Column(
        PG_ENUM('CAMPSITE', 'PARKING', 'REST_AREA', 'SERVICE_AREA', 'POI', 'EVENT',
                'ATTRACTION', 'RESTAURANT', 'HOTEL', 'ACTIVITY',
                name='location_type', schema='tripflow', create_type=False),
        nullable=False, index=True
    )

    # Geographic data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', srid=4326), nullable=False)  # PostGIS geometry
    altitude = Column(Integer)

    address = Column(String)
    city = Column(String, index=True)
    region = Column(String, index=True)
    country = Column(String, index=True)
    country_code = Column(String)
    postal_code = Column(String)

    # Amenities and features (JSONB in DB)
    amenities = Column(JSONB)
    features = Column(JSONB)
    restrictions = Column(JSONB)

    # Ratings and reviews
    rating = Column(Float)
    rating_count = Column(Integer)
    review_count = Column(Integer, default=0)
    popularity_score = Column(Float)

    # Practical information (matches DB schema)
    price_type = Column(
        PG_ENUM('free', 'paid', 'donation', 'unknown',
                name='price_type', schema='tripflow', create_type=False),
        nullable=True
    )
    price_min = Column(Float)
    price_max = Column(Float)
    price_currency = Column(String, default="EUR")
    price_info = Column(Text)
    capacity_total = Column(Integer)
    capacity_available = Column(Integer)

    # Availability
    is_24_7 = Column(Boolean, default=False)
    opening_hours = Column(JSONB)  # Flexible structure for opening hours
    seasonal_info = Column(Text)

    # Contact
    phone = Column(String)
    email = Column(String)
    website = Column(String)

    # Media (JSONB in DB)
    images = Column(JSONB)
    main_image_url = Column(String)

    # Categorization (for recommendations)
    tags = Column(ARRAY(String), default=[])  # ["nature", "beach", "family-friendly", "hiking"]

    # Status
    active = Column('is_active', Boolean, default=True, index=True)  # Maps to is_active in DB
    verified = Column('is_verified', Boolean, default=False)  # Maps to is_verified in DB
    is_featured = Column(Boolean, default=False)
    requires_booking = Column(Boolean, default=False)

    # Sync metadata
    raw_data = Column(JSONB)
    last_verified_at = Column(DateTime)

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', type={self.location_type})>"
