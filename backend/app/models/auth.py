"""
Authentication models - extends the base User model with auth-specific tables
"""
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserSession(Base):
    """User JWT session"""
    __tablename__ = "user_sessions"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)

    # Session tokens
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255))

    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_type = Column(String(50))

    # Timing
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())


class OAuthConnection(Base):
    """OAuth provider connection"""
    __tablename__ = "oauth_connections"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)

    # Provider info
    provider = Column(String(50), nullable=False)  # 'google', 'microsoft'
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255))

    # OAuth tokens (should be encrypted in production)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime(timezone=True))

    # Profile data from provider
    provider_data = Column(JSONB)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EmailVerificationToken(Base):
    """Email verification token"""
    __tablename__ = "email_verification_tokens"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)

    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    """Password reset token"""
    __tablename__ = "password_reset_tokens"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)

    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TripCreation(Base):
    """Track trip creation for analytics"""
    __tablename__ = "trip_creations"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger)  # Nullable for anonymous users

    # Trip details
    trip_type = Column(String(50))
    duration_days = Column(Integer)
    duration_hours = Column(Integer)
    num_waypoints = Column(Integer)
    total_distance_km = Column(DECIMAL(10, 2))
    start_country = Column(String(100))
    end_country = Column(String(100))

    # Session
    session_id = Column(String(255))
    ip_address = Column(String(45))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class APIUsage(Base):
    """Track API usage for analytics and rate limiting"""
    __tablename__ = "api_usage"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger)  # Nullable for anonymous users

    endpoint = Column(String(500), index=True)
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)

    # Session
    session_id = Column(String(255))
    ip_address = Column(String(45))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
