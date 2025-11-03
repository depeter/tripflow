from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing Qdrant vector database operations"""

    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    def init_collection(self, vector_size: int = 384):
        """
        Initialize Qdrant collection for locations.

        Args:
            vector_size: Size of the embedding vectors (default 384 for sentence-transformers)
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")

        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise

    def upsert_location(
        self,
        location_id: int,
        vector: List[float],
        payload: Dict[str, Any]
    ):
        """
        Insert or update a location in Qdrant.

        Args:
            location_id: ID of the location
            vector: Embedding vector for the location
            payload: Metadata about the location
        """
        try:
            point = PointStruct(
                id=location_id,
                vector=vector,
                payload=payload,
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
        except Exception as e:
            logger.error(f"Error upserting location {location_id} to Qdrant: {e}")
            raise

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar locations using vector similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional filters to apply

        Returns:
            List of similar locations with scores
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filters,
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching in Qdrant: {e}")
            raise

    def delete_location(self, location_id: int):
        """Delete a location from Qdrant"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[location_id],
            )
        except Exception as e:
            logger.error(f"Error deleting location {location_id} from Qdrant: {e}")
            raise


# Global instance
qdrant_service = QdrantService()
