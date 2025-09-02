import React, { useEffect, useRef } from 'react';
import { useAccessibility } from '../../contexts/AccessibilityContext';

interface ScreenReaderOnlyProps {
  children: React.ReactNode;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
}

/**
 * Component for content that should only be visible to screen readers
 */
export const ScreenReaderOnly: React.FC<ScreenReaderOnlyProps> = ({
  children,
  as: Component = 'span',
  className = '',
}) => {
  return (
    <Component className={`sr-only ${className}`}>
      {children}
    </Component>
  );
};

interface AudioDescriptionProps {
  description: string;
  element?: string; // CSS selector for the element being described
  delay?: number;
}

/**
 * Component for providing audio descriptions of visual elements
 */
export const AudioDescription: React.FC<AudioDescriptionProps> = ({
  description,
  element,
  delay = 500,
}) => {
  const { state } = useAccessibility();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!state.audioDescriptions || !description) return;

    const announceDescription = () => {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only';
      announcement.textContent = `Audio description: ${description}`;
      
      document.body.appendChild(announcement);
      
      setTimeout(() => {
        if (document.body.contains(announcement)) {
          document.body.removeChild(announcement);
        }
      }, 3000);
    };

    if (element) {
      const targetElement = document.querySelector(element);
      if (targetElement) {
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                timeoutRef.current = setTimeout(announceDescription, delay);
              } else if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
              }
            });
          },
          { threshold: 0.5 }
        );
        
        observer.observe(targetElement);
        
        return () => {
          observer.disconnect();
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
          }
        };
      }
    } else {
      // Announce immediately if no element specified
      timeoutRef.current = setTimeout(announceDescription, delay);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [description, element, delay, state.audioDescriptions]);

  return null; // This component doesn't render anything visible
};

interface StructuredContentProps {
  children: React.ReactNode;
  role?: string;
  label?: string;
  description?: string;
  level?: number; // For heading levels
}

/**
 * Component for creating screen reader optimized content structure
 */
export const StructuredContent: React.FC<StructuredContentProps> = ({
  children,
  role,
  label,
  description,
  level,
}) => {
  const { state } = useAccessibility();

  if (!state.screenReaderOptimized) {
    return <>{children}</>;
  }

  const props: Record<string, any> = {};
  
  if (role) props.role = role;
  if (label) props['aria-label'] = label;
  if (description) props['aria-describedby'] = `desc-${Math.random().toString(36).substr(2, 9)}`;

  // Use semantic heading if level is specified
  if (level && level >= 1 && level <= 6) {
    const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements;
    return (
      <div>
        <HeadingTag {...props} className="sr-only">
          {label}
        </HeadingTag>
        {description && (
          <div id={props['aria-describedby']} className="sr-only">
            {description}
          </div>
        )}
        <div role="group" aria-labelledby={props['aria-describedby']}>
          {children}
        </div>
      </div>
    );
  }

  return (
    <div {...props}>
      {description && (
        <div id={props['aria-describedby']} className="sr-only">
          {description}
        </div>
      )}
      {children}
    </div>
  );
};

interface ProgressAnnouncementProps {
  current: number;
  total: number;
  label?: string;
  announceInterval?: number; // Announce every N steps
}

/**
 * Component for announcing progress updates to screen readers
 */
export const ProgressAnnouncement: React.FC<ProgressAnnouncementProps> = ({
  current,
  total,
  label = 'Progress',
  announceInterval = 10,
}) => {
  const { state, announceToScreenReader } = useAccessibility();
  const lastAnnouncedRef = useRef<number>(0);

  useEffect(() => {
    if (!state.announceChanges) return;

    const percentage = Math.round((current / total) * 100);
    const shouldAnnounce = 
      percentage === 0 || 
      percentage === 100 || 
      percentage - lastAnnouncedRef.current >= announceInterval;

    if (shouldAnnounce) {
      const message = `${label}: ${percentage}% complete, ${current} of ${total}`;
      announceToScreenReader(message);
      lastAnnouncedRef.current = percentage;
    }
  }, [current, total, label, announceInterval, state.announceChanges, announceToScreenReader]);

  return (
    <div
      role="progressbar"
      aria-valuenow={current}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-label={`${label}: ${current} of ${total}`}
      className="sr-only"
    >
      {Math.round((current / total) * 100)}% complete
    </div>
  );
};

interface TableDescriptionProps {
  caption: string;
  summary?: string;
  rowCount?: number;
  columnCount?: number;
  children: React.ReactNode;
}

/**
 * Component for creating accessible table descriptions
 */
export const AccessibleTable: React.FC<TableDescriptionProps> = ({
  caption,
  summary,
  rowCount,
  columnCount,
  children,
}) => {
  const { state } = useAccessibility();

  const tableId = `table-${Math.random().toString(36).substr(2, 9)}`;
  const summaryId = `${tableId}-summary`;

  return (
    <div>
      {state.screenReaderOptimized && summary && (
        <div id={summaryId} className="sr-only">
          {summary}
          {rowCount && columnCount && (
            <span> Table has {rowCount} rows and {columnCount} columns.</span>
          )}
        </div>
      )}
      <table
        id={tableId}
        aria-describedby={state.screenReaderOptimized && summary ? summaryId : undefined}
        role="table"
      >
        <caption className={state.screenReaderOptimized ? '' : 'sr-only'}>
          {caption}
        </caption>
        {children}
      </table>
    </div>
  );
};

interface ListDescriptionProps {
  type: 'ordered' | 'unordered' | 'description';
  itemCount?: number;
  label?: string;
  children: React.ReactNode;
}

/**
 * Component for creating accessible list descriptions
 */
export const AccessibleList: React.FC<ListDescriptionProps> = ({
  type,
  itemCount,
  label,
  children,
}) => {
  const { state } = useAccessibility();

  const listProps: Record<string, any> = {
    role: type === 'description' ? 'list' : undefined,
  };

  if (label) {
    listProps['aria-label'] = label;
  }

  if (state.screenReaderOptimized && itemCount) {
    listProps['aria-label'] = `${label || 'List'} with ${itemCount} items`;
  }

  const ListComponent = type === 'ordered' ? 'ol' : type === 'unordered' ? 'ul' : 'dl';

  return (
    <ListComponent {...listProps}>
      {state.screenReaderOptimized && itemCount && (
        <li className="sr-only" aria-hidden="true">
          List contains {itemCount} items
        </li>
      )}
      {children}
    </ListComponent>
  );
};

export default {
  ScreenReaderOnly,
  AudioDescription,
  StructuredContent,
  ProgressAnnouncement,
  AccessibleTable,
  AccessibleList,
};