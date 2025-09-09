/**
 * Accessibility Testing Utilities
 * 
 * This module provides utilities for testing accessibility compliance
 * and identifying potential accessibility issues in the application.
 */

export interface AccessibilityIssue {
  type: 'error' | 'warning' | 'info';
  rule: string;
  message: string;
  element?: HTMLElement;
  selector?: string;
}

export interface AccessibilityReport {
  issues: AccessibilityIssue[];
  score: number; // 0-100
  summary: {
    errors: number;
    warnings: number;
    info: number;
  };
}

/**
 * Checks for missing alt text on images
 */
export function checkImageAltText(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const images = document.querySelectorAll('img');

  images.forEach((img) => {
    if (!img.hasAttribute('alt')) {
      issues.push({
        type: 'error',
        rule: 'img-alt',
        message: 'Image missing alt attribute',
        element: img,
        selector: getElementSelector(img),
      });
    } else if (img.getAttribute('alt')?.trim() === '') {
      // Empty alt is okay for decorative images, but check if it's intentional
      if (!img.hasAttribute('role') || img.getAttribute('role') !== 'presentation') {
        issues.push({
          type: 'warning',
          rule: 'img-alt-empty',
          message: 'Image has empty alt text - ensure this is decorative',
          element: img,
          selector: getElementSelector(img),
        });
      }
    }
  });

  return issues;
}

/**
 * Checks for proper heading hierarchy
 */
export function checkHeadingHierarchy(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
  let previousLevel = 0;

  headings.forEach((heading) => {
    const level = parseInt(heading.tagName.charAt(1));
    
    if (previousLevel === 0 && level !== 1) {
      issues.push({
        type: 'error',
        rule: 'heading-hierarchy',
        message: 'Page should start with h1',
        element: heading as HTMLElement,
        selector: getElementSelector(heading),
      });
    } else if (level > previousLevel + 1) {
      issues.push({
        type: 'error',
        rule: 'heading-hierarchy',
        message: `Heading level skipped from h${previousLevel} to h${level}`,
        element: heading as HTMLElement,
        selector: getElementSelector(heading),
      });
    }

    if (heading.textContent?.trim() === '') {
      issues.push({
        type: 'error',
        rule: 'heading-empty',
        message: 'Heading is empty',
        element: heading as HTMLElement,
        selector: getElementSelector(heading),
      });
    }

    previousLevel = level;
  });

  return issues;
}

/**
 * Checks for proper form labels
 */
export function checkFormLabels(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const formControls = document.querySelectorAll('input, select, textarea');

  formControls.forEach((control) => {
    const element = control as HTMLInputElement;
    
    // Skip hidden inputs and buttons
    if (element.type === 'hidden' || element.type === 'button' || element.type === 'submit') {
      return;
    }

    const hasLabel = element.labels && element.labels.length > 0;
    const hasAriaLabel = element.hasAttribute('aria-label');
    const hasAriaLabelledBy = element.hasAttribute('aria-labelledby');

    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
      issues.push({
        type: 'error',
        rule: 'form-label',
        message: 'Form control missing accessible label',
        element: element,
        selector: getElementSelector(element),
      });
    }
  });

  return issues;
}

/**
 * Checks for proper color contrast (simplified check)
 */
export function checkColorContrast(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const textElements = document.querySelectorAll('p, span, div, a, button, h1, h2, h3, h4, h5, h6');

  textElements.forEach((element) => {
    const styles = window.getComputedStyle(element);
    // const fontSize = parseFloat(styles.fontSize);
    // const fontWeight = styles.fontWeight;
    
    // This is a simplified check - in a real implementation, you'd calculate actual contrast ratios
    const textColor = styles.color;
    const backgroundColor = styles.backgroundColor;
    
    if (textColor === backgroundColor) {
      issues.push({
        type: 'error',
        rule: 'color-contrast',
        message: 'Text and background colors are the same',
        element: element as HTMLElement,
        selector: getElementSelector(element),
      });
    }

    // Check for very light text on light backgrounds (simplified)
    if (textColor.includes('rgb(255') && backgroundColor.includes('rgb(255')) {
      issues.push({
        type: 'warning',
        rule: 'color-contrast',
        message: 'Potential low contrast between text and background',
        element: element as HTMLElement,
        selector: getElementSelector(element),
      });
    }
  });

  return issues;
}

/**
 * Checks for keyboard accessibility
 */
export function checkKeyboardAccessibility(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]');

  interactiveElements.forEach((element) => {
    const htmlElement = element as HTMLElement;
    const tabIndex = htmlElement.tabIndex;
    
    // Check for positive tabindex (anti-pattern)
    if (tabIndex > 0) {
      issues.push({
        type: 'warning',
        rule: 'tabindex-positive',
        message: 'Avoid positive tabindex values',
        element: htmlElement,
        selector: getElementSelector(htmlElement),
      });
    }

    // Check for missing focus indicators
    const styles = window.getComputedStyle(htmlElement, ':focus');
    if (styles.outline === 'none' && !styles.boxShadow && !styles.border) {
      issues.push({
        type: 'warning',
        rule: 'focus-indicator',
        message: 'Interactive element may be missing focus indicator',
        element: htmlElement,
        selector: getElementSelector(htmlElement),
      });
    }
  });

  return issues;
}

/**
 * Checks for ARIA usage
 */
export function checkAriaUsage(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  const elementsWithAria = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby], [role]');

  elementsWithAria.forEach((element) => {
    const htmlElement = element as HTMLElement;
    
    // Check for empty aria-label
    const ariaLabel = htmlElement.getAttribute('aria-label');
    if (ariaLabel !== null && ariaLabel.trim() === '') {
      issues.push({
        type: 'error',
        rule: 'aria-label-empty',
        message: 'aria-label is empty',
        element: htmlElement,
        selector: getElementSelector(htmlElement),
      });
    }

    // Check for invalid aria-labelledby references
    const ariaLabelledBy = htmlElement.getAttribute('aria-labelledby');
    if (ariaLabelledBy) {
      const ids = ariaLabelledBy.split(' ');
      ids.forEach((id) => {
        if (!document.getElementById(id)) {
          issues.push({
            type: 'error',
            rule: 'aria-labelledby-invalid',
            message: `aria-labelledby references non-existent element: ${id}`,
            element: htmlElement,
            selector: getElementSelector(htmlElement),
          });
        }
      });
    }

    // Check for invalid aria-describedby references
    const ariaDescribedBy = htmlElement.getAttribute('aria-describedby');
    if (ariaDescribedBy) {
      const ids = ariaDescribedBy.split(' ');
      ids.forEach((id) => {
        if (!document.getElementById(id)) {
          issues.push({
            type: 'error',
            rule: 'aria-describedby-invalid',
            message: `aria-describedby references non-existent element: ${id}`,
            element: htmlElement,
            selector: getElementSelector(htmlElement),
          });
        }
      });
    }
  });

  return issues;
}

/**
 * Checks for proper landmark usage
 */
export function checkLandmarks(): AccessibilityIssue[] {
  const issues: AccessibilityIssue[] = [];
  
  // Check for main landmark
  const mainElements = document.querySelectorAll('main, [role="main"]');
  if (mainElements.length === 0) {
    issues.push({
      type: 'error',
      rule: 'landmark-main',
      message: 'Page missing main landmark',
    });
  } else if (mainElements.length > 1) {
    issues.push({
      type: 'error',
      rule: 'landmark-main-multiple',
      message: 'Page has multiple main landmarks',
    });
  }

  // Check for navigation landmarks
  const navElements = document.querySelectorAll('nav, [role="navigation"]');
  navElements.forEach((nav) => {
    const hasLabel = nav.hasAttribute('aria-label') || nav.hasAttribute('aria-labelledby');
    if (navElements.length > 1 && !hasLabel) {
      issues.push({
        type: 'warning',
        rule: 'landmark-nav-label',
        message: 'Multiple navigation landmarks should have labels',
        element: nav as HTMLElement,
        selector: getElementSelector(nav),
      });
    }
  });

  return issues;
}

/**
 * Runs all accessibility checks and returns a comprehensive report
 */
export function runAccessibilityAudit(): AccessibilityReport {
  const allIssues: AccessibilityIssue[] = [
    ...checkImageAltText(),
    ...checkHeadingHierarchy(),
    ...checkFormLabels(),
    ...checkColorContrast(),
    ...checkKeyboardAccessibility(),
    ...checkAriaUsage(),
    ...checkLandmarks(),
  ];

  const summary = {
    errors: allIssues.filter(issue => issue.type === 'error').length,
    warnings: allIssues.filter(issue => issue.type === 'warning').length,
    info: allIssues.filter(issue => issue.type === 'info').length,
  };

  // Calculate score (simplified scoring)
  const totalChecks = allIssues.length || 1;
  const errorWeight = 3;
  const warningWeight = 1;
  const totalDeductions = (summary.errors * errorWeight) + (summary.warnings * warningWeight);
  const score = Math.max(0, Math.round(100 - (totalDeductions / totalChecks) * 100));

  return {
    issues: allIssues,
    score,
    summary,
  };
}

/**
 * Helper function to generate a CSS selector for an element
 */
function getElementSelector(element: Element): string {
  if (element.id) {
    return `#${element.id}`;
  }

  if (element.className) {
    const classes = element.className.split(' ').filter(Boolean);
    if (classes.length > 0) {
      return `${element.tagName.toLowerCase()}.${classes.join('.')}`;
    }
  }

  // Generate a more specific selector
  let selector = element.tagName.toLowerCase();
  let parent = element.parentElement;
  
  while (parent && parent !== document.body) {
    const siblings = Array.from(parent.children);
    const index = siblings.indexOf(element);
    selector = `${parent.tagName.toLowerCase()} > ${selector}:nth-child(${index + 1})`;
    parent = parent.parentElement;
  }

  return selector;
}

/**
 * Highlights accessibility issues on the page (for development)
 */
export function highlightAccessibilityIssues(report: AccessibilityReport): void {
  // Remove existing highlights
  document.querySelectorAll('.accessibility-highlight').forEach(el => el.remove());

  report.issues.forEach((issue) => {
    if (!issue.element) return;

    const highlight = document.createElement('div');
    highlight.className = 'accessibility-highlight';
    highlight.style.cssText = `
      position: absolute;
      border: 2px solid ${issue.type === 'error' ? 'red' : issue.type === 'warning' ? 'orange' : 'blue'};
      background: ${issue.type === 'error' ? 'rgba(255,0,0,0.1)' : issue.type === 'warning' ? 'rgba(255,165,0,0.1)' : 'rgba(0,0,255,0.1)'};
      pointer-events: none;
      z-index: 10000;
      font-size: 12px;
      color: white;
      padding: 2px 4px;
    `;

    const rect = issue.element.getBoundingClientRect();
    highlight.style.top = `${rect.top + window.scrollY}px`;
    highlight.style.left = `${rect.left + window.scrollX}px`;
    highlight.style.width = `${rect.width}px`;
    highlight.style.height = `${rect.height}px`;

    const label = document.createElement('div');
    label.textContent = `${issue.type.toUpperCase()}: ${issue.message}`;
    label.style.cssText = `
      background: ${issue.type === 'error' ? 'red' : issue.type === 'warning' ? 'orange' : 'blue'};
      color: white;
      padding: 2px 4px;
      font-size: 10px;
      position: absolute;
      top: -20px;
      left: 0;
      white-space: nowrap;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
    `;

    highlight.appendChild(label);
    document.body.appendChild(highlight);
  });
}

/**
 * Removes accessibility issue highlights
 */
export function clearAccessibilityHighlights(): void {
  document.querySelectorAll('.accessibility-highlight').forEach(el => el.remove());
}