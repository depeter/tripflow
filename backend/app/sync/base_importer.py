from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseImporter(ABC):
    """
    Abstract base class for importing data from source databases.

    Each source database (park4night, campercontact, local_sites) should
    have its own importer class that inherits from this.
    """

    def __init__(self, source_engine, target_session: Session):
        """
        Initialize importer.

        Args:
            source_engine: SQLAlchemy engine for the source database
            target_session: SQLAlchemy session for the target (TripFlow) database
        """
        self.source_engine = source_engine
        self.target_session = target_session
        self.source_name = self.get_source_name()

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the source name (e.g., 'park4night', 'campercontact')"""
        pass

    @abstractmethod
    def get_source_query(self) -> str:
        """
        Return SQL query to fetch data from source database.

        This query should select all relevant fields from the source database.
        The query result should be convertible to Location model.
        """
        pass

    @abstractmethod
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a row from source database to TripFlow Location format.

        Args:
            row: Dictionary representing a row from source database

        Returns:
            Dictionary with fields matching Location model
        """
        pass

    def get_translations(self, row: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract multilingual translations from a source row (optional).

        Args:
            row: Dictionary representing a row from source database

        Returns:
            Dictionary mapping language codes to descriptions, e.g.:
            {
                'en': 'English description',
                'nl': 'Dutch description',
                'fr': 'French description'
            }
            Returns None if no translations available.
        """
        return None

    def fetch_source_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch data from source database.

        Args:
            limit: Optional limit on number of rows to fetch

        Returns:
            List of dictionaries representing source rows
        """
        query = self.get_source_query()
        if limit:
            query += f" LIMIT {limit}"

        logger.info(f"Fetching data from {self.source_name}...")

        with self.source_engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]

        logger.info(f"Fetched {len(rows)} rows from {self.source_name}")
        return rows

    def import_data(self, batch_size: int = 100, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Import data from source database to TripFlow database.

        Args:
            batch_size: Number of records to process in each batch
            limit: Optional limit on total records to import

        Returns:
            Dictionary with import statistics
        """
        from app.models import Location, LocationSource, LocationTranslation

        stats = {
            "fetched": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "translations": 0,
        }

        try:
            # Fetch source data
            source_rows = self.fetch_source_data(limit=limit)
            stats["fetched"] = len(source_rows)

            # Process in batches
            for i in range(0, len(source_rows), batch_size):
                batch = source_rows[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} rows)")

                for row in batch:
                    try:
                        # Transform row to Location format
                        location_data = self.transform_row(row)

                        # Check if location already exists
                        existing = self.target_session.query(Location).filter(
                            Location.external_id == location_data.get("external_id"),
                            Location.source == LocationSource[self.source_name.upper()]
                        ).first()

                        if existing:
                            # Update existing location
                            for key, value in location_data.items():
                                setattr(existing, key, value)
                            existing.last_synced_at = datetime.utcnow()
                            location_obj = existing
                            stats["updated"] += 1
                        else:
                            # Insert new location
                            location_data["source"] = LocationSource[self.source_name.upper()]
                            location_data["last_synced_at"] = datetime.utcnow()
                            location_obj = Location(**location_data)
                            self.target_session.add(location_obj)
                            stats["inserted"] += 1

                        # Flush to get location ID for translations
                        self.target_session.flush()

                        # Handle translations if available
                        translations = self.get_translations(row)
                        if translations and location_obj.id:
                            # Delete existing translations for this location
                            self.target_session.query(LocationTranslation).filter(
                                LocationTranslation.location_id == location_obj.id
                            ).delete()

                            # Insert new translations
                            for lang_code, description in translations.items():
                                if description and description.strip():
                                    translation = LocationTranslation(
                                        location_id=location_obj.id,
                                        language_code=lang_code,
                                        description=description.strip()
                                    )
                                    self.target_session.add(translation)
                                    stats["translations"] += 1

                    except Exception as e:
                        logger.error(f"Error processing row: {e}")
                        stats["errors"] += 1
                        continue

                # Commit batch
                self.target_session.commit()
                logger.info(f"Batch committed: {stats['inserted']} inserted, {stats['updated']} updated")

        except Exception as e:
            logger.error(f"Error during import from {self.source_name}: {e}")
            self.target_session.rollback()
            raise

        logger.info(f"Import from {self.source_name} complete: {stats}")
        return stats

    def sync(self, batch_size: int = 100, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Alias for import_data - performs sync operation.

        This method can be called by Celery tasks for scheduled syncing.
        """
        return self.import_data(batch_size=batch_size, limit=limit)
