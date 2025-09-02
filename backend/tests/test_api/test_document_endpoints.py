"""
Integration tests for Document API endpoints.

Tests document upload, retrieval, processing, and management endpoints.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import io

from app.main import app


class TestDocumentEndpoints:
    """Test cases for Document API endpoints."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    def test_upload_document_success(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_storage,
        mock_firestore,
        temp_pdf_file
    ):
        """Test successful document upload."""
        # Prepare file upload
        with open(temp_pdf_file, 'rb') as file:
            files = {"file": ("test.pdf", file, "application/pdf")}
            
            # Execute
            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=authenticated_headers
            )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "document_id" in data
        assert data["filename"] == "test.pdf"
    
    def test_upload_document_unauthorized(self, client, temp_pdf_file):
        """Test document upload without authentication."""
        with open(temp_pdf_file, 'rb') as file:
            files = {"file": ("test.pdf", file, "application/pdf")}
            
            # Execute
            response = client.post("/api/v1/documents/upload", files=files)
        
        # Verify
        assert response.status_code == 401
    
    def test_upload_document_invalid_file_type(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth
    ):
        """Test upload with invalid file type."""
        # Create text file
        text_content = b"This is a text file"
        files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
        
        # Execute
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file type" in data["detail"]
    
    def test_upload_document_too_large(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth
    ):
        """Test upload with file too large."""
        # Create large file (> 50MB)
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        # Execute
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["detail"]
    
    def test_get_document_success(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        sample_document_data
    ):
        """Test successful document retrieval."""
        document_id = "test-doc-123"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute
        response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["filename"] == sample_document_data["filename"]
    
    def test_get_document_not_found(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore
    ):
        """Test document retrieval when document doesn't exist."""
        document_id = "nonexistent-doc"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute
        response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 404
    
    def test_get_document_unauthorized_access(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        sample_document_data
    ):
        """Test document retrieval with unauthorized access."""
        document_id = "test-doc-123"
        
        # Modify sample data to have different user
        unauthorized_doc_data = sample_document_data.copy()
        unauthorized_doc_data["user_id"] = "different-user"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = unauthorized_doc_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute
        response = client.get(
            f"/api/v1/documents/{document_id}",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 403
    
    def test_list_user_documents(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        generate_test_documents
    ):
        """Test listing user documents."""
        # Setup test documents
        test_documents = generate_test_documents(count=3)
        
        # Mock Firestore query
        mock_query = Mock()
        mock_docs = []
        
        for doc_data in test_documents:
            mock_doc = Mock()
            mock_doc.to_dict.return_value = doc_data
            mock_docs.append(mock_doc)
        
        mock_query.stream = AsyncMock(return_value=mock_docs)
        mock_firestore.collection().where().order_by.return_value = mock_query
        
        # Execute
        response = client.get(
            "/api/v1/documents/",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(doc["user_id"] == "test-user-123" for doc in data)
    
    def test_list_user_documents_with_pagination(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        generate_test_documents
    ):
        """Test listing user documents with pagination."""
        # Setup test documents
        test_documents = generate_test_documents(count=10)
        
        # Mock Firestore query with limit
        mock_query = Mock()
        mock_docs = [Mock() for _ in range(5)]  # Return 5 documents
        
        for i, mock_doc in enumerate(mock_docs):
            mock_doc.to_dict.return_value = test_documents[i]
        
        mock_query.stream = AsyncMock(return_value=mock_docs)
        mock_firestore.collection().where().order_by().limit.return_value = mock_query
        
        # Execute
        response = client.get(
            "/api/v1/documents/?limit=5&offset=0",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_delete_document_success(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        mock_storage,
        sample_document_data
    ):
        """Test successful document deletion."""
        document_id = "test-doc-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        mock_firestore.collection().document().delete = AsyncMock()
        
        # Mock storage deletion
        mock_storage.bucket().blob().delete = Mock()
        
        # Execute
        response = client.delete(
            f"/api/v1/documents/{document_id}",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_delete_document_not_found(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore
    ):
        """Test deletion of non-existent document."""
        document_id = "nonexistent-doc"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute
        response = client.delete(
            f"/api/v1/documents/{document_id}",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 404
    
    def test_get_download_url(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        mock_storage,
        sample_document_data
    ):
        """Test getting document download URL."""
        document_id = "test-doc-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Mock storage signed URL
        expected_url = "https://signed-download-url.com"
        mock_storage.bucket().blob().generate_signed_url = Mock(return_value=expected_url)
        
        # Execute
        response = client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["download_url"] == expected_url
    
    def test_start_document_analysis(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        sample_document_data
    ):
        """Test starting document analysis."""
        document_id = "test-doc-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Mock job creation
        with patch('app.services.job_service.job_service.create_job') as mock_create_job:
            mock_create_job.return_value = {
                "job_id": "test-job-123",
                "status": "pending"
            }
            
            # Execute
            response = client.post(
                f"/api/v1/documents/{document_id}/analyze",
                headers=authenticated_headers,
                json={"analysis_type": "full"}
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-123"
            assert data["status"] == "pending"
    
    def test_get_document_analysis_results(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        sample_analysis_result
    ):
        """Test getting document analysis results."""
        document_id = "test-doc-123"
        
        # Mock Firestore get for analysis results
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_analysis_result
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute
        response = client.get(
            f"/api/v1/documents/{document_id}/analysis",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert "clauses" in data
        assert "summary" in data
    
    def test_update_document_metadata(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        sample_document_data
    ):
        """Test updating document metadata."""
        document_id = "test-doc-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        mock_firestore.collection().document().update = AsyncMock()
        
        # Execute
        update_data = {
            "title": "Updated Document Title",
            "tags": ["contract", "legal"]
        }
        
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            headers=authenticated_headers,
            json=update_data
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_bulk_document_operations(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore
    ):
        """Test bulk document operations."""
        document_ids = ["doc-1", "doc-2", "doc-3"]
        
        # Mock Firestore batch operations
        mock_batch = Mock()
        mock_firestore.batch.return_value = mock_batch
        mock_batch.commit = AsyncMock()
        
        # Execute bulk delete
        response = client.post(
            "/api/v1/documents/bulk-delete",
            headers=authenticated_headers,
            json={"document_ids": document_ids}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["deleted_count"] == 3
    
    def test_document_search(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        generate_test_documents
    ):
        """Test document search functionality."""
        # Setup test documents
        test_documents = generate_test_documents(count=5)
        
        # Mock Firestore query
        mock_query = Mock()
        mock_docs = []
        
        # Return documents that match search
        for doc_data in test_documents[:2]:  # Return 2 matching documents
            mock_doc = Mock()
            mock_doc.to_dict.return_value = doc_data
            mock_docs.append(mock_doc)
        
        mock_query.stream = AsyncMock(return_value=mock_docs)
        mock_firestore.collection().where().where().order_by.return_value = mock_query
        
        # Execute
        response = client.get(
            "/api/v1/documents/search?q=contract&limit=10",
            headers=authenticated_headers
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["total_count"] == 2
    
    def test_document_sharing(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth,
        mock_firestore,
        sample_document_data
    ):
        """Test document sharing functionality."""
        document_id = "test-doc-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        mock_firestore.collection().document().update = AsyncMock()
        
        # Execute
        share_data = {
            "email": "colleague@example.com",
            "permission": "read",
            "expires_in_days": 7
        }
        
        response = client.post(
            f"/api/v1/documents/{document_id}/share",
            headers=authenticated_headers,
            json=share_data
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "share_link" in data
    
    def test_error_handling_and_validation(
        self,
        client,
        authenticated_headers,
        mock_firebase_auth
    ):
        """Test API error handling and validation."""
        # Test invalid document ID format
        response = client.get(
            "/api/v1/documents/invalid-id-format",
            headers=authenticated_headers
        )
        
        # Should handle gracefully (might be 404 or 400 depending on implementation)
        assert response.status_code in [400, 404]
        
        # Test missing required fields in upload
        response = client.post(
            "/api/v1/documents/upload",
            headers=authenticated_headers
            # Missing file
        )
        
        assert response.status_code == 422  # Validation error