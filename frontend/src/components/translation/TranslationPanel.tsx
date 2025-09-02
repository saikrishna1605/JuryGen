import React, { useState, useEffect } from 'react';
import { Languages, Globe, CheckCircle, AlertCircle, Loader2, Download, Eye, EyeOff } from 'lucide-react';
import { translationService, TranslationResult, SupportedLanguage } from '../../services/translationService';
import { cn } from '../../lib/utils';

interface TranslationPanelProps {
    documentId?: string;
    originalText?: string;
    onTranslationComplete?: (results: TranslationResult[]) => void;
    className?: string;
}

interface TranslationState {
    selectedLanguages: string[];
    isTranslating: boolean;
    translations: Record<string, TranslationResult>;
    supportedLanguages: SupportedLanguage[];
    showOriginal: boolean;
    autoDetectLanguage: boolean;
    sourceLanguage?: string;
}

export const TranslationPanel: React.FC<TranslationPanelProps> = ({
    documentId,
    originalText,
    onTranslationComplete,
    className
}) => {
    const [state, setState] = useState<TranslationState>({
        selectedLanguages: [],
        isTranslating: false,
        translations: {},
        supportedLanguages: [],
        showOriginal: true,
        autoDetectLanguage: true,
        sourceLanguage: undefined
    });

    const [error, setError] = useState<string | null>(null);

    // Load supported languages on mount
    useEffect(() => {
        const loadSupportedLanguages = async () => {
            try {
                const languages = await translationService.getSupportedLanguages();
                setState(prev => ({ ...prev, supportedLanguages: languages }));
            } catch (err) {
                console.error('Failed to load supported languages:', err);
                setError('Failed to load supported languages');
            }
        };

        loadSupportedLanguages();
    }, []);

    // Auto-detect source language if enabled
    useEffect(() => {
        if (state.autoDetectLanguage && originalText && originalText.trim()) {
            const detectLanguage = async () => {
                try {
                    const result = await translationService.detectLanguage(originalText);
                    if (result.isReliable) {
                        setState(prev => ({ ...prev, sourceLanguage: result.language }));
                    }
                } catch (err) {
                    console.error('Language detection failed:', err);
                }
            };

            detectLanguage();
        }
    }, [originalText, state.autoDetectLanguage]);

    const handleLanguageToggle = (languageCode: string) => {
        setState(prev => ({
            ...prev,
            selectedLanguages: prev.selectedLanguages.includes(languageCode)
                ? prev.selectedLanguages.filter(lang => lang !== languageCode)
                : [...prev.selectedLanguages, languageCode]
        }));
    };

    const handleTranslate = async () => {
        if (!originalText || state.selectedLanguages.length === 0) {
            setError('Please select at least one target language');
            return;
        }

        setState(prev => ({ ...prev, isTranslating: true }));
        setError(null);

        try {
            const results: TranslationResult[] = [];
            const newTranslations: Record<string, TranslationResult> = {};

            // Translate to each selected language
            for (const targetLanguage of state.selectedLanguages) {
                const result = await translationService.translateText(
                    originalText,
                    targetLanguage,
                    {
                        sourceLanguage: state.autoDetectLanguage ? undefined : state.sourceLanguage,
                        useCache: true,
                        qualityThreshold: 0.7
                    }
                );

                results.push(result);
                newTranslations[targetLanguage] = result;
            }

            setState(prev => ({
                ...prev,
                translations: { ...prev.translations, ...newTranslations },
                isTranslating: false
            }));

            onTranslationComplete?.(results);
        } catch (err) {
            console.error('Translation failed:', err);
            setError(err instanceof Error ? err.message : 'Translation failed');
            setState(prev => ({ ...prev, isTranslating: false }));
        }
    };

    const handleClearTranslations = () => {
        setState(prev => ({
            ...prev,
            translations: {},
            selectedLanguages: []
        }));
    };

    const getQualityBadgeColor = (score: number) => {
        if (score >= 0.9) return 'bg-green-100 text-green-800';
        if (score >= 0.8) return 'bg-blue-100 text-blue-800';
        if (score >= 0.7) return 'bg-yellow-100 text-yellow-800';
        return 'bg-red-100 text-red-800';
    };

    const formatQualityScore = (score: number) => {
        const percentage = Math.round(score * 100);
        return `${percentage}%`;
    };

    const commonLanguages = [
        'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi', 'nl'
    ];

    const otherLanguages = state.supportedLanguages.filter(
        lang => !commonLanguages.includes(lang.code) && lang.code !== 'en'
    );

    return (
        <div className={cn('bg-white rounded-lg border border-gray-200 shadow-sm', className)}>
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Languages className="w-5 h-5 text-blue-600" />
                        <h3 className="text-lg font-semibold text-gray-900">Translation</h3>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={() => setState(prev => ({ ...prev, showOriginal: !prev.showOriginal }))}
                            className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            {state.showOriginal ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            <span>{state.showOriginal ? 'Hide' : 'Show'} Original</span>
                        </button>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Source Language Detection */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-gray-700">Source Language</label>
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={state.autoDetectLanguage}
                                onChange={(e) => setState(prev => ({ ...prev, autoDetectLanguage: e.target.checked }))}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-600">Auto-detect</span>
                        </label>
                    </div>

                    {state.sourceLanguage && (
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                            <Globe className="w-4 h-4" />
                            <span>
                                Detected: {translationService.getLanguageFlag(state.sourceLanguage)} {translationService.getLanguageName(state.sourceLanguage)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Language Selection */}
                <div className="space-y-4">
                    <h4 className="text-sm font-medium text-gray-700">Select Target Languages</h4>

                    {/* Common Languages */}
                    <div>
                        <h5 className="text-xs font-medium text-gray-500 mb-2">Common Languages</h5>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                            {state.supportedLanguages
                                .filter(lang => commonLanguages.includes(lang.code))
                                .map(language => (
                                    <label
                                        key={language.code}
                                        className={cn(
                                            'flex items-center space-x-2 p-2 rounded-md border cursor-pointer transition-colors',
                                            state.selectedLanguages.includes(language.code)
                                                ? 'border-blue-500 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                        )}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={state.selectedLanguages.includes(language.code)}
                                            onChange={() => handleLanguageToggle(language.code)}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-sm">
                                            {translationService.getLanguageFlag(language.code)} {language.name}
                                        </span>
                                    </label>
                                ))}
                        </div>
                    </div>

                    {/* Other Languages */}
                    {otherLanguages.length > 0 && (
                        <details className="group">
                            <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700">
                                More Languages ({otherLanguages.length})
                            </summary>
                            <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                                {otherLanguages.map(language => (
                                    <label
                                        key={language.code}
                                        className={cn(
                                            'flex items-center space-x-2 p-2 rounded-md border cursor-pointer transition-colors',
                                            state.selectedLanguages.includes(language.code)
                                                ? 'border-blue-500 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                        )}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={state.selectedLanguages.includes(language.code)}
                                            onChange={() => handleLanguageToggle(language.code)}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-sm">
                                            {translationService.getLanguageFlag(language.code)} {language.name}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </details>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                        {state.selectedLanguages.length > 0 && (
                            <span>{state.selectedLanguages.length} language{state.selectedLanguages.length !== 1 ? 's' : ''} selected</span>
                        )}
                    </div>
                    <div className="flex items-center space-x-3">
                        {Object.keys(state.translations).length > 0 && (
                            <button
                                onClick={handleClearTranslations}
                                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                            >
                                Clear
                            </button>
                        )}
                        <button
                            onClick={handleTranslate}
                            disabled={state.isTranslating || state.selectedLanguages.length === 0 || !originalText}
                            className={cn(
                                'flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                                state.isTranslating || state.selectedLanguages.length === 0 || !originalText
                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    : 'bg-blue-600 text-white hover:bg-blue-700'
                            )}
                        >
                            {state.isTranslating ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Translating...</span>
                                </>
                            ) : (
                                <>
                                    <Languages className="w-4 h-4" />
                                    <span>Translate</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-md">
                        <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                        <span className="text-sm text-red-700">{error}</span>
                    </div>
                )}

                {/* Translation Results */}
                {Object.keys(state.translations).length > 0 && (
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-700">Translation Results</h4>

                        {/* Original Text */}
                        {state.showOriginal && originalText && (
                            <div className="p-4 bg-gray-50 rounded-md">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-gray-700">
                                        Original ({state.sourceLanguage ? translationService.getLanguageName(state.sourceLanguage) : 'Unknown'})
                                    </span>
                                </div>
                                <p className="text-sm text-gray-900 leading-relaxed">{originalText}</p>
                            </div>
                        )}

                        {/* Translations */}
                        <div className="space-y-3">
                            {Object.entries(state.translations).map(([languageCode, translation]) => (
                                <div key={languageCode} className="p-4 border border-gray-200 rounded-md">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-sm font-medium text-gray-700">
                                                {translationService.getLanguageFlag(languageCode)} {translationService.getLanguageName(languageCode)}
                                            </span>
                                            <span className={cn(
                                                'px-2 py-1 text-xs font-medium rounded-full',
                                                getQualityBadgeColor(translation.qualityScore)
                                            )}>
                                                {formatQualityScore(translation.qualityScore)}
                                            </span>
                                            {translation.cached && (
                                                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                                    Cached
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center space-x-1 text-xs text-gray-500">
                                            <span>{translationService.formatProcessingTime(translation.processingTime)}</span>
                                        </div>
                                    </div>
                                    <p
                                        className="text-sm text-gray-900 leading-relaxed"
                                        dir={translationService.getTextDirection(languageCode)}
                                    >
                                        {translation.translatedText}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TranslationPanel;