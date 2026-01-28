"""
Storage Tools for Workflow Engine

Tools for uploading files to cloud storage services like AWS S3.
"""

import json
import os
import uuid
from typing import Optional, Dict, Any
from .decorators import function_schema


@function_schema
def upload_to_s3(
    attachment: Dict[str, Any],
    bucket_name: Optional[str] = None,
    s3_prefix: Optional[str] = None,
    url_expiration_seconds: Optional[int] = None,
) -> str:
    """
    Upload a file attachment to S3 and return a signed URL for accessing it.

    Args:
        attachment: The file attachment object containing name, size_bytes, mime, and path
        bucket_name: S3 bucket name (defaults to AWS_S3_BUCKET env var)
        s3_prefix: Optional prefix/folder path in S3 (defaults to AWS_S3_PREFIX env var or "uploads/")
        url_expiration_seconds: How long the signed URL should be valid (defaults to 3600 = 1 hour)

    Returns:
        A JSON string containing the S3 key and signed URL, or an error message
    """
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    # Extract attachment details
    file_name = attachment.get("name", "unknown")
    file_path = attachment.get("path")
    mime_type = attachment.get("mime", "application/octet-stream")

    if not file_path:
        return json.dumps({"error": "No file path in attachment", "success": False})

    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}", "success": False})

    # Get S3 configuration from environment or parameters
    bucket = bucket_name or os.getenv("AWS_S3_BUCKET")
    if not bucket:
        return json.dumps(
            {
                "error": "No S3 bucket specified. Set AWS_S3_BUCKET env var or pass bucket_name parameter.",
                "success": False,
            }
        )

    prefix = (
        s3_prefix if s3_prefix is not None else os.getenv("AWS_S3_PREFIX", "uploads/")
    )
    expiration = url_expiration_seconds or 3600

    # Generate unique S3 key
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file_name)[1]
    s3_key = f"{prefix.rstrip('/')}/{file_id}{file_ext}"

    try:
        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
        )

        # Upload file to S3
        with open(file_path, "rb") as f:
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=f,
                ContentType=mime_type,
            )

        # Generate presigned URL
        signed_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiration,
        )

        return json.dumps(
            {
                "success": True,
                "s3_bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": f"s3://{bucket}/{s3_key}",
                "signed_url": signed_url,
                "url_expires_in_seconds": expiration,
                "original_filename": file_name,
                "mime_type": mime_type,
            }
        )

    except NoCredentialsError:
        return json.dumps(
            {
                "error": "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
                "success": False,
            }
        )
    except ClientError as e:
        return json.dumps({"error": f"S3 error: {str(e)}", "success": False})
    except Exception as e:
        return json.dumps({"error": f"Upload failed: {str(e)}", "success": False})


STORAGE_TOOL_STORE = {
    "upload_to_s3": upload_to_s3,
}

STORAGE_TOOL_SCHEMAS = {
    name: func.openai_schema for name, func in STORAGE_TOOL_STORE.items()
}
