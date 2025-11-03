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

    # Source databases for import/sync
    SOURCE_DB_PARK4NIGHT: Optional[str] = None
    SOURCE_DB_CAMPERCONTACT: Optional[str] = None
    SOURCE_DB_LOCAL_SITES: Optional[str] = None

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

    # Authentication (for future use)
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

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
