"""
Custom exception classes for the application.
"""

from typing import Any, Dict, Optional


class LegalCompanionException(Exception):
    """Base exception class for Legal Companion application."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(LegalCompanionException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=422,
            details=details or {},
        )
        self.field = field


class AuthenticationException(LegalCompanionException):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="authentication_required",
            status_code=401,
            details=details or {},
        )


class AuthorizationException(LegalCompanionException):
    """Exception raised for authorization errors."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="insufficient_permissions",
            status_code=403,
            details=details or {},
        )


class ResourceNotFoundException(LegalCompanionException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="resource_not_found",
            status_code=404,
            details=details or {},
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitException(LegalCompanionException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            status_code=429,
            details=details or {},
        )
        self.retry_after = retry_after


class FileUploadException(LegalCompanionException):
    """Exception raised for file upload errors."""
    
    def __init__(
        self,
        message: str,
        file_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="file_upload_error",
            status_code=400,
            details=details or {},
        )
        self.file_name = file_name


class ProcessingException(LegalCompanionException):
    """Exception raised for document processing errors."""
    
    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        job_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="processing_error",
            status_code=500,
            details=details or {},
        )
        self.stage = stage
        self.job_id = job_id


class AIServiceException(LegalCompanionException):
    """Exception raised for AI service errors."""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="ai_service_error",
            status_code=502,
            details=details or {},
        )
        self.service = service
        self.model = model


class StorageException(LegalCompanionException):
    """Exception raised for storage errors."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        bucket: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="storage_error",
            status_code=500,
            details=details or {},
        )
        self.operation = operation
        self.bucket = bucket


class QuotaExceededException(LegalCompanionException):
    """Exception raised when quota is exceeded."""
    
    def __init__(
        self,
        message: str,
        quota_type: Optional[str] = None,
        current_usage: Optional[int] = None,
        limit: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="quota_exceeded",
            status_code=429,
            details=details or {},
        )
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.limit = limit


class ConfigurationException(LegalCompanionException):
    """Exception raised for configuration errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="configuration_error",
            status_code=500,
            details=details or {},
        )
        self.config_key = config_key


class ExternalServiceException(LegalCompanionException):
    """Exception raised for external service errors."""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="external_service_error",
            status_code=status_code,
            details=details or {},
        )
        self.service = service