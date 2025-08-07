import boto3
import json
from typing import List, Dict, Any, Optional
from .logger import get_logger

logger = get_logger(__name__)

# Initialize S3 client
s3_client = boto3.client("s3")


def list_s3_files(bucket_name: str, prefix: str = "") -> List[str]:
    """
    List files in S3 bucket with optional prefix.

    Args:
        bucket_name: S3 bucket name
        prefix: Optional prefix to filter files

    Returns:
        List of file keys
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [obj["Key"] for obj in response["Contents"]]
    except Exception as e:
        logger.error(f"Failed to list S3 files in {bucket_name}/{prefix}: {e}")
        return []


def fetch_json_from_s3(bucket_name: str, file_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and parse JSON file from S3.

    Args:
        bucket_name: S3 bucket name
        file_key: S3 file key

    Returns:
        Parsed JSON data or None if failed
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to fetch JSON from s3://{bucket_name}/{file_key}: {e}")
        return None


def save_json_to_s3(data: Dict[str, Any], bucket_name: str, file_key: str) -> bool:
    """
    Save JSON data to S3.

    Args:
        data: Data to save
        bucket_name: S3 bucket name
        file_key: S3 file key

    Returns:
        True if successful, False otherwise
    """
    try:
        json_content = json.dumps(data, indent=2)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=json_content,
            ContentType="application/json",
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to s3://{bucket_name}/{file_key}: {e}")
        return False
