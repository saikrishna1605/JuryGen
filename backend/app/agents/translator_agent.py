"""
Translator Agent for multilingual legal document output.

This agent handles:
- Translation of summaries, risk assessments, and Q&A responses
- Language-specific formatting and cultural adaptation
- Translation caching and optimization
- Legal terminology consistency across languages
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

try:
    from crewai import Agent, Task, Crew
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create dummy classes for type hints
    class Agent:
        pass
    class Task:
        pass
    class Crew:
        pass
    class BaseTool:
        pass

from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.exceptions import WorkflowError
from ..services.translation_service import translation_service, TranslationResult
from ..services.text_to_speech import text_to_speech_service

logger = logging.getLogger(__name__)
settings = get_settings()


class TranslationTask(BaseModel):
    """Represents a translation task."""
    
    task_id: str
    content_type: str  # 'summary', 'risk_assessment', 'qa_response', 'clause_analysis'
    source_content: str
    source_language: str
    target_languages: List[str]
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=5)
    preserve_legal_terms: bool = Field(default=True)
    cultural_adaptation: bool = Field(default=True)
    generate_audio: bool = Field(default=False)


class TranslationOutput(BaseModel):
    """Represents the output of a translation task."""
    
    task_id: str
    translations: Dict[str, Any]
    audio_outputs: Dict[str, Any] = Field(default_factory=dict)
    legal_term_glossary: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    cultural_notes: Dict[str, List[str]] = Field(default_factory=dict)
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LegalTerminologyTool(BaseTool if CREWAI_AVAILABLE else object):
    """Tool for handling legal terminology translations."""
    
    name: str = "legal_terminology_tool"
    description: str = "Translate legal terms with consistency and accuracy"
    
    def __init__(self):
        if CREWAI_AVAILABLE:
            super().__init__()
        # Legal term dictionary for consistent translations
        self.legal_terms = {
            "en": {
                "contract": {"es": "contrato", "fr": "contrat", "de": "Vertrag", "it": "contratto"},
                "liability": {"es": "responsabilidad", "fr": "responsabilité", "de": "Haftung", "it": "responsabilità"},
                "breach": {"es": "incumplimiento", "fr": "violation", "de": "Verletzung", "it": "violazione"},
                "termination": {"es": "terminación", "fr": "résiliation", "de": "Kündigung", "it": "risoluzione"},
                "indemnification": {"es": "indemnización", "fr": "indemnisation", "de": "Entschädigung", "it": "indennizzo"},
                "warranty": {"es": "garantía", "fr": "garantie", "de": "Gewährleistung", "it": "garanzia"},
                "jurisdiction": {"es": "jurisdicción", "fr": "juridiction", "de": "Gerichtsbarkeit", "it": "giurisdizione"},
                "arbitration": {"es": "arbitraje", "fr": "arbitrage", "de": "Schiedsverfahren", "it": "arbitrato"},
                "force majeure": {"es": "fuerza mayor", "fr": "force majeure", "de": "höhere Gewalt", "it": "forza maggiore"},
                "confidentiality": {"es": "confidencialidad", "fr": "confidentialité", "de": "Vertraulichkeit", "it": "riservatezza"},
            }
        }
    
    def _run(self, term: str, source_lang: str, target_lang: str) -> str:
        """Translate a legal term with consistency."""
        try:
            if source_lang in self.legal_terms:
                term_lower = term.lower()
                if term_lower in self.legal_terms[source_lang]:
                    translations = self.legal_terms[source_lang][term_lower]
                    if target_lang in translations:
                        return translations[target_lang]
            
            # Fallback to original term if no translation found
            return term
            
        except Exception as e:
            logger.warning(f"Legal term translation failed: {str(e)}")
            return term


class CulturalAdaptationTool(BaseTool if CREWAI_AVAILABLE else object):
    """Tool for cultural adaptation of legal content."""
    
    name: str = "cultural_adaptation_tool"
    description: str = "Adapt legal content for cultural and regional differences"
    
    def _run(self, content: str, target_language: str, content_type: str) -> Dict[str, Any]:
        """Adapt content for cultural differences."""
        try:
            adaptations = {
                "content": content,
                "cultural_notes": [],
                "formatting_changes": [],
            }
            
            # Language-specific adaptations
            if target_language == "ar":
                adaptations["cultural_notes"].append("Text direction: Right-to-left")
                adaptations["formatting_changes"].append("rtl_text")
            
            if target_language in ["ja", "ko", "zh"]:
                adaptations["cultural_notes"].append("Consider hierarchical language structures")
                adaptations["formatting_changes"].append("formal_tone")
            
            if target_language in ["es", "pt"]:
                adaptations["cultural_notes"].append("Consider regional variations (Spain vs Latin America)")
            
            if target_language == "de":
                adaptations["cultural_notes"].append("German legal system differences may apply")
                adaptations["formatting_changes"].append("compound_words")
            
            if target_language == "fr":
                adaptations["cultural_notes"].append("Consider French vs Canadian French legal terminology")
            
            # Content type specific adaptations
            if content_type == "risk_assessment":
                adaptations["cultural_notes"].append("Risk perception may vary by culture")
            
            if content_type == "summary":
                adaptations["cultural_notes"].append("Summary style preferences may vary")
            
            return adaptations
            
        except Exception as e:
            logger.warning(f"Cultural adaptation failed: {str(e)}")
            return {"content": content, "cultural_notes": [], "formatting_changes": []}


class TranslatorAgent:
    """
    Translator Agent for multilingual legal document output.
    
    Handles translation of legal content with cultural adaptation,
    terminology consistency, and quality optimization.
    """
    
    def __init__(self):
        """Initialize the Translator Agent."""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available - Translator Agent functionality limited")
            self.agent = None
            self.legal_terminology_tool = None
            self.cultural_adaptation_tool = None
            self.translation_cache: Dict[str, Dict[str, str]] = {}
            return
            
        try:
            # Initialize tools
            self.legal_terminology_tool = LegalTerminologyTool()
            self.cultural_adaptation_tool = CulturalAdaptationTool()
            
            # Initialize CrewAI agent
            self.agent = Agent(
                role="Legal Document Translator",
                goal="Translate legal documents accurately while preserving meaning and adapting for cultural differences",
                backstory="""You are an expert legal translator with deep knowledge of legal systems 
                across multiple jurisdictions. You specialize in translating complex legal documents 
                while maintaining accuracy, consistency, and cultural appropriateness. You understand 
                that legal translation requires not just linguistic skills but also legal knowledge 
                and cultural sensitivity.""",
                tools=[self.legal_terminology_tool, self.cultural_adaptation_tool],
                verbose=True,
                allow_delegation=False
            )
            
            # Translation cache for consistency
            self.translation_cache: Dict[str, Dict[str, str]] = {}
            
            logger.info("Translator Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Translator Agent: {str(e)}")
            raise WorkflowError(f"Translator Agent initialization failed: {str(e)}") from e
    
    async def translate_content(self, task: TranslationTask) -> TranslationOutput:
        """
        Translate content for multiple target languages.
        
        Args:
            task: Translation task with content and target languages
            
        Returns:
            TranslationOutput with translations and metadata
        """
        if not CREWAI_AVAILABLE:
            raise WorkflowError("CrewAI not available - translation functionality disabled")
            
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting translation task {task.task_id} for {len(task.target_languages)} languages")
            
            translations = {}
            audio_outputs = {}
            legal_term_glossary = {}
            cultural_notes = {}
            quality_scores = {}
            
            # Process each target language
            for target_lang in task.target_languages:
                try:
                    # Perform translation
                    translation_result = await self._translate_single_language(
                        task, target_lang
                    )
                    translations[target_lang] = translation_result
                    quality_scores[target_lang] = translation_result.quality_score
                    
                    # Extract legal terms for glossary
                    if task.preserve_legal_terms:
                        glossary = await self._extract_legal_terms(
                            task.source_content, translation_result.translated_text,
                            task.source_language, target_lang
                        )
                        legal_term_glossary[target_lang] = glossary
                    
                    # Cultural adaptation
                    if task.cultural_adaptation:
                        cultural_adaptation = self.cultural_adaptation_tool._run(
                            translation_result.translated_text, target_lang, task.content_type
                        )
                        cultural_notes[target_lang] = cultural_adaptation["cultural_notes"]
                    
                    # Generate audio if requested
                    if task.generate_audio:
                        audio_output = await self._generate_audio_output(
                            translation_result.translated_text, target_lang
                        )
                        audio_outputs[target_lang] = audio_output
                    
                except Exception as e:
                    logger.error(f"Translation failed for language {target_lang}: {str(e)}")
                    # Continue with other languages
                    continue
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            output = TranslationOutput(
                task_id=task.task_id,
                translations=translations,
                audio_outputs=audio_outputs,
                legal_term_glossary=legal_term_glossary,
                cultural_notes=cultural_notes,
                quality_scores=quality_scores,
                processing_time=processing_time
            )
            
            logger.info(f"Translation task {task.task_id} completed in {processing_time:.2f}s")
            return output
            
        except Exception as e:
            logger.error(f"Translation task {task.task_id} failed: {str(e)}")
            raise WorkflowError(f"Translation task failed: {str(e)}") from e
    
    async def translate_document_analysis(
        self,
        analysis_results: Dict[str, Any],
        target_languages: List[str],
        source_language: str = "en"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Translate complete document analysis results.
        
        Args:
            analysis_results: Complete analysis results from other agents
            target_languages: List of target language codes
            source_language: Source language code
            
        Returns:
            Dictionary of translated analysis results by language
        """
        try:
            translated_results = {}
            
            for target_lang in target_languages:
                translated_analysis = {}
                
                # Translate summary
                if "summary" in analysis_results:
                    summary_task = TranslationTask(
                        task_id=f"summary_{target_lang}",
                        content_type="summary",
                        source_content=analysis_results["summary"],
                        source_language=source_language,
                        target_languages=[target_lang],
                        preserve_legal_terms=True,
                        cultural_adaptation=True
                    )
                    summary_output = await self.translate_content(summary_task)
                    translated_analysis["summary"] = summary_output.translations[target_lang].translated_text
                
                # Translate risk assessment
                if "risk_assessment" in analysis_results:
                    risk_content = self._format_risk_assessment_for_translation(
                        analysis_results["risk_assessment"]
                    )
                    risk_task = TranslationTask(
                        task_id=f"risk_{target_lang}",
                        content_type="risk_assessment",
                        source_content=risk_content,
                        source_language=source_language,
                        target_languages=[target_lang],
                        preserve_legal_terms=True,
                        cultural_adaptation=True
                    )
                    risk_output = await self.translate_content(risk_task)
                    translated_analysis["risk_assessment"] = self._parse_translated_risk_assessment(
                        risk_output.translations[target_lang].translated_text
                    )
                
                # Translate clause analysis
                if "clauses" in analysis_results:
                    translated_clauses = []
                    for clause in analysis_results["clauses"]:
                        clause_task = TranslationTask(
                            task_id=f"clause_{clause.get('id', 'unknown')}_{target_lang}",
                            content_type="clause_analysis",
                            source_content=clause.get("text", ""),
                            source_language=source_language,
                            target_languages=[target_lang],
                            preserve_legal_terms=True,
                            cultural_adaptation=False  # Keep clause structure intact
                        )
                        clause_output = await self.translate_content(clause_task)
                        
                        translated_clause = clause.copy()
                        translated_clause["text"] = clause_output.translations[target_lang].translated_text
                        translated_clauses.append(translated_clause)
                    
                    translated_analysis["clauses"] = translated_clauses
                
                translated_results[target_lang] = translated_analysis
            
            return translated_results
            
        except Exception as e:
            logger.error(f"Document analysis translation failed: {str(e)}")
            raise WorkflowError(f"Document analysis translation failed: {str(e)}") from e
    
    async def _translate_single_language(
        self,
        task: TranslationTask,
        target_language: str
    ) -> TranslationResult:
        """Translate content to a single target language."""
        
        # Check cache first
        cache_key = f"{hash(task.source_content)}_{task.source_language}_{target_language}"
        if cache_key in self.translation_cache:
            cached_translation = self.translation_cache[cache_key]
            return TranslationResult(
                original_text=task.source_content,
                translated_text=cached_translation["text"],
                source_language=task.source_language,
                target_language=target_language,
                confidence=cached_translation["confidence"],
                quality_score=cached_translation["quality"],
                processing_time=0.0,
                cached=True
            )
        
        # Perform translation using translation service
        result = await translation_service.translate_text(
            text=task.source_content,
            target_language=target_language,
            source_language=task.source_language,
            use_cache=True,
            quality_threshold=0.8  # Higher threshold for legal content
        )
        
        # Post-process for legal terminology consistency
        if task.preserve_legal_terms:
            result.translated_text = await self._ensure_legal_terminology_consistency(
                result.translated_text, task.source_language, target_language
            )
        
        # Cache the result
        self.translation_cache[cache_key] = {
            "text": result.translated_text,
            "confidence": result.confidence,
            "quality": result.quality_score
        }
        
        return result
    
    async def _ensure_legal_terminology_consistency(
        self,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """Ensure legal terminology consistency in translated text."""
        
        # This would implement more sophisticated legal term consistency checking
        # For now, return the text as-is
        return translated_text
    
    async def _extract_legal_terms(
        self,
        source_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, str]:
        """Extract legal terms and their translations for glossary."""
        
        glossary = {}
        
        # Simple implementation - would be more sophisticated in practice
        legal_terms = [
            "contract", "agreement", "liability", "breach", "termination",
            "indemnification", "warranty", "jurisdiction", "arbitration",
            "force majeure", "confidentiality", "damages", "penalty"
        ]
        
        for term in legal_terms:
            if term.lower() in source_text.lower():
                translated_term = self.legal_terminology_tool._run(
                    term, source_language, target_language
                )
                glossary[term] = translated_term
        
        return glossary
    
    async def _generate_audio_output(
        self,
        text: str,
        language: str
    ) -> Dict[str, Any]:
        """Generate audio output for translated text."""
        
        try:
            # Map language codes to TTS language codes
            tts_language_map = {
                "es": "es-ES",
                "fr": "fr-FR",
                "de": "de-DE",
                "it": "it-IT",
                "pt": "pt-PT",
                "ru": "ru-RU",
                "ja": "ja-JP",
                "ko": "ko-KR",
                "zh": "zh-CN",
                "ar": "ar-SA",
                "hi": "hi-IN",
            }
            
            tts_language = tts_language_map.get(language, "en-US")
            
            # Generate audio
            audio_result = await text_to_speech_service.synthesize_text(
                text=text,
                language_code=tts_language,
                voice_gender="NEUTRAL",
                audio_format="MP3"
            )
            
            return {
                "audio_content_base64": audio_result.to_dict()["audio_content_base64"],
                "language_code": tts_language,
                "duration": audio_result.duration,
                "voice_name": audio_result.voice_name
            }
            
        except Exception as e:
            logger.warning(f"Audio generation failed for language {language}: {str(e)}")
            return {}
    
    def _format_risk_assessment_for_translation(self, risk_assessment: Dict[str, Any]) -> str:
        """Format risk assessment data for translation."""
        
        formatted_text = "Risk Assessment:\n\n"
        
        if "overall_risk_level" in risk_assessment:
            formatted_text += f"Overall Risk Level: {risk_assessment['overall_risk_level']}\n\n"
        
        if "risks" in risk_assessment:
            formatted_text += "Identified Risks:\n"
            for i, risk in enumerate(risk_assessment["risks"], 1):
                formatted_text += f"{i}. {risk.get('description', '')}\n"
                formatted_text += f"   Risk Level: {risk.get('level', 'Unknown')}\n"
                formatted_text += f"   Impact: {risk.get('impact', 'Unknown')}\n\n"
        
        if "recommendations" in risk_assessment:
            formatted_text += "Recommendations:\n"
            for i, rec in enumerate(risk_assessment["recommendations"], 1):
                formatted_text += f"{i}. {rec}\n"
        
        return formatted_text
    
    def _parse_translated_risk_assessment(self, translated_text: str) -> Dict[str, Any]:
        """Parse translated risk assessment text back to structured format."""
        
        # This would implement parsing logic to convert translated text
        # back to structured risk assessment format
        # For now, return a simple structure
        
        return {
            "translated_content": translated_text,
            "structure_preserved": True
        }
    
    async def get_translation_quality_report(
        self,
        translations: Dict[str, TranslationResult]
    ) -> Dict[str, Any]:
        """Generate a quality report for translations."""
        
        try:
            total_translations = len(translations)
            if total_translations == 0:
                return {"error": "No translations to analyze"}
            
            quality_scores = [t.quality_score for t in translations.values()]
            processing_times = [t.processing_time for t in translations.values()]
            cached_count = sum(1 for t in translations.values() if t.cached)
            
            report = {
                "total_translations": total_translations,
                "average_quality_score": sum(quality_scores) / len(quality_scores),
                "min_quality_score": min(quality_scores),
                "max_quality_score": max(quality_scores),
                "average_processing_time": sum(processing_times) / len(processing_times),
                "cache_hit_rate": cached_count / total_translations,
                "languages_translated": list(translations.keys()),
                "quality_distribution": {
                    "excellent": sum(1 for s in quality_scores if s >= 0.9),
                    "good": sum(1 for s in quality_scores if 0.8 <= s < 0.9),
                    "fair": sum(1 for s in quality_scores if 0.7 <= s < 0.8),
                    "poor": sum(1 for s in quality_scores if s < 0.7),
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Quality report generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Translator Agent."""
        
        try:
            # Test translation with a simple legal text
            test_task = TranslationTask(
                task_id="health_check",
                content_type="summary",
                source_content="This is a legal contract with terms and conditions.",
                source_language="en",
                target_languages=["es"],
                preserve_legal_terms=True,
                cultural_adaptation=False
            )
            
            result = await self.translate_content(test_task)
            
            return {
                "status": "healthy",
                "agent": "translator_agent",
                "timestamp": datetime.utcnow().isoformat(),
                "test_completed": True,
                "test_translation_quality": result.quality_scores.get("es", 0.0),
                "cache_size": len(self.translation_cache),
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": "translator_agent",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# Global agent instance
translator_agent = TranslatorAgent()