import React, { useEffect, useRef, useCallback } from 'react';
import { X } from 'lucide-react';
import { useFocusManagement } from '../../hooks/useFocusManagement';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { cn } from '../../utils';

interface AccessibleModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  className?: string;
  overlayClassName?: string;
  contentClassName?: string;
  initialFocus?: string; // CSS selector for initial focus
  returnFocus?: boolean;
  role?: 'dialog' | 'alertdialog';
}

/**
 * Accessible modal component with proper ARIA support and focus management
 */
export const AccessibleModal: React.FC<AccessibleModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
  overlayClassName,
  contentClassName,
  initialFocus,
  returnFocus = true,
  role = 'dialog',
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);
  
  const { 
    focusElement, 
    focusBySelector, 
    trapFocus, 
    saveFocus, 
    restoreFocus 
  } = useFocusManagement();
  
  const { announce } = useAriaAnnouncements();

  // Handle escape key
  const handleEscape = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape' && closeOnEscape) {
      event.preventDefault();
      onClose();
    }
  }, [closeOnEscape, onClose]);

  // Handle overlay click
  const handleOverlayClick = useCallback((event: React.MouseEvent) => {
    if (closeOnOverlayClick && event.target === overlayRef.current) {
      onClose();
    }
  }, [closeOnOverlayClick, onClose]);

  // Set up modal when opened
  useEffect(() => {
    if (isOpen) {
      // Save current focus
      if (returnFocus) {
        saveFocus();
      }

      // Prevent body scroll
      document.body.style.overflow = 'hidden';
      
      // Add escape key listener
      document.addEventListener('keydown', handleEscape);
      
      // Announce modal opening
      announce(`${title} dialog opened`, { priority: 'polite' });
      
      // Set up focus trap and initial focus
      const cleanup = trapFocus(modalRef.current);
      
      // Focus initial element
      setTimeout(() => {
        if (initialFocus) {
          focusBySelector(initialFocus);
        } else if (titleRef.current) {
          focusElement(titleRef.current);
        }
      }, 100);

      return () => {
        document.removeEventListener('keydown', handleEscape);
        if (cleanup) cleanup();
      };
    } else {
      // Restore body scroll
      document.body.style.overflow = '';
      
      // Restore focus
      if (returnFocus) {
        setTimeout(() => {
          restoreFocus();
        }, 100);
      }
      
      // Announce modal closing
      if (previousActiveElementRef.current) {
        announce(`${title} dialog closed`, { priority: 'polite' });
      }
    }
  }, [
    isOpen,
    title,
    initialFocus,
    returnFocus,
    handleEscape,
    trapFocus,
    focusBySelector,
    focusElement,
    saveFocus,
    restoreFocus,
    announce,
  ]);

  // Don't render if not open
  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-full mx-4',
  };

  return (
    <div
      className={cn('fixed inset-0 z-50 flex items-center justify-center', className)}
      role="presentation"
    >
      {/* Overlay */}
      <div
        ref={overlayRef}
        className={cn(
          'fixed inset-0 bg-black bg-opacity-50 transition-opacity',
          overlayClassName
        )}
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* Modal Content */}
      <div
        ref={modalRef}
        className={cn(
          'relative bg-white rounded-lg shadow-xl max-h-[90vh] overflow-hidden',
          'flex flex-col w-full',
          sizeClasses[size],
          contentClassName
        )}
        role={role}
        aria-modal="true"
        aria-labelledby="modal-title"
        aria-describedby={description ? "modal-description" : undefined}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2
            ref={titleRef}
            id="modal-title"
            className="text-xl font-semibold text-gray-900"
            tabIndex={-1}
          >
            {title}
          </h2>
          
          {showCloseButton && (
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
              aria-label="Close dialog"
              type="button"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Description */}
        {description && (
          <div className="px-6 py-2 border-b border-gray-200">
            <p id="modal-description" className="text-sm text-gray-600">
              {description}
            </p>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default AccessibleModal;