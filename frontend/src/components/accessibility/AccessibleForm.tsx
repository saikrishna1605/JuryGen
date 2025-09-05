import React, { useRef, useCallback } from 'react';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { cn } from '../../utils';

interface FormFieldProps {
  id: string;
  label: string;
  type?: 'text' | 'email' | 'password' | 'tel' | 'url' | 'search' | 'textarea' | 'select' | 'date';
  value: string;
  onChange: (value: string) => void;
  error?: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>; // For select fields
  rows?: number; // For textarea
  autoComplete?: string;
  className?: string;
  inputClassName?: string;
}

interface AccessibleFormProps {
  onSubmit: (event: React.FormEvent) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  noValidate?: boolean;
}

/**
 * Accessible form field component with proper ARIA support
 */
export const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  type = 'text',
  value,
  onChange,
  error,
  helperText,
  required = false,
  disabled = false,
  placeholder,
  options = [],
  rows = 4,
  autoComplete,
  className,
  inputClassName,
}) => {
  const { announceValidation } = useAriaAnnouncements();
  
  const handleChange = useCallback((newValue: string) => {
    onChange(newValue);
    
    // Announce validation state changes
    if (error) {
      announceValidation(label, false, error);
    } else if (required && newValue.trim()) {
      announceValidation(label, true);
    }
  }, [onChange, error, required, label, announceValidation]);

  const inputProps = {
    id,
    value,
    disabled,
    placeholder,
    autoComplete,
    required,
    'aria-invalid': !!error,
    'aria-describedby': [
      helperText ? `${id}-helper` : '',
      error ? `${id}-error` : '',
    ].filter(Boolean).join(' ') || undefined,
    className: cn(
      'w-full px-3 py-2 border rounded-md shadow-sm transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
      error 
        ? 'border-red-500 bg-red-50' 
        : 'border-gray-300 focus:border-blue-500',
      disabled && 'bg-gray-100 cursor-not-allowed opacity-60',
      inputClassName
    ),
  };

  const renderInput = () => {
    switch (type) {
      case 'textarea':
        return (
          <textarea
            {...inputProps}
            rows={rows}
            onChange={(e) => handleChange(e.target.value)}
          />
        );
      
      case 'select':
        return (
          <select
            {...inputProps}
            onChange={(e) => handleChange(e.target.value)}
          >
            <option value="">Select an option</option>
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      default:
        return (
          <input
            {...inputProps}
            type={type}
            onChange={(e) => handleChange(e.target.value)}
          />
        );
    }
  };

  return (
    <div className={cn('space-y-2', className)}>
      {/* Label */}
      <label
        htmlFor={id}
        className={cn(
          'block text-sm font-medium',
          error ? 'text-red-700' : 'text-gray-700',
          disabled && 'opacity-60'
        )}
      >
        {label}
        {required && (
          <span className="text-red-500 ml-1" aria-label="required">
            *
          </span>
        )}
      </label>

      {/* Input */}
      {renderInput()}

      {/* Helper Text */}
      {helperText && !error && (
        <div
          id={`${id}-helper`}
          className="flex items-start space-x-2 text-sm text-gray-600"
        >
          <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{helperText}</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div
          id={`${id}-error`}
          className="flex items-start space-x-2 text-sm text-red-600"
          role="alert"
          aria-live="polite"
        >
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Success Indicator */}
      {!error && required && value.trim() && (
        <div className="flex items-center space-x-2 text-sm text-green-600">
          <CheckCircle className="w-4 h-4" />
          <span className="sr-only">{label} is valid</span>
        </div>
      )}
    </div>
  );
};

/**
 * Accessible form component with proper structure and ARIA support
 */
export const AccessibleForm: React.FC<AccessibleFormProps> = ({
  onSubmit,
  title,
  description,
  children,
  className,
  noValidate = true,
}) => {
  const formRef = useRef<HTMLFormElement>(null);
  const { announceError } = useAriaAnnouncements();

  const handleSubmit = useCallback((event: React.FormEvent) => {
    event.preventDefault();
    
    try {
      onSubmit(event);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Form submission failed';
      announceError(errorMessage, 'Form submission');
    }
  }, [onSubmit, announceError]);

  // Focus first invalid field
  const focusFirstInvalidField = useCallback(() => {
    if (!formRef.current) return;
    
    const invalidField = formRef.current.querySelector('[aria-invalid="true"]') as HTMLElement;
    if (invalidField) {
      invalidField.focus();
      invalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit}
      noValidate={noValidate}
      className={cn('space-y-6', className)}
      role="form"
      aria-labelledby={title ? 'form-title' : undefined}
      aria-describedby={description ? 'form-description' : undefined}
    >
      {/* Form Title */}
      {title && (
        <div className="space-y-2">
          <h2 id="form-title" className="text-xl font-semibold text-gray-900">
            {title}
          </h2>
          {description && (
            <p id="form-description" className="text-sm text-gray-600">
              {description}
            </p>
          )}
        </div>
      )}

      {/* Form Content */}
      {children}

      {/* Form Actions */}
      <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={focusFirstInvalidField}
          className="sr-only focus:not-sr-only px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
        >
          Go to first error
        </button>
      </div>
    </form>
  );
};

export default AccessibleForm;