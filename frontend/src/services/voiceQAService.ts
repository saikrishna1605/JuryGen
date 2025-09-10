/**
 * Voice Q&A Service
 * 
 * Provides comprehensive voice-to-voice Q&A functionality by integrating:
 * - Speech-to-text transcription
 * - Q&A processing with context retrieval
 * - Text-to-speech synthesis
 * - Session management
 */

import { speechService } from './speechService';
import { qaService } from './qaService';

export interface VoiceQARequest {
  audioBlob?: Blob;
  question?: string;
  documentId?: string;
  sessionId?: string;
  languageCode?: string;
  voiceSettings?: VoiceSettings;
}

export interface VoiceSettings {
  voiceName?: string;
  voiceGender?: 'MALE' | 'FEMALE' | 'NEUTRAL';
  speakingRate?: number;
  pitch?: number;
  volumeGainDb?: number;
  audioFormat?: 'MP3' | 'WAV' | 'OGG';
}

export interface VoiceQAResponse {
  question: string;
  answer: string;
  confidence: number;
  sources: Array<{
    documentId: string;
    chunkId: string;
    title: string;
    relevanceScore: number;
    excerpt: string;
  }>;
  audioResponse?: {
    audioUrl: string;
    audioFormat: string;
    duration: number;
  };
  processingTime: number;
  sessionId: string;
  metadata: {
    transcriptionConfidence?: number;
    synthesisQuality?: number;
    contextDocsCount: number;
    languageCode: string;
  };
}

export interface QASession {
  sessionId: string;
  documentId?: string;
  userId: string;
  exchanges: QAExchange[];
  createdAt: Date;
  updatedAt: Date;
  settings: VoiceSettings;
}

export interface QAExchange {
  id: string;
  question: string;
  answer: string;
  questionAudio?: string;
  answerAudio?: string;
  confidence: number;
  sources: Array<any>;
  timestamp: Date;
  processingTime: number;
}

export interface ProcessingStatus {
  stage: 'transcribing' | 'processing' | 'synthesizing' | 'complete' | 'error';
  progress: number;
  message: string;
  error?: string;
}

class VoiceQAService {
  private activeSessions = new Map<string, QASession>();
  private processingCallbacks = new Map<string, (status: ProcessingStatus) => void>();

  /**
   * Process a voice question through the complete pipeline
   */
  async processVoiceQuestion(
    request: VoiceQARequest,
    onProgress?: (status: ProcessingStatus) => void
  ): Promise<VoiceQAResponse> {
    const startTime = Date.now();
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    if (onProgress) {
      this.processingCallbacks.set(requestId, onProgress);
    }

    try {
      let question = request.question;
      let transcriptionConfidence = 1.0;

      // Step 1: Transcribe audio if provided
      if (request.audioBlob && !question) {
        this.updateProgress(requestId, {
          stage: 'transcribing',
          progress: 10,
          message: 'Transcribing your question...'
        });

        const transcription = await speechService.transcribeAudio(
          new File([request.audioBlob], 'question.webm', { type: 'audio/webm' }),
          {
            languageCode: request.languageCode || 'en-US',
            enableAutomaticPunctuation: true,
            enableWordTimestamps: false,
            model: 'latest_short'
          }
        );

        question = transcription.transcript;
        transcriptionConfidence = transcription.confidence;

        if (!question.trim()) {
          throw new Error('No speech detected in audio');
        }
      }

      if (!question) {
        throw new Error('No question provided');
      }

      // Step 2: Process the question
      this.updateProgress(requestId, {
        stage: 'processing',
        progress: 30,
        message: 'Processing your question...'
      });

      if (!request.documentId) {
        throw new Error('Document ID is required for voice Q&A');
      }

      const qaResponse = await qaService.askTextQuestion(
        question,
        request.documentId,
        {
          sessionId: request.sessionId
        }
      );

      // Step 3: Synthesize answer to speech
      this.updateProgress(requestId, {
        stage: 'synthesizing',
        progress: 70,
        message: 'Generating audio response...'
      });

      let audioResponse;
      try {
        const synthesis = await speechService.synthesizeText(
          qaResponse.answer,
          {
            languageCode: request.languageCode || 'en-US',
            voiceName: request.voiceSettings?.voiceName,
            voiceGender: request.voiceSettings?.voiceGender || 'NEUTRAL',
            speakingRate: request.voiceSettings?.speakingRate || 1.0,
            pitch: request.voiceSettings?.pitch || 0.0,
            volumeGainDb: request.voiceSettings?.volumeGainDb || 0.0,
            audioFormat: request.voiceSettings?.audioFormat || 'MP3'
          }
        );

        audioResponse = {
          audioUrl: speechService.createAudioUrl(
            synthesis.audioContentBase64,
            `audio/${synthesis.audioFormat.toLowerCase()}`
          ),
          audioFormat: synthesis.audioFormat,
          duration: synthesis.duration || 0
        };
      } catch (error) {
        console.warn('Audio synthesis failed:', error);
        // Continue without audio response
      }

      // Step 4: Complete processing
      this.updateProgress(requestId, {
        stage: 'complete',
        progress: 100,
        message: 'Processing complete!'
      });

      const processingTime = (Date.now() - startTime) / 1000;

      const response: VoiceQAResponse = {
        question,
        answer: qaResponse.answer,
        confidence: qaResponse.confidence,
        sources: qaResponse.sources.map((source: any) => ({
          documentId: source.documentId,
          chunkId: source.chunkId || '',
          title: source.title || 'Unknown Document',
          relevanceScore: source.relevanceScore || 0,
          excerpt: source.excerpt || source.content?.substring(0, 200) + '...' || ''
        })),
        audioResponse,
        processingTime,
        sessionId: request.sessionId || `session_${Date.now()}`,
        metadata: {
          transcriptionConfidence,
          synthesisQuality: audioResponse ? 0.9 : 0,
          contextDocsCount: qaResponse.sources.length,
          languageCode: request.languageCode || 'en-US'
        }
      };

      // Update session history
      this.updateSessionHistory(response);

      return response;

    } catch (error) {
      this.updateProgress(requestId, {
        stage: 'error',
        progress: 0,
        message: 'Processing failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    } finally {
      this.processingCallbacks.delete(requestId);
    }
  }

  /**
   * Process a text question with optional voice response
   */
  async processTextQuestion(
    question: string,
    options: {
      documentId?: string;
      sessionId?: string;
      languageCode?: string;
      voiceSettings?: VoiceSettings;
      includeAudio?: boolean;
    } = {}
  ): Promise<VoiceQAResponse> {
    return this.processVoiceQuestion({
      question,
      documentId: options.documentId,
      sessionId: options.sessionId,
      languageCode: options.languageCode,
      voiceSettings: options.voiceSettings
    });
  }

  /**
   * Get session history
   */
  getSessionHistory(sessionId: string): QAExchange[] {
    const session = this.activeSessions.get(sessionId);
    return session?.exchanges || [];
  }

  /**
   * Clear session history
   */
  clearSession(sessionId: string): boolean {
    return this.activeSessions.delete(sessionId);
  }

  /**
   * Get all active sessions
   */
  getActiveSessions(): QASession[] {
    return Array.from(this.activeSessions.values());
  }

  /**
   * Create a new session
   */
  createSession(
    documentId?: string,
    settings: VoiceSettings = {}
  ): QASession {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const session: QASession = {
      sessionId,
      documentId,
      userId: 'current_user', // Would come from auth context
      exchanges: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      settings: {
        voiceGender: 'NEUTRAL',
        speakingRate: 1.0,
        pitch: 0.0,
        volumeGainDb: 0.0,
        audioFormat: 'MP3',
        ...settings
      }
    };

    this.activeSessions.set(sessionId, session);
    return session;
  }

  /**
   * Update session settings
   */
  updateSessionSettings(
    sessionId: string,
    settings: Partial<VoiceSettings>
  ): boolean {
    const session = this.activeSessions.get(sessionId);
    if (session) {
      session.settings = { ...session.settings, ...settings };
      session.updatedAt = new Date();
      return true;
    }
    return false;
  }

  /**
   * Get suggested questions for a document
   */
  async getSuggestedQuestions(_documentId: string): Promise<string[]> {
    try {
      // This would typically call the backend API with documentId
      // For now, return common legal document questions
      // TODO: Use documentId to fetch document-specific suggestions
      return [
        "What are the main terms and conditions?",
        "What are my obligations under this agreement?",
        "What are the key risks I should be aware of?",
        "Are there any important deadlines?",
        "What happens if I want to terminate this agreement?",
        "What are the payment terms?",
        "Are there any penalties or fees?",
        "What are my rights under this document?",
        "Can you explain the most complex clauses?",
        "What should I pay special attention to?"
      ];
    } catch (error) {
      console.error('Failed to get suggested questions:', error);
      return [];
    }
  }

  /**
   * Estimate processing time based on question complexity
   */
  estimateProcessingTime(question: string, hasAudio: boolean): number {
    let baseTime = 2; // Base processing time in seconds
    
    // Add time for transcription
    if (hasAudio) {
      baseTime += 3;
    }
    
    // Add time based on question length
    const wordCount = question.split(' ').length;
    baseTime += Math.ceil(wordCount / 10) * 0.5;
    
    // Add time for synthesis
    baseTime += 2;
    
    return baseTime;
  }

  /**
   * Validate audio input
   */
  validateAudioInput(audioBlob: Blob): { valid: boolean; error?: string } {
    if (!audioBlob) {
      return { valid: false, error: 'No audio data provided' };
    }

    if (audioBlob.size === 0) {
      return { valid: false, error: 'Audio file is empty' };
    }

    if (audioBlob.size > 10 * 1024 * 1024) { // 10MB limit
      return { valid: false, error: 'Audio file is too large (max 10MB)' };
    }

    if (!audioBlob.type.startsWith('audio/')) {
      return { valid: false, error: 'Invalid audio format' };
    }

    return { valid: true };
  }

  /**
   * Get processing statistics
   */
  getProcessingStats(): {
    totalSessions: number;
    totalExchanges: number;
    averageProcessingTime: number;
    averageConfidence: number;
  } {
    const sessions = Array.from(this.activeSessions.values());
    const allExchanges = sessions.flatMap(s => s.exchanges);

    return {
      totalSessions: sessions.length,
      totalExchanges: allExchanges.length,
      averageProcessingTime: allExchanges.length > 0 
        ? allExchanges.reduce((sum, ex) => sum + ex.processingTime, 0) / allExchanges.length
        : 0,
      averageConfidence: allExchanges.length > 0
        ? allExchanges.reduce((sum, ex) => sum + ex.confidence, 0) / allExchanges.length
        : 0
    };
  }

  private updateProgress(requestId: string, status: ProcessingStatus): void {
    const callback = this.processingCallbacks.get(requestId);
    if (callback) {
      callback(status);
    }
  }

  private updateSessionHistory(response: VoiceQAResponse): void {
    let session = this.activeSessions.get(response.sessionId);
    
    if (!session) {
      session = this.createSession(undefined, {});
      session.sessionId = response.sessionId;
    }

    const exchange: QAExchange = {
      id: `exchange_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      question: response.question,
      answer: response.answer,
      questionAudio: undefined, // Would store question audio URL if available
      answerAudio: response.audioResponse?.audioUrl,
      confidence: response.confidence,
      sources: response.sources,
      timestamp: new Date(),
      processingTime: response.processingTime
    };

    session.exchanges.push(exchange);
    session.updatedAt = new Date();

    // Keep only last 50 exchanges per session
    if (session.exchanges.length > 50) {
      session.exchanges = session.exchanges.slice(-50);
    }
  }
}

export const voiceQAService = new VoiceQAService();
export default voiceQAService;