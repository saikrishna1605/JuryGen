"""
Simplified Documents API endpoints for Legal Companion.
Provides basic document management without complex dependencies.
"""

import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ....core.security import require_auth
from ....models.base import ApiResponse

router = APIRouter()


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str = Field(..., description="Unique document identifier")
    upload_url: str = Field(..., description="Signed URL for file upload")
    expires_at: str = Field(..., description="Upload URL expiration time")
    processing_status: str = Field(..., description="Initial processing status")


class DocumentInfo(BaseModel):
    """Basic document information."""
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    upload_date: str = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Processing status")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    user_id: str = Field(..., description="Owner user ID")
    analysis_complete: bool = Field(..., description="Whether analysis is complete")
    risk_level: Optional[str] = Field(default=None, description="Risk assessment level")
    summary: Optional[str] = Field(default=None, description="Document summary")


# In-memory storage for development (replace with database in production)
documents_store: Dict[str, Dict[str, Any]] = {}


@router.post("/documents/upload", response_model=ApiResponse[DocumentUploadResponse])
async def create_document_upload(
    filename: str,
    content_type: str,
    current_user: dict = Depends(require_auth)
):
    """
    Create a new document upload URL.
    
    This is a simplified version that creates a mock upload URL.
    In production, this would integrate with Google Cloud Storage.
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
        
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type}"
            )
        
        # Store document info
        documents_store[document_id] = {
            "id": document_id,
            "filename": filename,
            "content_type": content_type,
            "user_id": current_user["uid"],
            "status": "pending_upload",
            "created_at": datetime.utcnow().isoformat(),
            "file_size": 0,
            "analysis_complete": False
        }
        
        # Generate mock upload URL
        upload_url = f"https://mock-storage.example.com/upload/{document_id}/{filename}"
        expires_at = datetime.utcnow().isoformat()
        
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
    file_size: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth)
):
    """
    Confirm document upload completion and start processing.
    """
    try:
        if document_id not in documents_store:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = documents_store[document_id]
        if doc["user_id"] != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update document info
        doc.update({
            "file_size": file_size,
            "status": "processing",
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Start mock processing
        background_tasks.add_task(mock_process_document, document_id)
        
        return ApiResponse(
            success=True,
            data={"document_id": document_id, "status": "processing"},
            message="Document upload confirmed, processing started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm upload: {str(e)}"
        )


@router.get("/documents", response_model=ApiResponse[List[DocumentInfo]])
async def get_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Documents per page"),
    # current_user: dict = Depends(require_auth)  # Temporarily disabled for CORS testing
):
    """
    Get user's documents with pagination.
    """
    try:
        # For testing without auth, return mock documents
        user_docs = []
        
        # Add mock documents for testing
        if True:  # Always show mock documents for testing
            mock_docs = [
                {
                    "id": "doc_1",
                    "filename": "contract_example.pdf",
                    "upload_date": "2024-01-15T10:30:00Z",
                    "status": "completed",
                    "file_size": 1024000,
                    "content_type": "application/pdf",
                    "user_id": "test_user",
                    "analysis_complete": True,
                    "risk_level": "medium",
                    "summary": "Employment contract with standard terms"
                },
                {
                    "id": "doc_2", 
                    "filename": "lease_agreement.pdf",
                    "upload_date": "2024-01-14T15:45:00Z",
                    "status": "completed",
                    "file_size": 2048000,
                    "content_type": "application/pdf",
                    "user_id": "test_user",
                    "analysis_complete": True,
                    "risk_level": "low",
                    "summary": "Residential lease agreement"
                }
            ]
            user_docs = mock_docs
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_docs = user_docs[start_idx:end_idx]
        
        # Convert to DocumentInfo objects
        document_list = []
        for doc in paginated_docs:
            document_list.append(DocumentInfo(
                id=doc["id"],
                filename=doc["filename"],
                upload_date=doc.get("upload_date", doc.get("created_at", "")),
                status=doc["status"],
                file_size=doc["file_size"],
                content_type=doc["content_type"],
                user_id=doc["user_id"],
                analysis_complete=doc.get("analysis_complete", False),
                risk_level=doc.get("risk_level"),
                summary=doc.get("summary")
            ))
        
        return ApiResponse(
            success=True,
            data=document_list,
            message=f"Retrieved {len(document_list)} documents"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Get a specific document by ID.
    """
    try:
        # Check if document exists in store
        if document_id in documents_store:
            doc = documents_store[document_id]
            if doc["user_id"] != current_user["uid"]:
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            # Return mock document for demo
            doc = {
                "id": document_id,
                "filename": "example_document.pdf",
                "upload_date": "2024-01-15T10:30:00Z",
                "status": "completed",
                "file_size": 1024000,
                "content_type": "application/pdf",
                "user_id": current_user["uid"],
                "analysis_complete": True,
                "risk_level": "medium",
                "summary": "Legal document with detailed analysis available",
                "structured_text": "This is the extracted text from the document...",
                "clauses": [
                    {
                        "id": "clause_1",
                        "text": "This is a sample clause for demonstration",
                        "risk_level": "low",
                        "explanation": "Standard contractual language"
                    }
                ]
            }
        
        return ApiResponse(
            success=True,
            data=doc,
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
    current_user: dict = Depends(require_auth)
):
    """
    Get download URL for document file.
    """
    try:
        # Mock download URL
        download_url = f"https://mock-storage.example.com/download/{document_id}"
        
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


@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth)
):
    """
    Start document processing with OCR and analysis.
    """
    try:
        if document_id not in documents_store:
            # Create mock document for processing
            documents_store[document_id] = {
                "id": document_id,
                "filename": "document.pdf",
                "content_type": "application/pdf",
                "user_id": current_user["uid"],
                "status": "processing",
                "created_at": datetime.utcnow().isoformat(),
                "file_size": 1024000,
                "analysis_complete": False
            }
        
        doc = documents_store[document_id]
        if doc["user_id"] != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update status
        doc["status"] = "processing"
        doc["updated_at"] = datetime.utcnow().isoformat()
        
        # Start mock processing
        background_tasks.add_task(mock_process_document, document_id)
        
        return ApiResponse(
            success=True,
            data={
                "document_id": document_id,
                "status": "processing",
                "message": "OCR and analysis started"
            },
            message="Document processing started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start processing: {str(e)}"
        )


async def mock_process_document(document_id: str):
    """
    Mock document processing function.
    
    In production, this would:
    1. Download the file from storage
    2. Process with Google Cloud Document AI for OCR
    3. Analyze the text for legal clauses and risks
    4. Store results in database
    """
    import asyncio
    
    # Simulate processing time
    await asyncio.sleep(5)
    
    if document_id in documents_store:
        doc = documents_store[document_id]
        doc.update({
            "status": "completed",
            "analysis_complete": True,
            "risk_level": "medium",
            "summary": "Document processed successfully with OCR and legal analysis",
            "structured_text": """
            LEGAL DOCUMENT ANALYSIS COMPLETE
            
            This document has been processed using Google Cloud Document AI for OCR
            and analyzed for legal content including:
            
            - Contract clauses identification
            - Risk assessment
            - Plain language summary
            - Key terms extraction
            
            Processing completed successfully.
            """,
            "updated_at": datetime.utcnow().isoformat(),
            "processing_time": 5.0
        })
        
        print(f"Mock processing completed for document {document_id}")