import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Trash2,
  MessageCircle,
  User,
  Bot,
  Play,
  Pause,
  Loader2,
} from 'lucide-react';
import { VoiceInput } from './VoiceInput';
import { speechService } from '../../services/speechService';
import { cn } from '../../lib/utils';

interface VoiceQAProps {
  documentId: string;
  sessionId?: string;
  onSessionChange?: (sessionId: string) => void;
  onError?: (error: string) => void;
  className?: string;
  autoPlayResponses?: boolean;
  showTranscripts?: boolean;
  voiceSettings?: {
    voiceGender?: 'MALE' | 'FEMALE' | 'NEUTRAL';
    speakingRate?: number;
    languageCode?: string;
  };
}

interface QAInteraction {
  id: string;
  timestamp: string;
  question: string;
  answer: string;
  confidence: number;
  audioResponse?: string; // base64 audio
  processingTime: number;
  isPlaying?: boolean;
}

interface QASession {
  sessionId: string;
  interactions: QAInteraction[];
  isActive: boolean;
}

export const VoiceQA: React.FC<VoiceQAProps> = ({
  documentId,
  sessionId,
  onSessionChange,
  onError,
  className,
  autoPlayResponses = true,
  showTranscripts = true,
  voiceSettings = {},
}) => {
  const [session, setSession] = useState<QASession>({
    sessionId: sessionId || `session_${Date.now()}`,
    interactions: [],
    isActive: false,
  });
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  
  const audioElementsRef = useRef<Map<string, HTMLAudioElement>>(new Map());
  const conversationEndRef = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    if (sessionId && sessionId !== session.sessionId) {
      setSession(prev => ({ ...prev, sessionId }));
    }
    onSessionChange?.(session.sessionId);
  }, [sessionId, session.sessionId, onSessionChange]);

  // Load suggested questions
  useEffect(() => {
    loadSuggestedQuestions();
  }, [documentId]);

  // Scroll to bottom when new interactions are added
  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [session.interactions]);

  // Load suggested questions
  const loadSuggestedQuestions = useCallback(async () => {
    try {
      // This would call the API to get suggested questions
      // For now, use static suggestions
      const questions = [
        "What are the main obligations in this document?",
        "What are the key risks I should be aware of?",
        "Are there any important deadlines?",
        "What are the payment terms?",
        "Can I terminate this agreement early?",
        "What happens if I breach this contract?",
      ];
      setSuggestedQuestions(questions);
    } catch (error) {
      console.error('Failed to load suggested questions:', error);
    }
  }, [documentId]);

  // Handle voice input
  const handleVoiceInput = useCallback(async (audioBlob: Blob) => {
    if (!audioBlob) return;

    setIsProcessing(true);
    setShowSuggestions(false);

    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'question.webm', { type: 'audio/webm' });
      
      // Create form data
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('document_id', documentId);
      formData.append('session_id', session.sessionId);
      formData.append('language_code', voiceSettings.languageCode || 'en-US');
      formData.append('voice_gender', voiceSettings.voiceGender || 'NEUTRAL');
      formData.append('speaking_rate', (voiceSettings.speakingRate || 1.0).toString());

      // Call Q&A API
      const response = await fetch('/api/v1/qa/ask-voice', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const result = await response.json();
      const qaData = result.data;

      // Create new interaction
      const interaction: QAInteraction = {
        id: `interaction_${Date.now()}`,
        timestamp: new Date().toISOString(),
        question: qaData.question,
        answer: qaData.answer,
        confidence: qaData.confidence,
        audioResponse: qaData.audio_response?.audio_content_base64,
        processingTime: qaData.processing_time,
      };

      // Add to session
      setSession(prev => ({
        ...prev,
        interactions: [...prev.interactions, interaction],
        isActive: true,
      }));

      // Auto-play response if enabled
      if (autoPlayResponses && interaction.audioResponse) {
        setTimeout(() => {
          playAudioResponse(interaction.id, interaction.audioResponse!);
        }, 500);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process voice question';
      onError?.(errorMessage);
      console.error('Voice Q&A error:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [documentId, session.sessionId, voiceSettings, autoPlayResponses, onError]);

  // Handle text question
  const handleTextQuestion = useCallback(async (question: string) => {
    if (!question.trim()) return;

    setIsProcessing(true);
    setShowSuggestions(false);

    try {
      const response = await fetch('/api/v1/qa/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          question: question.trim(),
          document_id: documentId,
          session_id: session.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const result = await response.json();
      const qaData = result.data;

      // Create new interaction
      const interaction: QAInteraction = {
        id: `interaction_${Date.now()}`,
        timestamp: new Date().toISOString(),
        question: qaData.question,
        answer: qaData.answer,
        confidence: qaData.confidence,
        processingTime: qaData.processing_time,
      };

      // Add to session
      setSession(prev => ({
        ...prev,
        interactions: [...prev.interactions, interaction],
        isActive: true,
      }));

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process text question';
      onError?.(errorMessage);
      console.error('Text Q&A error:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [documentId, session.sessionId, onError]);

  // Play audio response
  const playAudioResponse = useCallback((interactionId: string, audioBase64: string) => {
    try {
      // Stop any currently playing audio
      audioElementsRef.current.forEach((audio, id) => {
        if (id !== interactionId) {
          audio.pause();
        }
      });

      let audio = audioElementsRef.current.get(interactionId);
      
      if (!audio) {
        const audioBlob = speechService.base64ToBlob(audioBase64, 'audio/mpeg');
        const audioUrl = URL.createObjectURL(audioBlob);
        
        audio = new Audio(audioUrl);
        audio.onended = () => setCurrentlyPlaying(null);
        audio.onpause = () => setCurrentlyPlaying(null);
        audio.onplay = () => setCurrentlyPlaying(interactionId);
        
        audioElementsRef.current.set(interactionId, audio);
      }

      if (currentlyPlaying === interactionId) {
        audio.pause();
      } else {
        audio.play();
      }
    } catch (error) {
      console.error('Audio playback error:', error);
      onError?.('Failed to play audio response');
    }
  }, [currentlyPlaying, onError]);

  // Clear session
  const clearSession = useCallback(async () => {
    try {
      // Stop all audio
      audioElementsRef.current.forEach(audio => {
        audio.pause();
        URL.revokeObjectURL(audio.src);
      });
      audioElementsRef.current.clear();
      setCurrentlyPlaying(null);

      // Clear session on server
      await fetch(`/api/v1/qa/sessions/${documentId}/clear?session_id=${session.sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      // Reset local session
      setSession(prev => ({
        ...prev,
        interactions: [],
        isActive: false,
      }));
      
      setShowSuggestions(true);

    } catch (error) {
      console.error('Failed to clear session:', error);
      onError?.('Failed to clear conversation');
    }
  }, [documentId, session.sessionId, onError]);

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm flex flex-col h-full', className)}>
      {/* Header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <MessageCircle className="w-6 h-6 text-blue-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Voice Q&A</h3>
              <p className="text-sm text-gray-600">
                Ask questions about your document using voice or text
              </p>
            </div>
          </div>
          
          {session.interactions.length > 0 && (
            <button
              onClick={clearSession}
              className="p-2 text-gray-400 hover:text-red-500 rounded-md hover:bg-gray-100 transition-colors"
              title="Clear conversation"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Suggested Questions */}
        {showSuggestions && suggestedQuestions.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-3">
              Suggested Questions:
            </h4>
            <div className="space-y-2">
              {suggestedQuestions.slice(0, 4).map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleTextQuestion(question)}
                  disabled={isProcessing}
                  className="w-full text-left p-2 text-sm text-blue-700 hover:bg-blue-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Conversation History */}
        {session.interactions.map((interaction) => (
          <div key={interaction.id} className="space-y-4">
            {/* User Question */}
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 bg-blue-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900">You</span>
                  <span className="text-xs text-blue-600">
                    {formatTimestamp(interaction.timestamp)}
                  </span>
                </div>
                {showTranscripts && (
                  <p className="text-sm text-blue-800">{interaction.question}</p>
                )}
              </div>
            </div>

            {/* AI Response */}
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 bg-green-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-green-900">AI Assistant</span>
                    <span className={cn('text-xs', getConfidenceColor(interaction.confidence))}>
                      {Math.round(interaction.confidence * 100)}% confident
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-green-600">
                      {interaction.processingTime.toFixed(1)}s
                    </span>
                    {interaction.audioResponse && (
                      <button
                        onClick={() => playAudioResponse(interaction.id, interaction.audioResponse!)}
                        className="p-1 text-green-600 hover:text-green-800 rounded transition-colors"
                        title={currentlyPlaying === interaction.id ? 'Pause' : 'Play audio'}
                      >
                        {currentlyPlaying === interaction.id ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
                {showTranscripts && (
                  <p className="text-sm text-green-800 whitespace-pre-wrap">
                    {interaction.answer}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center space-x-3 text-blue-600">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span className="text-sm">Processing your question...</span>
            </div>
          </div>
        )}

        <div ref={conversationEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <VoiceInput
          onVoiceInput={handleVoiceInput}
          onError={onError}
          disabled={isProcessing}
          placeholder="Ask a question about your document..."
          autoSend={true}
          maxDuration={30}
          silenceTimeout={2000}
          showTranscript={false}
        />
      </div>

      {/* Status Bar */}
      <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span>Session: {session.sessionId.slice(-8)}</span>
            <span>{session.interactions.length} interactions</span>
          </div>
          <div className="flex items-center space-x-2">
            {session.isActive && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Active</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceQA;