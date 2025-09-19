"""
Store Stage Module

This module handles the storage of embeddings into vector databases.
Supports multiple vector database backends including Qdrant, Pinecone, and ChromaDB.
"""

# Note: Avoid importing heavy pipelines on package import to prevent optional-deps errors.
# from .vectordb_pipeline import execute_vector_db_stage as execute_store_stage

__all__: list[str] = []
