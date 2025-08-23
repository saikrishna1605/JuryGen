import React from 'react';
import { cn } from '../../lib/utils';

interface SkipLink {
  href: string;
  label: string;
}

interface SkipNavigationProps {
  links?: SkipLink[];
  className?: string;
}

const defaultLinks: SkipLink[] = [
  { href: '#main-content', label: 'Skip to main content' },
  { href: '#navigation', label: 'Skip to navigation' },
  { href: '#footer', label: 'Skip to footer' },
];

/**
 * Skip navigation component for keyboard users
 */
export const SkipNavigation: React.FC<SkipNavigationProps> = ({
  links = defaultLinks,
  className,
}) => {
  const handleSkipClick = (href: string) => {
    const target = document.querySelector(href);
    if (target) {
      // Focus the target element
      const focusableTarget = target as HTMLElement;
      
      // Make sure the target is focusable
      if (!focusableTarget.hasAttribute('tabindex')) {
        focusableTarget.setAttribute('tabindex', '-1');
      }
      
      focusableTarget.focus();
      
      // Scroll to the target
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <nav
      className={cn('skip-navigation', className)}
      aria-label="Skip navigation"
    >
      <ul className="skip-links">
        {links.map((link, index) => (
          <li key={index}>
            <a
              href={link.href}
              className="skip-link"
              onClick={(e) => {
                e.preventDefault();
                handleSkipClick(link.href);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleSkipClick(link.href);
                }
              }}
            >
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default SkipNavigation;