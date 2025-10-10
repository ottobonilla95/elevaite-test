from qdrant_client import QdrantClient
import logging

logger = logging.getLogger(__name__)

class QdrantConnector:
    def __init__(self, config):
        self.url = config["qdrant_url"]
        self.port = config["qdrant_port"] 
        self.collection_name = config["collection_name"]
        self.client = QdrantClient(url=f"{self.url}:{self.port}")
    
    def get_all_documents(self):
        """Get all documents from the collection with metadata"""
        try:
            # Get collection info first
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} has {collection_info.points_count} documents")
            
            # Scroll through all documents
            all_docs = []
            offset = None
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,  # Adjust batch size as needed
                    offset=offset,
                    with_payload=True,  # Get metadata
                    with_vectors=False  # We don't need vectors for tracking
                )
                
                points, next_offset = result
                all_docs.extend(points)
                
                if next_offset is None:
                    break
                offset = next_offset
            
            logger.info(f"Retrieved {len(all_docs)} documents from Qdrant")
            return all_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {e}")
            return []