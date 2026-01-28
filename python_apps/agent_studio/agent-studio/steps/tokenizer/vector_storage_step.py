"""
Vector Storage Step for Tokenizer Workflows

Stores vector embeddings in vector databases with metadata for RAG purposes:
- Qdrant (recommended for production)
- Chroma (local development)
- Pinecone (cloud-based)
- Custom vector database endpoints

Supports batch insertion, automatic collection creation, and metadata management.
Highly configurable through API parameters.
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime
import time

from steps.base_deterministic_step import (
    StepConfig,
    StepResult,
    StepStatus,
    StepValidationResult,
    DataOutputStep,
)
from services.workflow_execution_context import DeterministicStepType
from fastapi_logger import ElevaiteLogger


class VectorStorageStepConfig(StepConfig):
    """Configuration for Vector Storage Step"""
    step_type: DeterministicStepType = DeterministicStepType.DATA_OUTPUT


class VectorStorageStep(DataOutputStep):
    """
    Stores vector embeddings in vector databases for RAG retrieval.
    
    Supported vector databases:
    - qdrant: Qdrant vector database (recommended)
    - chroma: ChromaDB for local development  
    - pinecone: Pinecone cloud vector database
    - custom: Custom vector database API
    
    Configuration options:
    - vector_db: Database type (qdrant, chroma, pinecone, custom)
    - collection_name: Name of the collection/index to store vectors
    - host: Database host (default: localhost for local DBs)
    - port: Database port (default: 6333 for Qdrant, 8000 for Chroma)
    - api_key: API key for cloud services (Pinecone)
    - dimension: Vector dimension (will auto-detect if not provided)
    - distance_metric: Distance metric (cosine, euclidean, dot_product)
    - create_collection: Whether to create collection if it doesn't exist
    - batch_size: Batch size for insertions (default: 100)
    - upsert: Whether to upsert (update if exists) or insert only
    - metadata_config: Additional metadata configuration
    - index_config: Index configuration (HNSW parameters, etc.)
    """
    
    def __init__(self, config: VectorStorageStepConfig):
        super().__init__(config)
        self.logger = ElevaiteLogger()
        self._client = None
        self._collection_exists = False
    
    def validate_config(self) -> StepValidationResult:
        """Validate vector storage configuration"""
        result = StepValidationResult()
        
        config = self.config.config
        
        # Validate vector database type
        vector_db = config.get("vector_db", "qdrant")
        valid_dbs = ["qdrant", "chroma", "pinecone", "custom"]
        if vector_db not in valid_dbs:
            result.errors.append(f"'vector_db' must be one of: {valid_dbs}")
        
        # Validate collection name
        collection_name = config.get("collection_name")
        if not collection_name:
            result.errors.append("'collection_name' is required")
        elif not isinstance(collection_name, str) or len(collection_name.strip()) == 0:
            result.errors.append("'collection_name' must be a non-empty string")
        
        # Validate connection parameters
        if vector_db in ["qdrant", "chroma"]:
            host = config.get("host", "localhost")
            port = config.get("port", 6333 if vector_db == "qdrant" else 8000)
            if not isinstance(port, int) or port <= 0:
                result.errors.append("'port' must be a positive integer")
        
        # Validate Pinecone API key
        if vector_db == "pinecone":
            api_key = config.get("api_key")
            if not api_key:
                result.errors.append("'api_key' is required for Pinecone")
        
        # Validate distance metric
        distance_metric = config.get("distance_metric", "cosine")
        valid_metrics = ["cosine", "euclidean", "dot_product", "manhattan"]
        if distance_metric not in valid_metrics:
            result.errors.append(f"'distance_metric' must be one of: {valid_metrics}")
        
        # Validate batch size
        batch_size = config.get("batch_size", 100)
        if not isinstance(batch_size, int) or batch_size <= 0:
            result.errors.append("'batch_size' must be a positive integer")
        
        # Validate dimension (if specified)
        dimension = config.get("dimension")
        if dimension is not None:
            if not isinstance(dimension, int) or dimension <= 0:
                result.errors.append("'dimension' must be a positive integer")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        """Required inputs for vector storage step"""
        return ["embeddings"]  # Expects embeddings from embedding generation step
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Output schema for vector storage step"""
        return {
            "type": "object",
            "properties": {
                "storage_result": {
                    "type": "object",
                    "properties": {
                        "collection_name": {"type": "string"},
                        "vector_db": {"type": "string"},
                        "stored_vectors": {"type": "integer"},
                        "failed_vectors": {"type": "integer"},
                        "total_batches": {"type": "integer"},
                        "storage_ids": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "collection_created": {"type": "boolean"},
                        "dimension": {"type": "integer"},
                        "distance_metric": {"type": "string"},
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "processing_time_seconds": {"type": "number"},
                        "average_time_per_vector": {"type": "number"},
                        "vectors_per_second": {"type": "number"},
                        "collection_info": {"type": "object"},
                        "processed_at": {"type": "string"},
                    }
                },
                "success": {"type": "boolean"},
                "error": {"type": "string"},
            },
            "required": ["storage_result", "metadata", "success"]
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute vector storage step"""
        try:
            config = self.config.config
            
            # Get embeddings from input
            embeddings = input_data.get("embeddings", [])
            if not embeddings:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="No embeddings provided for vector storage"
                )
            
            start_time = time.time()
            vector_db = config.get("vector_db", "qdrant")
            collection_name = config.get("collection_name")
            
            self.logger.info(f"Storing {len(embeddings)} vectors in {vector_db} collection '{collection_name}'")
            
            # Initialize database client
            await self._initialize_client(config)
            
            # Auto-detect dimension from first embedding
            dimension = len(embeddings[0]["embedding"]) if embeddings else config.get("dimension")
            if not dimension:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="Could not determine vector dimension"
                )
            
            # Create collection if needed
            collection_created = False
            if config.get("create_collection", True):
                collection_created = await self._ensure_collection_exists(collection_name, dimension, config)
            
            # Process embeddings in batches
            batch_size = config.get("batch_size", 100)
            storage_ids = []
            stored_vectors = 0
            failed_vectors = 0
            total_batches = (len(embeddings) + batch_size - 1) // batch_size
            
            self._update_progress(
                total_items=len(embeddings),
                total_batches=total_batches,
                processed_items=0
            )
            
            for batch_idx in range(0, len(embeddings), batch_size):
                batch_embeddings = embeddings[batch_idx:batch_idx + batch_size]
                
                self._update_progress(
                    current_batch=batch_idx // batch_size + 1,
                    current_operation=f"Storing batch {batch_idx // batch_size + 1}/{total_batches}"
                )
                
                try:
                    batch_ids = await self._store_batch(batch_embeddings, collection_name, config)
                    storage_ids.extend(batch_ids)
                    stored_vectors += len(batch_embeddings)
                    
                    self._update_progress(
                        processed_items=batch_idx + len(batch_embeddings),
                        successful_items=stored_vectors
                    )
                    
                except Exception as e:
                    self.logger.error(f"Failed to store batch {batch_idx // batch_size + 1}: {e}")
                    failed_vectors += len(batch_embeddings)
                    
                    self._update_progress(
                        processed_items=batch_idx + len(batch_embeddings),
                        failed_items=failed_vectors
                    )
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            avg_time_per_vector = processing_time / len(embeddings) if embeddings else 0
            vectors_per_second = len(embeddings) / processing_time if processing_time > 0 else 0
            
            # Get collection info
            collection_info = await self._get_collection_info(collection_name, config)
            
            result_data = {
                "storage_result": {
                    "collection_name": collection_name,
                    "vector_db": vector_db,
                    "stored_vectors": stored_vectors,
                    "failed_vectors": failed_vectors,
                    "total_batches": total_batches,
                    "storage_ids": storage_ids,
                    "collection_created": collection_created,
                    "dimension": dimension,
                    "distance_metric": config.get("distance_metric", "cosine"),
                },
                "metadata": {
                    "processing_time_seconds": round(processing_time, 2),
                    "average_time_per_vector": round(avg_time_per_vector, 4),
                    "vectors_per_second": round(vectors_per_second, 2),
                    "collection_info": collection_info,
                    "processed_at": datetime.now().isoformat(),
                },
                "success": True,
            }
            
            self.logger.info(f"Stored {stored_vectors} vectors, {failed_vectors} failed, {vectors_per_second:.1f} vectors/sec")
            
            return StepResult(
                status=StepStatus.COMPLETED,
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Error storing vectors: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Vector storage error: {str(e)}"
            )
    
    async def _initialize_client(self, config: Dict[str, Any]):
        """Initialize vector database client"""
        vector_db = config.get("vector_db", "qdrant")
        
        if vector_db == "qdrant":
            await self._initialize_qdrant(config)
        elif vector_db == "chroma":
            await self._initialize_chroma(config)
        elif vector_db == "pinecone":
            await self._initialize_pinecone(config)
        elif vector_db == "custom":
            await self._initialize_custom(config)
    
    async def _initialize_qdrant(self, config: Dict[str, Any]):
        """Initialize Qdrant client"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            host = config.get("host", "localhost")
            port = config.get("port", 6333)
            api_key = config.get("api_key")
            
            # Support for Qdrant Cloud
            if api_key:
                self._client = QdrantClient(
                    host=host,
                    port=port,
                    api_key=api_key,
                    https=config.get("https", True)
                )
            else:
                self._client = QdrantClient(host=host, port=port)
            
            # Store models for later use
            self._qdrant_models = models
            
            self.logger.info(f"Connected to Qdrant at {host}:{port}")
            
        except ImportError:
            raise Exception("Qdrant client not installed. Install with: pip install qdrant-client")
    
    async def _initialize_chroma(self, config: Dict[str, Any]):
        """Initialize ChromaDB client"""
        try:
            import chromadb
            
            host = config.get("host", "localhost")
            port = config.get("port", 8000)
            
            # For ChromaDB, can be HTTP client or persistent client
            if config.get("persistent_path"):
                self._client = chromadb.PersistentClient(path=config.get("persistent_path"))
            else:
                self._client = chromadb.HttpClient(host=host, port=port)
            
            self.logger.info("Connected to ChromaDB")
            
        except ImportError:
            raise Exception("ChromaDB not installed. Install with: pip install chromadb")
    
    async def _initialize_pinecone(self, config: Dict[str, Any]):
        """Initialize Pinecone client"""
        try:
            import pinecone
            
            api_key = config.get("api_key")
            environment = config.get("environment", "us-west1-gcp")
            
            pinecone.init(api_key=api_key, environment=environment)
            self._client = pinecone
            
            self.logger.info(f"Connected to Pinecone in {environment}")
            
        except ImportError:
            raise Exception("Pinecone client not installed. Install with: pip install pinecone-client")
    
    async def _initialize_custom(self, config: Dict[str, Any]):
        """Initialize custom API client"""
        import httpx
        
        base_url = config.get("base_url")
        if not base_url:
            raise Exception("base_url is required for custom vector database")
        
        headers = config.get("headers", {})
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config.get('api_key')}"
        
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=config.get("timeout", 30)
        )
    
    async def _ensure_collection_exists(self, collection_name: str, dimension: int, config: Dict[str, Any]) -> bool:
        """Ensure collection exists, create if it doesn't"""
        vector_db = config.get("vector_db", "qdrant")
        
        if vector_db == "qdrant":
            return await self._ensure_qdrant_collection(collection_name, dimension, config)
        elif vector_db == "chroma":
            return await self._ensure_chroma_collection(collection_name, dimension, config)
        elif vector_db == "pinecone":
            return await self._ensure_pinecone_index(collection_name, dimension, config)
        elif vector_db == "custom":
            return await self._ensure_custom_collection(collection_name, dimension, config)
        
        return False
    
    async def _ensure_qdrant_collection(self, collection_name: str, dimension: int, config: Dict[str, Any]) -> bool:
        """Ensure Qdrant collection exists"""
        try:
            # Check if collection exists
            collections = self._client.get_collections()
            existing_names = [col.name for col in collections.collections]
            
            if collection_name in existing_names:
                self._collection_exists = True
                return False
            
            # Create collection
            distance_metric = config.get("distance_metric", "cosine")
            distance_map = {
                "cosine": self._qdrant_models.Distance.COSINE,
                "euclidean": self._qdrant_models.Distance.EUCLID,
                "dot_product": self._qdrant_models.Distance.DOT,
                "manhattan": self._qdrant_models.Distance.MANHATTAN,
            }
            
            # HNSW index configuration
            hnsw_config = config.get("hnsw_config", {})
            index_config = self._qdrant_models.VectorParams(
                size=dimension,
                distance=distance_map.get(distance_metric, self._qdrant_models.Distance.COSINE),
                hnsw_config=self._qdrant_models.HnswConfigDiff(
                    m=hnsw_config.get("m", 16),
                    ef_construct=hnsw_config.get("ef_construct", 100),
                )
            )
            
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=index_config,
            )
            
            self._collection_exists = True
            self.logger.info(f"Created Qdrant collection: {collection_name} (dim: {dimension})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating Qdrant collection: {e}")
            raise
    
    async def _ensure_chroma_collection(self, collection_name: str, dimension: int, config: Dict[str, Any]) -> bool:
        """Ensure ChromaDB collection exists"""
        try:
            # Check if collection exists
            try:
                self._collection = self._client.get_collection(name=collection_name)
                return False
            except:
                # Collection doesn't exist, create it
                distance_metric = config.get("distance_metric", "cosine")
                metadata = {"dimension": dimension, "distance_metric": distance_metric}
                
                self._collection = self._client.create_collection(
                    name=collection_name,
                    metadata=metadata
                )
                
                self.logger.info(f"Created ChromaDB collection: {collection_name} (dim: {dimension})")
                return True
                
        except Exception as e:
            self.logger.error(f"Error creating ChromaDB collection: {e}")
            raise
    
    async def _ensure_pinecone_index(self, collection_name: str, dimension: int, config: Dict[str, Any]) -> bool:
        """Ensure Pinecone index exists"""
        try:
            # Check if index exists
            if collection_name in self._client.list_indexes():
                self._index = self._client.Index(collection_name)
                return False
            
            # Create index
            distance_metric = config.get("distance_metric", "cosine")
            metric_map = {
                "cosine": "cosine",
                "euclidean": "euclidean",
                "dot_product": "dotproduct"
            }
            
            self._client.create_index(
                name=collection_name,
                dimension=dimension,
                metric=metric_map.get(distance_metric, "cosine"),
                pods=config.get("pods", 1),
                replicas=config.get("replicas", 1),
            )
            
            self._index = self._client.Index(collection_name)
            self.logger.info(f"Created Pinecone index: {collection_name} (dim: {dimension})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating Pinecone index: {e}")
            raise
    
    async def _ensure_custom_collection(self, collection_name: str, dimension: int, config: Dict[str, Any]) -> bool:
        """Ensure custom collection exists"""
        try:
            # Check if collection exists
            response = await self._client.get(f"/collections/{collection_name}")
            if response.status_code == 200:
                return False
            
            # Create collection
            create_data = {
                "name": collection_name,
                "dimension": dimension,
                "distance_metric": config.get("distance_metric", "cosine"),
                "index_config": config.get("index_config", {})
            }
            
            response = await self._client.post("/collections", json=create_data)
            response.raise_for_status()
            
            self.logger.info(f"Created custom collection: {collection_name} (dim: {dimension})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating custom collection: {e}")
            raise
    
    async def _store_batch(self, batch_embeddings: List[Dict[str, Any]], collection_name: str, config: Dict[str, Any]) -> List[str]:
        """Store a batch of embeddings"""
        vector_db = config.get("vector_db", "qdrant")
        
        if vector_db == "qdrant":
            return await self._store_batch_qdrant(batch_embeddings, collection_name, config)
        elif vector_db == "chroma":
            return await self._store_batch_chroma(batch_embeddings, collection_name, config)
        elif vector_db == "pinecone":
            return await self._store_batch_pinecone(batch_embeddings, collection_name, config)
        elif vector_db == "custom":
            return await self._store_batch_custom(batch_embeddings, collection_name, config)
        
        return []
    
    async def _store_batch_qdrant(self, batch_embeddings: List[Dict[str, Any]], collection_name: str, config: Dict[str, Any]) -> List[str]:
        """Store batch in Qdrant"""
        points = []
        ids = []
        
        for embedding_data in batch_embeddings:
            # Generate ID
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            # Prepare payload (metadata)
            payload = {
                "chunk_id": embedding_data.get("chunk_id"),
                "chunk_text": embedding_data.get("chunk_text", ""),
                "model": embedding_data.get("model"),
                "dimension": embedding_data.get("dimension"),
                "stored_at": datetime.now().isoformat(),
            }
            
            # Add chunk metadata
            chunk_metadata = embedding_data.get("chunk_metadata", {})
            payload.update(chunk_metadata)
            
            # Add any additional metadata
            additional_metadata = config.get("additional_metadata", {})
            payload.update(additional_metadata)
            
            points.append(self._qdrant_models.PointStruct(
                id=point_id,
                vector=embedding_data["embedding"],
                payload=payload
            ))
        
        # Upsert points
        operation_result = self._client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        if operation_result.status != self._qdrant_models.UpdateStatus.COMPLETED:
            raise Exception(f"Qdrant upsert failed: {operation_result}")
        
        return ids
    
    async def _store_batch_chroma(self, batch_embeddings: List[Dict[str, Any]], collection_name: str, config: Dict[str, Any]) -> List[str]:
        """Store batch in ChromaDB"""
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for embedding_data in batch_embeddings:
            # Generate ID
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            embeddings.append(embedding_data["embedding"])
            documents.append(embedding_data.get("chunk_text", ""))
            
            # Prepare metadata
            metadata = {
                "chunk_id": embedding_data.get("chunk_id"),
                "model": embedding_data.get("model"),
                "dimension": embedding_data.get("dimension"),
                "stored_at": datetime.now().isoformat(),
            }
            
            # Add chunk metadata
            chunk_metadata = embedding_data.get("chunk_metadata", {})
            metadata.update(chunk_metadata)
            
            # Add any additional metadata
            additional_metadata = config.get("additional_metadata", {})
            metadata.update(additional_metadata)
            
            metadatas.append(metadata)
        
        # Add to collection
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        return ids
    
    async def _store_batch_pinecone(self, batch_embeddings: List[Dict[str, Any]], collection_name: str, config: Dict[str, Any]) -> List[str]:
        """Store batch in Pinecone"""
        vectors = []
        ids = []
        
        for embedding_data in batch_embeddings:
            # Generate ID
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            # Prepare metadata
            metadata = {
                "chunk_id": embedding_data.get("chunk_id"),
                "chunk_text": embedding_data.get("chunk_text", "")[:1000],  # Pinecone metadata size limit
                "model": embedding_data.get("model"),
                "dimension": embedding_data.get("dimension"),
                "stored_at": datetime.now().isoformat(),
            }
            
            # Add chunk metadata (with size limits)
            chunk_metadata = embedding_data.get("chunk_metadata", {})
            for key, value in chunk_metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
            
            vectors.append((point_id, embedding_data["embedding"], metadata))
        
        # Upsert vectors
        self._index.upsert(vectors=vectors)
        
        return ids
    
    async def _store_batch_custom(self, batch_embeddings: List[Dict[str, Any]], collection_name: str, config: Dict[str, Any]) -> List[str]:
        """Store batch in custom vector database"""
        vectors = []
        ids = []
        
        for embedding_data in batch_embeddings:
            # Generate ID
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            
            # Prepare vector data
            vector_data = {
                "id": point_id,
                "vector": embedding_data["embedding"],
                "metadata": {
                    "chunk_id": embedding_data.get("chunk_id"),
                    "chunk_text": embedding_data.get("chunk_text", ""),
                    "model": embedding_data.get("model"),
                    "dimension": embedding_data.get("dimension"),
                    "stored_at": datetime.now().isoformat(),
                }
            }
            
            # Add chunk metadata
            chunk_metadata = embedding_data.get("chunk_metadata", {})
            vector_data["metadata"].update(chunk_metadata)
            
            vectors.append(vector_data)
        
        # Store via API
        store_data = {
            "collection": collection_name,
            "vectors": vectors,
            "upsert": config.get("upsert", True)
        }
        
        response = await self._client.post("/vectors", json=store_data)
        response.raise_for_status()
        
        return ids
    
    async def _get_collection_info(self, collection_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get collection information"""
        vector_db = config.get("vector_db", "qdrant")
        
        try:
            if vector_db == "qdrant":
                info = self._client.get_collection(collection_name)
                return {
                    "vectors_count": info.vectors_count,
                    "points_count": info.points_count,
                    "status": info.status.name if hasattr(info.status, 'name') else str(info.status)
                }
            elif vector_db == "chroma":
                return {
                    "count": self._collection.count()
                }
            elif vector_db == "pinecone":
                stats = self._index.describe_index_stats()
                return {
                    "vectors_count": stats.total_vector_count,
                    "dimension": stats.dimension
                }
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Could not get collection info: {e}")
            return {}


# Factory function for easy creation
def create_vector_storage_step(config: Dict[str, Any]) -> VectorStorageStep:
    """Create a VectorStorageStep with given configuration"""
    step_config = VectorStorageStepConfig(
        step_name=config.get("step_name", "Vector Storage"),
        config=config
    )
    return VectorStorageStep(step_config)