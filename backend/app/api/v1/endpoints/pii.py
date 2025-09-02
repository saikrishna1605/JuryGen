"""
PII Detection and Masking API endpoints.

Provides endpoints for:
- PII detection in content
- PII masking and redaction
- Redaction preview generation
- Compliance reporting
- Masking validation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....core.security import get_current_user
from ....services.pii_detection import pii_detection_service, PIIFinding, MaskingType
from ....core.exceptions import PIIDetectionError

router = APIRouter()


class PIIDetectionRequest(BaseModel):
    """Request model for PII detection."""
    content: str = Field(..., description="Content to analyze for PII")
    content_type: str = Field(default="text/plain", description="MIME type of content")
    info_types: Optional[List[str]] = Field(None, description="Specific PII types to detect")
    min_likelihood: str = Field(default="POSSIBLE", description="Minimum likelihood threshold")
    create_preview: bool = Field(default=False, description="Create redaction preview")


class PIIMaskingRequest(BaseModel):
    """Request model for PII masking."""
    content: str = Field(..., description="Original content")
    findings: List[Dict[str, Any]] = Field(..., description="PII findings to mask")
    masking_config: Optional[Dict[str, str]] = Field(None, description="Custom masking configuration")


class PIIDetectAndMaskRequest(BaseModel):
    """Request model for combined detect and mask operation."""
    content: str = Field(..., description="Content to process")
    content_type: str = Field(default="text/plain", description="MIME type of content")
    info_types: Optional[List[str]] = Field(None, description="Specific PII types to detect")
    masking_config: Optional[Dict[str, str]] = Field(None, description="Custom masking configuration")
    min_likelihood: str = Field(default="POSSIBLE", description="Minimum likelihood threshold")


class PIIValidationRequest(BaseModel):
    """Request model for masking validation."""
    original_content: str = Field(..., description="Original content")
    masked_content: str = Field(..., description="Masked content")
    findings: List[Dict[str, Any]] = Field(..., description="Original PII findings")


class PIIPreviewRequest(BaseModel):
    """Request model for redaction preview."""
    content: str = Field(..., description="Content to preview")
    findings: List[Dict[str, Any]] = Field(..., description="PII findings")


@router.post("/detect")
async def detect_pii(
    request: PIIDetectionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Detect PII in the provided content.
    
    Returns detected PII findings and optionally a redaction preview.
    """
    try:
        # Detect PII
        findings = await pii_detection_service.detect_pii(
            content=request.content,
            content_type=request.content_type,
            info_types=request.info_types,
            min_likelihood=request.min_likelihood
        )
        
        # Log audit trail
        await pii_detection_service.log_pii_audit(
            user_id=current_user["uid"],
            document_id="direct_input",  # For direct content input
            action="detect",
            findings=findings,
            metadata={
                "content_type": request.content_type,
                "min_likelihood": request.min_likelihood,
                "info_types": request.info_types
            }
        )
        
        # Create preview if requested
        if request.create_preview:
            preview = await pii_detection_service.create_redaction_preview(
                content=request.content,
                findings=findings
            )
            return preview
        
        # Return findings only
        return {
            "findings": [finding.to_dict() for finding in findings],
            "summary": {
                "total_findings": len(findings),
                "by_type": {},
                "risk_level": "low"
            }
        }
        
    except PIIDetectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII detection failed: {str(e)}")


@router.post("/mask")
async def mask_pii(
    request: PIIMaskingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Apply masking to detected PII in content.
    
    Returns masked content and validation results.
    """
    try:
        # Convert findings from dict to PIIFinding objects
        findings = []
        for finding_dict in request.findings:
            finding = PIIFinding(
                info_type=finding_dict["type"],
                likelihood=finding_dict["likelihood"],
                start_offset=finding_dict["start"],
                end_offset=finding_dict["end"],
                original_text=finding_dict["text"],
                confidence=finding_dict.get("confidence", 0.5)
            )
            findings.append(finding)
        
        # Apply masking
        masked_content, updated_findings = await pii_detection_service.mask_pii(
            content=request.content,
            findings=findings,
            masking_config=request.masking_config
        )
        
        # Validate masking quality
        validation = await pii_detection_service.validate_masking_quality(
            original_content=request.content,
            masked_content=masked_content,
            findings=updated_findings
        )
        
        # Log audit trail
        await pii_detection_service.log_pii_audit(
            user_id=current_user["uid"],
            document_id="direct_input",
            action="mask",
            findings=updated_findings,
            metadata={
                "masking_config": request.masking_config,
                "validation_passed": validation["is_valid"]
            }
        )
        
        return {
            "masked_content": masked_content,
            "findings": [finding.to_dict() for finding in updated_findings],
            "validation": validation
        }
        
    except PIIDetectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII masking failed: {str(e)}")


@router.post("/detect-and-mask")
async def detect_and_mask_pii(
    request: PIIDetectAndMaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Detect and mask PII in one operation.
    
    Combines detection and masking for convenience.
    """
    try:
        # Detect and mask PII
        masked_content, findings = await pii_detection_service.detect_and_mask_pii(
            content=request.content,
            content_type=request.content_type,
            info_types=request.info_types,
            masking_config=request.masking_config,
            min_likelihood=request.min_likelihood
        )
        
        # Validate masking quality
        validation = await pii_detection_service.validate_masking_quality(
            original_content=request.content,
            masked_content=masked_content,
            findings=findings
        )
        
        # Log audit trail
        await pii_detection_service.log_pii_audit(
            user_id=current_user["uid"],
            document_id="direct_input",
            action="detect_and_mask",
            findings=findings,
            metadata={
                "content_type": request.content_type,
                "masking_config": request.masking_config,
                "min_likelihood": request.min_likelihood,
                "validation_passed": validation["is_valid"]
            }
        )
        
        return {
            "masked_content": masked_content,
            "findings": [finding.to_dict() for finding in findings],
            "validation": validation
        }
        
    except PIIDetectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII processing failed: {str(e)}")


@router.post("/preview")
async def create_redaction_preview(
    request: PIIPreviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a redaction preview for client-side review.
    
    Returns preview data with highlighted PII locations.
    """
    try:
        # Convert findings from dict to PIIFinding objects
        findings = []
        for finding_dict in request.findings:
            finding = PIIFinding(
                info_type=finding_dict["type"],
                likelihood=finding_dict["likelihood"],
                start_offset=finding_dict["start"],
                end_offset=finding_dict["end"],
                original_text=finding_dict["text"],
                confidence=finding_dict.get("confidence", 0.5)
            )
            findings.append(finding)
        
        # Create preview
        preview = await pii_detection_service.create_redaction_preview(
            content=request.content,
            findings=findings
        )
        
        return preview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.post("/validate")
async def validate_masking(
    request: PIIValidationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate that masking was applied correctly.
    
    Checks for PII leakage and masking coverage.
    """
    try:
        # Convert findings from dict to PIIFinding objects
        findings = []
        for finding_dict in request.findings:
            finding = PIIFinding(
                info_type=finding_dict["type"],
                likelihood=finding_dict["likelihood"],
                start_offset=finding_dict["start"],
                end_offset=finding_dict["end"],
                original_text=finding_dict["text"],
                confidence=finding_dict.get("confidence", 0.5)
            )
            findings.append(finding)
        
        # Validate masking
        validation = await pii_detection_service.validate_masking_quality(
            original_content=request.original_content,
            masked_content=request.masked_content,
            findings=findings
        )
        
        # Log audit trail
        await pii_detection_service.log_pii_audit(
            user_id=current_user["uid"],
            document_id="direct_input",
            action="validate",
            findings=findings,
            metadata={
                "validation_passed": validation["is_valid"],
                "coverage": validation["coverage"],
                "leakage_detected": validation["leakage_detected"]
            }
        )
        
        return validation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/compliance-report")
async def get_compliance_report(
    user_id: Optional[str] = Query(None, description="Filter by specific user"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate compliance report for PII processing activities.
    
    Returns summary of PII operations and audit data.
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Generate report
        report = await pii_detection_service.get_compliance_report(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/info-types")
async def get_supported_info_types():
    """
    Get list of supported PII types for detection.
    
    Returns information about available PII detection categories.
    """
    info_types = [
        {
            "type": "EMAIL_ADDRESS",
            "name": "Email Address",
            "description": "Email addresses",
            "risk_level": "low"
        },
        {
            "type": "PHONE_NUMBER",
            "name": "Phone Number", 
            "description": "Phone numbers",
            "risk_level": "low"
        },
        {
            "type": "PERSON_NAME",
            "name": "Person Name",
            "description": "Names of individuals",
            "risk_level": "medium"
        },
        {
            "type": "US_SOCIAL_SECURITY_NUMBER",
            "name": "Social Security Number",
            "description": "US Social Security Numbers",
            "risk_level": "high"
        },
        {
            "type": "CREDIT_CARD_NUMBER",
            "name": "Credit Card Number",
            "description": "Credit card numbers",
            "risk_level": "high"
        },
        {
            "type": "DATE_OF_BIRTH",
            "name": "Date of Birth",
            "description": "Birth dates",
            "risk_level": "medium"
        },
        {
            "type": "STREET_ADDRESS",
            "name": "Street Address",
            "description": "Physical addresses",
            "risk_level": "medium"
        },
        {
            "type": "PASSPORT",
            "name": "Passport Number",
            "description": "Passport numbers",
            "risk_level": "high"
        },
        {
            "type": "US_DRIVERS_LICENSE_NUMBER",
            "name": "Driver License",
            "description": "US driver license numbers",
            "risk_level": "high"
        },
        {
            "type": "US_BANK_ROUTING_MICR",
            "name": "Bank Account",
            "description": "Bank routing and account numbers",
            "risk_level": "high"
        },
        {
            "type": "IP_ADDRESS",
            "name": "IP Address",
            "description": "IP addresses",
            "risk_level": "low"
        },
        {
            "type": "MEDICAL_RECORD_NUMBER",
            "name": "Medical Record",
            "description": "Medical record numbers",
            "risk_level": "high"
        },
        {
            "type": "US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER",
            "name": "Tax ID",
            "description": "US Individual Taxpayer ID",
            "risk_level": "high"
        }
    ]
    
    return {
        "info_types": info_types,
        "masking_types": [
            {
                "type": "redact",
                "name": "Redact",
                "description": "Completely remove the PII",
                "example": "[REDACTED]"
            },
            {
                "type": "mask",
                "name": "Mask",
                "description": "Replace with asterisks",
                "example": "***********"
            },
            {
                "type": "hash",
                "name": "Hash",
                "description": "Replace with cryptographic hash",
                "example": "[HASH:a1b2c3d4]"
            },
            {
                "type": "replace",
                "name": "Replace",
                "description": "Replace with generic label",
                "example": "[EMAIL], [NAME], [PHONE]"
            },
            {
                "type": "partial",
                "name": "Partial",
                "description": "Show first and last characters",
                "example": "jo***@ex*****.com"
            }
        ]
    }