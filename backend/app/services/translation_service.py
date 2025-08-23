"""
Translation service using Google Cloud Translation API.

This service handles:
- Multi-language content translation
- Language detection and automatic translation
- Translation quality scoring and fallback handling
- Batch translation for multiple texts
- Translation caching and optimization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import json

from google.cloud import translate_v2 as translate
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..core.exceptions import WorkflowError
from ..services.firestore import FirestoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class TranslationResult:
    """Represents a translation result."""
    
    def __init__(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str,
        confidence: float = 1.0,
        quality_score: float = 1.0,
        processing_time: float = 0.0,
        cached: bool = False,
        alternatives: List[str] = None
    ):
        self.original_text = original_text
        self.translated_text = translated_text
        self.source_language = source_language
        self.target_language = target_language
        self.confidence = confidence
        self.quality_score = quality_score
        self.processing_time = processing_time
        self.cached = cached
        self.alternatives = alternatives or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "processing_time": self.processing_time,
            "cached": self.cached,
            "alternatives": self.alternatives,
            "created_at": self.created_at.isoformat(),
        }


class BatchTranslationResult:
    """Represents a batch translation result."""
    
    def __init__(
        self,
        translations: List[TranslationResult],
        total_processing_time: float,
        success_count: int,
        failure_count: int,
        cache_hit_count: int
    ):
        self.translations = translations
        self.total_processing_time = total_processing_time
        self.success_count = success_count
        self.failure_count = failure_count
        self.cache_hit_count = cache_hit_count
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "translations": [t.to_dict() for t in self.translations],
            "total_processing_time": self.total_processing_time,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "cache_hit_count": self.cache_hit_count,
            "cache_hit_rate": self.cache_hit_count / len(self.translations) if self.translations else 0,
            "created_at": self.created_at.isoformat(),
        }


class TranslationService:
    """
    Service for multi-language translation using Google Cloud Translation API.
    
    Provides translation capabilities with caching, quality scoring,
    and batch processing for optimal performance.
    """
    
    def __init__(self):
        """Initialize the Translation service."""
        try:
            self.client = translate.Client()
            self.firestore_service = FirestoreService()
            
            # Translation cache (in-memory for performance)
            self.translation_cache: Dict[str, TranslationResult] = {}
            self.cache_max_size = 10000
            self.cache_ttl = timedelta(hours=24)
            
            logger.info("Translation service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Translation service: {str(e)}")
            raise WorkflowError(f"Translation service initialization failed: {str(e)}") from e
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        use_cache: bool = True,
        quality_threshold: float = 0.7
    ) -> TranslationResult:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            source_language: Source language code (auto-detected if None)
            use_cache: Whether to use translation cache
            quality_threshold: Minimum quality score for translation
            
        Returns:
            TranslationResult with translation and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            if use_cache:
                cached_result = await self._get_cached_translation(
                    text, target_language, source_language
                )
                if cached_result:
                    return cached_result
            
            # Detect source language if not provided
            if not source_language:
                detected_lang = await self._detect_language(text)
                source_language = detected_lang
            
            # Skip translation if source and target are the same
            if source_language == target_language:
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_language=source_language,
                    target_language=target_language,
                    confidence=1.0,
                    quality_score=1.0,
                    processing_time=processing_time,
                    cached=False
                )
            
            # Perform translation
            logger.info(f"Translating text from {source_language} to {target_language}")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.translate,
                text,
                target_language,
                source_language
            )
            
            translated_text = result['translatedText']
            detected_source = result.get('detectedSourceLanguage', source_language)
            
            # Calculate quality score
            quality_score = await self._calculate_quality_score(
                text, translated_text, detected_source, target_language
            )
            
            # Check quality threshold
            if quality_score < quality_threshold:
                logger.warning(f"Translation quality below threshold: {quality_score}")
                # Could implement fallback translation here
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            translation_result = TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=detected_source,
                target_language=target_language,
                confidence=1.0,  # Google Translate doesn't provide confidence scores
                quality_score=quality_score,
                processing_time=processing_time,
                cached=False
            )
            
            # Cache the result
            if use_cache:
                await self._cache_translation(translation_result)
            
            logger.info(f"Translation completed in {processing_time:.2f}s")
            return translation_result
            
        except gcp_exceptions.GoogleAPIError as e:
            logger.error(f"Google Translation API error: {str(e)}")
            raise WorkflowError(f"Translation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise WorkflowError(f"Translation failed: {str(e)}") from e
    
    async def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None,
        use_cache: bool = True,
        max_concurrent: int = 5
    ) -> BatchTranslationResult:
        """
        Translate multiple texts in batch.
        
        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code (auto-detected if None)
            use_cache: Whether to use translation cache
            max_concurrent: Maximum concurrent translations
            
        Returns:
            BatchTranslationResult with all translations and statistics
        """
        start_time = datetime.utcnow()
        
        try:
            # Create semaphore to limit concurrent translations
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def translate_single(text: str) -> Optional[TranslationResult]:
                async with semaphore:
                    try:
                        return await self.translate_text(
                            text, target_language, source_language, use_cache
                        )
                    except Exception as e:
                        logger.error(f"Failed to translate text: {str(e)}")
                        return None
            
            # Execute translations concurrently
            tasks = [translate_single(text) for text in texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            translations = []
            success_count = 0
            failure_count = 0
            cache_hit_count = 0
            
            for result in results:
                if isinstance(result, TranslationResult):
                    translations.append(result)
                    success_count += 1
                    if result.cached:
                        cache_hit_count += 1
                else:
                    failure_count += 1
            
            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            batch_result = BatchTranslationResult(
                translations=translations,
                total_processing_time=total_processing_time,
                success_count=success_count,
                failure_count=failure_count,
                cache_hit_count=cache_hit_count
            )
            
            logger.info(f"Batch translation completed: {success_count} success, {failure_count} failures")
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch translation error: {str(e)}")
            raise WorkflowError(f"Batch translation failed: {str(e)}") from e
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with language detection results
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.client.detect_language, text
            )
            
            return {
                "language": result["language"],
                "confidence": result["confidence"],
                "is_reliable": result["confidence"] > 0.8,
                "input_text": text[:100] + "..." if len(text) > 100 else text,
            }
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return {
                "language": "unknown",
                "confidence": 0.0,
                "is_reliable": False,
                "error": str(e),
            }
    
    async def get_supported_languages(
        self,
        target_language: str = "en"
    ) -> List[Dict[str, str]]:
        """
        Get list of supported languages.
        
        Args:
            target_language: Language for language names (default: English)
            
        Returns:
            List of supported languages with codes and names
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_languages, target_language
            )
            
            return [
                {
                    "code": lang["language"],
                    "name": lang["name"],
                }
                for lang in result
            ]
            
        except Exception as e:
            logger.error(f"Error getting supported languages: {str(e)}")
            # Return common languages as fallback
            return [
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
                {"code": "hi", "name": "Hindi"},
            ]
    
    async def translate_document_sections(
        self,
        sections: Dict[str, str],
        target_language: str,
        source_language: Optional[str] = None,
        preserve_formatting: bool = True
    ) -> Dict[str, TranslationResult]:
        """
        Translate document sections while preserving structure.
        
        Args:
            sections: Dictionary of section_id -> text
            target_language: Target language code
            source_language: Source language code
            preserve_formatting: Whether to preserve text formatting
            
        Returns:
            Dictionary of section_id -> TranslationResult
        """
        try:
            results = {}
            
            # Extract texts for batch translation
            section_ids = list(sections.keys())
            texts = list(sections.values())
            
            # Perform batch translation
            batch_result = await self.translate_batch(
                texts, target_language, source_language
            )
            
            # Map results back to sections
            for i, translation in enumerate(batch_result.translations):
                if i < len(section_ids):
                    section_id = section_ids[i]
                    results[section_id] = translation
            
            return results
            
        except Exception as e:
            logger.error(f"Document section translation error: {str(e)}")
            raise WorkflowError(f"Document section translation failed: {str(e)}") from e
    
    async def _detect_language(self, text: str) -> str:
        """Detect language of text."""
        try:
            result = await self.detect_language(text)
            return result["language"]
        except Exception:
            return "en"  # Default to English
    
    async def _calculate_quality_score(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> float:
        """
        Calculate translation quality score.
        
        This is a simplified implementation. In practice, you might use
        more sophisticated metrics like BLEU, METEOR, or neural quality estimation.
        """
        try:
            # Basic quality indicators
            quality_score = 1.0
            
            # Check for obvious issues
            if not translated_text or translated_text.strip() == "":
                return 0.0
            
            # Check if translation is identical to original (might indicate failure)
            if original_text == translated_text and source_language != target_language:
                quality_score -= 0.3
            
            # Check length ratio (very different lengths might indicate issues)
            length_ratio = len(translated_text) / len(original_text) if original_text else 1
            if length_ratio < 0.3 or length_ratio > 3.0:
                quality_score -= 0.2
            
            # Check for repeated characters (might indicate encoding issues)
            if any(char * 5 in translated_text for char in "abcdefghijklmnopqrstuvwxyz"):
                quality_score -= 0.2
            
            # Check for HTML/XML tags (might indicate formatting issues)
            if "<" in translated_text and ">" in translated_text:
                quality_score -= 0.1
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.warning(f"Quality score calculation failed: {str(e)}")
            return 0.8  # Default moderate quality
    
    def _generate_cache_key(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str]
    ) -> str:
        """Generate cache key for translation."""
        content = f"{text}|{source_language or 'auto'}|{target_language}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def _get_cached_translation(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str]
    ) -> Optional[TranslationResult]:
        """Get cached translation if available."""
        try:
            cache_key = self._generate_cache_key(text, target_language, source_language)
            
            # Check in-memory cache first
            if cache_key in self.translation_cache:
                cached = self.translation_cache[cache_key]
                # Check if cache entry is still valid
                if datetime.utcnow() - cached.created_at < self.cache_ttl:
                    cached.cached = True
                    return cached
                else:
                    # Remove expired entry
                    del self.translation_cache[cache_key]
            
            # Check Firestore cache
            doc_ref = self.firestore_service.db.collection("translation_cache").document(cache_key)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                created_at = datetime.fromisoformat(data["created_at"])
                
                # Check if cache entry is still valid
                if datetime.utcnow() - created_at < self.cache_ttl:
                    cached_result = TranslationResult(
                        original_text=data["original_text"],
                        translated_text=data["translated_text"],
                        source_language=data["source_language"],
                        target_language=data["target_language"],
                        confidence=data["confidence"],
                        quality_score=data["quality_score"],
                        processing_time=data["processing_time"],
                        cached=True
                    )
                    
                    # Add to in-memory cache
                    self.translation_cache[cache_key] = cached_result
                    
                    return cached_result
                else:
                    # Remove expired entry
                    doc_ref.delete()
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
            return None
    
    async def _cache_translation(self, result: TranslationResult):
        """Cache translation result."""
        try:
            cache_key = self._generate_cache_key(
                result.original_text,
                result.target_language,
                result.source_language
            )
            
            # Add to in-memory cache
            if len(self.translation_cache) >= self.cache_max_size:
                # Remove oldest entry
                oldest_key = min(
                    self.translation_cache.keys(),
                    key=lambda k: self.translation_cache[k].created_at
                )
                del self.translation_cache[oldest_key]
            
            self.translation_cache[cache_key] = result
            
            # Add to Firestore cache (async)
            asyncio.create_task(self._cache_to_firestore(cache_key, result))
            
        except Exception as e:
            logger.warning(f"Translation caching failed: {str(e)}")
    
    async def _cache_to_firestore(self, cache_key: str, result: TranslationResult):
        """Cache translation to Firestore."""
        try:
            doc_ref = self.firestore_service.db.collection("translation_cache").document(cache_key)
            doc_ref.set(result.to_dict())
        except Exception as e:
            logger.warning(f"Firestore caching failed: {str(e)}")
    
    async def clear_cache(self, older_than_hours: int = 24):
        """Clear translation cache entries older than specified hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            # Clear in-memory cache
            expired_keys = [
                key for key, result in self.translation_cache.items()
                if result.created_at < cutoff_time
            ]
            for key in expired_keys:
                del self.translation_cache[key]
            
            # Clear Firestore cache
            cache_collection = self.firestore_service.db.collection("translation_cache")
            query = cache_collection.where("created_at", "<", cutoff_time.isoformat())
            
            docs = query.stream()
            batch = self.firestore_service.db.batch()
            
            count = 0
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Commit in batches of 500
                if count % 500 == 0:
                    batch.commit()
                    batch = self.firestore_service.db.batch()
            
            if count % 500 != 0:
                batch.commit()
            
            logger.info(f"Cleared {count} expired cache entries")
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {str(e)}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get translation cache statistics."""
        try:
            return {
                "in_memory_cache_size": len(self.translation_cache),
                "cache_max_size": self.cache_max_size,
                "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600,
                "oldest_entry": min(
                    (result.created_at for result in self.translation_cache.values()),
                    default=None
                ),
                "newest_entry": max(
                    (result.created_at for result in self.translation_cache.values()),
                    default=None
                ),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the translation service."""
        try:
            # Test translation with a simple text
            test_text = "Hello, this is a test."
            
            result = await self.translate_text(
                text=test_text,
                target_language="es",
                source_language="en"
            )
            
            return {
                "status": "healthy",
                "service": "translation",
                "timestamp": datetime.utcnow().isoformat(),
                "test_completed": True,
                "test_translation": result.translated_text,
                "cache_stats": await self.get_cache_stats(),
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "translation",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# Global service instance
translation_service = TranslationService()