"""
Store Stage Module

This module handles the storage of embeddings into vector databases.
Supports multiple vector database backends including Qdrant, Pinecone, and ChromaDB.
"""

from .store_pipeline import execute_store_stage

__all__ = ["execute_store_stage"]
