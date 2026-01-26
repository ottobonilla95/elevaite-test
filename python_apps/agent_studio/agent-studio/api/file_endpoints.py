import uuid
import logging
import os
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import aiofiles
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

from db.database import get_db

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


# Configure upload directory from environment
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

# Maximum file size from environment (default: 50MB)
try:
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_BYTES", str(50 * 1024 * 1024)))
except ValueError:
    logger.warning("Invalid MAX_FILE_SIZE_BYTES value, using default: 50MB")
    MAX_FILE_SIZE = 50 * 1024 * 1024

# Allowed file extensions from environment
DEFAULT_EXTENSIONS = [
    ".txt",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".md",
    ".py",
    ".js",
    ".html",
    ".css",
    ".sql",
    ".log",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".mp4",
    ".avi",
    ".mov",
    ".mp3",
    ".wav",
    ".zip",
    ".tar",
    ".gz",
]

extensions_env = os.getenv("ALLOWED_FILE_EXTENSIONS")
if extensions_env:
    ALLOWED_EXTENSIONS = set(
        item.strip() for item in extensions_env.split(",") if item.strip()
    )
else:
    ALLOWED_EXTENSIONS = set(DEFAULT_EXTENSIONS)

# Log configuration on startup
logger.info("File upload configuration loaded:")
logger.info(f"  Upload directory: {UPLOAD_DIR}")
logger.info(
    f"  Max file size: {MAX_FILE_SIZE} bytes ({MAX_FILE_SIZE / (1024 * 1024):.1f} MB)"
)
logger.info(f"  Allowed extensions: {len(ALLOWED_EXTENSIONS)} types")


def get_file_size_readable(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} TB"


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file."""
    if not file.filename:
        return False, "No filename provided"

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return (
            False,
            f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check file size (this is approximate, actual size check happens during upload)
    if hasattr(file, "size") and file.size and file.size > MAX_FILE_SIZE:
        return (
            False,
            f"File too large. Maximum size: {get_file_size_readable(MAX_FILE_SIZE)}",
        )

    return True, "Valid"


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    workflow_id: Optional[str] = Form(None),
    agent_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a file for use in workflows or agents.

    Args:
        file: The uploaded file
        workflow_id: Optional workflow ID to associate with the file
        agent_id: Optional agent ID to associate with the file
        description: Optional description of the file
        db: Database session

    Returns:
        JSON response with file information
    """
    try:
        # Validate file
        is_valid, message = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = file.filename or "unknown"
        file_ext = Path(filename).suffix.lower()
        unique_filename = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Check actual file size during upload
        total_size = 0

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    await f.close()
                    if file_path.exists():
                        file_path.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {get_file_size_readable(MAX_FILE_SIZE)}",
                    )
                await f.write(chunk)

        # Get file info
        file_info = {
            "file_id": file_id,
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "file_path": str(file_path),
            "file_size": total_size,
            "file_size_readable": get_file_size_readable(total_size),
            "file_type": file.content_type or "application/octet-stream",
            "file_extension": file_ext,
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "description": description,
            "status": "uploaded",
        }

        logger.info(f"File uploaded successfully: {file.filename} -> {unique_filename}")

        return JSONResponse(
            content={
                "success": True,
                "message": "File uploaded successfully",
                "data": file_info,
            },
            status_code=200,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/")
async def list_files(
    workflow_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List uploaded files with optional filtering.

    Args:
        workflow_id: Filter by workflow ID
        agent_id: Filter by agent ID
        limit: Maximum number of files to return
        db: Database session

    Returns:
        List of file information
    """
    try:
        files = []

        # List files in upload directory
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                file_info = {
                    "file_id": file_path.stem,
                    "stored_filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": stat.st_size,
                    "file_size_readable": get_file_size_readable(stat.st_size),
                    "file_extension": file_path.suffix.lower(),
                    "created_at": stat.st_ctime,
                    "modified_at": stat.st_mtime,
                }
                files.append(file_info)

        # Sort by creation time (newest first)
        files.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply limit
        files = files[:limit]

        return JSONResponse(
            content={"success": True, "data": files, "count": len(files)},
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """
    Delete an uploaded file.

    Args:
        file_id: ID of the file to delete
        db: Database session

    Returns:
        Success message
    """
    try:
        # Find file by ID
        file_found = False
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.stem == file_id:
                file_path.unlink()
                file_found = True
                logger.info(f"File deleted: {file_path.name}")
                break

        if not file_found:
            raise HTTPException(status_code=404, detail="File not found")

        return JSONResponse(
            content={"success": True, "message": "File deleted successfully"},
            status_code=200,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/config")
async def get_upload_config():
    """
    Get current file upload configuration.

    Returns:
        Current upload configuration settings
    """
    return JSONResponse(
        content={
            "success": True,
            "data": {
                "upload_dir": str(UPLOAD_DIR),
                "max_file_size": MAX_FILE_SIZE,
                "max_file_size_readable": get_file_size_readable(MAX_FILE_SIZE),
                "allowed_extensions": sorted(list(ALLOWED_EXTENSIONS)),
                "total_allowed_types": len(ALLOWED_EXTENSIONS),
            },
        },
        status_code=200,
    )


@router.post("/upload-to-s3")
async def upload_files_to_s3(
    file_ids: str = Form(...),  # Comma-separated list of file IDs
    bucket_name: str = Form(...),
    s3_prefix: Optional[str] = Form(""),  # Optional prefix for S3 key
    db: Session = Depends(get_db),
):
    """
    Upload files to S3 bucket using their file IDs.

    Args:
        file_ids: Comma-separated list of file IDs to upload to S3
        bucket_name: Name of the S3 bucket
        s3_prefix: Optional prefix for S3 object keys
        db: Database session

    Returns:
        JSON response with upload results
    """
    try:
        # Parse file IDs
        file_id_list = [fid.strip() for fid in file_ids.split(",") if fid.strip()]

        if not file_id_list:
            raise HTTPException(status_code=400, detail="No file IDs provided")

        # Initialize S3 client
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
            )
        except NoCredentialsError:
            raise HTTPException(
                status_code=500,
                detail="AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.",
            )

        upload_results = []

        for file_id in file_id_list:
            try:
                # Find the file in the upload directory
                file_path = None
                for file in UPLOAD_DIR.iterdir():
                    if file.is_file() and file.stem == file_id:
                        file_path = file
                        break

                if not file_path or not file_path.exists():
                    upload_results.append(
                        {
                            "file_id": file_id,
                            "status": "error",
                            "message": f"File with ID {file_id} not found",
                        }
                    )
                    continue

                # Generate S3 key
                original_filename = file_path.name
                s3_key = (
                    f"{s3_prefix.rstrip('/')}/{original_filename}"
                    if s3_prefix
                    else original_filename
                )

                # Upload to S3
                s3_client.upload_file(str(file_path), bucket_name, s3_key)

                upload_results.append(
                    {
                        "file_id": file_id,
                        "status": "success",
                        "s3_bucket": bucket_name,
                        "s3_key": s3_key,
                        "original_filename": original_filename,
                        "message": f"Successfully uploaded to s3://{bucket_name}/{s3_key}",
                    }
                )

                logger.info(
                    f"Successfully uploaded {original_filename} to s3://{bucket_name}/{s3_key}"
                )

            except ClientError as e:
                error_message = f"S3 upload failed: {str(e)}"
                logger.error(f"S3 upload failed for file {file_id}: {error_message}")
                upload_results.append(
                    {"file_id": file_id, "status": "error", "message": error_message}
                )
            except Exception as e:
                error_message = f"Upload failed: {str(e)}"
                logger.error(f"Upload failed for file {file_id}: {error_message}")
                upload_results.append(
                    {"file_id": file_id, "status": "error", "message": error_message}
                )

        # Check if all uploads were successful
        successful_uploads = [r for r in upload_results if r["status"] == "success"]
        failed_uploads = [r for r in upload_results if r["status"] == "error"]

        response_status = (
            200 if len(failed_uploads) == 0 else 207
        )  # 207 Multi-Status for partial success

        return JSONResponse(
            content={
                "success": len(failed_uploads) == 0,
                "message": f"Uploaded {len(successful_uploads)}/{len(file_id_list)} files successfully",
                "data": {
                    "bucket_name": bucket_name,
                    "total_files": len(file_id_list),
                    "successful_uploads": len(successful_uploads),
                    "failed_uploads": len(failed_uploads),
                    "results": upload_results,
                },
            },
            status_code=response_status,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"S3 upload operation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"S3 upload operation failed: {str(e)}"
        )


@router.post("/upload-direct-to-s3")
async def upload_files_direct_to_s3(
    files: list[UploadFile] = File(...),
    bucket_name: str = Form(...),
    s3_prefix: Optional[str] = Form(""),  # Optional prefix for S3 key
    db: Session = Depends(get_db),
):
    """
    Upload files directly to S3 bucket without storing them on the server first.

    Args:
        files: List of files to upload directly to S3
        bucket_name: Name of the S3 bucket
        s3_prefix: Optional prefix for S3 object keys
        db: Database session

    Returns:
        JSON response with upload results and file metadata
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Initialize S3 client
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
            )
        except NoCredentialsError:
            raise HTTPException(
                status_code=500,
                detail="AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.",
            )

        upload_results = []

        for file in files:
            try:
                # Validate file
                is_valid, message = validate_file(file)
                if not is_valid:
                    upload_results.append(
                        {
                            "original_filename": file.filename,
                            "status": "error",
                            "message": message,
                        }
                    )
                    continue

                # Generate unique filename and S3 key
                file_id = str(uuid.uuid4())
                filename = file.filename or "unknown"
                file_ext = Path(filename).suffix.lower()
                unique_filename = f"{file_id}{file_ext}"
                s3_key = (
                    f"{s3_prefix.rstrip('/')}/{unique_filename}"
                    if s3_prefix
                    else unique_filename
                )

                # Read file content
                file_content = await file.read()
                file_size = len(file_content)

                # Check file size
                if file_size > MAX_FILE_SIZE:
                    upload_results.append(
                        {
                            "original_filename": filename,
                            "status": "error",
                            "message": f"File too large. Maximum size: {get_file_size_readable(MAX_FILE_SIZE)}",
                        }
                    )
                    continue

                # Upload directly to S3
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=file.content_type or "application/octet-stream",
                )

                upload_results.append(
                    {
                        "file_id": file_id,
                        "original_filename": filename,
                        "stored_filename": unique_filename,
                        "status": "success",
                        "s3_bucket": bucket_name,
                        "s3_key": s3_key,
                        "file_size": file_size,
                        "file_size_readable": get_file_size_readable(file_size),
                        "file_type": file.content_type or "application/octet-stream",
                        "file_extension": file_ext,
                        "message": f"Successfully uploaded to s3://{bucket_name}/{s3_key}",
                    }
                )

                logger.info(
                    f"Successfully uploaded {filename} directly to s3://{bucket_name}/{s3_key}"
                )

                # Reset file position for potential reuse
                await file.seek(0)

            except ClientError as e:
                error_message = f"S3 upload failed: {str(e)}"
                logger.error(
                    f"S3 upload failed for file {file.filename}: {error_message}"
                )
                upload_results.append(
                    {
                        "original_filename": file.filename,
                        "status": "error",
                        "message": error_message,
                    }
                )
            except Exception as e:
                error_message = f"Upload failed: {str(e)}"
                logger.error(f"Upload failed for file {file.filename}: {error_message}")
                upload_results.append(
                    {
                        "original_filename": file.filename,
                        "status": "error",
                        "message": error_message,
                    }
                )

        # Check if all uploads were successful
        successful_uploads = [r for r in upload_results if r["status"] == "success"]
        failed_uploads = [r for r in upload_results if r["status"] == "error"]

        response_status = (
            200 if len(failed_uploads) == 0 else 207
        )  # 207 Multi-Status for partial success

        return JSONResponse(
            content={
                "success": len(failed_uploads) == 0,
                "message": f"Uploaded {len(successful_uploads)}/{len(files)} files successfully",
                "data": {
                    "bucket_name": bucket_name,
                    "total_files": len(files),
                    "successful_uploads": len(successful_uploads),
                    "failed_uploads": len(failed_uploads),
                    "results": upload_results,
                },
            },
            status_code=response_status,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Direct S3 upload operation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Direct S3 upload operation failed: {str(e)}"
        )
