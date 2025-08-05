import uuid
import logging
import os
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import aiofiles
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
logger.info(f"File upload configuration loaded:")
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
