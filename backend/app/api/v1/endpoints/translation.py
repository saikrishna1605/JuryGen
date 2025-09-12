"""
Translation API endpoints for multi-language content translation.

This module provides endpoints for:
- Text translation with language detection
- Language detection and supported languages
- Translation history
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from ....core.security import require_auth
from ....models.base import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])


# Request/Response Models
class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language code (e.g., 'es', 'fr', 'de')")
    source_language: Optional[str] = Field(default=None, description="Source language code (auto-detected if None)")


class TranslationResponse(BaseModel):
    """Translation response model."""
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")
    confidence: float = Field(..., description="Translation confidence")
    quality_score: float = Field(..., description="Quality score")
    processing_time: float = Field(..., description="Processing time in seconds")
    cached: bool = Field(..., description="Whether result was cached")
    alternatives: List[str] = Field(default_factory=list, description="Alternative translations")
    created_at: str = Field(..., description="Creation timestamp")


class SupportedLanguage(BaseModel):
    """Supported language model."""
    code: str = Field(..., description="Language code")
    name: str = Field(..., description="Language name")
    native_name: Optional[str] = Field(default=None, description="Native language name")


class LanguageDetectionResponse(BaseModel):
    """Language detection response."""
    language: str = Field(..., description="Detected language code")
    confidence: float = Field(..., description="Detection confidence")


class TranslationHistoryItem(BaseModel):
    """Translation history item."""
    id: str = Field(..., description="Translation ID")
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")
    created_at: str = Field(..., description="Creation timestamp")
    confidence: float = Field(..., description="Translation confidence")


# Translation Endpoints
@router.post("/translate", response_model=ApiResponse[TranslationResponse])
async def translate_text(
    request: TranslationRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Translate text to target language.
    
    Translate a single text from source language to target language.
    """
    try:
        logger.info(f"Translating text to {request.target_language}: {request.text[:100]}...")
        
        # Mock translation for now
        response_data = TranslationResponse(
            original_text=request.text,
            translated_text=f"[Translated to {request.target_language}] {request.text}",
            source_language=request.source_language or "auto",
            target_language=request.target_language,
            confidence=0.95,
            quality_score=0.92,
            processing_time=0.1,
            cached=False,
            alternatives=[],
            created_at=datetime.utcnow().isoformat()
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Translation completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


# Language Detection
@router.post("/detect", response_model=ApiResponse[LanguageDetectionResponse])
async def detect_language_simple(
    request: dict,
    current_user: dict = Depends(require_auth)
):
    """
    Detect the language of the given text (simplified endpoint).
    
    Analyze text to determine its language with confidence scoring.
    """
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is required for language detection"
            )
            
        logger.info(f"Detecting language for text: {text[:100]}...")
        
        # Mock language detection for now
        mock_result = {
            "language": "en",
            "confidence": 0.95
        }
        
        response_data = LanguageDetectionResponse(
            language=mock_result["language"],
            confidence=mock_result["confidence"],
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Language detected: {mock_result['language']} (confidence: {mock_result['confidence']:.2f})"
        )
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {str(e)}"
        )


# Language Management
@router.get("/languages", response_model=ApiResponse[List[SupportedLanguage]])
async def get_languages(
    target_language: str = Query(default="en", description="Language for language names"),
    current_user: dict = Depends(require_auth)
):
    """
    Get list of supported languages for translation.
    
    Retrieve all supported languages with their codes and names
    in the specified target language.
    """
    try:
        # Return mock data for now since translation service might not be available
        mock_languages = [
            {"code": "auto", "name": "Auto-detect"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ar", "name": "Arabic"},
            {"code": "hi", "name": "Hindi"}
        ]
        
        response_data = [
            SupportedLanguage(code=lang["code"], name=lang["name"])
            for lang in mock_languages
        ]
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Retrieved {len(response_data)} supported languages"
        )
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported languages: {str(e)}"
        )


# Translation History
@router.get("/history", response_model=ApiResponse[List[TranslationHistoryItem]])
async def get_translation_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of items"),
    current_user: dict = Depends(require_auth)
):
    """
    Get user's translation history.
    
    Retrieve recent translations performed by the user.
    """
    try:
        # Mock translation history for now
        mock_history = [
            {
                "id": "trans_1",
                "original_text": "Hello, how are you?",
                "translated_text": "Hola, ¿cómo estás?",
                "source_language": "en",
                "target_language": "es",
                "created_at": "2024-01-15T10:30:00Z",
                "confidence": 0.98
            },
            {
                "id": "trans_2", 
                "original_text": "This is a legal document",
                "translated_text": "Este es un documento legal",
                "source_language": "en",
                "target_language": "es",
                "created_at": "2024-01-15T09:15:00Z",
                "confidence": 0.95
            }
        ]
        
        # Apply limit
        limited_history = mock_history[:limit]
        
        response_data = [
            TranslationHistoryItem(**item)
            for item in limited_history
        ]
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Retrieved {len(response_data)} translation history items"
        )
        
    except Exception as e:
        logger.error(f"Error getting translation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get translation history: {str(e)}"
        )