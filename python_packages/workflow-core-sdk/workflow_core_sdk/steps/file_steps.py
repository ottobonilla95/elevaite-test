"""
File Processing Steps

Steps for file operations, text processing, document parsing,
embedding generation, and vector storage for RAG workflows.
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Try to import elevaite_ingestion components (optional)
try:
    from elevaite_ingestion.stage.parse_stage.parse_pipeline import (
        process_file as ingestion_parse_file,
    )
    from elevaite_ingestion.config.chunker_config import CHUNKER_CONFIG

    INGESTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"elevaite_ingestion not available: {e}")
    INGESTION_AVAILABLE = False
    ingestion_parse_file = None
    CHUNKER_CONFIG = {}

import importlib
import inspect
import tempfile


from workflow_core_sdk.execution_context import ExecutionContext

# Initialize logger
logger = logging.getLogger(__name__)

QDRANT_AVAILABLE = True


async def file_reader_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    File reader step that extracts text content from various file formats.

    Config options:
    - file_path: Path to the file to read (can be from input_data)
    - supported_formats: List of supported file formats
    """

    config = step_config.get("config", {})

    # Get file path from config or input data; if missing, try trigger attachments (multipart path)
    file_path = config.get("file_path") or input_data.get("file_path")

    if not file_path:
        # Look for first attachment saved by the router under trigger_raw
        try:
            raw = execution_context.step_io_data.get("trigger_raw", {})
            atts = raw.get("attachments") or raw.get("data", {}).get("attachments") or []
            if isinstance(atts, list) and atts:
                first = atts[0] if isinstance(atts[0], dict) else None
                candidate = first.get("path") if first else None
                if candidate:
                    file_path = candidate
        except Exception:
            pass

    if not file_path:
        return {
            "error": "No file_path provided in config/input_data and no trigger attachment found",
            "success": False,
        }

    file_path = Path(file_path)

    if not file_path.exists():
        return {
            "error": f"File not found: {file_path}",
            "success": False,
        }

    try:
        # Determine file type and parse accordingly
        file_extension = file_path.suffix.lower()

        parsed_data = None
        if file_extension == ".txt":
            content = await _read_text_file(file_path)
            parsed_data = {"content": content, "filename": file_path.name}
        elif file_extension in [".pdf", ".docx", ".doc", ".xlsx", ".xls"]:
            # Delegate to elevaite_ingestion parse pipeline; it reads package config for tool selection
            md_path, structured = ingestion_parse_file(str(file_path), tempfile.gettempdir(), file_path.name)
            parsed_data = structured or {}
            if "paragraphs" in parsed_data:
                content = "\n\n".join(p.get("paragraph_text", "") for p in parsed_data.get("paragraphs", []))
            else:
                content = parsed_data.get("content", "")
        else:
            return {
                "file_path": str(file_path),
                "error": f"Unsupported file extension: {file_extension}",
                "success": False,
            }

        return {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_extension": file_extension,
            "content": content,
            "parsed": parsed_data,
            "content_length": len(content),
            "processed_at": datetime.now().isoformat(),
            "success": True,
        }

    except Exception as e:
        return {
            "file_path": str(file_path),
            "error": str(e),
            "success": False,
        }


async def _read_text_file(file_path: Path) -> str:
    """Read a plain text file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


async def text_chunking_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Text chunking step that divides text into manageable, semantically meaningful chunks.

    Config options:
    - strategy: "sliding_window" or "semantic"
    - chunk_size: Size of each chunk (for sliding window)
    - overlap: Overlap between chunks (for sliding window)
    """

    config = step_config.get("config", {})
    strategy = config.get("strategy", "sliding_window")
    chunk_size = config.get("chunk_size", 1000)
    overlap = config.get("overlap", 100)

    # Prefer parsed data from prior step if present; fallback to raw content
    parsed = input_data.get("parsed")
    content = input_data.get("content", "")
    if not parsed and not content:
        return {"error": "No input provided for chunking", "success": False}

    try:
        if strategy == "sliding_window":
            chunks = _simple_chunk_text(content, chunk_size, overlap)
        elif strategy == "semantic_chunking":
            # Use elevaite_ingestion semantic chunker (async)
            module_name = "elevaite_ingestion.chunk_strategy.custom_chunking.semantic_chunk_v1"
            chunk_module = importlib.import_module(module_name)
            chunk_func = getattr(chunk_module, "chunk_text")
            params = {
                **CHUNKER_CONFIG["available_chunkers"]["semantic_chunking"]["settings"],
            }
            parsed_input = parsed or {"content": content, "filename": input_data.get("file_name", "unknown")}
            # The semantic chunker expects PDF-style paragraphs; it may return empty for plain content
            if inspect.iscoroutinefunction(chunk_func):
                chunk_objs = await chunk_func(parsed_input, params)
            else:
                chunk_objs = chunk_func(parsed_input, params)
            # Normalize to list[str]
            chunks = [c.get("chunk_text", "") for c in (chunk_objs or []) if isinstance(c, dict)]
        else:
            return {"error": f"Unsupported chunking strategy: {strategy}", "success": False}

        return {
            "chunks": chunks,
            "chunk_count": len(chunks),
            "strategy": strategy,
            "chunk_size": chunk_size,
            "overlap": overlap if strategy == "sliding_window" else 0,
            "original_content_length": len(content),
            "processed_at": datetime.now().isoformat(),
            "success": True,
        }

    except Exception as e:
        return {"error": str(e), "success": False}


def _simple_chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Simple text chunking fallback"""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

        if start >= len(text):
            break

    return chunks


async def embedding_generation_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Embedding generation step that creates vector embeddings for text chunks.

    Config options:
    - provider: Embedding provider (e.g., "openai"), defaults to "openai"
    - model: Embedding model to use (e.g., "text-embedding-3-small")
    - batch_size: Number of chunks to process at once (reserved for future batching)
    """

    config = step_config.get("config", {})
    provider = config.get("provider", "openai")
    model = config.get("model", "text-embedding-ada-002")
    batch_size = config.get("batch_size", 10)

    # Get chunks from input
    chunks = input_data.get("chunks", [])
    if not chunks:
        return {
            "error": "No chunks provided for embedding generation",
            "success": False,
        }

    try:
        from elevaite_ingestion.stage.embed_stage.embed_local import embed_texts

        embeddings = embed_texts(chunks, provider=provider, model=model)

        return {
            "embeddings": embeddings,
            "embedding_count": len(embeddings),
            "provider": provider,
            "model": model,
            "batch_size": batch_size,
            "processed_at": datetime.now().isoformat(),
            "success": True,
        }

    except Exception as e:
        return {"error": str(e), "success": False}


async def vector_storage_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Vector storage step that stores embeddings in a vector database.

    Config options:
    - storage_type: "qdrant" or "in_memory"
    - collection_name: Name of the collection
    - qdrant_host: Qdrant server host (if using qdrant)
    - qdrant_port: Qdrant server port (if using qdrant)
    """

    config = step_config.get("config", {})
    storage_type = config.get("storage_type", "in_memory")
    collection_name = config.get("collection_name", "default")

    # Get embeddings and chunks from input
    embeddings = input_data.get("embeddings", [])
    chunks = input_data.get("chunks", [])

    if not embeddings or not chunks:
        return {
            "error": "No embeddings or chunks provided for storage",
            "success": False,
        }

    if len(embeddings) != len(chunks):
        return {
            "error": "Mismatch between number of embeddings and chunks",
            "success": False,
        }

    try:
        if storage_type == "in_memory":
            result = await _store_in_memory(embeddings, chunks, config)
        elif storage_type in {"qdrant", "chroma", "pinecone"}:
            from elevaite_ingestion.stage.vectorstore_stage.local_store import store_embeddings

            filename = input_data.get("file_name") or input_data.get("filename") or "unknown"

            if storage_type == "qdrant":
                settings = {
                    "host": config.get("qdrant_host", "http://localhost"),
                    "port": config.get("qdrant_port", 6333),
                    "collection_name": collection_name,
                }
            elif storage_type == "chroma":
                settings = {
                    "db_path": config.get("db_path", config.get("chroma_db_path", "data/chroma_db")),
                    "collection_name": collection_name,
                }
            else:  # pinecone
                settings = {
                    "api_key": config.get("api_key") or os.getenv("PINECONE_API_KEY", ""),
                    "cloud": config.get("cloud", "aws"),
                    "region": config.get("region", "us-west-1"),
                    "index_name": config.get("index_name", collection_name),
                    "dimension": config.get("dimension", len(embeddings[0]) if embeddings else 1536),
                }

            result_info = store_embeddings(storage_type, settings, embeddings, chunks, filename)
            result = {**result_info}
        else:
            return {"error": f"Unsupported storage_type: {storage_type}", "success": False}

        return {
            **result,
            "storage_type": storage_type,
            "collection_name": collection_name,
            "stored_count": len(embeddings),
            "processed_at": datetime.now().isoformat(),
            "success": True,
        }

    except Exception as e:
        return {"error": str(e), "success": False}


async def _store_in_memory(embeddings: List[List[float]], chunks: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Store embeddings in memory (simulation)"""
    # This is just a simulation - in a real implementation,
    # you might store in a local database or file

    storage_data = []
    for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
        storage_data.append(
            {
                "id": str(uuid.uuid4()),
                "embedding": embedding,
                "text": chunk,
                "chunk_index": i,
            }
        )

    return {
        "storage_location": "in_memory",
        "stored_items": len(storage_data),
    }


async def vector_search_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Vector search step that queries a vector database (Qdrant) with a user query
    and returns the top matching chunks.

    Config options:
    - db_type: Currently only "qdrant" supported
    - collection_name: Qdrant collection to search
    - qdrant_host: Qdrant server host (default http://localhost)
    - qdrant_port: Qdrant server port (default 6333)
    - top_k: Number of results to return (default 5)
    - provider: Embedding provider (default "openai")
    - model: Embedding model (default "text-embedding-ada-002")
    - query: Optional static query if not present in trigger/input
    """

    config = step_config.get("config", {})
    db_type = config.get("db_type", "qdrant")
    collection_name = config.get("collection_name", "default")
    top_k = int(config.get("top_k", 5))
    provider = config.get("provider", "openai")
    model = config.get("model", "text-embedding-ada-002")

    # Determine the query: prefer explicit input, then trigger current_message, then config
    query: Optional[str] = None
    if isinstance(input_data, dict):
        query = input_data.get("query") or input_data.get("current_message")
    if not query:
        try:
            trig = execution_context.step_io_data.get("trigger") or execution_context.step_io_data.get("trigger_raw")
            if isinstance(trig, dict):
                query = trig.get("current_message")
        except Exception:
            pass
    if not query:
        query = config.get("query")

    if not query or not isinstance(query, str):
        return {"error": "No query provided for vector search", "success": False}

    if db_type != "qdrant":
        return {"error": f"Unsupported db_type: {db_type}", "success": False}

    try:
        # Embed the query text
        from elevaite_ingestion.stage.embed_stage.embed_local import embed_texts

        qvecs = embed_texts([query], provider=provider, model=model)
        if not qvecs:
            return {"error": "Embedding failed for query", "success": False}
        qvec = qvecs[0]

        # Search Qdrant
        from qdrant_client import QdrantClient

        client = QdrantClient(
            url=config.get("qdrant_host", "http://localhost"),
            port=int(config.get("qdrant_port", 6333)),
        )
        results = client.search(
            collection_name=collection_name,
            query_vector=qvec,
            limit=top_k,
            with_payload=True,
        )

        retrieved: List[Dict[str, Any]] = []
        for m in results or []:
            payload = getattr(m, "payload", {}) or {}
            text = payload.get("text") or payload.get("chunk_text") or ""
            retrieved.append(
                {
                    "text": text,
                    "score": float(getattr(m, "score", 0.0) or 0.0),
                    "chunk_index": payload.get("chunk_index"),
                    "filename": payload.get("filename"),
                }
            )

        return {
            "retrieved_chunks": retrieved,
            "retrieved_count": len(retrieved),
            "collection_name": collection_name,
            "query": query,
            "success": True,
        }

    except Exception as e:
        return {"error": str(e), "success": False}
