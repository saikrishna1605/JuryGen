"""
File Upload API endpoints with real Google Cloud Storage integration.
"""

import os
import uuid
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field

from ....core.security import optional_auth
from ....services.storage_service import StorageService
from ....services.ocr_service import OCRService

router = APIRouter()

# Initialize services
storage_service = StorageService()
ocr_service = OCRService()


class UploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool = Field(..., description="Upload success status")
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    storage_url: str = Field(..., description="Storage URL")
    message: str = Field(..., description="Response message")


class SignedUploadResponse(BaseModel):
    """Response model for signed upload URL."""
    success: bool = Field(..., description="Success status")
    upload_url: str = Field(..., description="Signed upload URL")
    document_id: str = Field(..., description="Document identifier")
    expires_at: str = Field(..., description="URL expiration time")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Upload a file directly to Google Cloud Storage.
    """
    try:
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'text/plain'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
            )
        
        # Upload to Google Cloud Storage
        blob_name = f"documents/{document_id}/{file.filename}"
        success = await storage_service.upload_file(
            blob_name=blob_name,
            file_content=file_content,
            content_type=file.content_type
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file to storage"
            )
        
        # Get storage URL
        storage_url = f"gs://{os.getenv('STORAGE_BUCKET_NAME')}/{blob_name}"
        
        # Start OCR processing in background
        try:
            await ocr_service.process_document(
                file_content=file_content,
                content_type=file.content_type,
                document_id=document_id
            )
        except Exception as e:
            print(f"OCR processing failed: {e}")
            # Continue even if OCR fails
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type,
            storage_url=storage_url,
            message="File uploaded and processing started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/upload/signed-url", response_model=SignedUploadResponse)
async def get_signed_upload_url(
    filename: str = Form(...),
    content_type: str = Form(...),
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Get a signed URL for direct client-side upload to Google Cloud Storage.
    """
    try:
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'text/plain'
        ]
        
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type}"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Generate blob name
        blob_name = f"documents/{document_id}/{filename}"
        
        # Get signed upload URL
        upload_url = await storage_service.generate_signed_upload_url(
            blob_name=blob_name,
            content_type=content_type,
            expires_in=3600  # 1 hour
        )
        
        if not upload_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate signed upload URL"
            )
        
        # Calculate expiration time
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        return SignedUploadResponse(
            success=True,
            upload_url=upload_url,
            document_id=document_id,
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate signed URL: {str(e)}"
        )