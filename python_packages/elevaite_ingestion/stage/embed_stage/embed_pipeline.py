import os
import sys
import json
import glob
from dotenv import load_dotenv
from config.embedder_config import EMBEDDER_CONFIG, get_embedder
from utils.logger import get_logger
from embedding_factory.openai_embedder import get_embedding
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import S3 utilities, but make them optional
try:
    from config.aws_config import AWS_CONFIG
    from utils.s3_utils import list_s3_files, fetch_json_from_s3, save_json_to_s3

    S3_AVAILABLE = True
except ImportError:
    logger.warning("S3 utilities not available, using local mode only")
    S3_AVAILABLE = False
    AWS_CONFIG = {}

load_dotenv()
logger = get_logger(__name__)


def process_single_chunk_s3(chunk_key, input_s3_bucket, output_s3_prefix):
    try:
        chunk_data = fetch_json_from_s3(input_s3_bucket, chunk_key)
        if not chunk_data or "chunk_text" not in chunk_data:
            raise ValueError(f"Missing 'chunk_text' in {chunk_key}")

        chunk_id = chunk_data.get("chunk_id", "UNKNOWN")
        contextual_header = chunk_data.get("contextual_header", "NA")
        chunk_content = chunk_data["chunk_text"]
        filename = chunk_data.get("filename", "unknown_file")
        page_no = chunk_data.get("page_range", "NA")
        start_paragraph = chunk_data.get("start_paragraph", "UNKNOWN")
        end_paragraph = chunk_data.get("end_paragraph", "UNKNOWN")

        embedding_vector = get_embedding(chunk_content + contextual_header)

        embedding_output = {
            "chunk_id": chunk_id,
            "contextual_header": contextual_header,
            "chunk_text": chunk_content,
            "filename": filename,
            "page_range": page_no,
            "start_paragraph": start_paragraph,
            "end_paragraph": end_paragraph,
            "chunk_embedding": embedding_vector,
        }

        embedding_key = f"{output_s3_prefix}{filename}_chunk_{chunk_id}.json"
        save_json_to_s3(embedding_output, input_s3_bucket, embedding_key)

        return {
            "filename": filename,
            "page_range": page_no,
            "chunk_id": chunk_id,
            "chunk_length": len(chunk_content),
            "input": f"s3://{input_s3_bucket}/{chunk_key}",
            "output": f"s3://{input_s3_bucket}/{embedding_key}",
            "status": "Success",
        }

    except Exception as e:
        logger.error(f"❌ Failed to generate embedding for {chunk_key}. Error: {e}")
        return {
            "input": f"s3://{input_s3_bucket}/{chunk_key}",
            "status": f"Failed - {e}",
        }


def process_single_chunk_local(chunk_file_path, output_dir):
    """Process a single chunk from local file system."""
    try:
        # Read chunk data from local file
        with open(chunk_file_path, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)

        if not chunk_data or "chunk_text" not in chunk_data:
            raise ValueError(f"Missing 'chunk_text' in {chunk_file_path}")

        chunk_id = chunk_data.get("chunk_id", "UNKNOWN")
        contextual_header = chunk_data.get("contextual_header", "NA")
        chunk_content = chunk_data["chunk_text"]
        filename = chunk_data.get("filename", "unknown_file")
        page_no = chunk_data.get("page_range", "NA")
        start_paragraph = chunk_data.get("start_paragraph", "UNKNOWN")
        end_paragraph = chunk_data.get("end_paragraph", "UNKNOWN")

        # Generate embedding
        embedding_vector = get_embedding(chunk_content + contextual_header)

        embedding_output = {
            "chunk_id": chunk_id,
            "contextual_header": contextual_header,
            "chunk_text": chunk_content,
            "filename": filename,
            "page_range": page_no,
            "start_paragraph": start_paragraph,
            "end_paragraph": end_paragraph,
            "chunk_embedding": embedding_vector,
        }

        # Save to local output directory
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"{filename}_chunk_{chunk_id}.json"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(embedding_output, f, indent=2)

        return {
            "filename": filename,
            "page_range": page_no,
            "chunk_id": chunk_id,
            "chunk_length": len(chunk_content),
            "input": chunk_file_path,
            "output": output_path,
            "status": "Success",
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to generate embedding for {chunk_file_path}. Error: {e}"
        )
        return {"input": chunk_file_path, "status": f"Failed - {e}"}


def execute_embedding_stage():
    """Execute embedding stage with support for both local and S3 modes."""
    embedder = get_embedder()

    # Determine mode based on configuration
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

        if default_source == "local":
            return execute_embedding_stage_local(config)
        else:
            return execute_embedding_stage_s3()

    except Exception as e:
        logger.error(f"❌ Failed to determine storage mode: {e}")
        # Try local mode as fallback
        try:
            return execute_embedding_stage_local({})
        except:
            logger.error("❌ Both local and S3 modes failed")
            return {"error": f"Failed to execute embedding stage: {e}"}


def execute_embedding_stage_local(config):
    """Execute embedding stage for local files."""
    logger.info("🔹 Running embedding stage in LOCAL mode...")

    # Get directories from config
    loading_config = config.get("loading", {})
    local_config = loading_config.get("sources", {}).get("local", {})
    base_dir = local_config.get("output_directory", "")

    # Look for chunked files in various possible locations
    chunk_dirs = [
        os.path.join(base_dir, "chunked_output"),
        os.path.join(os.path.dirname(base_dir), "chunked_output"),
        os.path.join(base_dir, "data", "processed"),
        base_dir,
    ]

    chunk_files = []
    input_dir = None

    for chunk_dir in chunk_dirs:
        if os.path.exists(chunk_dir):
            files = glob.glob(os.path.join(chunk_dir, "*.json"))
            if files:
                chunk_files = files
                input_dir = chunk_dir
                break

    if not chunk_files:
        logger.error("❌ No chunked JSON files found in local directories.")
        return {"error": "STAGE_3 output not found in local directories"}

    # Set up output directory
    output_dir = os.path.join(os.path.dirname(input_dir), "embeddings_output")
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"📁 Found {len(chunk_files)} chunk files in {input_dir}")
    logger.info(f"📤 Output directory: {output_dir}")

    pipeline_status = {
        "STAGE_4: GET_EMBEDDING": {
            "INPUT": input_dir,
            "OUTPUT": output_dir,
            "EMBEDDING_MODEL_PROVIDER": EMBEDDER_CONFIG["provider"],
            "EMBEDDING_MODEL_NAME": EMBEDDER_CONFIG["model"],
            "TOTAL_FILES": len(chunk_files),
            "EVENT_DETAILS": [],
            "STATUS": "Failed",
        }
    }

    results = []
    max_workers = int(os.getenv("MAX_EMBED_WORKERS", 5))  # Reduced for local processing

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_chunk_local, chunk_file, output_dir)
            for chunk_file in chunk_files
        ]
        for future in as_completed(futures):
            results.append(future.result())

    processed_chunks = [r for r in results if r["status"] == "Success"]

    pipeline_status["STAGE_4: GET_EMBEDDING"].update(
        {
            "TOTAL_FILES": len(results),
            "EVENT_DETAILS": results,
            "STATUS": "Completed" if processed_chunks else "Failed",
        }
    )

    # Save status to local file
    status_file = os.path.join(output_dir, "stage_4_output.json")
    with open(status_file, "w") as f:
        json.dump(pipeline_status, f, indent=2)

    json_output = json.dumps(pipeline_status, indent=4)
    logger.info(
        f"📌 Pipeline Execution Summary (GET_EMBEDDING - LOCAL):\n{json_output}"
    )

    return pipeline_status


def execute_embedding_stage_s3():
    """Execute embedding stage for S3 files (original implementation)."""
    if not S3_AVAILABLE:
        raise Exception("S3 utilities not available but S3 mode requested")

    logger.info("🔹 Running embedding stage in S3 mode...")
    embedder = get_embedder()
    input_s3_bucket = AWS_CONFIG["intermediate_bucket"]
    output_s3_prefix = "embeddings_output/"

    logger.info("🔹 Listing chunked files from S3...")
    chunk_files = list_s3_files(input_s3_bucket, "chunked_output/")

    if not chunk_files:
        logger.error("❌ No chunked files found in S3. Aborting STAGE_4.")
        return {"error": "STAGE_3 output not found"}

    pipeline_status = {
        "STAGE_4: GET_EMBEDDING": {
            "INPUT": f"s3://{input_s3_bucket}/chunked_output/",
            "OUTPUT": f"s3://{input_s3_bucket}/{output_s3_prefix}",
            "EMBEDDING_MODEL_PROVIDER": EMBEDDER_CONFIG["provider"],
            "EMBEDDING_MODEL_NAME": EMBEDDER_CONFIG["model"],
            "TOTAL_FILES": len(chunk_files),
            "EVENT_DETAILS": [],
            "STATUS": "Failed",
        }
    }

    results = []
    max_workers = int(os.getenv("MAX_EMBED_WORKERS", 10))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_single_chunk_s3, chunk_file, input_s3_bucket, output_s3_prefix
            )
            for chunk_file in chunk_files
        ]
        for future in as_completed(futures):
            results.append(future.result())

    processed_chunks = [r for r in results if r["status"] == "Success"]

    pipeline_status["STAGE_4: GET_EMBEDDING"].update(
        {
            "TOTAL_FILES": len(results),
            "EVENT_DETAILS": results,
            "STATUS": "Completed" if processed_chunks else "Failed",
        }
    )

    final_output_key = f"{output_s3_prefix}stage_4_output.json"
    save_json_to_s3(pipeline_status, input_s3_bucket, final_output_key)

    json_output = json.dumps(pipeline_status, indent=4)
    logger.info(f"📌 Pipeline Execution Summary (GET_EMBEDDING - S3):\n{json_output}")

    return pipeline_status
