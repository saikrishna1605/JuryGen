"""
Translation API endpoints for multi-language content translation.

This module provides endpoints for:
- Text translation with language detection
- Batch translation for multiple texts
- Document section translation
- Language detection and supported languages
- Translation caching and optimization
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from pydantic import BaseModel, Field

from ....core.security import require_auth
from ....models.base import ApiResponse
from ....services.translation_service import translation_service, TranslationResult, BatchTranslationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])


# Request/Response Models
class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language code (e.g., 'es', 'fr', 'de')")
    source_language: Optional[str] = Field(default=None, description="Source language code (auto-detected if None)")
    use_cache: bool = Field(default=True, description="Whether to use translation cache")
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum quality score")


class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to translate")
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(default=None, description="Source language code")
    use_cache: bool = Field(default=True, description="Whether to use translation cache")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="Maximum concurrent translations")


class DocumentSectionRequest(BaseModel):
    sections: Dict[str, str] = Field(..., description="Dictionary of section_id -> text")
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(default=None, description="Source language code")
    preserve_formatting: bool = Field(default=True, description="Whether to preserve text formatting")


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    quality_score: float
    processing_time: float
    cached: bool
    alternatives: List[str]
    created_at: str


class BatchTranslationResponse(BaseModel):
    translations: List[TranslationResponse]
    total_processing_time: float
    success_count: int
    failure_count: int
    cache_hit_count: int
    cache_hit_rate: float
    created_at: str


class LanguageDetectionResponse(BaseModel):
    language: str
    confidence: float
    is_reliable: bool
    input_text: str


class SupportedLanguage(BaseModel):
    code: str
    name: str


# Translation Endpoints

@router.post("/translate", response_model=ApiResponse[TranslationResponse])
async def translate_text(
    request: TranslationRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Translate text to target language.
    
    Translate a single text from source language to target language
    with optional caching and quality scoring.
    """
    try:
        logger.info(f"Translating text to {request.target_language}: {request.text[:100]}...")
        
        # Perform translation
        result = await translation_service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
            use_cache=request.use_cache,
            quality_threshold=request.quality_threshold
        )
        
        response_data = TranslationResponse(
            original_text=result.original_text,
            translated_text=result.translated_text,
            source_language=result.source_language,
            target_language=result.target_language,
            confidence=result.confidence,
            quality_score=result.quality_score,
            processing_time=result.processing_time,
            cached=result.cached,
            alternatives=result.alternatives,
            created_at=result.created_at.isoformat()
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Text translated successfully"
        )
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/translate-batch", response_model=ApiResponse[BatchTranslationResponse])
async def translate_batch(
    request: BatchTranslationRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Translate multiple texts in batch.
    
    Efficiently translate multiple texts with concurrent processing
    and caching for optimal performance.
    """
    try:
        if len(request.texts) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 texts allowed per batch"
            )
        
        logger.info(f"Batch translating {len(request.texts)} texts to {request.target_language}")
        
        # Perform batch translation
        result = await translation_service.translate_batch(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language,
            use_cache=request.use_cache,
            max_concurrent=request.max_concurrent
        )
        
        response_data = BatchTranslationResponse(
            translations=[
                TranslationResponse(
                    original_text=t.original_text,
                    translated_text=t.translated_text,
                    source_language=t.source_language,
                    target_language=t.target_language,
                    confidence=t.confidence,
                    quality_score=t.quality_score,
                    processing_time=t.processing_time,
                    cached=t.cached,
                    alternatives=t.alternatives,
                    created_at=t.created_at.isoformat()
                )
                for t in result.translations
            ],
            total_processing_time=result.total_processing_time,
            success_count=result.success_count,
            failure_count=result.failure_count,
            cache_hit_count=result.cache_hit_count,
            cache_hit_rate=result.cache_hit_count / len(request.texts) if request.texts else 0,
            created_at=result.created_at.isoformat()
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Batch translation completed: {result.success_count} success, {result.failure_count} failures"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch translation failed: {str(e)}"
        )


@router.post("/translate-document-sections", response_model=ApiResponse[Dict[str, TranslationResponse]])
async def translate_document_sections(
    request: DocumentSectionRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Translate document sections while preserving structure.
    
    Translate multiple document sections (e.g., clauses, paragraphs)
    while maintaining the document structure and formatting.
    """
    try:
        if len(request.sections) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 sections allowed per request"
            )
        
        logger.info(f"Translating {len(request.sections)} document sections to {request.target_language}")
        
        # Perform document section translation
        results = await translation_service.translate_document_sections(
            sections=request.sections,
            target_language=request.target_language,
            source_language=request.source_language,
            preserve_formatting=request.preserve_formatting
        )
        
        response_data = {
            section_id: TranslationResponse(
                original_text=result.original_text,
                translated_text=result.translated_text,
                source_language=result.source_language,
                target_language=result.target_language,
                confidence=result.confidence,
                quality_score=result.quality_score,
                processing_time=result.processing_time,
                cached=result.cached,
                alternatives=result.alternatives,
                created_at=result.created_at.isoformat()
            )
            for section_id, result in results.items()
        }
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Document sections translated successfully: {len(results)} sections"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document section translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document section translation failed: {str(e)}"
        )


# Language Detection and Management

@router.post("/detect-language", response_model=ApiResponse[LanguageDetectionResponse])
async def detect_language(
    text: str = Form(..., description="Text to analyze for language detection"),
    current_user: dict = Depends(require_auth)
):
    """
    Detect the language of the given text.
    
    Analyze text to determine its language with confidence scoring.
    """
    try:
        logger.info(f"Detecting language for text: {text[:100]}...")
        
        # Perform language detection
        result = await translation_service.detect_language(text)
        
        response_data = LanguageDetectionResponse(
            language=result["language"],
            confidence=result["confidence"],
            is_reliable=result["is_reliable"],
            input_text=result["input_text"]
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Language detected: {result['language']} (confidence: {result['confidence']:.2f})"
        )
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {str(e)}"
        )


@router.get("/supported-languages", response_model=ApiResponse[List[SupportedLanguage]])
async def get_supported_languages(
    target_language: str = Query(default="en", description="Language for language names"),
    current_user: dict = Depends(require_auth)
):
    """
    Get list of supported languages for translation.
    
    Retrieve all supported languages with their codes and names
    in the specified target language.
    """
    try:
        languages = await translation_service.get_supported_languages(target_language)
        
        response_data = [
            SupportedLanguage(code=lang["code"], name=lang["name"])
            for lang in languages
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


# Cache Management

@router.post("/clear-cache")
async def clear_translation_cache(
    older_than_hours: int = Query(default=24, ge=1, le=168, description="Clear entries older than hours"),
    current_user: dict = Depends(require_auth)
):
    """
    Clear translation cache entries.
    
    Remove cached translations older than the specified number of hours
    to free up storage and ensure fresh translations.
    """
    try:
        # TODO: Add admin role check
        await translation_service.clear_cache(older_than_hours)
        
        return ApiResponse(
            success=True,
            data={"older_than_hours": older_than_hours},
            message=f"Translation cache cleared for entries older than {older_than_hours} hours"
        )
        
    except Exception as e:
        logger.error(f"Cache clearing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/cache-stats", response_model=ApiResponse[Dict[str, Any]])
async def get_cache_statistics(
    current_user: dict = Depends(require_auth)
):
    """
    Get translation cache statistics.
    
    Retrieve information about cache usage, hit rates, and performance metrics.
    """
    try:
        stats = await translation_service.get_cache_stats()
        
        return ApiResponse(
            success=True,
            data=stats,
            message="Translation cache statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


# Utility Endpoints

@router.post("/translate-with-alternatives", response_model=ApiResponse[Dict[str, Any]])
async def translate_with_alternatives(
    text: str = Form(..., description="Text to translate"),
    target_language: str = Form(..., description="Target language code"),
    source_language: Optional[str] = Form(default=None, description="Source language code"),
    num_alternatives: int = Form(default=3, ge=1, le=5, description="Number of alternative translations"),
    current_user: dict = Depends(require_auth)
):
    """
    Translate text with multiple alternative translations.
    
    Provide multiple translation options for the same text to give users
    choices and improve translation quality.
    """
    try:
        # This would implement alternative translation generation
        # For now, return the main translation with placeholder alternatives
        
        main_translation = await translation_service.translate_text(
            text=text,
            target_language=target_language,
            source_language=source_language
        )
        
        # Generate placeholder alternatives (in practice, these would be real alternatives)
        alternatives = [
            main_translation.translated_text,
            # Additional alternatives would be generated here
        ]
        
        response_data = {
            "main_translation": TranslationResponse(
                original_text=main_translation.original_text,
                translated_text=main_translation.translated_text,
                source_language=main_translation.source_language,
                target_language=main_translation.target_language,
                confidence=main_translation.confidence,
                quality_score=main_translation.quality_score,
                processing_time=main_translation.processing_time,
                cached=main_translation.cached,
                alternatives=main_translation.alternatives,
                created_at=main_translation.created_at.isoformat()
            ),
            "alternatives": alternatives[:num_alternatives],
            "total_alternatives": len(alternatives)
        }
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Translation with {len(alternatives)} alternatives generated"
        )
        
    except Exception as e:
        logger.error(f"Alternative translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alternative translation failed: {str(e)}"
        )


# Health Check

@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def translation_health_check():
    """
    Check the health of the translation service.
    
    Perform health checks on the translation service and return
    service status and performance metrics.
    """
    try:
        health_data = await translation_service.health_check()
        
        return ApiResponse(
            success=True,
            data=health_data,
            message="Translation service health check completed"
        )
        
    except Exception as e:
        logger.error(f"Translation health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation health check failed: {str(e)}"
        )