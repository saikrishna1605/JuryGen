import api from '../utils/api';

export interface TranslationOptions {
  sourceLanguage?: string;
  useCache?: boolean;
  qualityThreshold?: number;
}

export interface BatchTranslationOptions {
  sourceLanguage?: string;
  useCache?: boolean;
  maxConcurrent?: number;
}

export interface TranslationResult {
  originalText: string;
  translatedText: string;
  sourceLanguage: string;
  targetLanguage: string;
  confidence: number;
  qualityScore: number;
  processingTime: number;
  cached: boolean;
  alternatives: string[];
  createdAt: string;
}

export interface BatchTranslationResult {
  translations: TranslationResult[];
  totalProcessingTime: number;
  successCount: number;
  failureCount: number;
  cacheHitCount: number;
  cacheHitRate: number;
  createdAt: string;
}

export interface LanguageDetectionResult {
  language: string;
  confidence: number;
  isReliable: boolean;
  inputText: string;
}

export interface SupportedLanguage {
  code: string;
  name: string;
}

export interface DocumentSectionTranslation {
  [sectionId: string]: TranslationResult;
}

class TranslationService {
  /**
   * Translate a single text
   */
  async translateText(
    text: string,
    targetLanguage: string,
    options: TranslationOptions = {}
  ): Promise<TranslationResult> {
    const response = await api.post('/translation/translate', {
      text,
      target_language: targetLanguage,
      source_language: options.sourceLanguage,
      use_cache: options.useCache ?? true,
      quality_threshold: options.qualityThreshold ?? 0.7,
    });

    return response.data.data;
  }

  /**
   * Translate multiple texts in batch
   */
  async translateBatch(
    texts: string[],
    targetLanguage: string,
    options: BatchTranslationOptions = {}
  ): Promise<BatchTranslationResult> {
    const response = await api.post('/translation/translate-batch', {
      texts,
      target_language: targetLanguage,
      source_language: options.sourceLanguage,
      use_cache: options.useCache ?? true,
      max_concurrent: options.maxConcurrent ?? 5,
    });

    return response.data.data;
  }

  /**
   * Translate document sections while preserving structure
   */
  async translateDocumentSections(
    sections: { [sectionId: string]: string },
    targetLanguage: string,
    sourceLanguage?: string,
    preserveFormatting: boolean = true
  ): Promise<DocumentSectionTranslation> {
    const response = await api.post('/translation/translate-document-sections', {
      sections,
      target_language: targetLanguage,
      source_language: sourceLanguage,
      preserve_formatting: preserveFormatting,
    });

    return response.data.data;
  }

  /**
   * Detect the language of text
   */
  async detectLanguage(text: string): Promise<LanguageDetectionResult> {
    const formData = new FormData();
    formData.append('text', text);

    const response = await api.post('/translation/detect-language', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Get supported languages
   */
  async getSupportedLanguages(targetLanguage: string = 'en'): Promise<SupportedLanguage[]> {
    const response = await api.get('/translation/supported-languages', {
      params: { target_language: targetLanguage },
    });

    return response.data.data;
  }

  /**
   * Translate with multiple alternatives
   */
  async translateWithAlternatives(
    text: string,
    targetLanguage: string,
    sourceLanguage?: string,
    numAlternatives: number = 3
  ): Promise<{
    mainTranslation: TranslationResult;
    alternatives: string[];
    totalAlternatives: number;
  }> {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('target_language', targetLanguage);
    if (sourceLanguage) formData.append('source_language', sourceLanguage);
    formData.append('num_alternatives', numAlternatives.toString());

    const response = await api.post('/translation/translate-with-alternatives', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Clear translation cache
   */
  async clearCache(olderThanHours: number = 24): Promise<void> {
    await api.post('/translation/clear-cache', null, {
      params: { older_than_hours: olderThanHours },
    });
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<any> {
    const response = await api.get('/translation/cache-stats');
    return response.data.data;
  }

  /**
   * Check translation service health
   */
  async healthCheck(): Promise<any> {
    const response = await api.get('/translation/health');
    return response.data.data;
  }

  /**
   * Get language name from code
   */
  getLanguageName(code: string): string {
    const languageNames: { [key: string]: string } = {
      'en': 'English',
      'es': 'Spanish',
      'fr': 'French',
      'de': 'German',
      'it': 'Italian',
      'pt': 'Portuguese',
      'ru': 'Russian',
      'ja': 'Japanese',
      'ko': 'Korean',
      'zh': 'Chinese',
      'ar': 'Arabic',
      'hi': 'Hindi',
      'nl': 'Dutch',
      'sv': 'Swedish',
      'da': 'Danish',
      'no': 'Norwegian',
      'fi': 'Finnish',
      'pl': 'Polish',
      'tr': 'Turkish',
      'he': 'Hebrew',
      'th': 'Thai',
      'vi': 'Vietnamese',
      'id': 'Indonesian',
      'ms': 'Malay',
      'tl': 'Filipino',
      'uk': 'Ukrainian',
      'cs': 'Czech',
      'sk': 'Slovak',
      'hu': 'Hungarian',
      'ro': 'Romanian',
      'bg': 'Bulgarian',
      'hr': 'Croatian',
      'sr': 'Serbian',
      'sl': 'Slovenian',
      'et': 'Estonian',
      'lv': 'Latvian',
      'lt': 'Lithuanian',
      'mt': 'Maltese',
      'cy': 'Welsh',
      'ga': 'Irish',
      'is': 'Icelandic',
      'mk': 'Macedonian',
      'sq': 'Albanian',
      'eu': 'Basque',
      'ca': 'Catalan',
      'gl': 'Galician',
    };

    return languageNames[code] || code.toUpperCase();
  }

  /**
   * Get language flag emoji
   */
  getLanguageFlag(code: string): string {
    const flags: { [key: string]: string } = {
      'en': '🇺🇸',
      'es': '🇪🇸',
      'fr': '🇫🇷',
      'de': '🇩🇪',
      'it': '🇮🇹',
      'pt': '🇵🇹',
      'ru': '🇷🇺',
      'ja': '🇯🇵',
      'ko': '🇰🇷',
      'zh': '🇨🇳',
      'ar': '🇸🇦',
      'hi': '🇮🇳',
      'nl': '🇳🇱',
      'sv': '🇸🇪',
      'da': '🇩🇰',
      'no': '🇳🇴',
      'fi': '🇫🇮',
      'pl': '🇵🇱',
      'tr': '🇹🇷',
      'he': '🇮🇱',
      'th': '🇹🇭',
      'vi': '🇻🇳',
      'id': '🇮🇩',
      'ms': '🇲🇾',
      'tl': '🇵🇭',
      'uk': '🇺🇦',
      'cs': '🇨🇿',
      'sk': '🇸🇰',
      'hu': '🇭🇺',
      'ro': '🇷🇴',
      'bg': '🇧🇬',
      'hr': '🇭🇷',
      'sr': '🇷🇸',
      'sl': '🇸🇮',
      'et': '🇪🇪',
      'lv': '🇱🇻',
      'lt': '🇱🇹',
      'mt': '🇲🇹',
      'cy': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
      'ga': '🇮🇪',
      'is': '🇮🇸',
      'mk': '🇲🇰',
      'sq': '🇦🇱',
      'eu': '🏴󠁥󠁳󠁰󠁶󠁿',
      'ca': '🏴󠁥󠁳󠁣󠁴󠁿',
      'gl': '🏴󠁥󠁳󠁧󠁡󠁿',
    };

    return flags[code] || '🌐';
  }

  /**
   * Validate text for translation
   */
  validateText(text: string): { valid: boolean; error?: string } {
    const trimmed = text.trim();
    
    if (!trimmed) {
      return { valid: false, error: 'Text cannot be empty' };
    }
    
    if (trimmed.length > 10000) {
      return { valid: false, error: 'Text is too long (max 10,000 characters)' };
    }
    
    return { valid: true };
  }

  /**
   * Estimate translation cost (for UI purposes)
   */
  estimateTranslationCost(text: string, targetLanguages: string[]): number {
    const characters = text.length;
    const languages = targetLanguages.length;
    
    // Rough estimate: $20 per million characters
    const costPerCharacter = 0.00002;
    return characters * languages * costPerCharacter;
  }

  /**
   * Get quality score color for UI
   */
  getQualityScoreColor(score: number): string {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-green-500';
    if (score >= 0.7) return 'text-yellow-500';
    if (score >= 0.6) return 'text-orange-500';
    return 'text-red-500';
  }

  /**
   * Format quality score for display
   */
  formatQualityScore(score: number): string {
    const percentage = Math.round(score * 100);
    if (percentage >= 90) return `${percentage}% (Excellent)`;
    if (percentage >= 80) return `${percentage}% (Good)`;
    if (percentage >= 70) return `${percentage}% (Fair)`;
    if (percentage >= 60) return `${percentage}% (Poor)`;
    return `${percentage}% (Very Poor)`;
  }

  /**
   * Get common language pairs for legal documents
   */
  getCommonLegalLanguagePairs(): Array<{ source: string; targets: string[] }> {
    return [
      {
        source: 'en',
        targets: ['es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ar'],
      },
      {
        source: 'es',
        targets: ['en', 'pt', 'fr', 'it'],
      },
      {
        source: 'fr',
        targets: ['en', 'es', 'de', 'it'],
      },
      {
        source: 'de',
        targets: ['en', 'fr', 'it', 'es'],
      },
      {
        source: 'zh',
        targets: ['en', 'ja', 'ko'],
      },
    ];
  }

  /**
   * Check if language pair is commonly used
   */
  isCommonLanguagePair(source: string, target: string): boolean {
    const commonPairs = this.getCommonLegalLanguagePairs();
    return commonPairs.some(pair => 
      pair.source === source && pair.targets.includes(target)
    );
  }

  /**
   * Get translation direction (LTR or RTL)
   */
  getTextDirection(languageCode: string): 'ltr' | 'rtl' {
    const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
    return rtlLanguages.includes(languageCode) ? 'rtl' : 'ltr';
  }

  /**
   * Format processing time for display
   */
  formatProcessingTime(seconds: number): string {
    if (seconds < 1) {
      return `${Math.round(seconds * 1000)}ms`;
    } else if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    }
  }

  /**
   * Calculate translation statistics
   */
  calculateTranslationStats(results: TranslationResult[]): {
    averageQuality: number;
    averageProcessingTime: number;
    cacheHitRate: number;
    totalCharacters: number;
    languageDistribution: { [key: string]: number };
  } {
    if (results.length === 0) {
      return {
        averageQuality: 0,
        averageProcessingTime: 0,
        cacheHitRate: 0,
        totalCharacters: 0,
        languageDistribution: {},
      };
    }

    const totalQuality = results.reduce((sum, r) => sum + r.qualityScore, 0);
    const totalTime = results.reduce((sum, r) => sum + r.processingTime, 0);
    const cacheHits = results.filter(r => r.cached).length;
    const totalChars = results.reduce((sum, r) => sum + r.originalText.length, 0);

    const languageDistribution: { [key: string]: number } = {};
    results.forEach(r => {
      const pair = `${r.sourceLanguage}-${r.targetLanguage}`;
      languageDistribution[pair] = (languageDistribution[pair] || 0) + 1;
    });

    return {
      averageQuality: totalQuality / results.length,
      averageProcessingTime: totalTime / results.length,
      cacheHitRate: cacheHits / results.length,
      totalCharacters: totalChars,
      languageDistribution,
    };
  }
}

export const translationService = new TranslationService();