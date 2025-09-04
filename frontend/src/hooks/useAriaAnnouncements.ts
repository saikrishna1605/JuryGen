import { useCallback, useRef } from 'react';

export type AnnouncementPriority = 'polite' | 'assertive' | 'off';

export interface AnnouncementOptions {
  priority?: AnnouncementPriority;
  delay?: number;
  clearPrevious?: boolean;
}

/**
 * Hook for making announcements to screen readers
 */
export const useAriaAnnouncements = () => {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Create or get the announcement region
  const getAnnouncementRegion = useCallback((priority: AnnouncementPriority = 'polite') => {
    const regionId = `aria-announcement-${priority}`;
    let region = document.getElementById(regionId) as HTMLDivElement;
    
    if (!region) {
      region = document.createElement('div');
      region.id = regionId;
      region.setAttribute('aria-live', priority);
      region.setAttribute('aria-atomic', 'true');
      region.className = 'sr-only';
      region.style.position = 'absolute';
      region.style.left = '-10000px';
      region.style.width = '1px';
      region.style.height = '1px';
      region.style.overflow = 'hidden';
      document.body.appendChild(region);
    }
    
    return region;
  }, []);

  // Announce a message to screen readers
  const announce = useCallback((
    message: string,
    options: AnnouncementOptions = {}
  ) => {
    const {
      priority = 'polite',
      delay = 100,
      clearPrevious = true
    } = options;

    if (!message.trim()) return;

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const region = getAnnouncementRegion(priority);

    // Clear previous announcement if requested
    if (clearPrevious) {
      region.textContent = '';
    }

    // Announce after a small delay to ensure screen readers pick it up
    timeoutRef.current = setTimeout(() => {
      region.textContent = message;
      
      // Clear the announcement after it's been read
      setTimeout(() => {
        if (region.textContent === message) {
          region.textContent = '';
        }
      }, 1000);
    }, delay);
  }, [getAnnouncementRegion]);

  // Announce status changes
  const announceStatus = useCallback((status: string, context?: string) => {
    const message = context ? `${context}: ${status}` : status;
    announce(message, { priority: 'polite' });
  }, [announce]);

  // Announce errors
  const announceError = useCallback((error: string, context?: string) => {
    const message = context ? `Error in ${context}: ${error}` : `Error: ${error}`;
    announce(message, { priority: 'assertive' });
  }, [announce]);

  // Announce success messages
  const announceSuccess = useCallback((message: string, context?: string) => {
    const fullMessage = context ? `${context}: ${message}` : message;
    announce(fullMessage, { priority: 'polite' });
  }, [announce]);

  // Announce navigation changes
  const announceNavigation = useCallback((location: string, context?: string) => {
    const message = context 
      ? `Navigated to ${location} in ${context}`
      : `Navigated to ${location}`;
    announce(message, { priority: 'polite' });
  }, [announce]);

  // Announce loading states
  const announceLoading = useCallback((isLoading: boolean, context?: string) => {
    const message = isLoading 
      ? (context ? `Loading ${context}` : 'Loading')
      : (context ? `${context} loaded` : 'Loading complete');
    announce(message, { priority: 'polite' });
  }, [announce]);

  // Announce form validation
  const announceValidation = useCallback((
    fieldName: string,
    isValid: boolean,
    errorMessage?: string
  ) => {
    if (isValid) {
      announce(`${fieldName} is valid`, { priority: 'polite' });
    } else {
      const message = errorMessage 
        ? `${fieldName}: ${errorMessage}`
        : `${fieldName} is invalid`;
      announce(message, { priority: 'assertive' });
    }
  }, [announce]);

  // Announce progress updates
  const announceProgress = useCallback((
    current: number,
    total: number,
    context?: string
  ) => {
    const percentage = Math.round((current / total) * 100);
    const message = context 
      ? `${context}: ${percentage}% complete, ${current} of ${total}`
      : `${percentage}% complete, ${current} of ${total}`;
    announce(message, { priority: 'polite' });
  }, [announce]);

  return {
    announce,
    announceStatus,
    announceError,
    announceSuccess,
    announceNavigation,
    announceLoading,
    announceValidation,
    announceProgress,
  };
};