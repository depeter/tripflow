# TripFlow

**TripFlow** is an intelligent travel planning application that helps campers and day-trippers discover and plan trips based on their personal preferences and interests. It uses data from Park4Night, CamperContact, and local sites to provide personalized location recommendations and smart route planning.

## Features

### Core Features
- **Smart Trip Planning**: Plan trips with start/end points, distance constraints, and duration
- **Personalized Recommendations**: AI-powered location suggestions based on user preferences
- **Waypoint Suggestions**: Automatically suggest optimal stops along your route
- **Flow-Based Interface**: Step-by-step guided trip planning experience
- **Multi-Source Data**: Aggregates data from Park4Night, CamperContact, and local sites
- **Event Discovery**: Find nearby events and activities along your route

### Technical Features
- **Semantic Search**: Uses Qdrant vector database for intelligent similarity search
- **Geospatial Queries**: Efficient location searches with PostGIS
- **Preference Learning**: Learns from user interactions to improve recommendations
- **Scheduled Sync**: Automatic data synchronization from source databases
- **RESTful API**: Clean, documented API for all operations

## Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React (to be implemented)
- **Databases**:
  - PostgreSQL with PostGIS for structured data and geospatial queries
  - Qdrant for vector search and recommendations
  - Redis for task queue and caching
- **Task Queue**: Celery for scheduled data synchronization
- **ML**: Sentence Transformers for text embeddings

### Project Structure

```
tripflow/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints
│   │   │   ├── locations.py
│   │   │   ├── trips.py
│   │   │   └── recommendations.py
│   │   ├── core/             # Configuration
│   │   ├── db/               # Database connections
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   │   ├── location_service.py
│   │   │   ├── trip_service.py
│   │   │   └── recommendation_service.py
│   │   ├── sync/             # Data import/sync system
│   │   │   ├── base_importer.py
│   │   │   ├── park4night_importer.py
│   │   │   ├── campercontact_importer.py
│   │   │   ├── local_sites_importer.py
│   │   │   ├── sync_manager.py
│   │   │   ├── sync_cli.py
│   │   │   └── celery_tasks.py
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React app (to be implemented)
├── docs/                     # Documentation
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with PostGIS extension
- Redis
- Node.js 18+ (for frontend)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/depeter/tripflow.git
cd tripflow
```

2. **Set up Python environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database URLs and settings
```

4. **Set up databases**
```bash
# Create PostgreSQL database
createdb tripflow

# Enable PostGIS extension
psql tripflow -c "CREATE EXTENSION postgis;"
```

5. **Initialize database**
```bash
cd app
python -c "from db.database import init_db; init_db()"
```

6. **Run the API server**
```bash
python -m app.main
# Or with uvicorn:
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Data Synchronization

#### Configure Source Databases

Edit your `.env` file with connection strings to your source databases:
```env
SOURCE_DB_PARK4NIGHT=postgresql://user:password@host:5432/park4night
SOURCE_DB_CAMPERCONTACT=postgresql://user:password@host:5432/campercontact
SOURCE_DB_LOCAL_SITES=postgresql://user:password@host:5432/local_sites
```

#### Customize Importers

The importer classes in `app/sync/` contain template SQL queries. You need to customize them to match your actual source database schemas:

1. Open `app/sync/park4night_importer.py`
2. Update `get_source_query()` to match your table/column names
3. Update `transform_row()` to handle your data format
4. Repeat for `campercontact_importer.py` and `local_sites_importer.py`

#### Manual Sync

```bash
cd backend/app

# Test connection to a source
python sync/sync_cli.py test-connection --source park4night

# Sync specific source (with limit for testing)
python sync/sync_cli.py sync --source park4night --limit 100

# Sync all sources
python sync/sync_cli.py sync --all
```

#### Scheduled Sync with Celery

1. **Start Redis** (required for Celery)
```bash
redis-server
```

2. **Start Celery worker**
```bash
celery -A app.sync.celery_tasks worker --loglevel=info
```

3. **Start Celery beat scheduler** (for periodic tasks)
```bash
celery -A app.sync.celery_tasks beat --loglevel=info
```

Data will sync automatically every 24 hours (configurable in `.env`).

### Index Locations for Recommendations

After syncing data, index locations in Qdrant for semantic search:

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/recommendations/index-all

# Or via Python
python -c "from app.services.recommendation_service import RecommendationService; from app.db.database import SessionLocal; db = SessionLocal(); RecommendationService(db).index_all_locations()"
```

## API Usage

### Example: Plan a Trip

```bash
# 1. Create a trip
curl -X POST http://localhost:8000/api/v1/trips/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_address": "Amsterdam, Netherlands",
    "end_address": "Berlin, Germany",
    "max_distance_km": 1000,
    "duration_days": 7
  }'

# Response: {"id": 1, ...}

# 2. Get waypoint suggestions
curl -X POST http://localhost:8000/api/v1/trips/1/suggest-waypoints \
  -H "Content-Type: application/json" \
  -d '{"num_stops": 3}'

# 3. Add a waypoint
curl -X POST http://localhost:8000/api/v1/trips/1/waypoints \
  -H "Content-Type: application/json" \
  -d '{"location_id": 42, "order": 0}'

# 4. Get trip stats
curl http://localhost:8000/api/v1/trips/1/stats

# 5. Finalize trip
curl -X POST http://localhost:8000/api/v1/trips/1/finalize \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-06-01"}'
```

### Example: Search Locations

```bash
# Search by name/description
curl -X POST http://localhost:8000/api/v1/locations/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "beach",
    "min_rating": 4.0,
    "limit": 10
  }'

# Find nearby locations
curl -X POST http://localhost:8000/api/v1/locations/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.37,
    "longitude": 4.89,
    "radius_km": 50
  }'
```

### Example: Get Recommendations

```bash
# Personalized recommendations
curl -X POST http://localhost:8000/api/v1/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "near_latitude": 52.37,
    "near_longitude": 4.89,
    "radius_km": 100,
    "limit": 20
  }'

# Interest-based recommendations
curl -X POST http://localhost:8000/api/v1/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "interests": ["nature", "hiking", "beach"],
    "near_latitude": 52.37,
    "near_longitude": 4.89,
    "radius_km": 100
  }'
```

## Development

### Database Models

Key models:
- **Location**: Campsites, parking spots, attractions, POIs
- **User**: User accounts with vehicle info
- **UserPreference**: User interests and preferences
- **Trip**: Trip plans with waypoints
- **Event**: Upcoming events and activities

### Services

- **LocationService**: Search, geocoding, geospatial queries
- **TripPlanningService**: Trip creation, waypoint management, route optimization
- **RecommendationService**: Personalized recommendations, preference learning

### Adding a New Data Source

1. Create a new importer class inheriting from `BaseImporter`
2. Implement `get_source_name()`, `get_source_query()`, and `transform_row()`
3. Add the importer to `SyncManager` in `sync_manager.py`
4. Add source database URL to `.env`

## Deployment

### Using Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# Run migrations
docker-compose exec api python -c "from app.db.database import init_db; init_db()"

# Sync data
docker-compose exec api python app/sync/sync_cli.py sync --all
```

### Production Considerations

- Use a production WSGI server (gunicorn)
- Enable HTTPS
- Set up proper authentication (JWT)
- Configure database connection pooling
- Set up monitoring (Prometheus, Grafana)
- Use environment variables for secrets
- Enable database backups
- Scale Celery workers as needed

## Roadmap

- [ ] React frontend with flow-based UI
- [ ] Event scraping system
- [ ] User authentication and authorization
- [ ] Mobile app (React Native)
- [ ] Real-time event notifications
- [ ] Weather integration
- [ ] Fuel/charging station finder
- [ ] Social features (share trips, reviews)
- [ ] Offline mode
- [ ] Route optimization with traffic data

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For questions or issues, please open a GitHub issue.
