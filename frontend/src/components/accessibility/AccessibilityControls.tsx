import React, { useState } from 'react';
import {
  Settings,
  Eye,
  Type,
  Palette,
  Volume2,
  Navigation,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Sun,
  Moon,
  Contrast,
  Minus,
  Plus,
  Play,
  Pause,
} from 'lucide-react';
import { useAccessibility } from '../../contexts/AccessibilityContext';
import { cn } from '../../lib/utils';

interface AccessibilityControlsProps {
  className?: string;
  compact?: boolean;
  showLabels?: boolean;
}

export const AccessibilityControls: React.FC<AccessibilityControlsProps> = ({
  className,
  compact = false,
  showLabels = true,
}) => {
  const {
    state,
    dispatch,
    setTheme,
    setFontSize,
    setFontFamily,
    toggleHighContrast,
    toggleReduceMotion,
    resetToDefaults,
    announceToScreenReader,
  } = useAccessibility();

  const [isExpanded, setIsExpanded] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);

  // Handle theme change
  const handleThemeChange = (theme: typeof state.theme) => {
    setTheme(theme);
    announceToScreenReader(`Theme changed to ${theme}`);
  };

  // Handle font size change
  const handleFontSizeChange = (size: typeof state.fontSize) => {
    setFontSize(size);
    announceToScreenReader(`Font size changed to ${size}`);
  };

  // Handle font family change
  const handleFontFamilyChange = (family: typeof state.fontFamily) => {
    setFontFamily(family);
    announceToScreenReader(`Font family changed to ${family}`);
  };

  // Handle toggle with announcement
  const handleToggle = (action: () => void, feature: string, enabled: boolean) => {
    action();
    announceToScreenReader(`${feature} ${enabled ? 'disabled' : 'enabled'}`);
  };

  // Reset all settings
  const handleReset = () => {
    resetToDefaults();
    announceToScreenReader('Accessibility settings reset to defaults');
  };

  // Toggle section
  const toggleSection = (section: string) => {
    setActiveSection(activeSection === section ? null : section);
  };

  if (compact) {
    return (
      <div className={cn('accessibility-controls-compact', className)}>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 transition-colors"
          aria-label="Toggle accessibility controls"
          aria-expanded={isExpanded}
        >
          <Settings className="w-5 h-5" />
        </button>

        {isExpanded && (
          <div className="absolute top-full right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
            <div className="p-4">
              <h3 className="text-lg font-semibold mb-4">Accessibility Settings</h3>
              
              {/* Quick toggles */}
              <div className="grid grid-cols-2 gap-2 mb-4">
                <button
                  onClick={() => handleToggle(toggleHighContrast, 'High contrast', state.highContrast)}
                  className={cn(
                    'p-2 rounded-md text-sm transition-colors',
                    state.highContrast
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  )}
                >
                  <Contrast className="w-4 h-4 mx-auto mb-1" />
                  High Contrast
                </button>
                
                <button
                  onClick={() => handleToggle(toggleReduceMotion, 'Reduce motion', state.reduceMotion)}
                  className={cn(
                    'p-2 rounded-md text-sm transition-colors',
                    state.reduceMotion
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  )}
                >
                  {state.reduceMotion ? <Pause className="w-4 h-4 mx-auto mb-1" /> : <Play className="w-4 h-4 mx-auto mb-1" />}
                  Reduce Motion
                </button>
              </div>

              {/* Font size controls */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Font Size</label>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      const sizes = ['small', 'medium', 'large', 'extra-large'] as const;
                      const currentIndex = sizes.indexOf(state.fontSize);
                      if (currentIndex > 0) {
                        handleFontSizeChange(sizes[currentIndex - 1]);
                      }
                    }}
                    disabled={state.fontSize === 'small'}
                    className="p-1 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  
                  <span className="flex-1 text-center text-sm">{state.fontSize}</span>
                  
                  <button
                    onClick={() => {
                      const sizes = ['small', 'medium', 'large', 'extra-large'] as const;
                      const currentIndex = sizes.indexOf(state.fontSize);
                      if (currentIndex < sizes.length - 1) {
                        handleFontSizeChange(sizes[currentIndex + 1]);
                      }
                    }}
                    disabled={state.fontSize === 'extra-large'}
                    className="p-1 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Reset button */}
              <button
                onClick={handleReset}
                className="w-full p-2 bg-gray-100 hover:bg-gray-200 rounded-md text-sm transition-colors"
              >
                <RotateCcw className="w-4 h-4 inline mr-2" />
                Reset to Defaults
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn('accessibility-controls bg-white border border-gray-200 rounded-lg shadow-sm', className)}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Accessibility Settings
          </h2>
          <button
            onClick={handleReset}
            className="text-sm text-gray-600 hover:text-gray-800 flex items-center"
            title="Reset all settings to defaults"
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset
          </button>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {/* Theme Settings */}
        <div className="p-4">
          <button
            onClick={() => toggleSection('theme')}
            className="w-full flex items-center justify-between text-left"
            aria-expanded={activeSection === 'theme'}
          >
            <div className="flex items-center">
              <Palette className="w-5 h-5 mr-2" />
              <span className="font-medium">Theme & Colors</span>
            </div>
            {activeSection === 'theme' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {activeSection === 'theme' && (
            <div className="mt-4 space-y-4">
              {/* Theme selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Color Theme</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'light', label: 'Light', icon: Sun },
                    { value: 'dark', label: 'Dark', icon: Moon },
                    { value: 'high-contrast', label: 'High Contrast', icon: Contrast },
                  ].map(({ value, label, icon: Icon }) => (
                    <button
                      key={value}
                      onClick={() => handleThemeChange(value as typeof state.theme)}
                      className={cn(
                        'p-3 rounded-md border text-sm transition-colors',
                        state.theme === value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <Icon className="w-4 h-4 mx-auto mb-1" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* High contrast toggle */}
              <div className="flex items-center justify-between">
                <label htmlFor="high-contrast" className="text-sm font-medium">
                  Enhanced High Contrast
                </label>
                <button
                  id="high-contrast"
                  onClick={() => handleToggle(toggleHighContrast, 'High contrast', state.highContrast)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.highContrast ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.highContrast}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.highContrast ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>

              {/* Color blind friendly toggle */}
              <div className="flex items-center justify-between">
                <label htmlFor="color-blind-friendly" className="text-sm font-medium">
                  Color Blind Friendly
                </label>
                <button
                  id="color-blind-friendly"
                  onClick={() => handleToggle(() => dispatch({ type: 'TOGGLE_COLOR_BLIND_FRIENDLY' }), 'Color blind friendly mode', state.colorBlindFriendly)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.colorBlindFriendly ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.colorBlindFriendly}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.colorBlindFriendly ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Typography Settings */}
        <div className="p-4">
          <button
            onClick={() => toggleSection('typography')}
            className="w-full flex items-center justify-between text-left"
            aria-expanded={activeSection === 'typography'}
          >
            <div className="flex items-center">
              <Type className="w-5 h-5 mr-2" />
              <span className="font-medium">Typography</span>
            </div>
            {activeSection === 'typography' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {activeSection === 'typography' && (
            <div className="mt-4 space-y-4">
              {/* Font size */}
              <div>
                <label className="block text-sm font-medium mb-2">Font Size</label>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { value: 'small', label: 'Small' },
                    { value: 'medium', label: 'Medium' },
                    { value: 'large', label: 'Large' },
                    { value: 'extra-large', label: 'Extra Large' },
                  ].map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => handleFontSizeChange(value as typeof state.fontSize)}
                      className={cn(
                        'p-2 rounded-md border text-sm transition-colors',
                        state.fontSize === value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Font family */}
              <div>
                <label className="block text-sm font-medium mb-2">Font Family</label>
                <div className="space-y-2">
                  {[
                    { value: 'default', label: 'Default (Sans-serif)' },
                    { value: 'dyslexia-friendly', label: 'Dyslexia Friendly' },
                    { value: 'serif', label: 'Serif' },
                    { value: 'monospace', label: 'Monospace' },
                  ].map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => handleFontFamilyChange(value as typeof state.fontFamily)}
                      className={cn(
                        'w-full p-2 rounded-md border text-left text-sm transition-colors',
                        state.fontFamily === value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Line height */}
              <div>
                <label className="block text-sm font-medium mb-2">Line Height</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'normal', label: 'Normal' },
                    { value: 'relaxed', label: 'Relaxed' },
                    { value: 'loose', label: 'Loose' },
                  ].map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => {
                        dispatch({ type: 'SET_LINE_HEIGHT', payload: value as typeof state.lineHeight });
                        announceToScreenReader(`Line height changed to ${label}`);
                      }}
                      className={cn(
                        'p-2 rounded-md border text-sm transition-colors',
                        state.lineHeight === value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Letter spacing */}
              <div>
                <label className="block text-sm font-medium mb-2">Letter Spacing</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'normal', label: 'Normal' },
                    { value: 'wide', label: 'Wide' },
                    { value: 'wider', label: 'Wider' },
                  ].map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => {
                        dispatch({ type: 'SET_LETTER_SPACING', payload: value as typeof state.letterSpacing });
                        announceToScreenReader(`Letter spacing changed to ${label}`);
                      }}
                      className={cn(
                        'p-2 rounded-md border text-sm transition-colors',
                        state.letterSpacing === value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Motion & Animation */}
        <div className="p-4">
          <button
            onClick={() => toggleSection('motion')}
            className="w-full flex items-center justify-between text-left"
            aria-expanded={activeSection === 'motion'}
          >
            <div className="flex items-center">
              <Play className="w-5 h-5 mr-2" />
              <span className="font-medium">Motion & Animation</span>
            </div>
            {activeSection === 'motion' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {activeSection === 'motion' && (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <label htmlFor="reduce-motion" className="text-sm font-medium">
                  Reduce Motion
                </label>
                <button
                  id="reduce-motion"
                  onClick={() => handleToggle(toggleReduceMotion, 'Reduce motion', state.reduceMotion)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.reduceMotion ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.reduceMotion}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.reduceMotion ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Navigation & Focus */}
        <div className="p-4">
          <button
            onClick={() => toggleSection('navigation')}
            className="w-full flex items-center justify-between text-left"
            aria-expanded={activeSection === 'navigation'}
          >
            <div className="flex items-center">
              <Navigation className="w-5 h-5 mr-2" />
              <span className="font-medium">Navigation & Focus</span>
            </div>
            {activeSection === 'navigation' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {activeSection === 'navigation' && (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <label htmlFor="focus-visible" className="text-sm font-medium">
                  Enhanced Focus Indicators
                </label>
                <button
                  id="focus-visible"
                  onClick={() => handleToggle(() => dispatch({ type: 'TOGGLE_FOCUS_VISIBLE' }), 'Focus indicators', state.focusVisible)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.focusVisible ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.focusVisible}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.focusVisible ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <label htmlFor="keyboard-navigation" className="text-sm font-medium">
                  Keyboard Navigation
                </label>
                <button
                  id="keyboard-navigation"
                  onClick={() => handleToggle(() => dispatch({ type: 'TOGGLE_KEYBOARD_NAVIGATION' }), 'Keyboard navigation', state.keyboardNavigation)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.keyboardNavigation ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.keyboardNavigation}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.keyboardNavigation ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <label htmlFor="underline-links" className="text-sm font-medium">
                  Underline Links
                </label>
                <button
                  id="underline-links"
                  onClick={() => handleToggle(() => dispatch({ type: 'TOGGLE_UNDERLINE_LINKS' }), 'Link underlines', state.underlineLinks)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.underlineLinks ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.underlineLinks}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.underlineLinks ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Screen Reader */}
        <div className="p-4">
          <button
            onClick={() => toggleSection('screen-reader')}
            className="w-full flex items-center justify-between text-left"
            aria-expanded={activeSection === 'screen-reader'}
          >
            <div className="flex items-center">
              <Volume2 className="w-5 h-5 mr-2" />
              <span className="font-medium">Screen Reader</span>
            </div>
            {activeSection === 'screen-reader' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {activeSection === 'screen-reader' && (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <label htmlFor="screen-reader-optimized" className="text-sm font-medium">
                  Screen Reader Optimized
                </label>
                <button
                  id="screen-reader-optimized"
                  onClick={() => handleToggle(() => dispatch({ type: 'TOGGLE_SCREEN_READER_OPTIMIZED' }), 'Screen reader optimization', state.screenReaderOptimized)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.screenReaderOptimized ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.screenReaderOptimized}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.screenReaderOptimized ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <label htmlFor="announce-changes" className="text-sm font-medium">
                  Announce Changes
                </label>
                <button
                  id="announce-changes"
                  onClick={() => handleToggle(() => dispatch({ type: 'TOGGLE_ANNOUNCE_CHANGES' }), 'Change announcements', state.announceChanges)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    state.announceChanges ? 'bg-blue-600' : 'bg-gray-200'
                  )}
                  role="switch"
                  aria-checked={state.announceChanges}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      state.announceChanges ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AccessibilityControls;