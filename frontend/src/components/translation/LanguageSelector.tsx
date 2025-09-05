import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, Globe, Search, Check } from 'lucide-react';
import { translationService, SupportedLanguage } from '../../services/translationService';
import { cn } from '../../utils';

interface LanguageSelectorProps {
  value?: string;
  onChange: (languageCode: string) => void;
  placeholder?: string;
  disabled?: boolean;
  showFlags?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'minimal';
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  value,
  onChange,
  placeholder = 'Select language',
  disabled = false,
  showFlags = true,
  className,
  size = 'md',
  variant = 'default'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>([]);
  const [loading, setLoading] = useState(true);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Load supported languages
  useEffect(() => {
    const loadLanguages = async () => {
      try {
        const languages = await translationService.getSupportedLanguages();
        setSupportedLanguages(languages);
      } catch (error) {
        console.error('Failed to load supported languages:', error);
      } finally {
        setLoading(false);
      }
    };

    loadLanguages();
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Filter languages based on search query
  const filteredLanguages = supportedLanguages.filter(language =>
    language.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    language.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Get selected language info
  const selectedLanguage = supportedLanguages.find(lang => lang.code === value);

  // Handle language selection
  const handleSelect = (languageCode: string) => {
    onChange(languageCode);
    setIsOpen(false);
    setSearchQuery('');
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
      setSearchQuery('');
    } else if (event.key === 'Enter' && !isOpen) {
      setIsOpen(true);
    }
  };

  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };

  // Variant classes
  const variantClasses = {
    default: 'border border-gray-300 bg-white shadow-sm',
    minimal: 'border-0 bg-transparent'
  };

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-between rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
          sizeClasses[size],
          variantClasses[variant],
          disabled
            ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
            : 'hover:border-gray-400 cursor-pointer',
          isOpen && 'border-blue-500 ring-2 ring-blue-500'
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Select language"
      >
        <div className="flex items-center space-x-2 min-w-0">
          {loading ? (
            <>
              <div className="w-4 h-4 bg-gray-200 rounded animate-pulse" />
              <span className="text-gray-400">Loading...</span>
            </>
          ) : selectedLanguage ? (
            <>
              {showFlags && (
                <span className="text-base flex-shrink-0">
                  {translationService.getLanguageFlag(selectedLanguage.code)}
                </span>
              )}
              <span className="truncate">{selectedLanguage.name}</span>
            </>
          ) : (
            <>
              <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="text-gray-500 truncate">{placeholder}</span>
            </>
          )}
        </div>
        <ChevronDown 
          className={cn(
            'w-4 h-4 text-gray-400 transition-transform flex-shrink-0',
            isOpen && 'transform rotate-180'
          )} 
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-hidden">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search languages..."
                className="w-full pl-8 pr-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Language List */}
          <div className="max-h-48 overflow-y-auto">
            {filteredLanguages.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500 text-center">
                No languages found
              </div>
            ) : (
              <div role="listbox">
                {filteredLanguages.map((language) => (
                  <button
                    key={language.code}
                    type="button"
                    onClick={() => handleSelect(language.code)}
                    className={cn(
                      'w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50',
                      value === language.code && 'bg-blue-50 text-blue-700'
                    )}
                    role="option"
                    aria-selected={value === language.code}
                  >
                    <div className="flex items-center space-x-2 min-w-0">
                      {showFlags && (
                        <span className="text-base flex-shrink-0">
                          {translationService.getLanguageFlag(language.code)}
                        </span>
                      )}
                      <span className="truncate">{language.name}</span>
                      <span className="text-xs text-gray-400 uppercase">
                        {language.code}
                      </span>
                    </div>
                    {value === language.code && (
                      <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;