"""
Speech API endpoints for Speech-to-Text and Text-to-Speech services.

This module provides endpoints for:
- Audio transcription (Speech-to-Text)
- Text synthesis (Text-to-Speech)
- Voice and language management
- Audio format conversion
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ....core.security import require_auth
from ....models.base import ApiResponse
from ....services.speech_to_text import speech_to_text_service, TranscriptionResult
from ....services.text_to_speech import text_to_speech_service, SynthesisResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech", tags=["speech"])


# Request/Response Models
class TranscriptionRequest(BaseModel):
    language_code: str = Field(default="en-US", description="Language code for transcription")
    enable_word_timestamps: bool = Field(default=True, description="Include word-level timestamps")
    enable_speaker_diarization: bool = Field(default=False, description="Enable speaker identification")
    max_speaker_count: int = Field(default=2, ge=1, le=6, description="Maximum number of speakers")
    enable_automatic_punctuation: bool = Field(default=True, description="Add punctuation automatically")
    enable_profanity_filter: bool = Field(default=False, description="Filter profanity from results")
    speech_contexts: Optional[List[str]] = Field(default=None, description="Context phrases for better recognition")
    model: str = Field(default="latest_long", description="Speech recognition model")


class TranscriptionResponse(BaseModel):
    transcript: str
    confidence: float
    language_code: str
    alternatives: List[Dict[str, Any]]
    word_timestamps: List[Dict[str, Any]]
    speaker_labels: List[Dict[str, Any]]
    audio_duration: float
    processing_time: float


class SynthesisRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    language_code: str = Field(default="en-US", description="Language code for synthesis")
    voice_name: Optional[str] = Field(default=None, description="Specific voice name")
    voice_gender: str = Field(default="NEUTRAL", description="Voice gender (MALE, FEMALE, NEUTRAL)")
    audio_format: str = Field(default="MP3", description="Output audio format (MP3, WAV, OGG)")
    sample_rate: Optional[int] = Field(default=None, description="Audio sample rate")
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech rate")
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0, description="Voice pitch in semitones")
    volume_gain_db: float = Field(default=0.0, ge=-96.0, le=16.0, description="Volume gain in dB")
    use_ssml: bool = Field(default=False, description="Whether text contains SSML markup")


class SynthesisResponse(BaseModel):
    audio_content_base64: str
    text: str
    voice_name: str
    language_code: str
    audio_format: str
    sample_rate: int
    duration: float
    processing_time: float


class VoiceInfo(BaseModel):
    name: str
    language_codes: List[str]
    ssml_gender: str
    natural_sample_rate_hertz: int


# Speech-to-Text Endpoints

@router.post("/transcribe", response_model=ApiResponse[TranscriptionResponse])
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language_code: str = Form(default="en-US"),
    enable_word_timestamps: bool = Form(default=True),
    enable_speaker_diarization: bool = Form(default=False),
    max_speaker_count: int = Form(default=2),
    enable_automatic_punctuation: bool = Form(default=True),
    enable_profanity_filter: bool = Form(default=False),
    model: str = Form(default="latest_long"),
    current_user: dict = Depends(require_auth)
):
    """
    Transcribe an audio file to text.
    
    Upload an audio file and receive a text transcription with optional
    features like word timestamps, speaker diarization, and confidence scores.
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Read audio data
        audio_data = await audio_file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty"
            )
        
        # Determine audio format from content type
        audio_format = audio_file.content_type.split('/')[-1]
        if audio_format == 'mpeg':
            audio_format = 'mp3'
        
        logger.info(f"Transcribing audio file: {audio_file.filename} ({len(audio_data)} bytes)")
        
        # Perform transcription
        result = await speech_to_text_service.transcribe_audio_file(
            audio_data=audio_data,
            language_code=language_code,
            audio_format=audio_format,
            enable_word_timestamps=enable_word_timestamps,
            enable_speaker_diarization=enable_speaker_diarization,
            max_speaker_count=max_speaker_count,
            enable_automatic_punctuation=enable_automatic_punctuation,
            enable_profanity_filter=enable_profanity_filter,
            model=model
        )
        
        response_data = TranscriptionResponse(
            transcript=result.transcript,
            confidence=result.confidence,
            language_code=result.language_code,
            alternatives=result.alternatives,
            word_timestamps=result.word_timestamps,
            speaker_labels=result.speaker_labels,
            audio_duration=result.audio_duration,
            processing_time=result.processing_time
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Audio transcribed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/transcribe-with-language-detection", response_model=ApiResponse[TranscriptionResponse])
async def transcribe_with_language_detection(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    candidate_languages: List[str] = Query(default=["en-US", "es-ES", "fr-FR"], description="Candidate languages"),
    current_user: dict = Depends(require_auth)
):
    """
    Transcribe audio with automatic language detection.
    
    Upload an audio file and the service will automatically detect the language
    before performing transcription.
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file"
            )
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Determine audio format
        audio_format = audio_file.content_type.split('/')[-1]
        if audio_format == 'mpeg':
            audio_format = 'mp3'
        
        logger.info(f"Transcribing with language detection: {audio_file.filename}")
        
        # Perform transcription with language detection
        result = await speech_to_text_service.transcribe_with_language_detection(
            audio_data=audio_data,
            candidate_languages=candidate_languages
        )
        
        response_data = TranscriptionResponse(
            transcript=result.transcript,
            confidence=result.confidence,
            language_code=result.language_code,
            alternatives=result.alternatives,
            word_timestamps=result.word_timestamps,
            speaker_labels=result.speaker_labels,
            audio_duration=result.audio_duration,
            processing_time=result.processing_time
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message=f"Audio transcribed successfully (detected language: {result.language_code})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Language detection transcription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription with language detection failed: {str(e)}"
        )


# Text-to-Speech Endpoints

@router.post("/synthesize", response_model=ApiResponse[SynthesisResponse])
async def synthesize_text(
    request: SynthesisRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Synthesize text to speech.
    
    Convert text to high-quality speech audio with customizable voice,
    language, and audio parameters.
    """
    try:
        logger.info(f"Synthesizing text: {request.text[:100]}...")
        
        # Perform synthesis
        result = await text_to_speech_service.synthesize_text(
            text=request.text,
            language_code=request.language_code,
            voice_name=request.voice_name,
            voice_gender=request.voice_gender,
            audio_format=request.audio_format,
            sample_rate=request.sample_rate,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
            volume_gain_db=request.volume_gain_db,
            use_ssml=request.use_ssml
        )
        
        response_data = SynthesisResponse(
            audio_content_base64=result.to_dict()["audio_content_base64"],
            text=result.text,
            voice_name=result.voice_name,
            language_code=result.language_code,
            audio_format=result.audio_format,
            sample_rate=result.sample_rate,
            duration=result.duration,
            processing_time=result.processing_time
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="Text synthesized successfully"
        )
        
    except Exception as e:
        logger.error(f"Text synthesis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text synthesis failed: {str(e)}"
        )


@router.post("/synthesize-audio", response_class=Response)
async def synthesize_text_to_audio(
    request: SynthesisRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Synthesize text to speech and return audio file directly.
    
    Convert text to speech and return the audio content directly
    as a downloadable file.
    """
    try:
        # Perform synthesis
        result = await text_to_speech_service.synthesize_text(
            text=request.text,
            language_code=request.language_code,
            voice_name=request.voice_name,
            voice_gender=request.voice_gender,
            audio_format=request.audio_format,
            sample_rate=request.sample_rate,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
            volume_gain_db=request.volume_gain_db,
            use_ssml=request.use_ssml
        )
        
        # Determine content type
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
        }
        content_type = content_type_map.get(result.audio_format.lower(), "audio/mpeg")
        
        # Generate filename
        filename = f"synthesis_{result.created_at.strftime('%Y%m%d_%H%M%S')}.{result.audio_format.lower()}"
        
        return Response(
            content=result.audio_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(result.audio_content)),
            }
        )
        
    except Exception as e:
        logger.error(f"Audio synthesis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio synthesis failed: {str(e)}"
        )


@router.post("/synthesize-ssml", response_model=ApiResponse[SynthesisResponse])
async def synthesize_ssml(
    text: str = Form(..., description="SSML-formatted text"),
    language_code: str = Form(default="en-US"),
    voice_name: Optional[str] = Form(default=None),
    audio_format: str = Form(default="MP3"),
    current_user: dict = Depends(require_auth)
):
    """
    Synthesize SSML-formatted text to speech.
    
    Convert SSML (Speech Synthesis Markup Language) text to speech
    for advanced control over pronunciation, timing, and emphasis.
    """
    try:
        logger.info(f"Synthesizing SSML text: {text[:100]}...")
        
        # Perform SSML synthesis
        result = await text_to_speech_service.synthesize_with_ssml(
            ssml_text=text,
            language_code=language_code,
            voice_name=voice_name,
            audio_format=audio_format
        )
        
        response_data = SynthesisResponse(
            audio_content_base64=result.to_dict()["audio_content_base64"],
            text=result.text,
            voice_name=result.voice_name,
            language_code=result.language_code,
            audio_format=result.audio_format,
            sample_rate=result.sample_rate,
            duration=result.duration,
            processing_time=result.processing_time
        )
        
        return ApiResponse(
            success=True,
            data=response_data,
            message="SSML text synthesized successfully"
        )
        
    except Exception as e:
        logger.error(f"SSML synthesis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSML synthesis failed: {str(e)}"
        )


# Voice and Language Management

@router.get("/voices", response_model=ApiResponse[List[VoiceInfo]])
async def get_available_voices(
    language_code: Optional[str] = Query(default=None, description="Filter by language code"),
    current_user: dict = Depends(require_auth)
):
    """
    Get list of available voices for text-to-speech.
    
    Retrieve all available voices, optionally filtered by language code.
    """
    try:
        voices = await text_to_speech_service.get_available_voices(language_code)
        
        voice_list = [
            VoiceInfo(
                name=voice["name"],
                language_codes=voice["language_codes"],
                ssml_gender=voice["ssml_gender"],
                natural_sample_rate_hertz=voice["natural_sample_rate_hertz"]
            )
            for voice in voices
        ]
        
        return ApiResponse(
            success=True,
            data=voice_list,
            message=f"Retrieved {len(voice_list)} available voices"
        )
        
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available voices: {str(e)}"
        )


@router.get("/languages", response_model=ApiResponse[List[Dict[str, str]]])
async def get_supported_languages(
    current_user: dict = Depends(require_auth)
):
    """
    Get list of supported languages for speech services.
    
    Retrieve all supported languages for both speech-to-text and text-to-speech.
    """
    try:
        languages = await speech_to_text_service.get_supported_languages()
        
        return ApiResponse(
            success=True,
            data=languages,
            message=f"Retrieved {len(languages)} supported languages"
        )
        
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported languages: {str(e)}"
        )


# Utility Endpoints

@router.post("/create-pronunciation-guide", response_model=ApiResponse[str])
async def create_pronunciation_guide(
    text: str = Form(..., description="Text to create pronunciation guide for"),
    language_code: str = Form(default="en-US"),
    current_user: dict = Depends(require_auth)
):
    """
    Create SSML pronunciation guide for complex legal terms.
    
    Convert plain text to SSML with pronunciation guides for
    difficult legal terminology.
    """
    try:
        ssml_text = await text_to_speech_service.create_pronunciation_guide(
            text=text,
            language_code=language_code
        )
        
        return ApiResponse(
            success=True,
            data=ssml_text,
            message="Pronunciation guide created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating pronunciation guide: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pronunciation guide: {str(e)}"
        )


# Health Check

@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def speech_health_check():
    """
    Check the health of speech services.
    
    Perform health checks on both Speech-to-Text and Text-to-Speech services.
    """
    try:
        stt_health = await speech_to_text_service.health_check()
        tts_health = await text_to_speech_service.health_check()
        
        overall_status = "healthy" if (
            stt_health["status"] == "healthy" and 
            tts_health["status"] == "healthy"
        ) else "unhealthy"
        
        health_data = {
            "overall_status": overall_status,
            "speech_to_text": stt_health,
            "text_to_speech": tts_health,
        }
        
        return ApiResponse(
            success=True,
            data=health_data,
            message="Speech services health check completed"
        )
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )