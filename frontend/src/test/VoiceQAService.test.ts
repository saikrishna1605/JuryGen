/**
 * Voice Q&A Service Tests
 * 
 * Tests for the complete voice-to-voice Q&A pipeline including:
 * - Voice question processing
 * - Text question processing
 * - Session management
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { voiceQAService, type VoiceQARequest, type ProcessingStatus } from '../services/voiceQAService';
import { speechService } from '../services/speechService';
import { qaService } from '../services/qaService';

// Mock Firebase first
vi.mock('../config/firebase', () => ({
  auth: {},
  db: {},
  storage: {}
}));

// Mock dependencies
vi.mock('../services/speechService', () => ({
  speechService: {
    transcribeAudio: vi.fn(),
    synthesizeText: vi.fn(),
    createAudioUrl: vi.fn(),
    getAvailableVoices: vi.fn(),
    getSupportedLanguages: vi.fn(),
    base64ToBlob: vi.fn(),
    validateAudioFile: vi.fn(),
    estimateReadingTime: vi.fn(),
    formatDuration: vi.fn(),
    getAudioFormat: vi.fn(),
    downloadAudio: vi.fn()
  }
}));

vi.mock('../services/qaService', () => ({
  qaService: {
    askTextQuestion: vi.fn(),
    getSessionHistory: vi.fn(),
    clearSession: vi.fn(),
    health_check: vi.fn()
  }
}));

const mockSpeechService = vi.mocked(speechService);
const mockQAService = vi.mocked(qaService);

describe('VoiceQAService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    mockSpeechService.transcribeAudio.mockResolvedValue({
      transcript: 'What are the main terms of this contract?',
      confidence: 0.95,
      processingTime: 2.1,
      duration: 5.2,
      languageCode: 'en-US'
    });

    mockSpeechService.synthesizeText.mockResolvedValue({
      audioContentBase64: 'base64audiodata',
      audioFormat: 'MP3',
      duration: 8.5,
      processingTime: 1.8
    });

    mockSpeechService.createAudioUrl.mockReturnValue('blob:audio-url');

    mockQAService.askTextQuestion.mockResolvedValue({
      answer: 'The main terms include payment obligations, delivery requirements, and termination clauses.',
      confidence: 0.88,
      sources: [
        {
          documentId: 'doc1',
          chunkId: 'chunk1',
          title: 'Contract Agreement',
          relevanceScore: 0.92,
          content: 'This contract establishes the terms...'
        }
      ],
      sessionId: 'session123',
      processingTime: 3.2,
      contextUsed: ['contract_terms', 'obligations']
    });
  });

  afterEach(() => {
    // Clear any active sessions
    voiceQAService.getActiveSessions().forEach(session => {
      voiceQAService.clearSession(session.sessionId);
    });
  });

  describe('processVoiceQuestion', () => {
    it('should process voice question with audio input', async () => {
      const audioBlob = new Blob(['fake audio data'], { type: 'audio/webm' });
      const request: VoiceQARequest = {
        audioBlob,
        documentId: 'doc1',
        languageCode: 'en-US',
        voiceSettings: {
          voiceGender: 'FEMALE',
          speakingRate: 1.2
        }
      };

      const progressUpdates: ProcessingStatus[] = [];
      const onProgress = (status: ProcessingStatus) => {
        progressUpdates.push(status);
      };

      const response = await voiceQAService.processVoiceQuestion(request, onProgress);

      // Verify transcription was called
      expect(mockSpeechService.transcribeAudio).toHaveBeenCalledWith(
        expect.any(File),
        {
          languageCode: 'en-US',
          enableAutomaticPunctuation: true,
          enableWordTimestamps: false,
          model: 'latest_short'
        }
      );

      // Verify Q&A processing was called
      expect(mockQAService.askTextQuestion).toHaveBeenCalledWith(
        'What are the main terms of this contract?',
        'doc1',
        sessionId: undefined,
        includeContext: true,
        maxSources: 5
      });

      // Verify synthesis was called
      expect(mockSpeechService.synthesizeText).toHaveBeenCalledWith(
        'The main terms include payment obligations, delivery requirements, and termination clauses.',
        {
          languageCode: 'en-US',
          voiceName: undefined,
          voiceGender: 'FEMALE',
          speakingRate: 1.2,
          pitch: 0.0,
          volumeGainDb: 0.0,
          audioFormat: 'MP3'
        }
      );

      // Verify response structure
      expect(response.question).toBe('What are the main terms of this contract?');
      expect(response.answer).toBe('The main terms include payment obligations, delivery requirements, and termination clauses.');
      expect(response.confidence).toBe(0.88);
      expect(response.sources).toHaveLength(1);
      expect(response.sources[0].documentId).toBe('doc1');
      expect(response.audioResponse).toBeDefined();
      expect(response.audioResponse?.audioUrl).toBe('blob:audio-url');
      expect(response.processingTime).toBeGreaterThanOrEqual(0);
      expect(response.sessionId).toBeDefined();
      expect(response.metadata.transcriptionConfidence).toBe(0.95);

      // Verify progress updates
      expect(progressUpdates).toHaveLength(4);
      expect(progressUpdates[0].stage).toBe('transcribing');
      expect(progressUpdates[1].stage).toBe('processing');
      expect(progressUpdates[2].stage).toBe('synthesizing');
      expect(progressUpdates[3].stage).toBe('complete');
    });

    it('should process text question without audio input', async () => {
      const request: VoiceQARequest = {
        question: 'What are the payment terms?',
        documentId: 'doc1',
        languageCode: 'en-US'
      };

      const response = await voiceQAService.processVoiceQuestion(request);

      // Verify transcription was NOT called
      expect(mockSpeechService.transcribeAudio).not.toHaveBeenCalled();

      // Verify Q&A processing was called with provided question
      expect(mockQAService.askTextQuestion).toHaveBeenCalledWith(
        'What are the payment terms?',
        'doc1',
        sessionId: undefined,
        includeContext: true,
        maxSources: 5
      });

      expect(response.question).toBe('What are the payment terms?');
      expect(response.metadata.transcriptionConfidence).toBe(1.0);
    });

    it('should handle transcription failure', async () => {
      mockSpeechService.transcribeAudio.mockRejectedValue(new Error('Transcription failed'));

      const audioBlob = new Blob(['fake audio data'], { type: 'audio/webm' });
      const request: VoiceQARequest = {
        audioBlob,
        documentId: 'doc1'
      };

      await expect(voiceQAService.processVoiceQuestion(request)).rejects.toThrow('Transcription failed');
    });

    it('should handle empty transcription', async () => {
      mockSpeechService.transcribeAudio.mockResolvedValue({
        transcript: '',
        confidence: 0.1,
        processingTime: 1.0,
        audioLength: 2.0,
        languageCode: 'en-US'
      });

      const audioBlob = new Blob(['fake audio data'], { type: 'audio/webm' });
      const request: VoiceQARequest = {
        audioBlob,
        documentId: 'doc1'
      };

      await expect(voiceQAService.processVoiceQuestion(request)).rejects.toThrow('No speech detected in audio');
    });

    it('should continue processing when synthesis fails', async () => {
      mockSpeechService.synthesizeText.mockRejectedValue(new Error('Synthesis failed'));

      const request: VoiceQARequest = {
        question: 'What are the terms?',
        documentId: 'doc1'
      };

      const response = await voiceQAService.processVoiceQuestion(request);

      // Should still return response without audio
      expect(response.audioResponse).toBeUndefined();
      expect(response.answer).toBe('The main terms include payment obligations, delivery requirements, and termination clauses.');
      expect(response.metadata.synthesisQuality).toBe(0);
    });

    it('should handle Q&A processing failure', async () => {
      mockQAService.askTextQuestion.mockRejectedValue(new Error('Q&A processing failed'));

      const request: VoiceQARequest = {
        question: 'What are the terms?',
        documentId: 'doc1'
      };

      await expect(voiceQAService.processVoiceQuestion(request)).rejects.toThrow('Q&A processing failed');
    });
  });

  describe('processTextQuestion', () => {
    it('should process text question with voice response', async () => {
      const response = await voiceQAService.processTextQuestion(
        'What are the key obligations?',
        {
          documentId: 'doc1',
          languageCode: 'en-US',
          includeAudio: true,
          voiceSettings: {
            voiceGender: 'MALE',
            speakingRate: 0.9
          }
        }
      );

      expect(response.question).toBe('What are the key obligations?');
      expect(response.audioResponse).toBeDefined();
      expect(mockSpeechService.synthesizeText).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          voiceGender: 'MALE',
          speakingRate: 0.9
        })
      );
    });
  });

  describe('session management', () => {
    it('should create and manage sessions', () => {
      const session = voiceQAService.createSession('doc1', {
        voiceGender: 'FEMALE',
        speakingRate: 1.1
      });

      expect(session.sessionId).toBeDefined();
      expect(session.documentId).toBe('doc1');
      expect(session.settings.voiceGender).toBe('FEMALE');
      expect(session.settings.speakingRate).toBe(1.1);
      expect(session.exchanges).toHaveLength(0);

      const activeSessions = voiceQAService.getActiveSessions();
      expect(activeSessions.length).toBeGreaterThan(0);
      expect(activeSessions.find(s => s.sessionId === session.sessionId)).toBeDefined();
    });

    it('should update session settings', () => {
      const session = voiceQAService.createSession();
      
      const updated = voiceQAService.updateSessionSettings(session.sessionId, {
        speakingRate: 1.5,
        pitch: 2.0
      });

      expect(updated).toBe(true);
      
      const updatedSession = voiceQAService.getActiveSessions().find(s => s.sessionId === session.sessionId);
      expect(updatedSession?.settings.speakingRate).toBe(1.5);
      expect(updatedSession?.settings.pitch).toBe(2.0);
      expect(updatedSession?.settings.voiceGender).toBe('NEUTRAL'); // Should preserve other settings
    });

    it('should clear sessions', () => {
      const session = voiceQAService.createSession();
      const initialCount = voiceQAService.getActiveSessions().length;

      const cleared = voiceQAService.clearSession(session.sessionId);
      expect(cleared).toBe(true);
      expect(voiceQAService.getActiveSessions().length).toBe(initialCount - 1);
    });

    it('should track session history', async () => {
      const session = voiceQAService.createSession();
      
      const request: VoiceQARequest = {
        question: 'What are the terms?',
        sessionId: session.sessionId,
        documentId: 'doc1'
      };

      await voiceQAService.processVoiceQuestion(request);

      const history = voiceQAService.getSessionHistory(session.sessionId);
      expect(history).toHaveLength(1);
      expect(history[0].question).toBe('What are the terms?');
      expect(history[0].answer).toBe('The main terms include payment obligations, delivery requirements, and termination clauses.');
      expect(history[0].confidence).toBe(0.88);
    });
  });

  describe('utility methods', () => {
    it('should get suggested questions', async () => {
      const questions = await voiceQAService.getSuggestedQuestions('doc1');
      
      expect(questions).toBeInstanceOf(Array);
      expect(questions.length).toBeGreaterThan(0);
      expect(questions[0]).toContain('terms');
    });

    it('should estimate processing time', () => {
      const timeWithAudio = voiceQAService.estimateProcessingTime('What are the terms?', true);
      const timeWithoutAudio = voiceQAService.estimateProcessingTime('What are the terms?', false);
      
      expect(timeWithAudio).toBeGreaterThan(timeWithoutAudio);
      expect(timeWithAudio).toBeGreaterThan(5); // Should include transcription time
      expect(timeWithoutAudio).toBeGreaterThan(2); // Should include base processing time
    });

    it('should validate audio input', () => {
      const validAudio = new Blob(['audio data'], { type: 'audio/webm' });
      const invalidAudio = new Blob(['not audio'], { type: 'text/plain' });
      const emptyAudio = new Blob([], { type: 'audio/webm' });

      expect(voiceQAService.validateAudioInput(validAudio)).toEqual({ valid: true });
      expect(voiceQAService.validateAudioInput(invalidAudio)).toEqual({
        valid: false,
        error: 'Invalid audio format'
      });
      expect(voiceQAService.validateAudioInput(emptyAudio)).toEqual({
        valid: false,
        error: 'Audio file is empty'
      });
    });

    it('should calculate processing statistics', async () => {
      // Create a session and process some questions
      const session = voiceQAService.createSession();
      
      await voiceQAService.processVoiceQuestion({
        question: 'Question 1',
        sessionId: session.sessionId
      });
      
      await voiceQAService.processVoiceQuestion({
        question: 'Question 2',
        sessionId: session.sessionId
      });

      const stats = voiceQAService.getProcessingStats();
      
      expect(stats.totalSessions).toBeGreaterThan(0);
      expect(stats.totalExchanges).toBeGreaterThanOrEqual(2);
      expect(stats.averageConfidence).toBe(0.88);
      expect(stats.averageProcessingTime).toBeGreaterThan(0);
    });
  });

  describe('error handling', () => {
    it('should handle missing question and audio', async () => {
      const request: VoiceQARequest = {
        documentId: 'doc1'
      };

      await expect(voiceQAService.processVoiceQuestion(request)).rejects.toThrow('No question provided');
    });

    it('should report progress on error', async () => {
      mockQAService.askTextQuestion.mockRejectedValue(new Error('Processing failed'));

      const request: VoiceQARequest = {
        question: 'What are the terms?',
        documentId: 'doc1'
      };

      const progressUpdates: ProcessingStatus[] = [];
      const onProgress = (status: ProcessingStatus) => {
        progressUpdates.push(status);
      };

      await expect(voiceQAService.processVoiceQuestion(request, onProgress)).rejects.toThrow('Processing failed');

      // Should have received error progress update
      const errorUpdate = progressUpdates.find(update => update.stage === 'error');
      expect(errorUpdate).toBeDefined();
      expect(errorUpdate?.error).toBe('Processing failed');
    });

    it('should handle session operations on non-existent session', () => {
      const nonExistentId = 'non-existent-session';
      
      expect(voiceQAService.getSessionHistory(nonExistentId)).toEqual([]);
      expect(voiceQAService.clearSession(nonExistentId)).toBe(false);
      expect(voiceQAService.updateSessionSettings(nonExistentId, {})).toBe(false);
    });
  });

  describe('integration scenarios', () => {
    it('should handle complete voice-to-voice workflow', async () => {
      const audioBlob = new Blob(['question audio'], { type: 'audio/webm' });
      const progressUpdates: ProcessingStatus[] = [];
      
      const response = await voiceQAService.processVoiceQuestion({
        audioBlob,
        documentId: 'doc1',
        languageCode: 'en-US',
        voiceSettings: {
          voiceGender: 'FEMALE',
          speakingRate: 1.0,
          pitch: 0.0
        }
      }, (status) => progressUpdates.push(status));

      // Verify complete pipeline was executed
      expect(mockSpeechService.transcribeAudio).toHaveBeenCalled();
      expect(mockQAService.askTextQuestion).toHaveBeenCalled();
      expect(mockSpeechService.synthesizeText).toHaveBeenCalled();
      expect(mockSpeechService.createAudioUrl).toHaveBeenCalled();

      // Verify response completeness
      expect(response.question).toBeDefined();
      expect(response.answer).toBeDefined();
      expect(response.audioResponse).toBeDefined();
      expect(response.sources).toHaveLength(1);
      expect(response.confidence).toBeGreaterThan(0);
      expect(response.processingTime).toBeGreaterThanOrEqual(0);

      // Verify progress tracking
      expect(progressUpdates).toHaveLength(4);
      expect(progressUpdates.map(u => u.stage)).toEqual([
        'transcribing',
        'processing', 
        'synthesizing',
        'complete'
      ]);
    });

    it('should maintain session continuity across multiple questions', async () => {
      const session = voiceQAService.createSession('doc1');
      
      // First question
      await voiceQAService.processVoiceQuestion({
        question: 'What are the terms?',
        sessionId: session.sessionId,
        documentId: 'doc1'
      });

      // Second question
      await voiceQAService.processVoiceQuestion({
        question: 'What about penalties?',
        sessionId: session.sessionId,
        documentId: 'doc1'
      });

      const history = voiceQAService.getSessionHistory(session.sessionId);
      expect(history).toHaveLength(2);
      expect(history[0].question).toBe('What are the terms?');
      expect(history[1].question).toBe('What about penalties?');

      // Verify session was passed to Q&A service
      expect(mockQAService.askTextQuestion).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        expect.objectContaining({
          sessionId: session.sessionId
        })
      );
    });
  });
});