# Advanced Filtering & Discovery Tab System

## Summary

Added advanced filtering system with tabs to switch between **Locations** (campsites, parking, etc.) and **Events** (festivals, concerts, etc.) on the discovery page.

## Features Added

### 1. Tab System
- **Locations Tab**: Shows campsites, parking spots, service areas, attractions, and custom locations
- **Events Tab**: Shows nearby events, festivals, concerts, and activities
- Dynamic count badges showing number of results in each tab
- Smooth tab switching with automatic data loading

### 2. Event Discovery
- Fetches events from backend `/discover` endpoint
- Filters by:
  - Category (festival, concert, sports, market, exhibition, theater, cultural, food, outdoor)
  - Date range (upcoming, this week, this month)
  - Free only toggle
  - Distance radius
- Displays events with EventCard component

### 3. Enhanced Map Markers
- Events shown on map with 🎪 icon (event_venue type)
- Popups show event details:
  - Event name and category
  - Date and time
  - Price (FREE/paid/varies)
  - Distance from start point

### 4. Unified Selection System
- Both locations and events can be added to trip
- Selected items shown in the same "Selected Locations" panel
- Events treated as waypoints on the route

## Changes Made

### Backend Services (tripsService.js)

**Added Functions:**
```javascript
// Discover events near a location
export const discoverEvents = async (params) => {
  // Calls POST /discover endpoint
  // Parameters: latitude, longitude, radius_km, categories, start_date, end_date, free_only, limit
}

// Get available event categories
export const getEventCategories = async () => {
  // Calls GET /discover/categories
}

// Get discovery statistics
export const getDiscoveryStats = async () => {
  // Calls GET /discover/stats
}
```

### Frontend Components

**Step4_Recommendations.jsx:**
- Added `activeTab` state ('locations' | 'events')
- Added `events` state for event data
- Added `eventFilters` state for event filtering
- Added `loadEvents()` function to fetch events
- Updated `buildMapMarkers()` to include events
- Added tab UI with counts
- Added event rendering with EventCard

**EventCard.jsx & EventCard.css:**
- Already existed (created previously)
- Displays event information in card format
- Shows date, venue, price, category badge
- Add to trip functionality

**Step4_Recommendations.css:**
- Added `.discovery-tabs` styles for tab system
- Added `.discovery-tab` with active state
- Added `.tab-count` badge styles
- Added `.advanced-filters` styles (for future use)

### Backend API (Already Exists)

**Endpoint:** `POST /api/v1/discover`
**Request:**
```json
{
  "latitude": 50.8503,
  "longitude": 4.3517,
  "radius_km": 25,
  "categories": ["festival", "concert"],
  "start_date": "2025-11-20T00:00:00Z",
  "end_date": "2025-12-20T00:00:00Z",
  "free_only": false,
  "limit": 50
}
```

**Response:**
```json
{
  "events": [...],
  "total_count": 42,
  "search_center": {"latitude": 50.8503, "longitude": 4.3517},
  "radius_km": 25
}
```

## Usage

### 1. Switch Between Tabs

Users can click on the **Locations** or **Events** tabs to switch between:
- 📍 **Locations** - Campsites, parking, service areas, attractions
- 🎉 **Events** - Festivals, concerts, markets, exhibitions

### 2. View Events

When on the Events tab:
- Events are displayed as cards with date, venue, price
- Events are shown on the map with 🎪 icon
- Click "Add to trip" to include event as a waypoint
- Popups show event details

### 3. Select Events

- Click "Add to trip" on any event card
- Event appears in "Selected Locations" panel (right side of map)
- Events can be removed like any other location
- Events are included in the route planning

## Event Categories

Available event categories (from backend):
- **festival** - Music festivals, cultural festivals
- **concert** - Live music performances
- **sports** - Sports events and matches
- **market** - Markets, fairs, bazaars
- **exhibition** - Art exhibitions, expos
- **theater** - Theater performances, plays
- **cultural** - Cultural events, heritage
- **food** - Food festivals, tastings
- **outdoor** - Outdoor activities, nature events
- **other** - Other event types

## Advanced Filters (Future Enhancement)

CSS styles are ready for advanced filtering UI with:
- Location type checkboxes (campsite, parking, service_area, etc.)
- Amenities checkboxes (wifi, electricity, water, toilet, shower)
- Event category checkboxes
- Price range sliders
- Date range pickers
- Free only toggles

To enable, add:
```jsx
<div className="advanced-filters">
  <button className="filters-toggle" onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}>
    <div className="filters-toggle-left">
      <span className="filters-toggle-icon">▶</span>
      Advanced Filters
    </div>
  </button>
  {showAdvancedFilters && (
    <div className="filters-content">
      {/* Filter checkboxes here */}
    </div>
  )}
</div>
```

## Data Requirements

### Events Data

Events must be imported into the database. Check if data exists:

```bash
cd /home/peter/work/tripflow/backend
source venv/bin/activate

python << 'EOF'
from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM tripflow.events WHERE active = true"))
    count = result.scalar()
    print(f"Active events in database: {count}")

    # Events by category
    result = conn.execute(text("SELECT category, COUNT(*) FROM tripflow.events WHERE active = true GROUP BY category"))
    print("\nEvents by category:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")
EOF
```

### Import Events from Scraparr

If UiT in Vlaanderen events need to be imported:

```bash
cd /home/peter/work/tripflow
source venv/bin/activate

python << 'EOF'
from app.sync.uit_importer import UiTImporter
from app.db.database import SessionLocal

db = SessionLocal()
try:
    importer = UiTImporter(db)
    result = importer.sync()
    print(f"Imported {result['events_synced']} events")
    print(f"Errors: {result.get('errors', 0)}")
finally:
    db.close()
EOF
```

## Testing

### 1. Start Backend

```bash
cd /home/peter/work/tripflow/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Start Frontend

```bash
cd /home/peter/work/tripflow/frontend
npm start
```

### 3. Test Discovery

1. Go to http://localhost:3000
2. Create a new trip
3. Choose a location in Belgium (where event data exists)
4. Go to Step 4 (Find Locations)
5. You should see:
   - Two tabs: "📍 Locations" and "🎉 Events"
   - Tab counts showing number of results
   - Click Events tab to see nearby events
   - Click any event to add to trip
   - Events appear on map with 🎪 icon

### 4. Verify Event Display

- **Event Cards** should show:
  - Event name and category badge
  - Date and time
  - Venue name and city
  - Price (FREE/paid)
  - Distance from start point
  - Tags and description
  - "Add to trip" button

- **Map Markers** should show:
  - Events with 🎪 icon (purple/indigo color)
  - Popup with event details
  - Click to select/deselect

## API Testing

Test the discover endpoint directly:

```bash
# Get event categories
curl http://localhost:8001/api/v1/discover/categories

# Get discovery stats
curl http://localhost:8001/api/v1/discover/stats

# Search for events near Brussels
curl -X POST http://localhost:8001/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 50.8503,
    "longitude": 4.3517,
    "radius_km": 25,
    "limit": 10
  }'

# Search for free festivals
curl -X POST http://localhost:8001/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 50.8503,
    "longitude": 4.3517,
    "radius_km": 50,
    "categories": ["festival"],
    "free_only": true,
    "limit": 20
  }'
```

## Files Modified

### Frontend:
- `/home/peter/work/tripflow/frontend/src/services/tripsService.js` - Added event API functions
- `/home/peter/work/tripflow/frontend/src/pages/Step4_Recommendations.jsx` - Added tabs, event loading, event display
- `/home/peter/work/tripflow/frontend/src/pages/Step4_Recommendations.css` - Added tab and filter styles
- `/home/peter/work/tripflow/frontend/src/components/EventCard.jsx` - Event card component (already existed)
- `/home/peter/work/tripflow/frontend/src/components/EventCard.css` - Event card styles (already existed)

### Backend:
- No backend changes needed (discover API already exists)

## Future Enhancements

1. **Advanced Filters UI**
   - Collapsible filter panel with checkboxes
   - Filter by location types (campsite, parking, service area)
   - Filter by amenities (wifi, electricity, water, toilet, shower)
   - Filter by event categories with icons
   - Date range picker for events
   - Price range slider

2. **Filter Persistence**
   - Save filter preferences to localStorage
   - Remember last selected tab
   - Apply filters across sessions

3. **Sort Options**
   - Sort events by date (soonest first)
   - Sort by distance
   - Sort by price (free first)
   - Sort by relevance

4. **Map Enhancements**
   - Click event card to center map on event
   - Hover event card to highlight marker
   - Cluster markers when zoomed out
   - Show event date range on map

5. **Event Details Modal**
   - Full event details popup
   - Multiple images gallery
   - Book tickets button
   - Add to calendar button
   - Share event button

## Notes

- Events and locations share the same selection system
- Both are treated as waypoints in the route
- Tab switching triggers data reload
- Map automatically updates when tab changes
- Event markers use `event_venue` location type for icon
- Events show date/time in popup instead of rating
- Free events highlighted with green "FREE" badge

## Troubleshooting

### No Events Showing

1. Check if events exist in database:
```bash
cd /home/peter/work/tripflow/backend && source venv/bin/activate
python -c "from app.db.database import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM tripflow.events')).scalar())"
```

2. Check if events are within search radius:
   - Try increasing `max_distance_km` in trip settings
   - Choose location in Belgium where data exists

3. Check browser console for API errors

### Events Not Appearing on Map

1. Verify events have valid coordinates
2. Check `buildMapMarkers()` function includes events
3. Verify `activeTab === 'events'` condition
4. Check map bounds calculation

### Tab Not Switching

1. Check `activeTab` state updates
2. Verify tab click handlers
3. Check CSS for `.active` class
4. Look for JavaScript errors in console

## Related Documentation

- **Park4Night Implementation:** `/home/peter/work/tripflow/PARK4NIGHT_MAP_IMPLEMENTATION.md`
- **Backend API:** Check FastAPI docs at http://localhost:8001/docs
- **Event Model:** `/home/peter/work/tripflow/backend/app/models/event.py`
- **Discover API:** `/home/peter/work/tripflow/backend/app/api/discover.py`
