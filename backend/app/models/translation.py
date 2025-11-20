"""
Translation models for multilingual content support.

Provides translation tables for locations and events to support
multiple languages (en, nl, fr, de, es, it).
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base


class LocationTranslation(Base):
    """
    Multilingual translations for locations.

    Supports multiple languages for location names and descriptions.
    Languages: en (English), nl (Dutch), fr (French), de (German),
               es (Spanish), it (Italian)
    """
    __tablename__ = "location_translations"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("tripflow.locations.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(5), nullable=False, index=True)  # ISO 639-1: en, nl, fr, de, es, it
    name = Column(String(500))  # Translated name (optional, usually same as original)
    description = Column(Text)  # Translated description
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship back to location
    # location = relationship("Location", back_populates="translations")

    def __repr__(self):
        return f"<LocationTranslation(location_id={self.location_id}, lang='{self.language_code}')>"


class EventTranslation(Base):
    """
    Multilingual translations for events.

    Supports multiple languages for event names and descriptions.
    Languages: en (English), nl (Dutch), fr (French), de (German),
               es (Spanish), it (Italian)
    """
    __tablename__ = "event_translations"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("tripflow.events.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(5), nullable=False, index=True)  # ISO 639-1: en, nl, fr, de, es, it
    name = Column(String(500))  # Translated event name
    description = Column(Text)  # Translated description
    short_description = Column(Text)  # Translated short summary
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship back to event
    # event = relationship("Event", back_populates="translations")

    def __repr__(self):
        return f"<EventTranslation(event_id={self.event_id}, lang='{self.language_code}')>"
