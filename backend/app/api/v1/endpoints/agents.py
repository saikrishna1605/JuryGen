"""
AI Agent API endpoints with Murf, AssemblyAI, and Gemini integration.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from pydantic import BaseModel, Field

from ....core.security import optional_auth
from ....services.agent_service import agent_service

router = APIRouter()


class VoiceQuestionRequest(BaseModel):
    """Voice question request model."""
    document_id: str = Field(..., description="Document ID to ask about")
    session_id: str = Field(default="default", description="Session ID")


class TextGenerationRequest(BaseModel):
    """Text generation request model."""
    prompt: str = Field(..., description="Text generation prompt")
    context: str = Field(default="", description="Additional context")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")


class TTSRequest(BaseModel):
    """Text-to-speech request model."""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: str = Field(default="en-US-davis", description="Voice ID")
    speed: float = Field(default=1.0, description="Speech speed")


class AgentResponse(BaseModel):
    """Agent response model."""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message")
    message: str = Field(..., description="Response message")


@router.post("/agents/voice-question", response_model=AgentResponse)
async def process_voice_question(
    audio_file: UploadFile = File(..., description="Audio file with question"),
    document_id: str = Form(..., description="Document ID"),
    session_id: str = Form(default="default", description="Session ID"),
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Process a voice question using the complete AI pipeline:
    1. Transcribe audio (AssemblyAI)
    2. Generate answer (Gemini)
    3. Convert to speech (Murf)
    """
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Get document content for context
        document_content = await get_document_content(document_id)
        
        # Process through AI pipeline
        result = await agent_service.process_voice_question(audio_data, document_content)
        
        if result["success"]:
            # Save to conversation history
            await save_conversation_history(
                document_id=document_id,
                session_id=session_id,
                question=result["question"],
                answer=result["answer"],
                audio_url=result.get("audio_url"),
                confidence=result.get("transcription_confidence", 0.9)
            )
            
            return AgentResponse(
                success=True,
                data=result,
                message="Voice question processed successfully"
            )
        else:
            return AgentResponse(
                success=False,
                error=result["error"],
                message=f"Voice processing failed at {result.get('step', 'unknown')} step"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice question processing failed: {str(e)}"
        )


@router.post("/agents/transcribe", response_model=AgentResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Transcribe audio using AssemblyAI.
    """
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Get file format from filename
        audio_format = audio_file.filename.split('.')[-1].lower() if audio_file.filename else "wav"
        
        # Transcribe
        result = await agent_service.transcribe_audio(audio_data, audio_format)
        
        if result["success"]:
            return AgentResponse(
                success=True,
                data={
                    "text": result["text"],
                    "confidence": result.get("confidence", 0.9),
                    "language": result.get("language", "en"),
                    "duration": result.get("duration", 0)
                },
                message="Audio transcribed successfully"
            )
        else:
            return AgentResponse(
                success=False,
                error=result["error"],
                message="Transcription failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/agents/generate-text", response_model=AgentResponse)
async def generate_text(
    request: TextGenerationRequest,
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Generate text using Gemini AI.
    """
    try:
        result = await agent_service.generate_text(
            prompt=request.prompt,
            context=request.context,
            max_tokens=request.max_tokens
        )
        
        if result["success"]:
            return AgentResponse(
                success=True,
                data={
                    "text": result["text"],
                    "model": result.get("model", "gemini"),
                    "tokens_used": result.get("tokens_used", 0)
                },
                message="Text generated successfully"
            )
        else:
            return AgentResponse(
                success=False,
                error=result["error"],
                message="Text generation failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text generation failed: {str(e)}"
        )


@router.post("/agents/text-to-speech", response_model=AgentResponse)
async def text_to_speech(
    request: TTSRequest,
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Convert text to speech using Murf AI.
    """
    try:
        result = await agent_service.text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            speed=request.speed
        )
        
        if result["success"]:
            return AgentResponse(
                success=True,
                data={
                    "audio_url": result["audio_url"],
                    "audio_data": result.get("audio_data"),
                    "duration": result.get("duration", 0),
                    "voice_id": result["voice_id"],
                    "format": result.get("format", "mp3")
                },
                message="Text converted to speech successfully"
            )
        else:
            return AgentResponse(
                success=False,
                error=result["error"],
                message="Text-to-speech conversion failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text-to-speech failed: {str(e)}"
        )


@router.get("/agents/voices", response_model=AgentResponse)
async def get_available_voices(
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Get available Murf AI voices.
    """
    try:
        result = await agent_service.get_available_voices()
        
        if result["success"]:
            return AgentResponse(
                success=True,
                data={"voices": result["voices"]},
                message="Voices retrieved successfully"
            )
        else:
            return AgentResponse(
                success=False,
                error=result["error"],
                message="Failed to retrieve voices"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voices: {str(e)}"
        )


@router.post("/agents/chat", response_model=AgentResponse)
async def chat_with_document(
    document_id: str = Form(...),
    question: str = Form(...),
    session_id: str = Form(default="default"),
    user: Optional[dict] = Depends(optional_auth)
):
    """
    Chat with a document using Gemini AI.
    """
    try:
        # Get document content
        document_content = await get_document_content(document_id)
        
        # Generate response
        result = await agent_service.generate_text(
            prompt=question,
            context=document_content
        )
        
        if result["success"]:
            # Save to conversation history
            await save_conversation_history(
                document_id=document_id,
                session_id=session_id,
                question=question,
                answer=result["text"],
                confidence=0.95
            )
            
            return AgentResponse(
                success=True,
                data={
                    "question": question,
                    "answer": result["text"],
                    "model": result.get("model", "gemini"),
                    "session_id": session_id
                },
                message="Chat response generated successfully"
            )
        else:
            return AgentResponse(
                success=False,
                error=result["error"],
                message="Chat response generation failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/agents/status")
async def get_agent_status():
    """
    Get the status of all AI services.
    """
    return {
        "success": True,
        "data": {
            "services": {
                "murf_tts": bool(agent_service.murf_api_key),
                "assemblyai_transcription": bool(agent_service.assemblyai_api_key),
                "gemini_generation": agent_service.gemini_enabled
            },
            "capabilities": {
                "voice_questions": bool(agent_service.murf_api_key and agent_service.assemblyai_api_key and agent_service.gemini_enabled),
                "transcription": bool(agent_service.assemblyai_api_key),
                "text_generation": agent_service.gemini_enabled,
                "text_to_speech": bool(agent_service.murf_api_key)
            }
        },
        "message": "Agent status retrieved successfully"
    }


# Helper functions
async def get_document_content(document_id: str) -> str:
    """Get document content for AI processing."""
    import json
    from pathlib import Path
    
    uploads_dir = Path("uploads")
    metadata_file = uploads_dir / "documents.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                documents = json.load(f)
            
            for doc in documents:
                if doc["id"] == document_id:
                    return doc.get("extracted_text", "Document content not available for analysis.")
        except Exception as e:
            print(f"Error loading document content: {e}")
    
    return "Document content not available for analysis."


async def save_conversation_history(
    document_id: str,
    session_id: str,
    question: str,
    answer: str,
    audio_url: Optional[str] = None,
    confidence: float = 0.9
):
    """Save conversation to history."""
    import json
    from pathlib import Path
    
    try:
        qa_dir = Path("uploads/qa")
        qa_dir.mkdir(exist_ok=True)
        
        history_file = qa_dir / f"{document_id}_{session_id}.json"
        history = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Add new conversation
        conversation = {
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "audio_url": audio_url,
            "type": "voice" if audio_url else "text"
        }
        
        history.append(conversation)
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        print(f"Error saving conversation history: {e}")