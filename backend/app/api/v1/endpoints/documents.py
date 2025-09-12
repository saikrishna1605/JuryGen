"""
Documents API endpoints for Legal Companion.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....core.security import require_auth
from ....models.base import ApiResponse
from ....models.document import Document, DocumentSummary

router = APIRouter()


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[Document] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Documents per page")


@router.get("/documents", response_model=ApiResponse[List[Document]])
async def get_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Documents per page"),
    current_user: dict = Depends(require_auth)
):
    """
    Get user's documents with pagination.
    
    Args:
        page: Page number (1-based)
        per_page: Number of documents per page
        current_user: Authenticated user
        
    Returns:
        ApiResponse with list of documents
    """
    try:
        # For now, return mock data since we don't have a database connection
        # In a real implementation, this would query the database
        mock_documents = [
            {
                "id": "doc_1",
                "filename": "contract_example.pdf",
                "upload_date": "2024-01-15T10:30:00Z",
                "status": "processed",
                "file_size": 1024000,
                "content_type": "application/pdf",
                "user_id": current_user["uid"],
                "analysis_complete": True,
                "risk_level": "medium",
                "summary": "Employment contract with standard terms"
            },
            {
                "id": "doc_2", 
                "filename": "lease_agreement.pdf",
                "upload_date": "2024-01-14T15:45:00Z",
                "status": "processed",
                "file_size": 2048000,
                "content_type": "application/pdf",
                "user_id": current_user["uid"],
                "analysis_complete": True,
                "risk_level": "low",
                "summary": "Residential lease agreement"
            }
        ]
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_docs = mock_documents[start_idx:end_idx]
        
        return ApiResponse(
            success=True,
            data=paginated_docs,
            message=f"Retrieved {len(paginated_docs)} documents"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=ApiResponse[Document])
async def get_document(
    document_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document identifier
        current_user: Authenticated user
        
    Returns:
        ApiResponse with document details
    """
    try:
        # Mock document data
        mock_document = {
            "id": document_id,
            "filename": "example_document.pdf",
            "upload_date": "2024-01-15T10:30:00Z",
            "status": "processed",
            "file_size": 1024000,
            "content_type": "application/pdf",
            "user_id": current_user["uid"],
            "analysis_complete": True,
            "risk_level": "medium",
            "summary": "Legal document with detailed analysis available",
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
            data=mock_document,
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
    Download a document file.
    
    Args:
        document_id: Document identifier
        current_user: Authenticated user
        
    Returns:
        File download response
    """
    try:
        # In a real implementation, this would serve the actual file
        # For now, return a placeholder response
        raise HTTPException(
            status_code=501,
            detail="Document download not implemented in minimal mode"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download document: {str(e)}"
        )