import { useCallback, useRef } from 'react';

export interface FocusOptions {
  preventScroll?: boolean;
  selectText?: boolean;
  delay?: number;
}

/**
 * Hook for managing focus in accessible applications
 */
export const useFocusManagement = () => {
  const focusHistoryRef = useRef<HTMLElement[]>([]);
  const trapRef = useRef<HTMLElement | null>(null);

  // Focus an element with options
  const focusElement = useCallback((
    element: HTMLElement | null,
    options: FocusOptions = {}
  ) => {
    if (!element) return;

    const { preventScroll = false, selectText = false, delay = 0 } = options;

    const doFocus = () => {
      try {
        element.focus({ preventScroll });
        
        if (selectText && (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) {
          element.select();
        }
      } catch (error) {
        console.warn('Failed to focus element:', error);
      }
    };

    if (delay > 0) {
      setTimeout(doFocus, delay);
    } else {
      doFocus();
    }
  }, []);

  // Focus by selector
  const focusBySelector = useCallback((
    selector: string,
    options: FocusOptions = {}
  ) => {
    const element = document.querySelector(selector) as HTMLElement;
    focusElement(element, options);
  }, [focusElement]);

  // Focus the first focusable element in a container
  const focusFirst = useCallback((
    container: HTMLElement | null,
    options: FocusOptions = {}
  ) => {
    if (!container) return;

    const focusableElements = getFocusableElements(container);
    if (focusableElements.length > 0) {
      focusElement(focusableElements[0], options);
    }
  }, [focusElement]);

  // Focus the last focusable element in a container
  const focusLast = useCallback((
    container: HTMLElement | null,
    options: FocusOptions = {}
  ) => {
    if (!container) return;

    const focusableElements = getFocusableElements(container);
    if (focusableElements.length > 0) {
      focusElement(focusableElements[focusableElements.length - 1], options);
    }
  }, [focusElement]);

  // Save current focus to history
  const saveFocus = useCallback(() => {
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement && activeElement !== document.body) {
      focusHistoryRef.current.push(activeElement);
    }
  }, []);

  // Restore focus from history
  const restoreFocus = useCallback((options: FocusOptions = {}) => {
    const lastFocused = focusHistoryRef.current.pop();
    if (lastFocused && document.contains(lastFocused)) {
      focusElement(lastFocused, options);
      return true;
    }
    return false;
  }, [focusElement]);

  // Clear focus history
  const clearFocusHistory = useCallback(() => {
    focusHistoryRef.current = [];
  }, []);

  // Set up focus trap
  const trapFocus = useCallback((container: HTMLElement | null) => {
    if (!container) return;

    trapRef.current = container;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab' || !trapRef.current) return;

      const focusableElements = getFocusableElements(trapRef.current);
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      const activeElement = document.activeElement as HTMLElement;

      if (event.shiftKey) {
        // Shift + Tab
        if (activeElement === firstElement) {
          event.preventDefault();
          focusElement(lastElement);
        }
      } else {
        // Tab
        if (activeElement === lastElement) {
          event.preventDefault();
          focusElement(firstElement);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    // Focus the first element in the trap
    focusFirst(container, { delay: 100 });

    // Return cleanup function
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      trapRef.current = null;
    };
  }, [focusElement, focusFirst]);

  // Release focus trap
  const releaseFocusTrap = useCallback(() => {
    trapRef.current = null;
  }, []);

  // Handle roving tabindex
  const setupRovingTabindex = useCallback((
    container: HTMLElement,
    items: HTMLElement[],
    orientation: 'horizontal' | 'vertical' = 'horizontal'
  ) => {
    let currentIndex = 0;

    // Set initial tabindex values
    items.forEach((item, index) => {
      item.setAttribute('tabindex', index === 0 ? '0' : '-1');
    });

    const handleKeyDown = (event: KeyboardEvent) => {
      const { key } = event;
      let newIndex = currentIndex;

      if (orientation === 'horizontal') {
        if (key === 'ArrowLeft') {
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        } else if (key === 'ArrowRight') {
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        }
      } else {
        if (key === 'ArrowUp') {
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        } else if (key === 'ArrowDown') {
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        }
      }

      if (key === 'Home') {
        newIndex = 0;
      } else if (key === 'End') {
        newIndex = items.length - 1;
      }

      if (newIndex !== currentIndex) {
        event.preventDefault();
        
        // Update tabindex values
        items[currentIndex].setAttribute('tabindex', '-1');
        items[newIndex].setAttribute('tabindex', '0');
        
        // Focus new item
        focusElement(items[newIndex]);
        
        currentIndex = newIndex;
      }
    };

    const handleClick = (event: MouseEvent) => {
      const clickedItem = event.target as HTMLElement;
      const newIndex = items.indexOf(clickedItem);
      
      if (newIndex !== -1 && newIndex !== currentIndex) {
        // Update tabindex values
        items[currentIndex].setAttribute('tabindex', '-1');
        items[newIndex].setAttribute('tabindex', '0');
        
        currentIndex = newIndex;
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    container.addEventListener('click', handleClick);

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      container.removeEventListener('click', handleClick);
    };
  }, [focusElement]);

  return {
    focusElement,
    focusBySelector,
    focusFirst,
    focusLast,
    saveFocus,
    restoreFocus,
    clearFocusHistory,
    trapFocus,
    releaseFocusTrap,
    setupRovingTabindex,
  };
};

// Helper function to get focusable elements
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ].join(', ');

  const elements = Array.from(
    container.querySelectorAll(focusableSelectors)
  ) as HTMLElement[];

  return elements.filter(element => {
    // Check if element is visible and not hidden
    const style = window.getComputedStyle(element);
    return (
      style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      element.offsetWidth > 0 &&
      element.offsetHeight > 0
    );
  });
}