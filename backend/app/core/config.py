"""
Application configuration settings.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # API Configuration
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Legal Companion API"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = Field(default="your-super-secret-key-change-this-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.run.app"]
    )
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None)
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: Optional[str] = Field(default=None)
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = Field(default=None)
    FIREBASE_PRIVATE_KEY: Optional[str] = Field(default=None)
    FIREBASE_CLIENT_EMAIL: Optional[str] = Field(default=None)
    FIREBASE_CLIENT_ID: Optional[str] = Field(default=None)
    FIREBASE_AUTH_URI: str = Field(default="https://accounts.google.com/o/oauth2/auth")
    FIREBASE_TOKEN_URI: str = Field(default="https://oauth2.googleapis.com/token")
    
    # Database Configuration
    FIRESTORE_DATABASE_ID: str = Field(default="(default)")
    
    # Cloud Storage
    STORAGE_BUCKET: Optional[str] = Field(default=None)
    STORAGE_BUCKET_UPLOADS: Optional[str] = Field(default=None)
    STORAGE_BUCKET_OUTPUTS: Optional[str] = Field(default=None)
    
    # AI Services Configuration
    VERTEX_AI_LOCATION: str = Field(default="us-central1")
    GEMINI_MODEL_FLASH: str = Field(default="gemini-1.5-flash")
    GEMINI_MODEL_PRO: str = Field(default="gemini-1.5-pro")
    VECTOR_SEARCH_INDEX_ID: Optional[str] = Field(default=None)
    VECTOR_SEARCH_ENDPOINT_ID: Optional[str] = Field(default=None)
    
    # Document AI
    DOCUMENT_AI_PROCESSOR_ID: Optional[str] = Field(default=None)
    DOCUMENT_AI_LOCATION: str = Field(default="us")
    
    # Translation and TTS
    TRANSLATION_PROJECT_ID: Optional[str] = Field(default=None)
    TTS_VOICE_NAME: str = Field(default="en-US-Neural2-F")
    
    # BigQuery Configuration for Legal Data
    BIGQUERY_DATASET_ID: str = Field(default="legal_data")
    BIGQUERY_STATUTES_TABLE: str = Field(default="statutes")
    BIGQUERY_REGULATIONS_TABLE: str = Field(default="regulations")
    BIGQUERY_PRECEDENTS_TABLE: str = Field(default="precedents")
    BIGQUERY_LOCATION: str = Field(default="US")
    
    # Cloud DLP Configuration for PII Detection
    DLP_PROJECT_ID: Optional[str] = Field(default=None)
    DLP_LOCATION: str = Field(default="global")
    DLP_TEMPLATE_ID: Optional[str] = Field(default=None)
    DLP_JOB_TRIGGER_ID: Optional[str] = Field(default=None)
    
    # PII Detection Settings
    PII_CONFIDENCE_THRESHOLD: float = Field(default=0.7, ge=0.0, le=1.0)
    PII_MASKING_CHARACTER: str = Field(default="*")
    ENABLE_PII_AUDIT_LOGGING: bool = Field(default=True)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST: int = Field(default=10)
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None)
    LOG_LEVEL: str = Field(default="INFO")
    
    # Feature Flags
    ENABLE_VOICE_FEATURES: bool = Field(default=True)
    ENABLE_TRANSLATION: bool = Field(default=True)
    ENABLE_PII_DETECTION: bool = Field(default=True)
    
    # File Upload Limits
    MAX_FILE_SIZE_BYTES: int = Field(default=50 * 1024 * 1024)  # 50MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "image/jpeg",
            "image/png",
            "image/tiff",
        ]
    )
    
    # Processing Configuration
    DEFAULT_PROCESSING_TIMEOUT: int = Field(default=300)  # 5 minutes
    MAX_CONCURRENT_JOBS: int = Field(default=10)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"
    
    def get_firebase_credentials(self) -> Optional[dict]:
        """Get Firebase credentials as dictionary."""
        if not all([
            self.FIREBASE_PROJECT_ID,
            self.FIREBASE_PRIVATE_KEY_ID,
            self.FIREBASE_PRIVATE_KEY,
            self.FIREBASE_CLIENT_EMAIL,
            self.FIREBASE_CLIENT_ID,
        ]):
            return None
        
        return {
            "type": "service_account",
            "project_id": self.FIREBASE_PROJECT_ID,
            "private_key_id": self.FIREBASE_PRIVATE_KEY_ID,
            "private_key": self.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": self.FIREBASE_CLIENT_EMAIL,
            "client_id": self.FIREBASE_CLIENT_ID,
            "auth_uri": self.FIREBASE_AUTH_URI,
            "token_uri": self.FIREBASE_TOKEN_URI,
        }


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings