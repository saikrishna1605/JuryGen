import React, { useEffect, useRef } from 'react';
import { useAccessibility } from '../../contexts/AccessibilityContext';

interface LandmarkProps {
  role: 'banner' | 'navigation' | 'main' | 'complementary' | 'contentinfo' | 'search' | 'form' | 'region';
  label?: string;
  level?: number;
  children: React.ReactNode;
  className?: string;
}

/**
 * Component for creating ARIA landmarks with proper labeling
 */
export const Landmark: React.FC<LandmarkProps> = ({
  role,
  label,
  level,
  children,
  className = '',
}) => {
  const { state, announceToScreenReader } = useAccessibility();
  const landmarkRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (state.announceChanges && label && landmarkRef.current) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              announceToScreenReader(`Entered ${label} ${role}`);
            }
          });
        },
        { threshold: 0.1 }
      );

      observer.observe(landmarkRef.current);

      return () => observer.disconnect();
    }
  }, [role, label, state.announceChanges, announceToScreenReader]);

  const props: Record<string, any> = {
    ref: landmarkRef,
    role,
    className,
  };

  if (label) {
    props['aria-label'] = label;
  }

  if (level && (role === 'region' || role === 'complementary')) {
    props['aria-level'] = level;
  }

  // Use semantic HTML elements when appropriate
  const getSemanticElement = () => {
    switch (role) {
      case 'banner':
        return 'header';
      case 'navigation':
        return 'nav';
      case 'main':
        return 'main';
      case 'complementary':
        return 'aside';
      case 'contentinfo':
        return 'footer';
      case 'search':
        return 'search';
      case 'form':
        return 'form';
      default:
        return 'section';
    }
  };

  const Element = getSemanticElement() as keyof JSX.IntrinsicElements;

  return <Element {...props}>{children}</Element>;
};

interface BreadcrumbProps {
  items: Array<{
    label: string;
    href?: string;
    current?: boolean;
  }>;
  className?: string;
}

/**
 * Accessible breadcrumb navigation component
 */
export const AccessibleBreadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  className = '',
}) => {
  return (
    <nav aria-label="Breadcrumb" className={className}>
      <ol role="list" className="flex items-center space-x-2">
        {items.map((item, index) => (
          <li key={index} role="listitem">
            {index > 0 && (
              <span aria-hidden="true" className="text-gray-400 mx-2">
                /
              </span>
            )}
            {item.current ? (
              <span
                aria-current="page"
                className="text-gray-900 font-medium"
              >
                {item.label}
              </span>
            ) : item.href ? (
              <a
                href={item.href}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                {item.label}
              </a>
            ) : (
              <span className="text-gray-600">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

interface PageStructureProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

/**
 * Component for creating proper page structure with landmarks
 */
export const PageStructure: React.FC<PageStructureProps> = ({
  title,
  description,
  children,
}) => {
  const { state } = useAccessibility();

  useEffect(() => {
    // Set page title
    document.title = title;

    // Announce page change to screen readers
    if (state.announceChanges) {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'assertive');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only';
      announcement.textContent = `Page loaded: ${title}`;
      
      document.body.appendChild(announcement);
      
      setTimeout(() => {
        if (document.body.contains(announcement)) {
          document.body.removeChild(announcement);
        }
      }, 1000);
    }
  }, [title, state.announceChanges]);

  return (
    <>
      {state.screenReaderOptimized && (
        <div className="sr-only">
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
      )}
      {children}
    </>
  );
};

interface TabPanelProps {
  id: string;
  tabId: string;
  label: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Accessible tab panel component
 */
export const AccessibleTabPanel: React.FC<TabPanelProps> = ({
  id,
  tabId,
  label,
  children,
  className = '',
}) => {
  return (
    <div
      id={id}
      role="tabpanel"
      aria-labelledby={tabId}
      aria-label={label}
      tabIndex={0}
      className={className}
    >
      {children}
    </div>
  );
};

interface StatusRegionProps {
  status: 'success' | 'error' | 'warning' | 'info' | 'loading';
  message: string;
  details?: string;
  className?: string;
}

/**
 * Component for announcing status changes with appropriate urgency
 */
export const StatusRegion: React.FC<StatusRegionProps> = ({
  status,
  message,
  details,
  className = '',
}) => {
  const politeness = status === 'error' ? 'assertive' : 'polite';
  const role = status === 'error' ? 'alert' : 'status';

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      case 'loading':
        return '⟳';
      default:
        return '';
    }
  };

  return (
    <div
      role={role}
      aria-live={politeness}
      aria-atomic="true"
      className={`status-region ${className}`}
    >
      <span aria-hidden="true">{getStatusIcon()}</span>
      <span className="sr-only">{status}:</span>
      <span>{message}</span>
      {details && (
        <div className="mt-1 text-sm">
          {details}
        </div>
      )}
    </div>
  );
};

export default {
  Landmark,
  AccessibleBreadcrumb,
  PageStructure,
  AccessibleTabPanel,
  StatusRegion,
};