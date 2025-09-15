"""
Google Cloud configuration for Legal Companion.

This file contains configuration for Google Cloud services including:
- Document AI for OCR processing
- Cloud Storage for file storage
- Translation API for multi-language support
"""

import os
from typing import Optional


class GoogleCloudConfig:
    """Configuration class for Google Cloud services."""
    
    def __init__(self):
        # Project configuration
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Document AI configuration
        self.document_ai_location = os.getenv("DOCUMENT_AI_LOCATION", "us")
        self.document_ai_processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        
        # Cloud Storage configuration
        self.storage_bucket_name = os.getenv("STORAGE_BUCKET_NAME")
        
        # Translation API configuration
        self.translation_location = os.getenv("TRANSLATION_LOCATION", "global")
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        if not self.project_id:
            print("Warning: GOOGLE_CLOUD_PROJECT_ID not set. Using mock services.")
        
        if not self.credentials_path:
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS not set. Using mock services.")
        
        if not self.document_ai_processor_id:
            print("Warning: DOCUMENT_AI_PROCESSOR_ID not set. OCR will use mock processing.")
        
        if not self.storage_bucket_name:
            print("Warning: STORAGE_BUCKET_NAME not set. File storage will use mock service.")
    
    @property
    def is_configured(self) -> bool:
        """Check if Google Cloud is properly configured."""
        return bool(
            self.project_id and 
            self.credentials_path and 
            os.path.exists(self.credentials_path)
        )
    
    @property
    def document_ai_enabled(self) -> bool:
        """Check if Document AI is configured."""
        return bool(
            self.is_configured and 
            self.document_ai_processor_id
        )
    
    @property
    def storage_enabled(self) -> bool:
        """Check if Cloud Storage is configured."""
        return bool(
            self.is_configured and 
            self.storage_bucket_name
        )
    
    def get_document_ai_processor_name(self) -> Optional[str]:
        """Get the full Document AI processor name."""
        if not self.document_ai_enabled:
            return None
        
        return f"projects/{self.project_id}/locations/{self.document_ai_location}/processors/{self.document_ai_processor_id}"


# Global configuration instance
google_cloud_config = GoogleCloudConfig()


def setup_google_cloud_environment():
    """
    Setup Google Cloud environment and print configuration status.
    """
    print("=== Google Cloud Configuration ===")
    print(f"Project ID: {google_cloud_config.project_id or 'Not configured'}")
    print(f"Credentials: {'Configured' if google_cloud_config.credentials_path else 'Not configured'}")
    print(f"Document AI: {'Enabled' if google_cloud_config.document_ai_enabled else 'Disabled (using mock)'}")
    print(f"Cloud Storage: {'Enabled' if google_cloud_config.storage_enabled else 'Disabled (using mock)'}")
    print("=" * 35)
    
    if google_cloud_config.is_configured:
        print("✅ Google Cloud services are properly configured")
    else:
        print("⚠️  Google Cloud services not configured - using mock services for development")
        print("\nTo enable Google Cloud services:")
        print("1. Set GOOGLE_CLOUD_PROJECT_ID environment variable")
        print("2. Set GOOGLE_APPLICATION_CREDENTIALS to path of service account key")
        print("3. Set DOCUMENT_AI_PROCESSOR_ID for OCR processing")
        print("4. Set STORAGE_BUCKET_NAME for file storage")


# Environment variables template for .env file
ENV_TEMPLATE = """
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Document AI Configuration
DOCUMENT_AI_LOCATION=us
DOCUMENT_AI_PROCESSOR_ID=your-processor-id

# Cloud Storage Configuration
STORAGE_BUCKET_NAME=your-bucket-name

# Translation API Configuration
TRANSLATION_LOCATION=global
"""


def create_env_template():
    """Create a template .env file with Google Cloud configuration."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env.template")
    
    with open(env_path, "w") as f:
        f.write(ENV_TEMPLATE.strip())
    
    print(f"Created environment template at: {env_path}")
    print("Copy this to .env and fill in your Google Cloud configuration.")


if __name__ == "__main__":
    setup_google_cloud_environment()
    create_env_template()