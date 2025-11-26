#!/usr/bin/env python3
"""
CLI tool for managing data synchronization.

Usage:
    python sync_cli.py sync --source park4night
    python sync_cli.py sync --all
    python sync_cli.py sync --all --limit 100  # Test with limited records
"""

import click
import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.sync.sync_manager import create_sync_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """TripFlow Data Sync CLI"""
    pass


@cli.command()
@click.option('--source', type=click.Choice(['park4night', 'campercontact', 'local_sites', 'uitinvlaanderen', 'eventbrite', 'ticketmaster']), help='Specific source to sync')
@click.option('--all', 'sync_all', is_flag=True, help='Sync all sources')
@click.option('--batch-size', default=100, help='Batch size for processing')
@click.option('--limit', type=int, help='Limit number of records (for testing)')
def sync(source, sync_all, batch_size, limit):
    """Sync data from source databases"""

    if not source and not sync_all:
        click.echo("Error: Must specify either --source or --all")
        return

    db: Session = SessionLocal()
    try:
        sync_manager = create_sync_manager(db)

        if sync_all:
            click.echo("Syncing all sources...")
            results = sync_manager.sync_all(batch_size=batch_size, limit=limit)

            click.echo("\n=== Sync Results ===")
            for source_name, stats in results.items():
                if "error" in stats:
                    click.echo(f"\n{source_name}: ERROR - {stats['error']}")
                else:
                    click.echo(f"\n{source_name}:")
                    click.echo(f"  Fetched: {stats['fetched']}")
                    click.echo(f"  Inserted: {stats['inserted']}")
                    click.echo(f"  Updated: {stats['updated']}")
                    click.echo(f"  Translations: {stats.get('translations', 0)}")
                    click.echo(f"  Errors: {stats['errors']}")
                    click.echo(f"  Duration: {stats['duration_seconds']:.2f}s")

        else:
            click.echo(f"Syncing {source}...")
            stats = sync_manager.sync_source(
                source_name=source,
                batch_size=batch_size,
                limit=limit
            )

            click.echo("\n=== Sync Results ===")
            click.echo(f"Fetched: {stats['fetched']}")
            click.echo(f"Inserted: {stats['inserted']}")
            click.echo(f"Updated: {stats['updated']}")
            click.echo(f"Translations: {stats.get('translations', 0)}")
            click.echo(f"Errors: {stats['errors']}")
            click.echo(f"Duration: {stats['duration_seconds']:.2f}s")

        click.echo("\n✅ Sync completed successfully!")

    except Exception as e:
        click.echo(f"\n❌ Sync failed: {e}")
        logger.exception("Sync failed")
        raise

    finally:
        db.close()


@cli.command()
@click.option('--source', type=click.Choice(['park4night', 'campercontact', 'local_sites', 'uitinvlaanderen', 'eventbrite', 'ticketmaster']), required=True)
def test_connection(source):
    """Test connection to a source database"""
    from app.db.database import get_source_db_connection

    click.echo(f"Testing connection to {source}...")

    try:
        engine = get_source_db_connection(source)
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()

        click.echo(f"✅ Connection to {source} successful!")

    except Exception as e:
        click.echo(f"❌ Connection failed: {e}")
        raise


if __name__ == "__main__":
    cli()
