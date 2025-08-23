import React, { useState, useEffect } from 'react';
import {
  Mic,
  MicOff,
  Square,
  Play,
  Pause,
  Download,
  Trash2,
  Volume2,
  VolumeX,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { useVoiceRecording, VoiceRecordingOptions } from '../../hooks/useVoiceRecording';
import { cn } from '../../lib/utils';

interface VoiceRecorderProps {
  onRecordingComplete?: (audioBlob: Blob, duration: number) => void;
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
  onError?: (error: string) => void;
  options?: VoiceRecordingOptions;
  disabled?: boolean;
  className?: string;
  showWaveform?: boolean;
  showDownload?: boolean;
  autoStart?: boolean;
  maxDuration?: number;
}

interface AudioVisualizerProps {
  audioLevel: number;
  isRecording: boolean;
  className?: string;
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioLevel,
  isRecording,
  className,
}) => {
  const bars = Array.from({ length: 20 }, (_, i) => {
    const height = Math.max(2, audioLevel * 40 + Math.random() * 5);
    const opacity = isRecording ? Math.min(1, audioLevel * 3 + 0.3) : 0.3;
    
    return (
      <div
        key={i}
        className={cn(
          'bg-blue-500 rounded-full transition-all duration-100',
          isRecording && 'animate-pulse'
        )}
        style={{
          height: `${height}px`,
          width: '3px',
          opacity,
          animationDelay: `${i * 50}ms`,
        }}
      />
    );
  });

  return (
    <div className={cn('flex items-center justify-center space-x-1 h-12', className)}>
      {bars}
    </div>
  );
};

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onRecordingComplete,
  onRecordingStart,
  onRecordingStop,
  onError,
  options,
  disabled = false,
  className,
  showWaveform = true,
  showDownload = true,
  autoStart = false,
  maxDuration = 300,
}) => {
  const {
    state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
    downloadRecording,
  } = useVoiceRecording({ ...options, maxDuration });

  const [isPlaying, setIsPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  // Handle recording completion
  useEffect(() => {
    if (state.audioBlob && !state.isRecording && onRecordingComplete) {
      onRecordingComplete(state.audioBlob, state.duration);
    }
  }, [state.audioBlob, state.isRecording, state.duration, onRecordingComplete]);

  // Handle recording start/stop callbacks
  useEffect(() => {
    if (state.isRecording && onRecordingStart) {
      onRecordingStart();
    } else if (!state.isRecording && onRecordingStop) {
      onRecordingStop();
    }
  }, [state.isRecording, onRecordingStart, onRecordingStop]);

  // Handle errors
  useEffect(() => {
    if (state.error && onError) {
      onError(state.error);
    }
  }, [state.error, onError]);

  // Auto-start recording
  useEffect(() => {
    if (autoStart && !state.isRecording && !state.audioBlob) {
      startRecording();
    }
  }, [autoStart, state.isRecording, state.audioBlob, startRecording]);

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle play/pause audio
  const handlePlayPause = () => {
    if (!state.audioUrl) return;

    if (!audioElement) {
      const audio = new Audio(state.audioUrl);
      audio.onended = () => setIsPlaying(false);
      audio.onpause = () => setIsPlaying(false);
      audio.onplay = () => setIsPlaying(true);
      setAudioElement(audio);
      audio.play();
    } else {
      if (isPlaying) {
        audioElement.pause();
      } else {
        audioElement.play();
      }
    }
  };

  // Get recording quality indicator
  const getQualityIndicator = () => {
    if (!state.isRecording) return null;
    
    if (state.audioLevel > 0.7) {
      return { icon: Volume2, color: 'text-red-500', label: 'Too loud' };
    } else if (state.audioLevel > 0.3) {
      return { icon: Volume2, color: 'text-green-500', label: 'Good' };
    } else if (state.audioLevel > 0.05) {
      return { icon: Volume2, color: 'text-yellow-500', label: 'Low' };
    } else {
      return { icon: VolumeX, color: 'text-gray-400', label: 'No input' };
    }
  };

  const qualityIndicator = getQualityIndicator();

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Voice Recorder</h3>
        {state.isRecording && (
          <div className="flex items-center space-x-2 text-sm text-red-600">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span>Recording</span>
          </div>
        )}
      </div>

      {/* Error Display */}
      {state.error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-700">{state.error}</span>
          </div>
        </div>
      )}

      {/* Audio Visualizer */}
      {showWaveform && (
        <div className="mb-6">
          <AudioVisualizer
            audioLevel={state.audioLevel}
            isRecording={state.isRecording}
            className="bg-gray-50 rounded-lg p-4"
          />
        </div>
      )}

      {/* Recording Info */}
      <div className="mb-6 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Duration:</span>
          <span className="font-mono text-gray-900">
            {formatDuration(state.duration)} / {formatDuration(maxDuration)}
          </span>
        </div>
        
        {qualityIndicator && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Audio Quality:</span>
            <div className="flex items-center space-x-1">
              <qualityIndicator.icon className={cn('w-4 h-4', qualityIndicator.color)} />
              <span className={qualityIndicator.color}>{qualityIndicator.label}</span>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={cn(
              'h-2 rounded-full transition-all duration-300',
              state.isRecording ? 'bg-red-500' : 'bg-blue-500'
            )}
            style={{ width: `${Math.min(100, (state.duration / maxDuration) * 100)}%` }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center space-x-4">
        {!state.isRecording && !state.audioBlob && (
          <button
            onClick={startRecording}
            disabled={disabled || state.isProcessing}
            className={cn(
              'flex items-center justify-center w-16 h-16 rounded-full transition-all duration-200',
              'bg-red-500 hover:bg-red-600 text-white shadow-lg hover:shadow-xl',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              state.isProcessing && 'animate-pulse'
            )}
            title="Start recording"
          >
            <Mic className="w-6 h-6" />
          </button>
        )}

        {state.isRecording && (
          <>
            <button
              onClick={pauseRecording}
              className="flex items-center justify-center w-12 h-12 rounded-full bg-yellow-500 hover:bg-yellow-600 text-white shadow-lg hover:shadow-xl transition-all duration-200"
              title="Pause recording"
            >
              <Pause className="w-5 h-5" />
            </button>
            
            <button
              onClick={stopRecording}
              className="flex items-center justify-center w-16 h-16 rounded-full bg-gray-600 hover:bg-gray-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
              title="Stop recording"
            >
              <Square className="w-6 h-6" />
            </button>
          </>
        )}

        {state.audioBlob && (
          <>
            <button
              onClick={handlePlayPause}
              className="flex items-center justify-center w-12 h-12 rounded-full bg-green-500 hover:bg-green-600 text-white shadow-lg hover:shadow-xl transition-all duration-200"
              title={isPlaying ? 'Pause playback' : 'Play recording'}
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>

            {showDownload && (
              <button
                onClick={downloadRecording}
                className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-500 hover:bg-blue-600 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                title="Download recording"
              >
                <Download className="w-5 h-5" />
              </button>
            )}

            <button
              onClick={clearRecording}
              className="flex items-center justify-center w-12 h-12 rounded-full bg-red-500 hover:bg-red-600 text-white shadow-lg hover:shadow-xl transition-all duration-200"
              title="Delete recording"
            >
              <Trash2 className="w-5 h-5" />
            </button>

            <button
              onClick={startRecording}
              disabled={disabled || state.isProcessing}
              className="flex items-center justify-center w-12 h-12 rounded-full bg-gray-500 hover:bg-gray-600 text-white shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Record again"
            >
              <Mic className="w-5 h-5" />
            </button>
          </>
        )}
      </div>

      {/* Recording Status */}
      {state.audioBlob && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-sm text-green-700">
              Recording completed ({formatDuration(state.duration)})
            </span>
          </div>
        </div>
      )}

      {/* Processing Status */}
      {state.isProcessing && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-blue-700">Initializing recording...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;