"""
AI Agent Service with Murf TTS, AssemblyAI transcription, and Gemini text generation.
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64
import tempfile

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI not available. Install with: pip install google-generativeai")


class AgentService:
    """AI Agent service integrating multiple AI services."""
    
    def __init__(self):
        # Initialize API keys
        self.murf_api_key = os.getenv("MURF_API_KEY")
        self.assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            self.gemini_enabled = True
        else:
            self.gemini_model = None
            self.gemini_enabled = False
        
        # Service URLs
        self.murf_base_url = "https://api.murf.ai/v1"
        self.assemblyai_base_url = "https://api.assemblyai.com/v2"
        
        print(f"Agent Service initialized:")
        print(f"  Murf TTS: {'✅' if self.murf_api_key else '❌'}")
        print(f"  AssemblyAI: {'✅' if self.assemblyai_api_key else '❌'}")
        print(f"  Gemini: {'✅' if self.gemini_enabled else '❌'}")
    
    async def transcribe_audio(self, audio_data: bytes, audio_format: str = "wav") -> Dict[str, Any]:
        """
        Transcribe audio using AssemblyAI.
        
        Args:
            audio_data: Audio file bytes
            audio_format: Audio format (wav, mp3, etc.)
            
        Returns:
            Transcription result with text and confidence
        """
        if not self.assemblyai_api_key:
            return {
                "success": False,
                "error": "AssemblyAI API key not configured",
                "text": "Mock transcription: What are the key terms in this legal document?"
            }
        
        try:
            headers = {
                "authorization": self.assemblyai_api_key,
                "content-type": "application/json"
            }
            
            # Step 1: Upload audio file
            upload_url = f"{self.assemblyai_base_url}/upload"
            
            async with aiohttp.ClientSession() as session:
                # Upload audio
                async with session.post(
                    upload_url,
                    headers={"authorization": self.assemblyai_api_key},
                    data=audio_data
                ) as upload_response:
                    if upload_response.status != 200:
                        raise Exception(f"Upload failed: {upload_response.status}")
                    
                    upload_result = await upload_response.json()
                    audio_url = upload_result["upload_url"]
                
                # Step 2: Request transcription
                transcript_request = {
                    "audio_url": audio_url,
                    "language_detection": True,
                    "punctuate": True,
                    "format_text": True
                }
                
                async with session.post(
                    f"{self.assemblyai_base_url}/transcript",
                    headers=headers,
                    json=transcript_request
                ) as transcript_response:
                    if transcript_response.status != 200:
                        raise Exception(f"Transcription request failed: {transcript_response.status}")
                    
                    transcript_result = await transcript_response.json()
                    transcript_id = transcript_result["id"]
                
                # Step 3: Poll for completion
                max_attempts = 60  # 5 minutes max
                for attempt in range(max_attempts):
                    async with session.get(
                        f"{self.assemblyai_base_url}/transcript/{transcript_id}",
                        headers=headers
                    ) as status_response:
                        if status_response.status != 200:
                            raise Exception(f"Status check failed: {status_response.status}")
                        
                        status_result = await status_response.json()
                        
                        if status_result["status"] == "completed":
                            return {
                                "success": True,
                                "text": status_result["text"],
                                "confidence": status_result.get("confidence", 0.9),
                                "language": status_result.get("language_code", "en"),
                                "duration": status_result.get("audio_duration", 0)
                            }
                        elif status_result["status"] == "error":
                            raise Exception(f"Transcription failed: {status_result.get('error', 'Unknown error')}")
                        
                        # Wait before next poll
                        await asyncio.sleep(5)
                
                raise Exception("Transcription timeout")
                
        except Exception as e:
            print(f"AssemblyAI transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "Mock transcription: What are the main clauses in this contract?"
            }
    
    async def generate_text(self, prompt: str, context: str = "", max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate text using Gemini.
        
        Args:
            prompt: The prompt for text generation
            context: Additional context (document content, etc.)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        if not self.gemini_enabled:
            return {
                "success": False,
                "error": "Gemini API not configured",
                "text": f"Mock response to: {prompt}"
            }
        
        try:
            # Construct full prompt with context
            full_prompt = f"""
You are a legal AI assistant. Analyze the following legal document and answer the user's question.

Document Context:
{context}

User Question: {prompt}

Please provide a clear, accurate, and helpful response based on the document content. If the document doesn't contain relevant information, say so clearly.

Response:"""
            
            # Generate response
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                full_prompt
            )
            
            generated_text = response.text
            
            return {
                "success": True,
                "text": generated_text,
                "model": "gemini-1.5-flash",
                "tokens_used": len(generated_text.split())
            }
            
        except Exception as e:
            print(f"Gemini generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": f"I understand you're asking about: {prompt}. Based on typical legal documents, here's what you should know..."
            }
    
    async def text_to_speech(self, text: str, voice_id: str = "en-US-davis", speed: float = 1.0) -> Dict[str, Any]:
        """
        Convert text to speech using Murf AI.
        
        Args:
            text: Text to convert to speech
            voice_id: Murf voice ID
            speed: Speech speed (0.5 to 2.0)
            
        Returns:
            Audio data and metadata
        """
        if not self.murf_api_key:
            return {
                "success": False,
                "error": "Murf API key not configured",
                "audio_url": None
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.murf_api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare TTS request
            tts_request = {
                "voiceId": voice_id,
                "text": text,
                "speed": speed,
                "format": "mp3",
                "sampleRate": 22050
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.murf_base_url}/speech/generate",
                    headers=headers,
                    json=tts_request
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Murf API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    return {
                        "success": True,
                        "audio_url": result.get("audioUrl"),
                        "audio_data": result.get("audioData"),
                        "duration": result.get("duration", 0),
                        "voice_id": voice_id,
                        "format": "mp3"
                    }
                    
        except Exception as e:
            print(f"Murf TTS error: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_url": None
            }
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get available Murf voices."""
        if not self.murf_api_key:
            return {
                "success": False,
                "error": "Murf API key not configured",
                "voices": []
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.murf_api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.murf_base_url}/voices",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get voices: {response.status}")
                    
                    voices = await response.json()
                    
                    return {
                        "success": True,
                        "voices": voices
                    }
                    
        except Exception as e:
            print(f"Error getting Murf voices: {e}")
            return {
                "success": False,
                "error": str(e),
                "voices": [
                    {"id": "en-US-davis", "name": "Davis", "language": "en-US", "gender": "male"},
                    {"id": "en-US-sarah", "name": "Sarah", "language": "en-US", "gender": "female"}
                ]
            }
    
    async def process_voice_question(self, audio_data: bytes, document_content: str = "") -> Dict[str, Any]:
        """
        Complete voice processing pipeline: transcribe -> generate -> speak.
        
        Args:
            audio_data: Input audio bytes
            document_content: Document context for answering
            
        Returns:
            Complete response with transcription, answer, and audio
        """
        try:
            # Step 1: Transcribe audio
            print("🎤 Transcribing audio...")
            transcription = await self.transcribe_audio(audio_data)
            
            if not transcription["success"]:
                return {
                    "success": False,
                    "error": f"Transcription failed: {transcription['error']}",
                    "step": "transcription"
                }
            
            question_text = transcription["text"]
            print(f"📝 Transcribed: {question_text}")
            
            # Step 2: Generate answer
            print("🤖 Generating answer...")
            answer = await self.generate_text(question_text, document_content)
            
            if not answer["success"]:
                return {
                    "success": False,
                    "error": f"Text generation failed: {answer['error']}",
                    "step": "generation",
                    "question": question_text
                }
            
            answer_text = answer["text"]
            print(f"💬 Generated answer: {answer_text[:100]}...")
            
            # Step 3: Convert answer to speech
            print("🔊 Converting to speech...")
            speech = await self.text_to_speech(answer_text)
            
            return {
                "success": True,
                "question": question_text,
                "answer": answer_text,
                "transcription_confidence": transcription.get("confidence", 0.9),
                "audio_url": speech.get("audio_url"),
                "audio_data": speech.get("audio_data"),
                "processing_time": datetime.utcnow().isoformat(),
                "services_used": {
                    "transcription": "AssemblyAI",
                    "generation": "Gemini",
                    "tts": "Murf"
                }
            }
            
        except Exception as e:
            print(f"Voice processing pipeline error: {e}")
            return {
                "success": False,
                "error": str(e),
                "step": "pipeline"
            }

# Global agent service instance
agent_service = AgentService()