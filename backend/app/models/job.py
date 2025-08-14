"""
Job processing related Pydantic models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .base import (
    BaseEntity,
    ProcessingStatus,
    ProcessingStage,
    ErrorType,
    ReadingLevel,
    Language,
    ExportFormat,
)


class JobOptions(BaseModel):
    """Configuration options for job processing."""
    
    enable_translation: bool = Field(
        default=True,
        description="Enable multi-language translation"
    )
    enable_audio: bool = Field(
        default=True,
        description="Enable audio narration generation"
    )
    target_languages: List[Language] = Field(
        default_factory=list,
        description="Target languages for translation"
    )
    audio_voice: Optional[str] = Field(
        default=None,
        description="Preferred voice for audio generation"
    )
    reading_level: ReadingLevel = Field(
        default=ReadingLevel.MIDDLE,
        description="Target reading level for summaries"
    )
    include_explanations: bool = Field(
        default=True,
        description="Include detailed explanations"
    )
    highlight_risks: bool = Field(
        default=True,
        description="Highlight risky clauses in exports"
    )
    export_formats: List[ExportFormat] = Field(
        default_factory=lambda: [ExportFormat.PDF, ExportFormat.DOCX],
        description="Desired export formats"
    )
    max_processing_time: int = Field(
        default=300,
        ge=60,
        le=1800,
        description="Maximum processing time in seconds"
    )
    priority: str = Field(
        default="normal",
        description="Processing priority"
    )


class JobError(BaseModel):
    """Job processing error details."""
    
    type: ErrorType = Field(description="Error type classification")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error occurrence timestamp"
    )
    retryable: bool = Field(
        default=False,
        description="Whether the error is retryable"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    stack_trace: Optional[str] = Field(
        default=None,
        description="Stack trace for debugging"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Validate error message is not empty."""
        if not v.strip():
            raise ValueError('Error message cannot be empty')
        return v.strip()


class JobProgress(BaseModel):
    """Progress information for a processing stage."""
    
    stage: ProcessingStage = Field(description="Current processing stage")
    percentage: int = Field(
        ge=0, le=100,
        description="Completion percentage"
    )
    message: Optional[str] = Field(
        default=None,
        description="Progress message"
    )
    estimated_time_remaining: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated time remaining in seconds"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Stage start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Stage completion timestamp"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="AI tokens used in this stage"
    )
    api_calls: Optional[int] = Field(
        default=None,
        ge=0,
        description="API calls made in this stage"
    )


class JobMetrics(BaseModel):
    """Job processing metrics and statistics."""
    
    total_processing_time: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total processing time in seconds"
    )
    ai_models_used: List[str] = Field(
        default_factory=list,
        description="AI models used during processing"
    )
    total_tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total AI tokens consumed"
    )
    total_api_calls: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total API calls made"
    )
    processing_cost: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated processing cost"
    )
    stage_timings: Dict[ProcessingStage, float] = Field(
        default_factory=dict,
        description="Time spent in each stage"
    )


class Job(BaseEntity):
    """Job processing model."""
    
    document_id: UUID = Field(description="Associated document ID")
    user_id: str = Field(description="Job owner user ID")
    status: ProcessingStatus = Field(
        default=ProcessingStatus.QUEUED,
        description="Current job status"
    )
    current_stage: ProcessingStage = Field(
        default=ProcessingStage.UPLOAD,
        description="Current processing stage"
    )
    progress_percentage: int = Field(
        default=0,
        ge=0, le=100,
        description="Overall progress percentage"
    )
    options: JobOptions = Field(
        default_factory=JobOptions,
        description="Job processing options"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Job start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Job completion timestamp"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    error: Optional[JobError] = Field(
        default=None,
        description="Error details if job failed"
    )
    progress: List[JobProgress] = Field(
        default_factory=list,
        description="Progress history"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts"
    )
    metrics: Optional[JobMetrics] = Field(
        default=None,
        description="Processing metrics"
    )
    
    @property
    def is_terminal_status(self) -> bool:
        """Check if job is in a terminal status."""
        return self.status in [
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
            ProcessingStatus.CANCELLED
        ]
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return (
            self.status == ProcessingStatus.FAILED and
            self.retry_count < self.max_retries and
            self.error is not None and
            self.error.retryable
        )
    
    def add_progress(self, stage: ProcessingStage, percentage: int, message: Optional[str] = None) -> None:
        """Add progress update."""
        progress = JobProgress(
            stage=stage,
            percentage=percentage,
            message=message,
            started_at=datetime.utcnow()
        )
        self.progress.append(progress)
        self.current_stage = stage
        self.progress_percentage = percentage


class JobResults(BaseModel):
    """Job processing results summary."""
    
    job_id: UUID = Field(description="Job identifier")
    document_id: UUID = Field(description="Document identifier")
    completed_at: datetime = Field(description="Completion timestamp")
    processing_time: float = Field(
        gt=0,
        description="Total processing time in seconds"
    )
    summary: Dict[str, Any] = Field(
        description="Results summary statistics"
    )
    exports: Dict[str, str] = Field(
        default_factory=dict,
        description="Export file URLs by format"
    )
    translations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Translation results by language"
    )
    metadata: JobMetrics = Field(
        description="Processing metadata and metrics"
    )


class UploadRequest(BaseModel):
    """Document upload request."""
    
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type")
    size_bytes: int = Field(
        gt=0,
        le=50 * 1024 * 1024,  # 50MB limit
        description="File size in bytes"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Legal jurisdiction"
    )
    user_role: Optional[str] = Field(
        default=None,
        description="User role in document context"
    )
    options: Optional[JobOptions] = Field(
        default=None,
        description="Processing options"
    )
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename."""
        if not v.strip():
            raise ValueError('Filename cannot be empty')
        # Security: remove path components
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


class UploadResponse(BaseModel):
    """Document upload response."""
    
    job_id: UUID = Field(description="Created job identifier")
    upload_url: str = Field(description="Signed upload URL")
    expires_at: datetime = Field(description="Upload URL expiration")
    max_file_size: int = Field(description="Maximum allowed file size")
    allowed_content_types: List[str] = Field(
        description="Allowed content types"
    )
    fields: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional form fields for upload"
    )
    
    @field_validator('upload_url')
    @classmethod
    def validate_upload_url(cls, v: str) -> str:
        """Validate upload URL format."""
        import re
        if not re.match(r'^https://.+', v):
            raise ValueError('Upload URL must be HTTPS')
        return v


class JobStatusResponse(BaseModel):
    """Job status response."""
    
    job_id: UUID = Field(description="Job identifier")
    status: ProcessingStatus = Field(description="Current status")
    current_stage: ProcessingStage = Field(description="Current stage")
    progress_percentage: int = Field(
        ge=0, le=100,
        description="Progress percentage"
    )
    created_at: datetime = Field(description="Creation timestamp")
    started_at: Optional[datetime] = Field(
        default=None,
        description="Start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion timestamp"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Error details if failed"
    )
    queue_position: Optional[int] = Field(
        default=None,
        description="Position in processing queue"
    )


class JobAnalyzeRequest(BaseModel):
    """Request to analyze a job."""
    
    priority: str = Field(
        default="normal",
        description="Processing priority"
    )
    options: Optional[JobOptions] = Field(
        default=None,
        description="Override processing options"
    )
    force_restart: bool = Field(
        default=False,
        description="Force restart if already processing"
    )


class JobCancelRequest(BaseModel):
    """Request to cancel a job."""
    
    reason: Optional[str] = Field(
        default=None,
        description="Cancellation reason"
    )


# Server-Sent Events models
class SSEEvent(BaseModel):
    """Server-Sent Event message."""
    
    type: str = Field(description="Event type")
    data: Dict[str, Any] = Field(description="Event data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp"
    )
    job_id: Optional[UUID] = Field(
        default=None,
        description="Associated job ID"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request identifier"
    )


class JobUpdateEvent(BaseModel):
    """Job update event for SSE."""
    
    job_id: UUID = Field(description="Job identifier")
    status: ProcessingStatus = Field(description="Current status")
    stage: ProcessingStage = Field(description="Current stage")
    progress: int = Field(
        ge=0, le=100,
        description="Progress percentage"
    )
    message: Optional[str] = Field(
        default=None,
        description="Progress message"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Error details if applicable"
    )