import React from 'react';
import { Languages, CheckCircle, AlertCircle, Clock, Loader2, Globe } from 'lucide-react';
import { translationService } from '../../services/translationService';
import { cn } from '../../utils';

interface TranslationStatusProps {
  status: 'idle' | 'detecting' | 'translating' | 'completed' | 'error';
  sourceLanguage?: string;
  targetLanguages?: string[];
  progress?: number;
  error?: string;
  translationCount?: number;
  processingTime?: number;
  cacheHitRate?: number;
  className?: string;
}

export const TranslationStatus: React.FC<TranslationStatusProps> = ({
  status,
  sourceLanguage,
  targetLanguages = [],
  progress = 0,
  error,
  translationCount = 0,
  processingTime,
  cacheHitRate,
  className
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'detecting':
        return <Globe className="w-4 h-4 text-blue-600 animate-pulse" />;
      case 'translating':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Languages className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'detecting':
        return 'Detecting language...';
      case 'translating':
        return `Translating to ${targetLanguages.length} language${targetLanguages.length !== 1 ? 's' : ''}...`;
      case 'completed':
        return `Translation completed (${translationCount} translation${translationCount !== 1 ? 's' : ''})`;
      case 'error':
        return 'Translation failed';
      default:
        return 'Ready to translate';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'detecting':
      case 'translating':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'completed':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={cn('rounded-lg border p-4', getStatusColor(), className)}>
      {/* Main Status */}
      <div className="flex items-center space-x-3">
        {getStatusIcon()}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{getStatusText()}</p>
          {error && (
            <p className="text-xs text-red-600 mt-1">{error}</p>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {status === 'translating' && progress > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Language Information */}
      {(sourceLanguage || targetLanguages.length > 0) && (
        <div className="mt-3 space-y-2">
          {sourceLanguage && (
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-gray-500">From:</span>
              <span className="flex items-center space-x-1">
                <span>{translationService.getLanguageFlag(sourceLanguage)}</span>
                <span className="font-medium">{translationService.getLanguageName(sourceLanguage)}</span>
              </span>
            </div>
          )}
          
          {targetLanguages.length > 0 && (
            <div className="flex items-start space-x-2 text-xs">
              <span className="text-gray-500 mt-0.5">To:</span>
              <div className="flex flex-wrap gap-1">
                {targetLanguages.map((langCode) => (
                  <span
                    key={langCode}
                    className="flex items-center space-x-1 px-2 py-1 bg-white bg-opacity-50 rounded-full"
                  >
                    <span>{translationService.getLanguageFlag(langCode)}</span>
                    <span className="font-medium">{translationService.getLanguageName(langCode)}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Statistics */}
      {status === 'completed' && (processingTime || cacheHitRate !== undefined) && (
        <div className="mt-3 pt-3 border-t border-current border-opacity-20">
          <div className="grid grid-cols-2 gap-4 text-xs">
            {processingTime && (
              <div className="flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span className="text-gray-600">Time:</span>
                <span className="font-medium">
                  {translationService.formatProcessingTime(processingTime)}
                </span>
              </div>
            )}
            
            {cacheHitRate !== undefined && (
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-gray-600">Cache:</span>
                <span className="font-medium">
                  {Math.round(cacheHitRate * 100)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TranslationStatus;