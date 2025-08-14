"""
Legal Companion Data Models

This module contains all Pydantic models for data validation and serialization.
"""

from .document import *
from .job import *
from .user import *
from .analysis import *

__all__ = [
    # Document models
    "Document",
    "ProcessedDocument",
    "DocumentMetadata",
    "DocumentSummary",
    
    # Job models
    "Job",
    "JobOptions",
    "JobProgress",
    "JobError",
    "JobResults",
    "UploadRequest",
    "UploadResponse",
    
    # User models
    "User",
    "UserPreferences",
    "UserUsage",
    "UserSubscription",
    "AuthState",
    
    # Analysis models
    "Clause",
    "ClauseAnalysis",
    "RiskAssessment",
    "SaferAlternative",
    "LegalCitation",
    "Translation",
    "AudioNarration",
]