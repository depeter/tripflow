#!/usr/bin/env python
"""
Tripflow Deduplication Migration Script

This script:
1. Applies deduplication schema changes (if not already applied)
2. Scans for duplicate location candidates
3. Auto-merges high-confidence duplicates
4. Creates source mappings for all canonical locations
5. Provides statistics on the deduplication process

Usage:
    # Dry run - just find duplicates without merging
    python run_deduplication.py --dry-run

    # Run with default settings (auto-merge confidence >= 85)
    python run_deduplication.py

    # Custom confidence threshold
    python run_deduplication.py --min-confidence 90

    # Just populate candidates table (no merging)
    python run_deduplication.py --populate-only

    # Show current stats
    python run_deduplication.py --stats-only
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.deduplication_service import DeduplicationService, MergeService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_schema_changes(engine):
    """Apply deduplication schema changes if not already applied."""
    logger.info("Checking and applying schema changes...")

    schema_file = Path(__file__).parent.parent / 'db' / 'deduplication_schema.sql'
    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    with engine.connect() as conn:
        # Check if schema changes already applied
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'tripflow'
                AND table_name = 'locations'
                AND column_name = 'is_canonical'
            )
        """))
        if result.scalar():
            logger.info("Schema changes already applied")
            return True

        # Apply schema changes
        logger.info("Applying deduplication schema...")
        sql = schema_file.read_text()
        conn.execute(text(sql))
        conn.commit()
        logger.info("Schema changes applied successfully")
        return True


def create_source_mappings_for_canonical(session):
    """
    Create source mappings for all existing canonical locations.

    This ensures that future syncs won't re-create duplicates
    for locations that haven't been merged yet.
    """
    logger.info("Creating source mappings for canonical locations...")

    result = session.execute(text("""
        INSERT INTO tripflow.location_source_mappings
            (canonical_location_id, source, external_id, source_url,
             has_description, has_images, has_rating, last_synced_at)
        SELECT
            id, source, external_id, website,
            description IS NOT NULL AND description != '',
            images IS NOT NULL AND jsonb_array_length(images) > 0,
            rating IS NOT NULL,
            COALESCE(last_synced_at, updated_at, created_at)
        FROM tripflow.locations
        WHERE is_canonical = true AND external_id IS NOT NULL
        ON CONFLICT (external_id, source) DO NOTHING
    """))
    session.commit()

    count = result.rowcount
    logger.info(f"Created {count} source mappings")
    return count


def print_stats(session):
    """Print current deduplication statistics."""
    dedup_service = DeduplicationService(session)
    stats = dedup_service.get_stats()

    print("\n" + "=" * 60)
    print("DEDUPLICATION STATISTICS")
    print("=" * 60)
    print(f"  Total locations:        {stats.get('total_locations', 0):,}")
    print(f"  Canonical locations:    {stats.get('canonical_locations', 0):,}")
    print(f"  Merged (non-canonical): {stats.get('merged_locations', 0):,}")
    print("-" * 60)
    print("  Duplicate Candidates:")
    print(f"    Pending:              {stats.get('pending_candidates', 0):,}")
    print(f"    Confirmed:            {stats.get('confirmed_candidates', 0):,}")
    print(f"    Rejected:             {stats.get('rejected_candidates', 0):,}")
    print(f"    Merged:               {stats.get('merged_candidates', 0):,}")
    print("=" * 60 + "\n")


def run_deduplication(
    dry_run: bool = False,
    min_confidence: int = 85,
    populate_only: bool = False,
    stats_only: bool = False,
    distance_threshold: int = 100
):
    """
    Main deduplication workflow.

    Args:
        dry_run: If True, only show what would be merged without doing it
        min_confidence: Minimum confidence score for auto-merge (0-100)
        populate_only: If True, only populate candidates table, don't merge
        stats_only: If True, only show statistics
        distance_threshold: Maximum distance in meters to consider duplicates
    """
    logger.info("Starting deduplication process...")
    logger.info(f"Settings: dry_run={dry_run}, min_confidence={min_confidence}, "
                f"distance_threshold={distance_threshold}m")

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Apply schema changes
        if not stats_only:
            if not apply_schema_changes(engine):
                logger.error("Failed to apply schema changes")
                return

        # Show current stats
        print_stats(session)

        if stats_only:
            return

        # Initialize services
        dedup_service = DeduplicationService(session)
        merge_service = MergeService(session)

        # Step 1: Populate duplicate candidates table
        logger.info("Step 1: Finding duplicate candidates...")
        candidate_count = dedup_service.populate_duplicate_candidates_table(
            distance_threshold_m=distance_threshold,
            min_confidence=50  # Find more candidates for review
        )
        logger.info(f"Found {candidate_count} duplicate candidates")

        if populate_only:
            print_stats(session)
            logger.info("Populate-only mode: skipping merge step")
            return

        if dry_run:
            # Show top candidates that would be merged
            logger.info(f"\nDry run: showing top candidates that would be merged (score >= {min_confidence})...")
            candidates = dedup_service.get_pending_candidates(min_confidence=min_confidence, limit=20)

            print("\n" + "-" * 80)
            print(f"TOP {len(candidates)} DUPLICATE CANDIDATES (would be auto-merged)")
            print("-" * 80)
            for c in candidates:
                print(f"\nCandidate #{c['id']} (confidence: {c['overall_confidence']}%)")
                print(f"  Location 1: [{c['source_1']}] {c['name_1']} ({c['city_1']}, {c['country_1']})")
                print(f"  Location 2: [{c['source_2']}] {c['name_2']} ({c['city_2']}, {c['country_2']})")
                print(f"  Distance: {c['distance_meters']:.1f}m")
            print("-" * 80 + "\n")
            return

        # Step 2: Auto-merge high-confidence duplicates
        logger.info(f"Step 2: Auto-merging high-confidence duplicates (>= {min_confidence}%)...")
        merge_stats = merge_service.auto_merge_high_confidence(
            min_confidence=min_confidence,
            max_merges=5000
        )

        logger.info(f"Merge results: {merge_stats['merged']} merged, "
                    f"{merge_stats['skipped']} skipped, {merge_stats['errors']} errors")

        # Step 3: Create source mappings for remaining canonical locations
        logger.info("Step 3: Creating source mappings for canonical locations...")
        mapping_count = create_source_mappings_for_canonical(session)

        # Print final stats
        print_stats(session)

        logger.info("Deduplication process complete!")

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Duplicate candidates found:  {candidate_count:,}")
        print(f"  Locations merged:            {merge_stats['merged']:,}")
        print(f"  Merges skipped:              {merge_stats['skipped']:,}")
        print(f"  Merge errors:                {merge_stats['errors']:,}")
        print(f"  Source mappings created:     {mapping_count:,}")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Error during deduplication: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Tripflow Location Deduplication Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be merged without actually merging'
    )

    parser.add_argument(
        '--min-confidence',
        type=int,
        default=85,
        help='Minimum confidence score for auto-merge (default: 85)'
    )

    parser.add_argument(
        '--distance-threshold',
        type=int,
        default=100,
        help='Maximum distance in meters to consider duplicates (default: 100)'
    )

    parser.add_argument(
        '--populate-only',
        action='store_true',
        help='Only populate candidates table, do not merge'
    )

    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show current statistics'
    )

    args = parser.parse_args()

    run_deduplication(
        dry_run=args.dry_run,
        min_confidence=args.min_confidence,
        populate_only=args.populate_only,
        stats_only=args.stats_only,
        distance_threshold=args.distance_threshold
    )


if __name__ == '__main__':
    main()
