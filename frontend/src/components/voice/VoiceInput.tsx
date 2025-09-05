import React, { useState, useCallback, useEffect } from 'react';
import {
  Mic,
  Send,
  Square,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useVoiceRecording } from '../../hooks/useVoiceRecording';
import { cn } from '../../utils';

interface VoiceInputProps {
  onVoiceInput?: (audioBlob: Blob, transcript?: string) => void;
  onTranscriptChange?: (transcript: string) => void;
  onError?: (error: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  showTranscript?: boolean;
  autoSend?: boolean;
  maxDuration?: number;
  silenceTimeout?: number;
}

interface VoiceActivityIndicatorProps {
  level: number;
  isActive: boolean;
  className?: string;
}

const VoiceActivityIndicator: React.FC<VoiceActivityIndicatorProps> = ({
  level,
  isActive,
  className,
}) => {
  const rings = Array.from({ length: 3 }, (_, i) => {
    const scale = 1 + (level * 0.5 * (i + 1));
    const opacity = isActive ? Math.max(0.2, level * (1 - i * 0.2)) : 0.2;
    
    return (
      <div
        key={i}
        className={cn(
          'absolute inset-0 rounded-full border-2 border-blue-500 transition-all duration-200',
          isActive && 'animate-pulse'
        )}
        style={{
          transform: `scale(${scale})`,
          opacity,
          animationDelay: `${i * 100}ms`,
        }}
      />
    );
  });

  return (
    <div className={cn('relative w-16 h-16', className)}>
      {rings}
      <div className="absolute inset-2 bg-blue-500 rounded-full flex items-center justify-center">
        <Mic className="w-6 h-6 text-white" />
      </div>
    </div>
  );
};

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onVoiceInput,
  onTranscriptChange,
  onError,
  placeholder = "Click to start voice input...",
  disabled = false,
  className,
  showTranscript = true,
  autoSend = false,
  maxDuration = 60,
  silenceTimeout = 2000,
}) => {
  const [transcript, setTranscript] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptionError, setTranscriptionError] = useState<string | null>(null);
  
  const {
    state,
    startRecording,
    stopRecording,
    clearRecording,
  } = useVoiceRecording({
    maxDuration,
    silenceTimeout,
    voiceActivityThreshold: 0.01,
  });

  // Handle recording completion
  useEffect(() => {
    if (state.audioBlob && !state.isRecording) {
      handleTranscription(state.audioBlob);
    }
  }, [state.audioBlob, state.isRecording]);

  // Handle errors
  useEffect(() => {
    if (state.error) {
      onError?.(state.error);
    }
  }, [state.error, onError]);

  // Transcription function using Speech-to-Text API
  const handleTranscription = useCallback(async (audioBlob: Blob) => {
    setIsTranscribing(true);
    setTranscriptionError(null);
    
    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'voice-input.webm', { type: 'audio/webm' });
      
      // Import speech service dynamically to avoid circular dependencies
      const { speechService } = await import('../../services/speechService');
      
      // Perform transcription
      const result = await speechService.transcribeAudio(audioFile, {
        languageCode: 'en-US',
        enableAutomaticPunctuation: true,
        enableWordTimestamps: false,
        model: 'latest_short'
      });
      
      setTranscript(result.transcript);
      onTranscriptChange?.(result.transcript);
      
      if (autoSend) {
        onVoiceInput?.(audioBlob, result.transcript);
        setTranscript('');
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Transcription failed';
      setTranscriptionError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsTranscribing(false);
    }
  }, [onTranscriptChange, onVoiceInput, autoSend, onError]);

  // Start voice input
  const handleStartRecording = useCallback(async () => {
    setTranscript('');
    setTranscriptionError(null);
    clearRecording();
    await startRecording();
  }, [startRecording, clearRecording]);

  // Stop voice input
  const handleStopRecording = useCallback(() => {
    stopRecording();
  }, [stopRecording]);

  // Send voice input
  const handleSend = useCallback(() => {
    if (state.audioBlob && transcript) {
      onVoiceInput?.(state.audioBlob, transcript);
      setTranscript('');
      clearRecording();
    }
  }, [state.audioBlob, transcript, onVoiceInput, clearRecording]);

  // Clear input
  const handleClear = useCallback(() => {
    setTranscript('');
    setTranscriptionError(null);
    clearRecording();
  }, [clearRecording]);

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get audio level indicator
  const getAudioLevelColor = () => {
    if (state.audioLevel > 0.7) return 'text-red-500';
    if (state.audioLevel > 0.3) return 'text-green-500';
    if (state.audioLevel > 0.05) return 'text-yellow-500';
    return 'text-gray-400';
  };

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Voice Input Area */}
      <div className="p-4">
        <div className="flex items-center space-x-4">
          {/* Voice Activity Indicator */}
          {state.isRecording ? (
            <VoiceActivityIndicator
              level={state.audioLevel}
              isActive={state.isRecording}
              className="flex-shrink-0"
            />
          ) : (
            <button
              onClick={handleStartRecording}
              disabled={disabled || state.isProcessing}
              className={cn(
                'flex items-center justify-center w-16 h-16 rounded-full transition-all duration-200',
                'bg-blue-500 hover:bg-blue-600 text-white shadow-lg hover:shadow-xl',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                state.isProcessing && 'animate-pulse'
              )}
              title="Start voice input"
            >
              <Mic className="w-6 h-6" />
            </button>
          )}

          {/* Status and Controls */}
          <div className="flex-1">
            {state.isRecording ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium text-red-600">Recording...</span>
                  </div>
                  <span className="text-sm text-gray-600 font-mono">
                    {formatDuration(state.duration)}
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  {state.audioLevel > 0.05 ? (
                    <Volume2 className={cn('w-4 h-4', getAudioLevelColor())} />
                  ) : (
                    <VolumeX className="w-4 h-4 text-gray-400" />
                  )}
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 bg-blue-500 rounded-full transition-all duration-100"
                      style={{ width: `${Math.min(100, state.audioLevel * 100)}%` }}
                    />
                  </div>
                </div>
                
                <button
                  onClick={handleStopRecording}
                  className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors duration-200"
                >
                  <Square className="w-4 h-4 inline mr-2" />
                  Stop Recording
                </button>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-600 text-sm">{placeholder}</p>
                {state.duration > 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    Last recording: {formatDuration(state.duration)}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Transcription Status */}
      {isTranscribing && (
        <div className="px-4 py-3 border-t bg-blue-50">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            <span className="text-sm text-blue-700">Transcribing audio...</span>
          </div>
        </div>
      )}

      {/* Transcript Display */}
      {showTranscript && transcript && (
        <div className="px-4 py-3 border-t">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">Transcript:</label>
              <button
                onClick={handleClear}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            </div>
            
            <div className="bg-gray-50 rounded-md p-3">
              <p className="text-sm text-gray-900">{transcript}</p>
            </div>
            
            {!autoSend && (
              <div className="flex space-x-2">
                <button
                  onClick={handleSend}
                  disabled={!state.audioBlob || !transcript}
                  className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-md transition-colors duration-200 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4 inline mr-2" />
                  Send Voice Input
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {(state.error || transcriptionError) && (
        <div className="px-4 py-3 border-t bg-red-50">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-700">
              {state.error || transcriptionError}
            </span>
          </div>
        </div>
      )}

      {/* Processing Status */}
      {state.isProcessing && (
        <div className="px-4 py-3 border-t bg-blue-50">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            <span className="text-sm text-blue-700">Initializing microphone...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceInput;