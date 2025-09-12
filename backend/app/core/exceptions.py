"""
Custom exceptions for the Legal Companion application.
"""

from typing import Any, Dict, Optional


class LegalCompanionError(Exception):
    """Base exception for Legal Companion application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LegalCompanionException(Exception):
    """HTTP exception for Legal Companion application."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: str = "internal_error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LegalCompanionError):
    """Raised when data validation fails."""
    pass


class AuthenticationError(LegalCompanionError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(LegalCompanionError):
    """Raised when authorization fails."""
    pass


class DocumentFormatError(LegalCompanionError):
    """Raised when document format is unsupported or invalid."""
    pass


class OCRProcessingError(LegalCompanionError):
    """Raised when OCR processing fails."""
    pass


class AnalysisError(LegalCompanionError):
    """Raised when document analysis fails."""
    pass


class VectorSearchError(LegalCompanionError):
    """Raised when vector search operations fail."""
    pass


class WorkflowError(LegalCompanionError):
    """Raised when workflow execution fails."""
    pass


class StorageError(LegalCompanionError):
    """Raised when storage operations fail."""
    pass


class AIServiceError(LegalCompanionError):
    """Raised when AI service calls fail."""
    pass


class TranslationError(LegalCompanionError):
    """Raised when translation operations fail."""
    pass


class AudioProcessingError(LegalCompanionError):
    """Raised when audio processing fails."""
    pass


class ExportError(LegalCompanionError):
    """Raised when export operations fail."""
    pass


class RateLimitError(LegalCompanionError):
    """Raised when rate limits are exceeded."""
    pass


class QuotaExceededError(LegalCompanionError):
    """Raised when service quotas are exceeded."""
    pass


class ConfigurationError(LegalCompanionError):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(LegalCompanionError):
    """Raised when database operations fail."""
    pass


class NetworkError(LegalCompanionError):
    """Raised when network operations fail."""
    pass


class TimeoutError(LegalCompanionError):
    """Raised when operations timeout."""
    pass


class PIIDetectionError(LegalCompanionError):
    """Raised when PII detection or masking fails."""
    pass


class JurisdictionAnalysisError(LegalCompanionError):
    """Raised when jurisdiction analysis fails."""
    pass


class MonitoringError(LegalCompanionError):
    """Raised when monitoring operations fail."""
    pass


class DocumentError(LegalCompanionError):
    """Raised when document operations fail."""
    pass


class ProcessingError(LegalCompanionError):
    """Raised when document processing fails."""
    pass