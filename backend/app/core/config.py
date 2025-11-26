from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TripFlow"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database - Main TripFlow database
    DATABASE_URL: str = "postgresql://tripflow:tripflow@localhost:5432/tripflow"

    # Scraparr database for migrations
    SCRAPARR_DB_HOST: str = "localhost"
    SCRAPARR_DB_PORT: int = 5434
    SCRAPARR_DB_NAME: str = "scraparr"
    SCRAPARR_DB_USER: str = "scraparr"
    SCRAPARR_DB_PASSWORD: str = "scraparr"

    # Source databases for import/sync (all from Scraparr)
    SOURCE_DB_PARK4NIGHT: Optional[str] = None
    SOURCE_DB_CAMPERCONTACT: Optional[str] = None
    SOURCE_DB_LOCAL_SITES: Optional[str] = None
    SOURCE_DB_UITINVLAANDEREN: Optional[str] = None
    SOURCE_DB_EVENTBRITE: Optional[str] = None
    SOURCE_DB_TICKETMASTER: Optional[str] = None

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "locations"

    # Redis for Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Sync configuration
    SYNC_ENABLED: bool = True
    SYNC_SCHEDULE_HOURS: int = 24  # Sync every 24 hours

    # Authentication
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_use-at-least-32-random-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days

    # OAuth - Google
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/api/v1/auth/google/callback"

    # OAuth - Microsoft
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8001/api/v1/auth/microsoft/callback"
    MICROSOFT_TENANT_ID: str = "common"

    # Stripe Payment
    STRIPE_SECRET_KEY: str = "sk_test_CHANGE_THIS"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_CHANGE_THIS"
    STRIPE_WEBHOOK_SECRET: str = "whsec_CHANGE_THIS"
    STRIPE_PREMIUM_PRICE_ID: str = "price_CHANGE_THIS"  # Stripe Price ID for Premium tier

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Geocoding
    NOMINATIM_USER_AGENT: str = "tripflow-app"

    # Recommendations
    MAX_RECOMMENDATIONS: int = 20
    DEFAULT_SEARCH_RADIUS_KM: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
