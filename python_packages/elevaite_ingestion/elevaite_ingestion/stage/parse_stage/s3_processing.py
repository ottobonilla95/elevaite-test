import os
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from dotenv import load_dotenv

from elevaite_ingestion.stage.parse_stage.parse_pipeline import process_file
from elevaite_ingestion.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)
s3_client = boto3.client("s3")


def list_s3_files(bucket_name):
    """List all files in the given S3 bucket."""
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" not in response:
        return []
    return [obj["Key"] for obj in response["Contents"]]


def process_single_s3_file(file_key, input_bucket, intermediate_bucket):
    try:
        original_filename = os.path.basename(file_key)
        response = s3_client.get_object(Bucket=input_bucket, Key=file_key)
        file_stream = response["Body"].read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_key)[-1]) as tmp_file:
            tmp_file.write(file_stream)
            tmp_file_path = tmp_file.name

        md_path, structured_data = process_file(tmp_file_path, output_dir="/tmp", original_filename=original_filename)

        if md_path:
            structured_data["filename"] = original_filename

            json_content = json.dumps(structured_data, indent=4)
            json_file_key = file_key.rsplit(".", 1)[0] + ".json"

            s3_client.put_object(
                Bucket=intermediate_bucket, Key=json_file_key, Body=json_content, ContentType="application/json"
            )

            logger.info(f"✅ Processed {file_key} -> {json_file_key} successfully.")

            return {"input_key": file_key, "output_key": json_file_key, "status": "Success"}

        os.remove(tmp_file_path)

    except Exception as e:
        logger.error(f"Error processing {file_key}: {e}")
        return {"input_key": file_key, "output_key": None, "status": f"Failed - {e}"}


def process_s3_files(input_bucket, intermediate_bucket):
    """Processes files from S3 and uploads parsed content back to S3."""
    file_keys = list_s3_files(input_bucket)
    if not file_keys:
        logger.info("No files found in the input bucket.")
        return []

    event_status = []
    max_workers = int(os.getenv("MAX_PARSING_WORKERS", 5))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_s3_file, file_key, input_bucket, intermediate_bucket) for file_key in file_keys
        ]
        for future in as_completed(futures):
            event_status.append(future.result())

    return event_status
