"""
PII Detection and Masking Service using Google Cloud DLP.

This service handles:
- Cloud DLP integration for sensitive data detection
- Client-side redaction tools and preview
- PII audit logging and compliance reporting
- Configurable masking and anonymization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import json
import re
from enum import Enum

from google.cloud import dlp_v2
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..core.exceptions import PIIDetectionError
from ..services.firestore import FirestoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class PIIType(str, Enum):
    """Types of PII that can be detected."""
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    PERSON_NAME = "PERSON_NAME"
    SSN = "US_SOCIAL_SECURITY_NUMBER"
    CREDIT_CARD = "CREDIT_CARD_NUMBER"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    ADDRESS = "STREET_ADDRESS"
    PASSPORT = "PASSPORT"
    DRIVER_LICENSE = "US_DRIVERS_LICENSE_NUMBER"
    BANK_ACCOUNT = "US_BANK_ROUTING_MICR"
    IP_ADDRESS = "IP_ADDRESS"
    MEDICAL_RECORD = "MEDICAL_RECORD_NUMBER"
    TAX_ID = "US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER"


class MaskingType(str, Enum):
    """Types of masking that can be applied."""
    REDACT = "redact"  # Remove completely
    MASK = "mask"      # Replace with asterisks
    HASH = "hash"      # Replace with hash
    REPLACE = "replace"  # Replace with placeholder
    PARTIAL = "partial"  # Show only partial (e.g., first 2 and last 2 chars)


class PIIFinding:
    """Represents a PII finding from DLP analysis."""
    
    def __init__(
        self,
        info_type: str,
        likelihood: str,
        start_offset: int,
        end_offset: int,
        original_text: str,
        confidence: float = 0.0
    ):
        self.info_type = info_type
        self.likelihood = likelihood
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.original_text = original_text
        self.confidence = confidence
        self.masked_text = ""
        self.masking_type = MaskingType.MASK
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "info_type": self.info_type,
            "likelihood": self.likelihood,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "original_text": self.original_text,
            "masked_text": self.masked_text,
            "confidence": self.confidence,
            "masking_type": self.masking_type
        }


class PIIDetectionService:
    """
    Service for detecting and masking PII in legal documents.
    
    Integrates with Google Cloud DLP to identify sensitive information
    and provides various masking strategies for privacy protection.
    """
    
    def __init__(self):
        """Initialize the PII detection service."""
        # Initialize DLP client
        self.dlp_client = dlp_v2.DlpServiceClient()
        
        # Initialize Firestore for audit logging
        self.firestore_service = FirestoreService()
        
        # Project configuration
        self.project_id = settings.DLP_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.DLP_LOCATION
        
        # Default info types to detect
        self.default_info_types = [
            PIIType.EMAIL_ADDRESS,
            PIIType.PHONE_NUMBER,
            PIIType.PERSON_NAME,
            PIIType.SSN,
            PIIType.CREDIT_CARD,
            PIIType.DATE_OF_BIRTH,
            PIIType.ADDRESS,
            PIIType.PASSPORT,
            PIIType.DRIVER_LICENSE,
            PIIType.BANK_ACCOUNT,
            PIIType.IP_ADDRESS,
            PIIType.MEDICAL_RECORD,
            PIIType.TAX_ID
        ]
        
        # Confidence thresholds for different likelihood levels
        self.likelihood_scores = {
            "VERY_UNLIKELY": 0.1,
            "UNLIKELY": 0.3,
            "POSSIBLE": 0.5,
            "LIKELY": 0.7,
            "VERY_LIKELY": 0.9
        }
    
    async def detect_pii(
        self,
        content: str,
        content_type: str = "text/plain",
        info_types: Optional[List[str]] = None,
        min_likelihood: str = "POSSIBLE"
    ) -> List[PIIFinding]:
        """
        Detect PII in the provided content using Cloud DLP.
        
        Args:
            content: Text content to analyze
            content_type: MIME type of content
            info_types: Specific PII types to detect (uses defaults if None)
            min_likelihood: Minimum likelihood threshold
            
        Returns:
            List of PII findings
        """
        try:
            # Use default info types if none specified
            if info_types is None:
                info_types = self.default_info_types
            
            # Build DLP request
            inspect_config = {
                "info_types": [{"name": info_type} for info_type in info_types],
                "min_likelihood": min_likelihood,
                "include_quote": True,
                "limits": {
                    "max_findings_per_info_type": 100,
                    "max_findings_per_request": 1000
                }
            }
            
            # Create content item
            item = {"value": content}
            
            # Build parent path
            parent = f"projects/{self.project_id}/locations/{self.location}"
            
            # Call DLP API
            response = self.dlp_client.inspect_content(
                request={
                    "parent": parent,
                    "inspect_config": inspect_config,
                    "item": item
                }
            )
            
            # Process findings
            findings = []
            for finding in response.result.findings:
                pii_finding = PIIFinding(
                    info_type=finding.info_type.name,
                    likelihood=finding.likelihood.name,
                    start_offset=finding.location.byte_range.start,
                    end_offset=finding.location.byte_range.end,
                    original_text=finding.quote,
                    confidence=self.likelihood_scores.get(finding.likelihood.name, 0.5)
                )
                findings.append(pii_finding)
            
            logger.info(f"Detected {len(findings)} PII findings in content")
            return findings
            
        except gcp_exceptions.GoogleAPIError as e:
            logger.error(f"DLP API error: {e}")
            raise PIIDetectionError(f"Failed to detect PII: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in PII detection: {e}")
            raise PIIDetectionError(f"PII detection failed: {e}")
    
    async def mask_pii(
        self,
        content: str,
        findings: List[PIIFinding],
        masking_config: Optional[Dict[str, MaskingType]] = None
    ) -> Tuple[str, List[PIIFinding]]:
        """
        Apply masking to detected PII in content.
        
        Args:
            content: Original content
            findings: PII findings to mask
            masking_config: Custom masking configuration per PII type
            
        Returns:
            Tuple of (masked_content, updated_findings)
        """
        if not findings:
            return content, findings
        
        # Default masking configuration
        default_masking = {
            PIIType.EMAIL_ADDRESS: MaskingType.PARTIAL,
            PIIType.PHONE_NUMBER: MaskingType.PARTIAL,
            PIIType.PERSON_NAME: MaskingType.REPLACE,
            PIIType.SSN: MaskingType.MASK,
            PIIType.CREDIT_CARD: MaskingType.MASK,
            PIIType.DATE_OF_BIRTH: MaskingType.PARTIAL,
            PIIType.ADDRESS: MaskingType.REPLACE,
            PIIType.PASSPORT: MaskingType.MASK,
            PIIType.DRIVER_LICENSE: MaskingType.MASK,
            PIIType.BANK_ACCOUNT: MaskingType.MASK,
            PIIType.IP_ADDRESS: MaskingType.MASK,
            PIIType.MEDICAL_RECORD: MaskingType.MASK,
            PIIType.TAX_ID: MaskingType.MASK
        }
        
        # Merge with custom configuration
        if masking_config:
            default_masking.update(masking_config)
        
        # Sort findings by start offset (descending) to avoid offset issues
        sorted_findings = sorted(findings, key=lambda f: f.start_offset, reverse=True)
        
        masked_content = content
        updated_findings = []
        
        for finding in sorted_findings:
            masking_type = default_masking.get(finding.info_type, MaskingType.MASK)
            finding.masking_type = masking_type
            
            # Apply masking based on type
            masked_text = self._apply_masking(finding.original_text, masking_type, finding.info_type)
            finding.masked_text = masked_text
            
            # Replace in content
            masked_content = (
                masked_content[:finding.start_offset] +
                masked_text +
                masked_content[finding.end_offset:]
            )
            
            updated_findings.append(finding)
        
        # Reverse to maintain original order
        updated_findings.reverse()
        
        logger.info(f"Applied masking to {len(updated_findings)} PII findings")
        return masked_content, updated_findings
    
    def _apply_masking(self, text: str, masking_type: MaskingType, info_type: str) -> str:
        """Apply specific masking strategy to text."""
        if masking_type == MaskingType.REDACT:
            return "[REDACTED]"
        
        elif masking_type == MaskingType.MASK:
            return "*" * len(text)
        
        elif masking_type == MaskingType.HASH:
            import hashlib
            hash_obj = hashlib.sha256(text.encode())
            return f"[HASH:{hash_obj.hexdigest()[:8]}]"
        
        elif masking_type == MaskingType.REPLACE:
            replacements = {
                PIIType.PERSON_NAME: "[NAME]",
                PIIType.ADDRESS: "[ADDRESS]",
                PIIType.EMAIL_ADDRESS: "[EMAIL]",
                PIIType.PHONE_NUMBER: "[PHONE]",
                PIIType.DATE_OF_BIRTH: "[DOB]",
                PIIType.PASSPORT: "[PASSPORT]",
                PIIType.DRIVER_LICENSE: "[LICENSE]",
                PIIType.MEDICAL_RECORD: "[MEDICAL_ID]",
                PIIType.TAX_ID: "[TAX_ID]"
            }
            return replacements.get(info_type, "[PII]")
        
        elif masking_type == MaskingType.PARTIAL:
            if len(text) <= 4:
                return "*" * len(text)
            
            # Show first 2 and last 2 characters
            if info_type == PIIType.EMAIL_ADDRESS:
                # Special handling for emails
                if "@" in text:
                    local, domain = text.split("@", 1)
                    if len(local) > 2:
                        masked_local = local[:2] + "*" * (len(local) - 2)
                    else:
                        masked_local = "*" * len(local)
                    return f"{masked_local}@{domain}"
            
            return text[:2] + "*" * (len(text) - 4) + text[-2:]
        
        return text
    
    async def detect_and_mask_pii(
        self,
        content: str,
        content_type: str = "text/plain",
        info_types: Optional[List[str]] = None,
        masking_config: Optional[Dict[str, MaskingType]] = None,
        min_likelihood: str = "POSSIBLE"
    ) -> Tuple[str, List[PIIFinding]]:
        """
        Detect and mask PII in one operation.
        
        Args:
            content: Text content to process
            content_type: MIME type of content
            info_types: Specific PII types to detect
            masking_config: Custom masking configuration
            min_likelihood: Minimum likelihood threshold
            
        Returns:
            Tuple of (masked_content, findings)
        """
        # Detect PII
        findings = await self.detect_pii(
            content=content,
            content_type=content_type,
            info_types=info_types,
            min_likelihood=min_likelihood
        )
        
        # Apply masking
        masked_content, updated_findings = await self.mask_pii(
            content=content,
            findings=findings,
            masking_config=masking_config
        )
        
        return masked_content, updated_findings
    
    async def create_redaction_preview(
        self,
        content: str,
        findings: List[PIIFinding]
    ) -> Dict[str, Any]:
        """
        Create a preview of redaction for client-side review.
        
        Args:
            content: Original content
            findings: PII findings
            
        Returns:
            Preview data with highlighted PII locations
        """
        preview_data = {
            "original_content": content,
            "pii_locations": [],
            "summary": {
                "total_findings": len(findings),
                "by_type": {},
                "risk_level": "low"
            }
        }
        
        # Process findings for preview
        for finding in findings:
            location_data = {
                "start": finding.start_offset,
                "end": finding.end_offset,
                "type": finding.info_type,
                "text": finding.original_text,
                "likelihood": finding.likelihood,
                "confidence": finding.confidence,
                "suggested_masking": finding.masking_type
            }
            preview_data["pii_locations"].append(location_data)
            
            # Update summary
            pii_type = finding.info_type
            if pii_type not in preview_data["summary"]["by_type"]:
                preview_data["summary"]["by_type"][pii_type] = 0
            preview_data["summary"]["by_type"][pii_type] += 1
        
        # Determine risk level
        high_risk_types = [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.PASSPORT, PIIType.BANK_ACCOUNT]
        if any(finding.info_type in high_risk_types for finding in findings):
            preview_data["summary"]["risk_level"] = "high"
        elif len(findings) > 10:
            preview_data["summary"]["risk_level"] = "medium"
        
        return preview_data
    
    async def log_pii_audit(
        self,
        user_id: str,
        document_id: str,
        action: str,
        findings: List[PIIFinding],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log PII processing activity for compliance audit.
        
        Args:
            user_id: User performing the action
            document_id: Document being processed
            action: Action performed (detect, mask, redact, etc.)
            findings: PII findings involved
            metadata: Additional metadata
            
        Returns:
            Audit log ID
        """
        audit_data = {
            "user_id": user_id,
            "document_id": document_id,
            "action": action,
            "timestamp": datetime.utcnow(),
            "findings_count": len(findings),
            "pii_types": list(set(f.info_type for f in findings)),
            "high_confidence_count": len([f for f in findings if f.confidence > 0.7]),
            "metadata": metadata or {}
        }
        
        # Store in Firestore
        audit_id = await self.firestore_service.create_document(
            collection="pii_audit_logs",
            data=audit_data
        )
        
        logger.info(f"Created PII audit log {audit_id} for user {user_id}")
        return audit_id
    
    async def get_compliance_report(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for PII processing activities.
        
        Args:
            user_id: Filter by specific user (optional)
            start_date: Start date for report period
            end_date: End date for report period
            
        Returns:
            Compliance report data
        """
        # Build query filters
        filters = []
        if user_id:
            filters.append(("user_id", "==", user_id))
        if start_date:
            filters.append(("timestamp", ">=", start_date))
        if end_date:
            filters.append(("timestamp", "<=", end_date))
        
        # Query audit logs
        audit_logs = await self.firestore_service.query_documents(
            collection="pii_audit_logs",
            filters=filters,
            order_by=[("timestamp", "desc")]
        )
        
        # Generate report
        report = {
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "summary": {
                "total_operations": len(audit_logs),
                "unique_users": len(set(log["user_id"] for log in audit_logs)),
                "unique_documents": len(set(log["document_id"] for log in audit_logs)),
                "total_pii_findings": sum(log["findings_count"] for log in audit_logs)
            },
            "by_action": {},
            "by_pii_type": {},
            "high_risk_activities": []
        }
        
        # Process audit logs
        for log in audit_logs:
            action = log["action"]
            if action not in report["by_action"]:
                report["by_action"][action] = 0
            report["by_action"][action] += 1
            
            # Count PII types
            for pii_type in log["pii_types"]:
                if pii_type not in report["by_pii_type"]:
                    report["by_pii_type"][pii_type] = 0
                report["by_pii_type"][pii_type] += 1
            
            # Identify high-risk activities
            if log["high_confidence_count"] > 5:
                report["high_risk_activities"].append({
                    "timestamp": log["timestamp"].isoformat(),
                    "user_id": log["user_id"],
                    "document_id": log["document_id"],
                    "action": log["action"],
                    "high_confidence_findings": log["high_confidence_count"]
                })
        
        return report
    
    async def validate_masking_quality(
        self,
        original_content: str,
        masked_content: str,
        findings: List[PIIFinding]
    ) -> Dict[str, Any]:
        """
        Validate that masking was applied correctly and no PII leaked.
        
        Args:
            original_content: Original text content
            masked_content: Masked text content
            findings: Original PII findings
            
        Returns:
            Validation results
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "coverage": 0.0,
            "leakage_detected": False
        }
        
        try:
            # Check that all findings were masked
            masked_count = 0
            for finding in findings:
                if finding.original_text not in masked_content:
                    masked_count += 1
                else:
                    validation_result["issues"].append({
                        "type": "unmasked_pii",
                        "pii_type": finding.info_type,
                        "text": finding.original_text,
                        "location": f"{finding.start_offset}-{finding.end_offset}"
                    })
                    validation_result["leakage_detected"] = True
            
            # Calculate coverage
            validation_result["coverage"] = masked_count / len(findings) if findings else 1.0
            
            # Re-scan masked content for any remaining PII
            remaining_findings = await self.detect_pii(
                content=masked_content,
                min_likelihood="LIKELY"
            )
            
            if remaining_findings:
                validation_result["leakage_detected"] = True
                for finding in remaining_findings:
                    validation_result["issues"].append({
                        "type": "residual_pii",
                        "pii_type": finding.info_type,
                        "text": finding.original_text,
                        "confidence": finding.confidence
                    })
            
            # Overall validation
            validation_result["is_valid"] = (
                validation_result["coverage"] >= 0.95 and
                not validation_result["leakage_detected"]
            )
            
        except Exception as e:
            logger.error(f"Error validating masking quality: {e}")
            validation_result["is_valid"] = False
            validation_result["issues"].append({
                "type": "validation_error",
                "message": str(e)
            })
        
        return validation_result


# Singleton instance
pii_detection_service = PIIDetectionService()