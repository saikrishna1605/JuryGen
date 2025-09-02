"""
Tests for PII Detection and Masking Service.

Tests cover:
- PII detection functionality
- Masking strategies
- Validation and compliance
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.pii_detection import (
    PIIDetectionService,
    PIIFinding,
    PIIType,
    MaskingType,
    pii_detection_service
)
from app.core.exceptions import PIIDetectionError


class TestPIIDetectionService:
    """Test suite for PII Detection Service."""
    
    @pytest.fixture
    def service(self):
        """Create PII detection service instance."""
        return PIIDetectionService()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content with PII for testing."""
        return """
        John Doe's email is john.doe@example.com and his phone number is (555) 123-4567.
        His SSN is 123-45-6789 and credit card number is 4532-1234-5678-9012.
        He lives at 123 Main Street, Anytown, NY 12345.
        """
    
    @pytest.fixture
    def mock_dlp_response(self):
        """Mock DLP API response."""
        mock_finding = Mock()
        mock_finding.info_type.name = "EMAIL_ADDRESS"
        mock_finding.likelihood.name = "VERY_LIKELY"
        mock_finding.location.byte_range.start = 20
        mock_finding.location.byte_range.end = 40
        mock_finding.quote = "john.doe@example.com"
        
        mock_response = Mock()
        mock_response.result.findings = [mock_finding]
        
        return mock_response
    
    @pytest.fixture
    def sample_findings(self):
        """Sample PII findings for testing."""
        return [
            PIIFinding(
                info_type=PIIType.EMAIL_ADDRESS,
                likelihood="VERY_LIKELY",
                start_offset=20,
                end_offset=40,
                original_text="john.doe@example.com",
                confidence=0.9
            ),
            PIIFinding(
                info_type=PIIType.PHONE_NUMBER,
                likelihood="LIKELY",
                start_offset=65,
                end_offset=79,
                original_text="(555) 123-4567",
                confidence=0.8
            ),
            PIIFinding(
                info_type=PIIType.SSN,
                likelihood="VERY_LIKELY",
                start_offset=95,
                end_offset=106,
                original_text="123-45-6789",
                confidence=0.95
            )
        ]

    @pytest.mark.asyncio
    async def test_detect_pii_success(self, service, sample_content, mock_dlp_response):
        """Test successful PII detection."""
        with patch.object(service.dlp_client, 'inspect_content', return_value=mock_dlp_response):
            findings = await service.detect_pii(sample_content)
            
            assert len(findings) == 1
            assert findings[0].info_type == "EMAIL_ADDRESS"
            assert findings[0].original_text == "john.doe@example.com"
            assert findings[0].confidence == 0.9

    @pytest.mark.asyncio
    async def test_detect_pii_with_custom_info_types(self, service, sample_content, mock_dlp_response):
        """Test PII detection with custom info types."""
        custom_types = [PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER]
        
        with patch.object(service.dlp_client, 'inspect_content', return_value=mock_dlp_response):
            findings = await service.detect_pii(
                sample_content,
                info_types=custom_types,
                min_likelihood="LIKELY"
            )
            
            assert len(findings) == 1

    @pytest.mark.asyncio
    async def test_detect_pii_api_error(self, service, sample_content):
        """Test PII detection with API error."""
        from google.api_core import exceptions as gcp_exceptions
        
        with patch.object(service.dlp_client, 'inspect_content', 
                         side_effect=gcp_exceptions.GoogleAPIError("API Error")):
            with pytest.raises(PIIDetectionError):
                await service.detect_pii(sample_content)

    @pytest.mark.asyncio
    async def test_mask_pii_redact(self, service, sample_findings):
        """Test PII masking with redact strategy."""
        content = "Email: john.doe@example.com Phone: (555) 123-4567 SSN: 123-45-6789"
        
        masking_config = {
            PIIType.EMAIL_ADDRESS: MaskingType.REDACT,
            PIIType.PHONE_NUMBER: MaskingType.REDACT,
            PIIType.SSN: MaskingType.REDACT
        }
        
        masked_content, updated_findings = await service.mask_pii(
            content, sample_findings, masking_config
        )
        
        assert "[REDACTED]" in masked_content
        assert "john.doe@example.com" not in masked_content
        assert len(updated_findings) == 3

    @pytest.mark.asyncio
    async def test_mask_pii_mask_strategy(self, service, sample_findings):
        """Test PII masking with mask strategy."""
        content = "Email: john.doe@example.com Phone: (555) 123-4567 SSN: 123-45-6789"
        
        masking_config = {
            PIIType.EMAIL_ADDRESS: MaskingType.MASK,
            PIIType.PHONE_NUMBER: MaskingType.MASK,
            PIIType.SSN: MaskingType.MASK
        }
        
        masked_content, updated_findings = await service.mask_pii(
            content, sample_findings, masking_config
        )
        
        assert "*" in masked_content
        assert "john.doe@example.com" not in masked_content
        assert all(finding.masking_type == MaskingType.MASK for finding in updated_findings)

    @pytest.mark.asyncio
    async def test_mask_pii_partial_strategy(self, service):
        """Test PII masking with partial strategy."""
        content = "Email: john.doe@example.com"
        findings = [
            PIIFinding(
                info_type=PIIType.EMAIL_ADDRESS,
                likelihood="VERY_LIKELY",
                start_offset=7,
                end_offset=27,
                original_text="john.doe@example.com",
                confidence=0.9
            )
        ]
        
        masking_config = {PIIType.EMAIL_ADDRESS: MaskingType.PARTIAL}
        
        masked_content, updated_findings = await service.mask_pii(
            content, findings, masking_config
        )
        
        # Should show partial email like "jo***@example.com"
        assert "jo***@example.com" in masked_content
        assert updated_findings[0].masked_text == "jo***@example.com"

    @pytest.mark.asyncio
    async def test_mask_pii_replace_strategy(self, service, sample_findings):
        """Test PII masking with replace strategy."""
        content = "Email: john.doe@example.com Phone: (555) 123-4567 SSN: 123-45-6789"
        
        masking_config = {
            PIIType.EMAIL_ADDRESS: MaskingType.REPLACE,
            PIIType.PHONE_NUMBER: MaskingType.REPLACE,
            PIIType.SSN: MaskingType.REPLACE
        }
        
        masked_content, updated_findings = await service.mask_pii(
            content, sample_findings, masking_config
        )
        
        assert "[EMAIL]" in masked_content
        assert "[PHONE]" in masked_content
        assert "john.doe@example.com" not in masked_content

    @pytest.mark.asyncio
    async def test_detect_and_mask_pii(self, service, sample_content, mock_dlp_response):
        """Test combined detect and mask operation."""
        with patch.object(service.dlp_client, 'inspect_content', return_value=mock_dlp_response):
            masked_content, findings = await service.detect_and_mask_pii(
                content=sample_content,
                masking_config={PIIType.EMAIL_ADDRESS: MaskingType.MASK}
            )
            
            assert len(findings) == 1
            assert "john.doe@example.com" not in masked_content
            assert "*" in masked_content

    @pytest.mark.asyncio
    async def test_create_redaction_preview(self, service, sample_content, sample_findings):
        """Test redaction preview creation."""
        preview = await service.create_redaction_preview(sample_content, sample_findings)
        
        assert preview["original_content"] == sample_content
        assert len(preview["pii_locations"]) == 3
        assert preview["summary"]["total_findings"] == 3
        assert PIIType.EMAIL_ADDRESS in preview["summary"]["by_type"]
        assert preview["summary"]["risk_level"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_validate_masking_quality_success(self, service, sample_findings):
        """Test successful masking validation."""
        original_content = "Email: john.doe@example.com Phone: (555) 123-4567"
        masked_content = "Email: [EMAIL] Phone: [PHONE]"
        
        # Mock the re-scan to return no findings
        with patch.object(service, 'detect_pii', return_value=[]):
            validation = await service.validate_masking_quality(
                original_content, masked_content, sample_findings[:2]
            )
            
            assert validation["is_valid"] is True
            assert validation["coverage"] == 1.0
            assert validation["leakage_detected"] is False

    @pytest.mark.asyncio
    async def test_validate_masking_quality_leakage(self, service, sample_findings):
        """Test masking validation with PII leakage."""
        original_content = "Email: john.doe@example.com Phone: (555) 123-4567"
        masked_content = "Email: john.doe@example.com Phone: [PHONE]"  # Email not masked
        
        # Mock the re-scan to return remaining PII
        remaining_finding = PIIFinding(
            info_type=PIIType.EMAIL_ADDRESS,
            likelihood="VERY_LIKELY",
            start_offset=7,
            end_offset=27,
            original_text="john.doe@example.com",
            confidence=0.9
        )
        
        with patch.object(service, 'detect_pii', return_value=[remaining_finding]):
            validation = await service.validate_masking_quality(
                original_content, masked_content, sample_findings[:2]
            )
            
            assert validation["is_valid"] is False
            assert validation["leakage_detected"] is True
            assert len(validation["issues"]) > 0

    @pytest.mark.asyncio
    async def test_log_pii_audit(self, service):
        """Test PII audit logging."""
        with patch.object(service.firestore_service, 'create_document', return_value="audit_123") as mock_create:
            audit_id = await service.log_pii_audit(
                user_id="user_123",
                document_id="doc_456",
                action="detect",
                findings=[],
                metadata={"test": "data"}
            )
            
            assert audit_id == "audit_123"
            mock_create.assert_called_once()
            
            # Verify audit data structure
            call_args = mock_create.call_args
            assert call_args[1]["collection"] == "pii_audit_logs"
            audit_data = call_args[1]["data"]
            assert audit_data["user_id"] == "user_123"
            assert audit_data["document_id"] == "doc_456"
            assert audit_data["action"] == "detect"

    @pytest.mark.asyncio
    async def test_get_compliance_report(self, service):
        """Test compliance report generation."""
        mock_logs = [
            {
                "user_id": "user_1",
                "document_id": "doc_1",
                "action": "detect",
                "timestamp": datetime.utcnow(),
                "findings_count": 5,
                "pii_types": ["EMAIL_ADDRESS", "PHONE_NUMBER"],
                "high_confidence_count": 3
            },
            {
                "user_id": "user_2",
                "document_id": "doc_2",
                "action": "mask",
                "timestamp": datetime.utcnow(),
                "findings_count": 2,
                "pii_types": ["SSN"],
                "high_confidence_count": 2
            }
        ]
        
        with patch.object(service.firestore_service, 'query_documents', return_value=mock_logs):
            report = await service.get_compliance_report()
            
            assert report["summary"]["total_operations"] == 2
            assert report["summary"]["unique_users"] == 2
            assert report["summary"]["total_pii_findings"] == 7
            assert "detect" in report["by_action"]
            assert "mask" in report["by_action"]
            assert "EMAIL_ADDRESS" in report["by_pii_type"]

    def test_apply_masking_strategies(self, service):
        """Test different masking strategies."""
        test_cases = [
            ("john.doe@example.com", MaskingType.REDACT, PIIType.EMAIL_ADDRESS, "[REDACTED]"),
            ("john.doe@example.com", MaskingType.MASK, PIIType.EMAIL_ADDRESS, "*******************"),
            ("john.doe@example.com", MaskingType.REPLACE, PIIType.EMAIL_ADDRESS, "[EMAIL]"),
            ("john.doe@example.com", MaskingType.PARTIAL, PIIType.EMAIL_ADDRESS, "jo***@example.com"),
            ("John Smith", MaskingType.REPLACE, PIIType.PERSON_NAME, "[NAME]"),
            ("123-45-6789", MaskingType.MASK, PIIType.SSN, "***********"),
        ]
        
        for text, masking_type, info_type, expected in test_cases:
            result = service._apply_masking(text, masking_type, info_type)
            if masking_type == MaskingType.HASH:
                assert result.startswith("[HASH:")
            else:
                assert result == expected

    def test_pii_finding_to_dict(self):
        """Test PIIFinding serialization."""
        finding = PIIFinding(
            info_type=PIIType.EMAIL_ADDRESS,
            likelihood="VERY_LIKELY",
            start_offset=10,
            end_offset=30,
            original_text="test@example.com",
            confidence=0.9
        )
        finding.masked_text = "[EMAIL]"
        finding.masking_type = MaskingType.REPLACE
        
        result = finding.to_dict()
        
        assert result["info_type"] == PIIType.EMAIL_ADDRESS
        assert result["likelihood"] == "VERY_LIKELY"
        assert result["start_offset"] == 10
        assert result["end_offset"] == 30
        assert result["original_text"] == "test@example.com"
        assert result["masked_text"] == "[EMAIL]"
        assert result["confidence"] == 0.9
        assert result["masking_type"] == MaskingType.REPLACE


class TestPIIDetectionIntegration:
    """Integration tests for PII detection service."""
    
    @pytest.mark.asyncio
    async def test_full_pii_workflow(self):
        """Test complete PII detection and masking workflow."""
        content = """
        Dear John Smith,
        
        Your account john.smith@email.com has been updated.
        Please call us at (555) 123-4567 if you have questions.
        
        Your SSN ending in 6789 is on file.
        """
        
        service = PIIDetectionService()
        
        # Mock DLP responses
        mock_findings = [
            Mock(
                info_type=Mock(name="PERSON_NAME"),
                likelihood=Mock(name="VERY_LIKELY"),
                location=Mock(byte_range=Mock(start=14, end=24)),
                quote="John Smith"
            ),
            Mock(
                info_type=Mock(name="EMAIL_ADDRESS"),
                likelihood=Mock(name="VERY_LIKELY"),
                location=Mock(byte_range=Mock(start=47, end=68)),
                quote="john.smith@email.com"
            )
        ]
        
        mock_response = Mock()
        mock_response.result.findings = mock_findings
        
        with patch.object(service.dlp_client, 'inspect_content', return_value=mock_response):
            with patch.object(service.firestore_service, 'create_document', return_value="audit_123"):
                # Test detection
                findings = await service.detect_pii(content)
                assert len(findings) == 2
                
                # Test masking
                masked_content, masked_findings = await service.mask_pii(content, findings)
                assert "John Smith" not in masked_content
                assert "john.smith@email.com" not in masked_content
                
                # Test validation
                with patch.object(service, 'detect_pii', return_value=[]):
                    validation = await service.validate_masking_quality(
                        content, masked_content, masked_findings
                    )
                    assert validation["is_valid"] is True

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling in PII detection service."""
        service = PIIDetectionService()
        
        # Test DLP API failure
        with patch.object(service.dlp_client, 'inspect_content', 
                         side_effect=Exception("Network error")):
            with pytest.raises(PIIDetectionError):
                await service.detect_pii("test content")
        
        # Test Firestore failure (should not break main functionality)
        with patch.object(service.firestore_service, 'create_document', 
                         side_effect=Exception("Firestore error")):
            with pytest.raises(Exception):
                await service.log_pii_audit("user", "doc", "action", [])


if __name__ == "__main__":
    pytest.main([__file__])