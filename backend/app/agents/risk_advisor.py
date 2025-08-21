"""
Risk Advisor Agent for legal risk assessment and safer alternative generation.

This agent handles:
- Risk assessment logic with impact and likelihood scoring
- Safer alternative wording generation
- Legal citation and statute reference integration
- Jurisdiction-aware risk analysis
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import vertexai
from vertexai.generative_models import GenerativeModel
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..models.document import (
    Clause, RiskAssessment, SaferAlternative, LegalCitation
)
from ..models.base import UserRole, RiskLevel
from ..core.exceptions import AnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


class RiskAdvisorAgent:
    """
    Specialized agent for legal risk assessment and advisory services.
    
    Uses Gemini 1.5 Pro for sophisticated risk analysis and generates
    safer alternatives with legal grounding.
    """
    
    def __init__(self):
        """Initialize the Risk Advisor Agent."""
        # Initialize Vertex AI
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        
        # Initialize Gemini Pro model for complex risk analysis
        self.pro_model = GenerativeModel(settings.GEMINI_MODEL_PRO)
        
        # Risk categories and their typical impact levels
        self.risk_categories = {
            "financial": {
                "description": "Financial obligations, penalties, and monetary risks",
                "typical_impact": "high",
                "keywords": ["payment", "fee", "penalty", "damages", "cost", "price"]
            },
            "liability": {
                "description": "Legal liability and responsibility risks",
                "typical_impact": "high", 
                "keywords": ["liable", "responsible", "indemnify", "damages", "fault"]
            },
            "termination": {
                "description": "Contract termination and cancellation risks",
                "typical_impact": "medium",
                "keywords": ["terminate", "cancel", "end", "breach", "default"]
            },
            "confidentiality": {
                "description": "Information disclosure and privacy risks",
                "typical_impact": "medium",
                "keywords": ["confidential", "proprietary", "disclosure", "secret"]
            },
            "intellectual_property": {
                "description": "IP ownership and usage rights risks",
                "typical_impact": "high",
                "keywords": ["copyright", "trademark", "patent", "intellectual property"]
            },
            "compliance": {
                "description": "Regulatory and legal compliance risks",
                "typical_impact": "high",
                "keywords": ["comply", "regulation", "law", "requirement", "standard"]
            },
            "performance": {
                "description": "Performance obligations and delivery risks",
                "typical_impact": "medium",
                "keywords": ["perform", "deliver", "complete", "service", "obligation"]
            },
            "dispute": {
                "description": "Dispute resolution and litigation risks",
                "typical_impact": "medium",
                "keywords": ["dispute", "arbitration", "court", "litigation", "mediation"]
            }
        }
        
        # Common legal red flags that indicate high risk
        self.red_flag_patterns = [
            r"unlimited\s+liability",
            r"personal\s+guarantee",
            r"waive\s+all\s+rights",
            r"no\s+right\s+to\s+cancel",
            r"automatic\s+renewal",
            r"liquidated\s+damages",
            r"attorney\s+fees\s+and\s+costs",
            r"indemnify\s+and\s+hold\s+harmless",
            r"sole\s+discretion",
            r"without\s+notice",
            r"irrevocable",
            r"perpetual"
        ]
    
    async def assess_document_risk(
        self,
        clauses: List[Clause],
        user_role: UserRole,
        jurisdiction: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment of a legal document.
        
        Args:
            clauses: List of analyzed clauses
            user_role: User's role for risk perspective
            jurisdiction: Legal jurisdiction for context
            document_type: Type of document being analyzed
            
        Returns:
            RiskAssessment with overall risk analysis
            
        Raises:
            AnalysisError: If risk assessment fails
        """
        try:
            logger.info(f"Assessing document risk for {user_role} role")
            
            # Calculate overall risk metrics
            risk_metrics = self._calculate_risk_metrics(clauses)
            
            # Identify red flags
            red_flags = await self._identify_red_flags(clauses, user_role)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                clauses, user_role, jurisdiction, document_type
            )
            
            # Identify key negotiation points
            negotiation_points = await self._identify_negotiation_points(
                clauses, user_role
            )
            
            # Categorize risks by type
            risk_categories = self._categorize_risks(clauses)
            
            # Determine overall risk level
            overall_risk = self._determine_overall_risk_level(risk_metrics, red_flags)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(clauses)
            
            # Create RiskAssessment object
            risk_assessment = RiskAssessment(
                overall_risk=overall_risk,
                risk_score=risk_metrics["overall_risk_score"],
                high_risk_clauses=risk_metrics["high_risk_count"],
                medium_risk_clauses=risk_metrics["medium_risk_count"],
                low_risk_clauses=risk_metrics["low_risk_count"],
                recommendations=recommendations,
                negotiation_points=negotiation_points,
                red_flags=red_flags,
                risk_categories=risk_categories,
                confidence=confidence
            )
            
            logger.info(f"Risk assessment completed: {overall_risk} risk level")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            raise AnalysisError(f"Failed to assess document risk: {str(e)}") from e
    
    def _calculate_risk_metrics(self, clauses: List[Clause]) -> Dict[str, Any]:
        """Calculate basic risk metrics from clauses."""
        if not clauses:
            return {
                "overall_risk_score": 0.0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "average_impact": 0,
                "average_likelihood": 0
            }
        
        # Count clauses by risk level
        high_risk_count = len([c for c in clauses if c.risk_score > 0.7])
        medium_risk_count = len([c for c in clauses if 0.3 < c.risk_score <= 0.7])
        low_risk_count = len([c for c in clauses if c.risk_score <= 0.3])
        
        # Calculate averages
        total_clauses = len(clauses)
        overall_risk_score = sum(clause.risk_score for clause in clauses) / total_clauses
        average_impact = sum(clause.impact_score for clause in clauses) / total_clauses
        average_likelihood = sum(clause.likelihood_score for clause in clauses) / total_clauses
        
        return {
            "overall_risk_score": overall_risk_score,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "average_impact": average_impact,
            "average_likelihood": average_likelihood
        }
    
    async def _identify_red_flags(
        self, 
        clauses: List[Clause], 
        user_role: UserRole
    ) -> List[str]:
        """Identify critical red flags in the document."""
        red_flags = []
        
        # Check for pattern-based red flags
        for clause in clauses:
            clause_text_lower = clause.text.lower()
            
            for pattern in self.red_flag_patterns:
                if re.search(pattern, clause_text_lower):
                    red_flag_description = self._describe_red_flag(pattern, clause, user_role)
                    if red_flag_description not in red_flags:
                        red_flags.append(red_flag_description)
        
        # Use AI to identify additional red flags
        ai_red_flags = await self._identify_ai_red_flags(clauses, user_role)
        red_flags.extend(ai_red_flags)
        
        return red_flags[:10]  # Limit to top 10 red flags
    
    def _describe_red_flag(self, pattern: str, clause: Clause, user_role: UserRole) -> str:
        """Create a description for a red flag pattern."""
        descriptions = {
            r"unlimited\s+liability": f"Unlimited liability clause could expose {user_role.value} to significant financial risk",
            r"personal\s+guarantee": f"Personal guarantee requirement puts {user_role.value}'s personal assets at risk",
            r"waive\s+all\s+rights": f"Rights waiver clause removes important legal protections for {user_role.value}",
            r"no\s+right\s+to\s+cancel": f"No cancellation rights could trap {user_role.value} in unfavorable agreement",
            r"automatic\s+renewal": f"Automatic renewal clause could continue agreement without {user_role.value}'s consent",
            r"liquidated\s+damages": f"Liquidated damages clause could result in significant penalties for {user_role.value}",
            r"attorney\s+fees\s+and\s+costs": f"Attorney fees clause could make {user_role.value} pay opponent's legal costs",
            r"indemnify\s+and\s+hold\s+harmless": f"Indemnification clause could make {user_role.value} liable for third-party claims",
            r"sole\s+discretion": f"Sole discretion clause gives other party unilateral control over important decisions",
            r"without\s+notice": f"No notice requirement could result in sudden changes affecting {user_role.value}",
            r"irrevocable": f"Irrevocable clause prevents {user_role.value} from changing or canceling agreement",
            r"perpetual": f"Perpetual clause creates indefinite obligations for {user_role.value}"
        }
        
        return descriptions.get(pattern, f"Potentially risky clause identified: {pattern}")
    
    async def _identify_ai_red_flags(
        self, 
        clauses: List[Clause], 
        user_role: UserRole
    ) -> List[str]:
        """Use AI to identify additional red flags."""
        try:
            # Focus on highest risk clauses
            high_risk_clauses = [c for c in clauses if c.risk_score > 0.7]
            if not high_risk_clauses:
                return []
            
            # Build prompt for red flag identification
            prompt = self._build_red_flag_prompt(high_risk_clauses, user_role)
            
            response = await self.pro_model.generate_content_async(prompt)
            
            # Parse red flags from response
            red_flags = self._parse_red_flags_response(response.text)
            
            return red_flags
            
        except Exception as e:
            logger.warning(f"AI red flag identification failed: {str(e)}")
            return []
    
    def _build_red_flag_prompt(self, clauses: List[Clause], user_role: UserRole) -> str:
        """Build prompt for AI red flag identification."""
        clauses_text = "\n\n".join([
            f"Clause {i+1}: {clause.text}" 
            for i, clause in enumerate(clauses[:5])  # Limit to top 5
        ])
        
        return f"""
You are a legal expert identifying critical red flags in contract clauses from the perspective of a {user_role.value}.

Analyze these high-risk clauses and identify the most serious red flags that could significantly harm the {user_role.value}:

{clauses_text}

Focus on:
1. Unusual or extreme liability provisions
2. Unfair termination or cancellation terms
3. Excessive penalties or damages
4. Rights waivers or limitations
5. Unbalanced power dynamics
6. Hidden costs or obligations

Return as a JSON array of strings, where each string describes a specific red flag and its potential impact.
Example: ["Clause allows termination without cause or notice, leaving tenant vulnerable to sudden eviction"]

Return only the JSON array, no other text.
"""
    
    def _parse_red_flags_response(self, response_text: str) -> List[str]:
        """Parse red flags from AI response."""
        try:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                red_flags = json.loads(json_match.group())
                return [str(flag) for flag in red_flags if isinstance(flag, str)]
            else:
                return []
        except (json.JSONDecodeError, ValueError):
            return []
    
    async def _generate_recommendations(
        self,
        clauses: List[Clause],
        user_role: UserRole,
        jurisdiction: Optional[str],
        document_type: Optional[str]
    ) -> List[str]:
        """Generate actionable recommendations for risk mitigation."""
        try:
            # Build prompt for recommendations
            prompt = self._build_recommendations_prompt(
                clauses, user_role, jurisdiction, document_type
            )
            
            response = await self.pro_model.generate_content_async(prompt)
            
            # Parse recommendations
            recommendations = self._parse_recommendations_response(response.text)
            
            # Add standard recommendations based on risk patterns
            standard_recommendations = self._generate_standard_recommendations(clauses, user_role)
            
            # Combine and deduplicate
            all_recommendations = recommendations + standard_recommendations
            unique_recommendations = []
            for rec in all_recommendations:
                if rec not in unique_recommendations:
                    unique_recommendations.append(rec)
            
            return unique_recommendations[:8]  # Limit to 8 recommendations
            
        except Exception as e:
            logger.warning(f"Recommendation generation failed: {str(e)}")
            return self._generate_standard_recommendations(clauses, user_role)
    
    def _build_recommendations_prompt(
        self,
        clauses: List[Clause],
        user_role: UserRole,
        jurisdiction: Optional[str],
        document_type: Optional[str]
    ) -> str:
        """Build prompt for recommendation generation."""
        jurisdiction_context = f" in {jurisdiction}" if jurisdiction else ""
        doc_context = f" for a {document_type}" if document_type else ""
        
        # Summarize key risks
        high_risk_clauses = [c for c in clauses if c.risk_score > 0.7]
        risk_summary = f"Document contains {len(high_risk_clauses)} high-risk clauses"
        
        return f"""
You are a legal advisor providing recommendations to a {user_role.value}{jurisdiction_context}{doc_context}.

RISK SUMMARY: {risk_summary}

Provide practical, actionable recommendations for managing the risks in this document. Focus on:

1. Specific actions the {user_role.value} should take
2. Clauses that should be negotiated or modified
3. Additional protections that should be added
4. Professional advice that may be needed
5. Documentation or evidence to maintain

Return as a JSON array of strings, where each string is a clear, actionable recommendation.
Example: ["Request a 30-day notice period for termination instead of immediate termination"]

Limit to the 6 most important recommendations.
Return only the JSON array, no other text.
"""
    
    def _parse_recommendations_response(self, response_text: str) -> List[str]:
        """Parse recommendations from AI response."""
        try:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return [str(rec) for rec in recommendations if isinstance(rec, str)]
            else:
                return []
        except (json.JSONDecodeError, ValueError):
            return []
    
    def _generate_standard_recommendations(
        self, 
        clauses: List[Clause], 
        user_role: UserRole
    ) -> List[str]:
        """Generate standard recommendations based on risk patterns."""
        recommendations = []
        
        # Check for high-risk clauses
        high_risk_count = len([c for c in clauses if c.risk_score > 0.7])
        if high_risk_count > 0:
            recommendations.append("Consider having this document reviewed by a qualified attorney")
        
        # Check for liability clauses
        liability_clauses = [c for c in clauses if c.category == "liability"]
        if liability_clauses:
            recommendations.append("Review liability provisions carefully and consider liability insurance")
        
        # Check for termination clauses
        termination_clauses = [c for c in clauses if c.category == "termination"]
        if termination_clauses:
            recommendations.append("Ensure termination conditions are fair and provide adequate notice")
        
        # Check for payment clauses
        payment_clauses = [c for c in clauses if c.category == "payment"]
        if payment_clauses:
            recommendations.append("Verify all payment terms and due dates are clearly understood")
        
        return recommendations
    
    async def _identify_negotiation_points(
        self, 
        clauses: List[Clause], 
        user_role: UserRole
    ) -> List[str]:
        """Identify key points that should be negotiated."""
        negotiation_points = []
        
        # Focus on high and medium risk clauses
        negotiable_clauses = [c for c in clauses if c.risk_score > 0.4]
        
        for clause in negotiable_clauses:
            # Check if clause has role-specific analysis with negotiation points
            if user_role in clause.role_analysis:
                role_analysis = clause.role_analysis[user_role]
                negotiation_points.extend(role_analysis.negotiation_points)
        
        # Add AI-generated negotiation points
        ai_negotiation_points = await self._generate_ai_negotiation_points(
            negotiable_clauses, user_role
        )
        negotiation_points.extend(ai_negotiation_points)
        
        # Deduplicate and limit
        unique_points = []
        for point in negotiation_points:
            if point not in unique_points:
                unique_points.append(point)
        
        return unique_points[:6]  # Limit to 6 key negotiation points
    
    async def _generate_ai_negotiation_points(
        self, 
        clauses: List[Clause], 
        user_role: UserRole
    ) -> List[str]:
        """Generate negotiation points using AI."""
        try:
            if not clauses:
                return []
            
            # Build prompt for negotiation points
            prompt = f"""
Identify key negotiation points for a {user_role.value} in these contract clauses:

{chr(10).join([f"- {clause.text[:200]}..." for clause in clauses[:3]])}

Focus on terms that could be modified to better protect the {user_role.value}'s interests.

Return as a JSON array of specific negotiation points.
Example: ["Request right to terminate with 30 days notice", "Negotiate cap on liability damages"]

Return only the JSON array, no other text.
"""
            
            response = await self.pro_model.generate_content_async(prompt)
            
            # Parse response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                points = json.loads(json_match.group())
                return [str(point) for point in points if isinstance(point, str)]
            
            return []
            
        except Exception as e:
            logger.warning(f"AI negotiation points generation failed: {str(e)}")
            return []
    
    def _categorize_risks(self, clauses: List[Clause]) -> Dict[str, float]:
        """Categorize risks by type and calculate risk scores."""
        risk_categories = {}
        
        # Initialize categories
        for category in self.risk_categories:
            risk_categories[category] = 0.0
        
        # Categorize clauses and calculate risk scores
        category_counts = {category: 0 for category in self.risk_categories}
        
        for clause in clauses:
            # Determine category based on clause category or keywords
            clause_category = self._determine_clause_risk_category(clause)
            
            if clause_category in risk_categories:
                # Add weighted risk score
                risk_categories[clause_category] += clause.risk_score
                category_counts[clause_category] += 1
        
        # Calculate average risk scores for each category
        for category in risk_categories:
            if category_counts[category] > 0:
                risk_categories[category] = risk_categories[category] / category_counts[category]
        
        # Remove categories with no risk
        return {k: v for k, v in risk_categories.items() if v > 0}
    
    def _determine_clause_risk_category(self, clause: Clause) -> str:
        """Determine the risk category for a clause."""
        # First check if clause already has a category that matches our risk categories
        if clause.category and clause.category in self.risk_categories:
            return clause.category
        
        # Otherwise, determine category based on keywords
        clause_text_lower = clause.text.lower()
        
        for category, info in self.risk_categories.items():
            for keyword in info["keywords"]:
                if keyword in clause_text_lower:
                    return category
        
        # Default to performance if no specific category found
        return "performance"
    
    def _determine_overall_risk_level(
        self, 
        risk_metrics: Dict[str, Any], 
        red_flags: List[str]
    ) -> RiskLevel:
        """Determine the overall risk level of the document."""
        overall_score = risk_metrics["overall_risk_score"]
        high_risk_count = risk_metrics["high_risk_count"]
        red_flag_count = len(red_flags)
        
        # Calculate composite risk score
        composite_score = 0
        
        # Factor 1: Overall risk score (40% weight)
        composite_score += overall_score * 40
        
        # Factor 2: High-risk clause proportion (30% weight)
        total_clauses = (risk_metrics["high_risk_count"] + 
                        risk_metrics["medium_risk_count"] + 
                        risk_metrics["low_risk_count"])
        if total_clauses > 0:
            high_risk_ratio = high_risk_count / total_clauses
            composite_score += high_risk_ratio * 30
        
        # Factor 3: Red flags (30% weight)
        red_flag_score = min(1.0, red_flag_count / 5)  # Normalize to 0-1
        composite_score += red_flag_score * 30
        
        # Determine risk level
        if composite_score >= 70:
            return RiskLevel.HIGH
        elif composite_score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_confidence_score(self, clauses: List[Clause]) -> float:
        """Calculate confidence score for the risk assessment."""
        if not clauses:
            return 0.0
        
        # Base confidence on number of clauses analyzed
        clause_count_factor = min(1.0, len(clauses) / 10)  # Full confidence at 10+ clauses
        
        # Factor in clause analysis quality (based on presence of detailed analysis)
        detailed_analysis_count = 0
        for clause in clauses:
            if (clause.safer_alternatives or 
                clause.legal_citations or 
                clause.role_analysis):
                detailed_analysis_count += 1
        
        analysis_quality_factor = detailed_analysis_count / len(clauses) if clauses else 0
        
        # Combine factors
        confidence = (clause_count_factor * 0.6) + (analysis_quality_factor * 0.4)
        
        return min(1.0, confidence)
    
    async def generate_safer_alternatives(
        self,
        clause: Clause,
        user_role: UserRole,
        jurisdiction: Optional[str] = None
    ) -> List[SaferAlternative]:
        """
        Generate safer alternative wordings for a risky clause.
        
        Args:
            clause: The clause to improve
            user_role: User's role for perspective
            jurisdiction: Legal jurisdiction for context
            
        Returns:
            List of SaferAlternative objects
        """
        try:
            if clause.risk_score < 0.3:
                # Low-risk clauses don't need alternatives
                return []
            
            # Build prompt for safer alternatives
            prompt = self._build_safer_alternatives_prompt(clause, user_role, jurisdiction)
            
            response = await self.pro_model.generate_content_async(prompt)
            
            # Parse alternatives from response
            alternatives_data = self._parse_safer_alternatives_response(response.text)
            
            # Create SaferAlternative objects
            safer_alternatives = []
            for alt_data in alternatives_data:
                try:
                    alternative = SaferAlternative(
                        suggested_text=alt_data.get("suggested_text", ""),
                        rationale=alt_data.get("rationale", ""),
                        legal_basis=alt_data.get("legal_basis"),
                        confidence=max(0.0, min(1.0, float(alt_data.get("confidence", 0.7)))),
                        impact_reduction=max(0.0, min(1.0, float(alt_data.get("impact_reduction", 0.3))))
                    )
                    safer_alternatives.append(alternative)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid safer alternative data: {str(e)}")
                    continue
            
            return safer_alternatives[:3]  # Limit to 3 alternatives
            
        except Exception as e:
            logger.error(f"Safer alternatives generation failed: {str(e)}")
            return []
    
    def _build_safer_alternatives_prompt(
        self,
        clause: Clause,
        user_role: UserRole,
        jurisdiction: Optional[str]
    ) -> str:
        """Build prompt for generating safer alternatives."""
        jurisdiction_context = f" under {jurisdiction} law" if jurisdiction else ""
        
        return f"""
You are a legal expert helping a {user_role.value} negotiate safer contract terms{jurisdiction_context}.

ORIGINAL CLAUSE (Risk Score: {clause.risk_score:.2f}):
"{clause.text}"

CLAUSE CLASSIFICATION: {clause.classification}
RISK FACTORS: Impact {clause.impact_score}/100, Likelihood {clause.likelihood_score}/100

Generate 2-3 safer alternative wordings that:
1. Reduce risk for the {user_role.value}
2. Maintain the essential business purpose
3. Are legally sound and enforceable
4. Address the specific risks identified

Return as JSON array with this format:
[
  {{
    "suggested_text": "safer clause wording",
    "rationale": "explanation of why this is safer",
    "legal_basis": "legal principle or precedent supporting this change",
    "confidence": 0.0-1.0,
    "impact_reduction": 0.0-1.0
  }}
]

Return only the JSON array, no other text.
"""
    
    def _parse_safer_alternatives_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse safer alternatives from AI response."""
        try:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                alternatives = json.loads(json_match.group())
                return alternatives if isinstance(alternatives, list) else []
            else:
                return []
        except (json.JSONDecodeError, ValueError):
            return []