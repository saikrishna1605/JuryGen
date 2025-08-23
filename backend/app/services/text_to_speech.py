"""
Text-to-Speech service using Google Cloud Text-to-Speech API.

This service handles:
- Text synthesis to audio
- Voice selection and customization
- SSML support for advanced speech control
- Audio format optimization
- Batch processing for multiple texts
"""

import asyncio
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import io
import base64

from google.cloud import texttospeech
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..core.exceptions import WorkflowError

logger = logging.getLogger(__name__)
settings = get_settings()


class SynthesisResult:
    """Represents a text-to-speech synthesis result."""
    
    def __init__(
        self,
        audio_content: bytes,
        text: str,
        voice_name: str,
        language_code: str,
        audio_format: str,
        sample_rate: int,
        duration: float = 0.0,
        processing_time: float = 0.0,
        word_timestamps: List[Dict[str, Any]] = None
    ):
        self.audio_content = audio_content
        self.text = text
        self.voice_name = voice_name
        self.language_code = language_code
        self.audio_format = audio_format
        self.sample_rate = sample_rate
        self.duration = duration
        self.processing_time = processing_time
        self.word_timestamps = word_timestamps or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "audio_content_base64": base64.b64encode(self.audio_content).decode('utf-8'),
            "text": self.text,
            "voice_name": self.voice_name,
            "language_code": self.language_code,
            "audio_format": self.audio_format,
            "sample_rate": self.sample_rate,
            "duration": self.duration,
            "processing_time": self.processing_time,
            "word_timestamps": self.word_timestamps,
            "created_at": self.created_at.isoformat(),
        }
    
    def save_to_file(self, file_path: str) -> None:
        """Save audio content to file."""
        with open(file_path, 'wb') as f:
            f.write(self.audio_content)


class TextToSpeechService:
    """
    Service for converting text to speech using Google Cloud Text-to-Speech API.
    
    Provides high-quality speech synthesis with multiple voices,
    languages, and audio formats.
    """
    
    def __init__(self):
        """Initialize the Text-to-Speech service."""
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("Text-to-Speech service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Text-to-Speech service: {str(e)}")
            raise WorkflowError(f"Text-to-Speech service initialization failed: {str(e)}") from e
    
    async def synthesize_text(
        self,
        text: str,
        language_code: str = "en-US",
        voice_name: Optional[str] = None,
        voice_gender: str = "NEUTRAL",
        audio_format: str = "MP3",
        sample_rate: Optional[int] = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
        use_ssml: bool = False,
        enable_time_pointing: bool = False
    ) -> SynthesisResult:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            language_code: Language code (e.g., 'en-US', 'es-ES')
            voice_name: Specific voice name (auto-selected if None)
            voice_gender: Voice gender (MALE, FEMALE, NEUTRAL)
            audio_format: Output audio format (MP3, WAV, OGG)
            sample_rate: Audio sample rate (format default if None)
            speaking_rate: Speech rate (0.25 to 4.0)
            pitch: Voice pitch (-20.0 to 20.0 semitones)
            volume_gain_db: Volume gain (-96.0 to 16.0 dB)
            use_ssml: Whether text contains SSML markup
            enable_time_pointing: Enable word-level timestamps
            
        Returns:
            SynthesisResult with audio data and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare input text
            if use_ssml:
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice
            voice = await self._configure_voice(
                language_code, voice_name, voice_gender
            )
            
            # Configure audio
            audio_config = self._configure_audio(
                audio_format, sample_rate, speaking_rate, pitch, volume_gain_db
            )
            
            # Enable time pointing if requested
            if enable_time_pointing:
                audio_config.enable_time_pointing = [
                    texttospeech.SynthesisInput.TimePointingType.SSML_MARK
                ]
            
            # Perform synthesis
            logger.info(f"Synthesizing text: {text[:100]}...")
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.synthesize_speech,
                {
                    "input": synthesis_input,
                    "voice": voice,
                    "audio_config": audio_config,
                    "enable_time_pointing": enable_time_pointing,
                }
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Estimate duration (rough calculation)
            # Actual duration would require audio analysis
            estimated_duration = len(text.split()) * 0.6  # ~0.6 seconds per word
            
            # Extract word timestamps if available
            word_timestamps = []
            if hasattr(response, 'timepoints') and response.timepoints:
                for timepoint in response.timepoints:
                    word_timestamps.append({
                        "mark_name": timepoint.mark_name,
                        "time_seconds": timepoint.time_seconds,
                    })
            
            result = SynthesisResult(
                audio_content=response.audio_content,
                text=text,
                voice_name=voice.name or f"{language_code}-{voice_gender}",
                language_code=language_code,
                audio_format=audio_format.lower(),
                sample_rate=sample_rate or self._get_default_sample_rate(audio_format),
                duration=estimated_duration,
                processing_time=processing_time,
                word_timestamps=word_timestamps
            )
            
            logger.info(f"Text synthesis completed in {processing_time:.2f}s")
            return result
            
        except gcp_exceptions.GoogleAPIError as e:
            logger.error(f"Google Text-to-Speech API error: {str(e)}")
            raise WorkflowError(f"Text synthesis failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Text synthesis error: {str(e)}")
            raise WorkflowError(f"Text-to-speech synthesis failed: {str(e)}") from e
    
    async def synthesize_with_ssml(
        self,
        ssml_text: str,
        language_code: str = "en-US",
        voice_name: Optional[str] = None,
        **kwargs
    ) -> SynthesisResult:
        """
        Synthesize text with SSML markup for advanced speech control.
        
        Args:
            ssml_text: Text with SSML markup
            language_code: Language code
            voice_name: Specific voice name
            **kwargs: Additional synthesis parameters
            
        Returns:
            SynthesisResult with synthesized audio
        """
        return await self.synthesize_text(
            text=ssml_text,
            language_code=language_code,
            voice_name=voice_name,
            use_ssml=True,
            **kwargs
        )
    
    async def synthesize_batch(
        self,
        texts: List[str],
        language_code: str = "en-US",
        voice_name: Optional[str] = None,
        **kwargs
    ) -> List[SynthesisResult]:
        """
        Synthesize multiple texts in batch.
        
        Args:
            texts: List of texts to synthesize
            language_code: Language code
            voice_name: Specific voice name
            **kwargs: Additional synthesis parameters
            
        Returns:
            List of SynthesisResult objects
        """
        tasks = []
        for text in texts:
            task = self.synthesize_text(
                text=text,
                language_code=language_code,
                voice_name=voice_name,
                **kwargs
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to synthesize text {i}: {str(result)}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def get_available_voices(
        self,
        language_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        
        Args:
            language_code: Filter by language code (all languages if None)
            
        Returns:
            List of voice information dictionaries
        """
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.list_voices, {"language_code": language_code}
            )
            
            voices = []
            for voice in response.voices:
                voice_info = {
                    "name": voice.name,
                    "language_codes": list(voice.language_codes),
                    "ssml_gender": voice.ssml_gender.name,
                    "natural_sample_rate_hertz": voice.natural_sample_rate_hertz,
                }
                voices.append(voice_info)
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {str(e)}")
            return []
    
    async def create_pronunciation_guide(
        self,
        text: str,
        language_code: str = "en-US"
    ) -> str:
        """
        Create SSML with pronunciation guides for complex terms.
        
        Args:
            text: Original text
            language_code: Language code
            
        Returns:
            SSML-formatted text with pronunciation guides
        """
        # This is a simplified implementation
        # In practice, you'd use a dictionary of legal terms and their pronunciations
        
        legal_terms = {
            "voir dire": '<phoneme alphabet="ipa" ph="vwɑr ˈdir">voir dire</phoneme>',
            "amicus curiae": '<phoneme alphabet="ipa" ph="əˈmaɪkəs ˈkjʊriˌaɪ">amicus curiae</phoneme>',
            "habeas corpus": '<phoneme alphabet="ipa" ph="ˈheɪbiəs ˈkɔrpəs">habeas corpus</phoneme>',
            "pro bono": '<phoneme alphabet="ipa" ph="proʊ ˈboʊnoʊ">pro bono</phoneme>',
            "subpoena": '<phoneme alphabet="ipa" ph="səˈpinə">subpoena</phoneme>',
        }
        
        ssml_text = text
        for term, pronunciation in legal_terms.items():
            ssml_text = ssml_text.replace(term, pronunciation)
        
        # Wrap in SSML speak tag
        ssml_text = f'<speak>{ssml_text}</speak>'
        
        return ssml_text
    
    async def create_narration_with_pauses(
        self,
        sections: List[Dict[str, str]],
        language_code: str = "en-US",
        voice_name: Optional[str] = None,
        section_pause: float = 1.0,
        paragraph_pause: float = 0.5
    ) -> SynthesisResult:
        """
        Create narration with appropriate pauses between sections.
        
        Args:
            sections: List of sections with 'title' and 'content'
            language_code: Language code
            voice_name: Specific voice name
            section_pause: Pause between sections (seconds)
            paragraph_pause: Pause between paragraphs (seconds)
            
        Returns:
            SynthesisResult with complete narration
        """
        ssml_parts = ['<speak>']
        
        for i, section in enumerate(sections):
            if i > 0:
                ssml_parts.append(f'<break time="{section_pause}s"/>')
            
            # Add section title with emphasis
            if section.get('title'):
                ssml_parts.append(f'<emphasis level="strong">{section["title"]}</emphasis>')
                ssml_parts.append(f'<break time="{paragraph_pause}s"/>')
            
            # Add content with paragraph breaks
            content = section.get('content', '')
            paragraphs = content.split('\n\n')
            
            for j, paragraph in enumerate(paragraphs):
                if j > 0:
                    ssml_parts.append(f'<break time="{paragraph_pause}s"/>')
                ssml_parts.append(paragraph.strip())
        
        ssml_parts.append('</speak>')
        ssml_text = ' '.join(ssml_parts)
        
        return await self.synthesize_with_ssml(
            ssml_text=ssml_text,
            language_code=language_code,
            voice_name=voice_name
        )
    
    async def _configure_voice(
        self,
        language_code: str,
        voice_name: Optional[str],
        voice_gender: str
    ) -> texttospeech.VoiceSelectionParams:
        """Configure voice selection parameters."""
        
        # Convert gender string to enum
        gender_map = {
            "MALE": texttospeech.SsmlVoiceGender.MALE,
            "FEMALE": texttospeech.SsmlVoiceGender.FEMALE,
            "NEUTRAL": texttospeech.SsmlVoiceGender.NEUTRAL,
        }
        
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=gender_map.get(voice_gender, texttospeech.SsmlVoiceGender.NEUTRAL)
        )
        
        if voice_name:
            voice_config.name = voice_name
        
        return voice_config
    
    def _configure_audio(
        self,
        audio_format: str,
        sample_rate: Optional[int],
        speaking_rate: float,
        pitch: float,
        volume_gain_db: float
    ) -> texttospeech.AudioConfig:
        """Configure audio output parameters."""
        
        # Map format strings to enums
        format_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "WAV": texttospeech.AudioEncoding.LINEAR16,
            "OGG": texttospeech.AudioEncoding.OGG_OPUS,
        }
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=format_map.get(audio_format.upper(), texttospeech.AudioEncoding.MP3),
            speaking_rate=max(0.25, min(4.0, speaking_rate)),
            pitch=max(-20.0, min(20.0, pitch)),
            volume_gain_db=max(-96.0, min(16.0, volume_gain_db)),
        )
        
        if sample_rate:
            audio_config.sample_rate_hertz = sample_rate
        
        return audio_config
    
    def _get_default_sample_rate(self, audio_format: str) -> int:
        """Get default sample rate for audio format."""
        format_rates = {
            "MP3": 24000,
            "WAV": 24000,
            "OGG": 24000,
        }
        return format_rates.get(audio_format.upper(), 24000)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the service."""
        try:
            # Test synthesis with a short text
            test_text = "Hello, this is a test."
            
            result = await self.synthesize_text(
                text=test_text,
                language_code="en-US",
                audio_format="MP3"
            )
            
            return {
                "status": "healthy",
                "service": "text-to-speech",
                "timestamp": datetime.utcnow().isoformat(),
                "test_completed": True,
                "audio_size_bytes": len(result.audio_content),
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "text-to-speech",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# Global service instance
text_to_speech_service = TextToSpeechService()