"""
Unit tests for Document Service.

Tests document upload, processing, storage, and retrieval functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import tempfile
import os

from app.services.document_service import document_service
from app.models.document import Document, DocumentStatus
from app.core.exceptions import DocumentError, ValidationError


class TestDocumentService:
    """Test cases for DocumentService."""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(
        self,
        mock_storage,
        mock_firestore,
        sample_document_data,
        temp_pdf_file
    ):
        """Test successful document upload."""
        # Setup
        user_id = "test-user-123"
        
        with open(temp_pdf_file, 'rb') as file:
            file_content = file.read()
        
        # Mock storage upload
        mock_storage.bucket().blob().upload_from_string = Mock()
        mock_storage.bucket().blob().generate_signed_url = Mock(
            return_value="https://test-signed-url.com"
        )
        
        # Mock Firestore save
        mock_firestore.collection().document().set = AsyncMock()
        
        # Execute
        result = await document_service.upload_document(
            file_content=file_content,
            filename="test.pdf",
            content_type="application/pdf",
            user_id=user_id
        )
        
        # Verify
        assert result["status"] == "success"
        assert "document_id" in result
        assert result["filename"] == "test.pdf"
        
        # Verify storage was called
        mock_storage.bucket().blob().upload_from_string.assert_called_once()
        
        # Verify Firestore was called
        mock_firestore.collection().document().set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(self):
        """Test upload with invalid file type."""
        user_id = "test-user-123"
        file_content = b"invalid content"
        
        with pytest.raises(ValidationError) as exc_info:
            await document_service.upload_document(
                file_content=file_content,
                filename="test.txt",
                content_type="text/plain",
                user_id=user_id
            )
        
        assert "Unsupported file type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_document_file_too_large(self):
        """Test upload with file too large."""
        user_id = "test-user-123"
        # Create large file content (> 50MB)
        file_content = b"x" * (51 * 1024 * 1024)
        
        with pytest.raises(ValidationError) as exc_info:
            await document_service.upload_document(
                file_content=file_content,
                filename="large.pdf",
                content_type="application/pdf",
                user_id=user_id
            )
        
        assert "File too large" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        mock_firestore,
        sample_document_data
    ):
        """Test successful document retrieval."""
        # Setup
        document_id = "test-doc-123"
        user_id = "test-user-123"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute
        result = await document_service.get_document(document_id, user_id)
        
        # Verify
        assert result is not None
        assert result["id"] == document_id
        assert result["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_firestore):
        """Test document retrieval when document doesn't exist."""
        # Setup
        document_id = "nonexistent-doc"
        user_id = "test-user-123"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute & Verify
        with pytest.raises(DocumentError) as exc_info:
            await document_service.get_document(document_id, user_id)
        
        assert "Document not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_document_unauthorized(
        self,
        mock_firestore,
        sample_document_data
    ):
        """Test document retrieval with unauthorized user."""
        # Setup
        document_id = "test-doc-123"
        unauthorized_user_id = "unauthorized-user"
        
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Execute & Verify
        with pytest.raises(DocumentError) as exc_info:
            await document_service.get_document(document_id, unauthorized_user_id)
        
        assert "Access denied" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_user_documents(
        self,
        mock_firestore,
        generate_test_documents
    ):
        """Test listing user documents."""
        # Setup
        user_id = "test-user-123"
        test_documents = generate_test_documents(count=3, user_id=user_id)
        
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
        result = await document_service.list_user_documents(user_id)
        
        # Verify
        assert len(result) == 3
        assert all(doc["user_id"] == user_id for doc in result)
    
    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        mock_firestore,
        mock_storage,
        sample_document_data
    ):
        """Test successful document deletion."""
        # Setup
        document_id = "test-doc-123"
        user_id = "test-user-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        mock_firestore.collection().document().delete = AsyncMock()
        
        # Mock storage deletion
        mock_storage.bucket().blob().delete = Mock()
        
        # Execute
        result = await document_service.delete_document(document_id, user_id)
        
        # Verify
        assert result["status"] == "success"
        
        # Verify Firestore deletion
        mock_firestore.collection().document().delete.assert_called_once()
        
        # Verify storage deletion
        mock_storage.bucket().blob().delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_document_status(
        self,
        mock_firestore,
        sample_document_data
    ):
        """Test document status update."""
        # Setup
        document_id = "test-doc-123"
        new_status = DocumentStatus.PROCESSING
        
        # Mock Firestore update
        mock_firestore.collection().document().update = AsyncMock()
        
        # Execute
        await document_service.update_document_status(document_id, new_status)
        
        # Verify
        mock_firestore.collection().document().update.assert_called_once()
        
        # Check update data
        call_args = mock_firestore.collection().document().update.call_args[1]
        assert call_args["status"] == new_status.value
        assert "updated_at" in call_args
    
    @pytest.mark.asyncio
    async def test_get_signed_download_url(
        self,
        mock_storage,
        mock_firestore,
        sample_document_data
    ):
        """Test generating signed download URL."""
        # Setup
        document_id = "test-doc-123"
        user_id = "test-user-123"
        
        # Mock Firestore get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_document_data
        
        mock_firestore.collection().document().get = AsyncMock(return_value=mock_doc)
        
        # Mock storage signed URL
        expected_url = "https://signed-download-url.com"
        mock_storage.bucket().blob().generate_signed_url = Mock(return_value=expected_url)
        
        # Execute
        result = await document_service.get_signed_download_url(document_id, user_id)
        
        # Verify
        assert result == expected_url
        mock_storage.bucket().blob().generate_signed_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_document_content_pdf(self):
        """Test PDF document content validation."""
        # Valid PDF header
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n'
        
        result = document_service._validate_document_content(
            pdf_content, "test.pdf", "application/pdf"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_document_content_invalid_pdf(self):
        """Test invalid PDF document content validation."""
        # Invalid PDF content
        invalid_content = b'This is not a PDF file'
        
        with pytest.raises(ValidationError) as exc_info:
            document_service._validate_document_content(
                invalid_content, "test.pdf", "application/pdf"
            )
        
        assert "Invalid PDF file" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_document_metadata(self, temp_pdf_file):
        """Test document metadata extraction."""
        with open(temp_pdf_file, 'rb') as file:
            file_content = file.read()
        
        metadata = document_service._extract_document_metadata(
            file_content, "test.pdf", "application/pdf"
        )
        
        assert "size" in metadata
        assert "page_count" in metadata
        assert "creation_date" in metadata
        assert metadata["size"] == len(file_content)
    
    @pytest.mark.asyncio
    async def test_storage_error_handling(
        self,
        mock_storage,
        mock_firestore,
        temp_pdf_file
    ):
        """Test handling of storage errors during upload."""
        # Setup
        user_id = "test-user-123"
        
        with open(temp_pdf_file, 'rb') as file:
            file_content = file.read()
        
        # Mock storage error
        mock_storage.bucket().blob().upload_from_string.side_effect = Exception("Storage error")
        
        # Execute & Verify
        with pytest.raises(DocumentError) as exc_info:
            await document_service.upload_document(
                file_content=file_content,
                filename="test.pdf",
                content_type="application/pdf",
                user_id=user_id
            )
        
        assert "Failed to upload document" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads(
        self,
        mock_storage,
        mock_firestore,
        temp_pdf_file
    ):
        """Test handling of concurrent document uploads."""
        import asyncio
        
        user_id = "test-user-123"
        
        with open(temp_pdf_file, 'rb') as file:
            file_content = file.read()
        
        # Mock successful operations
        mock_storage.bucket().blob().upload_from_string = Mock()
        mock_storage.bucket().blob().generate_signed_url = Mock(
            return_value="https://test-url.com"
        )
        mock_firestore.collection().document().set = AsyncMock()
        
        # Execute concurrent uploads
        tasks = []
        for i in range(5):
            task = document_service.upload_document(
                file_content=file_content,
                filename=f"test-{i}.pdf",
                content_type="application/pdf",
                user_id=user_id
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all uploads succeeded
        assert len(results) == 5
        assert all(result["status"] == "success" for result in results)
        
        # Verify unique document IDs
        document_ids = [result["document_id"] for result in results]
        assert len(set(document_ids)) == 5