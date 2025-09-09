import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { translationService } from '../services/translationService';
import api from '../utils/api';

// Mock the API
vi.mock('../lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

// Helper function to create proper AxiosResponse mock
const createMockResponse = (data: any) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {}
} as any);

describe('TranslationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('translateText', () => {
    it('should translate text successfully', async () => {
      const mockResponseData = {
        data: {
          originalText: 'Hello world',
          translatedText: 'Hola mundo',
          sourceLanguage: 'en',
          targetLanguage: 'es',
          confidence: 1.0,
          qualityScore: 0.95,
          processingTime: 0.5,
          cached: false,
          alternatives: [],
          createdAt: '2023-01-01T00:00:00Z',
        },
      };

      mockApi.post.mockResolvedValueOnce(createMockResponse(mockResponseData));

      const result = await translationService.translateText('Hello world', 'es');

      expect(mockApi.post).toHaveBeenCalledWith('/translation/translate', {
        text: 'Hello world',
        target_language: 'es',
        source_language: undefined,
        use_cache: true,
        quality_threshold: 0.7,
      });

      expect(result).toEqual(mockResponseData.data);
    });

    it('should handle translation errors', async () => {
      const mockError = new Error('Translation failed');
      mockApi.post.mockRejectedValueOnce(mockError);

      await expect(
        translationService.translateText('Hello world', 'es')
      ).rejects.toThrow('Translation failed');
    });

    it('should pass custom options', async () => {
      const mockResponseData = {
        data: {
          originalText: 'Hello world',
          translatedText: 'Hola mundo',
          sourceLanguage: 'en',
          targetLanguage: 'es',
          confidence: 1.0,
          qualityScore: 0.95,
          processingTime: 0.5,
          cached: false,
          alternatives: [],
          createdAt: '2023-01-01T00:00:00Z',
        },
      };

      mockApi.post.mockResolvedValueOnce(createMockResponse(mockResponseData));

      await translationService.translateText('Hello world', 'es', {
        sourceLanguage: 'en',
        useCache: false,
        qualityThreshold: 0.8,
      });

      expect(mockApi.post).toHaveBeenCalledWith('/translation/translate', {
        text: 'Hello world',
        target_language: 'es',
        source_language: 'en',
        use_cache: false,
        quality_threshold: 0.8,
      });
    });
  });

  describe('translateBatch', () => {
    it('should translate multiple texts', async () => {
      const mockResponseData = {
        data: {
          translations: [
            {
              originalText: 'Hello',
              translatedText: 'Hola',
              sourceLanguage: 'en',
              targetLanguage: 'es',
              confidence: 1.0,
              qualityScore: 0.95,
              processingTime: 0.3,
              cached: false,
              alternatives: [],
              createdAt: '2023-01-01T00:00:00Z',
            },
            {
              originalText: 'World',
              translatedText: 'Mundo',
              sourceLanguage: 'en',
              targetLanguage: 'es',
              confidence: 1.0,
              qualityScore: 0.92,
              processingTime: 0.2,
              cached: true,
              alternatives: [],
              createdAt: '2023-01-01T00:00:00Z',
            },
          ],
          totalProcessingTime: 0.5,
          successCount: 2,
          failureCount: 0,
          cacheHitCount: 1,
          cacheHitRate: 0.5,
          createdAt: '2023-01-01T00:00:00Z',
        },
      };

      mockApi.post.mockResolvedValueOnce(createMockResponse(mockResponseData));

      const result = await translationService.translateBatch(['Hello', 'World'], 'es');

      expect(mockApi.post).toHaveBeenCalledWith('/translation/translate-batch', {
        texts: ['Hello', 'World'],
        target_language: 'es',
        source_language: undefined,
        use_cache: true,
        max_concurrent: 5,
      });

      expect(result).toEqual(mockResponseData.data);
    });
  });

  describe('detectLanguage', () => {
    it('should detect language successfully', async () => {
      const mockResponseData = {
        data: {
          language: 'en',
          confidence: 0.95,
          isReliable: true,
          inputText: 'Hello world',
        },
      };

      mockApi.post.mockResolvedValueOnce(createMockResponse(mockResponseData));

      const result = await translationService.detectLanguage('Hello world');

      expect(mockApi.post).toHaveBeenCalledWith(
        '/translation/detect-language',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      expect(result).toEqual(mockResponseData.data);
    });
  });

  describe('getSupportedLanguages', () => {
    it('should get supported languages', async () => {
      const mockResponseData = {
        data: [
          { code: 'en', name: 'English' },
          { code: 'es', name: 'Spanish' },
          { code: 'fr', name: 'French' },
        ],
      };

      mockApi.get.mockResolvedValueOnce(createMockResponse(mockResponseData));

      const result = await translationService.getSupportedLanguages();

      expect(mockApi.get).toHaveBeenCalledWith('/translation/supported-languages', {
        params: { target_language: 'en' },
      });

      expect(result).toEqual(mockResponseData.data);
    });

    it('should get supported languages in different target language', async () => {
      const mockResponseData = {
        data: [
          { code: 'en', name: 'Inglés' },
          { code: 'es', name: 'Español' },
          { code: 'fr', name: 'Francés' },
        ],
      };

      mockApi.get.mockResolvedValueOnce(createMockResponse(mockResponseData));

      const result = await translationService.getSupportedLanguages('es');

      expect(mockApi.get).toHaveBeenCalledWith('/translation/supported-languages', {
        params: { target_language: 'es' },
      });

      expect(result).toEqual(mockResponseData.data);
    });
  });

  describe('utility methods', () => {
    describe('getLanguageName', () => {
      it('should return language name for known codes', () => {
        expect(translationService.getLanguageName('en')).toBe('English');
        expect(translationService.getLanguageName('es')).toBe('Spanish');
        expect(translationService.getLanguageName('fr')).toBe('French');
      });

      it('should return uppercase code for unknown codes', () => {
        expect(translationService.getLanguageName('xyz')).toBe('XYZ');
      });
    });

    describe('getLanguageFlag', () => {
      it('should return flag emoji for known codes', () => {
        expect(translationService.getLanguageFlag('en')).toBe('🇺🇸');
        expect(translationService.getLanguageFlag('es')).toBe('🇪🇸');
        expect(translationService.getLanguageFlag('fr')).toBe('🇫🇷');
      });

      it('should return globe emoji for unknown codes', () => {
        expect(translationService.getLanguageFlag('xyz')).toBe('🌐');
      });
    });

    describe('validateText', () => {
      it('should validate text correctly', () => {
        expect(translationService.validateText('Hello world')).toEqual({
          valid: true,
        });

        expect(translationService.validateText('')).toEqual({
          valid: false,
          error: 'Text cannot be empty',
        });

        expect(translationService.validateText('   ')).toEqual({
          valid: false,
          error: 'Text cannot be empty',
        });

        const longText = 'a'.repeat(10001);
        expect(translationService.validateText(longText)).toEqual({
          valid: false,
          error: 'Text is too long (max 10,000 characters)',
        });
      });
    });

    describe('getQualityScoreColor', () => {
      it('should return correct color classes', () => {
        expect(translationService.getQualityScoreColor(0.95)).toBe('text-green-600');
        expect(translationService.getQualityScoreColor(0.85)).toBe('text-green-500');
        expect(translationService.getQualityScoreColor(0.75)).toBe('text-yellow-500');
        expect(translationService.getQualityScoreColor(0.65)).toBe('text-orange-500');
        expect(translationService.getQualityScoreColor(0.55)).toBe('text-red-500');
      });
    });

    describe('formatQualityScore', () => {
      it('should format quality scores correctly', () => {
        expect(translationService.formatQualityScore(0.95)).toBe('95% (Excellent)');
        expect(translationService.formatQualityScore(0.85)).toBe('85% (Good)');
        expect(translationService.formatQualityScore(0.75)).toBe('75% (Fair)');
        expect(translationService.formatQualityScore(0.65)).toBe('65% (Poor)');
        expect(translationService.formatQualityScore(0.55)).toBe('55% (Very Poor)');
      });
    });

    describe('getTextDirection', () => {
      it('should return correct text direction', () => {
        expect(translationService.getTextDirection('ar')).toBe('rtl');
        expect(translationService.getTextDirection('he')).toBe('rtl');
        expect(translationService.getTextDirection('fa')).toBe('rtl');
        expect(translationService.getTextDirection('ur')).toBe('rtl');
        expect(translationService.getTextDirection('en')).toBe('ltr');
        expect(translationService.getTextDirection('es')).toBe('ltr');
      });
    });

    describe('formatProcessingTime', () => {
      it('should format processing time correctly', () => {
        expect(translationService.formatProcessingTime(0.5)).toBe('500ms');
        expect(translationService.formatProcessingTime(1.5)).toBe('1.5s');
        expect(translationService.formatProcessingTime(65)).toBe('1m 5s');
        expect(translationService.formatProcessingTime(125)).toBe('2m 5s');
      });
    });

    describe('isCommonLanguagePair', () => {
      it('should identify common language pairs', () => {
        expect(translationService.isCommonLanguagePair('en', 'es')).toBe(true);
        expect(translationService.isCommonLanguagePair('en', 'fr')).toBe(true);
        expect(translationService.isCommonLanguagePair('es', 'en')).toBe(true);
        expect(translationService.isCommonLanguagePair('xyz', 'abc')).toBe(false);
      });
    });

    describe('calculateTranslationStats', () => {
      it('should calculate statistics correctly', () => {
        const results = [
          {
            originalText: 'Hello',
            translatedText: 'Hola',
            sourceLanguage: 'en',
            targetLanguage: 'es',
            confidence: 1.0,
            qualityScore: 0.9,
            processingTime: 0.5,
            cached: true,
            alternatives: [],
            createdAt: '2023-01-01T00:00:00Z',
          },
          {
            originalText: 'World',
            translatedText: 'Mundo',
            sourceLanguage: 'en',
            targetLanguage: 'es',
            confidence: 1.0,
            qualityScore: 0.8,
            processingTime: 0.3,
            cached: false,
            alternatives: [],
            createdAt: '2023-01-01T00:00:00Z',
          },
        ];

        const stats = translationService.calculateTranslationStats(results);

        expect(stats.averageQuality).toBeCloseTo(0.85);
        expect(stats.averageProcessingTime).toBe(0.4);
        expect(stats.cacheHitRate).toBe(0.5);
        expect(stats.totalCharacters).toBe(10); // 'Hello' + 'World'
        expect(stats.languageDistribution).toEqual({ 'en-es': 2 });
      });

      it('should handle empty results', () => {
        const stats = translationService.calculateTranslationStats([]);

        expect(stats.averageQuality).toBe(0);
        expect(stats.averageProcessingTime).toBe(0);
        expect(stats.cacheHitRate).toBe(0);
        expect(stats.totalCharacters).toBe(0);
        expect(stats.languageDistribution).toEqual({});
      });
    });
  });
});