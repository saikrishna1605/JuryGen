import React, { createContext, useContext, useReducer, useEffect } from 'react';

// Accessibility state interface
export interface AccessibilityState {
  // Theme settings
  theme: 'light' | 'dark' | 'high-contrast';
  
  // Font settings
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  fontFamily: 'default' | 'dyslexia-friendly' | 'serif' | 'monospace';
  lineHeight: 'normal' | 'relaxed' | 'loose';
  letterSpacing: 'normal' | 'wide' | 'wider';
  
  // Motion and animation
  reduceMotion: boolean;
  
  // Focus and navigation
  focusVisible: boolean;
  keyboardNavigation: boolean;
  
  // Screen reader support
  screenReaderOptimized: boolean;
  announceChanges: boolean;
  
  // Color and contrast
  highContrast: boolean;
  colorBlindFriendly: boolean;
  
  // Layout and spacing
  compactMode: boolean;
  increasedSpacing: boolean;
  
  // Audio settings
  audioDescriptions: boolean;
  captionsEnabled: boolean;
  
  // Reading assistance
  readingGuide: boolean;
  highlightLinks: boolean;
  underlineLinks: boolean;
}

// Default accessibility state
const defaultState: AccessibilityState = {
  theme: 'light',
  fontSize: 'medium',
  fontFamily: 'default',
  lineHeight: 'normal',
  letterSpacing: 'normal',
  reduceMotion: false,
  focusVisible: true,
  keyboardNavigation: true,
  screenReaderOptimized: false,
  announceChanges: true,
  highContrast: false,
  colorBlindFriendly: false,
  compactMode: false,
  increasedSpacing: false,
  audioDescriptions: false,
  captionsEnabled: false,
  readingGuide: false,
  highlightLinks: false,
  underlineLinks: true,
};

// Action types
type AccessibilityAction =
  | { type: 'SET_THEME'; payload: AccessibilityState['theme'] }
  | { type: 'SET_FONT_SIZE'; payload: AccessibilityState['fontSize'] }
  | { type: 'SET_FONT_FAMILY'; payload: AccessibilityState['fontFamily'] }
  | { type: 'SET_LINE_HEIGHT'; payload: AccessibilityState['lineHeight'] }
  | { type: 'SET_LETTER_SPACING'; payload: AccessibilityState['letterSpacing'] }
  | { type: 'TOGGLE_REDUCE_MOTION' }
  | { type: 'TOGGLE_FOCUS_VISIBLE' }
  | { type: 'TOGGLE_KEYBOARD_NAVIGATION' }
  | { type: 'TOGGLE_SCREEN_READER_OPTIMIZED' }
  | { type: 'TOGGLE_ANNOUNCE_CHANGES' }
  | { type: 'TOGGLE_HIGH_CONTRAST' }
  | { type: 'TOGGLE_COLOR_BLIND_FRIENDLY' }
  | { type: 'TOGGLE_COMPACT_MODE' }
  | { type: 'TOGGLE_INCREASED_SPACING' }
  | { type: 'TOGGLE_AUDIO_DESCRIPTIONS' }
  | { type: 'TOGGLE_CAPTIONS' }
  | { type: 'TOGGLE_READING_GUIDE' }
  | { type: 'TOGGLE_HIGHLIGHT_LINKS' }
  | { type: 'TOGGLE_UNDERLINE_LINKS' }
  | { type: 'RESET_TO_DEFAULTS' }
  | { type: 'LOAD_PREFERENCES'; payload: Partial<AccessibilityState> };

// Reducer function
function accessibilityReducer(
  state: AccessibilityState,
  action: AccessibilityAction
): AccessibilityState {
  switch (action.type) {
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    case 'SET_FONT_SIZE':
      return { ...state, fontSize: action.payload };
    case 'SET_FONT_FAMILY':
      return { ...state, fontFamily: action.payload };
    case 'SET_LINE_HEIGHT':
      return { ...state, lineHeight: action.payload };
    case 'SET_LETTER_SPACING':
      return { ...state, letterSpacing: action.payload };
    case 'TOGGLE_REDUCE_MOTION':
      return { ...state, reduceMotion: !state.reduceMotion };
    case 'TOGGLE_FOCUS_VISIBLE':
      return { ...state, focusVisible: !state.focusVisible };
    case 'TOGGLE_KEYBOARD_NAVIGATION':
      return { ...state, keyboardNavigation: !state.keyboardNavigation };
    case 'TOGGLE_SCREEN_READER_OPTIMIZED':
      return { ...state, screenReaderOptimized: !state.screenReaderOptimized };
    case 'TOGGLE_ANNOUNCE_CHANGES':
      return { ...state, announceChanges: !state.announceChanges };
    case 'TOGGLE_HIGH_CONTRAST':
      return { ...state, highContrast: !state.highContrast };
    case 'TOGGLE_COLOR_BLIND_FRIENDLY':
      return { ...state, colorBlindFriendly: !state.colorBlindFriendly };
    case 'TOGGLE_COMPACT_MODE':
      return { ...state, compactMode: !state.compactMode };
    case 'TOGGLE_INCREASED_SPACING':
      return { ...state, increasedSpacing: !state.increasedSpacing };
    case 'TOGGLE_AUDIO_DESCRIPTIONS':
      return { ...state, audioDescriptions: !state.audioDescriptions };
    case 'TOGGLE_CAPTIONS':
      return { ...state, captionsEnabled: !state.captionsEnabled };
    case 'TOGGLE_READING_GUIDE':
      return { ...state, readingGuide: !state.readingGuide };
    case 'TOGGLE_HIGHLIGHT_LINKS':
      return { ...state, highlightLinks: !state.highlightLinks };
    case 'TOGGLE_UNDERLINE_LINKS':
      return { ...state, underlineLinks: !state.underlineLinks };
    case 'RESET_TO_DEFAULTS':
      return defaultState;
    case 'LOAD_PREFERENCES':
      return { ...state, ...action.payload };
    default:
      return state;
  }
}

// Context interface
interface AccessibilityContextType {
  state: AccessibilityState;
  dispatch: React.Dispatch<AccessibilityAction>;
  
  // Convenience methods
  setTheme: (theme: AccessibilityState['theme']) => void;
  setFontSize: (size: AccessibilityState['fontSize']) => void;
  setFontFamily: (family: AccessibilityState['fontFamily']) => void;
  toggleHighContrast: () => void;
  toggleReduceMotion: () => void;
  resetToDefaults: () => void;
  savePreferences: () => void;
  loadPreferences: () => void;
  
  // Utility methods
  getCSSVariables: () => Record<string, string>;
  getClassName: () => string;
  announceToScreenReader: (message: string) => void;
}

// Create context
const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

// Storage key for preferences
const STORAGE_KEY = 'accessibility-preferences';

// Provider component
export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(accessibilityReducer, defaultState);

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
  }, []);

  // Save preferences when state changes
  useEffect(() => {
    savePreferences();
  }, [state]);

  // Apply CSS variables and classes when state changes
  useEffect(() => {
    applyAccessibilityStyles();
  }, [state]);

  // Detect system preferences
  useEffect(() => {
    detectSystemPreferences();
  }, []);

  // Convenience methods
  const setTheme = (theme: AccessibilityState['theme']) => {
    dispatch({ type: 'SET_THEME', payload: theme });
  };

  const setFontSize = (size: AccessibilityState['fontSize']) => {
    dispatch({ type: 'SET_FONT_SIZE', payload: size });
  };

  const setFontFamily = (family: AccessibilityState['fontFamily']) => {
    dispatch({ type: 'SET_FONT_FAMILY', payload: family });
  };

  const toggleHighContrast = () => {
    dispatch({ type: 'TOGGLE_HIGH_CONTRAST' });
  };

  const toggleReduceMotion = () => {
    dispatch({ type: 'TOGGLE_REDUCE_MOTION' });
  };

  const resetToDefaults = () => {
    dispatch({ type: 'RESET_TO_DEFAULTS' });
  };

  const savePreferences = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.warn('Failed to save accessibility preferences:', error);
    }
  };

  const loadPreferences = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const preferences = JSON.parse(saved);
        dispatch({ type: 'LOAD_PREFERENCES', payload: preferences });
      }
    } catch (error) {
      console.warn('Failed to load accessibility preferences:', error);
    }
  };

  // Detect system preferences
  const detectSystemPreferences = () => {
    // Detect dark mode preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    }

    // Detect reduced motion preference
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      dispatch({ type: 'TOGGLE_REDUCE_MOTION' });
    }

    // Detect high contrast preference
    if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
      dispatch({ type: 'TOGGLE_HIGH_CONTRAST' });
    }
  };

  // Apply accessibility styles to document
  const applyAccessibilityStyles = () => {
    const root = document.documentElement;
    const cssVariables = getCSSVariables();

    // Apply CSS variables
    Object.entries(cssVariables).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });

    // Apply classes
    const className = getClassName();
    root.className = className;

    // Apply reduce motion
    if (state.reduceMotion) {
      root.style.setProperty('--animation-duration', '0s');
      root.style.setProperty('--transition-duration', '0s');
    } else {
      root.style.removeProperty('--animation-duration');
      root.style.removeProperty('--transition-duration');
    }
  };

  // Get CSS variables based on current state
  const getCSSVariables = (): Record<string, string> => {
    const variables: Record<string, string> = {};

    // Font size variables
    const fontSizeMap = {
      small: '14px',
      medium: '16px',
      large: '18px',
      'extra-large': '22px',
    };
    variables['--base-font-size'] = fontSizeMap[state.fontSize];

    // Font family variables
    const fontFamilyMap = {
      default: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      'dyslexia-friendly': '"OpenDyslexic", "Comic Sans MS", cursive',
      serif: 'Georgia, "Times New Roman", serif',
      monospace: '"Fira Code", "Courier New", monospace',
    };
    variables['--font-family'] = fontFamilyMap[state.fontFamily];

    // Line height variables
    const lineHeightMap = {
      normal: '1.5',
      relaxed: '1.75',
      loose: '2',
    };
    variables['--line-height'] = lineHeightMap[state.lineHeight];

    // Letter spacing variables
    const letterSpacingMap = {
      normal: '0',
      wide: '0.025em',
      wider: '0.05em',
    };
    variables['--letter-spacing'] = letterSpacingMap[state.letterSpacing];

    // Theme colors
    if (state.theme === 'dark') {
      variables['--bg-primary'] = '#1a1a1a';
      variables['--bg-secondary'] = '#2d2d2d';
      variables['--text-primary'] = '#ffffff';
      variables['--text-secondary'] = '#cccccc';
      variables['--border-color'] = '#404040';
    } else if (state.theme === 'high-contrast') {
      variables['--bg-primary'] = '#000000';
      variables['--bg-secondary'] = '#ffffff';
      variables['--text-primary'] = '#ffffff';
      variables['--text-secondary'] = '#000000';
      variables['--border-color'] = '#ffffff';
    } else {
      variables['--bg-primary'] = '#ffffff';
      variables['--bg-secondary'] = '#f8f9fa';
      variables['--text-primary'] = '#212529';
      variables['--text-secondary'] = '#6c757d';
      variables['--border-color'] = '#dee2e6';
    }

    // Spacing variables
    if (state.increasedSpacing) {
      variables['--spacing-multiplier'] = '1.5';
    } else if (state.compactMode) {
      variables['--spacing-multiplier'] = '0.75';
    } else {
      variables['--spacing-multiplier'] = '1';
    }

    return variables;
  };

  // Get CSS class names based on current state
  const getClassName = (): string => {
    const classes = ['accessibility-enabled'];

    classes.push(`theme-${state.theme}`);
    classes.push(`font-size-${state.fontSize}`);
    classes.push(`font-family-${state.fontFamily}`);
    classes.push(`line-height-${state.lineHeight}`);
    classes.push(`letter-spacing-${state.letterSpacing}`);

    if (state.reduceMotion) classes.push('reduce-motion');
    if (state.focusVisible) classes.push('focus-visible');
    if (state.keyboardNavigation) classes.push('keyboard-navigation');
    if (state.screenReaderOptimized) classes.push('screen-reader-optimized');
    if (state.highContrast) classes.push('high-contrast');
    if (state.colorBlindFriendly) classes.push('color-blind-friendly');
    if (state.compactMode) classes.push('compact-mode');
    if (state.increasedSpacing) classes.push('increased-spacing');
    if (state.readingGuide) classes.push('reading-guide');
    if (state.highlightLinks) classes.push('highlight-links');
    if (state.underlineLinks) classes.push('underline-links');

    return classes.join(' ');
  };

  // Announce messages to screen readers
  const announceToScreenReader = (message: string) => {
    if (!state.announceChanges) return;

    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };

  const contextValue: AccessibilityContextType = {
    state,
    dispatch,
    setTheme,
    setFontSize,
    setFontFamily,
    toggleHighContrast,
    toggleReduceMotion,
    resetToDefaults,
    savePreferences,
    loadPreferences,
    getCSSVariables,
    getClassName,
    announceToScreenReader,
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
};

// Hook to use accessibility context
export const useAccessibility = (): AccessibilityContextType => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

// Hook to get accessibility-aware CSS classes
export const useAccessibilityClasses = (baseClasses: string = ''): string => {
  const { getClassName } = useAccessibility();
  const accessibilityClasses = getClassName();
  return `${baseClasses} ${accessibilityClasses}`.trim();
};

// Hook to announce messages to screen readers
export const useScreenReaderAnnouncement = () => {
  const { announceToScreenReader } = useAccessibility();
  return announceToScreenReader;
};