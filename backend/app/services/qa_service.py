"""
Q&A Service for voice-to-voice legal document interactions.

This service handles:
- Question understanding and context retrieval
- Gemini-powered response generation with grounding
- Voice-to-voice interaction pipeline
- Context management and conversation history
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Part
from vertexai.language_models import TextEmbeddingModel

from ..core.config import get_settings
from ..core.exceptions import WorkflowError
from ..services.speech_to_text import speech_to_text_service, TranscriptionResult
from ..services.text_to_speech import text_to_speech_service, SynthesisResult
from ..services.vector_search import VectorSearchService
from ..services.firestore import FirestoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class QAContext:
    """Represents the context for a Q&A session."""
    
    def __init__(
        self,
        document_id: str,
        user_id: str,
        session_id: str,
        document_content: str = "",
        document_analysis: Dict[str, Any] = None,
        conversation_history: List[Dict[str, Any]] = None
    ):
        self.document_id = document_id
        self.user_id = user_id
        self.session_id = session_id
        self.document_content = document_content
        self.document_analysis = document_analysis or {}
        self.conversation_history = conversation_history or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_interaction(self, question: str, answer: str, confidence: float = 1.0):
        """Add a Q&A interaction to the conversation history."""
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "answer": answer,
            "confidence": confidence,
        }
        self.conversation_history.append(interaction)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_id": self.document_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "document_content": self.document_content,
            "document_analysis": self.document_analysis,
            "conversation_history": self.conversation_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class QAResponse:
    """Represents a Q&A response."""
    
    def __init__(
        self,
        question: str,
        answer: str,
        confidence: float,
        sources: List[Dict[str, Any]] = None,
        audio_response: Optional[SynthesisResult] = None,
        processing_time: float = 0.0,
        context_used: List[str] = None
    ):
        self.question = question
        self.answer = answer
        self.confidence = confidence
        self.sources = sources or []
        self.audio_response = audio_response
        self.processing_time = processing_time
        self.context_used = context_used or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "audio_response": self.audio_response.to_dict() if self.audio_response else None,
            "processing_time": self.processing_time,
            "context_used": self.context_used,
            "created_at": self.created_at.isoformat(),
        }


class QAService:
    """
    Service for handling voice-to-voice Q&A interactions with legal documents.
    
    Provides question understanding, context retrieval, response generation,
    and audio synthesis for natural voice interactions.
    """
    
    def __init__(self):
        """Initialize the Q&A service."""
        try:
            # Initialize AI models
            self.generative_model = GenerativeModel("gemini-1.5-pro")
            self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
            
            # Initialize services
            self.vector_search = VectorSearchService()
            self.firestore_service = FirestoreService()
            
            # Active Q&A contexts
            self.active_contexts: Dict[str, QAContext] = {}
            
            logger.info("Q&A service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Q&A service: {str(e)}")
            raise WorkflowError(f"Q&A service initialization failed: {str(e)}") from e
    
    async def process_voice_question(
        self,
        audio_data: bytes,
        document_id: str,
        user_id: str,
        session_id: Optional[str] = None,
        language_code: str = "en-US",
        voice_settings: Dict[str, Any] = None
    ) -> QAResponse:
        """
        Process a voice question and return a voice response.
        
        Args:
            audio_data: Audio data containing the question
            document_id: ID of the document to query about
            user_id: ID of the user asking the question
            session_id: Optional session ID for conversation continuity
            language_code: Language code for speech processing
            voice_settings: Settings for voice synthesis
            
        Returns:
            QAResponse with text and audio response
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Transcribe the voice question
            logger.info("Transcribing voice question...")
            audio_file = await self._create_temp_audio_file(audio_data)
            
            transcription = await speech_to_text_service.transcribe_audio_file(
                audio_data=audio_data,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="latest_short"
            )
            
            question = transcription.transcript.strip()
            if not question:
                raise WorkflowError("Could not transcribe the question")
            
            logger.info(f"Transcribed question: {question}")
            
            # Step 2: Process the text question
            response = await self.process_text_question(
                question=question,
                document_id=document_id,
                user_id=user_id,
                session_id=session_id
            )
            
            # Step 3: Synthesize the response to audio
            logger.info("Synthesizing audio response...")
            voice_settings = voice_settings or {}
            
            audio_response = await text_to_speech_service.synthesize_text(
                text=response.answer,
                language_code=language_code,
                voice_gender=voice_settings.get("voice_gender", "NEUTRAL"),
                voice_name=voice_settings.get("voice_name"),
                speaking_rate=voice_settings.get("speaking_rate", 1.0),
                pitch=voice_settings.get("pitch", 0.0),
                audio_format=voice_settings.get("audio_format", "MP3")
            )
            
            # Update response with audio
            response.audio_response = audio_response
            response.processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Voice Q&A completed in {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Voice Q&A processing error: {str(e)}")
            raise WorkflowError(f"Voice Q&A processing failed: {str(e)}") from e
    
    async def process_text_question(
        self,
        question: str,
        document_id: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> QAResponse:
        """
        Process a text question and return a text response.
        
        Args:
            question: The question to answer
            document_id: ID of the document to query about
            user_id: ID of the user asking the question
            session_id: Optional session ID for conversation continuity
            
        Returns:
            QAResponse with text response
        """
        start_time = datetime.utcnow()
        
        try:
            # Get or create Q&A context
            context = await self._get_or_create_context(
                document_id, user_id, session_id
            )
            
            # Step 1: Understand the question and extract intent
            question_analysis = await self._analyze_question(question, context)
            
            # Step 2: Retrieve relevant context from document
            relevant_context = await self._retrieve_relevant_context(
                question, question_analysis, context
            )
            
            # Step 3: Generate response using Gemini
            response_text, confidence, sources = await self._generate_response(
                question, relevant_context, context
            )
            
            # Step 4: Update conversation history
            context.add_interaction(question, response_text, confidence)
            await self._save_context(context)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = QAResponse(
                question=question,
                answer=response_text,
                confidence=confidence,
                sources=sources,
                processing_time=processing_time,
                context_used=relevant_context
            )
            
            logger.info(f"Text Q&A completed in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Text Q&A processing error: {str(e)}")
            raise WorkflowError(f"Text Q&A processing failed: {str(e)}") from e
    
    async def _analyze_question(
        self,
        question: str,
        context: QAContext
    ) -> Dict[str, Any]:
        """Analyze the question to understand intent and extract key information."""
        
        prompt = f"""
        Analyze this legal document question and extract key information:
        
        Question: "{question}"
        
        Document type: Legal document
        Previous conversation: {json.dumps(context.conversation_history[-3:], indent=2) if context.conversation_history else "None"}
        
        Please analyze and return a JSON response with:
        1. intent: The main intent (e.g., "clarification", "risk_assessment", "definition", "obligation", "deadline")
        2. key_terms: Important legal terms or concepts mentioned
        3. question_type: Type of question (e.g., "what", "when", "why", "how", "who")
        4. context_needed: What type of document context is needed
        5. urgency: How urgent/important this question seems (1-5 scale)
        
        Return only valid JSON.
        """
        
        try:
            response = await self.generative_model.generate_content_async(prompt)
            analysis = json.loads(response.text.strip())
            return analysis
            
        except Exception as e:
            logger.warning(f"Question analysis failed: {str(e)}")
            # Return default analysis
            return {
                "intent": "general_inquiry",
                "key_terms": [],
                "question_type": "general",
                "context_needed": "full_document",
                "urgency": 3
            }
    
    async def _retrieve_relevant_context(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        context: QAContext
    ) -> List[str]:
        """Retrieve relevant context from the document based on the question."""
        
        relevant_context = []
        
        try:
            # Use vector search to find relevant document sections
            if context.document_content:
                # Generate embedding for the question
                question_embedding = await self._generate_embedding(question)
                
                # Search for similar content in the document
                # This is a simplified implementation - in practice, you'd use
                # the vector search service with pre-indexed document chunks
                document_chunks = self._chunk_document(context.document_content)
                
                # For now, use simple keyword matching as fallback
                key_terms = question_analysis.get("key_terms", [])
                for chunk in document_chunks:
                    if any(term.lower() in chunk.lower() for term in key_terms):
                        relevant_context.append(chunk)
                
                # Limit context size
                relevant_context = relevant_context[:5]
            
            # Add document analysis context if available
            if context.document_analysis:
                analysis_context = self._extract_analysis_context(
                    question_analysis, context.document_analysis
                )
                relevant_context.extend(analysis_context)
            
            return relevant_context
            
        except Exception as e:
            logger.warning(f"Context retrieval failed: {str(e)}")
            # Return basic document content as fallback
            return [context.document_content[:2000]] if context.document_content else []
    
    async def _generate_response(
        self,
        question: str,
        relevant_context: List[str],
        qa_context: QAContext
    ) -> Tuple[str, float, List[Dict[str, Any]]]:
        """Generate a response using Gemini with grounding."""
        
        # Build the prompt with context
        context_text = "\n\n".join(relevant_context) if relevant_context else "No specific context available."
        
        conversation_history = ""
        if qa_context.conversation_history:
            recent_history = qa_context.conversation_history[-3:]  # Last 3 interactions
            history_items = []
            for interaction in recent_history:
                history_items.append(f"Q: {interaction['question']}")
                history_items.append(f"A: {interaction['answer']}")
            conversation_history = "\n".join(history_items)
        
        prompt = f"""
        You are a helpful legal AI assistant that answers questions about legal documents in plain language.
        
        CONTEXT FROM DOCUMENT:
        {context_text}
        
        PREVIOUS CONVERSATION:
        {conversation_history}
        
        CURRENT QUESTION: {question}
        
        INSTRUCTIONS:
        1. Answer the question based on the provided document context
        2. Use plain language that a non-lawyer can understand
        3. If the document doesn't contain enough information, say so clearly
        4. Provide specific references to relevant clauses when possible
        5. If this relates to risks, explain them clearly
        6. Keep the response concise but complete
        7. If you're uncertain, express that uncertainty
        
        IMPORTANT: Only answer based on the provided document context. Do not provide general legal advice.
        
        Response:
        """
        
        try:
            response = await self.generative_model.generate_content_async(prompt)
            response_text = response.text.strip()
            
            # Estimate confidence based on response characteristics
            confidence = self._estimate_response_confidence(response_text, relevant_context)
            
            # Extract sources (simplified)
            sources = [{"type": "document_section", "content": ctx[:200] + "..."} 
                      for ctx in relevant_context[:3]]
            
            return response_text, confidence, sources
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return (
                "I apologize, but I'm having trouble processing your question right now. Please try again.",
                0.1,
                []
            )
    
    def _estimate_response_confidence(
        self,
        response_text: str,
        context: List[str]
    ) -> float:
        """Estimate confidence in the response based on various factors."""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence if response references specific context
        if any(ctx_phrase in response_text.lower() for ctx in context 
               for ctx_phrase in ctx.lower().split()[:10]):
            confidence += 0.2
        
        # Decrease confidence if response indicates uncertainty
        uncertainty_phrases = [
            "i'm not sure", "unclear", "might be", "possibly", 
            "it appears", "seems like", "i don't have enough information"
        ]
        if any(phrase in response_text.lower() for phrase in uncertainty_phrases):
            confidence -= 0.2
        
        # Increase confidence if response is detailed
        if len(response_text.split()) > 50:
            confidence += 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _chunk_document(self, document_content: str, chunk_size: int = 500) -> List[str]:
        """Split document into chunks for context retrieval."""
        
        # Simple sentence-based chunking
        sentences = document_content.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_analysis_context(
        self,
        question_analysis: Dict[str, Any],
        document_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract relevant context from document analysis based on question."""
        
        context = []
        intent = question_analysis.get("intent", "")
        
        # Add relevant analysis based on intent
        if intent == "risk_assessment" and "risks" in document_analysis:
            risks = document_analysis["risks"]
            context.append(f"Risk Analysis: {json.dumps(risks, indent=2)}")
        
        if intent == "definition" and "clauses" in document_analysis:
            clauses = document_analysis["clauses"]
            context.append(f"Clause Analysis: {json.dumps(clauses, indent=2)}")
        
        if "summary" in document_analysis:
            context.append(f"Document Summary: {document_analysis['summary']}")
        
        return context
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Vertex AI."""
        try:
            embeddings = await self.embedding_model.get_embeddings_async([text])
            return embeddings[0].values
        except Exception as e:
            logger.warning(f"Embedding generation failed: {str(e)}")
            return []
    
    async def _get_or_create_context(
        self,
        document_id: str,
        user_id: str,
        session_id: Optional[str]
    ) -> QAContext:
        """Get existing Q&A context or create a new one."""
        
        if not session_id:
            session_id = f"{user_id}_{document_id}_{datetime.utcnow().timestamp()}"
        
        context_key = f"{user_id}_{document_id}_{session_id}"
        
        # Check if context exists in memory
        if context_key in self.active_contexts:
            return self.active_contexts[context_key]
        
        # Try to load from Firestore
        try:
            doc_ref = self.firestore_service.db.collection("qa_contexts").document(context_key)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                context = QAContext(
                    document_id=data["document_id"],
                    user_id=data["user_id"],
                    session_id=data["session_id"],
                    document_content=data.get("document_content", ""),
                    document_analysis=data.get("document_analysis", {}),
                    conversation_history=data.get("conversation_history", [])
                )
                self.active_contexts[context_key] = context
                return context
        except Exception as e:
            logger.warning(f"Failed to load context from Firestore: {str(e)}")
        
        # Create new context
        # In practice, you'd load document content and analysis from the database
        context = QAContext(
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            document_content="",  # Would be loaded from document storage
            document_analysis={}   # Would be loaded from analysis results
        )
        
        self.active_contexts[context_key] = context
        return context
    
    async def _save_context(self, context: QAContext):
        """Save Q&A context to Firestore."""
        try:
            context_key = f"{context.user_id}_{context.document_id}_{context.session_id}"
            doc_ref = self.firestore_service.db.collection("qa_contexts").document(context_key)
            doc_ref.set(context.to_dict())
        except Exception as e:
            logger.warning(f"Failed to save context to Firestore: {str(e)}")
    
    async def _create_temp_audio_file(self, audio_data: bytes) -> str:
        """Create a temporary audio file from audio data."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_data)
            return temp_file.name
    
    async def get_session_history(
        self,
        document_id: str,
        user_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            context = await self._get_or_create_context(document_id, user_id, session_id)
            return context.conversation_history
        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            return []
    
    async def clear_session(
        self,
        document_id: str,
        user_id: str,
        session_id: str
    ):
        """Clear a Q&A session."""
        try:
            context_key = f"{user_id}_{document_id}_{session_id}"
            
            # Remove from memory
            if context_key in self.active_contexts:
                del self.active_contexts[context_key]
            
            # Remove from Firestore
            doc_ref = self.firestore_service.db.collection("qa_contexts").document(context_key)
            doc_ref.delete()
            
        except Exception as e:
            logger.error(f"Failed to clear session: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Q&A service."""
        try:
            # Test basic functionality
            test_question = "What is this document about?"
            test_context = QAContext("test", "test", "test", "This is a test document.")
            
            # Test question analysis
            analysis = await self._analyze_question(test_question, test_context)
            
            return {
                "status": "healthy",
                "service": "qa_service",
                "timestamp": datetime.utcnow().isoformat(),
                "test_completed": True,
                "active_contexts": len(self.active_contexts),
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "qa_service",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# Global service instance
qa_service = QAService()