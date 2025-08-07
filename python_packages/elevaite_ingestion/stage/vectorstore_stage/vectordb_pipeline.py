import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)
import json
from config.vector_db_config import VECTOR_DB_CONFIG
from config.aws_config import AWS_CONFIG
from utils.logger import get_logger
from vectorstore.vectordb_factory import VectorDBFactory
from utils.s3_utils import list_s3_files, fetch_json_from_s3
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
logger = get_logger(__name__)

def process_single_embedding_file(embedding_file, input_s3_bucket, vector_db_client, vector_db_type, vector_db_settings):
    try:
        embedding_data = fetch_json_from_s3(input_s3_bucket, embedding_file)
        if not embedding_data or "chunk_embedding" not in embedding_data:
            raise ValueError(f"❌ Missing 'chunk_embedding' in {embedding_file}")

        chunk_id = embedding_data.get("chunk_id", "UNKNOWN")
        contextual_header = embedding_data.get("contextual_header", "NA")
        chunk_content = embedding_data.get("chunk_text", "")
        filename = embedding_data.get("filename", "unknown_file")
        page_range = embedding_data.get("page_range", None)
        chunk_embedding = embedding_data["chunk_embedding"]
        start_paragraph = embedding_data.get("start_paragraph")
        end_paragraph = embedding_data.get("end_paragraph")

        metadata = {
            "chunk_id": chunk_id,
            "contexual_header": contextual_header,
            "chunk_text": chunk_content,
            "filename": filename,
            "page_range": page_range if page_range is not None else [],
            "start_paragraph": start_paragraph if start_paragraph is not None else [],
            "end_paragraph": end_paragraph if end_paragraph is not None else []
        }

        if vector_db_type == "pinecone":
            vector_db_client.upsert(vectors=[{
                "id": f"{filename}_chunk_{chunk_id}",
                "values": chunk_embedding,
                "metadata": metadata
            }])
            logger.info(f"✅ Upserted {filename} - Chunk {chunk_id} into Pinecone.")

        elif vector_db_type == "chroma":
            collection = vector_db_client.init_collection(vector_db_settings["collection_name"])
            vector_db_client.add(
                collection=collection,
                documents=[chunk_content],
                embeddings=[chunk_embedding],
                metadatas=[metadata],
                ids=[f"{filename}_chunk_{chunk_id}"]
            )
            logger.info(f"✅ Upserted {filename} - Chunk {chunk_id} into Chroma.")

        elif vector_db_type == "qdrant":
            collection_name = vector_db_settings["collection_name"]
            vector_size = 1536
            vector_db_client.ensure_collection(collection_name, vector_size=vector_size)

            vector_db_client.upsert_vectors(
                collection_name=collection_name,
                vectors=[{
                    "id": chunk_id,
                    "vector": chunk_embedding,
                    "payload": metadata
                }]
            )
            logger.info(f"✅ Upserted {filename} - Chunk {chunk_id} into Qdrant.")

        return {
            "filename": filename,
            "chunk_id": chunk_id,
            "input": f"s3://{input_s3_bucket}/{embedding_file}",
            "status": "Success"
        }

    except Exception as e:
        logger.error(f"❌ Failed to store embedding for {embedding_file}. Error: {e}")
        return {
            "input": f"s3://{input_s3_bucket}/{embedding_file}",
            "status": f"Failed - {e}"
        }

def execute_vector_db_stage():
    input_s3_bucket = AWS_CONFIG["intermediate_bucket"]
    embeddings_s3_prefix = "embeddings_output/"

    vector_db_type = VECTOR_DB_CONFIG["vector_db"]
    vector_db_settings = VECTOR_DB_CONFIG.get(vector_db_type, {})

    vector_db_client = VectorDBFactory.get_client(vector_db_type, **vector_db_settings)

    logger.info("🔹 Listing embedding files from S3...")
    embedding_files = list_s3_files(input_s3_bucket, embeddings_s3_prefix)

    if not embedding_files:
        logger.warning("⚠️ No embeddings found in S3. Aborting STAGE_5.")
        return {"error": "STAGE_4 output not found"}

    pipeline_status = {
        "STAGE_5: VECTORSTORE": {
            "INPUT": f"s3://{input_s3_bucket}/embeddings_output/",
            "VECTOR_DB": vector_db_type,
            "TOTAL_FILES": len(embedding_files),
            "EVENT_DETAILS": [],
            "STATUS": "Failed"
        }
    }

    results = []
    max_workers = int(os.getenv("MAX_VECTORSTORE_WORKERS", 10))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_embedding_file, embedding_file, input_s3_bucket, vector_db_client, vector_db_type, vector_db_settings)
            for embedding_file in embedding_files
        ]
        for future in as_completed(futures):
            results.append(future.result())

    processed_entries = [r for r in results if r["status"] == "Success"]

    pipeline_status["STAGE_5: VECTORSTORE"].update({
        "TOTAL_FILES": len(results),
        "EVENT_DETAILS": results,
        "STATUS": "Completed" if processed_entries else "Failed"
    })

    json_output = json.dumps(pipeline_status, indent=4)
    logger.info(f"📌 Pipeline Execution Summary (VECTORSTORE):\n{json_output}")

    return pipeline_status
