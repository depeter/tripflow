"""
Migration Runner Service - Executes migrations from within Tripflow backend
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, AsyncIterator
import subprocess
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.migration import MigrationRun, ScraperMetadata
from app.core.config import settings

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Service to run scraparr-to-tripflow migrations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.migrations_path = Path(__file__).parent.parent.parent.parent / "migrations"
        self.running_processes: Dict[int, subprocess.Popen] = {}

    async def run_migration(
        self,
        scraper_id: int,
        limit: Optional[int] = None,
        triggered_by: str = "admin"
    ) -> int:
        """
        Start a migration run for a specific scraper

        Returns:
            migration_run_id: ID of the created migration run
        """
        # Get scraper metadata
        result = await self.db.execute(
            select(ScraperMetadata).where(ScraperMetadata.scraper_id == scraper_id)
        )
        scraper = result.scalar_one_or_none()

        if not scraper:
            raise ValueError(f"Scraper {scraper_id} not found in metadata. Sync scrapers first.")

        # Create migration run record
        migration_run = MigrationRun(
            scraper_id=scraper_id,
            scraper_name=scraper.name,
            scraper_schema=scraper.schema_name,
            status="pending",
            triggered_by=triggered_by,
            params={"limit": limit} if limit else {}
        )

        self.db.add(migration_run)
        await self.db.commit()
        await self.db.refresh(migration_run)

        # Run migration in background
        asyncio.create_task(self._execute_migration(migration_run.id, scraper_id, limit))

        return migration_run.id

    async def _execute_migration(
        self,
        run_id: int,
        scraper_id: int,
        limit: Optional[int] = None
    ):
        """Execute the migration script as a subprocess"""
        try:
            # Update status to running
            await self.db.execute(
                update(MigrationRun)
                .where(MigrationRun.id == run_id)
                .values(status="running", started_at=datetime.utcnow())
            )
            await self.db.commit()

            # Build command
            script_path = self.migrations_path / "migrate_all_scrapers.py"
            cmd = [
                sys.executable,
                str(script_path),
                "--scraper-id", str(scraper_id),
                "--scraparr-host", settings.SCRAPARR_DB_HOST,
                "--scraparr-port", str(settings.SCRAPARR_DB_PORT),
                "--tripflow-host", settings.DATABASE_URL.split("@")[1].split(":")[0],
                "--tripflow-port", str(5432),  # Extract from DATABASE_URL
            ]

            if limit:
                cmd.extend(["--limit", str(limit)])

            logger.info(f"Starting migration {run_id}: {' '.join(cmd)}")

            # Execute process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self.migrations_path)
            )

            self.running_processes[run_id] = process

            # Read output
            log_lines = []
            async for line in self._read_stream(process.stdout):
                log_lines.append(line)
                # Optionally parse stats from log lines
                # Could extract "records_processed", "records_inserted" etc.

            # Wait for completion
            await process.wait()

            # Parse final stats from log
            stats = self._parse_migration_stats("\n".join(log_lines))

            # Update final status
            status = "completed" if process.returncode == 0 else "failed"
            completed_at = datetime.utcnow()

            # Get migration run to calculate duration
            result = await self.db.execute(
                select(MigrationRun).where(MigrationRun.id == run_id)
            )
            run = result.scalar_one()

            duration = None
            if run.started_at:
                duration = int((completed_at - run.started_at).total_seconds())

            await self.db.execute(
                update(MigrationRun)
                .where(MigrationRun.id == run_id)
                .values(
                    status=status,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    records_processed=stats.get("records_processed", 0),
                    records_inserted=stats.get("records_inserted", 0),
                    records_updated=stats.get("records_updated", 0),
                    records_failed=stats.get("errors", 0),
                    log_output="\n".join(log_lines[-1000:]),  # Last 1000 lines
                    error_message=stats.get("error_message") if status == "failed" else None
                )
            )
            await self.db.commit()

            # Cleanup
            if run_id in self.running_processes:
                del self.running_processes[run_id]

            logger.info(f"Migration {run_id} completed with status: {status}")

        except Exception as e:
            logger.error(f"Migration {run_id} failed with exception: {e}", exc_info=True)

            await self.db.execute(
                update(MigrationRun)
                .where(MigrationRun.id == run_id)
                .values(
                    status="failed",
                    completed_at=datetime.utcnow(),
                    error_message=str(e)
                )
            )
            await self.db.commit()

            if run_id in self.running_processes:
                del self.running_processes[run_id]

    async def _read_stream(self, stream) -> AsyncIterator[str]:
        """Read lines from stdout/stderr stream"""
        while True:
            line = await stream.readline()
            if not line:
                break
            yield line.decode('utf-8').rstrip()

    def _parse_migration_stats(self, log_output: str) -> Dict[str, Any]:
        """Parse statistics from migration log output"""
        stats = {
            "records_processed": 0,
            "records_inserted": 0,
            "records_updated": 0,
            "errors": 0,
        }

        # Parse log for stats
        # Look for patterns like:
        # "Migration completed for X: {'locations_inserted': 123, 'errors': 4}"

        import re

        # Find the migration completed line
        match = re.search(
            r"Migration completed for .+: \{(.+?)\}",
            log_output
        )

        if match:
            stats_str = "{" + match.group(1) + "}"
            try:
                # Safely evaluate the dict string
                import ast
                parsed_stats = ast.literal_eval(stats_str)

                stats["records_inserted"] = parsed_stats.get("locations_inserted", 0) + parsed_stats.get("events_inserted", 0)
                stats["errors"] = parsed_stats.get("errors", 0)
                # Note: records_processed would need to be in the log output
            except:
                pass

        return stats

    async def cancel_migration(self, run_id: int) -> bool:
        """Cancel a running migration"""
        if run_id in self.running_processes:
            process = self.running_processes[run_id]
            process.terminate()

            await self.db.execute(
                update(MigrationRun)
                .where(MigrationRun.id == run_id)
                .values(
                    status="cancelled",
                    completed_at=datetime.utcnow()
                )
            )
            await self.db.commit()

            del self.running_processes[run_id]
            return True

        return False

    async def get_migration_status(self, run_id: int) -> Optional[MigrationRun]:
        """Get status of a migration run"""
        result = await self.db.execute(
            select(MigrationRun).where(MigrationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_migrations(
        self,
        limit: int = 50,
        scraper_id: Optional[int] = None,
        status: Optional[str] = None
    ):
        """List recent migration runs"""
        query = select(MigrationRun).order_by(MigrationRun.created_at.desc())

        if scraper_id:
            query = query.where(MigrationRun.scraper_id == scraper_id)

        if status:
            query = query.where(MigrationRun.status == status)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def sync_scraper_metadata(self):
        """
        Sync scraper metadata from scraparr database
        This would query the scraparr.scrapers table and update ScraperMetadata
        """
        # TODO: Implement connection to scraparr DB to fetch scraper list
        # For now, we could manually populate this or use a separate sync script
        pass
