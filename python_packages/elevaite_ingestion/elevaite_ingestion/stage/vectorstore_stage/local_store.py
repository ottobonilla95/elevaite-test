from typing import List, Dict, Any

# Thin, local wrapper to store embeddings in supported vector DBs
# without involving S3. Uses the SDK clients.

from elevaite_ingestion.vectorstore.db import (
    PineconeClient,
    ChromaClient,
    QdrantClientWrapper,
)


def store_embeddings(
    db_type: str,
    settings: Dict[str, Any],
    embeddings: List[List[float]],
    chunks: List[str],
    filename: str | None = None,
) -> Dict[str, Any]:
    if not embeddings or not chunks:
        raise ValueError("No embeddings or chunks provided")
    if len(embeddings) != len(chunks):
        raise ValueError("Mismatch between number of embeddings and chunks")

    if db_type == "qdrant":
        host = settings.get("host", "http://localhost")
        port = int(settings.get("port", 6333))
        collection_name = settings.get("collection_name", "default")
        client = QdrantClientWrapper(host=host, port=port)
        vector_size = len(embeddings[0])
        client.ensure_collection(collection_name, vector_size=vector_size)
        vectors = []
        for i, (vec, text) in enumerate(zip(embeddings, chunks)):
            vectors.append(
                {
                    # Qdrant requires integer or UUID point IDs; use integers for batch safety
                    "id": i,
                    "vector": vec,
                    "payload": {"text": text, "chunk_index": i, "filename": filename or "unknown"},
                }
            )
        client.upsert_vectors(collection_name=collection_name, vectors=vectors)
        return {"db": "qdrant", "collection_name": collection_name, "upserted": len(vectors)}

    if db_type == "chroma":
        db_path = settings.get("db_path", "data/chroma_db")
        collection_name = settings.get("collection_name", "default")
        client = ChromaClient(db_path=db_path)
        collection = client.init_collection(collection_name)
        ids = [f"{filename or 'doc'}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"chunk_index": i, "filename": filename or "unknown"} for i in range(len(chunks))]
        client.add(collection, documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)
        return {"db": "chroma", "collection_name": collection_name, "upserted": len(ids)}

    if db_type == "pinecone":
        client = PineconeClient(
            api_key=settings["api_key"],
            cloud=settings["cloud"],
            region=settings["region"],
            index_name=settings["index_name"],
            dimension=int(settings.get("dimension", len(embeddings[0]))),
        )
        vectors = []
        for i, (vec, text) in enumerate(zip(embeddings, chunks)):
            vectors.append(
                {
                    "id": f"{filename or 'doc'}_chunk_{i}",
                    "values": vec,
                    "metadata": {"text": text, "chunk_index": i, "filename": filename or "unknown"},
                }
            )
        client.upsert_vectors(vectors)
        return {"db": "pinecone", "index_name": settings["index_name"], "upserted": len(vectors)}

    raise ValueError(f"Unsupported vector database type: {db_type}")
