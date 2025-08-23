import React, { useEffect, useRef } from 'react';

export type LiveRegionPoliteness = 'off' | 'polite' | 'assertive';

interface AriaLiveRegionProps {
  message: string;
  politeness?: LiveRegionPoliteness;
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all';
  clearOnUnmount?: boolean;
  delay?: number;
  className?: string;
}

/**
 * Component for announcing messages to screen readers
 */
export const AriaLiveRegion: React.FC<AriaLiveRegionProps> = ({
  message,
  politeness = 'polite',
  atomic = true,
  relevant = 'all',
  clearOnUnmount = true,
  delay = 100,
  className = 'sr-only',
}) => {
  const regionRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!message.trim()) return;

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Clear the region first to ensure the message is announced
    if (regionRef.current) {
      regionRef.current.textContent = '';
    }

    // Set the message after a small delay
    timeoutRef.current = setTimeout(() => {
      if (regionRef.current) {
        regionRef.current.textContent = message;
      }
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [message, delay]);

  useEffect(() => {
    return () => {
      if (clearOnUnmount && regionRef.current) {
        regionRef.current.textContent = '';
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [clearOnUnmount]);

  return (
    <div
      ref={regionRef}
      aria-live={politeness}
      aria-atomic={atomic}
      aria-relevant={relevant}
      className={className}
      role="status"
    />
  );
};

export default AriaLiveRegion;