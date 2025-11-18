from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from enum import Enum
from .base import Base, TimestampMixin


class EventCategory(str, Enum):
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


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # External reference
    external_id = Column(String, index=True, nullable=True)
    source_url = Column(String)

    # Basic info
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    category = Column(SQLEnum(EventCategory), nullable=False, index=True)

    # Dates and times
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, index=True)
    all_day = Column(Boolean, default=False)

    # Location
    venue_name = Column(String)
    address = Column(String)
    city = Column(String, index=True)
    region = Column(String)
    country = Column(String, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry('POINT', srid=4326), nullable=False)

    # Optionally link to a Location if the event is at a known location
    location_id = Column(Integer, ForeignKey("tripflow.locations.id"), nullable=True, index=True)

    # Details
    price = Column(Float)
    currency = Column(String, default="EUR")
    free = Column(Boolean, default=False)

    # Contact and booking
    website = Column(String)
    booking_url = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)

    # Media
    images = Column(ARRAY(String), default=[])

    # Categorization
    tags = Column(ARRAY(String), default=[], index=True)

    # Additional metadata from source
    organizer = Column(String)
    event_type = Column(String)  # Original event type from source
    themes = Column(ARRAY(String), default=[])  # Themes/topics
    source = Column(String, default='manual')  # 'uitinvlaanderen', 'manual', etc.

    # Status
    active = Column(Boolean, default=True, index=True)
    cancelled = Column(Boolean, default=False)

    # Scraping metadata
    last_scraped_at = Column(DateTime)

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', category={self.category})>"
