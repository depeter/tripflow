from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Usage in FastAPI endpoints:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)


def get_source_db_connection(db_name: str):
    """
    Get connection to source database for syncing.

    Args:
        db_name: One of 'park4night', 'campercontact', 'local_sites'

    Returns:
        SQLAlchemy engine for the source database
    """
    db_urls = {
        "park4night": settings.SOURCE_DB_PARK4NIGHT,
        "campercontact": settings.SOURCE_DB_CAMPERCONTACT,
        "local_sites": settings.SOURCE_DB_LOCAL_SITES,
    }

    db_url = db_urls.get(db_name)
    if not db_url:
        raise ValueError(f"Source database URL not configured for: {db_name}")

    return create_engine(db_url, pool_pre_ping=True)
