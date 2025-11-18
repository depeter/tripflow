# TripFlow - AI-Powered Travel Planning Application

## Project Overview

TripFlow is a full-stack web application for planning multi-day and day trips with AI-powered recommendations. Users can plan trips by selecting interests, browsing AI recommendations, searching for custom locations, and generating beautiful PDF itineraries.

**Technology Stack:**
- **Frontend**: React 18.2.0, React Router, Leaflet maps, jsPDF
- **Backend**: FastAPI (Python), PostgreSQL with PostGIS, Qdrant vector DB, Redis
- **Deployment**: Docker Compose with 7 containers, nginx reverse proxy
- **APIs**: OpenStreetMap Nominatim (geocoding), OSRM (routing)

## Quick Deployment

**For production deployment to scraparr server:**
```bash
cd /home/peter/work/tripflow
./deploy.sh
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment documentation.

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

7. **User Authentication** (Nov 15, 2025)
   - Login page with email/password
   - Registration page with validation
   - JWT token management
   - Automatic token refresh
   - User menu with avatar dropdown
   - Protected routes ready
   - OAuth placeholders (Google/Microsoft)

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
   - ✅ Database schema created and deployed (Nov 15, 2025)
   - ❌ No seed data for locations/events
   - ❌ Qdrant vector database not indexed

2. **Backend Functionality**
   - ❌ No actual location data in database
   - ❌ Recommendation engine needs data
   - ✅ User authentication implemented (backend + frontend)
   - ❌ Email itinerary feature (placeholder)

3. **Frontend Features**
   - ⚠️ Backend API integration partially complete (needs data)
   - ✅ User authentication/login UI (Nov 15, 2025)
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
│   │   ├── App.jsx                 # Main app component with routes
│   │   ├── index.css               # Global styles
│   │   ├── context/
│   │   │   ├── TripContext.jsx     # Trip state management
│   │   │   └── AuthContext.jsx     # Auth state management
│   │   ├── pages/
│   │   │   ├── Login.jsx           # Login page
│   │   │   ├── Register.jsx        # Registration page
│   │   │   ├── Auth.css            # Auth pages stylesheet
│   │   │   ├── TripFlowWizard.jsx  # Main wizard container
│   │   │   ├── Step1_TripType.jsx
│   │   │   ├── Step2_Duration.jsx
│   │   │   ├── Step3_Preferences.jsx
│   │   │   ├── Step4_Recommendations.jsx
│   │   │   ├── Step5_CustomizeRoute.jsx
│   │   │   └── Step6_ReviewFinalize.jsx
│   │   ├── components/
│   │   │   ├── Header.jsx          # Navigation header with user menu
│   │   │   ├── Header.css          # Header styles
│   │   │   ├── MapView.jsx         # Leaflet map component
│   │   │   ├── LocationCard.jsx
│   │   │   ├── ProgressBar.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   └── services/
│   │       ├── api.js              # Axios client with auth
│   │       ├── authService.js      # Auth API calls
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

**Authentication System** (Nov 15, 2025)

The frontend now has a complete authentication system:

**AuthContext** (`src/context/AuthContext.jsx`):
- Manages user state and authentication status
- Provides login, register, logout, refreshUser functions
- Automatically loads user on app mount
- Stores JWT tokens in localStorage

**API Integration** (`src/services/api.js`):
- Axios interceptor adds Bearer token to all requests
- Automatic token refresh on 401 responses
- Redirects to login on auth failure

**Auth Pages**:
- `/login` - Email/password login with OAuth buttons
- `/register` - User registration with validation
- Modern gradient design with error handling

**Header Component** (`src/components/Header.jsx`):
- Navigation links (Plan Trip, My Trips)
- User avatar dropdown with menu
- Sign In/Get Started buttons when not authenticated
- Profile, Settings, Sign Out options

**Routes**:
```javascript
/ - Trip planning wizard (with header)
/login - Login page
/register - Registration page
/my-trips - Saved trips (placeholder)
/profile - User profile (placeholder)
/settings - Account settings (placeholder)
```

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
localStorage.removeItem('access_token')           # Clear auth tokens
localStorage.removeItem('refresh_token')
docker compose restart  # Restart services
rm -rf backend/venv && python -m venv venv  # Recreate venv if needed
rm -rf frontend/node_modules && npm install  # Reinstall packages
```

### Authentication Testing

**Test User Login:**
```bash
# Start backend
cd /home/peter/work/tripflow/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Start frontend
cd /home/peter/work/tripflow/frontend
npm start

# Visit http://localhost:3000/register to create account
# Or use existing admin user: admin@tripflow.com / admin123
```

**API Testing:**
```bash
# Test registration
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","full_name":"Test User"}'

# Test login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"

# Test authenticated endpoint
TOKEN="your_token_here"
curl -X GET http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
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
**Last Updated:** 2025-11-15
**Version:** 0.2.0 (Alpha - Authentication Added)

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
- ✅ User authentication (login/register)
- ✅ Protected API routes
- ✅ JWT token management

**What Needs Data:**
- ❌ AI recommendations (no locations in DB)
- ❌ Saved trips (no user auth)
- ❌ Event integration (no event data)

**Immediate Next Step:**
Run database migrations and add seed data to enable full backend functionality.

## Production Deployment (Scraparr Server)

**Deployed**: November 15, 2025  
**Server**: scraparr (192.168.1.149)  
**Location**: `/home/peter/tripflow`

### Running Services

```
✅ Tripflow Backend API: http://192.168.1.149:8001
   - Health: http://192.168.1.149:8001/health
   - API Docs: http://192.168.1.149:8001/docs
   - Process: uvicorn app.main:app (port 8001)

✅ Tripflow PostgreSQL: localhost:5433
   - Container: tripflow-postgres
   - User: postgres/tripflow
   - Database: tripflow
   - Schema: tripflow (12 tables)

✅ Qdrant Vector DB: localhost:6333
   - Container: tripflow-qdrant
   - Collection: locations (exists but not indexed)

✅ Redis: localhost:6379
   - Container: tripflow-redis
   - Used for: Celery task queue

❌ Frontend: Not deployed yet
   - Node.js not installed on server
   - Plan: Production build with nginx
```

### Database Schema (Tripflow)

**Schema**: `tripflow` (all tables use this schema)

**Tables Created** (12 total):
```sql
-- Authentication & Users
tripflow.users                      -- User accounts (admin@tripflow.com seeded)
tripflow.user_sessions              -- JWT session tracking
tripflow.oauth_connections          -- Google/Microsoft OAuth
tripflow.email_verification_tokens  -- Email verification
tripflow.password_reset_tokens      -- Password reset flow

-- Core Data
tripflow.locations                  -- Camping/parking locations (empty)
tripflow.events                     -- Time-based events (empty)
tripflow.reviews                    -- Location reviews

-- Analytics & Tracking
tripflow.trip_creations             -- Trip planning analytics
tripflow.api_usage                  -- API usage tracking
tripflow.sync_log                   -- ETL sync history
tripflow.data_quality_metrics       -- Data quality monitoring
```

**Missing Tables** (will be auto-created when needed):
- `trips` - Trip plans (model exists, table creation blocked by permissions - now fixed)
- `subscriptions` - User subscriptions
- `subscription_usage` - Usage tracking
- `payment_history` - Payment records
- `migration_runs` - Migration tracking (may exist in SQL)
- `scraper_metadata` - Scraper info (may exist in SQL)

### Deployment Fixes Applied (Nov 15, 2025)

1. **Python Dependencies**:
   - Downgraded `huggingface-hub` from 0.36.0 → 0.19.4 (compatibility with sentence-transformers)
   - Downgraded `transformers` from 4.57.1 → 4.40.2
   - Downgraded `tokenizers` from 0.22.1 → 0.19.1
   - Installed `email-validator==2.3.0` for Pydantic email validation

2. **Code Fixes**:
   - Fixed `app/models/base.py`: Added `metadata = MetaData(schema="tripflow")`
   - Fixed `app/models/trip.py`: Changed `ForeignKey("users.id")` → `ForeignKey("tripflow.users.id")`
   - Fixed `app/models/event.py`: Changed `ForeignKey("locations.id")` → `ForeignKey("tripflow.locations.id")`
   - Fixed `app/services/recommendation_service.py`: Removed non-existent `UserPreference` import

3. **Database Configuration**:
   - Updated `.env`: Changed port from 5435 → 5433
   - Granted CREATE permission on schema: `GRANT CREATE ON SCHEMA tripflow TO tripflow;`
   - Changed table ownership: `ALTER TABLE tripflow.* OWNER TO tripflow;`
   - Granted all privileges: `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tripflow TO tripflow;`

4. **Schema Initialization**:
   - Ran `/home/peter/work/tripflow/backend/db/init_tripflow_schema.sql` (core tables)
   - Ran `/home/peter/work/tripflow/migrations/add_users_auth.sql` (auth tables)
   - SQLAlchemy will auto-create missing tables on first use

### Integration with Scraparr

**Data Flow**:
```
Scraparr DB (port 5434) → Migration Scripts → Tripflow DB (port 5433)
```

**Source Databases**:
- Scraparr PostgreSQL: `localhost:5434`
  - `scraper_2.places` - Park4Night camping spots (~49,000 records)
  - `scraper_3.events` - UiT in Vlaanderen events (~10,000 records)

**Migration Process** (not yet run):
```bash
cd /home/peter/tripflow/migrations
source ../venv/bin/activate
python migrate_all_scrapers.py
```

This will transform and load data from Scraparr into Tripflow's normalized schema.

### Configuration Files

**Backend `.env`** (on server):
```env
DATABASE_URL=postgresql://tripflow:tripflow@localhost:5433/tripflow
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379/0

# Source databases (for migration)
SCRAPARR_DB_HOST=localhost
SCRAPARR_DB_PORT=5434
SOURCE_DB_PARK4NIGHT=postgresql://scraparr:scraparr@localhost:5434/scraparr
```

### Deployment Commands

**Check Services**:
```bash
# Backend health
curl http://192.168.1.149:8001/health

# View logs
ssh peter@scraparr "tail -f /home/peter/tripflow/backend.log"

# Check database
ssh peter@scraparr "docker exec tripflow-postgres psql -U postgres -d tripflow -c '\dt tripflow.*'"
```

**Restart Backend**:
```bash
ssh peter@scraparr "ps aux | grep 'uvicorn app.main' | grep -v grep | awk '{print \$2}' | xargs kill -9"
ssh peter@scraparr "cd /home/peter/tripflow && source venv/bin/activate && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &"
```

**Deploy Code Changes**:
```bash
# From development machine
cd /home/peter/work/tripflow
./deploy-to-scraparr.sh

# Or manually
cat > /tmp/scraparr_pass.sh << 'EOF'
#!/bin/sh
echo "nomansland"
EOF
chmod +x /tmp/scraparr_pass.sh

SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  scp -r backend frontend docker-compose.yml migrations peter@scraparr:/home/peter/tripflow/

SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  ssh peter@scraparr "cd /home/peter/tripflow && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
```

### Known Issues

**Fixed Issues:**
- ✅ `huggingface_hub` import error → downgraded to 0.19.4
- ✅ Missing `email-validator` → installed via pip
- ✅ `UserPreference` import error → removed from recommendation_service.py
- ✅ Database port mismatch (5435 vs 5433) → updated .env
- ✅ SQLAlchemy schema not configured → added `metadata = MetaData(schema="tripflow")`
- ✅ Foreign keys without schema prefix → added "tripflow." to all FKs
- ✅ Database permission errors → granted privileges and changed table ownership

**Current Limitations:**
- Frontend deployment incomplete (Node.js not installed on scraparr server)
- Data migration not run yet (60,000+ locations waiting)
- Qdrant indexing not performed yet
- No production build of frontend created yet

### Next Steps

**Phase 1: Complete Backend Deployment** ✅
- [x] Fix backend dependencies (huggingface_hub, email-validator)
- [x] Fix database schema and permissions
- [x] Start Qdrant and Redis containers
- [x] Verify backend health endpoint works

**Phase 2: Data Migration & Indexing**
```bash
# Run data migration from Scraparr to Tripflow
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  ssh peter@scraparr "cd /home/peter/tripflow && source venv/bin/activate && python -m scripts.sync_from_scraparr"

# Index locations in Qdrant for AI recommendations
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  ssh peter@scraparr "cd /home/peter/tripflow && source venv/bin/activate && python -m scripts.index_locations"
```

**Phase 3: Frontend Deployment**
```bash
# Install Node.js on scraparr server (if needed)
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  ssh peter@scraparr "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs"

# Build and deploy frontend
cd /home/peter/work/tripflow/frontend
npm install
npm run build

# Upload production build
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  scp -r build peter@scraparr:/home/peter/tripflow/frontend/

# Configure nginx to serve frontend (see scraparr nginx config)
```

**Phase 4: Integration Testing**
- Test auth endpoints (login, register, JWT tokens)
- Test location search and recommendations
- Test trip creation and planning
- Verify Qdrant semantic search working
- Check database query performance with 60K+ locations

### Important Notes

- **CPU-Only ML**: sentence-transformers runs on CPU despite PyTorch CUDA libs installed
- **Schema Prefix Required**: All SQLAlchemy foreign keys must include "tripflow." schema prefix
- **Data Source**: Tripflow reads Scraparr data via migration scripts, doesn't query Scraparr DB directly
- **Port Allocation**: Backend 8001, Scraparr backend 8000, Tripflow DB 5433, Scraparr DB 5434
- **Admin Credentials**: admin@tripflow.com / admin123 (seeded in add_users_auth.sql)
