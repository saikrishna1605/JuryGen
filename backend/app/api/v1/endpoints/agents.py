"""
Agent-specific API endpoints for direct agent interactions.

This module provides endpoints for:
- Direct summarizer agent calls
- Individual agent testing and debugging
- Agent-specific configuration and status
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ....core.security import require_auth
from ....core.exceptions import AnalysisError
from ....models.base import ApiResponse, UserRole, ReadingLevel
from ....models.document import DocumentSummary
from ....models.analysis import SummarizationRequest, SummarizationResponse
from ....agents.summarizer_agent import SummarizerAgent
from ....services.firestore import FirestoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Initialize services
summarizer_agent = SummarizerAgent()
firestore_service = FirestoreService()


@router.post("/summarizer/summarize")
async def summarize_document(
    document_id: UUID,
    user_role: Optional[UserRole] = None,
    jurisdiction: Optional[str] = None,
    reading_level: ReadingLevel = ReadingLevel.MIDDLE,
    tone: str = "neutral",
    clause_analysis: Optional[list] = None,
    current_user: dict = Depends(require_auth)
) -> ApiResponse:
    """
    Create a plain language summary of a legal document.
    
    This endpoint is primarily used by Cloud Workflows but can also be called
    directly for testing or custom integrations.
    
    Args:
        document_id: ID of the document to summarize
        user_role: User's role for perspective
        jurisdiction: Legal jurisdiction for context
        reading_level: Target reading level for the summary
        tone: Desired tone (neutral, friendly, formal)
        clause_analysis: Pre-analyzed clauses (optional)
        current_user: Authenticated user information
        
    Returns:
        ApiResponse with DocumentSummary data
    """
    try:
        logger.info(f"Creating summary for document {document_id}")
        
        # Get document from Firestore
        document = await firestore_service.get_document_raw(str(document_id))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify user owns the document
        if document.get("user_id") != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to document"
            )
        
        # Get document text
        structured_text = document.get("structured_text")
        if not structured_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has not been processed for OCR yet"
            )
        
        # Get clauses if not provided
        clauses = clause_analysis
        if not clauses:
            # Fetch clauses from Firestore
            clauses_data = await firestore_service.get_document_clauses(str(document_id))
            clauses = clauses_data or []
        
        # Create summary using the summarizer agent
        summary = await summarizer_agent.create_summary(
            document_text=structured_text,
            clauses=clauses,
            user_role=user_role,
            reading_level=reading_level,
            tone=tone,
            jurisdiction=jurisdiction
        )
        
        # Store summary in Firestore
        await firestore_service.update_document_fields(
            str(document_id),
            {"summary": summary.model_dump()}
        )
        
        logger.info(f"Summary created successfully for document {document_id}")
        
        return ApiResponse(
            success=True,
            data=summary.model_dump(),
            message="Summary created successfully"
        )
        
    except HTTPException:
        raise
    except AnalysisError as e:
        logger.error(f"Analysis error during summarization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Summarization failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during summarization"
        )


@router.post("/summarizer/adjust-tone")
async def adjust_summary_tone(
    document_id: UUID,
    new_tone: str,
    new_reading_level: Optional[ReadingLevel] = None,
    current_user: dict = Depends(require_auth)
) -> ApiResponse:
    """
    Adjust the tone and/or reading level of an existing summary.
    
    Args:
        document_id: ID of the document with existing summary
        new_tone: New tone to apply (neutral, friendly, formal, etc.)
        new_reading_level: New reading level (optional)
        current_user: Authenticated user information
        
    Returns:
        ApiResponse with adjusted DocumentSummary
    """
    try:
        logger.info(f"Adjusting summary tone for document {document_id}")
        
        # Get document from Firestore
        document = await firestore_service.get_document_raw(str(document_id))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify user owns the document
        if document.get("user_id") != current_user["uid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to document"
            )
        
        # Get existing summary
        summary_data = document.get("summary")
        if not summary_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document does not have an existing summary"
            )
        
        # Convert to DocumentSummary object
        original_summary = DocumentSummary(**summary_data)
        
        # Adjust the summary
        adjusted_summary = await summarizer_agent.adjust_summary_tone(
            original_summary=original_summary,
            new_tone=new_tone,
            new_reading_level=new_reading_level
        )
        
        # Update summary in Firestore
        await firestore_service.update_document_fields(
            str(document_id),
            {"summary": adjusted_summary.model_dump()}
        )
        
        logger.info(f"Summary tone adjusted successfully for document {document_id}")
        
        return ApiResponse(
            success=True,
            data=adjusted_summary.model_dump(),
            message="Summary tone adjusted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting summary tone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during tone adjustment"
        )


@router.post("/summarizer/custom-summary")
async def create_custom_summary(
    request: SummarizationRequest,
    current_user: dict = Depends(require_auth)
) -> SummarizationResponse:
    """
    Create a custom summary from provided text.
    
    This endpoint allows for direct text summarization without requiring
    a stored document. Useful for testing or custom integrations.
    
    Args:
        request: Summarization request with text and options
        current_user: Authenticated user information
        
    Returns:
        SummarizationResponse with summary results
    """
    try:
        logger.info("Creating custom summary from provided text")
        
        # Validate request
        if len(request.text.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text too short for meaningful summarization"
            )
        
        # Create a basic summary using the summarizer agent
        # Note: This bypasses clause analysis since we don't have structured clauses
        summary = await summarizer_agent.create_summary(
            document_text=request.text,
            clauses=[],  # Empty clauses list for custom text
            reading_level=ReadingLevel(request.reading_level),
            tone="neutral"
        )
        
        # Calculate compression ratio
        original_words = len(request.text.split())
        summary_words = len(summary.plain_language.split())
        compression_ratio = original_words / summary_words if summary_words > 0 else 1.0
        
        # Extract main topics (simplified)
        topics = []
        if summary.document_type:
            topics.append(summary.document_type)
        
        response = SummarizationResponse(
            summary=summary.plain_language,
            key_points=summary.key_points,
            word_count=summary.word_count,
            reading_level=request.reading_level,
            compression_ratio=compression_ratio,
            topics=topics,
            confidence=0.85  # Default confidence for custom summaries
        )
        
        logger.info("Custom summary created successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during custom summarization"
        )


@router.get("/summarizer/status")
async def get_summarizer_status(
    current_user: dict = Depends(require_auth)
) -> ApiResponse:
    """
    Get the status and capabilities of the summarizer agent.
    
    Returns:
        ApiResponse with summarizer status information
    """
    try:
        # Get basic status information
        status_info = {
            "agent_name": "Summarizer Agent",
            "version": "1.0.0",
            "status": "ready",
            "capabilities": [
                "plain_language_conversion",
                "reading_level_control", 
                "key_points_extraction",
                "tone_adjustment",
                "document_type_classification"
            ],
            "supported_reading_levels": [level.value for level in ReadingLevel],
            "supported_tones": ["neutral", "friendly", "formal", "collaborative", "strict"],
            "model_info": {
                "primary_model": "gemini-1.5-pro",
                "backup_model": "gemini-1.5-flash"
            }
        }
        
        return ApiResponse(
            success=True,
            data=status_info,
            message="Summarizer agent status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting summarizer status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving status"
        )