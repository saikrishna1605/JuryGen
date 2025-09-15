#!/usr/bin/env python3
"""
Test AI Agent services - Murf, AssemblyAI, and Gemini integration.
"""

import requests
import json
import os

def test_agent_services():
    """Test all AI agent services."""
    base_url = "http://127.0.0.1:8000"
    
    print("🤖 Testing AI Agent Services")
    print("=" * 50)
    
    # Test 1: Agent Status
    try:
        r = requests.get(f"{base_url}/v1/agents/status")
        print(f"✅ Agent Status: {r.status_code}")
        
        if r.status_code == 200:
            status = r.json()
            services = status.get('data', {}).get('services', {})
            capabilities = status.get('data', {}).get('capabilities', {})
            
            print(f"   Murf TTS: {'✅' if services.get('murf_tts') else '❌'}")
            print(f"   AssemblyAI: {'✅' if services.get('assemblyai_transcription') else '❌'}")
            print(f"   Gemini: {'✅' if services.get('gemini_generation') else '❌'}")
            print(f"   Voice Questions: {'✅' if capabilities.get('voice_questions') else '❌'}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"❌ Agent Status failed: {e}")
    
    # Test 2: Text Generation
    try:
        payload = {
            "prompt": "What are the key risks in a legal contract?",
            "context": "This is a sample legal document with various clauses including liability, termination, and payment terms.",
            "max_tokens": 500
        }
        
        r = requests.post(f"{base_url}/v1/agents/generate-text", json=payload)
        print(f"✅ Text Generation: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                text = result.get('data', {}).get('text', '')
                print(f"   Generated: {text[:100]}...")
                print(f"   Model: {result.get('data', {}).get('model', 'unknown')}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"❌ Text Generation failed: {e}")
    
    # Test 3: Available Voices
    try:
        r = requests.get(f"{base_url}/v1/agents/voices")
        print(f"✅ Available Voices: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                voices = result.get('data', {}).get('voices', [])
                print(f"   Found {len(voices)} voices")
                for voice in voices[:3]:  # Show first 3
                    print(f"   - {voice.get('name', 'Unknown')}: {voice.get('id', 'no-id')}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"❌ Available Voices failed: {e}")
    
    # Test 4: Text-to-Speech
    try:
        payload = {
            "text": "This is a test of the Murf text-to-speech system for legal document analysis.",
            "voice_id": "en-US-davis",
            "speed": 1.0
        }
        
        r = requests.post(f"{base_url}/v1/agents/text-to-speech", json=payload)
        print(f"✅ Text-to-Speech: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                audio_url = result.get('data', {}).get('audio_url')
                duration = result.get('data', {}).get('duration', 0)
                print(f"   Audio URL: {'✅ Generated' if audio_url else '❌ Missing'}")
                print(f"   Duration: {duration} seconds")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"❌ Text-to-Speech failed: {e}")
    
    # Test 5: Document Chat
    try:
        # First, check if we have any documents
        docs_response = requests.get(f"{base_url}/v1/documents")
        document_id = "test_doc"
        
        if docs_response.status_code == 200:
            docs = docs_response.json().get('data', [])
            if docs:
                document_id = docs[0]['id']
        
        payload = {
            "document_id": document_id,
            "question": "What are the main terms and conditions in this document?",
            "session_id": "test_session"
        }
        
        r = requests.post(f"{base_url}/v1/agents/chat", data=payload)
        print(f"✅ Document Chat: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                answer = result.get('data', {}).get('answer', '')
                print(f"   Answer: {answer[:100]}...")
                print(f"   Session: {result.get('data', {}).get('session_id', 'unknown')}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"❌ Document Chat failed: {e}")
    
    # Test 6: Transcription (mock test without audio file)
    try:
        # This will fail without an actual audio file, but tests the endpoint
        r = requests.post(f"{base_url}/v1/agents/transcribe")
        print(f"✅ Transcription Endpoint: {r.status_code} (expected 422 - missing file)")
        
        if r.status_code == 422:
            print("   ✅ Endpoint exists and validates input correctly")
        else:
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 AI Agent Test Complete!")
    print("\n📋 Setup Instructions:")
    print("1. Add API keys to backend/.env:")
    print("   MURF_API_KEY=your-murf-key")
    print("   ASSEMBLYAI_API_KEY=your-assemblyai-key") 
    print("   GEMINI_API_KEY=your-gemini-key")
    print("2. Restart backend server")
    print("3. Test with real API keys for full functionality")

def test_with_sample_audio():
    """Test voice processing with a sample audio file (if available)."""
    base_url = "http://127.0.0.1:8000"
    
    # Check if sample audio exists
    sample_audio_path = "sample_question.wav"
    
    if os.path.exists(sample_audio_path):
        print("\n🎤 Testing Voice Processing with Sample Audio")
        print("-" * 40)
        
        try:
            with open(sample_audio_path, 'rb') as audio_file:
                files = {'audio_file': audio_file}
                data = {
                    'document_id': 'test_doc',
                    'session_id': 'voice_test'
                }
                
                r = requests.post(f"{base_url}/v1/agents/voice-question", files=files, data=data)
                print(f"✅ Voice Question: {r.status_code}")
                
                if r.status_code == 200:
                    result = r.json()
                    if result.get('success'):
                        print(f"   Question: {result.get('data', {}).get('question', 'N/A')}")
                        print(f"   Answer: {result.get('data', {}).get('answer', 'N/A')[:100]}...")
                        print(f"   Audio Response: {'✅' if result.get('data', {}).get('audio_url') else '❌'}")
                    else:
                        print(f"   Error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"   Error: {r.text}")
        except Exception as e:
            print(f"❌ Voice processing failed: {e}")
    else:
        print(f"\n📝 No sample audio file found at {sample_audio_path}")
        print("   Create a sample WAV file to test voice processing")

if __name__ == "__main__":
    test_agent_services()
    test_with_sample_audio()