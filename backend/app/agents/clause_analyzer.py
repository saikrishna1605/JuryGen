"""
Clause Analyzer Agent for legal document clause classification and risk assessment.

This agent handles:
- Gemini 1.5 Flash integration for clause classification
- Role-specific analysis prompts and response parsing
- Clause risk scoring algorithms (0-100 scale)
- Legal clause categorization and keyword extraction
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
import re

import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..models.document import Clause, ClauseClassification, RoleAnalysis, SaferAlternative, LegalCitation
from ..models.base import UserRole, RiskLevel
from ..core.exceptions import AnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


class ClauseAnalyzerAgent:
    """
    Specialized agent for legal clause analysis and risk assessment.
    
    Uses Gemini 1.5 Flash for efficient clause classification and 
    role-specific risk analysis.
    """
    
    def __init__(self):
        """Initialize the Clause Analyzer Agent."""
        # Initialize Vertex AI
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        
        # Initialize Gemini Flash model for classification
        self.flash_model = GenerativeModel(settings.GEMINI_MODEL_FLASH)
        
        # Clause categories for classification
        self.clause_categories = {
            "payment": ["payment", "fee", "cost", "price", "billing", "invoice"],
            "termination": ["terminate", "end", "cancel", "expire", "dissolution"],
            "liability": ["liable", "responsibility", "damages", "indemnify", "fault"],
            "confidentiality": ["confidential", "non-disclosure", "proprietary", "secret"],
            "intellectual_property": ["copyright", "trademark", "patent", "ip", "intellectual"],
            "dispute_resolution": ["dispute", "arbitration", "mediation", "court", "litigation"],
            "force_majeure": ["force majeure", "act of god", "unforeseeable", "beyond control"],
            "modification": ["modify", "amend", "change", "alter", "update"],
            "governing_law": ["governing law", "jurisdiction", "applicable law", "venue"],
            "warranties": ["warrant", "guarantee", "represent", "assure", "promise"]
        }
        
    async def analyze_clauses(
        self, 
        document_text: str, 
        user_role: UserRole,
        jurisdiction: Optional[str] = None
    ) -> List[Clause]:
        """
        Analyze document text and extract classified clauses.
        
        Args:
            document_text: Full document text
            user_role: User's role for role-specific analysis
            jurisdiction: Legal jurisdiction for context
            
        Returns:
            List of analyzed clauses with classifications and risk scores
            
        Raises:
            AnalysisError: If clause analysis fails
        """
        try:
            logger.info(f"Starting clause analysis for role: {user_role}")
            
            # Step 1: Extract individual clauses from document
            clause_segments = await self._extract_clause_segments(document_text)
            
            # Step 2: Analyze each clause
            analyzed_clauses = []
            for i, segment in enumerate(clause_segments):
                try:
                    clause = await self._analyze_single_clause(
                        segment, user_role, jurisdiction, i + 1
                    )
                    analyzed_clauses.append(clause)
                except Exception as e:
                    logger.warning(f"Failed to analyze clause {i + 1}: {str(e)}")
                    # Continue with other clauses
                    continue
            
            logger.info(f"Successfully analyzed {len(analyzed_clauses)} clauses")
            return analyzed_clauses
            
        except Exception as e:
            logger.error(f"Clause analysis failed: {str(e)}")
            raise AnalysisError(f"Failed to analyze clauses: {str(e)}") from e
    
    async def _extract_clause_segments(self, document_text: str) -> List[Dict]:
        """
        Extract individual clause segments from document text.
        
        Args:
            document_text: Full document text
            
        Returns:
            List of clause segments with text and metadata
        """
        # Use Gemini to intelligently segment the document into clauses
        prompt = self._build_segmentation_prompt(document_text)
        
        try:
            response = await self.flash_model.generate_content_async(prompt)
            
            # Parse the response to extract clause segments
            segments = self._parse_segmentation_response(response.text)
            
            return segments
            
        except Exception as e:
            logger.warning(f"AI segmentation failed, using fallback: {str(e)}")
            # Fallback to simple paragraph-based segmentation
            return self._fallback_segmentation(document_text)
    
    def _build_segmentation_prompt(self, document_text: str) -> str:
        """Build prompt for document segmentation."""
        return f"""
You are a legal document analysis expert. Your task is to segment the following legal document into individual clauses or provisions.

For each clause, identify:
1. The clause text
2. Any clause number or identifier (if present)
3. A brief description of what the clause covers

Return the result as a JSON array where each element has:
- "text": the full clause text
- "clause_number": the clause identifier (or null if none)
- "description": brief description of the clause purpose

Document text:
{document_text[:8000]}  # Limit to avoid token limits

Return only the JSON array, no other text.
"""
    
    def _parse_segmentation_response(self, response_text: str) -> List[Dict]:
        """Parse AI segmentation response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                segments_data = json.loads(json_match.group())
                return segments_data
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse segmentation response: {str(e)}")
            return []
    
    def _fallback_segmentation(self, document_text: str) -> List[Dict]:
        """Fallback segmentation using simple text processing."""
        # Split by common clause indicators
        clause_patterns = [
            r'\n\s*\d+\.\s+',  # Numbered clauses
            r'\n\s*\([a-z]\)\s+',  # Lettered subclauses
            r'\n\s*[A-Z][A-Z\s]+:\s*',  # All caps headers
            r'\n\s*WHEREAS\s+',  # Whereas clauses
            r'\n\s*NOW THEREFORE\s+',  # Therefore clauses
        ]
        
        segments = []
        current_text = document_text
        
        # Simple paragraph-based splitting as fallback
        paragraphs = [p.strip() for p in current_text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50:  # Only consider substantial paragraphs
                segments.append({
                    "text": paragraph,
                    "clause_number": None,
                    "description": f"Paragraph {i + 1}"
                })
        
        return segments
    
    async def _analyze_single_clause(
        self, 
        clause_segment: Dict, 
        user_role: UserRole, 
        jurisdiction: Optional[str],
        clause_index: int
    ) -> Clause:
        """
        Analyze a single clause for risk and classification.
        
        Args:
            clause_segment: Clause text and metadata
            user_role: User's role for analysis
            jurisdiction: Legal jurisdiction
            clause_index: Index of the clause
            
        Returns:
            Analyzed Clause object
        """
        clause_text = clause_segment["text"]
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(clause_text, user_role, jurisdiction)
        
        try:
            # Get analysis from Gemini
            response = await self.flash_model.generate_content_async(prompt)
            
            # Parse the analysis response
            analysis_result = self._parse_analysis_response(response.text)
            
            # Determine clause category
            category = self._categorize_clause(clause_text)
            
            # Create Clause object
            clause = Clause(
                text=clause_text,
                clause_number=clause_segment.get("clause_number"),
                classification=ClauseClassification(analysis_result["classification"]),
                risk_score=analysis_result["risk_score"],
                impact_score=analysis_result["impact_score"],
                likelihood_score=analysis_result["likelihood_score"],
                role_analysis={
                    user_role: RoleAnalysis(
                        classification=ClauseClassification(analysis_result["classification"]),
                        rationale=analysis_result["rationale"],
                        risk_level=analysis_result["risk_score"],
                        recommendations=analysis_result.get("recommendations", []),
                        negotiation_points=analysis_result.get("negotiation_points", [])
                    )
                },
                safer_alternatives=self._create_safer_alternatives(analysis_result.get("safer_alternatives", [])),
                legal_citations=self._create_legal_citations(analysis_result.get("legal_citations", [])),
                keywords=self._extract_keywords(clause_text),
                category=category
            )
            
            return clause
            
        except Exception as e:
            logger.error(f"Failed to analyze clause {clause_index}: {str(e)}")
            # Return a basic clause with minimal analysis
            return self._create_fallback_clause(clause_segment, clause_index)
    
    def _build_analysis_prompt(
        self, 
        clause_text: str, 
        user_role: UserRole, 
        jurisdiction: Optional[str]
    ) -> str:
        """Build analysis prompt for a single clause."""
        jurisdiction_context = f" in {jurisdiction}" if jurisdiction else ""
        
        return f"""
You are a legal expert analyzing contract clauses. Analyze the following clause from the perspective of a {user_role.value}{jurisdiction_context}.

Clause text:
"{clause_text}"

Provide your analysis in the following JSON format:
{{
    "classification": "beneficial|caution|risky",
    "risk_score": 0.0-1.0,
    "impact_score": 0-100,
    "likelihood_score": 0-100,
    "rationale": "explanation of the classification",
    "recommendations": ["list", "of", "recommendations"],
    "negotiation_points": ["key", "negotiation", "points"],
    "safer_alternatives": [
        {{
            "suggested_text": "safer clause wording",
            "rationale": "why this is safer",
            "confidence": 0.0-1.0
        }}
    ],
    "legal_citations": [
        {{
            "statute": "relevant law or regulation",
            "description": "how it applies",
            "jurisdiction": "applicable jurisdiction",
            "relevance": 0.0-1.0
        }}
    ]
}}

Classification guidelines:
- "beneficial": Clause clearly favors the {user_role.value} or is standard/fair
- "caution": Clause has some risks but is negotiable or common
- "risky": Clause significantly disadvantages the {user_role.value} or creates major liability

Risk scoring:
- risk_score: Overall risk level (0.0 = no risk, 1.0 = maximum risk)
- impact_score: Potential negative impact if risk materializes (0-100)
- likelihood_score: Probability of negative outcome (0-100)

Return only the JSON, no other text.
"""
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse the analysis response from Gemini."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                
                # Validate and normalize the response
                return self._validate_analysis_data(analysis_data)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse analysis response: {str(e)}")
            # Return default analysis
            return {
                "classification": "caution",
                "risk_score": 0.5,
                "impact_score": 50,
                "likelihood_score": 50,
                "rationale": "Analysis parsing failed, manual review recommended",
                "recommendations": ["Review this clause manually"],
                "negotiation_points": [],
                "safer_alternatives": [],
                "legal_citations": []
            }
    
    def _validate_analysis_data(self, data: Dict) -> Dict:
        """Validate and normalize analysis data."""
        # Ensure required fields exist with defaults
        validated = {
            "classification": data.get("classification", "caution"),
            "risk_score": max(0.0, min(1.0, float(data.get("risk_score", 0.5)))),
            "impact_score": max(0, min(100, int(data.get("impact_score", 50)))),
            "likelihood_score": max(0, min(100, int(data.get("likelihood_score", 50)))),
            "rationale": data.get("rationale", "No rationale provided"),
            "recommendations": data.get("recommendations", []),
            "negotiation_points": data.get("negotiation_points", []),
            "safer_alternatives": data.get("safer_alternatives", []),
            "legal_citations": data.get("legal_citations", [])
        }
        
        # Validate classification
        if validated["classification"] not in ["beneficial", "caution", "risky"]:
            validated["classification"] = "caution"
        
        return validated
    
    def _categorize_clause(self, clause_text: str) -> Optional[str]:
        """Categorize clause based on keywords."""
        clause_lower = clause_text.lower()
        
        for category, keywords in self.clause_categories.items():
            for keyword in keywords:
                if keyword in clause_lower:
                    return category
        
        return None
    
    def _extract_keywords(self, clause_text: str) -> List[str]:
        """Extract key legal terms from clause text."""
        # Common legal keywords to extract
        legal_terms = [
            "shall", "must", "may", "will", "agree", "covenant", "warrant",
            "represent", "indemnify", "liable", "damages", "breach", "default",
            "terminate", "cancel", "expire", "renew", "modify", "amend",
            "confidential", "proprietary", "intellectual property", "copyright",
            "trademark", "patent", "dispute", "arbitration", "mediation",
            "governing law", "jurisdiction", "venue", "force majeure"
        ]
        
        clause_lower = clause_text.lower()
        found_keywords = []
        
        for term in legal_terms:
            if term in clause_lower:
                found_keywords.append(term)
        
        return found_keywords[:10]  # Limit to top 10 keywords
    
    def _create_safer_alternatives(self, alternatives_data: List[Dict]) -> List[SaferAlternative]:
        """Create SaferAlternative objects from analysis data."""
        alternatives = []
        
        for alt_data in alternatives_data:
            try:
                alternative = SaferAlternative(
                    suggested_text=alt_data.get("suggested_text", ""),
                    rationale=alt_data.get("rationale", ""),
                    legal_basis=alt_data.get("legal_basis"),
                    confidence=max(0.0, min(1.0, float(alt_data.get("confidence", 0.7)))),
                    impact_reduction=max(0.0, min(1.0, float(alt_data.get("impact_reduction", 0.3))))
                )
                alternatives.append(alternative)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid safer alternative data: {str(e)}")
                continue
        
        return alternatives
    
    def _create_legal_citations(self, citations_data: List[Dict]) -> List[LegalCitation]:
        """Create LegalCitation objects from analysis data."""
        citations = []
        
        for citation_data in citations_data:
            try:
                citation = LegalCitation(
                    statute=citation_data.get("statute", ""),
                    description=citation_data.get("description", ""),
                    url=citation_data.get("url"),
                    jurisdiction=citation_data.get("jurisdiction", "US"),
                    relevance=max(0.0, min(1.0, float(citation_data.get("relevance", 0.5))))
                )
                citations.append(citation)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid legal citation data: {str(e)}")
                continue
        
        return citations
    
    def _create_fallback_clause(self, clause_segment: Dict, clause_index: int) -> Clause:
        """Create a basic clause when analysis fails."""
        return Clause(
            text=clause_segment["text"],
            clause_number=clause_segment.get("clause_number"),
            classification=ClauseClassification.CAUTION,
            risk_score=0.5,
            impact_score=50,
            likelihood_score=50,
            role_analysis={},
            safer_alternatives=[],
            legal_citations=[],
            keywords=[],
            category="unknown"
        )
    
    async def analyze_clause_batch(
        self, 
        clauses: List[str], 
        user_role: UserRole,
        jurisdiction: Optional[str] = None
    ) -> List[Clause]:
        """
        Analyze multiple clauses in batch for efficiency.
        
        Args:
            clauses: List of clause texts
            user_role: User's role for analysis
            jurisdiction: Legal jurisdiction
            
        Returns:
            List of analyzed Clause objects
        """
        try:
            # Process clauses in smaller batches to avoid token limits
            batch_size = 5
            all_results = []
            
            for i in range(0, len(clauses), batch_size):
                batch = clauses[i:i + batch_size]
                batch_results = await self._analyze_clause_batch_internal(
                    batch, user_role, jurisdiction, i
                )
                all_results.extend(batch_results)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Batch clause analysis failed: {str(e)}")
            raise AnalysisError(f"Failed to analyze clause batch: {str(e)}") from e
    
    async def _analyze_clause_batch_internal(
        self, 
        clause_batch: List[str], 
        user_role: UserRole,
        jurisdiction: Optional[str],
        start_index: int
    ) -> List[Clause]:
        """Internal method for batch analysis."""
        # Create tasks for concurrent processing
        tasks = []
        for i, clause_text in enumerate(clause_batch):
            clause_segment = {
                "text": clause_text,
                "clause_number": None,
                "description": f"Clause {start_index + i + 1}"
            }
            task = self._analyze_single_clause(
                clause_segment, user_role, jurisdiction, start_index + i + 1
            )
            tasks.append(task)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Clause {start_index + i + 1} analysis failed: {str(result)}")
                # Create fallback clause
                fallback = self._create_fallback_clause(
                    {"text": clause_batch[i], "clause_number": None}, 
                    start_index + i + 1
                )
                valid_results.append(fallback)
            else:
                valid_results.append(result)
        
        return valid_results