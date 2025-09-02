import api from '../lib/api';

export interface TranscriptionOptions {
  languageCode?: string;
  enableWordTimestamps?: boolean;
  enableSpeakerDiarization?: boolean;
  maxSpeakerCount?: number;
  enableAutomaticPunctuation?: boolean;
  enableProfanityFilter?: boolean;
  speechContexts?: string[];
  model?: string;
}

export interface TranscriptionResult {
  transcript: string;
  confidence: number;
  languageCode: string;
  alternatives: Array<{
    transcript: string;
    confidence: number;
  }>;
  wordTimestamps: Array<{
    word: string;
    startTime: number;
    endTime: number;
    speakerTag?: number;
  }>;
  speakerLabels: Array<{
    speakerTag: number;
    transcript: string;
  }>;
  audioDuration: number;
  processingTime: number;
}

export interface SynthesisOptions {
  languageCode?: string;
  voiceName?: string;
  voiceGender?: 'MALE' | 'FEMALE' | 'NEUTRAL';
  audioFormat?: 'MP3' | 'WAV' | 'OGG';
  sampleRate?: number;
  speakingRate?: number;
  pitch?: number;
  volumeGainDb?: number;
  useSSML?: boolean;
}

export interface SynthesisResult {
  audioContentBase64: string;
  text: string;
  voiceName: string;
  languageCode: string;
  audioFormat: string;
  sampleRate: number;
  duration: number;
  processingTime: number;
}

export interface VoiceInfo {
  name: string;
  languageCodes: string[];
  ssmlGender: string;
  naturalSampleRateHertz: number;
}

export interface LanguageInfo {
  code: string;
  name: string;
  region: string;
}

class SpeechService {
  /**
   * Transcribe an audio file to text
   */
  async transcribeAudio(
    audioFile: File,
    options: TranscriptionOptions = {}
  ): Promise<TranscriptionResult> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    
    // Add options as form fields
    if (options.languageCode) formData.append('language_code', options.languageCode);
    if (options.enableWordTimestamps !== undefined) {
      formData.append('enable_word_timestamps', options.enableWordTimestamps.toString());
    }
    if (options.enableSpeakerDiarization !== undefined) {
      formData.append('enable_speaker_diarization', options.enableSpeakerDiarization.toString());
    }
    if (options.maxSpeakerCount) {
      formData.append('max_speaker_count', options.maxSpeakerCount.toString());
    }
    if (options.enableAutomaticPunctuation !== undefined) {
      formData.append('enable_automatic_punctuation', options.enableAutomaticPunctuation.toString());
    }
    if (options.enableProfanityFilter !== undefined) {
      formData.append('enable_profanity_filter', options.enableProfanityFilter.toString());
    }
    if (options.model) formData.append('model', options.model);

    const response = await api.post('/speech/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Transcribe audio with automatic language detection
   */
  async transcribeWithLanguageDetection(
    audioFile: File,
    candidateLanguages: string[] = ['en-US', 'es-ES', 'fr-FR']
  ): Promise<TranscriptionResult> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);

    const params = new URLSearchParams();
    candidateLanguages.forEach(lang => params.append('candidate_languages', lang));

    const response = await api.post(`/speech/transcribe-with-language-detection?${params}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Synthesize text to speech
   */
  async synthesizeText(
    text: string,
    options: SynthesisOptions = {}
  ): Promise<SynthesisResult> {
    const requestData = {
      text,
      language_code: options.languageCode || 'en-US',
      voice_name: options.voiceName,
      voice_gender: options.voiceGender || 'NEUTRAL',
      audio_format: options.audioFormat || 'MP3',
      sample_rate: options.sampleRate,
      speaking_rate: options.speakingRate || 1.0,
      pitch: options.pitch || 0.0,
      volume_gain_db: options.volumeGainDb || 0.0,
      use_ssml: options.useSSML || false,
    };

    const response = await api.post('/speech/synthesize', requestData);
    return response.data.data;
  }

  /**
   * Synthesize text to speech and return audio blob
   */
  async synthesizeTextToAudio(
    text: string,
    options: SynthesisOptions = {}
  ): Promise<Blob> {
    const requestData = {
      text,
      language_code: options.languageCode || 'en-US',
      voice_name: options.voiceName,
      voice_gender: options.voiceGender || 'NEUTRAL',
      audio_format: options.audioFormat || 'MP3',
      sample_rate: options.sampleRate,
      speaking_rate: options.speakingRate || 1.0,
      pitch: options.pitch || 0.0,
      volume_gain_db: options.volumeGainDb || 0.0,
      use_ssml: options.useSSML || false,
    };

    const response = await api.post('/speech/synthesize-audio', requestData, {
      responseType: 'blob',
    });

    return response.data;
  }

  /**
   * Synthesize SSML text to speech
   */
  async synthesizeSSML(
    ssmlText: string,
    languageCode: string = 'en-US',
    voiceName?: string,
    audioFormat: string = 'MP3'
  ): Promise<SynthesisResult> {
    const formData = new FormData();
    formData.append('text', ssmlText);
    formData.append('language_code', languageCode);
    if (voiceName) formData.append('voice_name', voiceName);
    formData.append('audio_format', audioFormat);

    const response = await api.post('/speech/synthesize-ssml', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Get available voices for text-to-speech
   */
  async getAvailableVoices(languageCode?: string): Promise<VoiceInfo[]> {
    const params = languageCode ? { language_code: languageCode } : {};
    const response = await api.get('/speech/voices', { params });
    return response.data.data;
  }

  /**
   * Get supported languages
   */
  async getSupportedLanguages(): Promise<LanguageInfo[]> {
    const response = await api.get('/speech/languages');
    return response.data.data;
  }

  /**
   * Create pronunciation guide for legal terms
   */
  async createPronunciationGuide(
    text: string,
    languageCode: string = 'en-US'
  ): Promise<string> {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('language_code', languageCode);

    const response = await api.post('/speech/create-pronunciation-guide', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Check speech services health
   */
  async healthCheck(): Promise<any> {
    const response = await api.get('/speech/health');
    return response.data.data;
  }

  /**
   * Convert base64 audio to blob
   */
  base64ToBlob(base64: string, mimeType: string = 'audio/mpeg'): Blob {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }

  /**
   * Create audio URL from base64
   */
  createAudioUrl(base64: string, mimeType: string = 'audio/mpeg'): string {
    const blob = this.base64ToBlob(base64, mimeType);
    return URL.createObjectURL(blob);
  }

  /**
   * Download audio from base64
   */
  downloadAudio(
    base64: string,
    filename: string = 'audio.mp3',
    mimeType: string = 'audio/mpeg'
  ): void {
    const blob = this.base64ToBlob(base64, mimeType);
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  }

  /**
   * Estimate text reading time (for UI purposes)
   */
  estimateReadingTime(text: string, wordsPerMinute: number = 150): number {
    const words = text.trim().split(/\s+/).length;
    return (words / wordsPerMinute) * 60; // Return seconds
  }

  /**
   * Format duration in human readable format
   */
  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }

  /**
   * Validate audio file type
   */
  isValidAudioFile(file: File): boolean {
    const validTypes = [
      'audio/mp3',
      'audio/mpeg',
      'audio/wav',
      'audio/ogg',
      'audio/webm',
      'audio/m4a',
      'audio/aac',
    ];
    return validTypes.includes(file.type);
  }

  /**
   * Get audio file format from MIME type
   */
  getAudioFormat(mimeType: string): string {
    const formatMap: { [key: string]: string } = {
      'audio/mp3': 'MP3',
      'audio/mpeg': 'MP3',
      'audio/wav': 'WAV',
      'audio/ogg': 'OGG',
      'audio/webm': 'WEBM',
      'audio/m4a': 'M4A',
      'audio/aac': 'AAC',
    };
    return formatMap[mimeType] || 'MP3';
  }
}

export const speechService = new SpeechService();