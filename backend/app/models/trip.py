from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from enum import Enum
from .base import Base, TimestampMixin


class TripStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Trip(Base, TimestampMixin):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Basic trip info
    name = Column(String)
    status = Column(SQLEnum(TripStatus), default=TripStatus.PLANNING, index=True)

    # Trip parameters
    start_address = Column(String, nullable=False)
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)

    end_address = Column(String)
    end_latitude = Column(Float)
    end_longitude = Column(Float)

    # Trip constraints
    max_distance_km = Column(Integer)  # Maximum total trip distance
    duration_days = Column(Integer)  # Expected trip duration

    # Dates
    start_date = Column(Date)
    end_date = Column(Date)

    # Route and stops
    waypoints = Column(JSON)  # List of {location_id, order, arrival_date, departure_date}
    route_geometry = Column(JSON)  # GeoJSON of the route

    # Preferences for this specific trip
    trip_preferences = Column(JSON, default={})  # Trip-specific overrides

    # Feedback for learning
    user_ratings = Column(JSON, default={})  # {location_id: rating}
    user_feedback = Column(JSON, default={})  # {location_id: feedback_text}

    # Relationships
    user = relationship("User", back_populates="trips")

    def __repr__(self):
        return f"<Trip(id={self.id}, name='{self.name}', status={self.status})>"
