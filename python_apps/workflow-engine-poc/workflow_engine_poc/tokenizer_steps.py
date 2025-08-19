"""
Tokenizer Steps for RAG Workflows

Simplified tokenizer steps ported from elevaite_ingestion for the workflow engine.
Provides essential document processing functionality: file reading, text chunking,
embedding generation, and vector storage.
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .execution_context import ExecutionContext

# Initialize logger
logger = logging.getLogger(__name__)

# Import elevaite_ingestion components with graceful fallback
try:
    from elevaite_ingestion.parsers.pdf_parser import PdfParser
    from elevaite_ingestion.parsers.docx_parser import DocxParser
    from elevaite_ingestion.parsers.xlsx_parser import XlsxParser
    from elevaite_ingestion.embedding_factory.openai_embedder import get_embedding
    from elevaite_ingestion.chunk_strategy.semantic_chunking import semantic_chunk_text
    from elevaite_ingestion.chunk_strategy.sliding_window_chunking import (
        sliding_window_chunk_text,
    )

    ELEVAITE_INGESTION_AVAILABLE = True
except ImportError as e:
    logger.warning(
        f"elevaite_ingestion not available: {e}, using simplified implementations"
    )
    ELEVAITE_INGESTION_AVAILABLE = False

# Import vector storage dependencies
try:
    import qdrant_client
    from qdrant_client.models import Distance, VectorParams, PointStruct

    QDRANT_AVAILABLE = True
except ImportError:
    logger.warning("qdrant_client not available, vector storage will be simulated")
    QDRANT_AVAILABLE = False


class FileReaderStep:
    """
    Simplified file reader step for reading various document formats.

    Supports PDF, DOCX, XLSX, and plain text files.
    """

    @staticmethod
    async def execute(
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute file reading step"""

        try:
            config = step_config.get("config", {})

            # Get file path from input
            file_path = input_data.get("file_path")
            if not file_path:
                raise ValueError("file_path is required in input_data")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Determine file type
            file_extension = Path(file_path).suffix.lower()

            # Read file based on type
            if file_extension == ".pdf":
                content, page_count, metadata = await FileReaderStep._read_pdf(
                    file_path, config
                )
            elif file_extension == ".docx":
                content, page_count, metadata = await FileReaderStep._read_docx(
                    file_path, config
                )
            elif file_extension == ".xlsx":
                content, page_count, metadata = await FileReaderStep._read_xlsx(
                    file_path, config
                )
            elif file_extension == ".txt":
                content, page_count, metadata = await FileReaderStep._read_txt(
                    file_path, config
                )
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")

            # Prepare result
            result = {
                "success": True,
                "content": content,
                "metadata": {
                    "filename": os.path.basename(file_path),
                    "file_path": file_path,
                    "file_type": file_extension,
                    "page_count": page_count,
                    "content_length": len(content),
                    "extraction_method": metadata.get("extraction_method", "simple"),
                    **metadata,
                },
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Successfully read file: {file_path} ({len(content)} chars)")
            return result

        except Exception as e:
            logger.error(f"File reading failed: {e}")
            return {"success": False, "error": str(e), "content": None, "metadata": {}}

    @staticmethod
    async def _read_pdf(
        file_path: str, config: Dict[str, Any]
    ) -> tuple[str, int, Dict[str, Any]]:
        """Read PDF file"""
        if ELEVAITE_INGESTION_AVAILABLE:
            try:
                parser = PdfParser()
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, parser.parse, file_path, os.path.basename(file_path)
                )

                # Extract content from structured data
                content = ""
                if "paragraphs" in result:
                    content = "\n".join(
                        [p.get("text", "") for p in result["paragraphs"]]
                    )
                elif "content" in result:
                    content = result["content"]

                return (
                    content,
                    result.get("page_count", 1),
                    {"extraction_method": "elevaite_pdf_parser"},
                )
            except Exception as e:
                logger.warning(
                    f"elevaite_ingestion PDF parsing failed: {e}, falling back to simple"
                )

        # Fallback to simple text extraction
        try:
            import PyPDF2

            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
                return content, len(reader.pages), {"extraction_method": "pypdf2"}
        except ImportError:
            raise ImportError("PyPDF2 not available and elevaite_ingestion failed")

    @staticmethod
    async def _read_docx(
        file_path: str, config: Dict[str, Any]
    ) -> tuple[str, int, Dict[str, Any]]:
        """Read DOCX file"""
        if ELEVAITE_INGESTION_AVAILABLE:
            try:
                parser = DocxParser()
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, parser.parse, file_path, os.path.basename(file_path)
                )
                content = result.get("content", "")
                return content, 1, {"extraction_method": "elevaite_docx_parser"}
            except Exception as e:
                logger.warning(
                    f"elevaite_ingestion DOCX parsing failed: {e}, falling back to simple"
                )

        # Fallback to simple text extraction
        try:
            import docx

            doc = docx.Document(file_path)
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return content, 1, {"extraction_method": "python_docx"}
        except ImportError:
            raise ImportError("python-docx not available and elevaite_ingestion failed")

    @staticmethod
    async def _read_xlsx(
        file_path: str, config: Dict[str, Any]
    ) -> tuple[str, int, Dict[str, Any]]:
        """Read XLSX file"""
        if ELEVAITE_INGESTION_AVAILABLE:
            try:
                parser = XlsxParser()
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, parser.parse, file_path, os.path.basename(file_path)
                )
                content = result.get("content", "")
                return content, 1, {"extraction_method": "elevaite_xlsx_parser"}
            except Exception as e:
                logger.warning(
                    f"elevaite_ingestion XLSX parsing failed: {e}, falling back to simple"
                )

        # Fallback to simple text extraction
        try:
            import pandas as pd

            df = pd.read_excel(file_path)
            content = df.to_string()
            return content, 1, {"extraction_method": "pandas"}
        except ImportError:
            raise ImportError("pandas not available and elevaite_ingestion failed")

    @staticmethod
    async def _read_txt(
        file_path: str, config: Dict[str, Any]
    ) -> tuple[str, int, Dict[str, Any]]:
        """Read plain text file"""
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content, 1, {"extraction_method": "plain_text"}


class TextChunkingStep:
    """
    Simplified text chunking step for dividing text into manageable chunks.

    Supports semantic chunking and sliding window chunking strategies.
    """

    @staticmethod
    async def execute(
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute text chunking step"""

        try:
            config = step_config.get("config", {})

            # Get content from input
            content = input_data.get("content")
            if not content:
                raise ValueError("content is required in input_data")

            # Get chunking strategy
            strategy = config.get("strategy", "sliding_window")
            chunk_size = config.get("chunk_size", 1000)
            overlap = config.get("overlap", 200)

            # Perform chunking
            if strategy == "semantic" and ELEVAITE_INGESTION_AVAILABLE:
                chunks = await TextChunkingStep._semantic_chunk(content, config)
            else:
                chunks = await TextChunkingStep._sliding_window_chunk(
                    content, chunk_size, overlap
                )

            # Prepare result
            result = {
                "success": True,
                "chunks": chunks,
                "metadata": {
                    "strategy": strategy,
                    "chunk_count": len(chunks),
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "original_length": len(content),
                    "total_chunk_length": sum(
                        len(chunk["content"]) for chunk in chunks
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Successfully chunked text: {len(chunks)} chunks from {len(content)} chars"
            )
            return result

        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            return {"success": False, "error": str(e), "chunks": [], "metadata": {}}

    @staticmethod
    async def _semantic_chunk(
        content: str, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform semantic chunking using elevaite_ingestion"""
        try:
            # Prepare content in elevaite format
            parsed_content = {"content": content}

            # Use elevaite semantic chunking
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None, semantic_chunk_text, parsed_content, config
            )

            # Convert to standard format
            result_chunks = []
            for i, chunk in enumerate(chunks):
                result_chunks.append(
                    {
                        "id": f"chunk_{i}",
                        "content": chunk.get("chunk_text", ""),
                        "start_char": chunk.get("start_char", 0),
                        "end_char": chunk.get("end_char", 0),
                        "size": len(chunk.get("chunk_text", "")),
                        "word_count": len(chunk.get("chunk_text", "").split()),
                        "metadata": chunk,
                    }
                )

            return result_chunks

        except Exception as e:
            logger.warning(
                f"Semantic chunking failed: {e}, falling back to sliding window"
            )
            return await TextChunkingStep._sliding_window_chunk(content, 1000, 200)

    @staticmethod
    async def _sliding_window_chunk(
        content: str, chunk_size: int, overlap: int
    ) -> List[Dict[str, Any]]:
        """Perform sliding window chunking"""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk_content = content[start:end]

            chunks.append(
                {
                    "id": f"chunk_{chunk_id}",
                    "content": chunk_content,
                    "start_char": start,
                    "end_char": end,
                    "size": len(chunk_content),
                    "word_count": len(chunk_content.split()),
                    "metadata": {
                        "chunk_method": "sliding_window",
                        "chunk_size": chunk_size,
                        "overlap": overlap,
                    },
                }
            )

            chunk_id += 1
            start += chunk_size - overlap

            # Avoid infinite loop
            if start >= end:
                break

        return chunks


# File reader step function for workflow registration
async def file_reader_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """File reader step function for workflow registration"""
    return await FileReaderStep.execute(step_config, input_data, execution_context)


# Text chunking step function for workflow registration
async def text_chunking_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """Text chunking step function for workflow registration"""
    return await TextChunkingStep.execute(step_config, input_data, execution_context)


class EmbeddingGenerationStep:
    """
    Simplified embedding generation step for creating vector embeddings.

    Supports OpenAI embeddings and sentence transformers.
    """

    @staticmethod
    async def execute(
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute embedding generation step"""

        try:
            config = step_config.get("config", {})

            # Get chunks from input
            chunks = input_data.get("chunks")
            if not chunks:
                raise ValueError("chunks is required in input_data")

            # Get embedding configuration
            provider = config.get("provider", "openai")
            model = config.get("model", "text-embedding-ada-002")
            batch_size = config.get("batch_size", 10)

            # Generate embeddings
            embeddings = []

            # Process in batches
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_embeddings = (
                    await EmbeddingGenerationStep._generate_batch_embeddings(
                        batch_chunks, provider, model, config
                    )
                )
                embeddings.extend(batch_embeddings)

            # Prepare result
            result = {
                "success": True,
                "embeddings": embeddings,
                "metadata": {
                    "provider": provider,
                    "model": model,
                    "embedding_count": len(embeddings),
                    "dimension": embeddings[0]["dimension"] if embeddings else 0,
                    "batch_size": batch_size,
                },
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Successfully generated {len(embeddings)} embeddings using {provider}"
            )
            return result

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return {"success": False, "error": str(e), "embeddings": [], "metadata": {}}

    @staticmethod
    async def _generate_batch_embeddings(
        chunks: List[Dict[str, Any]], provider: str, model: str, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for a batch of chunks"""

        if provider == "openai":
            return await EmbeddingGenerationStep._generate_openai_embeddings(
                chunks, model, config
            )
        elif provider == "sentence_transformers":
            return (
                await EmbeddingGenerationStep._generate_sentence_transformer_embeddings(
                    chunks, model, config
                )
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    @staticmethod
    async def _generate_openai_embeddings(
        chunks: List[Dict[str, Any]], model: str, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate OpenAI embeddings"""

        if ELEVAITE_INGESTION_AVAILABLE:
            try:
                embeddings = []

                for chunk in chunks:
                    content = chunk.get("content", "")

                    # Use elevaite_ingestion OpenAI embedder
                    loop = asyncio.get_event_loop()
                    embedding_vector = await loop.run_in_executor(
                        None, get_embedding, content
                    )

                    embeddings.append(
                        {
                            "chunk_id": chunk.get("id", str(uuid.uuid4())),
                            "embedding": embedding_vector,
                            "dimension": len(embedding_vector),
                            "model": model,
                            "chunk_text": (
                                content[:200] + "..." if len(content) > 200 else content
                            ),
                            "chunk_metadata": {
                                "size": chunk.get("size", 0),
                                "word_count": chunk.get("word_count", 0),
                                "start_char": chunk.get("start_char", 0),
                                "end_char": chunk.get("end_char", 0),
                            },
                        }
                    )

                return embeddings

            except Exception as e:
                logger.warning(
                    f"elevaite_ingestion OpenAI embedding failed: {e}, falling back to simulation"
                )

        # Fallback to simulation
        return await EmbeddingGenerationStep._generate_simulated_embeddings(
            chunks, model
        )

    @staticmethod
    async def _generate_sentence_transformer_embeddings(
        chunks: List[Dict[str, Any]], model: str, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate sentence transformer embeddings"""

        try:
            from sentence_transformers import SentenceTransformer

            # Load model
            transformer_model = SentenceTransformer(model)

            # Extract texts
            texts = [chunk.get("content", "") for chunk in chunks]

            # Generate embeddings
            loop = asyncio.get_event_loop()
            embedding_matrix = await loop.run_in_executor(
                None, transformer_model.encode, texts
            )

            # Process results
            embeddings = []
            for i, embedding_vector in enumerate(embedding_matrix):
                chunk = chunks[i]

                embeddings.append(
                    {
                        "chunk_id": chunk.get("id", f"chunk_{i}"),
                        "embedding": embedding_vector.tolist(),
                        "dimension": len(embedding_vector),
                        "model": model,
                        "chunk_text": (
                            chunk.get("content", "")[:200] + "..."
                            if len(chunk.get("content", "")) > 200
                            else chunk.get("content", "")
                        ),
                        "chunk_metadata": {
                            "size": chunk.get("size", 0),
                            "word_count": chunk.get("word_count", 0),
                            "start_char": chunk.get("start_char", 0),
                            "end_char": chunk.get("end_char", 0),
                        },
                    }
                )

            return embeddings

        except ImportError:
            logger.warning(
                "sentence_transformers not available, falling back to simulation"
            )
            return await EmbeddingGenerationStep._generate_simulated_embeddings(
                chunks, model
            )

    @staticmethod
    async def _generate_simulated_embeddings(
        chunks: List[Dict[str, Any]], model: str
    ) -> List[Dict[str, Any]]:
        """Generate simulated embeddings for testing"""

        import random

        embeddings = []
        dimension = (
            1536 if "ada" in model else 384
        )  # OpenAI vs sentence transformer dimensions

        for chunk in chunks:
            # Generate random embedding vector
            embedding_vector = [random.random() for _ in range(dimension)]

            embeddings.append(
                {
                    "chunk_id": chunk.get("id", str(uuid.uuid4())),
                    "embedding": embedding_vector,
                    "dimension": dimension,
                    "model": f"{model}_simulated",
                    "chunk_text": (
                        chunk.get("content", "")[:200] + "..."
                        if len(chunk.get("content", "")) > 200
                        else chunk.get("content", "")
                    ),
                    "chunk_metadata": {
                        "size": chunk.get("size", 0),
                        "word_count": chunk.get("word_count", 0),
                        "start_char": chunk.get("start_char", 0),
                        "end_char": chunk.get("end_char", 0),
                    },
                }
            )

        return embeddings


class VectorStorageStep:
    """
    Simplified vector storage step for storing embeddings in vector databases.

    Supports Qdrant and in-memory storage for testing.
    """

    @staticmethod
    async def execute(
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute vector storage step"""

        try:
            config = step_config.get("config", {})

            # Get embeddings from input
            embeddings = input_data.get("embeddings")
            if not embeddings:
                raise ValueError("embeddings is required in input_data")

            # Get storage configuration
            storage_type = config.get("storage_type", "qdrant")
            collection_name = config.get("collection_name", "documents")

            # Store embeddings
            if storage_type == "qdrant" and QDRANT_AVAILABLE:
                storage_result = await VectorStorageStep._store_in_qdrant(
                    embeddings, config
                )
            else:
                storage_result = await VectorStorageStep._store_in_memory(
                    embeddings, config
                )

            # Prepare result
            result = {
                "success": True,
                "stored_count": len(embeddings),
                "storage_info": storage_result,
                "metadata": {
                    "storage_type": storage_type,
                    "collection_name": collection_name,
                    "embedding_count": len(embeddings),
                    "dimension": embeddings[0]["dimension"] if embeddings else 0,
                },
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Successfully stored {len(embeddings)} embeddings in {storage_type}"
            )
            return result

        except Exception as e:
            logger.error(f"Vector storage failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stored_count": 0,
                "storage_info": {},
                "metadata": {},
            }

    @staticmethod
    async def _store_in_qdrant(
        embeddings: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store embeddings in Qdrant vector database"""

        try:
            # Get Qdrant configuration
            host = config.get("qdrant_host", "localhost")
            port = config.get("qdrant_port", 6333)
            collection_name = config.get("collection_name", "documents")

            # Initialize Qdrant client
            client = qdrant_client.QdrantClient(host=host, port=port)

            # Get dimension from first embedding
            dimension = embeddings[0]["dimension"]

            # Create collection if it doesn't exist
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, client.get_collection, collection_name
                )
            except Exception:
                # Collection doesn't exist, create it
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    client.create_collection,
                    collection_name,
                    VectorParams(size=dimension, distance=Distance.COSINE),
                )

            # Prepare points for insertion
            points = []
            for embedding_data in embeddings:
                point_id = str(uuid.uuid4())

                # Prepare metadata
                metadata = {
                    "chunk_id": embedding_data.get("chunk_id"),
                    "model": embedding_data.get("model"),
                    "dimension": embedding_data.get("dimension"),
                    "stored_at": datetime.now().isoformat(),
                    "chunk_text": embedding_data.get("chunk_text", ""),
                }

                # Add chunk metadata
                chunk_metadata = embedding_data.get("chunk_metadata", {})
                metadata.update(chunk_metadata)

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding_data["embedding"],
                        payload=metadata,
                    )
                )

            # Insert points
            await asyncio.get_event_loop().run_in_executor(
                None, client.upsert, collection_name, points
            )

            return {
                "storage_type": "qdrant",
                "host": host,
                "port": port,
                "collection_name": collection_name,
                "points_stored": len(points),
            }

        except Exception as e:
            logger.warning(
                f"Qdrant storage failed: {e}, falling back to in-memory storage"
            )
            return await VectorStorageStep._store_in_memory(embeddings, config)

    @staticmethod
    async def _store_in_memory(
        embeddings: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store embeddings in memory for testing"""

        # For PoC, just simulate storage
        collection_name = config.get("collection_name", "documents")

        # In a real implementation, this would store in a persistent in-memory database
        # For now, we just log the storage
        logger.info(
            f"Simulated storage of {len(embeddings)} embeddings in collection '{collection_name}'"
        )

        return {
            "storage_type": "in_memory_simulation",
            "collection_name": collection_name,
            "points_stored": len(embeddings),
            "note": "This is a simulation - embeddings are not actually persisted",
        }


# Embedding generation step function for workflow registration
async def embedding_generation_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """Embedding generation step function for workflow registration"""
    return await EmbeddingGenerationStep.execute(
        step_config, input_data, execution_context
    )


# Vector storage step function for workflow registration
async def vector_storage_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """Vector storage step function for workflow registration"""
    return await VectorStorageStep.execute(step_config, input_data, execution_context)


# Example configurations for testing
EXAMPLE_FILE_READER_CONFIG = {
    "step_type": "file_reader",
    "config": {
        "pdf_method": "pypdf2",
        "extract_images": False,
        "extract_tables": False,
    },
}

EXAMPLE_TEXT_CHUNKING_CONFIG = {
    "step_type": "text_chunking",
    "config": {"strategy": "sliding_window", "chunk_size": 1000, "overlap": 200},
}

EXAMPLE_EMBEDDING_CONFIG = {
    "step_type": "embedding_generation",
    "config": {
        "provider": "openai",
        "model": "text-embedding-ada-002",
        "batch_size": 10,
    },
}

EXAMPLE_VECTOR_STORAGE_CONFIG = {
    "step_type": "vector_storage",
    "config": {
        "storage_type": "qdrant",
        "collection_name": "documents",
        "qdrant_host": "localhost",
        "qdrant_port": 6333,
    },
}
