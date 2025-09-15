"""
Documents API endpoints for Legal Companion.
Handles document upload, storage, OCR processing, and analysis.
"""

import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ....core.security import require_auth
from ....models.base import ApiResponse
from ....models.document import Document, ProcessedDocument, DocumentMetadata, OCRResult
from ....services.document_service import DocumentService
from ....services.storage_service import StorageService
from ....services.ocr_service import OCRService
from ....services.database import get_db

router = APIRouter()

# Initialize services
document_service = DocumentService()
storage_service = StorageService()
ocr_service = OCRService()


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    jurisdiction: Optional[str] = Field(default=None, description="Legal jurisdiction")
    user_role: Optional[str] = Field(default=None, description="User's role in document context")
    auto_process: bool = Field(default=True, description="Whether to automatically start processing")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str = Field(..., description="Unique document identifier")
    upload_url: str = Field(..., description="Signed URL for file upload")
    expires_at: datetime = Field(..., description="Upload URL expiration time")
    processing_status: str = Field(..., description="Initial processing status")


class DocumentProcessingRequest(BaseModel):
    """Request model for document processing."""
    document_id: str = Field(..., description="Document identifier")
    force_reprocess: bool = Field(default=False, description="Force reprocessing even if already processed")
    ocr_options: Optional[Dict[str, Any]] = Field(default=None, description="OCR processing options")


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[Document] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Documents per page")


class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis."""
    document_id: str = Field(..., description="Document identifier")
    analysis_status: str = Field(..., description="Analysis status")
    ocr_result: Optional[OCRResult] = Field(default=None, description="OCR processing result")
    metadata: Optional[DocumentMetadata] = Field(default=None, description="Document metadata")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")


# Document Upload Endpoints
@router.post("/documents/upload", response_model=ApiResponse[DocumentUploadResponse])
async def create_document_upload(
    request: DocumentUploadRequest,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Create a new document and get signed upload URL.
    
    This endpoint creates a document record in the database and returns
    a signed URL for uploading the actual file to cloud storage.
    """
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'image/jpeg',
            'image/png',
            'image/tiff'
        ]
        
        if request.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {request.content_type}"
            )
        
        # Create document record in database
        document_data = {
            "id": document_id,
            "filename": request.filename,
            "content_type": request.content_type,
            "size_bytes": 0,  # Will be updated after upload
            "user_id": current_user["uid"],
            "jurisdiction": request.jurisdiction,
            "user_role": request.user_role,
            "processing_status": "pending_upload",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to database
        document = await document_service.create_document(db, document_data)
        
        # Generate signed upload URL
        storage_path = f"documents/{current_user['uid']}/{document_id}/{request.filename}"
        upload_url, expires_at = await storage_service.generate_signed_upload_url(
            storage_path,
            content_type=request.content_type,
            expires_in=3600  # 1 hour
        )
        
        response_data = DocumentUploadResponse(
            document_id=document_id,
            upload_url=upload_url,
            expires_at=expires_at,
            processing_status="pending_upload"
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Document upload URL created successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create document upload: {str(e)}"
        )


@router.post("/documents/{document_id}/upload-complete")
async def confirm_document_upload(
    document_id: str,
    file_size: int = Form(..., description="Uploaded file size in bytes"),
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Confirm document upload completion and start processing.
    
    This endpoint should be called after the file has been successfully
    uploaded to the signed URL to update the document status and start processing.
    """
    try:
        # Update document with file size and status
        document = await document_service.get_document(db, document_id, current_user["uid"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update document status
        update_data = {
            "size_bytes": file_size,
            "processing_status": "queued",
            "storage_url": f"documents/{current_user['uid']}/{document_id}/{document.filename}",
            "updated_at": datetime.utcnow()
        }
        
        await document_service.update_document(db, document_id, update_data)
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            current_user["uid"],
            db
        )
        
        return ApiResponse(
            success=True,
            data={"document_id": document_id, "status": "queued"},
            message="Document upload confirmed, processing started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm upload: {str(e)}"
        )


# Document Processing Endpoints
@router.post("/documents/{document_id}/process", response_model=ApiResponse[DocumentAnalysisResponse])
async def process_document(
    document_id: str,
    request: DocumentProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Start or restart document processing with OCR and analysis.
    
    This endpoint triggers OCR processing using Google Cloud Document AI
    and subsequent legal analysis of the document.
    """
    try:
        # Get document from database
        document = await document_service.get_document(db, document_id, current_user["uid"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if already processing
        if document.processing_status == "processing" and not request.force_reprocess:
            raise HTTPException(
                status_code=409,
                detail="Document is already being processed"
            )
        
        # Update status to processing
        await document_service.update_document(
            db, 
            document_id, 
            {
                "processing_status": "processing",
                "updated_at": datetime.utcnow()
            }
        )
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            current_user["uid"],
            db,
            request.ocr_options
        )
        
        response_data = DocumentAnalysisResponse(
            document_id=document_id,
            analysis_status="processing",
            ocr_result=None,
            metadata=None,
            processing_time=None
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Document processing started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start processing: {str(e)}"
        )


@router.get("/documents/{document_id}/status")
async def get_document_processing_status(
    document_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get current processing status of a document.
    """
    try:
        document = await document_service.get_document(db, document_id, current_user["uid"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get processing progress if available
        progress = await document_service.get_processing_progress(db, document_id)
        
        return ApiResponse(
            success=True,
            data={
                "document_id": document_id,
                "status": document.processing_status,
                "progress": progress,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None
            },
            message="Processing status retrieved"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


# Document Retrieval Endpoints
@router.get("/documents", response_model=ApiResponse[List[Document]])
async def get_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Documents per page"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get user's documents with pagination and filtering.
    """
    try:
        # Get documents from database
        documents, total = await document_service.get_user_documents(
            db,
            user_id=current_user["uid"],
            page=page,
            per_page=per_page,
            status_filter=status
        )
        
        return ApiResponse(
            success=True,
            data=documents,
            message=f"Retrieved {len(documents)} documents",
            metadata={
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=ApiResponse[ProcessedDocument])
async def get_document(
    document_id: str,
    include_analysis: bool = Query(True, description="Include analysis results"),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get a specific document with optional analysis results.
    """
    try:
        document = await document_service.get_processed_document(
            db, 
            document_id, 
            current_user["uid"],
            include_analysis=include_analysis
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return ApiResponse(
            success=True,
            data=document,
            message="Document retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get signed download URL for document file.
    """
    try:
        document = await document_service.get_document(db, document_id, current_user["uid"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.storage_url:
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Generate signed download URL
        download_url = await storage_service.generate_signed_download_url(
            document.storage_url,
            expires_in=3600  # 1 hour
        )
        
        return ApiResponse(
            success=True,
            data={"download_url": download_url},
            message="Download URL generated"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its associated files.
    """
    try:
        document = await document_service.get_document(db, document_id, current_user["uid"])
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from storage
        if document.storage_url:
            await storage_service.delete_file(document.storage_url)
        
        # Delete from database
        await document_service.delete_document(db, document_id)
        
        return ApiResponse(
            success=True,
            data={"document_id": document_id},
            message="Document deleted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


# Background Processing Function
async def process_document_background(
    document_id: str,
    user_id: str,
    db: Session,
    ocr_options: Optional[Dict[str, Any]] = None
):
    """
    Background task for processing documents with OCR and analysis.
    """
    try:
        start_time = datetime.utcnow()
        
        # Get document
        document = await document_service.get_document(db, document_id, user_id)
        if not document:
            return
        
        # Download file from storage
        file_content = await storage_service.download_file(document.storage_url)
        
        # Perform OCR using Google Cloud Document AI
        ocr_result = await ocr_service.process_document(
            file_content,
            document.content_type,
            options=ocr_options or {}
        )
        
        # Extract metadata
        metadata = await document_service.extract_metadata(file_content, document.content_type)
        
        # Update document with OCR results
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        update_data = {
            "processing_status": "completed",
            "structured_text": ocr_result.text,
            "metadata": metadata.dict() if metadata else None,
            "processing_time": processing_time,
            "updated_at": datetime.utcnow()
        }
        
        await document_service.update_document(db, document_id, update_data)
        
        # Store OCR result separately
        await document_service.store_ocr_result(db, document_id, ocr_result)
        
        # TODO: Start legal analysis processing
        # This would trigger clause extraction, risk assessment, etc.
        
    except Exception as e:
        # Update document status to failed
        await document_service.update_document(
            db,
            document_id,
            {
                "processing_status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }
        )
        print(f"Document processing failed for {document_id}: {str(e)}")