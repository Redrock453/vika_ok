"""Qdrant Vector Database Manager with improved error handling."""
import hashlib
import logging
from typing import Optional, List, Dict, Any

import numpy as np

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger("qdrant_manager")


class QdrantManager:
    """Manager for Qdrant Vector Database with better error handling."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "vika_knowledge",
        vector_size: int = 512,
        distance: Distance = Distance.COSINE,
    ):
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant-client is not installed")

        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def create_collection(self, vector_size: Optional[int] = None) -> bool:
        """Create or recreate the collection."""
        size = vector_size or self.vector_size
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=size, distance=self.distance),
            )
            logger.info(f"Collection '{self.collection_name}' created (dim={size})")
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    def ensure_collection(self) -> bool:
        """Ensure collection exists, create if not."""
        try:
            collections = self.client.get_collections()
            exists = any(
                c.name == self.collection_name for c in collections.collections
            )
            if not exists:
                return self.create_collection()
            return True
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
            return False

    def upsert_documents(
        self,
        chunks: List[str],
        embeddings: List[np.ndarray | List[float]],
        source_name: str = "unknown",
    ) -> bool:
        """Upsert document chunks and their embeddings into Qdrant."""
        if len(chunks) != len(embeddings):
            logger.error(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch")
            return False

        try:
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Generate deterministic ID from source and index
                point_id = int(hashlib.sha256(f"{source_name}_{i}".encode()).hexdigest()[:16], 16)

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                        payload={
                            "text": chunk,
                            "source": source_name,
                            "chunk_index": i,
                        },
                    )
                )

            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"Upserted {len(points)} points from '{source_name}' to '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error upserting documents: {e}")
            return False

    def search(
        self, query_vector: np.ndarray | List[float], limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for the most similar chunks in Qdrant."""
        try:
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist() if isinstance(query_vector, np.ndarray) else query_vector,
                limit=limit,
            )

            results = []
            for hit in search_result.points:
                if hit.payload:
                    results.append(
                        {
                            "text": hit.payload.get("text", ""),
                            "source": hit.payload.get("source", "unknown"),
                            "score": hit.score,
                            "chunk_index": hit.payload.get("chunk_index", 0),
                        }
                    )
            return results
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

    def delete_by_source(self, source_name: str) -> bool:
        """Delete all points from a specific source."""
        try:
            # First, get all points from this source
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
            )
            points_to_delete = [p.id for p in result[0] if p.payload.get("source") == source_name]

            if points_to_delete:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector={"ids": points_to_delete},
                )
                logger.info(f"Deleted {len(points_to_delete)} points from '{source_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting by source: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vector_size": info.config.params.vectors.size,
                "points_count": info.points_count,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}


if __name__ == "__main__":
    # Test the manager
    if not QDRANT_AVAILABLE:
        print("qdrant-client not installed")
        exit(1)

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=6333)
    args = parser.parse_args()

    manager = QdrantManager(host=args.host, port=args.port)

    # Create collection
    manager.ensure_collection()

    # Test vector (512 dimensions for distiluse-base-multilingual-cased-v2)
    test_vector = np.random.rand(512).astype(np.float32)

    # Upsert dummy data
    manager.upsert_documents(
        chunks=["Vika is an AI assistant.", "She works for БАС subdivision."],
        embeddings=[test_vector, test_vector],
        source_name="test_doc",
    )

    # Search
    results = manager.search(test_vector, limit=1)
    if results:
        print(f"Search successful! Top match: {results[0]['text']} (Score: {results[0]['score']:.4f})")
    else:
        print("Search failed or returned no results.")
