from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    """
    User model matching tripflow.users schema
    """
    __tablename__ = "users"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=True)  # NULL for OAuth-only users

    # Profile
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # OAuth identifiers
    google_id = Column(String(255), unique=True, nullable=True)
    microsoft_id = Column(String(255), unique=True, nullable=True)

    # Subscription & billing
    subscription_tier = Column(String(50), default='free')
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)

    # Permissions
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class UserFavorite(Base):
    """
    User favorites model for discovery mode
    Maps users to their favorited events
    """
    __tablename__ = "user_favorites"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tripflow.users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("tripflow.events.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserFavorite(id={self.id}, user_id={self.user_id}, event_id={self.event_id})>"


# Note: UserPreference model removed - not in tripflow schema
# User preferences will be stored differently or in future migrations
