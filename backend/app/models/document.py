"""
Document-related Pydantic models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .base import (
    BaseEntity,
    ProcessingStatus,
    UserRole,
    ClauseClassification,
    RiskLevel,
    ReadingLevel,
    Language,
)


class DocumentMetadata(BaseModel):
    """Document metadata extracted during processing."""
    
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    keywords: List[str] = Field(default_factory=list)
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    language: Optional[str] = None
    
    @field_validator('page_count', 'word_count', 'character_count')
    @classmethod
    def validate_positive_counts(cls, v: Optional[int]) -> Optional[int]:
        """Validate that counts are positive."""
        if v is not None and v < 0:
            raise ValueError('Count must be non-negative')
        return v


class ClausePosition(BaseModel):
    """Position of a clause within the document."""
    
    page: int = Field(ge=1, description="Page number (1-indexed)")
    x: float = Field(ge=0, description="X coordinate")
    y: float = Field(ge=0, description="Y coordinate")
    width: float = Field(gt=0, description="Width")
    height: float = Field(gt=0, description="Height")


class LegalCitation(BaseModel):
    """Legal citation reference."""
    
    statute: str = Field(description="Statute or regulation reference")
    description: str = Field(description="Description of the legal reference")
    url: Optional[str] = Field(default=None, description="URL to the legal text")
    jurisdiction: str = Field(description="Legal jurisdiction")
    relevance: float = Field(ge=0, le=1, description="Relevance score")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v is not None:
            import re
            if not re.match(r'^https?://.+', v):
                raise ValueError('Invalid URL format')
        return v


class SaferAlternative(BaseModel):
    """Safer alternative wording for a clause."""
    
    suggested_text: str = Field(description="Suggested safer clause text")
    rationale: str = Field(description="Explanation of why this is safer")
    legal_basis: Optional[str] = Field(
        default=None,
        description="Legal justification for the change"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence in the suggestion"
    )
    impact_reduction: float = Field(
        ge=0, le=1,
        description="Expected risk reduction"
    )


class RoleAnalysis(BaseModel):
    """Role-specific analysis of a clause."""
    
    classification: ClauseClassification
    rationale: str = Field(description="Explanation of the classification")
    risk_level: float = Field(ge=0, le=1, description="Risk level for this role")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Specific recommendations for this role"
    )
    negotiation_points: List[str] = Field(
        default_factory=list,
        description="Suggested negotiation points"
    )


class Clause(BaseEntity):
    """Individual clause within a legal document."""
    
    document_id: UUID = Field(description="Parent document ID")
    text: str = Field(description="Original clause text")
    clause_number: Optional[str] = Field(
        default=None,
        description="Clause number or identifier"
    )
    classification: ClauseClassification = Field(
        description="Overall risk classification"
    )
    risk_score: float = Field(
        ge=0, le=1,
        description="Overall risk score"
    )
    impact_score: int = Field(
        ge=0, le=100,
        description="Potential impact score"
    )
    likelihood_score: int = Field(
        ge=0, le=100,
        description="Likelihood of negative outcome"
    )
    role_analysis: Dict[UserRole, RoleAnalysis] = Field(
        default_factory=dict,
        description="Role-specific analysis"
    )
    safer_alternatives: List[SaferAlternative] = Field(
        default_factory=list,
        description="Suggested safer alternatives"
    )
    legal_citations: List[LegalCitation] = Field(
        default_factory=list,
        description="Relevant legal citations"
    )
    position: Optional[ClausePosition] = Field(
        default=None,
        description="Position within the document"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Extracted keywords"
    )
    category: Optional[str] = Field(
        default=None,
        description="Clause category (e.g., 'payment', 'termination')"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Validate that clause text is not empty."""
        if not v.strip():
            raise ValueError('Clause text cannot be empty')
        return v.strip()


class DocumentSummary(BaseModel):
    """Plain language summary of a legal document."""
    
    plain_language: str = Field(description="Plain language summary")
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points and obligations"
    )
    reading_level: ReadingLevel = Field(
        default=ReadingLevel.MIDDLE,
        description="Target reading level"
    )
    word_count: int = Field(ge=0, description="Summary word count")
    estimated_reading_time: int = Field(
        ge=0,
        description="Estimated reading time in minutes"
    )
    overall_tone: str = Field(
        default="neutral",
        description="Overall tone of the document"
    )
    complexity: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="Document complexity level"
    )
    main_parties: List[str] = Field(
        default_factory=list,
        description="Main parties involved"
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Type of legal document"
    )
    
    @field_validator('plain_language')
    @classmethod
    def validate_summary_not_empty(cls, v: str) -> str:
        """Validate that summary is not empty."""
        if not v.strip():
            raise ValueError('Summary cannot be empty')
        return v.strip()


class RiskAssessment(BaseModel):
    """Overall risk assessment of a document."""
    
    overall_risk: RiskLevel = Field(description="Overall risk level")
    risk_score: float = Field(ge=0, le=1, description="Numerical risk score")
    high_risk_clauses: int = Field(ge=0, description="Number of high-risk clauses")
    medium_risk_clauses: int = Field(ge=0, description="Number of medium-risk clauses")
    low_risk_clauses: int = Field(ge=0, description="Number of low-risk clauses")
    recommendations: List[str] = Field(
        default_factory=list,
        description="General recommendations"
    )
    negotiation_points: List[str] = Field(
        default_factory=list,
        description="Key negotiation points"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Critical red flags"
    )
    risk_categories: Dict[str, float] = Field(
        default_factory=dict,
        description="Risk scores by category"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence in the assessment"
    )


class AudioNarration(BaseModel):
    """Audio narration of document summary."""
    
    url: str = Field(description="URL to audio file")
    duration: float = Field(gt=0, description="Duration in seconds")
    transcript: str = Field(description="Full transcript")
    language: Language = Field(default=Language.ENGLISH)
    voice: str = Field(description="Voice identifier used")
    timestamps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Timestamp markers for synchronization"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="File size in bytes"
    )
    format: str = Field(default="mp3", description="Audio format")
    
    @field_validator('url')
    @classmethod
    def validate_audio_url(cls, v: str) -> str:
        """Validate audio URL format."""
        import re
        if not re.match(r'^https?://.+\.(mp3|wav|ogg|m4a)(\?.*)?$', v, re.IGNORECASE):
            raise ValueError('Invalid audio URL format')
        return v


class Translation(BaseModel):
    """Translation of document content."""
    
    language: Language = Field(description="Target language")
    summary: str = Field(description="Translated summary")
    key_points: List[str] = Field(
        default_factory=list,
        description="Translated key points"
    )
    audio_url: Optional[str] = Field(
        default=None,
        description="URL to translated audio"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Translation confidence score"
    )
    translated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Translation timestamp"
    )
    translator_model: Optional[str] = Field(
        default=None,
        description="Translation model used"
    )


class ExportUrls(BaseModel):
    """URLs for exported document formats."""
    
    highlighted_pdf: Optional[str] = Field(
        default=None,
        description="URL to highlighted PDF"
    )
    summary_docx: Optional[str] = Field(
        default=None,
        description="URL to summary DOCX"
    )
    clauses_csv: Optional[str] = Field(
        default=None,
        description="URL to clauses CSV"
    )
    audio_narration: Optional[str] = Field(
        default=None,
        description="URL to audio narration"
    )
    transcript_srt: Optional[str] = Field(
        default=None,
        description="URL to SRT transcript"
    )
    
    @field_validator('highlighted_pdf', 'summary_docx', 'clauses_csv', 'audio_narration', 'transcript_srt')
    @classmethod
    def validate_export_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate export URL format."""
        if v is not None:
            import re
            if not re.match(r'^https?://.+', v):
                raise ValueError('Invalid export URL format')
        return v


class Document(BaseEntity):
    """Legal document model."""
    
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type")
    size_bytes: int = Field(gt=0, description="File size in bytes")
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.QUEUED,
        description="Current processing status"
    )
    user_id: str = Field(description="Owner user ID")
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Legal jurisdiction"
    )
    user_role: Optional[UserRole] = Field(
        default=None,
        description="User's role in the document context"
    )
    storage_url: Optional[str] = Field(
        default=None,
        description="Cloud storage URL"
    )
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Document metadata"
    )
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename format."""
        if not v.strip():
            raise ValueError('Filename cannot be empty')
        # Remove any path components for security
        import os
        return os.path.basename(v.strip())
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/tiff',
        ]
        if v not in allowed_types:
            raise ValueError(f'Unsupported content type: {v}')
        return v


class ProcessedDocument(Document):
    """Fully processed legal document with analysis results."""
    
    structured_text: str = Field(description="OCR extracted text")
    clauses: List[Clause] = Field(
        default_factory=list,
        description="Analyzed clauses"
    )
    summary: Optional[DocumentSummary] = Field(
        default=None,
        description="Document summary"
    )
    risk_assessment: Optional[RiskAssessment] = Field(
        default=None,
        description="Risk assessment"
    )
    audio_narration: Optional[AudioNarration] = Field(
        default=None,
        description="Audio narration"
    )
    translations: Dict[Language, Translation] = Field(
        default_factory=dict,
        description="Translations by language"
    )
    exports: ExportUrls = Field(
        default_factory=ExportUrls,
        description="Export file URLs"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Total processing time in seconds"
    )
    ai_models_used: List[str] = Field(
        default_factory=list,
        description="AI models used in processing"
    )
    
    @field_validator('structured_text')
    @classmethod
    def validate_structured_text(cls, v: str) -> str:
        """Validate structured text is not empty."""
        if not v.strip():
            raise ValueError('Structured text cannot be empty')
        return v.strip()