/**
 * Accessibility testing for AI Legal Companion.
 * 
 * Tests WCAG compliance, keyboard navigation, screen reader support,
 * and inclusive design features.
 */

import { test, expect, Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const TEST_USER_EMAIL = 'accessibility@example.com';
const TEST_USER_PASSWORD = 'accessibilitytest123';

class AccessibilityTester {
  constructor(private page: Page) {}

  async runAxeAnalysis(options?: any) {
    const accessibilityScanResults = await new AxeBuilder({ page: this.page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    return accessibilityScanResults;
  }

  async testKeyboardNavigation() {
    // Test tab navigation
    const focusableElements = await this.page.locator(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ).all();

    let currentIndex = 0;
    
    for (const element of focusableElements) {
      await this.page.keyboard.press('Tab');
      
      const focusedElement = await this.page.locator(':focus').first();
      const isSameElement = await element.evaluate((el, focused) => {
        return el === focused;
      }, await focusedElement.elementHandle());

      if (isSameElement) {
        currentIndex++;
      }
    }

    return currentIndex >= focusableElements.length * 0.8; // 80% success rate
  }

  async testScreenReaderSupport() {
    const ariaLabels = await this.page.locator('[aria-label]').count();
    const ariaDescriptions = await this.page.locator('[aria-describedby]').count();
    const headings = await this.page.locator('h1, h2, h3, h4, h5, h6').count();
    const landmarks = await this.page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"]').count();

    return {
      ariaLabels,
      ariaDescriptions,
      headings,
      landmarks,
      hasProperStructure: headings > 0 && landmarks > 0,
    };
  }

  async testColorContrast() {
    // This would typically use axe-core for automated testing
    // Manual verification points for high contrast mode
    await this.page.click('[data-testid="accessibility-menu"]');
    await this.page.click('[data-testid="high-contrast-toggle"]');

    // Verify high contrast styles are applied
    const bodyClass = await this.page.locator('body').getAttribute('class');
    return bodyClass?.includes('high-contrast') || false;
  }

  async testFontScaling() {
    // Test font scaling functionality
    await this.page.click('[data-testid="accessibility-menu"]');
    
    // Get initial font size
    const initialFontSize = await this.page.locator('body').evaluate(
      el => window.getComputedStyle(el).fontSize
    );

    // Increase font size
    await this.page.click('[data-testid="font-size-increase"]');
    
    const increasedFontSize = await this.page.locator('body').evaluate(
      el => window.getComputedStyle(el).fontSize
    );

    return parseFloat(increasedFontSize) > parseFloat(initialFontSize);
  }
}

test.describe('Accessibility Testing', () => {
  let accessibilityTester: AccessibilityTester;

  test.beforeEach(async ({ page }) => {
    accessibilityTester = new AccessibilityTester(page);
    
    // Sign in for authenticated pages
    await page.goto('/signin');
    await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
    await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
    await page.click('[data-testid="signin-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('homepage accessibility compliance', async ({ page }) => {
    await page.goto('/');
    
    const results = await accessibilityTester.runAxeAnalysis();
    
    expect(results.violations).toHaveLength(0);
    
    // Log any violations for debugging
    if (results.violations.length > 0) {
      console.log('Accessibility violations:', results.violations);
    }
  });

  test('dashboard accessibility compliance', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    const results = await accessibilityTester.runAxeAnalysis();
    
    // Allow minor violations but no critical ones
    const criticalViolations = results.violations.filter(
      violation => violation.impact === 'critical' || violation.impact === 'serious'
    );
    
    expect(criticalViolations).toHaveLength(0);
    
    if (criticalViolations.length > 0) {
      console.log('Critical accessibility violations:', criticalViolations);
    }
  });

  test('document upload accessibility', async ({ page }) => {
    await page.goto('/upload');
    
    const results = await accessibilityTester.runAxeAnalysis();
    expect(results.violations).toHaveLength(0);
    
    // Test drag and drop accessibility
    const dropZone = page.locator('[data-testid="drop-zone"]');
    await expect(dropZone).toHaveAttribute('role', 'button');
    await expect(dropZone).toHaveAttribute('aria-label');
    await expect(dropZone).toHaveAttribute('tabindex', '0');
    
    // Test keyboard interaction with drop zone
    await dropZone.focus();
    await page.keyboard.press('Enter');
    
    // Should open file dialog or show alternative upload method
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
  });

  test('keyboard navigation throughout app', async ({ page }) => {
    // Test navigation on dashboard
    await page.goto('/dashboard');
    
    const navigationSuccess = await accessibilityTester.testKeyboardNavigation();
    expect(navigationSuccess).toBe(true);
    
    // Test specific keyboard shortcuts
    await page.keyboard.press('Alt+u'); // Upload shortcut
    await expect(page).toHaveURL(/.*upload.*/);
    
    await page.keyboard.press('Alt+d'); // Dashboard shortcut
    await expect(page).toHaveURL(/.*dashboard.*/);
  });

  test('screen reader support', async ({ page }) => {
    await page.goto('/dashboard');
    
    const screenReaderSupport = await accessibilityTester.testScreenReaderSupport();
    
    expect(screenReaderSupport.hasProperStructure).toBe(true);
    expect(screenReaderSupport.headings).toBeGreaterThan(0);
    expect(screenReaderSupport.landmarks).toBeGreaterThan(0);
    expect(screenReaderSupport.ariaLabels).toBeGreaterThan(5);
    
    // Test specific ARIA attributes
    const mainContent = page.locator('[role="main"]');
    await expect(mainContent).toBeVisible();
    
    const navigation = page.locator('[role="navigation"]');
    await expect(navigation).toBeVisible();
  });

  test('high contrast mode', async ({ page }) => {
    await page.goto('/dashboard');
    
    const contrastSuccess = await accessibilityTester.testColorContrast();
    expect(contrastSuccess).toBe(true);
    
    // Verify specific elements have proper contrast
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const button = buttons.nth(i);
      const styles = await button.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          backgroundColor: computed.backgroundColor,
          color: computed.color,
          border: computed.border,
        };
      });
      
      // In high contrast mode, elements should have distinct colors
      expect(styles.backgroundColor).not.toBe(styles.color);
    }
  });

  test('font scaling functionality', async ({ page }) => {
    await page.goto('/dashboard');
    
    const fontScalingWorks = await accessibilityTester.testFontScaling();
    expect(fontScalingWorks).toBe(true);
    
    // Test multiple scaling levels
    const scalingLevels = ['small', 'medium', 'large', 'extra-large'];
    
    for (const level of scalingLevels) {
      await page.click(`[data-testid="font-size-${level}"]`);
      
      const bodyClass = await page.locator('body').getAttribute('class');
      expect(bodyClass).toContain(`font-${level}`);
    }
  });

  test('dyslexia-friendly features', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Enable dyslexia-friendly mode
    await page.click('[data-testid="accessibility-menu"]');
    await page.click('[data-testid="dyslexia-friendly-toggle"]');
    
    // Verify dyslexia-friendly styles are applied
    const bodyClass = await page.locator('body').getAttribute('class');
    expect(bodyClass).toContain('dyslexia-friendly');
    
    // Check font family change
    const fontFamily = await page.locator('body').evaluate(
      el => window.getComputedStyle(el).fontFamily
    );
    
    // Should use dyslexia-friendly font
    expect(fontFamily.toLowerCase()).toMatch(/(opendyslexic|arial|verdana)/);
  });

  test('focus management and skip links', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test skip to main content link
    await page.keyboard.press('Tab');
    
    const skipLink = page.locator('[data-testid="skip-to-main"]');
    await expect(skipLink).toBeFocused();
    
    await page.keyboard.press('Enter');
    
    // Should focus main content
    const mainContent = page.locator('[role="main"]');
    await expect(mainContent).toBeFocused();
  });

  test('form accessibility', async ({ page }) => {
    await page.goto('/upload');
    
    // Test form labels and descriptions
    const fileInput = page.locator('input[type="file"]');
    
    // Should have proper labeling
    const labelId = await fileInput.getAttribute('aria-labelledby');
    if (labelId) {
      const label = page.locator(`#${labelId}`);
      await expect(label).toBeVisible();
    }
    
    // Should have description
    const descriptionId = await fileInput.getAttribute('aria-describedby');
    if (descriptionId) {
      const description = page.locator(`#${descriptionId}`);
      await expect(description).toBeVisible();
    }
    
    // Test error handling accessibility
    // This would require triggering a validation error
    await page.setInputFiles('input[type="file"]', {
      name: 'invalid.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('invalid content'),
    });
    
    // Error should be announced to screen readers
    const errorMessage = page.locator('[role="alert"]');
    await expect(errorMessage).toBeVisible();
    
    // Error should be associated with the input
    const errorId = await errorMessage.getAttribute('id');
    const inputAriaDescribedBy = await fileInput.getAttribute('aria-describedby');
    expect(inputAriaDescribedBy).toContain(errorId);
  });

  test('modal and dialog accessibility', async ({ page }) => {
    await page.goto('/documents');
    
    // Open a modal (e.g., delete confirmation)
    const firstDocument = page.locator('[data-testid="document-item"]').first();
    await firstDocument.hover();
    await page.click('[data-testid="delete-document-btn"]');
    
    // Modal should be properly announced
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    
    // Should have proper ARIA attributes
    await expect(modal).toHaveAttribute('aria-labelledby');
    await expect(modal).toHaveAttribute('aria-describedby');
    
    // Focus should be trapped in modal
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    
    // Focused element should be within modal
    const isWithinModal = await focusedElement.evaluate((el, modalEl) => {
      return modalEl.contains(el);
    }, await modal.elementHandle());
    
    expect(isWithinModal).toBe(true);
    
    // Escape should close modal
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });

  test('data table accessibility', async ({ page }) => {
    await page.goto('/documents');
    
    // Test document list table
    const table = page.locator('[role="table"]');
    await expect(table).toBeVisible();
    
    // Should have proper table structure
    const headers = page.locator('[role="columnheader"]');
    const headerCount = await headers.count();
    expect(headerCount).toBeGreaterThan(0);
    
    // Headers should have proper labels
    for (let i = 0; i < headerCount; i++) {
      const header = headers.nth(i);
      const text = await header.textContent();
      expect(text?.trim()).toBeTruthy();
    }
    
    // Test sorting accessibility
    const sortableHeader = page.locator('[role="columnheader"][aria-sort]').first();
    if (await sortableHeader.count() > 0) {
      await sortableHeader.click();
      
      const sortDirection = await sortableHeader.getAttribute('aria-sort');
      expect(['ascending', 'descending']).toContain(sortDirection);
    }
  });

  test('progress indicators accessibility', async ({ page }) => {
    // This test would require starting a document analysis
    // For now, we'll test the static progress components
    await page.goto('/dashboard');
    
    // Look for any progress indicators
    const progressBars = page.locator('[role="progressbar"]');
    const progressCount = await progressBars.count();
    
    if (progressCount > 0) {
      const firstProgress = progressBars.first();
      
      // Should have proper ARIA attributes
      await expect(firstProgress).toHaveAttribute('aria-valuemin');
      await expect(firstProgress).toHaveAttribute('aria-valuemax');
      await expect(firstProgress).toHaveAttribute('aria-valuenow');
      
      // Should have accessible label
      const label = await firstProgress.getAttribute('aria-label');
      const labelledBy = await firstProgress.getAttribute('aria-labelledby');
      
      expect(label || labelledBy).toBeTruthy();
    }
  });

  test('responsive design accessibility', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Mobile menu should be accessible
    const mobileMenuButton = page.locator('[data-testid="mobile-menu-btn"]');
    if (await mobileMenuButton.count() > 0) {
      await expect(mobileMenuButton).toHaveAttribute('aria-expanded', 'false');
      
      await mobileMenuButton.click();
      await expect(mobileMenuButton).toHaveAttribute('aria-expanded', 'true');
      
      // Menu should be keyboard accessible
      await page.keyboard.press('Tab');
      const focusedElement = page.locator(':focus');
      
      // Should focus first menu item
      const menuItems = page.locator('[role="menuitem"]');
      if (await menuItems.count() > 0) {
        const firstMenuItem = menuItems.first();
        const isFocused = await focusedElement.evaluate((el, menuItem) => {
          return el === menuItem;
        }, await firstMenuItem.elementHandle());
        
        expect(isFocused).toBe(true);
      }
    }
    
    // Reset viewport
    await page.setViewportSize({ width: 1280, height: 720 });
  });
});