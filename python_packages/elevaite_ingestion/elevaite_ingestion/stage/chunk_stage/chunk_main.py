import os
import time
import json
import boto3
import asyncio
from typing import Optional
from dotenv import load_dotenv

from elevaite_ingestion.config.pipeline_config import PipelineConfig

# Legacy imports for backward compatibility
from elevaite_ingestion.config.load_config import LOADING_CONFIG
from elevaite_ingestion.config.aws_config import AWS_CONFIG
from elevaite_ingestion.utils.logger import get_logger
from elevaite_ingestion.stage.chunk_stage.chunk_pipeline import execute_chunking_stage

load_dotenv()

logger = get_logger(__name__)
s3_client = boto3.client("s3")


def clean_s3_bucket_name(bucket_name):
    return bucket_name.replace("s3://", "") if bucket_name.startswith("s3://") else bucket_name


def list_s3_files(bucket_name, prefix=""):
    try:
        bucket_name = clean_s3_bucket_name(bucket_name)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".json")]
    except Exception as e:
        logger.error(f"Error listing files from {bucket_name}: {e}")
        return []


def fetch_parsed_json_from_s3(bucket_name, file_key):
    try:
        bucket_name = clean_s3_bucket_name(bucket_name)
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        json_content = response["Body"].read().decode("utf-8")
        return json.loads(json_content)
    except Exception as e:
        logger.error(f"Failed to fetch {file_key} from S3: {e}")
        return None


async def execute_chunking_pipeline(config: Optional[PipelineConfig] = None) -> dict:
    """Execute the chunking pipeline.

    Args:
        config: Optional PipelineConfig object. Falls back to global config if not provided.

    Returns:
        Dictionary with pipeline execution status.
    """
    # Use provided config or fall back to legacy global config
    if config:
        source_type = "s3"  # Chunking only supports S3 mode
        intermediate_bucket = config.aws.intermediate_bucket
    else:
        source_type = LOADING_CONFIG["default_source"]
        intermediate_bucket = AWS_CONFIG["intermediate_bucket"]

    input_bucket = intermediate_bucket  # Input comes from parsing output

    if source_type != "s3":
        logger.error("This script is designed for S3 mode only.")
        return {"error": "Invalid mode. This script supports S3 only."}

    intermediate_bucket_clean = clean_s3_bucket_name(intermediate_bucket)
    parsed_files = list_s3_files(intermediate_bucket_clean)

    if not parsed_files:
        logger.error("No parsed files found in S3. Aborting chunking stage.")
        return {"error": "No parsed files found in S3"}

    stage_2_status = {
        "STAGE_2: PARSING": {
            "MODE": source_type,
            "INPUT": f"s3://{input_bucket}",
            "OUTPUT": f"s3://{intermediate_bucket}",
            "TOTAL_FILES": len(parsed_files),
            "EVENT_DETAILS": [],
            "STATUS": "Completed",
        }
    }

    for file_key in parsed_files:
        stage_2_status["STAGE_2: PARSING"]["EVENT_DETAILS"].append(
            {
                "input": f"s3://{intermediate_bucket}/{file_key}",
                "output": f"s3://{intermediate_bucket}/{file_key}",
                "status": "Success",
            }
        )

    logger.info("Starting STAGE_3: CHUNKING...")
    stage_3_status = await execute_chunking_stage(parsed_files, stage_2_status, config=config)

    pipeline_status = {**stage_3_status}

    json_output = json.dumps(pipeline_status, indent=4)
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "stage_3_status.json")
    with open(file_path, "w") as json_file:
        json_file.write(json_output)
    logger.info(f"CHUNKING STAGE: Pipeline Execution Summary:\n{json_output}")

    return pipeline_status


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(execute_chunking_pipeline())
    end_time = time.time()
    print(f"total chunking time: {end_time - start_time:.2f} seconds")
