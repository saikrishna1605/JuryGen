"""
Jurisdiction analysis API endpoints.

Provides endpoints for jurisdiction-aware legal analysis including:
- Jurisdiction context retrieval
- Compliance analysis
- Multi-jurisdiction conflict detection
- Jurisdiction-safe alternatives
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ....core.security import get_current_user
from ....services.jurisdiction_analysis import JurisdictionAnalysisService
from ....services.firestore import FirestoreService
from ....models.document import Clause, ProcessedDocument
from ....models.base import UserRole
from ....core.exceptions import AnalysisError

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class JurisdictionContextRequest(BaseModel):
    """Request model for jurisdiction context."""
    jurisdiction: str = Field(..., description="Jurisdiction code (e.g., 'CA', 'NY', 'US')")
    legal_area: Optional[str] = Field(None, description="Legal area (e.g., 'contract', 'employment')")
    sample_text: Optional[str] = Field(None, description="Sample text for context")


class JurisdictionContextResponse(BaseModel):
    """Response model for jurisdiction context."""
    jurisdiction: str
    jurisdiction_full_name: str
    legal_area: Optional[str]
    statutes: List[Dict[str, Any]]
    regulations: List[Dict[str, Any]]
    precedents: List[Dict[str, Any]]
    summary: str
    confidence: float
    last_updated: str


class ComplianceAnalysisRequest(BaseModel):
    """Request model for compliance analysis."""
    document_id: UUID = Field(..., description="Document ID to analyze")
    jurisdiction: str = Field(..., description="Target jurisdiction")
    user_role: UserRole = Field(..., description="User's role for analysis")


class ComplianceAnalysisResponse(BaseModel):
    """Response model for compliance analysis."""
    jurisdiction: str
    jurisdiction_full_name: str
    overall_compliance_score: float
    overall_compliance_risk: float
    clauses_analyzed: int
    high_risk_clauses: int
    compliance_issues: int
    recommendations: List[str]
    validation_timestamp: str


class MultiJurisdictionRequest(BaseModel):
    """Request model for multi-jurisdiction analysis."""
    document_id: UUID = Field(..., description="Document ID to analyze")
    jurisdictions: List[str] = Field(..., min_items=2, description="List of jurisdictions to compare")
    user_role: UserRole = Field(..., description="User's role for analysis")


class MultiJurisdictionResponse(BaseModel):
    """Response model for multi-jurisdiction analysis."""
    primary_jurisdiction: str
    secondary_jurisdictions: List[str]
    legal_area: Optional[str]
    general_conflicts: List[Dict[str, Any]]
    clause_specific_conflicts: List[Dict[str, Any]]
    recommendations: List[str]
    risk_level: str
    analysis_timestamp: str


class SaferAlternativesRequest(BaseModel):
    """Request model for safer alternatives."""
    clause_text: str = Field(..., description="Clause text to analyze")
    jurisdiction: str = Field(..., description="Target jurisdiction")
    user_role: UserRole = Field(..., description="User's role for analysis")


class SaferAlternativesResponse(BaseModel):
    """Response model for safer alternatives."""
    original_clause: str
    jurisdiction: str
    safer_alternatives: List[Dict[str, Any]]
    analysis_timestamp: str


# Initialize services
jurisdiction_service = JurisdictionAnalysisService()
firestore_service = FirestoreService()


@router.get("/context", response_model=JurisdictionContextResponse)
async def get_jurisdiction_context(
    jurisdiction: str,
    legal_area: Optional[str] = None,
    sample_text: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get jurisdiction-specific legal context.
    
    Retrieves relevant statutes, regulations, and precedents for the specified
    jurisdiction and legal area.
    """
    try:
        logger.info(f"Getting jurisdiction context for {jurisdiction}")
        
        # Get jurisdiction context
        context = await jurisdiction_service.jurisdiction_agent.get_jurisdiction_context(
            jurisdiction, legal_area, sample_text
        )
        
        return JurisdictionContextResponse(
            jurisdiction=context["jurisdiction"],
            jurisdiction_full_name=context["jurisdiction_full_name"],
            legal_area=context.get("legal_area"),
            statutes=context.get("statutes", []),
            regulations=context.get("regulations", []),
            precedents=context.get("precedents", []),
            summary=context.get("summary", ""),
            confidence=context.get("confidence", 0.7),
            last_updated=context["last_updated"]
        )
        
    except AnalysisError as e:
        logger.error(f"Jurisdiction context retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jurisdiction context: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in jurisdiction context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/compliance", response_model=ComplianceAnalysisResponse)
async def analyze_compliance(
    request: ComplianceAnalysisRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze document compliance with jurisdiction-specific laws.
    
    Validates each clause in the document against the specified jurisdiction's
    legal requirements and provides compliance scores and recommendations.
    """
    try:
        logger.info(f"Analyzing compliance for document {request.document_id} in {request.jurisdiction}")
        
        # Get the processed document
        processed_doc = await firestore_service.get_processed_document(
            request.document_id, current_user["uid"]
        )
        
        if not processed_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Validate compliance
        compliance_result = await jurisdiction_service.validate_jurisdiction_compliance(
            processed_doc, request.jurisdiction, request.user_role
        )
        
        return ComplianceAnalysisResponse(
            jurisdiction=compliance_result["jurisdiction"],
            jurisdiction_full_name=compliance_result["jurisdiction_full_name"],
            overall_compliance_score=compliance_result["overall_compliance_score"],
            overall_compliance_risk=compliance_result["overall_compliance_risk"],
            clauses_analyzed=compliance_result["clauses_analyzed"],
            high_risk_clauses=compliance_result["high_risk_clauses"],
            compliance_issues=compliance_result["compliance_issues"],
            recommendations=compliance_result["recommendations"],
            validation_timestamp=compliance_result["validation_timestamp"]
        )
        
    except HTTPException:
        raise
    except AnalysisError as e:
        logger.error(f"Compliance analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance analysis failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in compliance analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/multi-jurisdiction", response_model=MultiJurisdictionResponse)
async def analyze_multi_jurisdiction(
    request: MultiJurisdictionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze conflicts between multiple jurisdictions for a document.
    
    Compares legal requirements across multiple jurisdictions and identifies
    potential conflicts and compliance issues.
    """
    try:
        logger.info(f"Analyzing multi-jurisdiction conflicts for document {request.document_id}")
        
        # Get the processed document
        processed_doc = await firestore_service.get_processed_document(
            request.document_id, current_user["uid"]
        )
        
        if not processed_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Analyze conflicts
        conflict_result = await jurisdiction_service.analyze_multi_jurisdiction_conflicts(
            processed_doc, request.jurisdictions, request.user_role
        )
        
        return MultiJurisdictionResponse(
            primary_jurisdiction=conflict_result["primary_jurisdiction"],
            secondary_jurisdictions=conflict_result["secondary_jurisdictions"],
            legal_area=conflict_result.get("legal_area"),
            general_conflicts=conflict_result["general_conflicts"],
            clause_specific_conflicts=conflict_result["clause_specific_conflicts"],
            recommendations=conflict_result["recommendations"],
            risk_level=conflict_result["risk_level"],
            analysis_timestamp=conflict_result["analysis_timestamp"]
        )
        
    except HTTPException:
        raise
    except AnalysisError as e:
        logger.error(f"Multi-jurisdiction analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-jurisdiction analysis failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in multi-jurisdiction analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/safer-alternatives", response_model=SaferAlternativesResponse)
async def get_safer_alternatives(
    request: SaferAlternativesRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get jurisdiction-specific safer alternatives for a clause.
    
    Analyzes a clause and provides safer alternative wordings that comply
    with the specified jurisdiction's legal requirements.
    """
    try:
        logger.info(f"Getting safer alternatives for clause in {request.jurisdiction}")
        
        # Create a temporary clause object for analysis
        temp_clause = Clause(
            text=request.clause_text,
            classification="caution",  # Default classification
            risk_score=0.5,
            impact_score=50,
            likelihood_score=50,
            role_analysis={},
            safer_alternatives=[],
            legal_citations=[],
            keywords=[],
            category=None
        )
        
        # Get safer alternatives
        safer_alternatives = await jurisdiction_service.get_jurisdiction_safe_alternatives(
            temp_clause, request.jurisdiction, request.user_role
        )
        
        # Convert to response format
        alternatives_data = []
        for alt in safer_alternatives:
            alternatives_data.append({
                "suggested_text": alt.suggested_text,
                "rationale": alt.rationale,
                "legal_basis": alt.legal_basis,
                "confidence": alt.confidence,
                "impact_reduction": alt.impact_reduction
            })
        
        return SaferAlternativesResponse(
            original_clause=request.clause_text,
            jurisdiction=request.jurisdiction,
            safer_alternatives=alternatives_data,
            analysis_timestamp=datetime.utcnow().isoformat()
        )
        
    except AnalysisError as e:
        logger.error(f"Safer alternatives analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safer alternatives analysis failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in safer alternatives: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/enhance-document")
async def enhance_document_with_jurisdiction(
    document_id: UUID,
    jurisdiction: str,
    user_role: UserRole,
    current_user: Dict = Depends(get_current_user)
):
    """
    Enhance an existing processed document with jurisdiction-specific analysis.
    
    Adds jurisdiction-aware insights to an already processed document,
    including compliance analysis and jurisdiction-specific recommendations.
    """
    try:
        logger.info(f"Enhancing document {document_id} with jurisdiction analysis: {jurisdiction}")
        
        # Get the processed document
        processed_doc = await firestore_service.get_processed_document(
            document_id, current_user["uid"]
        )
        
        if not processed_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Enhance with jurisdiction analysis
        enhanced_doc = await jurisdiction_service.enhance_document_analysis(
            processed_doc, jurisdiction, user_role
        )
        
        # Save the enhanced document
        await firestore_service.save_processed_document(enhanced_doc)
        
        return {
            "message": "Document enhanced with jurisdiction analysis",
            "document_id": str(document_id),
            "jurisdiction": jurisdiction,
            "enhanced_clauses": len(enhanced_doc.clauses),
            "enhancement_timestamp": enhanced_doc.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except AnalysisError as e:
        logger.error(f"Document enhancement failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document enhancement failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in document enhancement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/supported-jurisdictions")
async def get_supported_jurisdictions(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get list of supported jurisdictions.
    
    Returns a list of all jurisdictions supported by the system
    with their full names and codes.
    """
    try:
        # Get jurisdiction mappings from the agent
        jurisdiction_mappings = jurisdiction_service.jurisdiction_agent.jurisdiction_mappings
        
        supported_jurisdictions = []
        for code, alternatives in jurisdiction_mappings.items():
            supported_jurisdictions.append({
                "code": code,
                "full_name": alternatives[0] if alternatives else code,
                "alternatives": alternatives[1:] if len(alternatives) > 1 else []
            })
        
        return {
            "supported_jurisdictions": supported_jurisdictions,
            "total_count": len(supported_jurisdictions)
        }
        
    except Exception as e:
        logger.error(f"Error getting supported jurisdictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported jurisdictions"
        )


# Add missing import
from datetime import datetime