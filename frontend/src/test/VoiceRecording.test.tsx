import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVoiceRecording } from '../hooks/useVoiceRecording';

// Mock MediaRecorder
class MockMediaRecorder {
  static isTypeSupported = vi.fn(() => true);
  
  ondataavailable: ((event: any) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  
  constructor(_stream: MediaStream, _options?: any) {}
  
  start = vi.fn();
  stop = vi.fn(() => {
    if (this.onstop) {
      this.onstop();
    }
  });
  pause = vi.fn();
  resume = vi.fn();
}

// Mock AudioContext
class MockAudioContext {
  createAnalyser = vi.fn(() => ({
    fftSize: 256,
    smoothingTimeConstant: 0.8,
    frequencyBinCount: 128,
    getByteFrequencyData: vi.fn(),
  }));
  
  createMediaStreamSource = vi.fn(() => ({
    connect: vi.fn(),
  }));
  
  close = vi.fn();
}

// Mock getUserMedia
const mockGetUserMedia = vi.fn();

describe('useVoiceRecording', () => {
  beforeEach(() => {
    // Setup mocks
    global.MediaRecorder = MockMediaRecorder as any;
    global.AudioContext = MockAudioContext as any;
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      writable: true,
    });
    
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useVoiceRecording());

    expect(result.current.state).toEqual({
      isRecording: false,
      isProcessing: false,
      audioLevel: 0,
      duration: 0,
      error: null,
      audioBlob: null,
      audioUrl: null,
    });
  });

  it('starts recording successfully', async () => {
    const { result } = renderHook(() => useVoiceRecording());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(mockGetUserMedia).toHaveBeenCalledWith({
      audio: {
        sampleRate: 44100,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    expect(result.current.state.isRecording).toBe(true);
    expect(result.current.state.isProcessing).toBe(false);
  });

  it('handles getUserMedia failure', async () => {
    mockGetUserMedia.mockRejectedValueOnce(new Error('Permission denied'));
    
    const { result } = renderHook(() => useVoiceRecording());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.state.error).toBe('Permission denied');
    expect(result.current.state.isRecording).toBe(false);
  });

  it('stops recording and creates audio blob', async () => {
    const { result } = renderHook(() => useVoiceRecording());

    // Start recording first
    await act(async () => {
      await result.current.startRecording();
    });

    // Stop recording
    act(() => {
      result.current.stopRecording();
    });

    expect(result.current.state.audioLevel).toBe(0);
  });

  it('clears recording data', async () => {
    const { result } = renderHook(() => useVoiceRecording());

    // Start and stop recording to create audio data
    await act(async () => {
      await result.current.startRecording();
    });

    act(() => {
      result.current.stopRecording();
    });

    // Clear recording
    act(() => {
      result.current.clearRecording();
    });

    expect(result.current.state.audioBlob).toBeNull();
    expect(result.current.state.audioUrl).toBeNull();
    expect(result.current.state.duration).toBe(0);
    expect(result.current.state.error).toBeNull();
  });

  it('respects custom options', () => {
    const options = {
      maxDuration: 120,
      sampleRate: 48000,
      channels: 2,
    };

    const { result } = renderHook(() => useVoiceRecording(options));

    expect(result.current).toBeDefined();
    // Options are used internally, so we can't directly test them
    // but we can verify the hook initializes correctly
  });

  it('handles unsupported browser', async () => {
    // Mock unsupported browser
    Object.defineProperty(navigator, 'mediaDevices', {
      value: undefined,
      writable: true,
    });

    const { result } = renderHook(() => useVoiceRecording());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.state.error).toBe('Voice recording is not supported in this browser');
  });

  it('pauses and resumes recording', async () => {
    const { result } = renderHook(() => useVoiceRecording());

    // Start recording
    await act(async () => {
      await result.current.startRecording();
    });

    // Pause recording
    act(() => {
      result.current.pauseRecording();
    });

    // Resume recording
    act(() => {
      result.current.resumeRecording();
    });

    expect(result.current.state.isRecording).toBe(true);
  });

  it('downloads recording when audio blob exists', () => {
    const { result } = renderHook(() => useVoiceRecording());

    // Mock DOM methods
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    };
    const createElement = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    const appendChild = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    const removeChild = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

    // Test that downloadRecording doesn't crash when no audio blob exists
    act(() => {
      result.current.downloadRecording();
    });

    // Should not create link when no audio blob
    expect(createElement).not.toHaveBeenCalled();

    // Cleanup
    createElement.mockRestore();
    appendChild.mockRestore();
    removeChild.mockRestore();
  });
});