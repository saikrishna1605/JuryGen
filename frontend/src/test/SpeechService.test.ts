import { describe, it, expect, vi, beforeEach } from 'vitest';
import { speechService } from '../services/speechService';
import api from '../utils/api';

// Mock the API
vi.mock('../lib/api', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('SpeechService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('transcribeAudio', () => {
    it('should transcribe audio file successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            transcript: 'Hello world',
            confidence: 0.95,
            languageCode: 'en-US',
            alternatives: [],
            wordTimestamps: [],
            speakerLabels: [],
            audioDuration: 2.5,
            processingTime: 1.2,
          },
        },
      };

      (api.post as any).mockResolvedValue(mockResponse);

      const audioFile = new File(['audio data'], 'test.wav', { type: 'audio/wav' });
      const result = await speechService.transcribeAudio(audioFile, {
        languageCode: 'en-US',
        enableWordTimestamps: true,
      });

      expect(api.post).toHaveBeenCalledWith(
        '/speech/transcribe',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      expect(result.transcript).toBe('Hello world');
      expect(result.confidence).toBe(0.95);
      expect(result.languageCode).toBe('en-US');
    });

    it('should handle transcription errors', async () => {
      (api.post as any).mockRejectedValue(new Error('API Error'));

      const audioFile = new File(['audio data'], 'test.wav', { type: 'audio/wav' });

      await expect(speechService.transcribeAudio(audioFile)).rejects.toThrow('API Error');
    });
  });

  describe('synthesizeText', () => {
    it('should synthesize text successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            audioContentBase64: 'base64audiodata',
            text: 'Hello world',
            voiceName: 'en-US-Standard-A',
            languageCode: 'en-US',
            audioFormat: 'mp3',
            sampleRate: 24000,
            duration: 2.0,
            processingTime: 0.8,
          },
        },
      };

      (api.post as any).mockResolvedValue(mockResponse);

      const result = await speechService.synthesizeText('Hello world', {
        languageCode: 'en-US',
        voiceGender: 'FEMALE',
      });

      expect(api.post).toHaveBeenCalledWith('/speech/synthesize', {
        text: 'Hello world',
        language_code: 'en-US',
        voice_name: undefined,
        voice_gender: 'FEMALE',
        audio_format: 'MP3',
        sample_rate: undefined,
        speaking_rate: 1.0,
        pitch: 0.0,
        volume_gain_db: 0.0,
        use_ssml: false,
      });

      expect(result.audioContentBase64).toBe('base64audiodata');
      expect(result.text).toBe('Hello world');
      expect(result.voiceName).toBe('en-US-Standard-A');
    });
  });

  describe('getAvailableVoices', () => {
    it('should get available voices', async () => {
      const mockResponse = {
        data: {
          data: [
            {
              name: 'en-US-Standard-A',
              languageCodes: ['en-US'],
              ssmlGender: 'FEMALE',
              naturalSampleRateHertz: 24000,
            },
            {
              name: 'en-US-Standard-B',
              languageCodes: ['en-US'],
              ssmlGender: 'MALE',
              naturalSampleRateHertz: 24000,
            },
          ],
        },
      };

      (api.get as any).mockResolvedValue(mockResponse);

      const voices = await speechService.getAvailableVoices('en-US');

      expect(api.get).toHaveBeenCalledWith('/speech/voices', {
        params: { language_code: 'en-US' },
      });

      expect(voices).toHaveLength(2);
      expect(voices[0].name).toBe('en-US-Standard-A');
      expect(voices[1].ssmlGender).toBe('MALE');
    });
  });

  describe('getSupportedLanguages', () => {
    it('should get supported languages', async () => {
      const mockResponse = {
        data: {
          data: [
            { code: 'en-US', name: 'English (US)', region: 'United States' },
            { code: 'es-ES', name: 'Spanish (Spain)', region: 'Spain' },
          ],
        },
      };

      (api.get as any).mockResolvedValue(mockResponse);

      const languages = await speechService.getSupportedLanguages();

      expect(api.get).toHaveBeenCalledWith('/speech/languages');
      expect(languages).toHaveLength(2);
      expect(languages[0].code).toBe('en-US');
      expect(languages[1].name).toBe('Spanish (Spain)');
    });
  });

  describe('utility methods', () => {
    it('should convert base64 to blob', () => {
      const testData = 'test audio data';
      const base64 = btoa(testData);
      const blob = speechService.base64ToBlob(base64, 'audio/mp3');

      expect(blob).toBeInstanceOf(Blob);
      expect(blob.type).toBe('audio/mp3');
    });

    it('should create audio URL from base64', () => {
      const testData = 'test audio data';
      const base64 = btoa(testData);
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');

      const url = speechService.createAudioUrl(base64, 'audio/mp3');

      expect(url).toBe('blob:mock-url');
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });

    it('should validate audio file types', () => {
      const validFile = new File(['data'], 'test.mp3', { type: 'audio/mp3' });
      const invalidFile = new File(['data'], 'test.txt', { type: 'text/plain' });

      expect(speechService.isValidAudioFile(validFile)).toBe(true);
      expect(speechService.isValidAudioFile(invalidFile)).toBe(false);
    });

    it('should estimate reading time', () => {
      const text = 'This is a test sentence with ten words total.';
      const time = speechService.estimateReadingTime(text, 150); // 150 WPM

      // 9 words at 150 WPM = 9/150 * 60 = 3.6 seconds
      expect(Math.round(time)).toBe(4);
    });

    it('should format duration correctly', () => {
      expect(speechService.formatDuration(30)).toBe('30s');
      expect(speechService.formatDuration(90)).toBe('1m 30s');
      expect(speechService.formatDuration(120)).toBe('2m');
      expect(speechService.formatDuration(3661)).toBe('61m 1s');
    });

    it('should get audio format from MIME type', () => {
      expect(speechService.getAudioFormat('audio/mp3')).toBe('MP3');
      expect(speechService.getAudioFormat('audio/wav')).toBe('WAV');
      expect(speechService.getAudioFormat('audio/ogg')).toBe('OGG');
      expect(speechService.getAudioFormat('unknown/type')).toBe('MP3'); // default
    });
  });

  describe('downloadAudio', () => {
    it('should download audio file', () => {
      const testData = 'test audio data';
      const base64 = btoa(testData);
      
      // Mock DOM methods
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
      };
      
      const createElement = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
      const appendChild = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
      const removeChild = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
      
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
      global.URL.revokeObjectURL = vi.fn();

      speechService.downloadAudio(base64, 'test.mp3', 'audio/mp3');

      expect(createElement).toHaveBeenCalledWith('a');
      expect(mockLink.download).toBe('test.mp3');
      expect(mockLink.click).toHaveBeenCalled();
      expect(appendChild).toHaveBeenCalledWith(mockLink);
      expect(removeChild).toHaveBeenCalledWith(mockLink);
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');

      // Cleanup
      createElement.mockRestore();
      appendChild.mockRestore();
      removeChild.mockRestore();
    });
  });
});