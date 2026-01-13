"""
Deduplication Service for Tripflow

This service handles detection and merging of duplicate locations
across different data sources.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DuplicateCandidate:
    """Represents a potential duplicate pair."""
    location_id_1: int
    location_id_2: int
    distance_meters: float
    name_similarity: float
    geo_score: int
    name_score: int
    overall_score: int
    same_city: bool


class DeduplicationService:
    """Service for finding duplicate location candidates."""

    def __init__(self, db: Session):
        self.db = db

    def find_duplicates(
        self,
        distance_threshold_m: int = 100,
        name_similarity_threshold: float = 0.4,
        min_confidence: int = 50,
        batch_size: int = 1000
    ) -> List[DuplicateCandidate]:
        """
        Find duplicate location candidates across sources.

        Args:
            distance_threshold_m: Maximum distance in meters to consider as duplicate
            name_similarity_threshold: Minimum name similarity (0-1)
            min_confidence: Minimum overall confidence score (0-100)
            batch_size: Maximum number of candidates to return

        Returns:
            List of DuplicateCandidate objects
        """
        query = text("""
            SELECT * FROM tripflow.find_duplicate_candidates(
                :distance_threshold,
                :name_threshold,
                :batch_size
            )
            WHERE overall_score >= :min_confidence
        """)

        result = self.db.execute(query, {
            'distance_threshold': distance_threshold_m,
            'name_threshold': name_similarity_threshold,
            'batch_size': batch_size,
            'min_confidence': min_confidence
        })

        candidates = []
        for row in result:
            candidates.append(DuplicateCandidate(
                location_id_1=row.location_id_1,
                location_id_2=row.location_id_2,
                distance_meters=row.distance_meters,
                name_similarity=row.name_similarity,
                geo_score=row.geo_score,
                name_score=row.name_score,
                overall_score=row.overall_score,
                same_city=row.same_city
            ))

        return candidates

    def populate_duplicate_candidates_table(
        self,
        distance_threshold_m: int = 100,
        min_confidence: int = 60
    ) -> int:
        """
        Populate the duplicate_candidates table for review.

        Args:
            distance_threshold_m: Maximum distance to consider
            min_confidence: Minimum confidence score

        Returns:
            Number of candidates found
        """
        query = text("""
            SELECT tripflow.populate_duplicate_candidates(:distance, :min_confidence)
        """)

        result = self.db.execute(query, {
            'distance': distance_threshold_m,
            'min_confidence': min_confidence
        })
        self.db.commit()

        count = result.scalar()
        logger.info(f"Found {count} duplicate candidates")
        return count

    def get_pending_candidates(
        self,
        min_confidence: int = 50,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get pending duplicate candidates with location details.

        Returns list of dicts with location info for review.
        """
        query = text("""
            SELECT
                dc.id,
                dc.location_id_1,
                dc.location_id_2,
                dc.distance_meters,
                dc.overall_confidence,
                dc.geo_proximity_score,
                dc.name_similarity_score,
                dc.created_at,
                l1.name as name_1,
                l1.source as source_1,
                l1.city as city_1,
                l1.country as country_1,
                l2.name as name_2,
                l2.source as source_2,
                l2.city as city_2,
                l2.country as country_2
            FROM tripflow.duplicate_candidates dc
            JOIN tripflow.locations l1 ON dc.location_id_1 = l1.id
            JOIN tripflow.locations l2 ON dc.location_id_2 = l2.id
            WHERE dc.status = 'pending'
              AND dc.overall_confidence >= :min_confidence
            ORDER BY dc.overall_confidence DESC
            LIMIT :limit
        """)

        result = self.db.execute(query, {
            'min_confidence': min_confidence,
            'limit': limit
        })

        return [dict(row._mapping) for row in result]

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        query = text("SELECT * FROM tripflow.get_duplicate_stats()")
        result = self.db.execute(query)
        row = result.fetchone()
        return dict(row._mapping) if row else {}


class MergeService:
    """Service for merging duplicate locations."""

    # Source priority for determining canonical record
    SOURCE_PRIORITY = {
        'google_places': 100,
        'park4night': 90,
        'campercontact': 85,
        'wikidata': 80,
        'openstreetmap': 75,
        'uitinvlaanderen': 70,
        'visitwallonia': 65,
        'dagjeweg': 60,
        'manual': 50,
        'other': 40,
    }

    def __init__(self, db: Session):
        self.db = db

    def determine_canonical(self, loc1_id: int, loc2_id: int) -> Tuple[int, int]:
        """
        Determine which location should be canonical.

        Returns (canonical_id, merge_id) tuple.
        """
        from app.models import Location

        loc1 = self.db.query(Location).filter(Location.id == loc1_id).first()
        loc2 = self.db.query(Location).filter(Location.id == loc2_id).first()

        if not loc1 or not loc2:
            raise ValueError("One or both locations not found")

        score1 = self._calculate_data_quality_score(loc1)
        score2 = self._calculate_data_quality_score(loc2)

        if score1 >= score2:
            return loc1.id, loc2.id
        return loc2.id, loc1.id

    def _calculate_data_quality_score(self, loc: Any) -> int:
        """Calculate quality score for a location record."""
        score = 0

        # Source priority
        source_name = loc.source if isinstance(loc.source, str) else loc.source.value if loc.source else 'other'
        score += self.SOURCE_PRIORITY.get(source_name, 0)

        # Description quality
        if loc.description:
            desc_len = len(loc.description)
            if desc_len > 500:
                score += 30
            elif desc_len > 200:
                score += 20
            elif desc_len > 50:
                score += 10

        # Images
        if loc.images:
            img_count = len(loc.images) if isinstance(loc.images, list) else 0
            score += min(img_count * 5, 25)

        # Rating with reviews
        if loc.rating and loc.rating_count:
            score += min(loc.rating_count, 50)

        # Amenities
        if loc.amenities:
            amenity_count = len(loc.amenities) if isinstance(loc.amenities, list) else 0
            score += min(amenity_count * 2, 20)

        # Address completeness
        if loc.address:
            score += 10
        if loc.city:
            score += 5
        if loc.postal_code:
            score += 5

        return score

    def merge_locations(
        self,
        canonical_id: int,
        merge_id: int,
        merged_by: str = 'auto'
    ) -> Any:
        """
        Merge merge_id into canonical_id, preserving best data from both.

        Args:
            canonical_id: ID of the location to keep as canonical
            merge_id: ID of the location to merge in
            merged_by: Who initiated the merge ('auto' or user email)

        Returns:
            The updated canonical Location object
        """
        from app.models import Location

        canonical = self.db.query(Location).filter(Location.id == canonical_id).first()
        to_merge = self.db.query(Location).filter(Location.id == merge_id).first()

        if not canonical or not to_merge:
            raise ValueError("One or both locations not found")

        if not canonical.is_canonical:
            raise ValueError(f"Location {canonical_id} is not a canonical record")
        if not to_merge.is_canonical:
            raise ValueError(f"Location {merge_id} is already merged")

        data_contributed = {}

        # Merge description (keep longest/most complete)
        if to_merge.description:
            if not canonical.description or len(to_merge.description) > len(canonical.description):
                canonical.description = to_merge.description
                data_contributed['description'] = True

        # Merge amenities (combine unique)
        if to_merge.amenities:
            canonical_amenities = set(canonical.amenities or [])
            merge_amenities = set(to_merge.amenities if isinstance(to_merge.amenities, list) else [])
            new_amenities = merge_amenities - canonical_amenities
            if new_amenities:
                data_contributed['amenities'] = list(new_amenities)
            canonical.amenities = list(canonical_amenities | merge_amenities)

        # Merge features (combine unique)
        if to_merge.features:
            canonical_features = set(canonical.features or [])
            merge_features = set(to_merge.features if isinstance(to_merge.features, list) else [])
            canonical.features = list(canonical_features | merge_features)

        # Merge images (combine, limit to 20, avoid duplicates)
        if to_merge.images:
            canonical_images = canonical.images or []
            merge_images = to_merge.images if isinstance(to_merge.images, list) else []

            # Deduplicate by URL
            def get_url(img):
                return img.get('url') if isinstance(img, dict) else img

            existing_urls = {get_url(img) for img in canonical_images}
            new_images = [img for img in merge_images if get_url(img) not in existing_urls]
            if new_images:
                canonical.images = (canonical_images + new_images)[:20]
                data_contributed['images'] = len(new_images)

        # Merge rating (weighted average by review count)
        if to_merge.rating and to_merge.rating_count:
            if canonical.rating and canonical.rating_count:
                total_reviews = (canonical.rating_count or 0) + (to_merge.rating_count or 0)
                if total_reviews > 0:
                    weighted_rating = (
                        (canonical.rating * (canonical.rating_count or 0)) +
                        (to_merge.rating * (to_merge.rating_count or 0))
                    ) / total_reviews
                    canonical.rating = round(weighted_rating, 2)
                    canonical.rating_count = total_reviews
                    data_contributed['rating'] = True
            else:
                canonical.rating = to_merge.rating
                canonical.rating_count = to_merge.rating_count
                data_contributed['rating'] = True

        # Add review counts
        canonical.review_count = (canonical.review_count or 0) + (to_merge.review_count or 0)

        # Merge tags
        if to_merge.tags:
            canonical_tags = set(canonical.tags or [])
            merge_tags = set(to_merge.tags or [])
            canonical.tags = list(canonical_tags | merge_tags)

        # Fill in missing fields
        for field in ['phone', 'email', 'website', 'address', 'city', 'postal_code',
                      'region', 'country', 'country_code', 'altitude', 'price_info']:
            if getattr(to_merge, field, None) and not getattr(canonical, field, None):
                setattr(canonical, field, getattr(to_merge, field))
                data_contributed[field] = True

        # Update main_image_url if missing
        if not canonical.main_image_url and to_merge.main_image_url:
            canonical.main_image_url = to_merge.main_image_url
            data_contributed['main_image_url'] = True

        # Update source count
        canonical.source_count = (canonical.source_count or 1) + 1

        # Create source mapping for the merged location
        self._create_source_mapping(canonical.id, to_merge)

        # Mark merged location as non-canonical
        to_merge.is_canonical = False
        to_merge.canonical_id = canonical.id
        to_merge.merged_at = datetime.utcnow()
        to_merge.active = False  # Deactivate but don't delete

        # Create merge history record
        self._create_merge_history(canonical.id, to_merge, merged_by, data_contributed)

        # Update reviews to point to canonical
        self._reassign_reviews(to_merge.id, canonical.id)

        # Update duplicate_candidates status
        self._update_duplicate_status(canonical.id, to_merge.id)

        self.db.commit()

        logger.info(f"Merged location {merge_id} into canonical {canonical_id}")
        return canonical

    def _create_source_mapping(self, canonical_id: int, merged_loc: Any):
        """Create a source mapping record for the merged location."""
        source_name = merged_loc.source if isinstance(merged_loc.source, str) else merged_loc.source.value if merged_loc.source else 'other'

        mapping = text("""
            INSERT INTO tripflow.location_source_mappings
                (canonical_location_id, source, external_id, source_url,
                 has_description, has_images, has_rating, last_synced_at)
            VALUES
                (:canonical_id, :source, :external_id, :source_url,
                 :has_desc, :has_images, :has_rating, NOW())
            ON CONFLICT (external_id, source) DO UPDATE SET
                canonical_location_id = EXCLUDED.canonical_location_id,
                last_synced_at = NOW()
        """)

        self.db.execute(mapping, {
            'canonical_id': canonical_id,
            'source': source_name,
            'external_id': merged_loc.external_id,
            'source_url': merged_loc.website,
            'has_desc': bool(merged_loc.description),
            'has_images': bool(merged_loc.images),
            'has_rating': bool(merged_loc.rating),
        })

    def _create_merge_history(self, canonical_id: int, merged: Any,
                              merged_by: str, data_contributed: dict):
        """Record the merge in history table."""
        source_name = merged.source if isinstance(merged.source, str) else merged.source.value if merged.source else 'other'

        history = text("""
            INSERT INTO tripflow.merge_history
                (canonical_location_id, merged_location_id, merged_source,
                 merged_external_id, data_contributed, merged_by)
            VALUES (:canonical_id, :merged_id, :source, :external_id, :data, :by)
        """)

        self.db.execute(history, {
            'canonical_id': canonical_id,
            'merged_id': merged.id,
            'source': source_name,
            'external_id': merged.external_id,
            'data': json.dumps(data_contributed),
            'by': merged_by,
        })

    def _reassign_reviews(self, old_location_id: int, new_location_id: int):
        """Move reviews from merged location to canonical."""
        update = text("""
            UPDATE tripflow.reviews
            SET location_id = :new_id
            WHERE location_id = :old_id
        """)
        self.db.execute(update, {'old_id': old_location_id, 'new_id': new_location_id})

    def _update_duplicate_status(self, canonical_id: int, merged_id: int):
        """Mark duplicate candidate as merged."""
        id1, id2 = min(canonical_id, merged_id), max(canonical_id, merged_id)

        update = text("""
            UPDATE tripflow.duplicate_candidates
            SET status = 'merged', resolved_at = NOW(), resolved_by = 'auto'
            WHERE location_id_1 = :id1 AND location_id_2 = :id2
        """)
        self.db.execute(update, {'id1': id1, 'id2': id2})

    def auto_merge_high_confidence(
        self,
        min_confidence: int = 85,
        max_merges: int = 1000
    ) -> Dict[str, int]:
        """
        Automatically merge high-confidence duplicate pairs.

        Args:
            min_confidence: Minimum confidence score to auto-merge
            max_merges: Maximum number of merges to perform

        Returns:
            Dict with merge statistics
        """
        stats = {'merged': 0, 'skipped': 0, 'errors': 0}

        query = text("""
            SELECT location_id_1, location_id_2, overall_confidence
            FROM tripflow.duplicate_candidates
            WHERE status = 'pending' AND overall_confidence >= :min_confidence
            ORDER BY overall_confidence DESC
            LIMIT :max_merges
        """)

        pairs = self.db.execute(query, {
            'min_confidence': min_confidence,
            'max_merges': max_merges
        }).fetchall()

        for loc1_id, loc2_id, confidence in pairs:
            try:
                # Check if both locations are still canonical
                if not self._is_still_canonical(loc1_id) or not self._is_still_canonical(loc2_id):
                    stats['skipped'] += 1
                    continue

                canonical_id, merge_id = self.determine_canonical(loc1_id, loc2_id)
                self.merge_locations(canonical_id, merge_id, merged_by='auto')
                stats['merged'] += 1

                if stats['merged'] % 100 == 0:
                    logger.info(f"Merged {stats['merged']} locations...")

            except Exception as e:
                logger.error(f"Error merging {loc1_id} and {loc2_id}: {e}")
                stats['errors'] += 1
                self.db.rollback()

        logger.info(f"Auto-merge complete: {stats}")
        return stats

    def _is_still_canonical(self, location_id: int) -> bool:
        """Check if a location is still canonical (not merged)."""
        result = self.db.execute(text("""
            SELECT is_canonical FROM tripflow.locations WHERE id = :id
        """), {'id': location_id}).fetchone()
        return result and result[0]

    def reject_duplicate(self, candidate_id: int, rejected_by: str = 'manual') -> bool:
        """Mark a duplicate candidate as rejected (not actually duplicates)."""
        update = text("""
            UPDATE tripflow.duplicate_candidates
            SET status = 'rejected', resolved_at = NOW(), resolved_by = :by
            WHERE id = :id AND status = 'pending'
        """)
        result = self.db.execute(update, {'id': candidate_id, 'by': rejected_by})
        self.db.commit()
        return result.rowcount > 0

    def confirm_duplicate(self, candidate_id: int) -> bool:
        """Mark a duplicate candidate as confirmed (will be merged)."""
        update = text("""
            UPDATE tripflow.duplicate_candidates
            SET status = 'confirmed', resolved_at = NOW()
            WHERE id = :id AND status = 'pending'
        """)
        result = self.db.execute(update, {'id': candidate_id})
        self.db.commit()
        return result.rowcount > 0
