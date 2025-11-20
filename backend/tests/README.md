# TripFlow Backend Tests

## Quick Start

```bash
# Run all tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=app/services --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_location_service.py -v
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (mock all dependencies)
│   ├── test_location_service.py    # LocationService tests (10 tests)
│   └── test_trip_service.py        # TripPlanningService tests (8 tests)
└── integration/             # Integration tests (future - use test DB)
```

## Current Test Coverage

| Service | Tests | Coverage | Status |
|---------|-------|----------|--------|
| LocationService | 10 | 79% | ✅ Complete |
| TripPlanningService | 8 | 53% | ✅ Basic coverage |
| RecommendationService | 0 | 14% | ⏳ TODO |
| StripeService | 0 | 0% | ⏳ TODO |
| OAuthService | 0 | 0% | ⏳ TODO |

**Total: 18 tests passing in ~17 seconds**

## Fixtures Available

From `conftest.py`:

- `mock_db_session` - Mocked SQLAlchemy session
- `sample_location_data` - Sample location dictionary
- `sample_trip_data` - Sample trip dictionary

## Test Examples

### Basic Unit Test

```python
@pytest.mark.unit
def test_get_location_by_id(mock_db_session):
    # Arrange
    mock_location = Mock()
    mock_location.id = 1
    mock_location.name = "Test Location"
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_location

    service = LocationService(mock_db_session)

    # Act
    result = service.get_location_by_id(1)

    # Assert
    assert result.id == 1
    assert result.name == "Test Location"
```

### Mocking External APIs

```python
@patch('geopy.geocoders.Nominatim')
def test_geocode_address(mock_nominatim_class, mock_db_session):
    # Arrange
    mock_geocoder = Mock()
    mock_location = Mock()
    mock_location.latitude = 50.8503
    mock_location.longitude = 4.3517
    mock_geocoder.geocode.return_value = mock_location
    mock_nominatim_class.return_value = mock_geocoder

    service = LocationService(mock_db_session)

    # Act
    result = service.geocode_address("Brussels, Belgium")

    # Assert
    assert result["latitude"] == 50.8503
    assert result["longitude"] == 4.3517
```

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/unit/ -v --cov=app/services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Common Commands

```bash
# Run only unit tests
pytest -m unit

# Run tests in parallel (faster)
pytest tests/unit/ -n auto

# Run with verbose output
pytest tests/unit/ -vv

# Stop on first failure
pytest tests/unit/ -x

# Run specific test class
pytest tests/unit/test_location_service.py::TestLocationService

# Run specific test method
pytest tests/unit/test_location_service.py::TestLocationService::test_get_location_by_id

# Show print statements
pytest tests/unit/ -s

# Generate HTML coverage report
pytest tests/unit/ --cov=app/services --cov-report=html
# Then open: htmlcov/index.html
```

## Writing New Tests

### 1. Create test file

```bash
touch tests/unit/test_my_service.py
```

### 2. Write test class

```python
import pytest
from unittest.mock import Mock
from app.services.my_service import MyService

@pytest.mark.unit
class TestMyService:
    def test_my_method(self, mock_db_session):
        # Arrange
        service = MyService(mock_db_session)

        # Act
        result = service.my_method()

        # Assert
        assert result is not None
```

### 3. Run your tests

```bash
pytest tests/unit/test_my_service.py -v
```

## Debugging Tests

### Show full error output
```bash
pytest tests/unit/ --tb=long
```

### Drop into debugger on failure
```bash
pytest tests/unit/ --pdb
```

### Show local variables on failure
```bash
pytest tests/unit/ --showlocals
```

## Best Practices

1. **Test behavior, not implementation** - Focus on what the code does, not how
2. **One assertion focus per test** - Test one thing at a time
3. **Use descriptive test names** - `test_geocode_address_with_invalid_input`
4. **Follow AAA pattern** - Arrange, Act, Assert
5. **Mock external dependencies** - Database, APIs, file system
6. **Keep tests fast** - All unit tests should run in seconds
7. **Make tests deterministic** - Same input = same output every time

## Common Pitfalls

### ❌ Wrong enum value
```python
LocationType.CAMPING  # Wrong! Check the actual enum
```

### ✅ Correct enum value
```python
LocationType.CAMPSITE  # Correct
```

### ❌ Mock not iterable
```python
mock_query.all.return_value = Mock()  # Wrong!
```

### ✅ Return actual list
```python
mock_query.all.return_value = [mock_object1, mock_object2]  # Correct
```

### ❌ Wrong patch path
```python
@patch('app.services.location_service.Nominatim')  # Wrong!
```

### ✅ Patch where imported
```python
@patch('geopy.geocoders.Nominatim')  # Correct
```

## Documentation

- [TESTING.md](../TESTING.md) - Complete testing guide
- [TEST_RESULTS.md](../TEST_RESULTS.md) - Current test results and coverage
- [pytest docs](https://docs.pytest.org/) - Official pytest documentation

## Questions?

Check the existing tests in `tests/unit/` for examples, or refer to the comprehensive documentation in `TESTING.md`.
