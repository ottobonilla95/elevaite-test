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

# Require elevaite_ingestion components (no fallbacks)
from elevaite_ingestion.parsers.pdf_parser import PdfParser
from elevaite_ingestion.parsers.docx_parser import DocxParser
from elevaite_ingestion.parsers.xlsx_parser import XlsxParser
from elevaite_ingestion.embedding_factory.openai_embedder import get_embedding
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct


from ..execution_context import ExecutionContext

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

    # Get file path from config or input data
    file_path = config.get("file_path") or input_data.get("file_path")

    if not file_path:
        return {
            "error": "No file_path provided in config or input_data",
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

        if file_extension == ".txt":
            content = await _read_text_file(file_path)
        elif file_extension == ".pdf":
            content = await _read_pdf_file(file_path)
        elif file_extension in [".docx", ".doc"]:
            content = await _read_docx_file(file_path)
        elif file_extension in [".xlsx", ".xls"]:
            content = await _read_xlsx_file(file_path)
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


async def _read_pdf_file(file_path: Path) -> str:
    """Read a PDF file using elevaite_ingestion PdfParser"""
    parser = PdfParser()
    parsed = parser.parse(str(file_path), original_filename=file_path.name)
    # Join paragraph texts into a single content string
    paragraphs = parsed.get("paragraphs", [])
    if paragraphs:
        return "\n\n".join(p.get("paragraph_text", "") for p in paragraphs)
    # Fallback: if parser returns a plain content
    return parsed.get("content", "")


async def _read_docx_file(file_path: Path) -> str:
    """Read a DOCX file using elevaite_ingestion DocxParser"""
    parser = DocxParser()
    parsed = parser.parse(str(file_path))
    return parsed.get("content", "")


async def _read_xlsx_file(file_path: Path) -> str:
    """Read an XLSX file using elevaite_ingestion XlsxParser"""
    parser = XlsxParser()
    parsed = parser.parse(str(file_path))
    return parsed.get("content", "")


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

    # Get text content from input
    content = input_data.get("content", "")
    if not content:
        return {"error": "No content provided for chunking", "success": False}

    try:
        if strategy == "sliding_window":
            chunks = _simple_chunk_text(content, chunk_size, overlap)
        elif strategy == "semantic":
            # Not wired yet to elevaite_ingestion semantic chunker in PoC
            return {"error": "semantic strategy not implemented in PoC", "success": False}
        else:
            # Treat any other value as invalid for now
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
    - model: Embedding model to use
    - batch_size: Number of chunks to process at once
    """

    config = step_config.get("config", {})
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
        embeddings = []
        # Process chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            batch_embeddings = []
            for chunk in batch:
                embedding = get_embedding(chunk)
                batch_embeddings.append(embedding)
            embeddings.extend(batch_embeddings)

        return {
            "embeddings": embeddings,
            "embedding_count": len(embeddings),
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
        if storage_type == "qdrant":
            if not QDRANT_AVAILABLE:
                return {"error": "qdrant_client is not installed", "success": False}
            result = await _store_in_qdrant(embeddings, chunks, config)
        else:
            # In-memory storage (explicit behavior)
            result = await _store_in_memory(embeddings, chunks, config)

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


async def _store_in_qdrant(embeddings: List[List[float]], chunks: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Store embeddings in Qdrant vector database"""
    host = config.get("qdrant_host", "localhost")
    port = config.get("qdrant_port", 6333)
    collection_name = config.get("collection_name", "default")

    client = qdrant_client.QdrantClient(host=host, port=port)

    # Create collection if it doesn't exist
    try:
        client.get_collection(collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
        )

    # Prepare points
    points = []
    for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk, "chunk_index": i},
        )
        points.append(point)

    # Upload points
    client.upsert(collection_name=collection_name, points=points)

    return {
        "qdrant_host": host,
        "qdrant_port": port,
        "points_uploaded": len(points),
    }


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
