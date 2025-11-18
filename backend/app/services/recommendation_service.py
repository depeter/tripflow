from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging

from app.models import Location, User, Trip
from app.db.qdrant_client import qdrant_service
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service for generating personalized location recommendations.

    Uses:
    - Qdrant for semantic similarity search
    - Sentence transformers for text embeddings
    - User preference learning from interaction history
    """

    def __init__(self, db: Session):
        self.db = db
        self.location_service = LocationService(db)
        # Use a lightweight model for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

    def create_location_embedding(self, location: Location) -> List[float]:
        """
        Create text embedding for a location.

        Combines name, description, amenities, and tags into a single text.

        Args:
            location: Location object

        Returns:
            Embedding vector (list of floats)
        """
        # Create text representation
        text_parts = [location.name]

        if location.description:
            text_parts.append(location.description)

        if location.amenities:
            text_parts.append(f"Amenities: {', '.join(location.amenities)}")

        if location.tags:
            text_parts.append(f"Tags: {', '.join(location.tags)}")

        text_parts.append(f"Type: {location.location_type.value}")

        text = " ".join(text_parts)

        # Generate embedding
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def index_location(self, location: Location):
        """
        Index a location in Qdrant for similarity search.

        Args:
            location: Location to index
        """
        try:
            # Create embedding
            vector = self.create_location_embedding(location)

            # Prepare payload (metadata)
            payload = {
                "name": location.name,
                "location_type": location.location_type.value,
                "city": location.city,
                "country": location.country,
                "rating": location.rating,
                "price": location.price,
                "amenities": location.amenities,
                "tags": location.tags,
                "latitude": location.latitude,
                "longitude": location.longitude,
            }

            # Upsert to Qdrant
            qdrant_service.upsert_location(
                location_id=location.id,
                vector=vector,
                payload=payload,
            )

            logger.info(f"Indexed location {location.id} in Qdrant")

        except Exception as e:
            logger.error(f"Failed to index location {location.id}: {e}")
            raise

    def index_all_locations(self, batch_size: int = 100):
        """
        Index all active locations in Qdrant.

        This should be run after initial data sync or periodically.

        Args:
            batch_size: Number of locations to process at once
        """
        total = self.db.query(Location).filter(Location.active == True).count()
        logger.info(f"Indexing {total} locations in Qdrant...")

        offset = 0
        indexed = 0

        while offset < total:
            locations = (
                self.db.query(Location)
                .filter(Location.active == True)
                .offset(offset)
                .limit(batch_size)
                .all()
            )

            for location in locations:
                try:
                    self.index_location(location)
                    indexed += 1
                except Exception as e:
                    logger.error(f"Failed to index location {location.id}: {e}")

            offset += batch_size
            logger.info(f"Indexed {indexed}/{total} locations")

        logger.info(f"Indexing complete: {indexed} locations indexed")

    def get_user_preference_vector(self, user_id: int) -> Optional[List[float]]:
        """
        Get user's preference vector.

        If user has no preference vector yet, create one based on their stated preferences.

        Args:
            user_id: User ID

        Returns:
            Preference vector or None
        """
        user_pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not user_pref:
            return None

        # If preference vector exists, return it
        if user_pref.preference_vector:
            return user_pref.preference_vector

        # Otherwise, create one from stated preferences
        text_parts = []

        if user_pref.interests:
            text_parts.append(f"Interests: {', '.join(user_pref.interests)}")

        if user_pref.preferred_amenities:
            text_parts.append(f"Amenities: {', '.join(user_pref.preferred_amenities)}")

        if user_pref.preferred_activities:
            text_parts.append(f"Activities: {', '.join(user_pref.preferred_activities)}")

        if user_pref.preferred_environment:
            text_parts.append(f"Environment: {', '.join(user_pref.preferred_environment)}")

        if not text_parts:
            return None

        text = " ".join(text_parts)
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        # Save the preference vector
        user_pref.preference_vector = embedding.tolist()
        self.db.commit()

        return embedding.tolist()

    def recommend_locations(
        self,
        user_id: Optional[int] = None,
        near_latitude: Optional[float] = None,
        near_longitude: Optional[float] = None,
        radius_km: Optional[int] = None,
        interests: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized location recommendations.

        Args:
            user_id: Optional user ID for personalization
            near_latitude: Optional latitude for proximity filter
            near_longitude: Optional longitude for proximity filter
            radius_km: Search radius in km
            interests: Optional list of interest keywords
            limit: Maximum recommendations

        Returns:
            List of recommended locations with scores
        """
        # Create query vector
        query_vector = None

        if user_id:
            # Use user's preference vector
            query_vector = self.get_user_preference_vector(user_id)

        if query_vector is None and interests:
            # Create vector from interests
            text = f"Interests: {', '.join(interests)}"
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            query_vector = embedding.tolist()

        if query_vector is None:
            # No personalization available, use text search or nearby
            if near_latitude and near_longitude:
                nearby = self.location_service.find_nearby_locations(
                    latitude=near_latitude,
                    longitude=near_longitude,
                    radius_km=radius_km or 50,
                    limit=limit,
                )
                return [
                    {
                        **item,
                        "score": 1.0 / (1.0 + item["distance_km"]),  # Inverse distance score
                    }
                    for item in nearby
                ]
            else:
                # Return top-rated locations
                locations = (
                    self.db.query(Location)
                    .filter(Location.active == True)
                    .order_by(Location.rating.desc())
                    .limit(limit)
                    .all()
                )
                return [{"location": loc, "score": loc.rating or 0} for loc in locations]

        # Use Qdrant for semantic search
        try:
            # TODO: Add geo-filtering in Qdrant if coordinates provided
            results = qdrant_service.search_similar(
                query_vector=query_vector,
                limit=limit * 2,  # Get more to filter by distance if needed
            )

            # Convert to Location objects
            recommendations = []
            for result in results:
                location = self.db.query(Location).filter(
                    Location.id == result["id"]
                ).first()

                if location:
                    rec = {
                        "location": location,
                        "score": result["score"],
                    }

                    # Add distance if coordinates provided
                    if near_latitude and near_longitude:
                        from geopy.distance import geodesic
                        distance = geodesic(
                            (near_latitude, near_longitude),
                            (location.latitude, location.longitude)
                        ).kilometers

                        # Filter by radius if specified
                        if radius_km and distance > radius_km:
                            continue

                        rec["distance_km"] = distance

                    recommendations.append(rec)

                if len(recommendations) >= limit:
                    break

            return recommendations

        except Exception as e:
            logger.error(f"Recommendation search failed: {e}")
            # Fallback to nearby search
            if near_latitude and near_longitude:
                return self.location_service.find_nearby_locations(
                    latitude=near_latitude,
                    longitude=near_longitude,
                    radius_km=radius_km or 50,
                    limit=limit,
                )
            return []

    def learn_from_trip(self, trip_id: int):
        """
        Learn user preferences from a completed trip.

        Updates user's preference vector based on locations they visited and rated.

        Args:
            trip_id: Trip ID
        """
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            return

        # Extract locations from trip waypoints
        if not trip.waypoints:
            return

        liked_locations = []
        for waypoint in trip.waypoints:
            location_id = waypoint.get("location_id")
            rating = trip.user_ratings.get(str(location_id)) if trip.user_ratings else None

            if rating and rating >= 4:  # User liked this location (4-5 stars)
                location = self.db.query(Location).filter(Location.id == location_id).first()
                if location:
                    liked_locations.append(location)

        if not liked_locations:
            return

        # Create embeddings for liked locations
        embeddings = [self.create_location_embedding(loc) for loc in liked_locations]

        # Average the embeddings to update user preference
        import numpy as np
        avg_embedding = np.mean(embeddings, axis=0)

        # Get current preference
        user_pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == trip.user_id
        ).first()

        if user_pref:
            if user_pref.preference_vector:
                # Blend with existing preference (80% old, 20% new)
                current = np.array(user_pref.preference_vector)
                updated = 0.8 * current + 0.2 * avg_embedding
                user_pref.preference_vector = updated.tolist()
            else:
                user_pref.preference_vector = avg_embedding.tolist()

            self.db.commit()
            logger.info(f"Updated preference vector for user {trip.user_id} from trip {trip_id}")
