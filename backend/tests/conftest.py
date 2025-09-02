"""
Pytest configuration and fixtures for AI Legal Companion tests.

Provides common fixtures and test utilities for:
- Database setup and teardown
- Authentication mocking
- AI service mocking
- Test data generation
"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os
from datetime import datetime

from fastapi.testclient import TestClient
from google.cloud import firestore
from google.cloud import storage

from app.main import app
from app.core.config import get_settings
from app.services.monitoring import monitoring_service


# Test settings
@pytest.fixture(scope="session")
def test_settings():
    """Test configuration settings."""
    return {
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "VERTEX_AI_LOCATION": "us-central1",
        "STORAGE_BUCKET": "test-bucket",
        "FIRESTORE_DATABASE": "test-db",
        "ENVIRONMENT": "test"
    }


# FastAPI test client
@pytest.fixture(scope="session")
def client():
    """FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


# Async test client
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture
async def mock_firestore():
    """Mock Firestore client."""
    with patch('google.cloud.firestore.Client') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Mock collection and document operations
        mock_collection = Mock()
        mock_document = Mock()
        
        mock_instance.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_document
        
        # Mock async operations
        mock_document.set = AsyncMock()
        mock_document.get = AsyncMock()
        mock_document.update = AsyncMock()
        mock_document.delete = AsyncMock()
        
        yield mock_instance


@pytest.fixture
async def mock_storage():
    """Mock Cloud Storage client."""
    with patch('google.cloud.storage.Client') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Mock bucket and blob operations
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_instance.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock blob operations
        mock_blob.upload_from_string = Mock()
        mock_blob.download_as_text = Mock(return_value="test content")
        mock_blob.delete = Mock()
        mock_blob.generate_signed_url = Mock(return_value="https://test-url.com")
        
        yield mock_instance


# Authentication fixtures
@pytest.fixture
def mock_firebase_auth():
    """Mock Firebase authentication."""
    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        mock_verify.return_value = {
            'uid': 'test-user-123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        yield mock_verify


@pytest.fixture
def authenticated_headers():
    """Headers for authenticated requests."""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


# AI service fixtures
@pytest.fixture
def mock_vertex_ai():
    """Mock Vertex AI services."""
    with patch('google.cloud.aiplatform.init') as mock_init:
        mock_init.return_value = None
        
        # Mock model predictions
        with patch('google.cloud.aiplatform.Model') as mock_model:
            mock_instance = Mock()
            mock_model.return_value = mock_instance
            
            mock_instance.predict = AsyncMock(return_value=Mock(
                predictions=[{
                    "content": "Test AI response",
                    "confidence": 0.95
                }]
            ))
            
            yield mock_instance


@pytest.fixture
def mock_document_ai():
    """Mock Document AI services."""
    with patch('google.cloud.documentai.DocumentProcessorServiceClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Mock document processing
        mock_response = Mock()
        mock_response.document.text = "Extracted text from document"
        mock_response.document.entities = []
        
        mock_instance.process_document = Mock(return_value=mock_response)
        
        yield mock_instance


# Test data fixtures
@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "id": "test-doc-123",
        "filename": "test-contract.pdf",
        "content_type": "application/pdf",
        "size": 1024000,
        "upload_timestamp": datetime.utcnow().isoformat(),
        "user_id": "test-user-123",
        "status": "uploaded"
    }


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "id": "test-job-123",
        "document_id": "test-doc-123",
        "user_id": "test-user-123",
        "job_type": "document_analysis",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "progress": 0
    }


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        "document_id": "test-doc-123",
        "clauses": [
            {
                "id": "clause-1",
                "text": "This is a test clause",
                "type": "termination",
                "risk_score": 75,
                "page": 1,
                "position": {"x": 100, "y": 200, "width": 300, "height": 50}
            }
        ],
        "summary": {
            "total_clauses": 1,
            "high_risk_clauses": 1,
            "overall_risk_score": 75
        },
        "processing_time": 45.2
    }


# File fixtures
@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        # Write minimal PDF content
        temp_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
        temp_file.flush()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)


@pytest.fixture
def temp_docx_file():
    """Create a temporary DOCX file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
        # Write minimal DOCX content (simplified)
        temp_file.write(b'PK\x03\x04\x14\x00\x00\x00\x08\x00')
        temp_file.flush()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)


# Monitoring fixtures
@pytest.fixture
def mock_monitoring():
    """Mock monitoring services."""
    with patch.object(monitoring_service, 'record_metric') as mock_record:
        mock_record.return_value = None
        
        with patch.object(monitoring_service, 'report_error') as mock_error:
            mock_error.return_value = None
            
            yield {
                'record_metric': mock_record,
                'report_error': mock_error
            }


# Async test utilities
@pytest.fixture
def async_mock():
    """Create async mock helper."""
    def _async_mock(*args, **kwargs):
        mock = AsyncMock(*args, **kwargs)
        return mock
    return _async_mock


# Test database cleanup
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    
    # Cleanup logic would go here
    # For now, we'll just pass since we're using mocks
    pass


# Error simulation fixtures
@pytest.fixture
def simulate_network_error():
    """Simulate network errors for testing error handling."""
    def _simulate_error(exception_type=Exception, message="Network error"):
        return Mock(side_effect=exception_type(message))
    return _simulate_error


@pytest.fixture
def simulate_timeout():
    """Simulate timeout errors for testing."""
    def _simulate_timeout():
        import asyncio
        return Mock(side_effect=asyncio.TimeoutError("Operation timed out"))
    return _simulate_timeout


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Test data generators
@pytest.fixture
def generate_test_users():
    """Generate test user data."""
    def _generate(count=1):
        users = []
        for i in range(count):
            users.append({
                "uid": f"test-user-{i}",
                "email": f"user{i}@example.com",
                "name": f"Test User {i}",
                "created_at": datetime.utcnow().isoformat()
            })
        return users if count > 1 else users[0]
    return _generate


@pytest.fixture
def generate_test_documents():
    """Generate test document data."""
    def _generate(count=1, user_id="test-user-123"):
        documents = []
        for i in range(count):
            documents.append({
                "id": f"test-doc-{i}",
                "filename": f"document-{i}.pdf",
                "content_type": "application/pdf",
                "size": 1024000 + i * 1000,
                "user_id": user_id,
                "status": "uploaded",
                "upload_timestamp": datetime.utcnow().isoformat()
            })
        return documents if count > 1 else documents[0]
    return _generate