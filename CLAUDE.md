# TripFlow - AI-Powered Travel Planning Application

## Project Overview

TripFlow is a full-stack web application for planning multi-day and day trips with AI-powered recommendations. Users can plan trips by selecting interests, browsing AI recommendations, searching for custom locations, and generating beautiful PDF itineraries.

**Technology Stack:**
- **Frontend**: React 18.2.0, React Router, Leaflet maps, jsPDF
- **Backend**: FastAPI (Python), PostgreSQL with PostGIS, Qdrant vector DB, Redis
- **APIs**: OpenStreetMap Nominatim (geocoding), OSRM (routing)

## Current Status

### ✅ Completed Features

#### Frontend (React)
1. **Complete 6-Step Wizard**
   - Step 1: Trip Type Selection (Multi-Day vs Day Trip)
   - Step 2: Interactive Route Planning with map
   - Step 3: Interests & Preferences selection
   - Step 4: AI Recommendations + Custom Location Search
   - Step 5: Customize Route (drag-and-drop reordering)
   - Step 6: Review & Finalize with PDF export

2. **Interactive Mapping**
   - Leaflet integration with OpenStreetMap tiles
   - Real-time route calculation and display
   - Click-to-add custom locations
   - Draggable markers
   - Numbered waypoint markers
   - Route polylines with distance/time stats

3. **Location Search & Discovery**
   - Search bar with autocomplete (OpenStreetMap Nominatim)
   - Click anywhere on map to add custom locations
   - Reverse geocoding for map clicks
   - Browse AI recommendations (when backend has data)
   - Filter by type, rating
   - Sort by match score, rating, price, distance

4. **Trip Management**
   - Real-time route recalculation
   - Drag-and-drop waypoint reordering
   - Add/remove waypoints
   - Round trip vs one-way options
   - Duration-based planning
   - LocalStorage auto-save

5. **PDF Export**
   - Professional trip itinerary PDFs
   - Color-coded sections
   - Waypoint details with icons
   - Trip statistics and summary
   - Auto-generated filenames

6. **State Management**
   - React Context API for global state
   - LocalStorage persistence
   - Validation and error handling

#### Backend (FastAPI)
1. **API Structure**
   - `/api/v1/trips/` - Trip CRUD operations
   - `/api/v1/recommendations/` - AI recommendations
   - `/api/v1/locations/` - Location search
   - Health check endpoint at `/health`
   - Auto-generated API docs at `/docs`

2. **Database Models**
   - Location (with PostGIS geometry)
   - Event (time-based events)
   - Trip
   - Waypoint
   - User preferences

3. **Services**
   - Location service
   - Trip planning service
   - Recommendation service (Qdrant + ML)
   - Route optimization

4. **Configuration**
   - Environment-based settings
   - CORS enabled for frontend
   - PostgreSQL + Qdrant + Redis integration

### 🚧 Missing/Incomplete Features

1. **Database Setup**
   - ❌ Database migrations not run (tables don't exist yet)
   - ❌ No seed data for locations/events
   - ❌ Qdrant vector database not indexed

2. **Backend Functionality**
   - ❌ No actual location data in database
   - ❌ Recommendation engine needs data
   - ❌ User authentication not implemented
   - ❌ Email itinerary feature (placeholder)

3. **Frontend Features**
   - ⚠️ Backend API integration partially complete (needs data)
   - ❌ User authentication/login
   - ❌ Save trips to account
   - ❌ View past trips
   - ❌ Share trip URLs

4. **Data Pipeline**
   - ❌ No data scraping/import from camper sites
   - ❌ No event data integration
   - ❌ No location photo integration

## Project Structure

```
tripflow/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── locations.py        # Location endpoints
│   │   │   ├── trips.py            # Trip endpoints
│   │   │   └── recommendations.py  # Recommendation endpoints
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── location.py         # Location, LocationType, LocationSource
│   │   │   ├── event.py            # Event, EventCategory
│   │   │   └── trip.py             # Trip, Waypoint models
│   │   ├── services/
│   │   │   ├── location_service.py
│   │   │   ├── trip_service.py
│   │   │   └── recommendation_service.py
│   │   ├── core/
│   │   │   ├── config.py           # Settings
│   │   │   └── database.py         # DB connection
│   │   └── db/
│   ├── .env                        # Environment variables
│   ├── requirements.txt            # Python dependencies
│   └── venv/                       # Python virtual environment
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── index.js                # React entry point
│   │   ├── App.jsx                 # Main app component
│   │   ├── index.css               # Global styles
│   │   ├── context/
│   │   │   └── TripContext.jsx     # Global state management
│   │   ├── pages/
│   │   │   ├── TripFlowWizard.jsx  # Main wizard container
│   │   │   ├── Step1_TripType.jsx
│   │   │   ├── Step2_Duration.jsx
│   │   │   ├── Step3_Preferences.jsx
│   │   │   ├── Step4_Recommendations.jsx
│   │   │   ├── Step5_CustomizeRoute.jsx
│   │   │   └── Step6_ReviewFinalize.jsx
│   │   ├── components/
│   │   │   ├── MapView.jsx         # Leaflet map component
│   │   │   ├── LocationCard.jsx
│   │   │   ├── ProgressBar.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   └── services/
│   │       ├── api.js              # Axios client
│   │       ├── tripsService.js     # Backend API calls
│   │       ├── geocodingService.js # OSM Nominatim + OSRM
│   │       ├── recommendationsService.js  # Mock data (legacy)
│   │       └── pdfService.js       # PDF generation
│   ├── .env                        # Frontend env vars
│   ├── package.json
│   └── node_modules/
│
├── docs/
│   ├── FRONTEND_PLAN.md           # Original plan
│   └── BACKEND_PLAN.md            # Backend architecture
│
└── CLAUDE.md                      # This file
```

## Running the Application

### Prerequisites
- Node.js 16+
- Python 3.11+
- PostgreSQL 14+ with PostGIS
- Docker & Docker Compose (for services)

### Quick Start

**1. Start Database Services**
```bash
cd /home/peter/tripflow
docker compose up -d postgres qdrant redis
```

**2. Start Backend**
```bash
cd /home/peter/tripflow/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
- Backend runs on: http://localhost:8001
- API docs: http://localhost:8001/docs

**3. Start Frontend**
```bash
cd /home/peter/tripflow/frontend
npm start
```
- Frontend runs on: http://localhost:3000

### Current Running Services

Check status:
```bash
# Backend
curl http://localhost:8001/health

# Database
docker ps | grep -E "postgres|qdrant|redis"

# Frontend (check browser)
curl http://localhost:3000
```

## Environment Configuration

### Backend (.env)
```env
APP_NAME=TripFlow
DEBUG=True
DATABASE_URL=postgresql://tripflow:tripflow@localhost:5432/tripflow
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SYNC_ENABLED=False
SECRET_KEY=dev-secret-key-change-in-production
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### Frontend (.env)
```env
REACT_APP_API_BASE_URL=http://localhost:8001
REACT_APP_NAME=TripFlow
```

## Key Implementation Details

### Frontend Architecture

**State Management (TripContext.jsx)**
```javascript
{
  trip_type: 'multi_day' | 'day_trip',
  start_address: string,
  start_coordinates: {lat, lng},
  duration_days: number,
  duration_hours: number,
  max_distance_km: number,
  is_round_trip: boolean,
  waypoints: [],  // For Step 2 intermediate points
  selected_waypoints: [],  // Final selected locations
  interests: [],
  preferred_environment: [],
  route_stats: {
    total_distance_km: number,
    estimated_driving_hours: number,
    feasibility_status: 'comfortable' | 'tight' | 'too_ambitious'
  },
  current_step: 1-6,
  completed_steps: []
}
```

**Geocoding Integration**
- Uses OpenStreetMap Nominatim for address search
- Debounced search (300ms) to reduce API calls
- OSRM for route calculation between waypoints
- Reverse geocoding for map clicks

**PDF Generation**
- jsPDF for document creation
- Color-coded sections (green header, blue waypoints)
- Automatic page breaks
- Professional formatting with icons

### Backend Architecture

**Database Models**
- SQLAlchemy ORM with async support
- PostGIS for geographic queries
- Alembic for migrations (not yet run)

**Recommendation Engine**
- Qdrant vector database for semantic search
- Sentence transformers for embeddings
- Match scoring based on user preferences

**API Design**
- RESTful endpoints
- Pydantic schemas for validation
- Async/await throughout
- CORS enabled for frontend

## Known Issues & Fixes

### Issue 1: Navigation Not Working
**Problem**: All steps marked complete, can't navigate
**Solution**: Clear localStorage and refresh
```javascript
localStorage.removeItem('tripflow_current_trip');
location.reload();
```

### Issue 2: Map Marker Icon Error
**Problem**: `can't access property "createIcon", options.icon is undefined`
**Solution**: Fixed - don't pass `icon={undefined}`, only add icon prop when needed

### Issue 3: React Key Warning
**Problem**: Key prop being spread into component
**Solution**: Fixed - pass key directly to component, not in spread props

### Issue 4: Backend Port Conflict
**Problem**: Port 8000 already in use by scraparr-backend
**Solution**: Backend runs on port 8001 instead

## Next Steps for Production

### Critical Path
1. **Database Setup**
   ```bash
   cd /home/peter/tripflow/backend
   source venv/bin/activate
   alembic upgrade head  # Run migrations
   python scripts/seed_data.py  # Need to create this
   ```

2. **Add Location Data**
   - Scrape camper sites (Park4Night, CamperContact)
   - Import tourist attractions (OpenStreetMap POIs)
   - Add events (local APIs)
   - Index in Qdrant for recommendations

3. **User Authentication**
   - Add user model
   - Implement JWT auth
   - Protect trip endpoints
   - Add login/signup UI

4. **Trip Persistence**
   - Save trips to database (currently only localStorage)
   - View past trips
   - Edit saved trips
   - Share trip links

### Nice to Have
- Email itinerary feature
- Real-time weather integration
- Cost estimation improvements
- Photo integration for locations
- Mobile responsive improvements
- Progressive Web App (PWA)
- Offline mode support

## Development Workflow

### Adding a New Feature
1. Update models if needed (`backend/app/models/`)
2. Create/update API endpoints (`backend/app/api/`)
3. Update frontend service (`frontend/src/services/`)
4. Create/update React components
5. Test full stack integration
6. Update this CLAUDE.md file

### Testing Changes
```bash
# Backend
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/trips/

# Frontend - check browser console for errors
# Check Network tab for API calls
```

### Common Commands
```bash
# Install new Python package
cd backend
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt

# Install new npm package
cd frontend
npm install package-name

# Create database migration
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head

# Clear frontend cache
localStorage.clear()  # In browser console
```

## Important Files Reference

### Configuration Files
- `backend/.env` - Backend environment variables
- `frontend/.env` - Frontend environment variables
- `backend/app/core/config.py` - Backend settings class
- `docker-compose.yml` - Service definitions

### Entry Points
- `backend/app/main.py` - FastAPI application
- `frontend/src/index.js` - React application
- `frontend/src/App.jsx` - React router setup

### Core Services
- `frontend/src/context/TripContext.jsx` - Global state
- `frontend/src/services/tripsService.js` - Backend API
- `frontend/src/services/geocodingService.js` - Maps/routing
- `frontend/src/services/pdfService.js` - PDF generation
- `backend/app/services/recommendation_service.py` - AI recommendations

## Debugging Tips

### Backend Issues
```bash
# Check logs
docker logs tripflow-postgres
docker logs tripflow-qdrant
docker logs tripflow-redis

# Test database connection
psql postgresql://tripflow:tripflow@localhost:5432/tripflow

# Check Qdrant
curl http://localhost:6333/collections
```

### Frontend Issues
```bash
# Check for compilation errors
# Errors appear in terminal where npm start is running

# Clear cache
rm -rf node_modules/.cache
npm start

# Check browser console
# Network tab for API calls
# React DevTools for component state
```

### Common Fixes
```bash
# Reset everything
localStorage.removeItem('tripflow_current_trip')  # Browser console
docker compose restart  # Restart services
rm -rf backend/venv && python -m venv venv  # Recreate venv if needed
rm -rf frontend/node_modules && npm install  # Reinstall packages
```

## Security Notes

⚠️ **Current Security Issues (Development Only):**
- No authentication
- Debug mode enabled
- Simple secret key
- CORS allows all origins
- No rate limiting
- No input sanitization

🔒 **Before Production:**
- Implement proper authentication
- Use strong secret keys
- Restrict CORS origins
- Add rate limiting
- Validate/sanitize all inputs
- Enable HTTPS
- Use environment variables properly
- Add request logging
- Implement CSRF protection

## Contact & Resources

**External APIs:**
- OpenStreetMap Nominatim: https://nominatim.org/
- OSRM Routing: http://project-osrm.org/
- Leaflet: https://leafletjs.com/

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Qdrant: https://qdrant.tech/documentation/
- jsPDF: https://github.com/parallax/jsPDF

**Project Status:** Active Development
**Last Updated:** 2025-11-04
**Version:** 0.1.0 (Alpha)

---

## Quick Reference: Current Session State

**What's Running:**
- Frontend: http://localhost:3000 (React dev server)
- Backend: http://localhost:8001 (FastAPI with uvicorn)
- PostgreSQL: localhost:5432 (Docker container)
- Qdrant: localhost:6333 (Docker container)
- Redis: localhost:6379 (Docker container)

**What Works:**
- ✅ Complete wizard flow
- ✅ Interactive mapping
- ✅ Location search
- ✅ PDF export
- ✅ Route calculation
- ✅ State persistence

**What Needs Data:**
- ❌ AI recommendations (no locations in DB)
- ❌ Saved trips (no user auth)
- ❌ Event integration (no event data)

**Immediate Next Step:**
Run database migrations and add seed data to enable full backend functionality.
