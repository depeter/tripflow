from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, AsyncGenerator
from app.core.config import settings

# Create async SQLAlchemy engine
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create async SessionLocal class
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create synchronous engine for compatibility
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create synchronous SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session.
    Usage in FastAPI endpoints:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db_sync() -> Generator[Session, None, None]:
    """
    Dependency function to get synchronous database session.
    Usage in FastAPI endpoints:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_sync)):
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
        db_name: One of 'park4night', 'campercontact', 'local_sites',
                 'uitinvlaanderen', 'eventbrite', 'ticketmaster'

    Returns:
        SQLAlchemy engine for the source database
    """
    db_urls = {
        "park4night": settings.SOURCE_DB_PARK4NIGHT,
        "campercontact": settings.SOURCE_DB_CAMPERCONTACT,
        "local_sites": settings.SOURCE_DB_LOCAL_SITES,
        "uitinvlaanderen": settings.SOURCE_DB_UITINVLAANDEREN,
        "eventbrite": settings.SOURCE_DB_EVENTBRITE,
        "ticketmaster": settings.SOURCE_DB_TICKETMASTER,
    }

    db_url = db_urls.get(db_name)
    if not db_url:
        raise ValueError(f"Source database URL not configured for: {db_name}")

    return create_engine(db_url, pool_pre_ping=True)
