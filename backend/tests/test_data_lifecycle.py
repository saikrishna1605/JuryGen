"""
Tests for Data Lifecycle and Retention Management Service.

Tests cover:
- Retention policy management
- User consent management
- Data residency controls
- Data export and deletion
- GDPR compliance features
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.data_lifecycle import (
    DataLifecycleService,
    DataCategory,
    RetentionPeriod,
    DataResidency,
    ConsentType
)
from app.core.exceptions import DatabaseError, StorageError


@pytest.fixture
def mock_firestore_service():
    """Mock Firestore service."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_storage_client():
    """Mock Cloud Storage client."""
    mock = Mock()
    return mock


@pytest.fixture
def data_lifecycle_service(mock_firestore_service, mock_storage_client):
    """Create DataLifecycleService with mocked dependencies."""
    service = DataLifecycleService()
    service.firestore_service = mock_firestore_service
    service.storage_client = mock_storage_client
    return service


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "data_residency": DataResidency.US,
        "consents": {
            ConsentType.DATA_PROCESSING: {
                "granted": True,
                "timestamp": datetime.utcnow()
            }
        }
    }


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "id": "doc-123",
        "user_id": "test-user-123",
        "filename": "test.pdf",
        "size_bytes": 1024000,
        "storage_url": "gs://bucket/doc-123.pdf",
        "retention_policy": {
            "data_category": DataCategory.DOCUMENTS,
            "retention_days": 30,
            "expiration_date": datetime.utcnow() + timedelta(days=30)
        }
    }


class TestRetentionPolicyManagement:
    """Test retention policy management functionality."""

    @pytest.mark.asyncio
    async def test_create_retention_policy_success(self, data_lifecycle_service, mock_firestore_service):
        """Test successful retention policy creation."""
        # Arrange
        mock_firestore_service.create_document.return_value = "policy-123"
        
        # Act
        policy_id = await data_lifecycle_service.create_retention_policy(
            user_id="test-user-123",
            data_category=DataCategory.DOCUMENTS,
            retention_period=RetentionPeriod.DAYS_30
        )
        
        # Assert
        assert policy_id == "policy-123"
        mock_firestore_service.create_document.assert_called_once()
        call_args = mock_firestore_service.create_document.call_args
        assert call_args[1]["collection"] == "retention_policies"
        assert call_args[1]["data"]["user_id"] == "test-user-123"
        assert call_args[1]["data"]["data_category"] == DataCategory.DOCUMENTS
        assert call_args[1]["data"]["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_create_retention_policy_custom_days(self, data_lifecycle_service, mock_firestore_service):
        """Test retention policy creation with custom days."""
        # Arrange
        mock_firestore_service.create_document.return_value = "policy-123"
        
        # Act
        policy_id = await data_lifecycle_service.create_retention_policy(
            user_id="test-user-123",
            data_category=DataCategory.DOCUMENTS,
            retention_period=RetentionPeriod.DAYS_30,
            custom_days=45
        )
        
        # Assert
        assert policy_id == "policy-123"
        call_args = mock_firestore_service.create_document.call_args
        assert call_args[1]["data"]["retention_days"] == 45

    @pytest.mark.asyncio
    async def test_create_retention_policy_permanent(self, data_lifecycle_service, mock_firestore_service):
        """Test retention policy creation for permanent storage."""
        # Arrange
        mock_firestore_service.create_document.return_value = "policy-123"
        
        # Act
        policy_id = await data_lifecycle_service.create_retention_policy(
            user_id="test-user-123",
            data_category=DataCategory.USER_PREFERENCES,
            retention_period=RetentionPeriod.PERMANENT
        )
        
        # Assert
        call_args = mock_firestore_service.create_document.call_args
        assert call_args[1]["data"]["retention_days"] == -1
        assert call_args[1]["data"]["expiration_date"] is None

    @pytest.mark.asyncio
    async def test_apply_retention_to_document(self, data_lifecycle_service, mock_firestore_service):
        """Test applying retention policy to a document."""
        # Arrange
        mock_firestore_service.query_documents.return_value = []  # No custom policy
        
        # Act
        await data_lifecycle_service.apply_retention_to_document(
            document_id="doc-123",
            user_id="test-user-123",
            data_category=DataCategory.DOCUMENTS
        )
        
        # Assert
        mock_firestore_service.update_document.assert_called_once()
        call_args = mock_firestore_service.update_document.call_args
        assert call_args[1]["collection"] == "documents"
        assert call_args[1]["document_id"] == "doc-123"
        assert "retention_policy" in call_args[1]["data"]


class TestConsentManagement:
    """Test user consent management functionality."""

    @pytest.mark.asyncio
    async def test_manage_user_consent_grant(self, data_lifecycle_service, mock_firestore_service):
        """Test granting user consent."""
        # Arrange
        mock_firestore_service.create_document.return_value = "consent-123"
        
        # Act
        consent_id = await data_lifecycle_service.manage_user_consent(
            user_id="test-user-123",
            consent_type=ConsentType.MODEL_TRAINING,
            granted=True,
            metadata={"ip_address": "192.168.1.1"}
        )
        
        # Assert
        assert consent_id == "consent-123"
        mock_firestore_service.create_document.assert_called_once()
        mock_firestore_service.update_document.assert_called_once()
        
        # Check consent record creation
        create_call = mock_firestore_service.create_document.call_args
        assert create_call[1]["collection"] == "user_consents"
        assert create_call[1]["data"]["granted"] is True
        assert create_call[1]["data"]["consent_type"] == ConsentType.MODEL_TRAINING
        
        # Check user profile update
        update_call = mock_firestore_service.update_document.call_args
        assert update_call[1]["collection"] == "users"
        assert update_call[1]["document_id"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_manage_user_consent_revoke(self, data_lifecycle_service, mock_firestore_service):
        """Test revoking user consent."""
        # Arrange
        mock_firestore_service.create_document.return_value = "consent-123"
        
        # Act
        consent_id = await data_lifecycle_service.manage_user_consent(
            user_id="test-user-123",
            consent_type=ConsentType.ANALYTICS,
            granted=False
        )
        
        # Assert
        create_call = mock_firestore_service.create_document.call_args
        assert create_call[1]["data"]["granted"] is False

    @pytest.mark.asyncio
    async def test_check_user_consent_granted(self, data_lifecycle_service, mock_firestore_service):
        """Test checking granted user consent."""
        # Arrange
        mock_firestore_service.get_document.return_value = {
            "consents": {
                ConsentType.DATA_PROCESSING: {
                    "granted": True,
                    "timestamp": datetime.utcnow()
                }
            }
        }
        
        # Act
        has_consent = await data_lifecycle_service.check_user_consent(
            user_id="test-user-123",
            consent_type=ConsentType.DATA_PROCESSING
        )
        
        # Assert
        assert has_consent is True

    @pytest.mark.asyncio
    async def test_check_user_consent_not_granted(self, data_lifecycle_service, mock_firestore_service):
        """Test checking non-granted user consent."""
        # Arrange
        mock_firestore_service.get_document.return_value = {
            "consents": {
                ConsentType.DATA_PROCESSING: {
                    "granted": False,
                    "timestamp": datetime.utcnow()
                }
            }
        }
        
        # Act
        has_consent = await data_lifecycle_service.check_user_consent(
            user_id="test-user-123",
            consent_type=ConsentType.DATA_PROCESSING
        )
        
        # Assert
        assert has_consent is False

    @pytest.mark.asyncio
    async def test_check_user_consent_no_record(self, data_lifecycle_service, mock_firestore_service):
        """Test checking consent when no record exists."""
        # Arrange
        mock_firestore_service.get_document.return_value = None
        
        # Act
        has_consent = await data_lifecycle_service.check_user_consent(
            user_id="test-user-123",
            consent_type=ConsentType.DATA_PROCESSING
        )
        
        # Assert
        assert has_consent is False


class TestDataResidency:
    """Test data residency management functionality."""

    @pytest.mark.asyncio
    async def test_set_data_residency(self, data_lifecycle_service, mock_firestore_service):
        """Test setting data residency preference."""
        # Act
        await data_lifecycle_service.set_data_residency(
            user_id="test-user-123",
            residency=DataResidency.EU
        )
        
        # Assert
        mock_firestore_service.update_document.assert_called_once()
        call_args = mock_firestore_service.update_document.call_args
        assert call_args[1]["collection"] == "users"
        assert call_args[1]["document_id"] == "test-user-123"
        assert call_args[1]["data"]["data_residency"] == DataResidency.EU


class TestDataExportAndDeletion:
    """Test data export and deletion functionality."""

    @pytest.mark.asyncio
    async def test_export_user_data(self, data_lifecycle_service, mock_firestore_service, sample_user_data):
        """Test exporting user data."""
        # Arrange
        mock_firestore_service.get_document.return_value = sample_user_data
        mock_firestore_service.query_documents.side_effect = [
            [{"id": "doc-1", "filename": "test.pdf"}],  # documents
            [{"id": "job-1", "status": "completed"}],   # jobs
            [{"id": "consent-1", "granted": True}],     # consents
            [{"id": "audit-1", "action": "upload"}]     # audit logs
        ]
        mock_firestore_service.create_document.return_value = "export-123"
        
        # Act
        export_data = await data_lifecycle_service.export_user_data("test-user-123")
        
        # Assert
        assert "user_profile" in export_data
        assert "documents" in export_data
        assert "jobs" in export_data
        assert "consents" in export_data
        assert "audit_logs" in export_data
        assert export_data["export_version"] == "1.0"
        
        # Verify export logging
        mock_firestore_service.create_document.assert_called()
        log_call = mock_firestore_service.create_document.call_args
        assert log_call[1]["collection"] == "data_exports"

    @pytest.mark.asyncio
    async def test_delete_user_data(self, data_lifecycle_service, mock_firestore_service, sample_document):
        """Test deleting all user data."""
        # Arrange
        mock_firestore_service.query_documents.side_effect = [
            [sample_document],  # documents
            [{"id": "job-1"}],  # jobs
            [{"id": "consent-1"}],  # consents
            [{"id": "policy-1"}],  # policies
            [{"id": "audit-1"}]  # audit logs
        ]
        mock_firestore_service.create_document.return_value = "deletion-123"
        
        # Mock storage operations
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        data_lifecycle_service.storage_client.bucket.return_value = mock_bucket
        
        # Act
        deletion_counts = await data_lifecycle_service.delete_user_data("test-user-123")
        
        # Assert
        assert "documents" in deletion_counts
        assert "jobs" in deletion_counts
        assert "consents" in deletion_counts
        assert "policies" in deletion_counts
        assert "anonymized_logs" in deletion_counts
        assert "user_profile" in deletion_counts
        
        # Verify storage cleanup
        mock_blob.delete.assert_called_once()
        
        # Verify deletion logging
        mock_firestore_service.create_document.assert_called()
        log_call = mock_firestore_service.create_document.call_args
        assert log_call[1]["collection"] == "data_deletions"


class TestDataCleanup:
    """Test automated data cleanup functionality."""

    @pytest.mark.asyncio
    async def test_delete_expired_data(self, data_lifecycle_service, mock_firestore_service, sample_document):
        """Test deleting expired data."""
        # Arrange
        expired_document = sample_document.copy()
        expired_document["retention_policy"]["expiration_date"] = datetime.utcnow() - timedelta(days=1)
        
        mock_firestore_service.query_documents.side_effect = [
            [expired_document],  # expired documents
            [{"id": "log-1", "timestamp": datetime.utcnow() - timedelta(days=2556)}],  # expired audit logs
            [{"id": "pii-1", "timestamp": datetime.utcnow() - timedelta(days=1096)}]   # expired PII logs
        ]
        
        # Mock storage operations
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        data_lifecycle_service.storage_client.bucket.return_value = mock_bucket
        
        # Act
        deletion_counts = await data_lifecycle_service.delete_expired_data(batch_size=10)
        
        # Assert
        assert deletion_counts[DataCategory.DOCUMENTS] == 1
        assert deletion_counts[DataCategory.AUDIT_LOGS] == 1
        assert deletion_counts[DataCategory.PII_LOGS] == 1
        
        # Verify storage cleanup
        mock_blob.delete.assert_called()

    @pytest.mark.asyncio
    async def test_get_user_data_summary(self, data_lifecycle_service, mock_firestore_service, sample_user_data):
        """Test getting user data summary."""
        # Arrange
        mock_firestore_service.get_document.return_value = sample_user_data
        mock_firestore_service.query_documents.side_effect = [
            [{"size_bytes": 1000, "retention_policy": {"data_category": "documents"}}],  # documents
            [{"data_category": "documents", "retention_period": "30_days", "retention_days": 30}]  # policies
        ]
        
        # Act
        summary = await data_lifecycle_service.get_user_data_summary("test-user-123")
        
        # Assert
        assert summary["user_id"] == "test-user-123"
        assert summary["data_residency"] == DataResidency.US
        assert summary["total_documents"] == 1
        assert summary["storage_usage_bytes"] == 1000
        assert "storage_by_category" in summary
        assert "retention_policies" in summary
        assert "consents" in summary


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_retention_days(self, data_lifecycle_service):
        """Test retention period to days conversion."""
        assert data_lifecycle_service._get_retention_days(RetentionPeriod.DAYS_7) == 7
        assert data_lifecycle_service._get_retention_days(RetentionPeriod.DAYS_30) == 30
        assert data_lifecycle_service._get_retention_days(RetentionPeriod.YEAR_1) == 365
        assert data_lifecycle_service._get_retention_days(RetentionPeriod.PERMANENT) == -1

    @pytest.mark.asyncio
    async def test_get_user_retention_policy(self, data_lifecycle_service, mock_firestore_service):
        """Test getting user retention policy."""
        # Arrange
        mock_firestore_service.query_documents.return_value = [
            {"data_category": "documents", "retention_days": 30}
        ]
        
        # Act
        policy = await data_lifecycle_service._get_user_retention_policy(
            "test-user-123", DataCategory.DOCUMENTS
        )
        
        # Assert
        assert policy is not None
        assert policy["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_get_user_retention_policy_not_found(self, data_lifecycle_service, mock_firestore_service):
        """Test getting user retention policy when none exists."""
        # Arrange
        mock_firestore_service.query_documents.return_value = []
        
        # Act
        policy = await data_lifecycle_service._get_user_retention_policy(
            "test-user-123", DataCategory.DOCUMENTS
        )
        
        # Assert
        assert policy is None


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_create_retention_policy_database_error(self, data_lifecycle_service, mock_firestore_service):
        """Test handling database error during policy creation."""
        # Arrange
        mock_firestore_service.create_document.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(DatabaseError):
            await data_lifecycle_service.create_retention_policy(
                user_id="test-user-123",
                data_category=DataCategory.DOCUMENTS,
                retention_period=RetentionPeriod.DAYS_30
            )

    @pytest.mark.asyncio
    async def test_export_user_data_database_error(self, data_lifecycle_service, mock_firestore_service):
        """Test handling database error during data export."""
        # Arrange
        mock_firestore_service.get_document.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(DatabaseError):
            await data_lifecycle_service.export_user_data("test-user-123")

    @pytest.mark.asyncio
    async def test_delete_document_storage_error(self, data_lifecycle_service, mock_firestore_service):
        """Test handling storage error during document deletion."""
        # Arrange
        sample_doc = {
            "id": "doc-123",
            "storage_url": "gs://bucket/doc-123.pdf"
        }
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.delete.side_effect = Exception("Storage error")
        mock_bucket.blob.return_value = mock_blob
        data_lifecycle_service.storage_client.bucket.return_value = mock_bucket
        
        # Act & Assert
        with pytest.raises(StorageError):
            await data_lifecycle_service._delete_document_and_assets(sample_doc)


if __name__ == "__main__":
    pytest.main([__file__])