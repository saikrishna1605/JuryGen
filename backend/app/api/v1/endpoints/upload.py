"""
Document upload endpoints.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.core.config import settings
from app.core.security import get_current_user
from app.models.job import UploadRequest, UploadResponse, Job, JobOptions
from app.models.document import Document
from app.models.user import User
from app.models.base import ProcessingStatus, ProcessingStage
from app.services.storage import StorageService
from app.services.firestore import FirestoreService
import structlog

logger = structlog.get_logger()

router = APIRouter()

# Initialize services
storage_service = StorageService()
firestore_service = FirestoreService()


@router.post("/upload", response_model=UploadResponse)
async def create_upload_url(
    request: UploadRequest,
    current_user: User = Depends(get_current_user)
) -> UploadResponse:
    """
    Create a signed upload URL for document upload.
    
    This endpoint:
    1. Validates the upload request
    2. Creates a new job and document record
    3. Generates a signed upload URL
    4. Returns the upload URL and job ID
    """
    try:
        # Generate unique IDs
        job_id = uuid.uuid4()
        document_id = uuid.uuid4()
        
        # Create document record
        document = Document(
            id=document_id,
            filename=request.filename,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
            user_id=current_user.id,
            jurisdiction=request.jurisdiction,
            user_role=request.user_role,
        )
        
        # Create job record
        job_options = request.options or JobOptions()
        job = Job(
            id=job_id,
            document_id=document_id,
            user_id=current_user.id,
            options=job_options,
        )
        
        # Generate signed upload URL
        blob_name = f"documents/{current_user.id}/{document_id}/{request.filename}"
        upload_url = await storage_service.generate_signed_upload_url(
            blob_name=blob_name,
            content_type=request.content_type,
            size_limit=request.size_bytes,
            expiration_minutes=30
        )
        
        # Store document and job in Firestore
        await firestore_service.create_document(document)
        await firestore_service.create_job(job)
        
        # Update document with storage URL
        document.storage_url = f"gs://{settings.STORAGE_BUCKET}/{blob_name}"
        await firestore_service.update_document(document)
        
        logger.info(
            "Upload URL created",
            job_id=str(job_id),
            document_id=str(document_id),
            user_id=current_user.id,
            filename=request.filename,
            size_bytes=request.size_bytes
        )
        
        return UploadResponse(
            job_id=job_id,
            upload_url=upload_url,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            max_file_size=50 * 1024 * 1024,  # 50MB
            allowed_content_types=[
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain',
                'image/jpeg',
                'image/png',
                'image/tiff',
            ]
        )
        
    except GoogleCloudError as e:
        logger.error(
            "Google Cloud error during upload URL creation",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service temporarily unavailable"
        )
    except Exception as e:
        logger.error(
            "Unexpected error during upload URL creation",
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create upload URL"
        )


@router.post("/upload/{job_id}/complete")
async def complete_upload(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Mark upload as complete and trigger processing.
    
    This endpoint is called after the file has been successfully uploaded
    to the signed URL to trigger the document processing pipeline.
    """
    try:
        # Get job from Firestore
        job = await firestore_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Verify job ownership
        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Verify file was uploaded
        document = await firestore_service.get_document(job.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if file exists in storage
        blob_exists = await storage_service.blob_exists(document.storage_url)
        if not blob_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File upload not completed"
            )
        
        # Update job status and trigger processing
        from app.services.workflow import WorkflowService
        workflow_service = WorkflowService()
        
        # Start the processing workflow
        await workflow_service.start_document_processing(job_id)
        
        logger.info(
            "Upload completed and processing started",
            job_id=str(job_id),
            document_id=str(job.document_id),
            user_id=current_user.id
        )
        
        return {
            "message": "Upload completed successfully",
            "job_id": str(job_id),
            "status": "processing_started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error completing upload",
            job_id=str(job_id),
            user_id=current_user.id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete upload"
        )


@router.get("/upload/limits")
async def get_upload_limits(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get upload limits and supported file types.
    """
    return {
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "max_files_per_day": 100,
        "supported_content_types": [
            {
                "type": "application/pdf",
                "extensions": [".pdf"],
                "description": "PDF documents"
            },
            {
                "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "extensions": [".docx"],
                "description": "Microsoft Word documents (modern)"
            },
            {
                "type": "application/msword",
                "extensions": [".doc"],
                "description": "Microsoft Word documents (legacy)"
            },
            {
                "type": "text/plain",
                "extensions": [".txt"],
                "description": "Plain text files"
            },
            {
                "type": "image/jpeg",
                "extensions": [".jpg", ".jpeg"],
                "description": "JPEG images"
            },
            {
                "type": "image/png",
                "extensions": [".png"],
                "description": "PNG images"
            },
            {
                "type": "image/tiff",
                "extensions": [".tiff", ".tif"],
                "description": "TIFF images"
            }
        ],
        "processing_options": {
            "enable_translation": {
                "type": "boolean",
                "default": True,
                "description": "Enable multi-language translation"
            },
            "enable_audio": {
                "type": "boolean",
                "default": True,
                "description": "Generate audio narration"
            },
            "reading_level": {
                "type": "enum",
                "options": ["elementary", "middle", "high", "college"],
                "default": "middle",
                "description": "Target reading level for summaries"
            },
            "highlight_risks": {
                "type": "boolean",
                "default": True,
                "description": "Highlight risky clauses in exports"
            }
        }
    }