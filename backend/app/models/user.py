from sqlalchemy import Column, Integer, String, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Authentication (for future use)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)

    # Basic info
    username = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String)

    # User type
    is_camper = Column(Boolean, default=True)  # False for day-trippers
    is_active = Column(Boolean, default=True)

    # Vehicle info (for campers)
    vehicle_type = Column(String)  # "motorhome", "caravan", "van", "car"
    vehicle_length = Column(Float)  # in meters
    vehicle_height = Column(Float)  # in meters

    # Relationships
    trips = relationship("Trip", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    # Preference learning - interests
    interests = Column(ARRAY(String), default=[])  # ["nature", "culture", "sports", "food", "history"]
    preferred_amenities = Column(ARRAY(String), default=[])  # ["wifi", "electricity", "water"]

    # Budget preferences
    max_price_per_night = Column(Float)
    preferred_currency = Column(String, default="EUR")

    # Activity preferences
    activity_level = Column(String, default="moderate")  # "low", "moderate", "high"
    preferred_activities = Column(ARRAY(String), default=[])  # ["hiking", "cycling", "sightseeing"]

    # Location preferences
    preferred_environment = Column(ARRAY(String), default=[])  # ["beach", "mountains", "city", "countryside"]
    avoid_crowded = Column(Boolean, default=False)

    # Travel style
    planning_horizon_days = Column(Integer, default=7)  # How far ahead they plan
    typical_stay_duration = Column(Integer, default=2)  # Nights per location
    typical_daily_distance = Column(Integer, default=150)  # km per day

    # Learned preferences (machine learning)
    preference_vector = Column(JSON)  # Embedding vector for ML recommendations
    interaction_history = Column(JSON, default={})  # Track user interactions for learning

    # Relationship
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id={self.user_id})>"
