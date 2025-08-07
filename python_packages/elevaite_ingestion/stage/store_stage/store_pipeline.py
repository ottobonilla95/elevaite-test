import os
import sys
import json
import glob
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from config.vector_db_config import VECTOR_DB_CONFIG
from utils.logger import get_logger
from db import QdrantClientWrapper
from qdrant_client.http import models
import uuid

load_dotenv()
logger = get_logger(__name__)


def load_embeddings_from_local(embeddings_dir: str) -> List[Dict[str, Any]]:
    """
    Load embeddings from local JSON files.

    Args:
        embeddings_dir: Directory containing embedding JSON files

    Returns:
        List of embedding data dictionaries
    """
    embeddings = []

    if not os.path.exists(embeddings_dir):
        logger.error(f"❌ Embeddings directory not found: {embeddings_dir}")
        return embeddings

    # Look for JSON files in the embeddings directory
    json_files = glob.glob(os.path.join(embeddings_dir, "*.json"))

    if not json_files:
        logger.warning(f"⚠️ No JSON files found in {embeddings_dir}")
        return embeddings

    logger.info(f"📁 Found {len(json_files)} embedding files to process")

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                embedding_data = json.load(f)

            # Validate required fields
            required_fields = ["chunk_id", "chunk_text", "chunk_embedding"]
            if all(field in embedding_data for field in required_fields):
                embeddings.append(embedding_data)
                logger.debug(f"✅ Loaded embedding from {os.path.basename(json_file)}")
            else:
                logger.warning(f"⚠️ Missing required fields in {json_file}")

        except Exception as e:
            logger.error(f"❌ Failed to load {json_file}: {str(e)}")

    logger.info(f"📊 Successfully loaded {len(embeddings)} embeddings")
    return embeddings


def load_embeddings_from_s3(
    bucket_name: str, prefix: str = "embeddings_output/"
) -> List[Dict[str, Any]]:
    """
    Load embeddings from S3 (for compatibility with existing S3-based pipeline).

    Args:
        bucket_name: S3 bucket name
        prefix: S3 prefix for embedding files

    Returns:
        List of embedding data dictionaries
    """
    try:
        from utils.s3_utils import list_s3_files, fetch_json_from_s3

        embeddings = []
        embedding_files = list_s3_files(bucket_name, prefix)

        if not embedding_files:
            logger.warning(f"⚠️ No embedding files found in s3://{bucket_name}/{prefix}")
            return embeddings

        logger.info(f"📁 Found {len(embedding_files)} embedding files in S3")

        for file_key in embedding_files:
            try:
                embedding_data = fetch_json_from_s3(bucket_name, file_key)
                if embedding_data and "chunk_embedding" in embedding_data:
                    embeddings.append(embedding_data)
                    logger.debug(
                        f"✅ Loaded embedding from s3://{bucket_name}/{file_key}"
                    )
                else:
                    logger.warning(f"⚠️ Invalid embedding data in {file_key}")
            except Exception as e:
                logger.error(f"❌ Failed to load {file_key}: {str(e)}")

        logger.info(f"📊 Successfully loaded {len(embeddings)} embeddings from S3")
        return embeddings

    except ImportError:
        logger.error("❌ S3 utilities not available. Cannot load from S3.")
        return []


def prepare_vectors_for_qdrant(
    embeddings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert embedding data to Qdrant point format.

    Args:
        embeddings: List of embedding dictionaries

    Returns:
        List of Qdrant points
    """
    points = []

    for embedding in embeddings:
        try:
            # Generate unique point ID
            point_id = str(uuid.uuid4())

            # Extract vector
            vector = embedding.get("chunk_embedding", [])
            if not vector or not isinstance(vector, list):
                logger.warning(
                    f"⚠️ Invalid vector for chunk {embedding.get('chunk_id', 'unknown')}"
                )
                continue

            # Prepare metadata payload
            payload = {
                "chunk_id": embedding.get("chunk_id", ""),
                "chunk_text": embedding.get("chunk_text", ""),
                "filename": embedding.get("filename", ""),
                "page_range": embedding.get("page_range", ""),
                "contextual_header": embedding.get("contextual_header", ""),
                "start_paragraph": embedding.get("start_paragraph", ""),
                "end_paragraph": embedding.get("end_paragraph", ""),
            }

            # Create Qdrant point
            point = {"id": point_id, "vector": vector, "payload": payload}

            points.append(point)

        except Exception as e:
            logger.error(
                f"❌ Failed to prepare vector for chunk {embedding.get('chunk_id', 'unknown')}: {str(e)}"
            )

    logger.info(f"🔢 Prepared {len(points)} vectors for storage")
    return points


def store_vectors_to_qdrant(
    points: List[Dict[str, Any]], collection_name: str
) -> Dict[str, Any]:
    """
    Store vectors in Qdrant vector database.

    Args:
        points: List of Qdrant points
        collection_name: Name of the collection

    Returns:
        Storage result dictionary
    """
    try:
        # Get Qdrant configuration
        qdrant_config = VECTOR_DB_CONFIG.get("qdrant", {})
        host = qdrant_config.get("host", "localhost")
        port = qdrant_config.get("port", 6333)

        logger.info(f"🔗 Connecting to Qdrant at {host}:{port}")

        # Initialize Qdrant client
        qdrant_client = QdrantClientWrapper(host=host, port=port)

        # Ensure collection exists
        vector_size = len(points[0]["vector"]) if points else 1536
        qdrant_client.ensure_collection(collection_name, vector_size=vector_size)

        # Store vectors in batches
        batch_size = 100
        total_stored = 0
        failed_count = 0

        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            try:
                qdrant_client.upsert_vectors(collection_name, batch)
                total_stored += len(batch)
                logger.info(
                    f"✅ Stored batch {i//batch_size + 1}: {len(batch)} vectors"
                )
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"❌ Failed to store batch {i//batch_size + 1}: {str(e)}")

        result = {
            "total_vectors": len(points),
            "stored_vectors": total_stored,
            "failed_vectors": failed_count,
            "collection_name": collection_name,
            "vector_size": vector_size,
            "status": "Success" if total_stored > 0 else "Failed",
        }

        logger.info(f"📊 Storage complete: {total_stored}/{len(points)} vectors stored")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to store vectors to Qdrant: {str(e)}")
        return {
            "total_vectors": len(points),
            "stored_vectors": 0,
            "failed_vectors": len(points),
            "error": str(e),
            "status": "Failed",
        }


def execute_store_stage() -> Dict[str, Any]:
    """
    Execute the store stage of the ingestion pipeline.

    Returns:
        Stage execution status and results
    """
    logger.info("🚀 Starting vector storage stage...")

    # Determine storage mode (local or S3) based on configuration
    try:
        # Try to load configuration from environment or config file
        config_file = os.getenv("CONFIG_FILE")
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        else:
            # Fallback to default config
            from config.load_config import load_config

            config = load_config()

        # Determine if we're using local or S3 storage
        loading_config = config.get("loading", {})
        default_source = loading_config.get("default_source", "local")

        embeddings = []

        if default_source == "local":
            # Load from local directory
            local_config = loading_config.get("sources", {}).get("local", {})
            output_dir = local_config.get("output_directory", "")

            # Look for embeddings in the output directory or a subdirectory
            embeddings_dir = os.path.join(output_dir, "embeddings_output")
            if not os.path.exists(embeddings_dir):
                # Try alternative locations
                embeddings_dir = os.path.join(
                    os.path.dirname(output_dir), "embeddings_output"
                )
                if not os.path.exists(embeddings_dir):
                    embeddings_dir = output_dir

            embeddings = load_embeddings_from_local(embeddings_dir)

        else:
            # Load from S3
            from config.aws_config import AWS_CONFIG

            bucket_name = AWS_CONFIG.get("intermediate_bucket", "")
            embeddings = load_embeddings_from_s3(bucket_name)

        if not embeddings:
            return {
                "STAGE_5: STORE_VECTORS": {
                    "INPUT": f"Embeddings from {default_source}",
                    "OUTPUT": "None - no embeddings found",
                    "TOTAL_EMBEDDINGS": 0,
                    "STORED_VECTORS": 0,
                    "STATUS": "Failed",
                    "ERROR": "No embeddings found to store",
                }
            }

        # Prepare vectors for Qdrant
        points = prepare_vectors_for_qdrant(embeddings)

        if not points:
            return {
                "STAGE_5: STORE_VECTORS": {
                    "INPUT": f"{len(embeddings)} embeddings",
                    "OUTPUT": "None - no valid vectors",
                    "TOTAL_EMBEDDINGS": len(embeddings),
                    "STORED_VECTORS": 0,
                    "STATUS": "Failed",
                    "ERROR": "No valid vectors prepared",
                }
            }

        # Get collection name from config
        vector_db_config = config.get("vector_db", {})
        qdrant_config = vector_db_config.get("databases", {}).get("qdrant", {})
        collection_name = qdrant_config.get(
            "collection_name", f"vectorization_{uuid.uuid4().hex[:8]}"
        )

        # Store vectors
        storage_result = store_vectors_to_qdrant(points, collection_name)

        # Prepare final status
        pipeline_status = {
            "STAGE_5: STORE_VECTORS": {
                "INPUT": f"{len(embeddings)} embeddings from {default_source}",
                "OUTPUT": f"Qdrant collection: {collection_name}",
                "TOTAL_EMBEDDINGS": len(embeddings),
                "PREPARED_VECTORS": len(points),
                "STORED_VECTORS": storage_result.get("stored_vectors", 0),
                "FAILED_VECTORS": storage_result.get("failed_vectors", 0),
                "COLLECTION_NAME": collection_name,
                "VECTOR_SIZE": storage_result.get("vector_size", 1536),
                "STATUS": (
                    "Completed"
                    if storage_result.get("status") == "Success"
                    else "Failed"
                ),
                "STORAGE_DETAILS": storage_result,
            }
        }

        if storage_result.get("error"):
            pipeline_status["STAGE_5: STORE_VECTORS"]["ERROR"] = storage_result["error"]

        return pipeline_status

    except Exception as e:
        logger.error(f"❌ Store stage failed: {str(e)}")
        return {
            "STAGE_5: STORE_VECTORS": {
                "INPUT": "Unknown",
                "OUTPUT": "None",
                "TOTAL_EMBEDDINGS": 0,
                "STORED_VECTORS": 0,
                "STATUS": "Failed",
                "ERROR": str(e),
            }
        }
