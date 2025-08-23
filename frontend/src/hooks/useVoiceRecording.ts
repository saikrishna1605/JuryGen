import { useState, useRef, useCallback, useEffect } from 'react';

export interface VoiceRecordingState {
  isRecording: boolean;
  isProcessing: boolean;
  audioLevel: number;
  duration: number;
  error: string | null;
  audioBlob: Blob | null;
  audioUrl: string | null;
}

export interface VoiceRecordingOptions {
  maxDuration?: number; // in seconds
  sampleRate?: number;
  channels?: number;
  mimeType?: string;
  voiceActivityThreshold?: number;
  silenceTimeout?: number; // in ms
}

export interface UseVoiceRecordingReturn {
  state: VoiceRecordingState;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  clearRecording: () => void;
  downloadRecording: () => void;
}

const DEFAULT_OPTIONS: Required<VoiceRecordingOptions> = {
  maxDuration: 300, // 5 minutes
  sampleRate: 44100,
  channels: 1,
  mimeType: 'audio/webm;codecs=opus',
  voiceActivityThreshold: 0.01,
  silenceTimeout: 3000, // 3 seconds
};

export const useVoiceRecording = (
  options: VoiceRecordingOptions = {}
): UseVoiceRecordingReturn => {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  const [state, setState] = useState<VoiceRecordingState>({
    isRecording: false,
    isProcessing: false,
    audioLevel: 0,
    duration: 0,
    error: null,
    audioBlob: null,
    audioUrl: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioLevelIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Check if browser supports required APIs
  const isSupported = useCallback(() => {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.MediaRecorder &&
      window.AudioContext
    );
  }, []);

  // Get supported MIME types
  const getSupportedMimeType = useCallback(() => {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
      'audio/wav',
    ];
    
    return types.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';
  }, []);

  // Initialize audio context and analyser
  const initializeAudioAnalysis = useCallback((stream: MediaStream) => {
    try {
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      return true;
    } catch (error) {
      console.error('Failed to initialize audio analysis:', error);
      return false;
    }
  }, []);

  // Calculate audio level
  const calculateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return 0;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    
    return sum / bufferLength / 255; // Normalize to 0-1
  }, []);

  // Start monitoring audio levels
  const startAudioLevelMonitoring = useCallback(() => {
    if (audioLevelIntervalRef.current) {
      clearInterval(audioLevelIntervalRef.current);
    }
    
    audioLevelIntervalRef.current = setInterval(() => {
      const level = calculateAudioLevel();
      setState(prev => ({ ...prev, audioLevel: level }));
      
      // Voice activity detection
      if (level > opts.voiceActivityThreshold) {
        // Reset silence timeout when voice is detected
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      } else if (!silenceTimeoutRef.current && state.isRecording) {
        // Start silence timeout
        silenceTimeoutRef.current = setTimeout(() => {
          console.log('Silence detected, stopping recording');
          stopRecording();
        }, opts.silenceTimeout);
      }
    }, 100);
  }, [calculateAudioLevel, opts.voiceActivityThreshold, opts.silenceTimeout, state.isRecording]);

  // Start duration tracking
  const startDurationTracking = useCallback(() => {
    startTimeRef.current = Date.now();
    
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }
    
    durationIntervalRef.current = setInterval(() => {
      const duration = (Date.now() - startTimeRef.current) / 1000;
      setState(prev => ({ ...prev, duration }));
      
      // Auto-stop at max duration
      if (duration >= opts.maxDuration) {
        stopRecording();
      }
    }, 100);
  }, [opts.maxDuration]);

  // Start recording
  const startRecording = useCallback(async () => {
    if (!isSupported()) {
      setState(prev => ({
        ...prev,
        error: 'Voice recording is not supported in this browser',
      }));
      return;
    }

    try {
      setState(prev => ({ ...prev, isProcessing: true, error: null }));

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: opts.sampleRate,
          channelCount: opts.channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      // Initialize audio analysis
      if (!initializeAudioAnalysis(stream)) {
        throw new Error('Failed to initialize audio analysis');
      }

      // Create MediaRecorder
      const mimeType = getSupportedMimeType();
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Set up event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: mimeType });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        setState(prev => ({
          ...prev,
          audioBlob,
          audioUrl,
          isRecording: false,
          isProcessing: false,
        }));
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setState(prev => ({
          ...prev,
          error: 'Recording failed',
          isRecording: false,
          isProcessing: false,
        }));
      };

      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms
      
      setState(prev => ({
        ...prev,
        isRecording: true,
        isProcessing: false,
        duration: 0,
        audioLevel: 0,
      }));

      // Start monitoring
      startDurationTracking();
      startAudioLevelMonitoring();

    } catch (error) {
      console.error('Failed to start recording:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to start recording',
        isProcessing: false,
      }));
    }
  }, [
    isSupported,
    opts.sampleRate,
    opts.channels,
    getSupportedMimeType,
    initializeAudioAnalysis,
    startDurationTracking,
    startAudioLevelMonitoring,
  ]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.stop();
    }

    // Clean up intervals and timeouts
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }
    
    if (audioLevelIntervalRef.current) {
      clearInterval(audioLevelIntervalRef.current);
      audioLevelIntervalRef.current = null;
    }
    
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setState(prev => ({ ...prev, audioLevel: 0 }));
  }, [state.isRecording]);

  // Pause recording
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.pause();
      
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
      
      if (audioLevelIntervalRef.current) {
        clearInterval(audioLevelIntervalRef.current);
        audioLevelIntervalRef.current = null;
      }
    }
  }, [state.isRecording]);

  // Resume recording
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.resume();
      startDurationTracking();
      startAudioLevelMonitoring();
    }
  }, [state.isRecording, startDurationTracking, startAudioLevelMonitoring]);

  // Clear recording
  const clearRecording = useCallback(() => {
    if (state.audioUrl) {
      URL.revokeObjectURL(state.audioUrl);
    }
    
    setState(prev => ({
      ...prev,
      audioBlob: null,
      audioUrl: null,
      duration: 0,
      error: null,
    }));
    
    chunksRef.current = [];
  }, [state.audioUrl]);

  // Download recording
  const downloadRecording = useCallback(() => {
    if (state.audioBlob && state.audioUrl) {
      const link = document.createElement('a');
      link.href = state.audioUrl;
      link.download = `voice-recording-${new Date().toISOString()}.webm`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, [state.audioBlob, state.audioUrl]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (state.audioUrl) {
        URL.revokeObjectURL(state.audioUrl);
      }
    };
  }, []);

  return {
    state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    clearRecording,
    downloadRecording,
  };
};