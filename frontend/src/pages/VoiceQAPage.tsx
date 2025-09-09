import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Mic, 
  MicOff, 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  MessageCircle, 
  FileText,
  Trash2,
  Download
} from 'lucide-react';

interface VoiceQASession {
  id: string;
  document_id: string;
  interactions: Array<{
    id: string;
    question: string;
    answer: string;
    audio_question?: string;
    audio_answer?: string;
    timestamp: string;
    confidence: number;
  }>;
}

interface Document {
  id: string;
  filename: string;
  summary?: {
    document_type: string;
  };
}

const VoiceQAPage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const documentId = searchParams.get('document');
  
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string>(documentId || '');
  const [session, setSession] = useState<VoiceQASession | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [language, setLanguage] = useState('en-US');
  const [voiceSettings, setVoiceSettings] = useState({
    gender: 'NEUTRAL',
    speed: 1.0,
    pitch: 0.0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!currentUser) {
      navigate('/login');
      return;
    }
    
    fetchDocuments();
    if (selectedDocument) {
      initializeSession();
    }
  }, [currentUser, selectedDocument, navigate]);

  const fetchDocuments = async () => {
    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch('/api/v1/documents', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const initializeSession = async () => {
    if (!selectedDocument) return;
    
    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch(`/api/v1/qa/sessions/${selectedDocument}/history?session_id=default`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSession(data.data);
      } else {
        // Create new session
        setSession({
          id: 'default',
          document_id: selectedDocument,
          interactions: []
        });
      }
    } catch (err) {
      console.error('Failed to initialize session:', err);
      setSession({
        id: 'default',
        document_id: selectedDocument,
        interactions: []
      });
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processVoiceQuestion(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setError(null);
    } catch (err) {
      setError('Failed to access microphone. Please check permissions.');
      console.error('Recording error:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processVoiceQuestion = async (audioBlob: Blob) => {
    if (!selectedDocument) return;
    
    setLoading(true);
    try {
      const token = await currentUser?.getIdToken();
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'question.wav');
      formData.append('document_id', selectedDocument);
      formData.append('session_id', session?.id || 'default');
      formData.append('language_code', language);
      formData.append('voice_gender', voiceSettings.gender);
      formData.append('speaking_rate', voiceSettings.speed.toString());

      const response = await fetch('/api/v1/qa/ask-voice', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const newInteraction = {
          id: Date.now().toString(),
          question: data.data.question,
          answer: data.data.answer,
          audio_answer: data.data.audio_response?.url,
          timestamp: new Date().toISOString(),
          confidence: data.data.confidence
        };

        setSession(prev => prev ? {
          ...prev,
          interactions: [...prev.interactions, newInteraction]
        } : null);

        // Auto-play response if not muted
        if (!isMuted && data.data.audio_response?.url) {
          playAudio(data.data.audio_response.url);
        }
      } else {
        throw new Error('Failed to process voice question');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process voice question');
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (audioUrl: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    
    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    
    audio.play();
    setIsPlaying(audioUrl);
    
    audio.onended = () => {
      setIsPlaying(null);
    };
    
    audio.onerror = () => {
      setIsPlaying(null);
      setError('Failed to play audio response');
    };
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(null);
    }
  };

  const clearSession = async () => {
    if (!selectedDocument || !session) return;
    
    try {
      const token = await currentUser?.getIdToken();
      await fetch(`/api/v1/qa/sessions/${selectedDocument}/clear?session_id=${session.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      setSession({
        ...session,
        interactions: []
      });
    } catch (err) {
      console.error('Failed to clear session:', err);
    }
  };

  const exportConversation = () => {
    if (!session) return;
    
    const content = session.interactions.map(interaction => 
      `Q: ${interaction.question}\nA: ${interaction.answer}\n---\n`
    ).join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-qa-session-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const selectedDoc = documents.find(doc => doc.id === selectedDocument);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Voice Q&A</h1>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsMuted(!isMuted)}
                className={`p-2 rounded-md ${isMuted ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}
              >
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
              <button
                onClick={exportConversation}
                disabled={!session?.interactions.length}
                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
              <button
                onClick={clearSession}
                disabled={!session?.interactions.length}
                className="flex items-center px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear
              </button>
            </div>
          </div>

          {/* Document Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Document
            </label>
            <select
              value={selectedDocument}
              onChange={(e) => setSelectedDocument(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose a document...</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename} {doc.summary?.document_type && `(${doc.summary.document_type})`}
                </option>
              ))}
            </select>
          </div>

          {selectedDoc && (
            <div className="flex items-center text-sm text-gray-600">
              <FileText className="w-4 h-4 mr-2" />
              <span>Selected: {selectedDoc.filename}</span>
            </div>
          )}
        </div>

        {/* Voice Controls */}
        {selectedDocument && (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <div className="text-center">
              <div className="mb-6">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={loading}
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                    isRecording 
                      ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                      : 'bg-blue-500 hover:bg-blue-600'
                  } text-white disabled:opacity-50`}
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                  ) : isRecording ? (
                    <MicOff className="w-8 h-8" />
                  ) : (
                    <Mic className="w-8 h-8" />
                  )}
                </button>
              </div>
              
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isRecording ? 'Recording... Click to stop' : 'Click to ask a question'}
              </p>
              <p className="text-sm text-gray-600">
                {loading ? 'Processing your question...' : 'Speak naturally about the document'}
              </p>
            </div>

            {/* Settings */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="en-US">English (US)</option>
                    <option value="en-GB">English (UK)</option>
                    <option value="es-ES">Spanish</option>
                    <option value="fr-FR">French</option>
                    <option value="de-DE">German</option>
                    <option value="it-IT">Italian</option>
                    <option value="pt-BR">Portuguese</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Voice Gender
                  </label>
                  <select
                    value={voiceSettings.gender}
                    onChange={(e) => setVoiceSettings(prev => ({ ...prev, gender: e.target.value }))}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="NEUTRAL">Neutral</option>
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Speaking Speed
                  </label>
                  <select
                    value={voiceSettings.speed}
                    onChange={(e) => setVoiceSettings(prev => ({ ...prev, speed: parseFloat(e.target.value) }))}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="0.75">Slow</option>
                    <option value="1.0">Normal</option>
                    <option value="1.25">Fast</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Conversation History */}
        {session && session.interactions.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Conversation History</h2>
            </div>
            <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
              {session.interactions.map((interaction) => (
                <div key={interaction.id} className="space-y-3">
                  {/* Question */}
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <MessageCircle className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-900 font-medium">You asked:</p>
                      <p className="text-gray-700 mt-1">{interaction.question}</p>
                    </div>
                  </div>

                  {/* Answer */}
                  <div className="flex items-start space-x-3 ml-11">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <FileText className="w-4 h-4 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-gray-900 font-medium">Legal Companion:</p>
                        {interaction.audio_answer && (
                          <button
                            onClick={() => 
                              isPlaying === interaction.audio_answer 
                                ? pauseAudio() 
                                : playAudio(interaction.audio_answer!)
                            }
                            className="flex items-center text-blue-600 hover:text-blue-700"
                          >
                            {isPlaying === interaction.audio_answer ? (
                              <Pause className="w-4 h-4 mr-1" />
                            ) : (
                              <Play className="w-4 h-4 mr-1" />
                            )}
                            {isPlaying === interaction.audio_answer ? 'Pause' : 'Play'}
                          </button>
                        )}
                      </div>
                      <p className="text-gray-700 mt-1">{interaction.answer}</p>
                      <div className="flex items-center mt-2 text-xs text-gray-500">
                        <span>Confidence: {Math.round(interaction.confidence * 100)}%</span>
                        <span className="mx-2">•</span>
                        <span>{new Date(interaction.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <hr className="border-gray-200" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {selectedDocument && session && session.interactions.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
            <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Start a Conversation</h3>
            <p className="text-gray-600 mb-6">
              Click the microphone button above to ask your first question about this document.
            </p>
            <div className="bg-blue-50 rounded-lg p-4 text-left max-w-md mx-auto">
              <h4 className="font-medium text-blue-900 mb-2">Try asking:</h4>
              <ul className="text-blue-800 text-sm space-y-1">
                <li>• "What are the main terms of this agreement?"</li>
                <li>• "Are there any risks I should know about?"</li>
                <li>• "What are my obligations under this contract?"</li>
                <li>• "Can you explain this in simple terms?"</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceQAPage;