import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TranslationPanel } from '../components/translation/TranslationPanel';
import { translationService } from '../services/translationService';

// Mock the translation service
vi.mock('../services/translationService', () => ({
  translationService: {
    getSupportedLanguages: vi.fn(),
    detectLanguage: vi.fn(),
    translateText: vi.fn(),
    getLanguageName: vi.fn(),
    getLanguageFlag: vi.fn(),
    getTextDirection: vi.fn(),
    formatProcessingTime: vi.fn(),
  },
}));

const mockTranslationService = vi.mocked(translationService);

describe('TranslationPanel', () => {
  const mockSupportedLanguages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    mockTranslationService.getSupportedLanguages.mockResolvedValue(mockSupportedLanguages);
    mockTranslationService.getLanguageName.mockImplementation((code) => {
      const lang = mockSupportedLanguages.find(l => l.code === code);
      return lang?.name || code.toUpperCase();
    });
    mockTranslationService.getLanguageFlag.mockImplementation((code) => {
      const flags: Record<string, string> = {
        'en': '🇺🇸',
        'es': '🇪🇸',
        'fr': '🇫🇷',
        'de': '🇩🇪',
      };
      return flags[code] || '🌐';
    });
    mockTranslationService.getTextDirection.mockReturnValue('ltr');
    mockTranslationService.formatProcessingTime.mockImplementation((seconds) => `${seconds}s`);
  });

  const findLanguageCheckbox = (languageName: string) => {
    return screen.getByRole('checkbox', { 
      name: new RegExp(languageName, 'i') 
    });
  };

  const waitForLanguagesToLoad = async () => {
    await waitFor(() => {
      expect(screen.getByText((_content, element) => 
        element?.textContent?.includes('Spanish') || false
      )).toBeInTheDocument();
    });
  };

  it('renders translation panel correctly', async () => {
    render(<TranslationPanel originalText="Hello world" />);

    expect(screen.getByText('Translation')).toBeInTheDocument();
    expect(screen.getByText('Source Language')).toBeInTheDocument();
    expect(screen.getByText('Select Target Languages')).toBeInTheDocument();
    expect(screen.getByText('Auto-detect')).toBeInTheDocument();

    // Wait for supported languages to load
    await waitForLanguagesToLoad();
    expect(screen.getByText((_content, element) => 
      element?.textContent?.includes('French') || false
    )).toBeInTheDocument();
  });

  it('detects source language when auto-detect is enabled', async () => {
    mockTranslationService.detectLanguage.mockResolvedValue({
      language: 'en',
      confidence: 0.95,
      isReliable: true,
      inputText: 'Hello world',
    });

    render(<TranslationPanel originalText="Hello world" />);

    await waitFor(() => {
      expect(mockTranslationService.detectLanguage).toHaveBeenCalledWith('Hello world');
    });

    await waitFor(() => {
      expect(screen.getByText(/Detected: 🇺🇸 English/)).toBeInTheDocument();
    });
  });

  it('allows language selection', async () => {
    render(<TranslationPanel originalText="Hello world" />);

    await waitForLanguagesToLoad();

    // Select Spanish
    const spanishCheckbox = findLanguageCheckbox('Spanish');
    fireEvent.click(spanishCheckbox);

    expect(spanishCheckbox).toBeChecked();
    expect(screen.getByText('1 language selected')).toBeInTheDocument();
  });

  it('performs translation when translate button is clicked', async () => {
    const mockTranslationResult = {
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
    };

    mockTranslationService.translateText.mockResolvedValue(mockTranslationResult);

    const onTranslationComplete = vi.fn();
    render(
      <TranslationPanel 
        originalText="Hello world" 
        onTranslationComplete={onTranslationComplete}
      />
    );

    // Wait for languages to load and select Spanish
    await waitForLanguagesToLoad();

    const spanishCheckbox = findLanguageCheckbox('Spanish');
    fireEvent.click(spanishCheckbox);

    // Click translate button
    const translateButton = screen.getByRole('button', { name: /translate/i });
    fireEvent.click(translateButton);

    // Verify translation was called
    await waitFor(() => {
      expect(mockTranslationService.translateText).toHaveBeenCalledWith(
        'Hello world',
        'es',
        {
          sourceLanguage: undefined,
          useCache: true,
          qualityThreshold: 0.7,
        }
      );
    });

    // Verify callback was called
    await waitFor(() => {
      expect(onTranslationComplete).toHaveBeenCalledWith([mockTranslationResult]);
    });

    // Verify translation result is displayed
    await waitFor(() => {
      expect(screen.getByText('Translation Results')).toBeInTheDocument();
      expect(screen.getByText('Hola mundo')).toBeInTheDocument();
    });
  });

  it('shows error when translation fails', async () => {
    mockTranslationService.translateText.mockRejectedValue(new Error('Translation failed'));

    render(<TranslationPanel originalText="Hello world" />);

    // Wait for languages to load and select Spanish
    await waitForLanguagesToLoad();

    const spanishCheckbox = findLanguageCheckbox('Spanish');
    fireEvent.click(spanishCheckbox);

    // Click translate button
    const translateButton = screen.getByRole('button', { name: /translate/i });
    fireEvent.click(translateButton);

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText('Translation failed')).toBeInTheDocument();
    });
  });

  it('disables translate button when no languages selected', async () => {
    render(<TranslationPanel originalText="Hello world" />);

    await waitFor(() => {
      const translateButton = screen.getByRole('button', { name: /translate/i });
      expect(translateButton).toBeDisabled();
    });
  });

  it('disables translate button when no text provided', async () => {
    render(<TranslationPanel />);

    await waitFor(() => {
      const translateButton = screen.getByRole('button', { name: /translate/i });
      expect(translateButton).toBeDisabled();
    });
  });

  it('shows loading state during translation', async () => {
    // Create a promise that we can control
    let resolveTranslation: (value: any) => void;
    const translationPromise = new Promise((resolve) => {
      resolveTranslation = resolve;
    });

    mockTranslationService.translateText.mockReturnValue(translationPromise as Promise<any>);

    render(<TranslationPanel originalText="Hello world" />);

    // Wait for languages to load and select Spanish
    await waitForLanguagesToLoad();

    const spanishCheckbox = findLanguageCheckbox('Spanish');
    fireEvent.click(spanishCheckbox);

    // Click translate button
    const translateButton = screen.getByRole('button', { name: /translate/i });
    fireEvent.click(translateButton);

    // Verify loading state
    await waitFor(() => {
      expect(screen.getByText('Translating...')).toBeInTheDocument();
      expect(translateButton).toBeDisabled();
    });

    // Resolve the translation
    resolveTranslation!({
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
    });

    // Verify loading state is cleared
    await waitFor(() => {
      expect(screen.queryByText('Translating...')).not.toBeInTheDocument();
      expect(translateButton).not.toBeDisabled();
    });
  });

  it('toggles original text visibility', async () => {
    const mockTranslationResult = {
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
    };

    mockTranslationService.translateText.mockResolvedValue(mockTranslationResult);
    mockTranslationService.detectLanguage.mockResolvedValue({
      language: 'en',
      confidence: 0.95,
      isReliable: true,
      inputText: 'Hello world',
    });

    render(<TranslationPanel originalText="Hello world" />);

    // Perform translation first
    await waitForLanguagesToLoad();

    const spanishCheckbox = findLanguageCheckbox('Spanish');
    fireEvent.click(spanishCheckbox);

    const translateButton = screen.getByRole('button', { name: /translate/i });
    fireEvent.click(translateButton);

    await waitFor(() => {
      expect(screen.getByText('Translation Results')).toBeInTheDocument();
    });

    // Original text should be visible by default
    expect(screen.getByText('Hello world')).toBeInTheDocument();

    // Click hide original button
    const hideButton = screen.getByRole('button', { name: /hide original/i });
    fireEvent.click(hideButton);

    // Original text should be hidden
    expect(screen.queryByText('Hello world')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /show original/i })).toBeInTheDocument();
  });

  it('clears translations when clear button is clicked', async () => {
    const mockTranslationResult = {
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
    };

    mockTranslationService.translateText.mockResolvedValue(mockTranslationResult);

    render(<TranslationPanel originalText="Hello world" />);

    // Perform translation
    await waitForLanguagesToLoad();

    const spanishCheckbox = findLanguageCheckbox('Spanish');
    fireEvent.click(spanishCheckbox);

    const translateButton = screen.getByRole('button', { name: /translate/i });
    fireEvent.click(translateButton);

    await waitFor(() => {
      expect(screen.getByText('Translation Results')).toBeInTheDocument();
    });

    // Click clear button
    const clearButton = screen.getByRole('button', { name: /clear/i });
    fireEvent.click(clearButton);

    // Verify translations are cleared
    expect(screen.queryByText('Translation Results')).not.toBeInTheDocument();
    expect(screen.queryByText('Hola mundo')).not.toBeInTheDocument();
  });
});