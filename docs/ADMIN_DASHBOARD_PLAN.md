# Tripflow Admin Dashboard - Architecture Plan

## Overview
Build a comprehensive admin dashboard for managing migrations, users, and subscriptions in Tripflow.

## Phase 1: Migration Management (Current Priority)

### Backend Components

#### 1. Database Models
```python
# backend/app/models/migration.py
class MigrationRun(Base):
    - id
    - scraper_id (FK to scrapers table)
    - scraper_name
    - status (pending, running, completed, failed)
    - started_at
    - completed_at
    - duration_seconds
    - records_processed
    - records_inserted
    - records_updated
    - records_failed
    - error_message
    - log_output (TEXT)

class MigrationSchedule(Base):
    - id
    - scraper_id
    - schedule_cron (e.g., "0 2 * * *" for daily at 2am)
    - is_active
    - last_run_at
    - next_run_at
```

#### 2. Admin API Endpoints
```
POST   /api/v1/admin/migrations/run         - Trigger migration
GET    /api/v1/admin/migrations              - List all migration runs
GET    /api/v1/admin/migrations/{id}         - Get migration details
GET    /api/v1/admin/migrations/{id}/logs    - Stream logs
DELETE /api/v1/admin/migrations/{id}         - Cancel running migration

GET    /api/v1/admin/scrapers                - List configured scrapers
POST   /api/v1/admin/scrapers/{id}/schedule  - Set auto-schedule

GET    /api/v1/admin/stats/overview          - Dashboard stats
GET    /api/v1/admin/stats/locations         - Location stats by source
GET    /api/v1/admin/stats/users             - User stats
```

#### 3. Migration Runner Service
```python
# backend/app/services/migration_runner.py
class MigrationRunner:
    - run_migration(scraper_id, limit=None)
    - get_migration_status(run_id)
    - cancel_migration(run_id)
    - stream_logs(run_id)

    # Connects to scraparr DB
    # Runs migration script logic
    # Stores progress in MigrationRun table
    # Uses asyncio/threading for non-blocking
```

### Frontend Components

#### Admin Layout
```
/admin
  ├── /dashboard       - Overview stats
  ├── /migrations      - Migration management
  ├── /users           - User management (Phase 2)
  └── /settings        - System settings
```

#### Pages to Create

**1. Admin Dashboard (`/admin/dashboard`)**
- Total locations, events, users
- Recent migration runs
- System health metrics
- Data quality scores

**2. Migration Management (`/admin/migrations`)**
- Table of all migration runs (status, duration, records)
- "Run Migration" button per scraper
- Real-time log streaming during migration
- Schedule configuration

**3. Scrapers Overview (`/admin/scrapers`)**
- List of configured scrapers
- Enable/disable scrapers
- Set automatic schedules
- View last run stats

## Phase 2: User Management & Analytics

### Database Models
```python
# backend/app/models/user.py
class User(Base):
    - id
    - email (unique)
    - password_hash
    - full_name
    - is_active
    - is_admin
    - subscription_tier (free, basic, premium)
    - created_at
    - last_login_at

class UserSession(Base):
    - id
    - user_id
    - session_token
    - ip_address
    - user_agent
    - created_at
    - expires_at

# backend/app/models/analytics.py
class TripCreation(Base):
    - id
    - user_id (nullable for anonymous)
    - trip_type (multi_day, day_trip)
    - duration_days
    - num_waypoints
    - total_distance_km
    - created_at
    - session_id

class APIUsage(Base):
    - id
    - user_id (nullable)
    - endpoint
    - method
    - status_code
    - response_time_ms
    - created_at
```

### Admin Endpoints
```
# User Management
GET    /api/v1/admin/users
GET    /api/v1/admin/users/{id}
POST   /api/v1/admin/users/{id}/disable
POST   /api/v1/admin/users/{id}/change-tier

# Analytics
GET    /api/v1/admin/analytics/trips
GET    /api/v1/admin/analytics/api-usage
GET    /api/v1/admin/analytics/popular-locations
```

### Frontend Pages

**User Management (`/admin/users`)**
- Table of all users
- Filter by tier, status
- User details modal
- Change subscription tier
- View user's trip history

**Analytics (`/admin/analytics`)**
- Trip creation trends (daily/weekly/monthly)
- Popular routes/locations
- API usage graphs
- Geographic distribution of users

## Phase 3: Subscription & Billing

### Database Models
```python
# backend/app/models/subscription.py
class SubscriptionTier(Base):
    - id
    - name (free, basic, premium, enterprise)
    - price_monthly
    - max_trips_per_month
    - max_waypoints_per_trip
    - api_rate_limit
    - features (JSONB)

class Subscription(Base):
    - id
    - user_id
    - tier_id
    - status (active, cancelled, expired)
    - stripe_subscription_id
    - current_period_start
    - current_period_end
    - cancel_at_period_end

class Payment(Base):
    - id
    - user_id
    - subscription_id
    - amount
    - currency
    - status (succeeded, failed, pending)
    - stripe_payment_intent_id
    - created_at
```

### Integration
- Stripe for payments
- Webhook handlers for subscription events
- Usage tracking and enforcement
- Upgrade/downgrade flows

## Implementation Order

### Sprint 1 (Current)
1. ✅ Create migration database models
2. ✅ Build migration runner service
3. ✅ Create admin API endpoints for migrations
4. ✅ Build admin frontend layout
5. ✅ Create migration management page
6. ✅ Add real-time log streaming

### Sprint 2
1. Add user authentication (JWT)
2. Create user management backend
3. Build user management frontend
4. Add basic analytics tracking
5. Create analytics dashboard

### Sprint 3
1. Design subscription tiers
2. Integrate Stripe
3. Build subscription management
4. Add usage limits/enforcement
5. Create billing portal

## Technical Stack

**Backend**
- FastAPI (existing)
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL
- Redis (for rate limiting)
- Celery (for background jobs)

**Frontend**
- React 18 (existing)
- React Router
- Context API for state
- Chart.js for analytics
- Tailwind CSS (optional, or keep current CSS)

**External Services**
- Stripe (payments)
- SendGrid (emails)
- Sentry (error tracking)

## Security Considerations

1. **Admin Authentication**
   - Separate admin login
   - Role-based access control (RBAC)
   - Admin actions logged

2. **API Security**
   - JWT tokens
   - Rate limiting per tier
   - API key rotation

3. **Data Privacy**
   - GDPR compliance
   - User data export
   - Right to deletion

## Database Schema Updates Needed

```sql
-- Add to existing tripflow schema
CREATE TABLE migration_runs (
    id BIGSERIAL PRIMARY KEY,
    scraper_id INTEGER NOT NULL,
    scraper_name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    log_output TEXT,
    triggered_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE trip_creations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    trip_type VARCHAR(50),
    duration_days INTEGER,
    num_waypoints INTEGER,
    total_distance_km DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    endpoint VARCHAR(500),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_migration_runs_status ON migration_runs(status);
CREATE INDEX idx_migration_runs_started ON migration_runs(started_at DESC);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(subscription_tier);
CREATE INDEX idx_trip_creations_user ON trip_creations(user_id);
CREATE INDEX idx_trip_creations_created ON trip_creations(created_at DESC);
CREATE INDEX idx_api_usage_user ON api_usage(user_id);
CREATE INDEX idx_api_usage_created ON api_usage(created_at DESC);
```

## Next Steps

1. Start with migration management (highest priority)
2. Test migration runner thoroughly
3. Build admin UI for migrations
4. Add user authentication
5. Implement analytics
6. Plan subscription tiers
7. Integrate billing
