"""
File upload and processing endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, Depends
from typing import Optional
from pathlib import Path
from datetime import datetime

from ..util import api_key_or_user_guard
from ..schemas import FileUploadResponse
from ..services.queue_service import get_queue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    workflow_id: Optional[str] = Form(None),
    auto_process: bool = Form(False),
    request: Request = None,
    _principal: str = Depends(api_key_or_user_guard("upload_file")),
):
    """
    Upload a file and optionally trigger workflow processing.

    This endpoint handles file uploads and can automatically trigger
    workflow execution if a workflow_id is provided and auto_process is True.
    """
    try:
        # Create upload directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / unique_filename

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        result = {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "upload_timestamp": datetime.now().isoformat(),
        }

        # Auto-process if requested
        if auto_process and workflow_id:
            from uuid import uuid4

            # Generate execution ID
            execution_id = str(uuid4())

            # Queue the workflow execution
            queue_service = await get_queue_service()
            await queue_service.publish_workflow_execution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                trigger_data={"file_path": str(file_path)},
                user_context={"user_id": "file_upload_user"},
            )

            result["auto_processing"] = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "queued",
            }

        return result

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
