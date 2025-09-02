"""
Jurisdiction Data Agent for legal database queries and jurisdiction-specific analysis.

This agent handles:
- BigQuery integration for legal database queries
- Statute and regulation reference system
- Legal precedent matching and citation generation
- Jurisdiction-specific law compliance checking
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import re

from google.cloud import bigquery
from google.api_core import exceptions as gcp_exceptions
import vertexai
from vertexai.generative_models import GenerativeModel

from ..core.config import get_settings
from ..models.document import LegalCitation, Clause, ClauseClassification
from ..models.base import UserRole
from ..core.exceptions import AnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


class JurisdictionDataAgent:
    """
    Specialized agent for jurisdiction-aware legal analysis and data retrieval.
    
    Integrates with BigQuery legal databases to provide jurisdiction-specific
    legal context, statutes, regulations, and precedents.
    """
    
    def __init__(self):
        """Initialize the Jurisdiction Data Agent."""
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.BIGQUERY_LOCATION
        )
        
        # Initialize Vertex AI for legal analysis
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        
        # Use Pro model for complex legal analysis
        self.gemini_model = GenerativeModel(settings.GEMINI_MODEL_PRO)
        
        # Dataset and table references
        self.dataset_id = settings.BIGQUERY_DATASET_ID
        self.statutes_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{self.dataset_id}.{settings.BIGQUERY_STATUTES_TABLE}"
        self.regulations_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{self.dataset_id}.{settings.BIGQUERY_REGULATIONS_TABLE}"
        self.precedents_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{self.dataset_id}.{settings.BIGQUERY_PRECEDENTS_TABLE}"
        
        # Jurisdiction mappings
        self.jurisdiction_mappings = {
            "US": ["United States", "Federal", "USA"],
            "CA": ["California", "CA", "Calif"],
            "NY": ["New York", "NY", "New York State"],
            "TX": ["Texas", "TX", "Tex"],
            "FL": ["Florida", "FL", "Fla"],
            "IL": ["Illinois", "IL", "Ill"],
            "PA": ["Pennsylvania", "PA", "Penn"],
            "OH": ["Ohio", "OH"],
            "GA": ["Georgia", "GA"],
            "NC": ["North Carolina", "NC"],
            "MI": ["Michigan", "MI", "Mich"],
            "NJ": ["New Jersey", "NJ"],
            "VA": ["Virginia", "VA"],
            "WA": ["Washington", "WA", "Washington State"],
            "AZ": ["Arizona", "AZ", "Ariz"],
            "MA": ["Massachusetts", "MA", "Mass"],
            "TN": ["Tennessee", "TN", "Tenn"],
            "IN": ["Indiana", "IN", "Ind"],
            "MO": ["Missouri", "MO"],
            "MD": ["Maryland", "MD"],
            "WI": ["Wisconsin", "WI", "Wis"],
            "CO": ["Colorado", "CO", "Colo"],
            "MN": ["Minnesota", "MN", "Minn"],
            "SC": ["South Carolina", "SC"],
            "AL": ["Alabama", "AL", "Ala"],
            "LA": ["Louisiana", "LA"],
            "KY": ["Kentucky", "KY"],
            "OR": ["Oregon", "OR", "Ore"],
            "OK": ["Oklahoma", "OK", "Okla"],
            "CT": ["Connecticut", "CT", "Conn"],
            "UT": ["Utah", "UT"],
            "IA": ["Iowa", "IA"],
            "NV": ["Nevada", "NV", "Nev"],
            "AR": ["Arkansas", "AR", "Ark"],
            "MS": ["Mississippi", "MS", "Miss"],
            "KS": ["Kansas", "KS", "Kan"],
            "NM": ["New Mexico", "NM"],
            "NE": ["Nebraska", "NE", "Neb"],
            "WV": ["West Virginia", "WV"],
            "ID": ["Idaho", "ID"],
            "HI": ["Hawaii", "HI"],
            "NH": ["New Hampshire", "NH"],
            "ME": ["Maine", "ME"],
            "MT": ["Montana", "MT", "Mont"],
            "RI": ["Rhode Island", "RI"],
            "DE": ["Delaware", "DE", "Del"],
            "SD": ["South Dakota", "SD"],
            "ND": ["North Dakota", "ND"],
            "AK": ["Alaska", "AK"],
            "VT": ["Vermont", "VT"],
            "WY": ["Wyoming", "WY", "Wyo"],
            "DC": ["District of Columbia", "DC", "Washington DC"]
        }
        
        # Legal area mappings for better search
        self.legal_areas = {
            "contract": ["contract", "agreement", "covenant", "obligation"],
            "employment": ["employment", "labor", "workplace", "employee", "employer"],
            "real_estate": ["real estate", "property", "lease", "rental", "landlord", "tenant"],
            "consumer": ["consumer", "purchase", "sale", "warranty", "return"],
            "privacy": ["privacy", "data protection", "confidentiality", "personal information"],
            "intellectual_property": ["copyright", "trademark", "patent", "trade secret", "ip"],
            "corporate": ["corporate", "business", "company", "corporation", "llc"],
            "finance": ["finance", "loan", "credit", "banking", "investment"],
            "insurance": ["insurance", "coverage", "claim", "policy", "premium"],
            "healthcare": ["healthcare", "medical", "hipaa", "patient", "health"]
        }
    
    async def get_jurisdiction_context(
        self, 
        jurisdiction: str, 
        legal_area: Optional[str] = None,
        clause_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive jurisdiction context for legal analysis.
        
        Args:
            jurisdiction: Legal jurisdiction (e.g., "CA", "NY", "US")
            legal_area: Specific legal area (e.g., "contract", "employment")
            clause_text: Specific clause text for targeted analysis
            
        Returns:
            Dictionary containing jurisdiction-specific legal context
            
        Raises:
            AnalysisError: If jurisdiction context retrieval fails
        """
        try:
            logger.info(f"Retrieving jurisdiction context for {jurisdiction}")
            
            # Normalize jurisdiction
            normalized_jurisdiction = self._normalize_jurisdiction(jurisdiction)
            
            # Get relevant statutes and regulations
            statutes = await self._get_relevant_statutes(
                normalized_jurisdiction, legal_area, clause_text
            )
            
            regulations = await self._get_relevant_regulations(
                normalized_jurisdiction, legal_area, clause_text
            )
            
            precedents = await self._get_relevant_precedents(
                normalized_jurisdiction, legal_area, clause_text
            )
            
            # Generate jurisdiction summary
            jurisdiction_summary = await self._generate_jurisdiction_summary(
                normalized_jurisdiction, statutes, regulations, precedents
            )
            
            context = {
                "jurisdiction": normalized_jurisdiction,
                "jurisdiction_full_name": self._get_jurisdiction_full_name(normalized_jurisdiction),
                "legal_area": legal_area,
                "statutes": statutes,
                "regulations": regulations,
                "precedents": precedents,
                "summary": jurisdiction_summary,
                "last_updated": datetime.utcnow().isoformat(),
                "confidence": self._calculate_context_confidence(statutes, regulations, precedents)
            }
            
            logger.info(f"Retrieved {len(statutes)} statutes, {len(regulations)} regulations, {len(precedents)} precedents")
            return context
            
        except Exception as e:
            logger.error(f"Failed to get jurisdiction context: {str(e)}")
            raise AnalysisError(f"Jurisdiction context retrieval failed: {str(e)}") from e
    
    async def analyze_clause_jurisdiction_compliance(
        self, 
        clause: Clause, 
        jurisdiction: str,
        user_role: UserRole
    ) -> Dict[str, Any]:
        """
        Analyze a clause for jurisdiction-specific compliance issues.
        
        Args:
            clause: Clause to analyze
            jurisdiction: Target jurisdiction
            user_role: User's role for analysis perspective
            
        Returns:
            Dictionary containing compliance analysis results
        """
        try:
            logger.info(f"Analyzing clause compliance for {jurisdiction}")
            
            # Get jurisdiction context
            legal_area = self._determine_legal_area(clause.text)
            context = await self.get_jurisdiction_context(
                jurisdiction, legal_area, clause.text
            )
            
            # Analyze compliance using AI
            compliance_analysis = await self._analyze_compliance_with_ai(
                clause, context, user_role
            )
            
            # Check for specific compliance issues
            compliance_issues = await self._check_specific_compliance_issues(
                clause, context, user_role
            )
            
            # Generate safer alternatives if needed
            safer_alternatives = []
            if compliance_analysis.get("compliance_risk", 0) > 0.6:
                safer_alternatives = await self._generate_jurisdiction_safe_alternatives(
                    clause, context, user_role
                )
            
            result = {
                "jurisdiction": jurisdiction,
                "legal_area": legal_area,
                "compliance_score": compliance_analysis.get("compliance_score", 0.5),
                "compliance_risk": compliance_analysis.get("compliance_risk", 0.5),
                "compliance_issues": compliance_issues,
                "applicable_laws": context.get("statutes", [])[:5],  # Top 5 most relevant
                "relevant_regulations": context.get("regulations", [])[:3],
                "legal_precedents": context.get("precedents", [])[:3],
                "safer_alternatives": safer_alternatives,
                "recommendations": compliance_analysis.get("recommendations", []),
                "citations": self._create_legal_citations_from_context(context),
                "confidence": compliance_analysis.get("confidence", 0.7),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Clause jurisdiction compliance analysis failed: {str(e)}")
            raise AnalysisError(f"Compliance analysis failed: {str(e)}") from e
    
    async def _get_relevant_statutes(
        self, 
        jurisdiction: str, 
        legal_area: Optional[str] = None,
        clause_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant statutes from BigQuery."""
        try:
            # Build query based on parameters
            query_conditions = [f"jurisdiction = '{jurisdiction}'"]
            
            if legal_area:
                area_keywords = self.legal_areas.get(legal_area, [legal_area])
                keyword_conditions = " OR ".join([
                    f"LOWER(title) LIKE '%{keyword}%' OR LOWER(description) LIKE '%{keyword}%'"
                    for keyword in area_keywords
                ])
                query_conditions.append(f"({keyword_conditions})")
            
            if clause_text:
                # Extract key terms from clause for better matching
                key_terms = self._extract_legal_terms(clause_text)
                if key_terms:
                    term_conditions = " OR ".join([
                        f"LOWER(content) LIKE '%{term}%'"
                        for term in key_terms[:5]  # Limit to top 5 terms
                    ])
                    query_conditions.append(f"({term_conditions})")
            
            query = f"""
            SELECT 
                statute_id,
                title,
                section,
                description,
                content,
                effective_date,
                url,
                relevance_score
            FROM `{self.statutes_table}`
            WHERE {' AND '.join(query_conditions)}
            ORDER BY relevance_score DESC, effective_date DESC
            LIMIT 10
            """
            
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            statutes = []
            for row in results:
                statute = {
                    "id": row.statute_id,
                    "title": row.title,
                    "section": row.section,
                    "description": row.description,
                    "content": row.content[:1000] if row.content else "",  # Truncate for performance
                    "effective_date": row.effective_date.isoformat() if row.effective_date else None,
                    "url": row.url,
                    "relevance_score": float(row.relevance_score) if row.relevance_score else 0.5,
                    "type": "statute"
                }
                statutes.append(statute)
            
            return statutes
            
        except Exception as e:
            logger.warning(f"Failed to retrieve statutes: {str(e)}")
            return []
    
    async def _get_relevant_regulations(
        self, 
        jurisdiction: str, 
        legal_area: Optional[str] = None,
        clause_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant regulations from BigQuery."""
        try:
            # Similar query structure as statutes
            query_conditions = [f"jurisdiction = '{jurisdiction}'"]
            
            if legal_area:
                area_keywords = self.legal_areas.get(legal_area, [legal_area])
                keyword_conditions = " OR ".join([
                    f"LOWER(title) LIKE '%{keyword}%' OR LOWER(description) LIKE '%{keyword}%'"
                    for keyword in area_keywords
                ])
                query_conditions.append(f"({keyword_conditions})")
            
            if clause_text:
                key_terms = self._extract_legal_terms(clause_text)
                if key_terms:
                    term_conditions = " OR ".join([
                        f"LOWER(content) LIKE '%{term}%'"
                        for term in key_terms[:5]
                    ])
                    query_conditions.append(f"({term_conditions})")
            
            query = f"""
            SELECT 
                regulation_id,
                title,
                section,
                description,
                content,
                effective_date,
                agency,
                url,
                relevance_score
            FROM `{self.regulations_table}`
            WHERE {' AND '.join(query_conditions)}
            ORDER BY relevance_score DESC, effective_date DESC
            LIMIT 8
            """
            
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            regulations = []
            for row in results:
                regulation = {
                    "id": row.regulation_id,
                    "title": row.title,
                    "section": row.section,
                    "description": row.description,
                    "content": row.content[:1000] if row.content else "",
                    "effective_date": row.effective_date.isoformat() if row.effective_date else None,
                    "agency": row.agency,
                    "url": row.url,
                    "relevance_score": float(row.relevance_score) if row.relevance_score else 0.5,
                    "type": "regulation"
                }
                regulations.append(regulation)
            
            return regulations
            
        except Exception as e:
            logger.warning(f"Failed to retrieve regulations: {str(e)}")
            return []
    
    async def _get_relevant_precedents(
        self, 
        jurisdiction: str, 
        legal_area: Optional[str] = None,
        clause_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant legal precedents from BigQuery."""
        try:
            # Query for precedents with broader jurisdiction matching
            jurisdiction_conditions = [f"jurisdiction = '{jurisdiction}'"]
            
            # Also include federal precedents for state jurisdictions
            if jurisdiction != "US":
                jurisdiction_conditions.append("jurisdiction = 'US'")
            
            query_conditions = [f"({' OR '.join(jurisdiction_conditions)})"]
            
            if legal_area:
                area_keywords = self.legal_areas.get(legal_area, [legal_area])
                keyword_conditions = " OR ".join([
                    f"LOWER(case_name) LIKE '%{keyword}%' OR LOWER(summary) LIKE '%{keyword}%'"
                    for keyword in area_keywords
                ])
                query_conditions.append(f"({keyword_conditions})")
            
            if clause_text:
                key_terms = self._extract_legal_terms(clause_text)
                if key_terms:
                    term_conditions = " OR ".join([
                        f"LOWER(summary) LIKE '%{term}%' OR LOWER(holding) LIKE '%{term}%'"
                        for term in key_terms[:5]
                    ])
                    query_conditions.append(f"({term_conditions})")
            
            query = f"""
            SELECT 
                case_id,
                case_name,
                court,
                decision_date,
                summary,
                holding,
                citation,
                url,
                relevance_score,
                jurisdiction
            FROM `{self.precedents_table}`
            WHERE {' AND '.join(query_conditions)}
            ORDER BY 
                CASE WHEN jurisdiction = '{jurisdiction}' THEN 1 ELSE 2 END,
                relevance_score DESC, 
                decision_date DESC
            LIMIT 6
            """
            
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            precedents = []
            for row in results:
                precedent = {
                    "id": row.case_id,
                    "case_name": row.case_name,
                    "court": row.court,
                    "decision_date": row.decision_date.isoformat() if row.decision_date else None,
                    "summary": row.summary,
                    "holding": row.holding,
                    "citation": row.citation,
                    "url": row.url,
                    "relevance_score": float(row.relevance_score) if row.relevance_score else 0.5,
                    "jurisdiction": row.jurisdiction,
                    "type": "precedent"
                }
                precedents.append(precedent)
            
            return precedents
            
        except Exception as e:
            logger.warning(f"Failed to retrieve precedents: {str(e)}")
            return []
    
    def _normalize_jurisdiction(self, jurisdiction: str) -> str:
        """Normalize jurisdiction string to standard format."""
        if not jurisdiction:
            return "US"
        
        jurisdiction_upper = jurisdiction.upper().strip()
        
        # Direct mapping
        if jurisdiction_upper in self.jurisdiction_mappings:
            return jurisdiction_upper
        
        # Search in alternative names
        for code, alternatives in self.jurisdiction_mappings.items():
            if jurisdiction_upper in [alt.upper() for alt in alternatives]:
                return code
        
        # Default to US if not found
        logger.warning(f"Unknown jurisdiction '{jurisdiction}', defaulting to US")
        return "US"
    
    def _get_jurisdiction_full_name(self, jurisdiction_code: str) -> str:
        """Get full name for jurisdiction code."""
        mapping = self.jurisdiction_mappings.get(jurisdiction_code, [jurisdiction_code])
        return mapping[0] if mapping else jurisdiction_code
    
    def _determine_legal_area(self, clause_text: str) -> Optional[str]:
        """Determine the legal area based on clause content."""
        clause_lower = clause_text.lower()
        
        # Score each legal area based on keyword matches
        area_scores = {}
        for area, keywords in self.legal_areas.items():
            score = sum(1 for keyword in keywords if keyword in clause_lower)
            if score > 0:
                area_scores[area] = score
        
        # Return the area with the highest score
        if area_scores:
            return max(area_scores, key=area_scores.get)
        
        return None
    
    def _extract_legal_terms(self, text: str) -> List[str]:
        """Extract key legal terms from text for search."""
        # Common legal terms that are useful for search
        legal_keywords = [
            "agreement", "contract", "covenant", "obligation", "liability",
            "indemnify", "warrant", "represent", "breach", "default",
            "terminate", "cancel", "modify", "amend", "confidential",
            "proprietary", "damages", "penalty", "fee", "payment",
            "dispute", "arbitration", "mediation", "governing", "jurisdiction"
        ]
        
        text_lower = text.lower()
        found_terms = []
        
        for term in legal_keywords:
            if term in text_lower:
                found_terms.append(term)
        
        # Also extract quoted terms (often important legal concepts)
        quoted_terms = re.findall(r'"([^"]*)"', text)
        found_terms.extend([term.lower() for term in quoted_terms if len(term) > 3])
        
        return list(set(found_terms))[:10]  # Return unique terms, limit to 10
    
    async def _generate_jurisdiction_summary(
        self, 
        jurisdiction: str, 
        statutes: List[Dict], 
        regulations: List[Dict], 
        precedents: List[Dict]
    ) -> str:
        """Generate AI-powered jurisdiction summary."""
        try:
            # Prepare context for AI
            context_items = []
            
            for statute in statutes[:3]:  # Top 3 statutes
                context_items.append(f"Statute: {statute['title']} - {statute['description']}")
            
            for regulation in regulations[:2]:  # Top 2 regulations
                context_items.append(f"Regulation: {regulation['title']} - {regulation['description']}")
            
            for precedent in precedents[:2]:  # Top 2 precedents
                context_items.append(f"Case: {precedent['case_name']} - {precedent['summary']}")
            
            if not context_items:
                return f"Limited legal data available for {self._get_jurisdiction_full_name(jurisdiction)}."
            
            prompt = f"""
            Provide a concise summary of the legal landscape for {self._get_jurisdiction_full_name(jurisdiction)} based on the following legal authorities:

            {chr(10).join(context_items)}

            Create a 2-3 sentence summary highlighting:
            1. Key legal principles or trends
            2. Important considerations for contract analysis
            3. Notable regulatory requirements

            Keep the summary professional and factual.
            """
            
            response = await self.gemini_model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate jurisdiction summary: {str(e)}")
            return f"Legal analysis available for {self._get_jurisdiction_full_name(jurisdiction)}."
    
    async def _analyze_compliance_with_ai(
        self, 
        clause: Clause, 
        context: Dict[str, Any], 
        user_role: UserRole
    ) -> Dict[str, Any]:
        """Use AI to analyze clause compliance with jurisdiction laws."""
        try:
            # Prepare legal context
            legal_authorities = []
            
            for statute in context.get("statutes", [])[:3]:
                legal_authorities.append(f"Statute: {statute['title']} - {statute['description']}")
            
            for regulation in context.get("regulations", [])[:2]:
                legal_authorities.append(f"Regulation: {regulation['title']} - {regulation['description']}")
            
            prompt = f"""
            You are a legal compliance expert analyzing a contract clause for jurisdiction-specific compliance.

            Jurisdiction: {context['jurisdiction_full_name']}
            User Role: {user_role.value}
            Legal Area: {context.get('legal_area', 'general')}

            Clause to analyze:
            "{clause.text}"

            Relevant legal authorities:
            {chr(10).join(legal_authorities) if legal_authorities else "No specific authorities found."}

            Analyze this clause and provide your assessment in JSON format:
            {{
                "compliance_score": 0.0-1.0,
                "compliance_risk": 0.0-1.0,
                "confidence": 0.0-1.0,
                "recommendations": ["list", "of", "recommendations"],
                "potential_issues": ["list", "of", "issues"],
                "rationale": "explanation of the analysis"
            }}

            Scoring guidelines:
            - compliance_score: 1.0 = fully compliant, 0.0 = non-compliant
            - compliance_risk: 0.0 = no risk, 1.0 = high risk of legal issues
            - confidence: your confidence in this analysis

            Return only the JSON, no other text.
            """
            
            response = await self.gemini_model.generate_content_async(prompt)
            
            # Parse AI response
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return self._validate_compliance_analysis(analysis)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError):
                # Return default analysis if parsing fails
                return {
                    "compliance_score": 0.7,
                    "compliance_risk": 0.3,
                    "confidence": 0.5,
                    "recommendations": ["Manual legal review recommended"],
                    "potential_issues": ["Analysis parsing failed"],
                    "rationale": "AI analysis could not be parsed, manual review needed"
                }
            
        except Exception as e:
            logger.warning(f"AI compliance analysis failed: {str(e)}")
            return {
                "compliance_score": 0.5,
                "compliance_risk": 0.5,
                "confidence": 0.3,
                "recommendations": ["Consult with local legal counsel"],
                "potential_issues": ["Analysis unavailable"],
                "rationale": f"Analysis failed: {str(e)}"
            }
    
    def _validate_compliance_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize compliance analysis data."""
        return {
            "compliance_score": max(0.0, min(1.0, float(analysis.get("compliance_score", 0.5)))),
            "compliance_risk": max(0.0, min(1.0, float(analysis.get("compliance_risk", 0.5)))),
            "confidence": max(0.0, min(1.0, float(analysis.get("confidence", 0.5)))),
            "recommendations": analysis.get("recommendations", []),
            "potential_issues": analysis.get("potential_issues", []),
            "rationale": analysis.get("rationale", "No rationale provided")
        }
    
    async def _check_specific_compliance_issues(
        self, 
        clause: Clause, 
        context: Dict[str, Any], 
        user_role: UserRole
    ) -> List[Dict[str, Any]]:
        """Check for specific compliance issues based on jurisdiction."""
        issues = []
        clause_lower = clause.text.lower()
        jurisdiction = context.get("jurisdiction", "US")
        
        # California-specific checks
        if jurisdiction == "CA":
            if "unilateral" in clause_lower and "modify" in clause_lower:
                issues.append({
                    "type": "california_unilateral_modification",
                    "severity": "high",
                    "description": "California law restricts unilateral contract modifications",
                    "recommendation": "Add mutual consent requirement for modifications"
                })
            
            if "waive" in clause_lower and ("jury" in clause_lower or "trial" in clause_lower):
                issues.append({
                    "type": "california_jury_waiver",
                    "severity": "medium",
                    "description": "California has specific requirements for jury trial waivers",
                    "recommendation": "Ensure waiver meets California Civil Code requirements"
                })
        
        # New York-specific checks
        if jurisdiction == "NY":
            if "choice of law" in clause_lower and "new york" not in clause_lower:
                issues.append({
                    "type": "new_york_choice_of_law",
                    "severity": "medium",
                    "description": "Non-NY governing law may not be enforceable for NY residents",
                    "recommendation": "Consider NY law for NY-based parties"
                })
        
        # Federal/general checks
        if "liquidated damages" in clause_lower:
            issues.append({
                "type": "liquidated_damages_enforceability",
                "severity": "medium",
                "description": "Liquidated damages must be reasonable and not punitive",
                "recommendation": "Ensure damages are proportional to actual harm"
            })
        
        if user_role == UserRole.CONSUMER and "arbitration" in clause_lower:
            issues.append({
                "type": "consumer_arbitration",
                "severity": "high",
                "description": "Mandatory arbitration clauses may be unenforceable for consumers",
                "recommendation": "Consider making arbitration optional for consumers"
            })
        
        return issues
    
    async def _generate_jurisdiction_safe_alternatives(
        self, 
        clause: Clause, 
        context: Dict[str, Any], 
        user_role: UserRole
    ) -> List[Dict[str, Any]]:
        """Generate jurisdiction-safe alternative clause wordings."""
        try:
            # Get top legal authorities for context
            authorities = []
            for statute in context.get("statutes", [])[:2]:
                authorities.append(f"{statute['title']}: {statute['description']}")
            
            prompt = f"""
            Generate safer alternative wording for this contract clause to comply with {context['jurisdiction_full_name']} law.

            Original clause:
            "{clause.text}"

            User role: {user_role.value}
            Relevant laws: {'; '.join(authorities) if authorities else 'General contract law'}

            Provide 2-3 alternative wordings that:
            1. Maintain the original intent where legally possible
            2. Comply with jurisdiction-specific requirements
            3. Protect the {user_role.value}'s interests

            Format as JSON:
            {{
                "alternatives": [
                    {{
                        "text": "alternative clause wording",
                        "rationale": "why this is safer/compliant",
                        "confidence": 0.0-1.0
                    }}
                ]
            }}

            Return only the JSON, no other text.
            """
            
            response = await self.gemini_model.generate_content_async(prompt)
            
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result.get("alternatives", [])
            except (json.JSONDecodeError, ValueError):
                pass
            
            return []
            
        except Exception as e:
            logger.warning(f"Failed to generate safer alternatives: {str(e)}")
            return []
    
    def _create_legal_citations_from_context(self, context: Dict[str, Any]) -> List[LegalCitation]:
        """Create LegalCitation objects from jurisdiction context."""
        citations = []
        
        # Add statute citations
        for statute in context.get("statutes", [])[:3]:
            citation = LegalCitation(
                statute=statute.get("title", ""),
                description=statute.get("description", ""),
                url=statute.get("url"),
                jurisdiction=context.get("jurisdiction", "US"),
                relevance=statute.get("relevance_score", 0.5)
            )
            citations.append(citation)
        
        # Add regulation citations
        for regulation in context.get("regulations", [])[:2]:
            citation = LegalCitation(
                statute=regulation.get("title", ""),
                description=regulation.get("description", ""),
                url=regulation.get("url"),
                jurisdiction=context.get("jurisdiction", "US"),
                relevance=regulation.get("relevance_score", 0.5)
            )
            citations.append(citation)
        
        return citations
    
    def _calculate_context_confidence(
        self, 
        statutes: List[Dict], 
        regulations: List[Dict], 
        precedents: List[Dict]
    ) -> float:
        """Calculate confidence score for jurisdiction context."""
        total_items = len(statutes) + len(regulations) + len(precedents)
        
        if total_items == 0:
            return 0.1
        elif total_items < 3:
            return 0.4
        elif total_items < 6:
            return 0.7
        else:
            return 0.9
    
    async def get_jurisdiction_conflicts(
        self, 
        primary_jurisdiction: str, 
        secondary_jurisdictions: List[str],
        legal_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify conflicts between multiple jurisdictions.
        
        Args:
            primary_jurisdiction: Primary jurisdiction
            secondary_jurisdictions: List of other applicable jurisdictions
            legal_area: Specific legal area to focus on
            
        Returns:
            Dictionary containing conflict analysis
        """
        try:
            logger.info(f"Analyzing jurisdiction conflicts: {primary_jurisdiction} vs {secondary_jurisdictions}")
            
            # Get context for all jurisdictions
            primary_context = await self.get_jurisdiction_context(primary_jurisdiction, legal_area)
            
            secondary_contexts = []
            for jurisdiction in secondary_jurisdictions:
                context = await self.get_jurisdiction_context(jurisdiction, legal_area)
                secondary_contexts.append(context)
            
            # Analyze conflicts using AI
            conflicts = await self._analyze_jurisdiction_conflicts_with_ai(
                primary_context, secondary_contexts, legal_area
            )
            
            return {
                "primary_jurisdiction": primary_jurisdiction,
                "secondary_jurisdictions": secondary_jurisdictions,
                "legal_area": legal_area,
                "conflicts": conflicts,
                "recommendations": self._generate_conflict_recommendations(conflicts),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Jurisdiction conflict analysis failed: {str(e)}")
            raise AnalysisError(f"Conflict analysis failed: {str(e)}") from e
    
    async def _analyze_jurisdiction_conflicts_with_ai(
        self, 
        primary_context: Dict[str, Any], 
        secondary_contexts: List[Dict[str, Any]],
        legal_area: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Use AI to analyze jurisdiction conflicts."""
        try:
            # Prepare context summary
            context_summary = f"Primary: {primary_context['jurisdiction_full_name']}\n"
            context_summary += f"Summary: {primary_context.get('summary', 'No summary available')}\n\n"
            
            for i, context in enumerate(secondary_contexts):
                context_summary += f"Secondary {i+1}: {context['jurisdiction_full_name']}\n"
                context_summary += f"Summary: {context.get('summary', 'No summary available')}\n\n"
            
            prompt = f"""
            Analyze potential legal conflicts between these jurisdictions for {legal_area or 'general contract'} matters:

            {context_summary}

            Identify potential conflicts and provide analysis in JSON format:
            {{
                "conflicts": [
                    {{
                        "type": "conflict type",
                        "description": "description of the conflict",
                        "severity": "low|medium|high",
                        "affected_areas": ["list", "of", "affected", "areas"],
                        "resolution_approach": "suggested approach"
                    }}
                ]
            }}

            Focus on practical conflicts that would affect contract enforceability or compliance.
            Return only the JSON, no other text.
            """
            
            response = await self.gemini_model.generate_content_async(prompt)
            
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result.get("conflicts", [])
            except (json.JSONDecodeError, ValueError):
                pass
            
            return []
            
        except Exception as e:
            logger.warning(f"AI conflict analysis failed: {str(e)}")
            return []
    
    def _generate_conflict_recommendations(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for handling jurisdiction conflicts."""
        recommendations = []
        
        if not conflicts:
            recommendations.append("No significant jurisdiction conflicts identified.")
            return recommendations
        
        high_severity_conflicts = [c for c in conflicts if c.get("severity") == "high"]
        if high_severity_conflicts:
            recommendations.append("Consult with legal counsel in all applicable jurisdictions due to high-severity conflicts.")
        
        choice_of_law_conflicts = [c for c in conflicts if "choice of law" in c.get("type", "").lower()]
        if choice_of_law_conflicts:
            recommendations.append("Include explicit choice of law and forum selection clauses.")
        
        enforcement_conflicts = [c for c in conflicts if "enforcement" in c.get("type", "").lower()]
        if enforcement_conflicts:
            recommendations.append("Consider alternative dispute resolution mechanisms.")
        
        if len(conflicts) > 2:
            recommendations.append("Consider simplifying the jurisdictional scope to reduce complexity.")
        
        return recommendations