import time
import threading
from pinecone import Pinecone, ServerlessSpec
from chromadb import PersistentClient
from chromadb.config import Settings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse


class PineconeClient:
    def __init__(
        self, api_key: str, cloud: str, region: str, index_name: str, dimension: int
    ):
        self.client = Pinecone(api_key=api_key)
        self.spec = ServerlessSpec(cloud=cloud, region=region)
        self.index_name = index_name
        self.dimension = dimension

        if self.index_name not in self.client.list_indexes().names():
            self.client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=self.spec,
            )
            while not self.client.describe_index(self.index_name).status["ready"]:
                time.sleep(1)

        self.index = self.client.Index(self.index_name)

    def upsert_vectors(self, vectors):
        self.index.upsert(vectors=vectors)

    def query(self, vector, top_k):
        return self.index.query(vector=vector, top_k=top_k, include_metadata=True)


class ChromaClient:
    def __init__(self, db_path: str):
        self.client = PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
        )

    def init_collection(self, collection_name: str):
        return self.client.get_or_create_collection(name=collection_name)

    def add(self, collection, documents, embeddings, metadatas, ids):
        collection.add(
            documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
        )


class QdrantClientWrapper:
    # Lock to prevent race conditions when creating collections
    _collection_locks: dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    def __init__(self, host: str, port: int):
        self.client = QdrantClient(url=host, port=port)

    def _get_collection_lock(self, collection_name: str) -> threading.Lock:
        """Get or create a lock for a specific collection."""
        with self._global_lock:
            if collection_name not in self._collection_locks:
                self._collection_locks[collection_name] = threading.Lock()
            return self._collection_locks[collection_name]

    def ensure_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,
        distance: "models.Distance" = None,
    ):
        """Check if the collection exists, create it if it doesn't.

        Thread-safe: uses locking to prevent race conditions when multiple threads
        try to create the same collection simultaneously.
        """
        lock = self._get_collection_lock(collection_name)
        with lock:
            existing_collections = self.client.get_collections().collections
            if not any(
                collection.name == collection_name
                for collection in existing_collections
            ):
                try:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=vector_size,
                            distance=distance or models.Distance.COSINE,
                        ),
                    )
                    print(
                        f"✅ Created collection '{collection_name}' with vector size {vector_size}."
                    )
                except UnexpectedResponse as e:
                    # Handle race condition: collection was created by another process
                    if e.status_code == 409:
                        print(
                            f"✅ Collection '{collection_name}' already exists (created by another process)."
                        )
                    else:
                        raise
            else:
                print(f"✅ Collection '{collection_name}' already exists.")

    def upsert_vectors(self, collection_name: str, vectors: list):
        """
        Upsert vectors into the collection.
        :param collection_name: Name of the collection
        :param vectors: List of vectors with structure:
                        [{"id": "chunk_1", "vector": [float, float, ...], "payload": {metadata_dict}}, ...]
        """
        self.client.upsert(collection_name=collection_name, points=vectors)
        print(f"✅ Upserted {len(vectors)} vectors into '{collection_name}'.")
