import os
import sys
import json
import boto3
import importlib
import asyncio
from dotenv import load_dotenv
from elevaite_ingestion.config.chunker_config import CHUNKER_CONFIG
from elevaite_ingestion.config.aws_config import AWS_CONFIG
from elevaite_ingestion.utils.logger import get_logger
from elevaite_ingestion.utils.s3_utils import list_s3_files, fetch_json_from_s3

load_dotenv()
logger = get_logger(__name__)
s3_client = boto3.client("s3")


def create_s3_folder(bucket_name, folder_name):
    if not folder_name.strip():
        logger.warning(f"⚠️ Skipping folder creation: Empty folder_name received.")
        return

    try:
        folder_key = folder_name.rstrip("/") + "/"
        s3_client.put_object(Bucket=bucket_name, Key=folder_key)
        logger.info(f"✅ Created S3 folder: s3://{bucket_name}/{folder_name}/")
    except Exception as e:
        logger.error(f"❌ Failed to create S3 folder {folder_name}. Error: {e}")


def load_chunking_function():
    chunking_strategy = CHUNKER_CONFIG["chunk_strategy"]

    if chunking_strategy not in CHUNKER_CONFIG["available_chunkers"]:
        raise ValueError(
            f"❌ Invalid chunking strategy '{chunking_strategy}'. "
            f"Available: {list(CHUNKER_CONFIG['available_chunkers'].keys())}"
        )

    chunker_info = CHUNKER_CONFIG["available_chunkers"][chunking_strategy]
    module_name = chunker_info["import_path"]
    function_name = chunker_info["function_name"]

    try:
        module = importlib.import_module(module_name)
        chunk_text_func = getattr(module, function_name)
        logger.info(f"📦 Using chunking strategy: {chunking_strategy} ({module_name}.{function_name})")
        return chunk_text_func, chunker_info["settings"]
    except (ImportError, AttributeError) as e:
        raise ImportError(f"❌ Failed to load chunking function '{function_name}' from '{module_name}'. Error: {e}")


async def process_single_file(file_key, chunk_text, chunking_params, output_s3_bucket, output_s3_prefix):
    parsed_content = fetch_json_from_s3(output_s3_bucket, file_key)
    event_result = {"input_url": f"s3://{output_s3_bucket}/{file_key}", "status": "Failed"}

    if not parsed_content or not isinstance(parsed_content, dict):
        logger.error(f"❌ Skipping {file_key}: Invalid JSON structure.")
        event_result["status"] = "Failed - Invalid JSON"
        return event_result

    filename = parsed_content.get("filename", file_key)

    if "paragraphs" in parsed_content:
        logger.info(f"📄 Processing PDF Chunking: {filename}")
    elif "content" in parsed_content:
        logger.info(f"📝 Processing Non-PDF Chunking: {filename}")
    else:
        logger.error(f"❌ {filename} is missing both 'paragraphs' and 'content' fields.")
        event_result["status"] = "Failed - Missing required fields"
        return event_result

    try:
        chunks = await chunk_text(parsed_content, chunking_params)
    except Exception as e:
        logger.error(f"❌ Chunking failed for {filename}: {e}")
        event_result["status"] = f"Failed - Chunking error: {e}"
        return event_result

    if not chunks:
        logger.warning(f"⚠️ No chunks were created for {filename}.")
        event_result["status"] = "Failed - No chunks created"
        return event_result

    for i, chunk in enumerate(chunks):
        chunk["filename"] = filename
        chunk_key = f"{output_s3_prefix}{filename}_chunk_{i + 1}.json"
        chunk_data = json.dumps(chunk, indent=4, ensure_ascii=False)

        try:
            s3_client.put_object(Bucket=output_s3_bucket, Key=chunk_key, Body=chunk_data, ContentType="application/json")
            logger.info(f"✅ Uploaded {filename} - chunk {i + 1} to s3://{output_s3_bucket}/{chunk_key}")
        except Exception as e:
            logger.error(f"❌ Failed to upload chunk {i + 1} of {filename}. Error: {e}")
            event_result["status"] = f"Failed - S3 Upload error: {e}"
            return event_result

    event_result.update(
        {
            "output_url": f"s3://{output_s3_bucket}/{output_s3_prefix}{filename}_chunk_*.json",
            "total_chunks": len(chunks),
            "status": "Success",
        }
    )

    return event_result


async def execute_chunking_stage(parsed_files, stage_2_status):
    mode = os.getenv("MODE", "s3")
    output_s3_bucket = AWS_CONFIG["intermediate_bucket"]
    output_s3_prefix = "chunked_output/"
    chunk_text, chunking_params = load_chunking_function()

    create_s3_folder(output_s3_bucket, output_s3_prefix)

    pipeline_status = {
        "STAGE_3: CHUNKING": {
            "DATA_SOURCE": mode,
            "INPUT_BUCKET_URL": stage_2_status["STAGE_2: PARSING"]["OUTPUT"],
            "OUTPUT_BUCKET_URL": f"s3://{output_s3_bucket}/{output_s3_prefix}",
            "CHUNKING_STRATEGY": CHUNKER_CONFIG["chunk_strategy"],
            "TOTAL_FILES": len(parsed_files),
            "EVENT_DETAILS": [],
            "STATUS": "Failed",
        }
    }

    try:
        for file_key in parsed_files:
            result = await process_single_file(file_key, chunk_text, chunking_params, output_s3_bucket, output_s3_prefix)
            pipeline_status["STAGE_3: CHUNKING"]["EVENT_DETAILS"].append(result)

        all_success = all(e["status"].startswith("Success") for e in pipeline_status["STAGE_3: CHUNKING"]["EVENT_DETAILS"])
        pipeline_status["STAGE_3: CHUNKING"]["STATUS"] = "Completed" if all_success else "Partial Success"

    except Exception as e:
        logger.error(f"❌ Failed to chunk files. Error: {e}")
        pipeline_status["STAGE_3: CHUNKING"]["EVENT_DETAILS"].append({"input": "All parsed files", "status": f"Failed - {e}"})

    json_output = json.dumps(pipeline_status, indent=4)
    logger.info(f"📌 Pipeline Execution Summary (CHUNKING):\n{json_output}")

    return pipeline_status
