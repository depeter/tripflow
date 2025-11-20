"""
Pytest configuration and shared fixtures
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Import models to ensure they're registered
from app.models.base import Base
from app.models.location import Location, LocationType, LocationSource
from app.models.trip import Trip, TripStatus
from app.models.user import User
from app.models.event import Event


# ============================================================================
# UNIT TEST FIXTURES (Mocked)
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests"""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    return session


@pytest.fixture
def sample_location_data():
    """Sample location data for testing"""
    return {
        "id": 1,
        "name": "Beautiful Camping Spot",
        "description": "A scenic camping location near the mountains",
        "latitude": 51.0543,
        "longitude": 3.7174,
        "city": "Brussels",
        "country": "Belgium",
        "location_type": "CAMPING",
        "rating": 4.5,
        "price": 25.0,
        "amenities": ["wifi", "shower", "electricity"],
        "tags": ["nature", "mountains"],
        "active": True
    }


@pytest.fixture
def sample_trip_data():
    """Sample trip data for testing"""
    return {
        "id": 1,
        "user_id": 123,
        "start_address": "Brussels, Belgium",
        "start_latitude": 50.8503,
        "start_longitude": 4.3517,
        "end_address": "Amsterdam, Netherlands",
        "end_latitude": 52.3676,
        "end_longitude": 4.9041,
        "max_distance_km": 500,
        "duration_days": 3,
        "status": "PLANNING",
        "trip_preferences": {
            "interests": ["nature", "camping"],
            "budget": "medium"
        }
    }


# ============================================================================
# API TEST FIXTURES (FastAPI TestClient)
# ============================================================================

@pytest.fixture
def test_client():
    """FastAPI TestClient for API testing"""
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@pytest.fixture
def mock_location_service():
    """Mock LocationService for API tests"""
    from unittest.mock import Mock
    service = Mock()
    return service


@pytest.fixture
def mock_trip_service():
    """Mock TripPlanningService for API tests"""
    from unittest.mock import Mock
    service = Mock()
    return service


@pytest.fixture
def auth_headers():
    """Generate valid auth headers with JWT token"""
    from app.core.security import create_access_token

    # JWT sub field should be user_id as string
    token = create_access_token({"sub": "1"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_async_db():
    """Mock async database session for API tests"""
    from unittest.mock import AsyncMock, Mock
    session = AsyncMock()
    # Make session usable in async context managers
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


# ============================================================================
# INTEGRATION TEST FIXTURES (Real Database)
# ============================================================================

@pytest.fixture(scope="session")
def test_db_url():
    """Get test database URL from environment or use default"""
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://tripflow:tripflow@localhost:5432/tripflow_test"
    )


@pytest.fixture(scope="session")
def db_engine(test_db_url):
    """
    Create test database engine.

    For SQLite (in-memory):
    - Uses StaticPool to maintain single connection
    - Enables PostGIS-like functionality via SQLite extensions

    For PostgreSQL:
    - Uses real test database
    - Requires PostGIS extension
    """
    # Check if using SQLite for faster tests
    if test_db_url.startswith("sqlite"):
        engine = create_engine(
            test_db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

        # Enable spatialite extension for SQLite
        @event.listens_for(engine, "connect")
        def load_spatialite(dbapi_conn, connection_record):
            try:
                dbapi_conn.enable_load_extension(True)
                dbapi_conn.load_extension("/usr/lib/x86_64-linux-gnu/mod_spatialite.so")
            except Exception:
                # Spatialite not available, skip
                pass
    else:
        # PostgreSQL test database
        engine = create_engine(test_db_url, echo=False)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup: Drop all tables after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a new database session for a test.

    Uses transaction rollback to ensure test isolation:
    - Begin a transaction
    - Run test
    - Rollback transaction (no changes persist)
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    # Create session bound to connection
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    yield session

    # Rollback transaction and close
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user for integration tests"""
    from app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_location(db_session):
    """Create a test location for integration tests"""
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point

    location = Location(
        external_id="test_001",
        source=LocationSource.MANUAL,
        name="Test Camping Spot",
        description="A test camping location",
        location_type=LocationType.CAMPSITE,
        latitude=50.8503,
        longitude=4.3517,
        geom=from_shape(Point(4.3517, 50.8503), srid=4326),
        city="Brussels",
        country="Belgium",
        amenities=["wifi", "shower"],
        tags=["nature"],
        rating=4.5,
        price=25.0,
        active=True
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location
