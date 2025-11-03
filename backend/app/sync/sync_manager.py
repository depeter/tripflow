from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.db.database import get_source_db_connection
from .park4night_importer import Park4NightImporter
from .campercontact_importer import CamperContactImporter
from .local_sites_importer import LocalSitesImporter

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Manages data synchronization from all source databases.
    """

    def __init__(self, target_session: Session):
        self.target_session = target_session
        self.importers = {
            "park4night": Park4NightImporter,
            "campercontact": CamperContactImporter,
            "local_sites": LocalSitesImporter,
        }

    def sync_source(
        self,
        source_name: str,
        batch_size: int = 100,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Sync data from a specific source database.

        Args:
            source_name: Name of source ('park4night', 'campercontact', 'local_sites')
            batch_size: Number of records per batch
            limit: Optional limit on records to import

        Returns:
            Dictionary with sync statistics
        """
        if source_name not in self.importers:
            raise ValueError(f"Unknown source: {source_name}")

        logger.info(f"Starting sync for {source_name}...")
        start_time = datetime.utcnow()

        try:
            # Get source database connection
            source_engine = get_source_db_connection(source_name)

            # Create importer instance
            importer_class = self.importers[source_name]
            importer = importer_class(source_engine, self.target_session)

            # Perform sync
            stats = importer.sync(batch_size=batch_size, limit=limit)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"Sync for {source_name} completed in {duration:.2f}s: {stats}")

            return {
                **stats,
                "source": source_name,
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error syncing {source_name}: {e}")
            raise

    def sync_all(
        self,
        batch_size: int = 100,
        limit: Optional[int] = None,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, int]]:
        """
        Sync data from all configured source databases.

        Args:
            batch_size: Number of records per batch
            limit: Optional limit on records per source
            sources: Optional list of specific sources to sync (default: all)

        Returns:
            Dictionary mapping source names to their sync statistics
        """
        sources_to_sync = sources or list(self.importers.keys())
        results = {}

        logger.info(f"Starting sync for sources: {sources_to_sync}")

        for source_name in sources_to_sync:
            try:
                results[source_name] = self.sync_source(
                    source_name=source_name,
                    batch_size=batch_size,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"Failed to sync {source_name}: {e}")
                results[source_name] = {
                    "error": str(e),
                    "success": False,
                }

        logger.info(f"Sync completed for all sources: {results}")
        return results


def create_sync_manager(target_session: Session) -> SyncManager:
    """Factory function to create SyncManager instance"""
    return SyncManager(target_session)
