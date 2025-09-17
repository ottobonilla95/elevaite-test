import json
import boto3
from elevaite_ingestion.utils.logger import get_logger

logger = get_logger(__name__)

s3_client = boto3.client("s3")


def list_s3_files(bucket_name, prefix=""):
    """List all JSON files in the given S3 bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".json")]
    except Exception as e:
        logger.error(f"❌ Error listing files from {bucket_name}: {e}")
        return []


def fetch_json_from_s3(bucket_name, file_key):
    """Downloads and reads a JSON file from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        logger.error(f"❌ Failed to fetch {file_key} from S3: {e}")
        return None


def save_json_to_s3(data, bucket_name, file_key):
    """Uploads JSON data to S3."""
    try:
        json_content = json.dumps(data, indent=4)
        s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=json_content, ContentType="application/json")
        logger.info(f"✅ Saved JSON to S3: s3://{bucket_name}/{file_key}")
    except Exception as e:
        logger.error(f"❌ Failed to save JSON to S3: {e}")
