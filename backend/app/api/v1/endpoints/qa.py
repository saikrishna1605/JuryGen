"""
Q&A API endpoints for voice-to-voice legal document interactions.

This module provides endpoints for:
- Voice-to-voice Q&A interactions
- Text-based Q&A processing
- Session management and conversation history
- Context retrieval and management
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel, Field

from ....core.security import require_auth
from ....models.base import ApiResponse
from ....services.qa_service import qa_service, QAResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])


# Request/Response Models
class TextQuestionRequest(BaseModel):
    question: str = Field(..., description="The question to ask about the document")
    document_id: str = Field(..., description="ID of the document to query")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")


class VoiceQuestionRequest(BaseModel):
    document_id: str = Field(..., description="ID of the document to query")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    language_code: str = Field(default="en-US", description="Language code for speech processing")
    voice_settings: Optional[Dict[str, Any]] = Field(default=None, description="Voice synthesis settings")


class QAResponseModel(BaseModel):
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    audio_response: Optional[Dict[str, Any]]
    processing_time: float
    context_used: List[str]
    created_at: str


class ConversationHistory(BaseModel):
    interactions: List[Dict[str, Any]]
    session_id: str
    document_id: str
    total_interactions: int


# Text-based Q&A Endpoints

@router.post("/ask", response_model=ApiResponse[QAResponseModel])
async def ask_text_question(
    request: TextQuestionRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Ask a text question about a legal document.
    
    Process a text-based question and return a comprehensive answer
    based on the document content and analysis.
    """
    try:
        logger.info(f"Processing text question: {request.question[:100]}...")
        
        # Process the question
        response = await qa_service.process_text_question(
            question=request.question,
            document_id=request.document_id,
            user_id=current_user["uid"],
            session_id=request.session_id
        )
        
        response_data = QAResponseModel(
            question=response.question,
            answer=response.answer,
            confidence=response.confidence,
            sources=response.sources,
            audio_response=response.audio_response.to_dict() if response.audio_response else None,
            processing_time=response.processing_time,
            context_used=response.context_used,
            created_at=response.created_at.isoformat()
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Question processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Text Q&A error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


# Voice-based Q&A Endpoints

@router.post("/ask-voice", response_model=ApiResponse[QAResponseModel])
async def ask_voice_question(
    audio_file: UploadFile = File(..., description="Audio file containing the question"),
    document_id: str = Form(..., description="ID of the document to query"),
    session_id: Optional[str] = Form(default=None, description="Session ID for conversation continuity"),
    language_code: str = Form(default="en-US", description="Language code for speech processing"),
    voice_gender: str = Form(default="NEUTRAL", description="Voice gender for response"),
    speaking_rate: float = Form(default=1.0, description="Speaking rate for response"),
    current_user: dict = Depends(require_auth)
):
    """
    Ask a voice question about a legal document.
    
    Upload an audio file containing a question and receive both text
    and audio responses based on the document content.
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Read audio data
        audio_data = await audio_file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty"
            )
        
        logger.info(f"Processing voice question from file: {audio_file.filename}")
        
        # Prepare voice settings
        voice_settings = {
            "voice_gender": voice_gender,
            "speaking_rate": speaking_rate,
            "audio_format": "MP3"
        }
        
        # Process the voice question
        response = await qa_service.process_voice_question(
            audio_data=audio_data,
            document_id=document_id,
            user_id=current_user["uid"],
            session_id=session_id,
            language_code=language_code,
            voice_settings=voice_settings
        )
        
        response_data = QAResponseModel(
            question=response.question,
            answer=response.answer,
            confidence=response.confidence,
            sources=response.sources,
            audio_response=response.audio_response.to_dict() if response.audio_response else None,
            processing_time=response.processing_time,
            context_used=response.context_used,
            created_at=response.created_at.isoformat()
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Voice question processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice Q&A error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice question: {str(e)}"
        )


@router.post("/ask-voice-stream", response_model=ApiResponse[QAResponseModel])
async def ask_voice_question_streaming(
    request: VoiceQuestionRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Ask a voice question with streaming audio input.
    
    This endpoint is designed for real-time voice interactions
    where audio is streamed rather than uploaded as a file.
    """
    try:
        # This would be implemented for streaming audio
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Streaming voice Q&A not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming voice Q&A error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process streaming voice question: {str(e)}"
        )


# Session Management Endpoints

@router.get("/sessions/{document_id}/history", response_model=ApiResponse[ConversationHistory])
async def get_conversation_history(
    document_id: UUID,
    session_id: str = Query(..., description="Session ID"),
    current_user: dict = Depends(require_auth)
):
    """
    Get conversation history for a Q&A session.
    
    Retrieve the complete conversation history for a specific
    document and session.
    """
    try:
        history = await qa_service.get_session_history(
            document_id=str(document_id),
            user_id=current_user["uid"],
            session_id=session_id
        )
        
        conversation_data = ConversationHistory(
            interactions=history,
            session_id=session_id,
            document_id=str(document_id),
            total_interactions=len(history)
        )
        
        return ApiResponse(
            success=True,
            data=conversation_data,
            message=f"Retrieved {len(history)} conversation interactions"
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@router.delete("/sessions/{document_id}/clear")
async def clear_conversation_session(
    document_id: UUID,
    session_id: str = Query(..., description="Session ID"),
    current_user: dict = Depends(require_auth)
):
    """
    Clear a conversation session.
    
    Delete all conversation history and context for a specific session.
    """
    try:
        await qa_service.clear_session(
            document_id=str(document_id),
            user_id=current_user["uid"],
            session_id=session_id
        )
        
        return ApiResponse(
            success=True,
            data={"session_id": session_id, "document_id": str(document_id)},
            message="Conversation session cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )


# Utility Endpoints

@router.post("/suggest-questions", response_model=ApiResponse[List[str]])
async def suggest_questions(
    document_id: str = Form(..., description="ID of the document"),
    context: Optional[str] = Form(default=None, description="Additional context"),
    current_user: dict = Depends(require_auth)
):
    """
    Suggest relevant questions for a document.
    
    Generate a list of suggested questions that users might want
    to ask about the document based on its content and analysis.
    """
    try:
        # This would analyze the document and generate relevant questions
        # For now, return some common legal document questions
        suggested_questions = [
            "What are the main obligations in this document?",
            "What are the key risks I should be aware of?",
            "Are there any important deadlines or dates?",
            "What happens if I want to terminate this agreement?",
            "What are the payment terms and conditions?",
            "Are there any penalties or fees mentioned?",
            "What are my rights under this agreement?",
            "Can you explain the most complex clauses in simple terms?",
        ]
        
        return ApiResponse(
            success=True,
            data=suggested_questions,
            message="Generated suggested questions"
        )
        
    except Exception as e:
        logger.error(f"Error generating suggested questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggested questions: {str(e)}"
        )


@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def qa_health_check():
    """
    Check the health of the Q&A service.
    
    Perform health checks on the Q&A processing pipeline
    and return service status information.
    """
    try:
        health_data = await qa_service.health_check()
        
        return ApiResponse(
            success=True,
            data=health_data,
            message="Q&A service health check completed"
        )
        
    except Exception as e:
        logger.error(f"Q&A health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A health check failed: {str(e)}"
        )