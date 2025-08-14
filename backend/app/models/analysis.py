"""
Analysis-related Pydantic models for Q&A, exports, and AI processing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .base import (
    BaseEntity,
    ClauseClassification,
    Language,
    ResponseFormat,
    ExportFormat,
    RiskLevel,
)


class QARequest(BaseModel):
    """Question and answer request."""
    
    job_id: UUID = Field(description="Associated job ID")
    query: str = Field(
        min_length=1,
        max_length=1000,
        description="User question"
    )
    audio_url: Optional[str] = Field(
        default=None,
        description="URL to audio question"
    )
    role: Optional[str] = Field(
        default=None,
        description="User role context"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Legal jurisdiction context"
    )
    locale: str = Field(
        default="en-US",
        description="Locale for response"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Desired response format"
    )
    context_clauses: Optional[List[UUID]] = Field(
        default=None,
        description="Specific clause IDs for context"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty."""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @field_validator('audio_url')
    @classmethod
    def validate_audio_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate audio URL format."""
        if v is not None:
            import re
            if not re.match(r'^https?://.+\.(mp3|wav|ogg|m4a)(\?.*)?$', v, re.IGNORECASE):
                raise ValueError('Invalid audio URL format')
        return v


class QASource(BaseModel):
    """Source reference for Q&A response."""
    
    clause_id: UUID = Field(description="Referenced clause ID")
    clause_text: str = Field(description="Clause text excerpt")
    relevance: float = Field(
        ge=0, le=1,
        description="Relevance score to the question"
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number in original document"
    )
    clause_number: Optional[str] = Field(
        default=None,
        description="Clause number or identifier"
    )


class QAResponse(BaseModel):
    """Question and answer response."""
    
    question: str = Field(description="Original or transcribed question")
    answer: str = Field(description="Generated answer")
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence in the answer"
    )
    sources: List[QASource] = Field(
        default_factory=list,
        description="Source clauses referenced"
    )
    audio_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Audio response details"
    )
    related_questions: List[str] = Field(
        default_factory=list,
        description="Suggested related questions"
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Response generation time in seconds"
    )
    model_used: Optional[str] = Field(
        default=None,
        description="AI model used for generation"
    )
    
    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v: str) -> str:
        """Validate answer is not empty."""
        if not v.strip():
            raise ValueError('Answer cannot be empty')
        return v.strip()


class ExportOptions(BaseModel):
    """Export generation options."""
    
    include_annotations: bool = Field(
        default=True,
        description="Include risk annotations"
    )
    highlight_risks: bool = Field(
        default=True,
        description="Highlight risky clauses"
    )
    language: Language = Field(
        default=Language.ENGLISH,
        description="Export language"
    )
    audio_voice: Optional[str] = Field(
        default=None,
        description="Voice for audio exports"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include document metadata"
    )
    watermark: bool = Field(
        default=False,
        description="Add watermark to exports"
    )
    page_numbers: bool = Field(
        default=True,
        description="Include page numbers"
    )
    table_of_contents: bool = Field(
        default=True,
        description="Include table of contents"
    )


class ExportRequest(BaseModel):
    """Export generation request."""
    
    job_id: UUID = Field(description="Associated job ID")
    formats: List[ExportFormat] = Field(
        min_length=1,
        description="Requested export formats"
    )
    options: Optional[ExportOptions] = Field(
        default=None,
        description="Export options"
    )
    custom_template: Optional[str] = Field(
        default=None,
        description="Custom export template ID"
    )
    
    @field_validator('formats')
    @classmethod
    def validate_formats(cls, v: List[ExportFormat]) -> List[ExportFormat]:
        """Validate export formats."""
        if not v:
            raise ValueError('At least one export format must be specified')
        return list(set(v))  # Remove duplicates


class ExportFile(BaseModel):
    """Individual export file information."""
    
    format: ExportFormat = Field(description="File format")
    url: str = Field(description="Download URL")
    filename: str = Field(description="Generated filename")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    expires_at: datetime = Field(description="URL expiration time")
    checksum: Optional[str] = Field(
        default=None,
        description="File checksum for integrity"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate download URL."""
        import re
        if not re.match(r'^https?://.+', v):
            raise ValueError('Invalid download URL')
        return v


class ExportResponse(BaseModel):
    """Export generation response."""
    
    export_id: UUID = Field(description="Export batch identifier")
    status: str = Field(description="Export status")
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    files: List[ExportFile] = Field(
        default_factory=list,
        description="Generated export files"
    )
    progress_percentage: int = Field(
        default=0,
        ge=0, le=100,
        description="Export progress"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate export status."""
        allowed_statuses = ['generating', 'completed', 'failed', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v


class ClauseAnalysisRequest(BaseModel):
    """Request for clause analysis."""
    
    text: str = Field(description="Clause text to analyze")
    context: Optional[str] = Field(
        default=None,
        description="Additional context"
    )
    role: Optional[str] = Field(
        default=None,
        description="User role for analysis"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Legal jurisdiction"
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Type of legal document"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate clause text."""
        if not v.strip():
            raise ValueError('Clause text cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Clause text too short for meaningful analysis')
        return v.strip()


class ClauseAnalysisResponse(BaseModel):
    """Response for clause analysis."""
    
    classification: ClauseClassification = Field(
        description="Risk classification"
    )
    risk_score: float = Field(
        ge=0, le=1,
        description="Risk score"
    )
    impact_score: int = Field(
        ge=0, le=100,
        description="Impact score"
    )
    likelihood_score: int = Field(
        ge=0, le=100,
        description="Likelihood score"
    )
    rationale: str = Field(description="Analysis rationale")
    keywords: List[str] = Field(
        default_factory=list,
        description="Extracted keywords"
    )
    category: Optional[str] = Field(
        default=None,
        description="Clause category"
    )
    safer_alternatives: List[str] = Field(
        default_factory=list,
        description="Suggested safer alternatives"
    )
    legal_references: List[str] = Field(
        default_factory=list,
        description="Relevant legal references"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Analysis confidence"
    )


class SummarizationRequest(BaseModel):
    """Request for document summarization."""
    
    text: str = Field(description="Document text to summarize")
    target_length: Optional[int] = Field(
        default=None,
        ge=50,
        description="Target summary length in words"
    )
    reading_level: str = Field(
        default="middle",
        description="Target reading level"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Areas to focus on in summary"
    )
    include_key_points: bool = Field(
        default=True,
        description="Include key points list"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate document text."""
        if not v.strip():
            raise ValueError('Document text cannot be empty')
        if len(v.strip()) < 100:
            raise ValueError('Document text too short for summarization')
        return v.strip()
    
    @field_validator('reading_level')
    @classmethod
    def validate_reading_level(cls, v: str) -> str:
        """Validate reading level."""
        allowed_levels = ['elementary', 'middle', 'high', 'college']
        if v not in allowed_levels:
            raise ValueError(f'Reading level must be one of: {allowed_levels}')
        return v


class SummarizationResponse(BaseModel):
    """Response for document summarization."""
    
    summary: str = Field(description="Generated summary")
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points extracted"
    )
    word_count: int = Field(ge=0, description="Summary word count")
    reading_level: str = Field(description="Achieved reading level")
    compression_ratio: float = Field(
        gt=0,
        description="Compression ratio (original/summary)"
    )
    topics: List[str] = Field(
        default_factory=list,
        description="Main topics covered"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Summarization confidence"
    )


class TranslationRequest(BaseModel):
    """Request for text translation."""
    
    text: str = Field(description="Text to translate")
    source_language: Optional[Language] = Field(
        default=None,
        description="Source language (auto-detect if None)"
    )
    target_language: Language = Field(description="Target language")
    preserve_formatting: bool = Field(
        default=True,
        description="Preserve text formatting"
    )
    context: Optional[str] = Field(
        default=None,
        description="Additional context for translation"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text to translate."""
        if not v.strip():
            raise ValueError('Text to translate cannot be empty')
        return v.strip()


class TranslationResponse(BaseModel):
    """Response for text translation."""
    
    translated_text: str = Field(description="Translated text")
    detected_language: Optional[Language] = Field(
        default=None,
        description="Detected source language"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Translation confidence"
    )
    alternative_translations: List[str] = Field(
        default_factory=list,
        description="Alternative translation options"
    )
    
    @field_validator('translated_text')
    @classmethod
    def validate_translated_text(cls, v: str) -> str:
        """Validate translated text."""
        if not v.strip():
            raise ValueError('Translated text cannot be empty')
        return v.strip()


class AudioGenerationRequest(BaseModel):
    """Request for audio generation."""
    
    text: str = Field(description="Text to convert to speech")
    language: Language = Field(
        default=Language.ENGLISH,
        description="Audio language"
    )
    voice: Optional[str] = Field(
        default=None,
        description="Voice identifier"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5, le=2.0,
        description="Speech speed multiplier"
    )
    pitch: float = Field(
        default=0.0,
        ge=-20.0, le=20.0,
        description="Pitch adjustment in semitones"
    )
    include_timestamps: bool = Field(
        default=True,
        description="Include word-level timestamps"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text for audio generation."""
        if not v.strip():
            raise ValueError('Text for audio generation cannot be empty')
        return v.strip()


class AudioGenerationResponse(BaseModel):
    """Response for audio generation."""
    
    audio_url: str = Field(description="Generated audio URL")
    duration: float = Field(gt=0, description="Audio duration in seconds")
    format: str = Field(default="mp3", description="Audio format")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    timestamps: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Word-level timestamps"
    )
    voice_used: str = Field(description="Voice identifier used")
    
    @field_validator('audio_url')
    @classmethod
    def validate_audio_url(cls, v: str) -> str:
        """Validate audio URL."""
        import re
        if not re.match(r'^https?://.+\.(mp3|wav|ogg|m4a)(\?.*)?$', v, re.IGNORECASE):
            raise ValueError('Invalid audio URL format')
        return v