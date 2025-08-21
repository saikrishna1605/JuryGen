"""
Summarizer Agent for converting legal documents to plain language summaries.

This agent handles:
- Gemini 1.5 Pro integration for document summarization
- Reading level control and tone adjustment features
- Structured summary generation with clause preservation
- Key points extraction and obligation identification
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import vertexai
from vertexai.generative_models import GenerativeModel
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..models.document import DocumentSummary, Clause
from ..models.base import ReadingLevel, RiskLevel, UserRole
from ..core.exceptions import AnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


class SummarizerAgent:
    """
    Specialized agent for converting legal documents to plain language summaries.
    
    Uses Gemini 1.5 Pro for sophisticated document summarization with
    reading level control and structured output.
    """
    
    def __init__(self):
        """Initialize the Summarizer Agent."""
        # Initialize Vertex AI
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        
        # Initialize Gemini Pro model for complex summarization
        self.pro_model = GenerativeModel(settings.GEMINI_MODEL_PRO)
        
        # Reading level guidelines
        self.reading_level_guidelines = {
            ReadingLevel.ELEMENTARY: {
                "target_grade": "5th grade",
                "sentence_length": "short (10-15 words)",
                "vocabulary": "simple, everyday words",
                "complexity": "very simple concepts only"
            },
            ReadingLevel.MIDDLE: {
                "target_grade": "8th grade", 
                "sentence_length": "moderate (15-20 words)",
                "vocabulary": "common words with some technical terms explained",
                "complexity": "moderate concepts with explanations"
            },
            ReadingLevel.HIGH: {
                "target_grade": "12th grade",
                "sentence_length": "varied (15-25 words)",
                "vocabulary": "standard vocabulary with technical terms",
                "complexity": "complex concepts explained clearly"
            },
            ReadingLevel.COLLEGE: {
                "target_grade": "college level",
                "sentence_length": "varied and complex",
                "vocabulary": "advanced vocabulary and technical terms",
                "complexity": "sophisticated concepts and analysis"
            }
        }
        
        # Document type patterns for classification
        self.document_type_patterns = {
            "lease": ["lease", "rental", "tenant", "landlord", "rent"],
            "employment": ["employment", "employee", "employer", "job", "work"],
            "loan": ["loan", "borrow", "lender", "credit", "mortgage"],
            "purchase": ["purchase", "buy", "sell", "sale", "buyer", "seller"],
            "service": ["service", "provider", "client", "contractor"],
            "partnership": ["partnership", "partner", "joint venture"],
            "license": ["license", "licensing", "intellectual property"],
            "nda": ["non-disclosure", "confidentiality", "proprietary"],
            "terms_of_service": ["terms of service", "user agreement", "website"],
            "privacy_policy": ["privacy", "data", "personal information"]
        }
    
    async def create_summary(
        self,
        document_text: str,
        clauses: List[Clause],
        user_role: Optional[UserRole] = None,
        reading_level: ReadingLevel = ReadingLevel.MIDDLE,
        tone: str = "neutral",
        jurisdiction: Optional[str] = None
    ) -> DocumentSummary:
        """
        Create a comprehensive plain language summary of a legal document.
        
        Args:
            document_text: Full document text
            clauses: List of analyzed clauses
            user_role: User's role for perspective
            reading_level: Target reading level
            tone: Desired tone (neutral, friendly, formal)
            jurisdiction: Legal jurisdiction for context
            
        Returns:
            DocumentSummary with plain language content
            
        Raises:
            AnalysisError: If summarization fails
        """
        try:
            logger.info(f"Creating summary at {reading_level} level with {tone} tone")
            
            # Analyze document structure and type
            document_type = self._classify_document_type(document_text)
            main_parties = self._extract_main_parties(document_text)
            
            # Generate the main summary
            summary_text = await self._generate_main_summary(
                document_text, clauses, user_role, reading_level, tone, jurisdiction
            )
            
            # Extract key points and obligations
            key_points = await self._extract_key_points(
                document_text, clauses, user_role, reading_level
            )
            
            # Calculate summary metrics
            word_count = len(summary_text.split())
            reading_time = max(1, word_count // 200)  # Assume 200 words per minute
            
            # Assess document complexity
            complexity = self._assess_document_complexity(clauses)
            
            # Determine overall tone
            overall_tone = self._analyze_document_tone(document_text, clauses)
            
            # Create DocumentSummary object
            summary = DocumentSummary(
                plain_language=summary_text,
                key_points=key_points,
                reading_level=reading_level,
                word_count=word_count,
                estimated_reading_time=reading_time,
                overall_tone=overall_tone,
                complexity=complexity,
                main_parties=main_parties,
                document_type=document_type
            )
            
            logger.info(f"Successfully created summary: {word_count} words, {reading_time} min read")
            return summary
            
        except Exception as e:
            logger.error(f"Summary creation failed: {str(e)}")
            raise AnalysisError(f"Failed to create summary: {str(e)}") from e
    
    async def _generate_main_summary(
        self,
        document_text: str,
        clauses: List[Clause],
        user_role: Optional[UserRole],
        reading_level: ReadingLevel,
        tone: str,
        jurisdiction: Optional[str]
    ) -> str:
        """Generate the main plain language summary."""
        
        # Build comprehensive prompt
        prompt = self._build_summary_prompt(
            document_text, clauses, user_role, reading_level, tone, jurisdiction
        )
        
        try:
            # Generate summary using Gemini Pro
            response = await self.pro_model.generate_content_async(prompt)
            
            # Clean and validate the response
            summary_text = self._clean_summary_text(response.text)
            
            # Validate reading level
            if not self._validate_reading_level(summary_text, reading_level):
                logger.warning("Summary may not meet target reading level")
            
            return summary_text
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            # Return a basic fallback summary
            return self._create_fallback_summary(document_text, clauses)
    
    def _build_summary_prompt(
        self,
        document_text: str,
        clauses: List[Clause],
        user_role: Optional[UserRole],
        reading_level: ReadingLevel,
        tone: str,
        jurisdiction: Optional[str]
    ) -> str:
        """Build the prompt for summary generation."""
        
        # Get reading level guidelines
        level_guide = self.reading_level_guidelines[reading_level]
        
        # Build role context
        role_context = f" from the perspective of a {user_role.value}" if user_role else ""
        jurisdiction_context = f" in {jurisdiction}" if jurisdiction else ""
        
        # Analyze clause risks for context
        high_risk_clauses = [c for c in clauses if c.risk_score > 0.7]
        medium_risk_clauses = [c for c in clauses if 0.3 < c.risk_score <= 0.7]
        
        # Build clause context
        clause_context = ""
        if high_risk_clauses:
            clause_context += f"\nHigh-risk clauses identified: {len(high_risk_clauses)}"
        if medium_risk_clauses:
            clause_context += f"\nMedium-risk clauses identified: {len(medium_risk_clauses)}"
        
        prompt = f"""
You are a legal expert who specializes in explaining complex legal documents in plain language. 
Your task is to create a comprehensive summary of the following legal document{role_context}{jurisdiction_context}.

WRITING GUIDELINES:
- Target reading level: {level_guide['target_grade']}
- Sentence length: {level_guide['sentence_length']}
- Vocabulary: {level_guide['vocabulary']}
- Complexity: {level_guide['complexity']}
- Tone: {tone}

DOCUMENT ANALYSIS CONTEXT:{clause_context}

REQUIREMENTS:
1. Start with a brief overview of what this document is and its main purpose
2. Explain the key obligations and rights for each party
3. Highlight important deadlines, payments, or conditions
4. Explain any significant risks or benefits
5. Use bullet points or numbered lists for clarity
6. Define any technical terms that must be used
7. Focus on practical implications and what it means in everyday terms

DOCUMENT TEXT:
{document_text[:6000]}  # Limit to avoid token limits

Create a comprehensive but accessible summary that helps someone understand what they're agreeing to.
"""
        
        return prompt
    
    def _clean_summary_text(self, raw_text: str) -> str:
        """Clean and format the generated summary text."""
        # Remove any markdown formatting that might interfere
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_text)  # Remove bold
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)  # Remove italic
        
        # Ensure proper paragraph spacing
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _validate_reading_level(self, text: str, target_level: ReadingLevel) -> bool:
        """Validate if text meets the target reading level (simplified check)."""
        sentences = re.split(r'[.!?]+', text)
        
        # Calculate average sentence length
        total_words = sum(len(sentence.split()) for sentence in sentences if sentence.strip())
        avg_sentence_length = total_words / len([s for s in sentences if s.strip()]) if sentences else 0
        
        # Simple validation based on sentence length
        if target_level == ReadingLevel.ELEMENTARY and avg_sentence_length > 20:
            return False
        elif target_level == ReadingLevel.MIDDLE and avg_sentence_length > 25:
            return False
        elif target_level == ReadingLevel.HIGH and avg_sentence_length > 30:
            return False
        
        return True
    
    def _create_fallback_summary(self, document_text: str, clauses: List[Clause]) -> str:
        """Create a basic fallback summary when AI generation fails."""
        doc_type = self._classify_document_type(document_text)
        
        summary_parts = [
            f"This appears to be a {doc_type or 'legal'} document.",
            f"The document contains {len(clauses)} main clauses or sections.",
        ]
        
        # Add risk information
        high_risk = len([c for c in clauses if c.risk_score > 0.7])
        if high_risk > 0:
            summary_parts.append(f"There are {high_risk} clauses that may require careful attention.")
        
        summary_parts.append("Please review the full document carefully and consider consulting with a legal professional.")
        
        return " ".join(summary_parts)
    
    async def _extract_key_points(
        self,
        document_text: str,
        clauses: List[Clause],
        user_role: Optional[UserRole],
        reading_level: ReadingLevel
    ) -> List[str]:
        """Extract key points and obligations from the document."""
        
        # Build prompt for key points extraction
        prompt = self._build_key_points_prompt(document_text, clauses, user_role, reading_level)
        
        try:
            response = await self.pro_model.generate_content_async(prompt)
            
            # Parse the response to extract key points
            key_points = self._parse_key_points_response(response.text)
            
            return key_points
            
        except Exception as e:
            logger.warning(f"Key points extraction failed: {str(e)}")
            # Return fallback key points based on clause analysis
            return self._create_fallback_key_points(clauses)
    
    def _build_key_points_prompt(
        self,
        document_text: str,
        clauses: List[Clause],
        user_role: Optional[UserRole],
        reading_level: ReadingLevel
    ) -> str:
        """Build prompt for key points extraction."""
        
        role_context = f" for a {user_role.value}" if user_role else ""
        level_guide = self.reading_level_guidelines[reading_level]
        
        return f"""
Extract the most important key points from this legal document{role_context}.

WRITING GUIDELINES:
- Use {level_guide['vocabulary']}
- Keep explanations at {level_guide['target_grade']} level
- Focus on practical implications

Focus on:
1. Main obligations and responsibilities
2. Important deadlines and dates
3. Payment terms and amounts
4. Rights and benefits
5. Termination conditions
6. Key restrictions or limitations
7. Important definitions or terms

Return as a JSON array of strings, where each string is a clear, concise key point.
Example: ["You must pay rent by the 1st of each month", "The landlord must provide 24-hour notice before entering"]

DOCUMENT TEXT:
{document_text[:4000]}

Return only the JSON array, no other text.
"""
    
    def _parse_key_points_response(self, response_text: str) -> List[str]:
        """Parse key points from AI response."""
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                key_points = json.loads(json_match.group())
                # Validate that all items are strings
                return [str(point) for point in key_points if isinstance(point, str)]
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse key points response: {str(e)}")
            # Try to extract bullet points or numbered lists
            return self._extract_key_points_fallback(response_text)
    
    def _extract_key_points_fallback(self, text: str) -> List[str]:
        """Fallback method to extract key points from text."""
        key_points = []
        
        # Look for bullet points or numbered lists
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Match bullet points or numbered items
            if re.match(r'^[-*•]\s+', line) or re.match(r'^\d+\.\s+', line):
                # Clean the line
                cleaned = re.sub(r'^[-*•\d.]\s+', '', line)
                if cleaned and len(cleaned) > 10:  # Ensure substantial content
                    key_points.append(cleaned)
        
        return key_points[:10]  # Limit to top 10 points
    
    def _create_fallback_key_points(self, clauses: List[Clause]) -> List[str]:
        """Create fallback key points based on clause analysis."""
        key_points = []
        
        # Add points based on high-risk clauses
        high_risk_clauses = [c for c in clauses if c.risk_score > 0.7]
        for clause in high_risk_clauses[:3]:  # Top 3 high-risk clauses
            key_points.append(f"Important clause requires attention: {clause.text[:100]}...")
        
        # Add points based on clause categories
        categories = {}
        for clause in clauses:
            if clause.category:
                if clause.category not in categories:
                    categories[clause.category] = []
                categories[clause.category].append(clause)
        
        # Add category-based points
        for category, category_clauses in categories.items():
            if category == "payment":
                key_points.append("This document includes payment obligations")
            elif category == "termination":
                key_points.append("This document includes termination conditions")
            elif category == "liability":
                key_points.append("This document includes liability provisions")
        
        return key_points[:8]  # Limit to 8 points
    
    def _classify_document_type(self, document_text: str) -> Optional[str]:
        """Classify the type of legal document."""
        text_lower = document_text.lower()
        
        # Score each document type based on keyword matches
        type_scores = {}
        for doc_type, keywords in self.document_type_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[doc_type] = score
        
        # Return the highest scoring type
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return None
    
    def _extract_main_parties(self, document_text: str) -> List[str]:
        """Extract the main parties involved in the document."""
        parties = []
        
        # Common patterns for party identification
        party_patterns = [
            r'between\s+([^,\n]+)\s+and\s+([^,\n]+)',
            r'party\s+of\s+the\s+first\s+part[:\s]+([^,\n]+)',
            r'party\s+of\s+the\s+second\s+part[:\s]+([^,\n]+)',
            r'landlord[:\s]+([^,\n]+)',
            r'tenant[:\s]+([^,\n]+)',
            r'employer[:\s]+([^,\n]+)',
            r'employee[:\s]+([^,\n]+)',
            r'lender[:\s]+([^,\n]+)',
            r'borrower[:\s]+([^,\n]+)'
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, document_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    parties.extend([m.strip() for m in match])
                else:
                    parties.append(match.strip())
        
        # Clean and deduplicate parties
        cleaned_parties = []
        for party in parties:
            # Remove common legal phrases
            party = re.sub(r'\s*\([^)]*\)\s*', '', party)  # Remove parenthetical
            party = party.strip(' ,"')
            
            if party and len(party) > 2 and party not in cleaned_parties:
                cleaned_parties.append(party)
        
        return cleaned_parties[:4]  # Limit to 4 main parties
    
    def _assess_document_complexity(self, clauses: List[Clause]) -> RiskLevel:
        """Assess the overall complexity of the document."""
        if not clauses:
            return RiskLevel.LOW
        
        # Calculate complexity based on various factors
        avg_risk_score = sum(clause.risk_score for clause in clauses) / len(clauses)
        high_risk_count = len([c for c in clauses if c.risk_score > 0.7])
        total_clauses = len(clauses)
        
        # Complexity scoring
        complexity_score = 0
        
        # Factor 1: Average risk score
        complexity_score += avg_risk_score * 40
        
        # Factor 2: Proportion of high-risk clauses
        if total_clauses > 0:
            high_risk_ratio = high_risk_count / total_clauses
            complexity_score += high_risk_ratio * 30
        
        # Factor 3: Total number of clauses
        if total_clauses > 20:
            complexity_score += 20
        elif total_clauses > 10:
            complexity_score += 10
        
        # Factor 4: Variety of clause categories
        categories = set(clause.category for clause in clauses if clause.category)
        if len(categories) > 5:
            complexity_score += 10
        
        # Determine complexity level
        if complexity_score >= 70:
            return RiskLevel.HIGH
        elif complexity_score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _analyze_document_tone(self, document_text: str, clauses: List[Clause]) -> str:
        """Analyze the overall tone of the document."""
        text_lower = document_text.lower()
        
        # Tone indicators
        formal_indicators = ['whereas', 'heretofore', 'aforementioned', 'pursuant to', 'notwithstanding']
        friendly_indicators = ['agree', 'mutual', 'cooperation', 'partnership', 'understanding']
        strict_indicators = ['shall', 'must', 'required', 'mandatory', 'penalty', 'breach', 'default']
        
        # Count indicators
        formal_count = sum(1 for indicator in formal_indicators if indicator in text_lower)
        friendly_count = sum(1 for indicator in friendly_indicators if indicator in text_lower)
        strict_count = sum(1 for indicator in strict_indicators if indicator in text_lower)
        
        # Determine tone based on counts and risk levels
        avg_risk = sum(clause.risk_score for clause in clauses) / len(clauses) if clauses else 0
        
        if strict_count > formal_count and strict_count > friendly_count:
            return "strict"
        elif friendly_count > formal_count and avg_risk < 0.4:
            return "collaborative"
        elif formal_count > 0 or avg_risk > 0.6:
            return "formal"
        else:
            return "neutral"
    
    async def adjust_summary_tone(
        self,
        original_summary: DocumentSummary,
        new_tone: str,
        new_reading_level: Optional[ReadingLevel] = None
    ) -> DocumentSummary:
        """
        Adjust the tone and/or reading level of an existing summary.
        
        Args:
            original_summary: The original summary to adjust
            new_tone: New tone to apply
            new_reading_level: New reading level (optional)
            
        Returns:
            Adjusted DocumentSummary
        """
        try:
            target_level = new_reading_level or original_summary.reading_level
            level_guide = self.reading_level_guidelines[target_level]
            
            prompt = f"""
Rewrite the following legal document summary with a {new_tone} tone at a {level_guide['target_grade']} reading level.

ORIGINAL SUMMARY:
{original_summary.plain_language}

ORIGINAL KEY POINTS:
{chr(10).join(f"- {point}" for point in original_summary.key_points)}

REQUIREMENTS:
- Maintain all factual information
- Use {level_guide['vocabulary']}
- Keep sentences {level_guide['sentence_length']}
- Apply a {new_tone} tone throughout
- Preserve the structure and key points

Return the rewritten summary as plain text.
"""
            
            response = await self.pro_model.generate_content_async(prompt)
            adjusted_text = self._clean_summary_text(response.text)
            
            # Create new summary with adjusted content
            adjusted_summary = DocumentSummary(
                plain_language=adjusted_text,
                key_points=original_summary.key_points,  # Keep original key points
                reading_level=target_level,
                word_count=len(adjusted_text.split()),
                estimated_reading_time=max(1, len(adjusted_text.split()) // 200),
                overall_tone=new_tone,
                complexity=original_summary.complexity,
                main_parties=original_summary.main_parties,
                document_type=original_summary.document_type
            )
            
            return adjusted_summary
            
        except Exception as e:
            logger.error(f"Summary tone adjustment failed: {str(e)}")
            # Return original summary if adjustment fails
            return original_summary