# 🤖 AI Agents Setup - Murf, AssemblyAI & Gemini

## 🚀 **Complete AI Agent System Added!**

Your Legal Companion now has a full AI agent system with:
- **🎤 AssemblyAI**: Speech-to-text transcription
- **🤖 Gemini**: Intelligent text generation and document analysis
- **🔊 Murf**: High-quality text-to-speech

## 📋 **API Keys Required:**

### **1. Murf AI (Text-to-Speech)**
- Sign up: https://murf.ai/
- Get API key from dashboard
- Add to `.env`: `MURF_API_KEY=your-murf-api-key`

### **2. AssemblyAI (Speech-to-Text)**
- Sign up: https://www.assemblyai.com/
- Get API key from dashboard
- Add to `.env`: `ASSEMBLYAI_API_KEY=your-assemblyai-api-key`

### **3. Google Gemini (Text Generation)**
- Go to: https://makersuite.google.com/app/apikey
- Create API key
- Add to `.env`: `GEMINI_API_KEY=your-gemini-api-key`

## 🔧 **Installation:**

### **1. Install Dependencies:**
```bash
cd backend
pip install google-generativeai aiohttp
```

### **2. Update Environment:**
```env
# Add to backend/.env
MURF_API_KEY=your-murf-api-key-here
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

### **3. Restart Backend:**
```bash
cd backend/app
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 🎯 **New API Endpoints:**

### **Voice Processing Pipeline:**
```
POST /v1/agents/voice-question
- Upload audio file with question
- Returns: transcription + AI answer + speech audio
- Complete pipeline: Audio → Text → AI → Speech
```

### **Individual Services:**
```
POST /v1/agents/transcribe          # AssemblyAI transcription
POST /v1/agents/generate-text       # Gemini text generation  
POST /v1/agents/text-to-speech      # Murf TTS
POST /v1/agents/chat                # Chat with documents
GET  /v1/agents/voices              # Available Murf voices
GET  /v1/agents/status              # Service status
```

## 🧪 **Test the Agents:**

### **1. Check Agent Status:**
```bash
curl http://127.0.0.1:8000/v1/agents/status
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "services": {
      "murf_tts": true,
      "assemblyai_transcription": true, 
      "gemini_generation": true
    },
    "capabilities": {
      "voice_questions": true,
      "transcription": true,
      "text_generation": true,
      "text_to_speech": true
    }
  }
}
```

### **2. Test Text Generation:**
```bash
curl -X POST http://127.0.0.1:8000/v1/agents/generate-text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the key risks in a legal contract",
    "context": "This is a sample legal document..."
  }'
```

### **3. Test Voice Processing:**
```bash
curl -X POST http://127.0.0.1:8000/v1/agents/voice-question \
  -F "audio_file=@question.wav" \
  -F "document_id=doc_123" \
  -F "session_id=default"
```

## 🎭 **Available Murf Voices:**

### **English Voices:**
- `en-US-davis` - Male, professional
- `en-US-sarah` - Female, friendly
- `en-US-michael` - Male, authoritative
- `en-US-emma` - Female, clear

### **Get All Voices:**
```bash
curl http://127.0.0.1:8000/v1/agents/voices
```

## 🔄 **Complete Workflow:**

### **Voice Question Processing:**
1. **User speaks** → Audio recorded
2. **AssemblyAI** → Transcribes to text
3. **Gemini** → Analyzes document + generates answer
4. **Murf** → Converts answer to speech
5. **Response** → Text + Audio returned

### **Document Chat:**
1. **User types question** about document
2. **Gemini** → Analyzes document content
3. **AI Response** → Intelligent legal analysis
4. **Optional TTS** → Convert to speech

## 📊 **Integration with Frontend:**

### **Voice Questions:**
```typescript
// Frontend can now send audio files
const formData = new FormData();
formData.append('audio_file', audioBlob);
formData.append('document_id', documentId);

const response = await fetch('/api/v1/agents/voice-question', {
  method: 'POST',
  body: formData
});

const result = await response.json();
// result.data.question - transcribed text
// result.data.answer - AI response
// result.data.audio_url - speech audio
```

### **Text Chat:**
```typescript
// Chat with documents using AI
const response = await fetch('/api/v1/agents/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id: 'doc_123',
    question: 'What are the liability clauses?',
    session_id: 'default'
  })
});
```

## 🎯 **Use Cases:**

### **Legal Document Analysis:**
- **Voice Questions**: "What are the key risks in this contract?"
- **AI Analysis**: Intelligent legal clause identification
- **Spoken Responses**: Audio explanations of complex terms

### **Document Q&A:**
- **Natural Language**: Ask questions in plain English
- **Context Aware**: AI understands document content
- **Conversational**: Maintains chat history

### **Accessibility:**
- **Voice Interface**: Hands-free document interaction
- **Audio Responses**: For visually impaired users
- **Multi-modal**: Text + Voice + Visual

## 💰 **Pricing Estimates:**

### **AssemblyAI:**
- $0.00037 per second of audio
- ~$1.33 per hour of transcription

### **Murf AI:**
- ~$0.06 per minute of generated speech
- Various voice quality tiers

### **Google Gemini:**
- $0.00025 per 1K characters input
- $0.0005 per 1K characters output

## 🔒 **Security & Privacy:**

### **Data Handling:**
- Audio files processed in memory
- No permanent audio storage
- Conversation history saved locally
- API keys secured in environment

### **Best Practices:**
- Rotate API keys regularly
- Monitor usage and costs
- Implement rate limiting
- Validate all inputs

## 🚀 **Ready to Use:**

### **1. Add API Keys to `.env`**
### **2. Restart Backend Server**  
### **3. Test Agent Status**
### **4. Start Using Voice Features**

---

## 🎉 **Your Legal Companion now has full AI agent capabilities!**

**Voice questions → AI analysis → Spoken responses**
**Complete conversational AI for legal document analysis!** 🤖✨