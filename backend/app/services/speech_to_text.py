"""
Speech-to-Text service using Google Cloud Speech-to-Text API.

This service handles:
- Audio file transcription
- Real-time streaming transcription
- Language detection and multi-language support
- Audio quality optimization
- Confidence scoring and alternatives
"""

import asyncio
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from datetime import datetime
import io

from google.cloud import speech
from google.api_core import exceptions as gcp_exceptions
import librosa
import soundfile as sf
import numpy as np

from ..core.config import get_settings
from ..core.exceptions import WorkflowError

logger = logging.getLogger(__name__)
settings = get_settings()


class TranscriptionResult:
    """Represents a transcription result."""
    
    def __init__(
        self,
        transcript: str,
        confidence: float,
        language_code: str,
        alternatives: List[Dict[str, Any]] = None,
        word_timestamps: List[Dict[str, Any]] = None,
        speaker_labels: List[Dict[str, Any]] = None,
        audio_duration: float = 0.0,
        processing_time: float = 0.0
    ):
        self.transcript = transcript
        self.confidence = confidence
        self.language_code = language_code
        self.alternatives = alternatives or []
        self.word_timestamps = word_timestamps or []
        self.speaker_labels = speaker_labels or []
        self.audio_duration = audio_duration
        self.processing_time = processing_time
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "transcript": self.transcript,
            "confidence": self.confidence,
            "language_code": self.language_code,
            "alternatives": self.alternatives,
            "word_timestamps": self.word_timestamps,
            "speaker_labels": self.speaker_labels,
            "audio_duration": self.audio_duration,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat(),
        }


class SpeechToTextService:
    """
    Service for converting speech to text using Google Cloud Speech-to-Text API.
    
    Provides both batch and streaming transcription capabilities with
    advanced features like language detection, speaker diarization,
    and word-level timestamps.
    """
    
    def __init__(self):
        """Initialize the Speech-to-Text service."""
        try:
            self.client = speech.SpeechClient()
            logger.info("Speech-to-Text service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Speech-to-Text service: {str(e)}")
            raise WorkflowError(f"Speech-to-Text service initialization failed: {str(e)}") from e
    
    async def transcribe_audio_file(
        self,
        audio_data: bytes,
        language_code: str = "en-US",
        sample_rate: Optional[int] = None,
        audio_format: str = "webm",
        enable_word_timestamps: bool = True,
        enable_speaker_diarization: bool = False,
        max_speaker_count: int = 2,
        enable_automatic_punctuation: bool = True,
        enable_profanity_filter: bool = False,
        speech_contexts: List[str] = None,
        model: str = "latest_long"
    ) -> TranscriptionResult:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_data: Raw audio data bytes
            language_code: Language code (e.g., 'en-US', 'es-ES')
            sample_rate: Audio sample rate (auto-detected if None)
            audio_format: Audio format (webm, wav, mp3, etc.)
            enable_word_timestamps: Include word-level timestamps
            enable_speaker_diarization: Enable speaker identification
            max_speaker_count: Maximum number of speakers to detect
            enable_automatic_punctuation: Add punctuation automatically
            enable_profanity_filter: Filter profanity from results
            speech_contexts: Context phrases to improve recognition
            model: Speech recognition model to use
            
        Returns:
            TranscriptionResult with transcript and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Preprocess audio
            processed_audio, detected_sample_rate, duration = await self._preprocess_audio(
                audio_data, audio_format, sample_rate
            )
            
            # Configure recognition
            config = self._build_recognition_config(
                language_code=language_code,
                sample_rate=detected_sample_rate,
                enable_word_timestamps=enable_word_timestamps,
                enable_speaker_diarization=enable_speaker_diarization,
                max_speaker_count=max_speaker_count,
                enable_automatic_punctuation=enable_automatic_punctuation,
                enable_profanity_filter=enable_profanity_filter,
                speech_contexts=speech_contexts,
                model=model
            )
            
            # Create audio object
            audio = speech.RecognitionAudio(content=processed_audio)
            
            # Perform transcription
            logger.info(f"Starting transcription for {duration:.2f}s audio")
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.recognize, config, audio
            )
            
            # Process results
            result = self._process_transcription_response(
                response, duration, start_time
            )
            
            logger.info(f"Transcription completed in {result.processing_time:.2f}s")
            return result
            
        except gcp_exceptions.GoogleAPIError as e:
            logger.error(f"Google Speech API error: {str(e)}")
            raise WorkflowError(f"Speech recognition failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise WorkflowError(f"Audio transcription failed: {str(e)}") from e
    
    async def transcribe_with_language_detection(
        self,
        audio_data: bytes,
        candidate_languages: List[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio with automatic language detection.
        
        Args:
            audio_data: Raw audio data bytes
            candidate_languages: List of candidate language codes
            **kwargs: Additional transcription parameters
            
        Returns:
            TranscriptionResult with detected language
        """
        if not candidate_languages:
            candidate_languages = ["en-US", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR"]
        
        try:
            # First, try language detection with a short sample
            detected_language = await self._detect_language(audio_data, candidate_languages)
            
            # Transcribe with detected language
            result = await self.transcribe_audio_file(
                audio_data,
                language_code=detected_language,
                **kwargs
            )
            
            logger.info(f"Detected language: {detected_language}")
            return result
            
        except Exception as e:
            logger.warning(f"Language detection failed, falling back to en-US: {str(e)}")
            # Fallback to English
            return await self.transcribe_audio_file(
                audio_data,
                language_code="en-US",
                **kwargs
            )
    
    async def stream_transcribe(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        language_code: str = "en-US",
        sample_rate: int = 16000,
        interim_results: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform streaming transcription of audio data.
        
        Args:
            audio_stream: Async generator yielding audio chunks
            language_code: Language code for recognition
            sample_rate: Audio sample rate
            interim_results: Return interim (partial) results
            
        Yields:
            Transcription results as they become available
        """
        try:
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="latest_short",
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=interim_results,
                single_utterance=False,
            )
            
            # Create audio generator
            async def audio_generator():
                yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
                async for chunk in audio_stream:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
            
            # Start streaming recognition
            responses = self.client.streaming_recognize(audio_generator())
            
            for response in responses:
                for result in response.results:
                    yield {
                        "transcript": result.alternatives[0].transcript,
                        "confidence": result.alternatives[0].confidence,
                        "is_final": result.is_final,
                        "stability": result.stability,
                        "language_code": language_code,
                    }
                    
        except Exception as e:
            logger.error(f"Streaming transcription error: {str(e)}")
            raise WorkflowError(f"Streaming transcription failed: {str(e)}") from e
    
    async def _preprocess_audio(
        self,
        audio_data: bytes,
        audio_format: str,
        target_sample_rate: Optional[int] = None
    ) -> tuple[bytes, int, float]:
        """
        Preprocess audio data for optimal recognition.
        
        Args:
            audio_data: Raw audio data
            audio_format: Original audio format
            target_sample_rate: Target sample rate (16kHz if None)
            
        Returns:
            Tuple of (processed_audio_bytes, sample_rate, duration)
        """
        try:
            # Create temporary file for audio processing
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Load audio with librosa
                audio, original_sr = librosa.load(temp_path, sr=None, mono=True)
                duration = len(audio) / original_sr
                
                # Resample if needed
                if target_sample_rate and original_sr != target_sample_rate:
                    audio = librosa.resample(audio, orig_sr=original_sr, target_sr=target_sample_rate)
                    sample_rate = target_sample_rate
                else:
                    sample_rate = original_sr
                
                # Normalize audio
                audio = librosa.util.normalize(audio)
                
                # Apply noise reduction (simple high-pass filter)
                audio = self._apply_noise_reduction(audio, sample_rate)
                
                # Convert to 16-bit PCM
                audio_int16 = (audio * 32767).astype(np.int16)
                
                # Convert to bytes
                audio_bytes = audio_int16.tobytes()
                
                return audio_bytes, int(sample_rate), duration
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Audio preprocessing error: {str(e)}")
            raise WorkflowError(f"Audio preprocessing failed: {str(e)}") from e
    
    def _apply_noise_reduction(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply basic noise reduction to audio."""
        try:
            # Simple high-pass filter to remove low-frequency noise
            from scipy.signal import butter, filtfilt
            
            # High-pass filter at 80 Hz
            nyquist = sample_rate / 2
            low = 80 / nyquist
            b, a = butter(4, low, btype='high')
            filtered_audio = filtfilt(b, a, audio)
            
            return filtered_audio
            
        except ImportError:
            # If scipy is not available, return original audio
            logger.warning("scipy not available, skipping noise reduction")
            return audio
        except Exception as e:
            logger.warning(f"Noise reduction failed: {str(e)}")
            return audio
    
    def _build_recognition_config(
        self,
        language_code: str,
        sample_rate: int,
        enable_word_timestamps: bool = True,
        enable_speaker_diarization: bool = False,
        max_speaker_count: int = 2,
        enable_automatic_punctuation: bool = True,
        enable_profanity_filter: bool = False,
        speech_contexts: List[str] = None,
        model: str = "latest_long"
    ) -> speech.RecognitionConfig:
        """Build recognition configuration."""
        
        # Base configuration
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            max_alternatives=3,
            enable_word_time_offsets=enable_word_timestamps,
            enable_automatic_punctuation=enable_automatic_punctuation,
            profanity_filter=enable_profanity_filter,
            model=model,
        )
        
        # Speaker diarization
        if enable_speaker_diarization:
            config.diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=1,
                max_speaker_count=max_speaker_count,
            )
        
        # Speech contexts for better recognition
        if speech_contexts:
            config.speech_contexts = [
                speech.SpeechContext(phrases=speech_contexts)
            ]
        
        return config
    
    def _process_transcription_response(
        self,
        response: speech.RecognizeResponse,
        audio_duration: float,
        start_time: datetime
    ) -> TranscriptionResult:
        """Process the transcription response."""
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if not response.results:
            return TranscriptionResult(
                transcript="",
                confidence=0.0,
                language_code="unknown",
                audio_duration=audio_duration,
                processing_time=processing_time
            )
        
        # Get the best result
        result = response.results[0]
        best_alternative = result.alternatives[0]
        
        # Extract alternatives
        alternatives = []
        for alt in result.alternatives[1:]:
            alternatives.append({
                "transcript": alt.transcript,
                "confidence": alt.confidence,
            })
        
        # Extract word timestamps
        word_timestamps = []
        if hasattr(best_alternative, 'words'):
            for word in best_alternative.words:
                word_timestamps.append({
                    "word": word.word,
                    "start_time": word.start_time.total_seconds(),
                    "end_time": word.end_time.total_seconds(),
                    "speaker_tag": getattr(word, 'speaker_tag', 0),
                })
        
        # Extract speaker labels
        speaker_labels = []
        if hasattr(result, 'speaker_tag'):
            speaker_labels.append({
                "speaker_tag": result.speaker_tag,
                "transcript": best_alternative.transcript,
            })
        
        return TranscriptionResult(
            transcript=best_alternative.transcript,
            confidence=best_alternative.confidence,
            language_code=response.results[0].language_code if hasattr(response.results[0], 'language_code') else "unknown",
            alternatives=alternatives,
            word_timestamps=word_timestamps,
            speaker_labels=speaker_labels,
            audio_duration=audio_duration,
            processing_time=processing_time
        )
    
    async def _detect_language(
        self,
        audio_data: bytes,
        candidate_languages: List[str]
    ) -> str:
        """Detect the language of the audio."""
        try:
            # Use a shorter sample for language detection
            sample_audio = audio_data[:min(len(audio_data), 1024 * 1024)]  # Max 1MB sample
            
            # Process audio
            processed_audio, sample_rate, _ = await self._preprocess_audio(
                sample_audio, "webm", 16000
            )
            
            # Configure for language detection
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=candidate_languages[0],  # Primary language
                alternative_language_codes=candidate_languages[1:5],  # Up to 4 alternatives
                max_alternatives=1,
            )
            
            audio = speech.RecognitionAudio(content=processed_audio)
            
            # Perform recognition
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.recognize, config, audio
            )
            
            if response.results:
                # Return the detected language
                return response.results[0].language_code
            
            # Fallback to first candidate
            return candidate_languages[0]
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return candidate_languages[0]
    
    async def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages."""
        # This is a static list of commonly supported languages
        # In a real implementation, you might fetch this from the API
        return [
            {"code": "en-US", "name": "English (US)", "region": "United States"},
            {"code": "en-GB", "name": "English (UK)", "region": "United Kingdom"},
            {"code": "es-ES", "name": "Spanish (Spain)", "region": "Spain"},
            {"code": "es-US", "name": "Spanish (US)", "region": "United States"},
            {"code": "fr-FR", "name": "French", "region": "France"},
            {"code": "de-DE", "name": "German", "region": "Germany"},
            {"code": "it-IT", "name": "Italian", "region": "Italy"},
            {"code": "pt-BR", "name": "Portuguese (Brazil)", "region": "Brazil"},
            {"code": "pt-PT", "name": "Portuguese (Portugal)", "region": "Portugal"},
            {"code": "ru-RU", "name": "Russian", "region": "Russia"},
            {"code": "ja-JP", "name": "Japanese", "region": "Japan"},
            {"code": "ko-KR", "name": "Korean", "region": "South Korea"},
            {"code": "zh-CN", "name": "Chinese (Simplified)", "region": "China"},
            {"code": "zh-TW", "name": "Chinese (Traditional)", "region": "Taiwan"},
            {"code": "ar-SA", "name": "Arabic", "region": "Saudi Arabia"},
            {"code": "hi-IN", "name": "Hindi", "region": "India"},
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the service."""
        try:
            # Test with a small audio sample
            test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32)
            test_audio_bytes = (test_audio * 32767).astype(np.int16).tobytes()
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
            )
            
            audio = speech.RecognitionAudio(content=test_audio_bytes)
            
            # This should complete quickly even if it doesn't recognize anything
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.client.recognize, config, audio
            )
            
            return {
                "status": "healthy",
                "service": "speech-to-text",
                "timestamp": datetime.utcnow().isoformat(),
                "test_completed": True,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "speech-to-text",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# Global service instance
speech_to_text_service = SpeechToTextService()