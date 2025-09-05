import api from '../utils/api';

export interface AudioExportOptions {
  format: 'mp3' | 'wav' | 'ogg';
  quality: 'low' | 'medium' | 'high';
  voice: string; // Voice ID for TTS
  speed: number; // 0.5 to 2.0
  includeTimestamps?: boolean;
  includeChapters?: boolean;
  language?: string;
}

export interface TranscriptExportOptions {
  format: 'srt' | 'vtt' | 'txt' | 'json';
  includeTimestamps: boolean;
  includeMetadata?: boolean;
  chapterMarkers?: boolean;
}

export interface AudioExportRequest {
  documentId: string;
  jobId: string;
  content: 'summary' | 'full_document' | 'risk_analysis' | 'qa_responses';
  audioOptions: AudioExportOptions;
  transcriptOptions?: TranscriptExportOptions;
}

export interface AudioExportResponse {
  exportId: string;
  audioUrl?: string;
  transcriptUrl?: string;
  duration: number; // in seconds
  filename: string;
  transcriptFilename?: string;
  size: number;
  status: 'generating' | 'ready' | 'failed';
  expiresAt: string;
}

export interface VoiceOption {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  description: string;
  sampleUrl?: string;
}

export class AudioExportService {
  /**
   * Get available TTS voices
   */
  async getAvailableVoices(language?: string): Promise<VoiceOption[]> {
    const response = await api.get('/audio/voices', {
      params: { language },
    });
    return response.data;
  }

  /**
   * Request audio export generation
   */
  async requestAudioExport(request: AudioExportRequest): Promise<AudioExportResponse> {
    const response = await api.post('/audio/export', request);
    return response.data;
  }

  /**
   * Get audio export status
   */
  async getAudioExportStatus(exportId: string): Promise<AudioExportResponse> {
    const response = await api.get(`/audio/export/${exportId}/status`);
    return response.data;
  }

  /**
   * Download audio file
   */
  async downloadAudio(exportId: string): Promise<Blob> {
    const response = await api.get(`/audio/export/${exportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Download transcript file
   */
  async downloadTranscript(exportId: string): Promise<Blob> {
    const response = await api.get(`/audio/export/${exportId}/transcript`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generate MP3 narration with synchronized timestamps
   */
  async generateMP3Narration(
    documentId: string,
    jobId: string,
    options: Partial<AudioExportOptions> = {}
  ): Promise<AudioExportResponse> {
    return this.requestAudioExport({
      documentId,
      jobId,
      content: 'summary',
      audioOptions: {
        format: 'mp3',
        quality: 'high',
        voice: 'en-US-Standard-A',
        speed: 1.0,
        includeTimestamps: true,
        includeChapters: true,
        ...options,
      },
      transcriptOptions: {
        format: 'srt',
        includeTimestamps: true,
        includeMetadata: true,
        chapterMarkers: true,
      },
    });
  }

  /**
   * Generate SRT subtitle file
   */
  async generateSRTSubtitles(
    documentId: string,
    jobId: string,
    options: Partial<TranscriptExportOptions> = {}
  ): Promise<AudioExportResponse> {
    return this.requestAudioExport({
      documentId,
      jobId,
      content: 'summary',
      audioOptions: {
        format: 'mp3',
        quality: 'medium',
        voice: 'en-US-Standard-A',
        speed: 1.0,
      },
      transcriptOptions: {
        format: 'srt',
        includeTimestamps: true,
        includeMetadata: false,
        chapterMarkers: true,
        ...options,
      },
    });
  }

  /**
   * Generate audio with custom voice settings
   */
  async generateCustomAudio(
    documentId: string,
    jobId: string,
    content: AudioExportRequest['content'],
    audioOptions: AudioExportOptions,
    transcriptOptions?: TranscriptExportOptions
  ): Promise<AudioExportResponse> {
    return this.requestAudioExport({
      documentId,
      jobId,
      content,
      audioOptions,
      transcriptOptions,
    });
  }

  /**
   * Preview voice with sample text
   */
  async previewVoice(voiceId: string, text: string): Promise<Blob> {
    const response = await api.post('/audio/preview', {
      voiceId,
      text,
    }, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Get audio export progress stream
   */
  getAudioExportProgressStream(exportId: string): EventSource {
    return new EventSource(`/api/audio/export/${exportId}/progress`);
  }

  /**
   * Cancel audio export
   */
  async cancelAudioExport(exportId: string): Promise<void> {
    await api.delete(`/audio/export/${exportId}`);
  }

  /**
   * Get audio export history
   */
  async getAudioExportHistory(limit: number = 20): Promise<AudioExportResponse[]> {
    const response = await api.get('/audio/export/history', {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Get supported audio formats and quality options
   */
  async getSupportedFormats(): Promise<{
    formats: Array<{ id: string; name: string; extension: string; description: string }>;
    qualities: Array<{ id: string; name: string; bitrate: string; description: string }>;
  }> {
    const response = await api.get('/audio/formats');
    return response.data;
  }

  /**
   * Estimate audio generation time and cost
   */
  async estimateAudioGeneration(
    textLength: number,
    options: AudioExportOptions
  ): Promise<{
    estimatedDuration: number; // seconds
    estimatedSize: number; // bytes
    estimatedCost: number; // USD
  }> {
    const response = await api.post('/audio/estimate', {
      textLength,
      options,
    });
    return response.data;
  }
}

export const audioExportService = new AudioExportService();