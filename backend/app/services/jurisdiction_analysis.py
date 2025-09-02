"""
Jurisdiction-aware analysis service that integrates jurisdiction-specific legal analysis
into the document processing pipeline.

This service handles:
- Location-based legal context injection
- Jurisdiction conflict detection and resolution
- Local law compliance checking for safer alternatives
- Multi-jurisdiction analysis coordination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import UUID

from ..agents.jurisdiction_agent import JurisdictionDataAgent
from ..models.document import Clause, ProcessedDocument, LegalCitation, SaferAlternative
from ..models.base import UserRole
from ..core.config import get_settings
from ..core.exceptions import AnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


class JurisdictionAnalysisService:
    """
    Service for integrating jurisdiction-aware legal analysis into document processing.
    
    Provides high-level methods for jurisdiction analysis that can be easily
    integrated into existing workflows and API endpoints.
    """
    
    def __init__(self):
        """Initialize the jurisdiction analysis service."""
        self.jurisdiction_agent = JurisdictionDataAgent()
        
        # Cache for jurisdiction contexts to avoid repeated queries
        self._context_cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    async def enhance_document_analysis(
        self,
        processed_doc: ProcessedDocument,
        jurisdiction: str,
        user_role: UserRole
    ) -> ProcessedDocument:
        """
        Enhance an existing processed document with jurisdiction-specific analysis.
        
        Args:
            processed_doc: Already processed document
            jurisdiction: Target jurisdiction for analysis
            user_role: User's role for analysis perspective
            
        Returns:
            Enhanced ProcessedDocument with jurisdiction-specific insights
        """
        try:
            logger.info(f"Enhancing document analysis with jurisdiction context: {jurisdiction}")
            
            # Get jurisdiction context
            jurisdiction_context = await self._get_cached_jurisdiction_context(
                jurisdiction, processed_doc.structured_text[:2000]
            )
            
            # Enhance clauses with jurisdiction-specific analysis
            enhanced_clauses = await self._enhance_clauses_with_jurisdiction(
                processed_doc.clauses, jurisdiction, user_role, jurisdiction_context
            )
            
            # Update risk assessment with jurisdiction insights
            enhanced_risk_assessment = await self._enhance_risk_assessment(
                processed_doc.risk_assessment, jurisdiction_context, enhanced_clauses
            )
            
            # Add jurisdiction-specific legal citations
            jurisdiction_citations = self._extract_jurisdiction_citations(jurisdiction_context)
            
            # Update the processed document
            processed_doc.clauses = enhanced_clauses
            processed_doc.risk_assessment = enhanced_risk_assessment
            processed_doc.updated_at = datetime.utcnow()
            
            # Add jurisdiction metadata
            if not processed_doc.metadata:
                processed_doc.metadata = {}
            
            processed_doc.metadata.update({
                "jurisdiction_analysis": {
                    "jurisdiction": jurisdiction,
                    "jurisdiction_full_name": jurisdiction_context.get("jurisdiction_full_name"),
                    "legal_area": jurisdiction_context.get("legal_area"),
                    "analysis_confidence": jurisdiction_context.get("confidence", 0.7),
                    "applicable_statutes": len(jurisdiction_context.get("statutes", [])),
                    "applicable_regulations": len(jurisdiction_context.get("regulations", [])),
                    "legal_precedents": len(jurisdiction_context.get("precedents", [])),
                    "enhanced_at": datetime.utcnow().isoformat()
                }
            })
            
            logger.info(f"Document analysis enhanced with {len(enhanced_clauses)} jurisdiction-aware clauses")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Failed to enhance document with jurisdiction analysis: {str(e)}")
            raise AnalysisError(f"Jurisdiction enhancement failed: {str(e)}") from e
    
    async def analyze_multi_jurisdiction_conflicts(
        self,
        processed_doc: ProcessedDocument,
        jurisdictions: List[str],
        user_role: UserRole
    ) -> Dict[str, Any]:
        """
        Analyze conflicts between multiple jurisdictions for a document.
        
        Args:
            processed_doc: Processed document to analyze
            jurisdictions: List of jurisdictions to compare
            user_role: User's role for analysis perspective
            
        Returns:
            Dictionary containing conflict analysis and recommendations
        """
        try:
            logger.info(f"Analyzing multi-jurisdiction conflicts: {jurisdictions}")
            
            if len(jurisdictions) < 2:
                return {
                    "conflicts": [],
                    "recommendations": ["Single jurisdiction - no conflicts to analyze"],
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            
            # Get the primary jurisdiction (first in list)
            primary_jurisdiction = jurisdictions[0]
            secondary_jurisdictions = jurisdictions[1:]
            
            # Determine legal area from document
            legal_area = self._determine_document_legal_area(processed_doc)
            
            # Analyze conflicts
            conflict_analysis = await self.jurisdiction_agent.get_jurisdiction_conflicts(
                primary_jurisdiction, secondary_jurisdictions, legal_area
            )
            
            # Analyze clause-specific conflicts
            clause_conflicts = await self._analyze_clause_jurisdiction_conflicts(
                processed_doc.clauses, jurisdictions, user_role
            )
            
            # Generate comprehensive recommendations
            recommendations = self._generate_multi_jurisdiction_recommendations(
                conflict_analysis, clause_conflicts, jurisdictions
            )
            
            return {
                "primary_jurisdiction": primary_jurisdiction,
                "secondary_jurisdictions": secondary_jurisdictions,
                "legal_area": legal_area,
                "general_conflicts": conflict_analysis.get("conflicts", []),
                "clause_specific_conflicts": clause_conflicts,
                "recommendations": recommendations,
                "risk_level": self._assess_conflict_risk_level(conflict_analysis, clause_conflicts),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Multi-jurisdiction conflict analysis failed: {str(e)}")
            raise AnalysisError(f"Conflict analysis failed: {str(e)}") from e
    
    async def get_jurisdiction_safe_alternatives(
        self,
        clause: Clause,
        jurisdiction: str,
        user_role: UserRole
    ) -> List[SaferAlternative]:
        """
        Get jurisdiction-specific safer alternatives for a clause.
        
        Args:
            clause: Clause to analyze
            jurisdiction: Target jurisdiction
            user_role: User's role for analysis
            
        Returns:
            List of jurisdiction-safe alternative wordings
        """
        try:
            # Get jurisdiction context
            jurisdiction_context = await self._get_cached_jurisdiction_context(
                jurisdiction, clause.text
            )
            
            # Analyze clause compliance
            compliance_analysis = await self.jurisdiction_agent.analyze_clause_jurisdiction_compliance(
                clause, jurisdiction, user_role
            )
            
            # Extract safer alternatives from compliance analysis
            safer_alternatives = []
            for alt_data in compliance_analysis.get("safer_alternatives", []):
                alternative = SaferAlternative(
                    suggested_text=alt_data.get("text", ""),
                    rationale=alt_data.get("rationale", ""),
                    legal_basis=f"Compliance with {jurisdiction} law",
                    confidence=alt_data.get("confidence", 0.7),
                    impact_reduction=0.3  # Default impact reduction
                )
                safer_alternatives.append(alternative)
            
            return safer_alternatives
            
        except Exception as e:
            logger.error(f"Failed to get jurisdiction-safe alternatives: {str(e)}")
            return []
    
    async def validate_jurisdiction_compliance(
        self,
        processed_doc: ProcessedDocument,
        jurisdiction: str,
        user_role: UserRole
    ) -> Dict[str, Any]:
        """
        Validate document compliance with jurisdiction-specific laws.
        
        Args:
            processed_doc: Document to validate
            jurisdiction: Target jurisdiction
            user_role: User's role for validation
            
        Returns:
            Compliance validation results
        """
        try:
            logger.info(f"Validating jurisdiction compliance: {jurisdiction}")
            
            # Get jurisdiction context
            jurisdiction_context = await self._get_cached_jurisdiction_context(
                jurisdiction, processed_doc.structured_text[:2000]
            )
            
            # Validate each clause
            compliance_results = []
            high_risk_clauses = []
            compliance_issues = []
            
            for clause in processed_doc.clauses:
                try:
                    compliance = await self.jurisdiction_agent.analyze_clause_jurisdiction_compliance(
                        clause, jurisdiction, user_role
                    )
                    
                    compliance_results.append({
                        "clause_text": clause.text[:200] + "..." if len(clause.text) > 200 else clause.text,
                        "compliance_score": compliance.get("compliance_score", 0.5),
                        "compliance_risk": compliance.get("compliance_risk", 0.5),
                        "issues": compliance.get("compliance_issues", [])
                    })
                    
                    # Track high-risk clauses
                    if compliance.get("compliance_risk", 0) > 0.7:
                        high_risk_clauses.append({
                            "clause": clause.text[:200] + "..." if len(clause.text) > 200 else clause.text,
                            "risk": compliance.get("compliance_risk"),
                            "issues": compliance.get("compliance_issues", [])
                        })
                    
                    # Collect compliance issues
                    compliance_issues.extend(compliance.get("compliance_issues", []))
                    
                except Exception as e:
                    logger.warning(f"Compliance validation failed for clause: {str(e)}")
                    continue
            
            # Calculate overall compliance score
            if compliance_results:
                overall_compliance = sum(r["compliance_score"] for r in compliance_results) / len(compliance_results)
                overall_risk = sum(r["compliance_risk"] for r in compliance_results) / len(compliance_results)
            else:
                overall_compliance = 0.5
                overall_risk = 0.5
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(
                overall_compliance, high_risk_clauses, compliance_issues, jurisdiction
            )
            
            return {
                "jurisdiction": jurisdiction,
                "jurisdiction_full_name": jurisdiction_context.get("jurisdiction_full_name"),
                "overall_compliance_score": overall_compliance,
                "overall_compliance_risk": overall_risk,
                "clauses_analyzed": len(compliance_results),
                "high_risk_clauses": len(high_risk_clauses),
                "compliance_issues": len(set(issue.get("type", "") for issue in compliance_issues)),
                "detailed_results": compliance_results,
                "high_risk_details": high_risk_clauses,
                "recommendations": recommendations,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Jurisdiction compliance validation failed: {str(e)}")
            raise AnalysisError(f"Compliance validation failed: {str(e)}") from e
    
    async def _get_cached_jurisdiction_context(
        self,
        jurisdiction: str,
        sample_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get jurisdiction context with caching."""
        cache_key = f"{jurisdiction}:{hash(sample_text) if sample_text else 'general'}"
        
        # Check cache
        if cache_key in self._context_cache:
            cached_data = self._context_cache[cache_key]
            if (datetime.utcnow() - cached_data["timestamp"]).seconds < self._cache_ttl:
                return cached_data["context"]
        
        # Get fresh context
        legal_area = None
        if sample_text:
            legal_area = self.jurisdiction_agent._determine_legal_area(sample_text)
        
        context = await self.jurisdiction_agent.get_jurisdiction_context(
            jurisdiction, legal_area, sample_text
        )
        
        # Cache the result
        self._context_cache[cache_key] = {
            "context": context,
            "timestamp": datetime.utcnow()
        }
        
        return context
    
    async def _enhance_clauses_with_jurisdiction(
        self,
        clauses: List[Clause],
        jurisdiction: str,
        user_role: UserRole,
        jurisdiction_context: Dict[str, Any]
    ) -> List[Clause]:
        """Enhance clauses with jurisdiction-specific analysis."""
        enhanced_clauses = []
        
        for clause in clauses:
            try:
                # Get jurisdiction-specific compliance analysis
                compliance = await self.jurisdiction_agent.analyze_clause_jurisdiction_compliance(
                    clause, jurisdiction, user_role
                )
                
                # Create enhanced clause with jurisdiction insights
                enhanced_clause = clause.copy()
                
                # Add jurisdiction-specific legal citations
                jurisdiction_citations = []
                for law in compliance.get("applicable_laws", [])[:3]:
                    citation = LegalCitation(
                        statute=law.get("title", ""),
                        description=law.get("description", ""),
                        url=law.get("url"),
                        jurisdiction=jurisdiction,
                        relevance=law.get("relevance_score", 0.5)
                    )
                    jurisdiction_citations.append(citation)
                
                # Merge with existing citations
                enhanced_clause.legal_citations.extend(jurisdiction_citations)
                
                # Add jurisdiction-specific safer alternatives
                for alt_data in compliance.get("safer_alternatives", []):
                    alternative = SaferAlternative(
                        suggested_text=alt_data.get("text", ""),
                        rationale=alt_data.get("rationale", ""),
                        legal_basis=f"Compliance with {jurisdiction} law",
                        confidence=alt_data.get("confidence", 0.7),
                        impact_reduction=0.3
                    )
                    enhanced_clause.safer_alternatives.append(alternative)
                
                # Update risk score if jurisdiction analysis indicates higher risk
                jurisdiction_risk = compliance.get("compliance_risk", 0.5)
                if jurisdiction_risk > enhanced_clause.risk_score:
                    enhanced_clause.risk_score = min(1.0, enhanced_clause.risk_score + (jurisdiction_risk * 0.3))
                
                enhanced_clauses.append(enhanced_clause)
                
            except Exception as e:
                logger.warning(f"Failed to enhance clause with jurisdiction analysis: {str(e)}")
                enhanced_clauses.append(clause)  # Keep original clause
        
        return enhanced_clauses
    
    async def _enhance_risk_assessment(
        self,
        risk_assessment: Optional[Any],
        jurisdiction_context: Dict[str, Any],
        enhanced_clauses: List[Clause]
    ) -> Optional[Any]:
        """Enhance risk assessment with jurisdiction insights."""
        if not risk_assessment:
            return None
        
        # Add jurisdiction-specific recommendations
        jurisdiction_recommendations = [
            f"Document analyzed under {jurisdiction_context.get('jurisdiction_full_name', 'specified')} jurisdiction",
            f"Consider {len(jurisdiction_context.get('statutes', []))} applicable statutes",
            f"Review {len(jurisdiction_context.get('regulations', []))} relevant regulations"
        ]
        
        # Add jurisdiction-specific red flags
        jurisdiction_red_flags = []
        high_risk_clauses = [c for c in enhanced_clauses if c.risk_score > 0.7]
        if high_risk_clauses:
            jurisdiction_red_flags.append(
                f"{len(high_risk_clauses)} clauses may not comply with local jurisdiction requirements"
            )
        
        # Update risk assessment
        enhanced_risk = risk_assessment.copy()
        enhanced_risk.recommendations.extend(jurisdiction_recommendations)
        enhanced_risk.red_flags.extend(jurisdiction_red_flags)
        
        return enhanced_risk
    
    def _extract_jurisdiction_citations(self, jurisdiction_context: Dict[str, Any]) -> List[LegalCitation]:
        """Extract legal citations from jurisdiction context."""
        citations = []
        
        # Add statute citations
        for statute in jurisdiction_context.get("statutes", [])[:5]:
            citation = LegalCitation(
                statute=statute.get("title", ""),
                description=statute.get("description", ""),
                url=statute.get("url"),
                jurisdiction=jurisdiction_context.get("jurisdiction", "US"),
                relevance=statute.get("relevance_score", 0.5)
            )
            citations.append(citation)
        
        return citations
    
    def _determine_document_legal_area(self, processed_doc: ProcessedDocument) -> Optional[str]:
        """Determine the legal area of a document."""
        # Use the jurisdiction agent's legal area determination
        sample_text = processed_doc.structured_text[:1000] if processed_doc.structured_text else ""
        return self.jurisdiction_agent._determine_legal_area(sample_text)
    
    async def _analyze_clause_jurisdiction_conflicts(
        self,
        clauses: List[Clause],
        jurisdictions: List[str],
        user_role: UserRole
    ) -> List[Dict[str, Any]]:
        """Analyze jurisdiction conflicts for specific clauses."""
        clause_conflicts = []
        
        # Analyze a sample of clauses to avoid performance issues
        sample_clauses = clauses[:5] if len(clauses) > 5 else clauses
        
        for clause in sample_clauses:
            try:
                # Get compliance analysis for each jurisdiction
                jurisdiction_analyses = {}
                for jurisdiction in jurisdictions:
                    compliance = await self.jurisdiction_agent.analyze_clause_jurisdiction_compliance(
                        clause, jurisdiction, user_role
                    )
                    jurisdiction_analyses[jurisdiction] = compliance
                
                # Identify conflicts
                conflicts = self._identify_clause_conflicts(clause, jurisdiction_analyses)
                
                if conflicts:
                    clause_conflicts.append({
                        "clause_text": clause.text[:200] + "..." if len(clause.text) > 200 else clause.text,
                        "conflicts": conflicts,
                        "jurisdictions": jurisdictions
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to analyze clause jurisdiction conflicts: {str(e)}")
                continue
        
        return clause_conflicts
    
    def _identify_clause_conflicts(
        self,
        clause: Clause,
        jurisdiction_analyses: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify conflicts between jurisdiction analyses for a clause."""
        conflicts = []
        
        # Compare compliance scores
        compliance_scores = {
            jurisdiction: analysis.get("compliance_score", 0.5)
            for jurisdiction, analysis in jurisdiction_analyses.items()
        }
        
        # Check for significant differences in compliance scores
        max_score = max(compliance_scores.values())
        min_score = min(compliance_scores.values())
        
        if max_score - min_score > 0.3:  # Significant difference threshold
            conflicts.append({
                "type": "compliance_variance",
                "description": "Significant compliance differences between jurisdictions",
                "severity": "medium",
                "details": compliance_scores
            })
        
        # Check for conflicting recommendations
        all_recommendations = []
        for analysis in jurisdiction_analyses.values():
            all_recommendations.extend(analysis.get("recommendations", []))
        
        if len(set(all_recommendations)) > len(all_recommendations) * 0.7:  # High diversity in recommendations
            conflicts.append({
                "type": "conflicting_recommendations",
                "description": "Jurisdictions provide conflicting recommendations",
                "severity": "high",
                "details": {
                    jurisdiction: analysis.get("recommendations", [])
                    for jurisdiction, analysis in jurisdiction_analyses.items()
                }
            })
        
        return conflicts
    
    def _generate_multi_jurisdiction_recommendations(
        self,
        conflict_analysis: Dict[str, Any],
        clause_conflicts: List[Dict[str, Any]],
        jurisdictions: List[str]
    ) -> List[str]:
        """Generate recommendations for multi-jurisdiction scenarios."""
        recommendations = []
        
        # General recommendations
        recommendations.append(f"Document involves {len(jurisdictions)} jurisdictions: {', '.join(jurisdictions)}")
        
        # Conflict-based recommendations
        if conflict_analysis.get("conflicts"):
            recommendations.append("Consult legal counsel familiar with all applicable jurisdictions")
            recommendations.append("Consider jurisdiction-specific contract versions")
        
        if clause_conflicts:
            recommendations.append(f"{len(clause_conflicts)} clauses show jurisdiction-specific conflicts")
            recommendations.append("Review conflicting clauses for jurisdiction-neutral alternatives")
        
        # Specific jurisdiction recommendations
        if "CA" in jurisdictions:
            recommendations.append("California law may override certain contract provisions")
        
        if "NY" in jurisdictions:
            recommendations.append("New York choice of law provisions may be required")
        
        return recommendations
    
    def _assess_conflict_risk_level(
        self,
        conflict_analysis: Dict[str, Any],
        clause_conflicts: List[Dict[str, Any]]
    ) -> str:
        """Assess the overall risk level of jurisdiction conflicts."""
        high_severity_conflicts = len([
            c for c in conflict_analysis.get("conflicts", [])
            if c.get("severity") == "high"
        ])
        
        clause_conflict_count = len(clause_conflicts)
        
        if high_severity_conflicts > 0 or clause_conflict_count > 3:
            return "high"
        elif clause_conflict_count > 1:
            return "medium"
        else:
            return "low"
    
    def _generate_compliance_recommendations(
        self,
        overall_compliance: float,
        high_risk_clauses: List[Dict[str, Any]],
        compliance_issues: List[Dict[str, Any]],
        jurisdiction: str
    ) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if overall_compliance < 0.6:
            recommendations.append(f"Document shows low compliance with {jurisdiction} law")
            recommendations.append("Comprehensive legal review recommended before execution")
        
        if high_risk_clauses:
            recommendations.append(f"{len(high_risk_clauses)} clauses require immediate attention")
            recommendations.append("Consider safer alternative wordings for high-risk clauses")
        
        # Issue-specific recommendations
        issue_types = set(issue.get("type", "") for issue in compliance_issues)
        for issue_type in issue_types:
            if "unilateral" in issue_type:
                recommendations.append("Review unilateral modification clauses for enforceability")
            elif "arbitration" in issue_type:
                recommendations.append("Ensure arbitration clauses comply with local consumer protection laws")
            elif "liquidated_damages" in issue_type:
                recommendations.append("Verify liquidated damages are reasonable and not punitive")
        
        return recommendations