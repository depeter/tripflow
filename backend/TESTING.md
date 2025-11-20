# Testing Guide for TripFlow Backend

## Test Architecture

### Test Types

1. **Unit Tests** (`tests/unit/`) - Test business logic in isolation with mocked dependencies
2. **Integration Tests** (`tests/integration/`) - Test database interactions with test DB
3. **E2E Tests** (`test_api.py`) - Test full API with running server (legacy)

### Why Unit Tests?

The original `test_api.py` is an **end-to-end test** that requires:
- Running FastAPI server (port 8001)
- Running PostgreSQL database
- Running Qdrant vector DB
- Running Redis

This is **not suitable for unit testing** because it tests the entire stack, not isolated business logic.

## Architecture

```
API Layer (FastAPI routes in app/api/)
    ↓ (calls)
Service Layer (Business Logic in app/services/) ← Unit tests target this layer
    ↓ (uses)
Data Layer (SQLAlchemy ORM + External APIs)
```

## Service Layer Components

### Services with Business Logic:

1. **LocationService** (`app/services/location_service.py`)
   - Dependencies: Database, Geopy/Nominatim
   - Methods: get_location_by_id, search_locations, find_nearby_locations, geocode_address, reverse_geocode

2. **TripPlanningService** (`app/services/trip_service.py`)
   - Dependencies: Database, LocationService, RecommendationService
   - Methods: create_trip, suggest_waypoints, optimize_route

3. **RecommendationService** (`app/services/recommendation_service.py`)
   - Dependencies: Database, Qdrant, SentenceTransformer
   - Methods: recommend_locations, learn_from_trip, index_location

4. **StripeService** (`app/services/stripe_service.py`)
   - Dependencies: Database, Stripe API
   - Methods: create_customer, create_checkout_session, handle_webhook

5. **OAuthService** (`app/services/oauth_service.py`)
   - Dependencies: Database, Authlib, Google/Microsoft APIs
   - Methods: handle_google_callback, handle_microsoft_callback

## Running Tests

### Run All Unit Tests
```bash
cd /home/peter/work/tripflow/backend
/home/peter/work/tripflow/backend/venv/bin/python3 -m pytest tests/unit/ -v
```

### Run Specific Test File
```bash
/home/peter/work/tripflow/backend/venv/bin/python3 -m pytest tests/unit/test_location_service.py -v
```

### Run Tests with Coverage
```bash
/home/peter/work/tripflow/backend/venv/bin/python3 -m pytest tests/unit/ --cov=app/services --cov-report=html
```

### Run Only Unit Tests (skip integration)
```bash
/home/peter/work/tripflow/backend/venv/bin/python3 -m pytest -m unit
```

### Run E2E Tests (requires running server)
```bash
# Start backend first
cd /home/peter/work/tripflow/backend
./venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# In another terminal
./venv/bin/python3 test_api.py
```

## Test Results

### LocationService Unit Tests (10/10 passing)

```
✅ test_get_location_by_id - Retrieve location by ID
✅ test_get_location_by_id_not_found - Handle non-existent location
✅ test_search_locations_with_query - Text search in locations
✅ test_search_locations_with_filters - Multi-filter search (type, rating, price, amenities, tags)
✅ test_find_nearby_locations_basic - PostGIS geospatial query
✅ test_find_nearby_locations_with_type_filter - Geospatial with type filter
✅ test_geocode_address_success - Successful address → coordinates
✅ test_geocode_address_not_found - Invalid address handling
✅ test_reverse_geocode_success - Coordinates → address
✅ test_reverse_geocode_failure - Invalid coordinates handling
```

**All tests passed in 0.23 seconds** ✨

## Test Structure

### Fixtures (`tests/conftest.py`)

- `mock_db_session` - Mocked SQLAlchemy session for database operations
- `sample_location_data` - Sample location dictionary for testing
- `sample_trip_data` - Sample trip dictionary for testing

### Test Pattern

```python
@pytest.mark.unit
class TestLocationService:
    """Test LocationService business logic"""

    def test_get_location_by_id(self, mock_db_session, sample_location_data):
        """Test retrieving a location by ID"""
        # Arrange - Set up mocks and test data
        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Beautiful Camping Spot"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_location

        service = LocationService(mock_db_session)

        # Act - Call the method under test
        result = service.get_location_by_id(1)

        # Assert - Verify behavior
        assert result is not None
        assert result.id == 1
        assert result.name == "Beautiful Camping Spot"
        mock_db_session.query.assert_called_once()
```

## Mocking Strategy

### Database Mocking
```python
mock_db_session = Mock(spec=Session)
mock_db_session.query = Mock()
mock_db_session.add = Mock()
mock_db_session.commit = Mock()
```

### External API Mocking (Geopy/Nominatim)
```python
@patch('geopy.geocoders.Nominatim')
def test_geocode_address_success(self, mock_nominatim_class, mock_db_session):
    mock_geocoder = Mock()
    mock_location = Mock()
    mock_location.latitude = 50.8503
    mock_location.longitude = 4.3517
    mock_geocoder.geocode.return_value = mock_location
    mock_nominatim_class.return_value = mock_geocoder

    # Test code...
```

## Adding New Tests

### 1. Create Test File
```bash
# For a new service
touch tests/unit/test_trip_service.py
```

### 2. Write Test Class
```python
import pytest
from unittest.mock import Mock, patch
from app.services.trip_service import TripPlanningService

@pytest.mark.unit
class TestTripPlanningService:
    def test_create_trip(self, mock_db_session):
        # Test implementation
        pass
```

### 3. Run Tests
```bash
pytest tests/unit/test_trip_service.py -v
```

## Key Differences: Unit vs E2E Tests

| Aspect | Unit Tests | E2E Tests (test_api.py) |
|--------|-----------|------------------------|
| **Scope** | Single service/function | Entire API stack |
| **Dependencies** | Mocked | Real (DB, Redis, Qdrant) |
| **Speed** | Fast (< 1 second) | Slow (10+ seconds) |
| **Setup** | None required | Start server + services |
| **Purpose** | Test business logic | Test integration |
| **Isolation** | Complete | None |

## Best Practices

1. **Mock external dependencies** - Database, APIs, file system
2. **Test business logic, not implementation** - Focus on what, not how
3. **Use descriptive test names** - `test_geocode_address_with_invalid_input`
4. **Follow AAA pattern** - Arrange, Act, Assert
5. **One assertion focus per test** - Test one thing at a time
6. **Use fixtures for common setup** - Reduce code duplication

## Common Issues

### Issue: `AttributeError: CAMPING`
**Problem**: Wrong enum value
**Fix**: Use correct enum values from `app/models/location.py`
```python
# Wrong
LocationType.CAMPING

# Correct
LocationType.CAMPSITE
```

### Issue: `'Mock' object is not iterable`
**Problem**: Mock doesn't return iterable when code expects list/tuple
**Fix**: Return actual list/tuple from mock
```python
# Wrong
mock_query.all.return_value = Mock()

# Correct
mock_query.all.return_value = [mock_object1, mock_object2]
```

### Issue: `AttributeError: does not have attribute 'Nominatim'`
**Problem**: Wrong patch path
**Fix**: Patch where it's imported from, not where it's used
```python
# Wrong
@patch('app.services.location_service.Nominatim')

# Correct
@patch('geopy.geocoders.Nominatim')
```

## Next Steps

### Services Needing Unit Tests:
- [ ] TripPlanningService (trip_service.py)
- [ ] RecommendationService (recommendation_service.py)
- [ ] StripeService (stripe_service.py)
- [ ] OAuthService (oauth_service.py)
- [ ] MigrationRunner (migration_runner.py)

### Integration Tests Needed:
- [ ] Database schema validation
- [ ] PostGIS geospatial queries
- [ ] Qdrant vector search
- [ ] End-to-end trip planning flow

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

**Last Updated**: 2025-11-19
**Test Coverage**: LocationService - 10/10 tests passing
