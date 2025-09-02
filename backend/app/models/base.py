"""
Base models and common utilities for Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator

T = TypeVar('T')


class TimestampMixin(BaseModel):
    """Mixin for models that need timestamp fields."""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class BaseEntity(TimestampMixin):
    """Base class for all entities with ID and timestamps."""
    
    id: UUID = Field(default_factory=uuid4)
    
    model_config = ConfigDict(
        # Use enum values instead of enum names
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Allow population by field name or alias
        populate_by_name=True,
        # Serialize datetime as ISO format
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )


class ProcessingStatus(str, Enum):
    """Job processing status enumeration."""
    
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(str, Enum):
    """Job processing stage enumeration."""
    
    UPLOAD = "upload"
    OCR = "ocr"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    RISK_ASSESSMENT = "risk_assessment"
    TRANSLATION = "translation"
    AUDIO_GENERATION = "audio_generation"
    EXPORT_GENERATION = "export_generation"


class ClauseClassification(str, Enum):
    """Clause risk classification enumeration."""
    
    BENEFICIAL = "beneficial"
    CAUTION = "caution"
    RISKY = "risky"


class UserRole(str, Enum):
    """User role in legal document context."""
    
    TENANT = "tenant"
    LANDLORD = "landlord"
    BORROWER = "borrower"
    LENDER = "lender"
    BUYER = "buyer"
    SELLER = "seller"
    EMPLOYEE = "employee"
    EMPLOYER = "employer"
    CONSUMER = "consumer"
    BUSINESS = "business"


class ErrorType(str, Enum):
    """Error type classification."""
    
    VALIDATION_ERROR = "validation_error"
    UPLOAD_ERROR = "upload_error"
    OCR_ERROR = "ocr_error"
    ANALYSIS_ERROR = "analysis_error"
    AI_SERVICE_ERROR = "ai_service_error"
    STORAGE_ERROR = "storage_error"
    TIMEOUT_ERROR = "timeout_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    INTERNAL_ERROR = "internal_error"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReadingLevel(str, Enum):
    """Reading level enumeration."""
    
    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    HIGH = "high"
    COLLEGE = "college"


class Language(str, Enum):
    """Supported language codes."""
    
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"


class ResponseFormat(str, Enum):
    """Response format for Q&A."""
    
    TEXT = "text"
    AUDIO = "audio"
    BOTH = "both"


class ExportFormat(str, Enum):
    """Export file format enumeration."""
    
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    MP3 = "mp3"
    SRT = "srt"
    JSON = "json"


class SubscriptionTier(str, Enum):
    """User subscription tier."""
    
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AuthProvider(str, Enum):
    """Authentication provider."""
    
    GOOGLE = "google"
    EMAIL = "email"
    PHONE = "phone"
    ANONYMOUS = "anonymous"


# Common field validators
class CommonValidators:
    """Common validation functions for models."""
    
    @staticmethod
    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @staticmethod
    @field_validator('phone_number')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        import re
        # Basic international phone number validation
        if not re.match(r'^\+?[1-9]\d{1,14}$', v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid phone number format')
        return v
    
    @staticmethod
    @field_validator('url')
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v is None:
            return v
        import re
        if not re.match(r'^https?://.+', v):
            raise ValueError('Invalid URL format')
        return v


# Response wrapper models
class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    
    data: list[Any]
    pagination: Dict[str, Any] = Field(
        description="Pagination metadata"
    )
    
    @classmethod
    def create(
        cls,
        data: list[Any],
        page: int,
        limit: int,
        total: int
    ) -> "PaginatedResponse":
        """Create paginated response with metadata."""
        total_pages = (total + limit - 1) // limit
        
        return cls(
            data=data,
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        )


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status_code: int
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    
    field: str
    message: str
    code: str
    value: Optional[Any] = None


# Health check model
class HealthCheck(BaseModel):
    """Health check response model."""
    
    status: str = Field(description="Service health status")
    version: str = Field(description="Application version")
    timestamp: float = Field(description="Current timestamp")
    services: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Status of dependent services"
    )
    
    @classmethod
    def healthy(cls, version: str = "1.0.0") -> "HealthCheck":
        """Create healthy status response."""
        return cls(
            status="healthy",
            version=version,
            timestamp=datetime.utcnow().timestamp()
        )
    
    @classmethod
    def unhealthy(cls, version: str = "1.0.0", services: Optional[Dict] = None) -> "HealthCheck":
        """Create unhealthy status response."""
        return cls(
            status="unhealthy",
            version=version,
            timestamp=datetime.utcnow().timestamp(),
            services=services or {}
        )