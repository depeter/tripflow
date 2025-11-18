from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, MetaData
from datetime import datetime

# Configure metadata to use tripflow schema by default
metadata = MetaData(schema="tripflow")
Base = declarative_base(metadata=metadata)


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
