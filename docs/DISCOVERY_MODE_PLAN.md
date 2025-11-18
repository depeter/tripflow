# TripFlow Discovery Mode - Implementation Plan

**Date:** November 16, 2025
**Status:** Planning → Implementation
**Priority:** High - Core UX Redesign

---

## Executive Summary

Transform TripFlow from a **trip planning tool** into a **spontaneous discovery app** with optional trip planning.

### The Shift
- **Before:** Plan trip → discover locations along route
- **After:** Discover what's nearby → optionally plan trips

### User Journey (New)
1. Open app → "What's happening around you?"
2. Grant location → See events/POIs on map + bottom sheet
3. Browse/filter events by distance, date, category
4. Tap event → See details, save to favorites
5. **Optional:** Plan trip from saved favorites

---

## Available Data

### Scraparr Database (scraparr-postgres:5434)

**scraper_2.events** - 12,292 events (UiT in Vlaanderen)
```
- event_id (unique)
- name, description
- start_date, end_date (VARCHAR - needs parsing!)
- location_name, street_address, city, postal_code, country
- latitude, longitude
- organizer, event_type, themes (comma-separated)
- url, image_url
- scraped_at, updated_at
```

**scraper_3.events** - 235 events (additional sources)
```
- event_id, name, description, url
- start_date (VARCHAR)
- location, venue_name, city, country, country_code
- status, image_url, is_online
- scraped_at, updated_at
```

**Note:** No static POI data (museums, restaurants) - only events. Could scrape OpenStreetMap in future.

---

## Implementation Phases

### Phase 1: MVP - Discovery Backend & Frontend (Week 1-2)

#### 1.1 Database Migration & Schema Enhancement

**Tasks:**
- [ ] Enhance `tripflow.events` table schema
- [ ] Create `tripflow.user_favorites` table
- [ ] Write migration script `migrate_scraparr_events.py`
- [ ] Add geospatial indexes
- [ ] Run migration (12,527 events)

**SQL Schema Changes:**
```sql
-- Enhance events table
ALTER TABLE tripflow.events
  ADD COLUMN IF NOT EXISTS event_type VARCHAR(100),
  ADD COLUMN IF NOT EXISTS themes TEXT[], -- ARRAY instead of VARCHAR
  ADD COLUMN IF NOT EXISTS image_url VARCHAR(500),
  ADD COLUMN IF NOT EXISTS organizer VARCHAR(300),
  ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'uitinvlaanderen',
  ADD COLUMN IF NOT EXISTS external_id VARCHAR(100) UNIQUE,
  ADD COLUMN IF NOT EXISTS external_url VARCHAR(500);

-- Convert location to PostGIS geometry (if not already)
ALTER TABLE tripflow.events
  ADD COLUMN IF NOT EXISTS geom GEOMETRY(Point, 4326);

UPDATE tripflow.events
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;

-- Geospatial index for fast nearby queries
CREATE INDEX IF NOT EXISTS idx_events_geom ON tripflow.events USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON tripflow.events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_event_category ON tripflow.events(event_category);

-- User favorites
CREATE TABLE IF NOT EXISTS tripflow.user_favorites (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES tripflow.users(id) ON DELETE CASCADE,
  event_id INTEGER NOT NULL REFERENCES tripflow.events(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, event_id)
);

CREATE INDEX idx_user_favorites_user ON tripflow.user_favorites(user_id);
CREATE INDEX idx_user_favorites_event ON tripflow.user_favorites(event_id);
```

**Migration Script:** `/home/peter/work/tripflow/backend/scripts/migrate_scraparr_events.py`

```python
"""
Migrate event data from Scraparr database to Tripflow.

Source: scraparr-postgres:5434 (scraper_2.events, scraper_3.events)
Target: tripflow-postgres:5433 (tripflow.events)
"""

import psycopg2
from datetime import datetime
from dateutil import parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_DB = "postgresql://scraparr:scraparr@localhost:5434/scraparr"
TARGET_DB = "postgresql://tripflow:tripflow@localhost:5433/tripflow"

def parse_date(date_str):
    """Parse various date formats to DATE."""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return parser.parse(date_str).date()
    except:
        logger.warning(f"Failed to parse date: {date_str}")
        return None

def normalize_themes(themes_str):
    """Convert comma-separated themes to array."""
    if not themes_str:
        return []
    return [t.strip() for t in themes_str.split(',') if t.strip()]

def migrate_scraper_2():
    """Migrate scraper_2.events (12,292 events)."""
    source_conn = psycopg2.connect(SOURCE_DB)
    target_conn = psycopg2.connect(TARGET_DB)

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    # Fetch all events
    source_cur.execute("""
        SELECT
            event_id, name, description, start_date, end_date,
            location_name, street_address, city, postal_code, country,
            latitude, longitude, organizer, event_type, themes,
            url, image_url, scraped_at, updated_at
        FROM scraper_2.events
    """)

    events = source_cur.fetchall()
    logger.info(f"Found {len(events)} events in scraper_2")

    inserted = 0
    skipped = 0

    for event in events:
        (external_id, name, description, start_date_str, end_date_str,
         location_name, street_address, city, postal_code, country,
         lat, lng, organizer, event_type, themes_str,
         url, image_url, scraped_at, updated_at) = event

        # Parse dates
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)

        # Skip if no start date or coordinates
        if not start_date or lat is None or lng is None:
            skipped += 1
            continue

        # Normalize themes
        themes = normalize_themes(themes_str)

        # Construct address
        address_parts = [p for p in [street_address, postal_code, city, country] if p]
        address = ', '.join(address_parts) if address_parts else location_name

        try:
            target_cur.execute("""
                INSERT INTO tripflow.events (
                    name, description, event_category, start_date, end_date,
                    location_name, address, city, country,
                    latitude, longitude, geom,
                    organizer, event_type, themes, external_url, image_url,
                    source, external_id, active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (external_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    updated_at = EXCLUDED.updated_at
            """, (
                name, description, event_type or 'other', start_date, end_date,
                location_name, address, city, country,
                lat, lng, lng, lat,  # geom uses lng, lat order
                organizer, event_type, themes, url, image_url,
                'uitinvlaanderen', external_id, True, scraped_at, updated_at
            ))
            inserted += 1

            if inserted % 100 == 0:
                target_conn.commit()
                logger.info(f"Inserted {inserted} events...")

        except Exception as e:
            logger.error(f"Error inserting event {external_id}: {e}")
            skipped += 1

    target_conn.commit()

    source_cur.close()
    target_cur.close()
    source_conn.close()
    target_conn.close()

    logger.info(f"Migration complete: {inserted} inserted, {skipped} skipped")

def migrate_scraper_3():
    """Migrate scraper_3.events (235 events)."""
    # Similar to scraper_2, adjust column mappings
    pass

if __name__ == "__main__":
    logger.info("Starting event migration from Scraparr to Tripflow")
    migrate_scraper_2()
    # migrate_scraper_3()
    logger.info("Migration complete!")
```

---

#### 1.2 Discovery API Endpoint

**File:** `/home/peter/work/tripflow/backend/app/api/discover.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import date, timedelta
from app.db.database import get_db
from app.models.event import Event
from app.api.schemas import EventResponse, DiscoveryResponse

router = APIRouter(prefix="/api/v1/discover", tags=["discovery"])

@router.get("", response_model=DiscoveryResponse)
def discover_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(10, ge=1, le=100),
    categories: Optional[List[str]] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Discover events near a location.

    - **latitude**: Center point latitude
    - **longitude**: Center point longitude
    - **radius_km**: Search radius in kilometers (default: 10km)
    - **categories**: Filter by event categories (optional)
    - **start_date**: Show events from this date (default: today)
    - **end_date**: Show events until this date (default: +30 days)
    - **limit**: Maximum results (default: 50)

    Returns events sorted by distance (nearest first).
    """

    # Default date range: today to +30 days
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today() + timedelta(days=30)

    radius_meters = radius_km * 1000

    # PostGIS query
    query = db.query(
        Event,
        func.ST_Distance(
            func.cast(Event.geom, "geography"),
            func.cast(
                func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                "geography"
            )
        ).label("distance_meters")
    ).filter(
        and_(
            Event.active == True,
            Event.start_date >= start_date,
            Event.start_date <= end_date,
            func.ST_DWithin(
                func.cast(Event.geom, "geography"),
                func.cast(
                    func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                    "geography"
                ),
                radius_meters
            )
        )
    )

    # Filter by categories
    if categories:
        query = query.filter(Event.event_category.in_(categories))

    # Order by distance
    query = query.order_by("distance_meters")

    results = query.limit(limit).all()

    events = [
        {
            **EventResponse.from_orm(event).dict(),
            "distance_km": round(distance_meters / 1000, 2)
        }
        for event, distance_meters in results
    ]

    return {
        "results": events,
        "total": len(events),
        "query": {
            "center": [latitude, longitude],
            "radius_km": radius_km,
            "date_range": [start_date, end_date]
        }
    }
```

**Schemas:** Add to `/home/peter/work/tripflow/backend/app/api/schemas.py`

```python
class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    event_category: str
    start_date: date
    end_date: Optional[date]
    location_name: Optional[str]
    city: Optional[str]
    latitude: float
    longitude: float
    image_url: Optional[str]
    external_url: Optional[str]
    themes: List[str] = []
    organizer: Optional[str]

    class Config:
        from_attributes = True

class DiscoveryResponse(BaseModel):
    results: List[EventResponse]
    total: int
    query: Dict[str, Any]
```

**Register Router:** In `/home/peter/work/tripflow/backend/app/api/__init__.py`

```python
from .discover import router as discover_router

# ... existing code ...
app.include_router(discover_router)
```

---

#### 1.3 Favorites API Endpoints

**File:** `/home/peter/work/tripflow/backend/app/api/favorites.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.models.event import Event

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])

@router.post("/{event_id}")
def add_favorite(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save an event to favorites."""
    # Check event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check if already favorited
    existing = db.execute(
        "SELECT 1 FROM tripflow.user_favorites WHERE user_id = :uid AND event_id = :eid",
        {"uid": current_user.id, "eid": event_id}
    ).fetchone()

    if existing:
        return {"message": "Already favorited", "event_id": event_id}

    # Insert favorite
    db.execute(
        "INSERT INTO tripflow.user_favorites (user_id, event_id) VALUES (:uid, :eid)",
        {"uid": current_user.id, "eid": event_id}
    )
    db.commit()

    return {"message": "Added to favorites", "event_id": event_id}

@router.delete("/{event_id}")
def remove_favorite(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an event from favorites."""
    db.execute(
        "DELETE FROM tripflow.user_favorites WHERE user_id = :uid AND event_id = :eid",
        {"uid": current_user.id, "eid": event_id}
    )
    db.commit()
    return {"message": "Removed from favorites", "event_id": event_id}

@router.get("")
def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's favorite events."""
    results = db.execute("""
        SELECT e.*
        FROM tripflow.events e
        JOIN tripflow.user_favorites f ON e.id = f.event_id
        WHERE f.user_id = :uid
        ORDER BY f.created_at DESC
    """, {"uid": current_user.id}).fetchall()

    return {"favorites": [EventResponse.from_orm(r) for r in results]}
```

---

### Phase 2: Frontend - Discovery UI (Week 2)

#### 2.1 DiscoveryPage Component

**File:** `/home/peter/work/tripflow/frontend/src/pages/DiscoveryPage.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import MapView from '../components/MapView';
import BottomSheet from '../components/BottomSheet';
import EventCard from '../components/EventCard';
import EventDetailModal from '../components/EventDetailModal';
import { discoverNearby } from '../services/discoveryService';
import './DiscoveryPage.css';

export default function DiscoveryPage() {
  const { user } = useAuth();
  const [userLocation, setUserLocation] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [radiusKm, setRadiusKm] = useState(10);
  const [locationPermission, setLocationPermission] = useState('prompt'); // 'prompt', 'granted', 'denied'

  // Request location permission
  const requestLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation not supported');
      return;
    }

    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        setUserLocation(location);
        setSelectedLocation(location);
        setLocationPermission('granted');
        fetchEvents(location.lat, location.lng);
      },
      (error) => {
        console.error('Location error:', error);
        setLocationPermission('denied');
        setLoading(false);
        // Default to Belgium center
        setSelectedLocation({ lat: 50.8503, lng: 4.3517 });
      }
    );
  };

  // Fetch events near location
  const fetchEvents = async (lat, lng) => {
    setLoading(true);
    try {
      const data = await discoverNearby(lat, lng, radiusKm);
      setEvents(data.results);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-request location on mount
  useEffect(() => {
    if (locationPermission === 'prompt') {
      requestLocation();
    }
  }, []);

  // Refetch when radius changes
  useEffect(() => {
    if (selectedLocation) {
      fetchEvents(selectedLocation.lat, selectedLocation.lng);
    }
  }, [radiusKm]);

  return (
    <div className="discovery-page">
      {/* Location Permission Banner */}
      {locationPermission === 'denied' && (
        <div className="location-banner">
          <p>📍 Location access denied. <button onClick={requestLocation}>Try Again</button> or search for a location.</p>
        </div>
      )}

      {/* Map */}
      <MapView
        center={selectedLocation || { lat: 50.8503, lng: 4.3517 }}
        zoom={radiusKm <= 10 ? 12 : 10}
        events={events}
        userLocation={userLocation}
        onEventClick={(event) => setSelectedEvent(event)}
        onMapClick={(lat, lng) => {
          setSelectedLocation({ lat, lng });
          fetchEvents(lat, lng);
        }}
      />

      {/* Bottom Sheet with Event List */}
      <BottomSheet>
        <div className="discovery-controls">
          <label>
            Radius:
            <select value={radiusKm} onChange={(e) => setRadiusKm(Number(e.target.value))}>
              <option value={5}>5 km</option>
              <option value={10}>10 km</option>
              <option value={25}>25 km</option>
              <option value={50}>50 km</option>
            </select>
          </label>
        </div>

        <div className="events-list">
          {loading && <p>Loading events...</p>}
          {!loading && events.length === 0 && <p>No events found nearby.</p>}
          {events.map(event => (
            <EventCard
              key={event.id}
              event={event}
              onClick={() => setSelectedEvent(event)}
            />
          ))}
        </div>
      </BottomSheet>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  );
}
```

---

#### 2.2 EventCard Component

**File:** `/home/peter/work/tripflow/frontend/src/components/EventCard.jsx`

```jsx
import React from 'react';
import './EventCard.css';

export default function EventCard({ event, onClick }) {
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  };

  return (
    <div className="event-card" onClick={onClick}>
      {event.image_url && (
        <div className="event-card-image">
          <img src={event.image_url} alt={event.name} onError={(e) => e.target.style.display = 'none'} />
        </div>
      )}

      <div className="event-card-content">
        <div className="event-card-header">
          <h3>{event.name}</h3>
          <span className="event-distance">{event.distance_km} km</span>
        </div>

        <div className="event-card-meta">
          <span className="event-date">📅 {formatDate(event.start_date)}</span>
          <span className="event-location">📍 {event.city}</span>
        </div>

        {event.themes && event.themes.length > 0 && (
          <div className="event-themes">
            {event.themes.slice(0, 3).map((theme, idx) => (
              <span key={idx} className="theme-tag">{theme}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

#### 2.3 Update Routing

**File:** `/home/peter/work/tripflow/frontend/src/App.jsx`

```jsx
import DiscoveryPage from './pages/DiscoveryPage';

function App() {
  return (
    <Router>
      <AuthProvider>
        <TripProvider>
          <Header />
          <Routes>
            {/* Discovery is now the default landing page */}
            <Route path="/" element={<DiscoveryPage />} />

            {/* Auth routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Trip planning (moved to /plan) */}
            <Route path="/plan" element={<TripFlowWizard />} />

            {/* User pages */}
            <Route path="/favorites" element={<FavoritesPage />} />
            <Route path="/my-trips" element={<MyTripsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Routes>
        </TripProvider>
      </AuthProvider>
    </Router>
  );
}
```

---

## Next Steps

### Immediate Actions (This Session)
1. ✅ Create plan document (this file)
2. ⏭️ Enhance database schema (SQL migrations)
3. ⏭️ Write event migration script
4. ⏭️ Run migration to populate events
5. ⏭️ Create discovery API endpoint
6. ⏭️ Test API with curl/Postman

### Follow-up (Next Session)
1. Build DiscoveryPage React component
2. Create EventCard and BottomSheet components
3. Update MapView to show event markers
4. Implement EventDetailModal
5. Add favorites functionality
6. Deploy to scraparr server

---

## Questions & Decisions

### Answered
1. **Default Landing:** Yes, discovery replaces wizard as `/`
2. **Auth Requirements:** Discovery works for anonymous users, login required only for favorites
3. **Image Fallbacks:** Hide image if URL is null/broken
4. **Radius Limits:** Max 100km to prevent huge queries
5. **Event Expiry:** Hide events with start_date < today
6. **Trip Planning:** Keep full wizard, but move to `/plan` route

### Open Questions
- Should we show past events in a separate "Archive" view?
- Do we need event categories beyond what's in the data?
- Should we add push notifications for saved events?

---

## Success Metrics

**MVP Success Criteria:**
- [ ] 12,500+ events migrated to tripflow database
- [ ] Discovery API returns results in <500ms for 50km radius
- [ ] Frontend loads and displays events on map
- [ ] User can save events to favorites (auth required)
- [ ] Mobile-responsive UI works on phone screens

**Post-MVP Goals:**
- Add static POI data (museums, parks, restaurants)
- Implement "For You" personalized recommendations
- Add event reminders/notifications
- Support trip planning from saved events
- PWA offline support

---

**End of Plan**
