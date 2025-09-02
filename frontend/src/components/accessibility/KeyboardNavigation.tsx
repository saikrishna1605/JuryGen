import React, { useEffect, useRef, useCallback } from 'react';
import { useFocusManagement } from '../../hooks/useFocusManagement';
import { useAccessibility } from '../../contexts/AccessibilityContext';

interface KeyboardShortcutProps {
  keys: string[]; // e.g., ['ctrl', 'k'] or ['alt', 'n']
  onActivate: () => void;
  description: string;
  global?: boolean; // Whether the shortcut works globally or only when component is focused
  disabled?: boolean;
}

/**
 * Component for managing keyboard shortcuts with accessibility announcements
 */
export const KeyboardShortcut: React.FC<KeyboardShortcutProps> = ({
  keys,
  onActivate,
  description,
  global = false,
  disabled = false,
}) => {
  const { announceToScreenReader } = useAccessibility();

  useEffect(() => {
    if (disabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const pressedKeys = [];
      
      if (event.ctrlKey) pressedKeys.push('ctrl');
      if (event.altKey) pressedKeys.push('alt');
      if (event.shiftKey) pressedKeys.push('shift');
      if (event.metaKey) pressedKeys.push('meta');
      
      // Add the main key
      if (!['Control', 'Alt', 'Shift', 'Meta'].includes(event.key)) {
        pressedKeys.push(event.key.toLowerCase());
      }

      // Check if pressed keys match the shortcut
      if (keys.length === pressedKeys.length && 
          keys.every(key => pressedKeys.includes(key.toLowerCase()))) {
        event.preventDefault();
        onActivate();
        announceToScreenReader(`Keyboard shortcut activated: ${description}`);
      }
    };

    const target = global ? document : document.activeElement;
    target?.addEventListener('keydown', handleKeyDown as EventListener);

    return () => {
      target?.removeEventListener('keydown', handleKeyDown as EventListener);
    };
  }, [keys, onActivate, description, global, disabled, announceToScreenReader]);

  return null; // This component doesn't render anything
};

interface FocusTrapProps {
  active: boolean;
  children: React.ReactNode;
  initialFocus?: string; // CSS selector
  returnFocus?: boolean;
  className?: string;
}

/**
 * Component for trapping focus within a container
 */
export const FocusTrap: React.FC<FocusTrapProps> = ({
  active,
  children,
  initialFocus,
  returnFocus = true,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { trapFocus, focusBySelector, saveFocus, restoreFocus } = useFocusManagement();

  useEffect(() => {
    if (!active || !containerRef.current) return;

    if (returnFocus) {
      saveFocus();
    }

    const cleanup = trapFocus(containerRef.current);

    if (initialFocus) {
      setTimeout(() => focusBySelector(initialFocus), 100);
    }

    return () => {
      if (cleanup) cleanup();
      if (returnFocus) {
        setTimeout(() => restoreFocus(), 100);
      }
    };
  }, [active, initialFocus, returnFocus, trapFocus, focusBySelector, saveFocus, restoreFocus]);

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  );
};

interface RovingTabIndexProps {
  orientation?: 'horizontal' | 'vertical';
  wrap?: boolean;
  children: React.ReactNode;
  className?: string;
  onSelectionChange?: (index: number) => void;
}

/**
 * Component for implementing roving tabindex pattern
 */
export const RovingTabIndex: React.FC<RovingTabIndexProps> = ({
  orientation = 'horizontal',
  wrap = true,
  children,
  className = '',
  onSelectionChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { setupRovingTabindex } = useFocusManagement();
  const currentIndexRef = useRef(0);

  useEffect(() => {
    if (!containerRef.current) return;

    const items = Array.from(
      containerRef.current.querySelectorAll('[role="option"], [role="tab"], [role="menuitem"], button, a')
    ) as HTMLElement[];

    if (items.length === 0) return;

    const cleanup = setupRovingTabindex(containerRef.current, items, orientation);

    // Enhanced keyboard handling
    const handleKeyDown = (event: KeyboardEvent) => {
      const { key } = event;
      let newIndex = currentIndexRef.current;

      if (orientation === 'horizontal') {
        if (key === 'ArrowLeft') {
          newIndex = wrap 
            ? (currentIndexRef.current > 0 ? currentIndexRef.current - 1 : items.length - 1)
            : Math.max(0, currentIndexRef.current - 1);
        } else if (key === 'ArrowRight') {
          newIndex = wrap
            ? (currentIndexRef.current < items.length - 1 ? currentIndexRef.current + 1 : 0)
            : Math.min(items.length - 1, currentIndexRef.current + 1);
        }
      } else {
        if (key === 'ArrowUp') {
          newIndex = wrap
            ? (currentIndexRef.current > 0 ? currentIndexRef.current - 1 : items.length - 1)
            : Math.max(0, currentIndexRef.current - 1);
        } else if (key === 'ArrowDown') {
          newIndex = wrap
            ? (currentIndexRef.current < items.length - 1 ? currentIndexRef.current + 1 : 0)
            : Math.min(items.length - 1, currentIndexRef.current + 1);
        }
      }

      if (key === 'Home') {
        newIndex = 0;
      } else if (key === 'End') {
        newIndex = items.length - 1;
      }

      if (newIndex !== currentIndexRef.current) {
        event.preventDefault();
        currentIndexRef.current = newIndex;
        items[newIndex].focus();
        onSelectionChange?.(newIndex);
      }
    };

    containerRef.current.addEventListener('keydown', handleKeyDown);

    return () => {
      cleanup?.();
      containerRef.current?.removeEventListener('keydown', handleKeyDown);
    };
  }, [orientation, wrap, setupRovingTabindex, onSelectionChange]);

  return (
    <div
      ref={containerRef}
      className={className}
      role="group"
    >
      {children}
    </div>
  );
};

interface AccessibleMenuProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end';
  className?: string;
}

/**
 * Accessible dropdown menu with keyboard navigation
 */
export const AccessibleMenu: React.FC<AccessibleMenuProps> = ({
  trigger,
  children,
  placement = 'bottom-start',
  className = '',
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const { focusFirst, focusLast } = useFocusManagement();

  const handleTriggerKeyDown = useCallback((event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
      case 'Enter':
      case ' ':
        event.preventDefault();
        setIsOpen(true);
        setTimeout(() => {
          if (menuRef.current) {
            focusFirst(menuRef.current);
          }
        }, 100);
        break;
      case 'ArrowUp':
        event.preventDefault();
        setIsOpen(true);
        setTimeout(() => {
          if (menuRef.current) {
            focusLast(menuRef.current);
          }
        }, 100);
        break;
      case 'Escape':
        setIsOpen(false);
        triggerRef.current?.focus();
        break;
    }
  }, [focusFirst, focusLast]);

  const handleMenuKeyDown = useCallback((event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'Escape':
        event.preventDefault();
        setIsOpen(false);
        triggerRef.current?.focus();
        break;
      case 'Tab':
        // Allow tab to close menu and move to next element
        setIsOpen(false);
        break;
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        triggerRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const menuId = `menu-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`relative ${className}`}>
      <button
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleTriggerKeyDown}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-controls={isOpen ? menuId : undefined}
        className="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        {trigger}
      </button>

      {isOpen && (
        <div
          ref={menuRef}
          id={menuId}
          role="menu"
          onKeyDown={handleMenuKeyDown}
          className={`absolute z-50 bg-white border border-gray-200 rounded-md shadow-lg ${
            placement.includes('bottom') ? 'top-full mt-1' : 'bottom-full mb-1'
          } ${
            placement.includes('end') ? 'right-0' : 'left-0'
          }`}
        >
          <RovingTabIndex orientation="vertical">
            {children}
          </RovingTabIndex>
        </div>
      )}
    </div>
  );
};

interface AccessibleMenuItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Accessible menu item component
 */
export const AccessibleMenuItem: React.FC<AccessibleMenuItemProps> = ({
  children,
  onClick,
  disabled = false,
  className = '',
}) => {
  const handleClick = useCallback(() => {
    if (!disabled && onClick) {
      onClick();
    }
  }, [disabled, onClick]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  }, [handleClick]);

  return (
    <div
      role="menuitem"
      tabIndex={disabled ? -1 : 0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-disabled={disabled}
      className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 focus:bg-gray-100 focus:outline-none ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

export default {
  KeyboardShortcut,
  FocusTrap,
  RovingTabIndex,
  AccessibleMenu,
  AccessibleMenuItem,
};