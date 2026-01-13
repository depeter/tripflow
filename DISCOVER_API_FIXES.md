# Discover API Fixes - December 29, 2025

## Problem Summary

The `/api/v1/discover` endpoint was crashing with HTTP 500 errors due to enum mismatches between the Python models and database values.

### Original Error
```
POST https://tripflow.pm-consulting.be/api/v1/discover
[HTTP/2 500  186ms]

LookupError: 'wikidata' is not among the defined enum values.
Enum name: location_source. Possible values: park4night, camperconta.., uitinvlaand.., ..., other

LookupError: 'other' is not among the defined enum values.
Enum name: eventcategory. Possible values: FESTIVAL, CONCERT, SPORTS, ..., OTHER
```

## Root Causes

1. **Location Source Enum Mismatch**:
   - Database had locations from sources: `wikidata`, `visitwallonia`, `dagjeweg`
   - Python `LocationSource` enum only included: `park4night`, `campercontact`, `uitinvlaanderen`, `openstreetmap`, `google_places`, `manual`, `other`
   - Missing values: `wikidata`, `visitwallonia`, `dagjeweg`

2. **Event Category Enum Issue**:
   - Database had 100+ different category values (e.g., 'Miscellaneous', 'Alternative', 'other', 'Other', 'OTHER')
   - Python `EventCategory` enum only had 10 uppercase values
   - `EventCategory` class was being exported and imported, causing SQLAlchemy to create a `public.eventcategory` enum type during `init_db()`
   - Event model used `SQLEnum(EventCategory)` instead of plain `String` column type

## Fixes Applied

### 1. Location Source Enum Fix (`app/models/location.py`)

**Added missing enum values:**
```python
class LocationSource(str, Enum):
    PARK4NIGHT = "park4night"
    CAMPERCONTACT = "campercontact"
    UITINVLAANDEREN = "uitinvlaanderen"
    OPENSTREETMAP = "openstreetmap"
    GOOGLE_PLACES = "google_places"
    MANUAL = "manual"
    OTHER = "other"
    VISITWALLONIA = "visitwallonia"  # Added
    DAGJEWEG = "dagjeweg"            # Added
    WIKIDATA = "wikidata"            # Added
```

**Updated PG_ENUM column definition:**
```python
source = Column(
    PG_ENUM('park4night', 'campercontact', 'uitinvlaanderen', 'openstreetmap',
            'google_places', 'manual', 'other', 'visitwallonia', 'dagjeweg', 'wikidata',
            name='location_source', schema='tripflow', create_type=False),
    nullable=False, index=True
)
```

### 2. Event Category Enum Fix

**Changed Event model to use String instead of Enum (`app/models/event.py`):**
```python
# Before:
category = Column(SQLEnum(EventCategory), nullable=False, index=True)

# After:
category = Column(String, nullable=False, index=True)
```

**Removed EventCategory from model exports (`app/models/__init__.py`):**
```python
# Removed:
from .event import Event, EventCategory
# Added:
from .event import Event
```

**Updated discover endpoint to query categories from database (`app/api/discover.py`):**
```python
# Removed EventCategory import:
from app.models.event import Event  # Not Event, EventCategory

# Changed get_categories endpoint to query DB:
@router.get("/categories", response_model=List[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get list of available event categories from database"""
    result = await db.execute(
        select(Event.category).distinct().where(Event.category.isnot(None)).order_by(Event.category)
    )
    categories = [row[0] for row in result.all()]
    return categories
```

**Disabled automatic database initialization (`app/main.py`):**
```python
# Disabled init_db() to prevent enum type recreation:
# try:
#     init_db()
#     logger.info("Database initialized")
# except Exception as e:
#     logger.error(f"Database initialization failed: {e}")
logger.info("Database initialization skipped (production mode)")
```

**Dropped eventcategory enum type from database:**
```sql
DROP TYPE IF EXISTS public.eventcategory CASCADE;
```

### 3. Integration Tests

Created comprehensive integration tests (`tests/integration/test_discover_api.py`):
- Basic search
- Location filters
- Event filters
- Corridor (route) search
- Text search
- Date range filtering
- Wikidata source handling
- All location sources validation

## Results

### Before Fixes
- HTTP 500 errors on any discover request with events or certain locations
- Unable to handle locations from wikidata, visitwallonia, or dagjeweg sources
- Unable to query events due to enum mismatch

### After Fixes
- ✅ All 8 integration tests passing
- ✅ Successfully handles all location sources (wikidata, visitwallonia, dagjeweg)
- ✅ Successfully handles all event categories (100+ different values)
- ✅ Discover endpoint returns events and locations without errors
- ✅ No enum-related crashes

## Testing

Run integration tests:
```bash
cd /home/peter/work/tripflow/backend
./venv/bin/python tests/integration/test_discover_api.py
```

Expected output:
```
Results: 8 passed, 0 failed out of 8 tests
```

Test manually:
```bash
# Test locations with wikidata source
curl -X POST https://tripflow.pm-consulting.be/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"latitude": 51.0543, "longitude": 3.7174, "radius_km": 100, "item_types": ["locations"], "limit": 100}' \
  -k

# Test events with various categories
curl -X POST https://tripflow.pm-consulting.be/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"latitude": 51.0543, "longitude": 3.7174, "radius_km": 25, "item_types": ["events"], "limit": 10}' \
  -k
```

## Files Modified

1. `/home/peter/work/tripflow/backend/app/models/location.py` - Added missing location sources to enum
2. `/home/peter/work/tripflow/backend/app/models/event.py` - Changed category from SQLEnum to String
3. `/home/peter/work/tripflow/backend/app/models/__init__.py` - Removed EventCategory export
4. `/home/peter/work/tripflow/backend/app/api/discover.py` - Changed get_categories to query database
5. `/home/peter/work/tripflow/backend/app/main.py` - Disabled init_db() in production
6. `/home/peter/work/tripflow/backend/tests/integration/test_discover_api.py` - Created integration tests

## Deployment Notes

- Backend running on port 8001: http://192.168.1.149:8001
- Frontend URL: https://tripflow.pm-consulting.be
- Database: PostgreSQL on localhost:5433
- Schema already exists, no migrations needed
- `init_db()` disabled to prevent enum type recreation

## Important Lessons

1. **Enum Types**: SQLAlchemy creates PostgreSQL enum types when using `SQLEnum()` or `PG_ENUM()` columns
2. **Enum Imports**: Even importing an Enum class can cause SQLAlchemy to create database types during `Base.metadata.create_all()`
3. **String Columns**: Use plain `String` columns for database fields with many dynamic values
4. **init_db()**: Calling `Base.metadata.create_all()` can recreate enum types; disable in production if schema exists
5. **Integration Tests**: Critical for catching enum mismatches and production issues

## Next Steps

- Consider creating a migration script to properly manage enum types
- Add monitoring for HTTP 500 errors in production
- Consider using Alembic for database schema migrations instead of `init_db()`
