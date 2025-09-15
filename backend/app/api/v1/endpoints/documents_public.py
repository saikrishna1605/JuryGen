"""
Public Documents API endpoints for testing (no authentication required).
"""

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class DocumentInfo(BaseModel):
    """Basic document information."""
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    upload_date: str = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Processing status")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    analysis_complete: bool = Field(..., description="Whether analysis is complete")
    risk_level: str = Field(..., description="Risk assessment level")
    summary: str = Field(..., description="Document summary")


class ApiResponse(BaseModel):
    """Standard API response format."""
    success: bool
    data: List[DocumentInfo]
    message: str


@router.get("/documents", response_model=ApiResponse)
async def get_documents_public():
    """
    Get documents without authentication (for testing).
    """
    # Return mock documents
    mock_documents = [
        DocumentInfo(
            id="doc_1",
            filename="contract_example.pdf",
            upload_date="2024-01-15T10:30:00Z",
            status="completed",
            file_size=1024000,
            content_type="application/pdf",
            analysis_complete=True,
            risk_level="medium",
            summary="Employment contract with standard terms and conditions"
        ),
        DocumentInfo(
            id="doc_2",
            filename="lease_agreement.pdf", 
            upload_date="2024-01-14T15:45:00Z",
            status="completed",
            file_size=2048000,
            content_type="application/pdf",
            analysis_complete=True,
            risk_level="low",
            summary="Residential lease agreement with tenant protections"
        ),
        DocumentInfo(
            id="doc_3",
            filename="privacy_policy.pdf",
            upload_date="2024-01-13T09:15:00Z", 
            status="processing",
            file_size=512000,
            content_type="application/pdf",
            analysis_complete=False,
            risk_level="high",
            summary="Privacy policy document currently being analyzed"
        )
    ]
    
    return ApiResponse(
        success=True,
        data=mock_documents,
        message="Documents retrieved successfully"
    )