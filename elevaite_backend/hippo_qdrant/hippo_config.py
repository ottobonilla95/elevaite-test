"""
HippoRAG Step 1: Configuration and Setup
Handles all configuration, environment setup, and shared utilities.
"""

import os
import openai
import pandas as pd
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HippoRAGConfig:
    """Configuration class for HippoRAG pipeline"""
    
    def __init__(self):
        load_dotenv()
        
        # Qdrant Configuration
        self.QDRANT_HOST = "http://3.101.65.253"
        self.QDRANT_PORT = 5333
        
        # OpenAI Configuration
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.VECTOR_SIZE = 1536
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        
        # Initialize clients
        self.openai_client = openai.OpenAI(api_key=self.api_key)
        self.qdrant_client = QdrantClient(url=self.QDRANT_HOST, port=self.QDRANT_PORT)
        
        # Collection names
        self.PASSAGES_COLLECTION = "hipporag_passages"
        self.ENTITIES_COLLECTION = "hipporag_entities"
        self.FACTS_COLLECTION = "hipporag_facts"
        
        # File paths
        self.TRIPLET_CSV = "/Users/dheeraj/Desktop/vscode_check/elevaite_ingestion/stage/retrieval_stage/triplets_deduped.csv"
        self.GRAPH_FILE = "knowledge_graph.pkl"
        self.PASSAGES_FILE = "passages.json"
        
        logger.info("HippoRAG configuration initialized successfully")
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * self.VECTOR_SIZE
    
    def setup_qdrant_collections(self):
        """Initialize Qdrant collections with proper configuration"""
        collections = [
            self.PASSAGES_COLLECTION,
            self.ENTITIES_COLLECTION,
            self.FACTS_COLLECTION
        ]
        
        for collection_name in collections:
            try:
                # Check if collection exists
                collections_info = self.qdrant_client.get_collections()
                existing_collections = [col.name for col in collections_info.collections]
                
                if collection_name not in existing_collections:
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.VECTOR_SIZE,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {collection_name}")
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    
            except Exception as e:
                logger.error(f"Error setting up collection {collection_name}: {e}")
                raise
    
    def load_triplets(self) -> pd.DataFrame:
        """Load triplets from CSV file"""
        try:
            df = pd.read_csv(self.TRIPLET_CSV)
            logger.info(f"Loaded {len(df)} triplets from {self.TRIPLET_CSV}")
            return df
        except Exception as e:
            logger.error(f"Error loading triplets: {e}")
            raise

