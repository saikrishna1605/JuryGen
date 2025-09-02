/**
 * End-to-end tests for complete document workflow.
 * 
 * Tests the full user journey from document upload through analysis
 * to results viewing and export.
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

// Test data and utilities
const TEST_PDF_PATH = path.join(__dirname, '../fixtures/sample-contract.pdf');
const TEST_USER_EMAIL = 'test@example.com';
const TEST_USER_PASSWORD = 'testpassword123';

class DocumentWorkflowPage {
  constructor(private page: Page) {}

  async navigateToUpload() {
    await this.page.goto('/upload');
    await this.page.waitForLoadState('networkidle');
  }

  async uploadDocument(filePath: string) {
    // Upload file
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);

    // Wait for upload to complete
    await this.page.waitForSelector('[data-testid="upload-success"]', {
      timeout: 30000
    });

    // Get document ID from success message
    const documentId = await this.page.getAttribute(
      '[data-testid="document-id"]',
      'data-document-id'
    );

    return documentId;
  }

  async startAnalysis(documentId: string) {
    // Navigate to document page
    await this.page.goto(`/documents/${documentId}`);
    
    // Start analysis
    await this.page.click('[data-testid="start-analysis-btn"]');
    
    // Wait for analysis to start
    await this.page.waitForSelector('[data-testid="analysis-progress"]');
  }

  async waitForAnalysisComplete(timeout = 120000) {
    // Wait for analysis to complete
    await this.page.waitForSelector('[data-testid="analysis-complete"]', {
      timeout
    });
  }

  async viewResults() {
    // Click to view results
    await this.page.click('[data-testid="view-results-btn"]');
    
    // Wait for results page to load
    await this.page.waitForSelector('[data-testid="analysis-results"]');
  }

  async exportResults(format: 'pdf' | 'docx' | 'csv') {
    // Click export button
    await this.page.click('[data-testid="export-btn"]');
    
    // Select format
    await this.page.click(`[data-testid="export-${format}"]`);
    
    // Wait for download
    const downloadPromise = this.page.waitForEvent('download');
    await this.page.click('[data-testid="confirm-export"]');
    
    const download = await downloadPromise;
    return download;
  }
}

class AuthPage {
  constructor(private page: Page) {}

  async signIn(email: string, password: string) {
    await this.page.goto('/signin');
    
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    
    await this.page.click('[data-testid="signin-btn"]');
    
    // Wait for redirect to dashboard
    await this.page.waitForURL('/dashboard');
  }

  async signOut() {
    await this.page.click('[data-testid="user-menu"]');
    await this.page.click('[data-testid="signout-btn"]');
    
    // Wait for redirect to home
    await this.page.waitForURL('/');
  }
}

test.describe('Document Analysis Workflow', () => {
  let authPage: AuthPage;
  let workflowPage: DocumentWorkflowPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    workflowPage = new DocumentWorkflowPage(page);
    
    // Sign in before each test
    await authPage.signIn(TEST_USER_EMAIL, TEST_USER_PASSWORD);
  });

  test.afterEach(async ({ page }) => {
    // Clean up - sign out
    await authPage.signOut();
  });

  test('complete document analysis workflow', async ({ page }) => {
    // Step 1: Upload document
    await workflowPage.navigateToUpload();
    
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);
    expect(documentId).toBeTruthy();

    // Step 2: Start analysis
    await workflowPage.startAnalysis(documentId!);
    
    // Verify analysis progress is shown
    await expect(page.locator('[data-testid="analysis-progress"]')).toBeVisible();
    
    // Step 3: Wait for analysis completion
    await workflowPage.waitForAnalysisComplete();
    
    // Verify completion notification
    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible();

    // Step 4: View results
    await workflowPage.viewResults();
    
    // Verify results are displayed
    await expect(page.locator('[data-testid="clause-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="risk-summary"]')).toBeVisible();
    await expect(page.locator('[data-testid="document-summary"]')).toBeVisible();

    // Step 5: Export results
    const download = await workflowPage.exportResults('pdf');
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });

  test('document upload validation', async ({ page }) => {
    await workflowPage.navigateToUpload();

    // Test invalid file type
    const invalidFile = path.join(__dirname, '../fixtures/invalid-file.txt');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(invalidFile);

    // Should show error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-error"]')).toContainText('Unsupported file type');
  });

  test('analysis progress tracking', async ({ page }) => {
    // Upload document
    await workflowPage.navigateToUpload();
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);

    // Start analysis
    await workflowPage.startAnalysis(documentId!);

    // Verify progress indicators
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    await expect(page.locator('[data-testid="current-stage"]')).toBeVisible();
    
    // Verify stages are shown
    const stages = ['OCR Processing', 'Clause Analysis', 'Risk Assessment', 'Summary Generation'];
    
    for (const stage of stages) {
      await expect(page.locator(`[data-testid="stage-${stage.toLowerCase().replace(' ', '-')}"]`)).toBeVisible();
    }

    // Wait for completion
    await workflowPage.waitForAnalysisComplete();
    
    // Verify final progress state
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '100');
  });

  test('real-time status updates', async ({ page }) => {
    // Upload document
    await workflowPage.navigateToUpload();
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);

    // Start analysis
    await workflowPage.startAnalysis(documentId!);

    // Monitor status updates
    let lastStatus = '';
    const statusUpdates: string[] = [];

    // Listen for status changes
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        const data = JSON.parse(event.payload as string);
        if (data.type === 'job_status_update' && data.document_id === documentId) {
          const newStatus = data.status;
          if (newStatus !== lastStatus) {
            statusUpdates.push(newStatus);
            lastStatus = newStatus;
          }
        }
      });
    });

    // Wait for analysis to complete
    await workflowPage.waitForAnalysisComplete();

    // Verify we received status updates
    expect(statusUpdates.length).toBeGreaterThan(0);
    expect(statusUpdates).toContain('processing');
    expect(statusUpdates[statusUpdates.length - 1]).toBe('completed');
  });

  test('clause highlighting and interaction', async ({ page }) => {
    // Complete analysis workflow
    await workflowPage.navigateToUpload();
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);
    await workflowPage.startAnalysis(documentId!);
    await workflowPage.waitForAnalysisComplete();
    await workflowPage.viewResults();

    // Verify PDF viewer is loaded
    await expect(page.locator('[data-testid="pdf-viewer"]')).toBeVisible();

    // Verify clause highlights are visible
    await expect(page.locator('[data-testid="clause-highlight"]').first()).toBeVisible();

    // Click on a clause highlight
    await page.locator('[data-testid="clause-highlight"]').first().click();

    // Verify clause details panel opens
    await expect(page.locator('[data-testid="clause-details"]')).toBeVisible();
    await expect(page.locator('[data-testid="clause-text"]')).toBeVisible();
    await expect(page.locator('[data-testid="risk-score"]')).toBeVisible();
    await expect(page.locator('[data-testid="risk-explanation"]')).toBeVisible();
  });

  test('voice interaction workflow', async ({ page }) => {
    // Complete analysis first
    await workflowPage.navigateToUpload();
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);
    await workflowPage.startAnalysis(documentId!);
    await workflowPage.waitForAnalysisComplete();
    await workflowPage.viewResults();

    // Navigate to voice Q&A
    await page.click('[data-testid="voice-qa-tab"]');

    // Verify voice interface is available
    await expect(page.locator('[data-testid="voice-recorder"]')).toBeVisible();
    await expect(page.locator('[data-testid="record-btn"]')).toBeVisible();

    // Test text input as fallback
    await page.fill('[data-testid="question-input"]', 'What are the main risks in this contract?');
    await page.click('[data-testid="ask-btn"]');

    // Wait for response
    await expect(page.locator('[data-testid="ai-response"]')).toBeVisible({ timeout: 30000 });
    
    // Verify response contains relevant information
    const response = await page.locator('[data-testid="ai-response"]').textContent();
    expect(response).toBeTruthy();
    expect(response!.length).toBeGreaterThan(50);
  });

  test('multi-language support', async ({ page }) => {
    // Change language to Spanish
    await page.click('[data-testid="language-selector"]');
    await page.click('[data-testid="lang-es"]');

    // Verify UI language changed
    await expect(page.locator('[data-testid="upload-title"]')).toContainText('Subir Documento');

    // Upload and analyze document
    await workflowPage.navigateToUpload();
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);
    await workflowPage.startAnalysis(documentId!);
    await workflowPage.waitForAnalysisComplete();
    await workflowPage.viewResults();

    // Verify results are in Spanish
    await expect(page.locator('[data-testid="summary-title"]')).toContainText('Resumen');
  });

  test('accessibility compliance', async ({ page }) => {
    // Enable high contrast mode
    await page.click('[data-testid="accessibility-menu"]');
    await page.click('[data-testid="high-contrast-toggle"]');

    // Verify high contrast styles applied
    await expect(page.locator('body')).toHaveClass(/high-contrast/);

    // Test keyboard navigation
    await workflowPage.navigateToUpload();
    
    // Navigate using Tab key
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="browse-files-btn"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="help-btn"]')).toBeFocused();

    // Test screen reader support
    const uploadButton = page.locator('[data-testid="browse-files-btn"]');
    await expect(uploadButton).toHaveAttribute('aria-label');
    await expect(uploadButton).toHaveAttribute('role', 'button');
  });

  test('error handling and recovery', async ({ page }) => {
    // Simulate network error during upload
    await page.route('**/api/v1/documents/upload', route => {
      route.abort('failed');
    });

    await workflowPage.navigateToUpload();
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_PDF_PATH);

    // Should show error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();

    // Remove network error simulation
    await page.unroute('**/api/v1/documents/upload');

    // Retry upload
    await page.click('[data-testid="retry-btn"]');

    // Should succeed on retry
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 30000 });
  });

  test('concurrent document processing', async ({ page, context }) => {
    // Open multiple tabs
    const page2 = await context.newPage();
    const workflowPage2 = new DocumentWorkflowPage(page2);
    const authPage2 = new AuthPage(page2);

    // Sign in to second tab
    await authPage2.signIn(TEST_USER_EMAIL, TEST_USER_PASSWORD);

    // Upload documents simultaneously
    const uploadPromise1 = (async () => {
      await workflowPage.navigateToUpload();
      return await workflowPage.uploadDocument(TEST_PDF_PATH);
    })();

    const uploadPromise2 = (async () => {
      await workflowPage2.navigateToUpload();
      return await workflowPage2.uploadDocument(TEST_PDF_PATH);
    })();

    const [documentId1, documentId2] = await Promise.all([uploadPromise1, uploadPromise2]);

    expect(documentId1).toBeTruthy();
    expect(documentId2).toBeTruthy();
    expect(documentId1).not.toBe(documentId2);

    // Start analysis on both documents
    const analysisPromise1 = (async () => {
      await workflowPage.startAnalysis(documentId1!);
      await workflowPage.waitForAnalysisComplete();
    })();

    const analysisPromise2 = (async () => {
      await workflowPage2.startAnalysis(documentId2!);
      await workflowPage2.waitForAnalysisComplete();
    })();

    // Both should complete successfully
    await Promise.all([analysisPromise1, analysisPromise2]);

    // Clean up
    await authPage2.signOut();
    await page2.close();
  });

  test('performance benchmarks', async ({ page }) => {
    const performanceMetrics = {
      uploadTime: 0,
      analysisTime: 0,
      renderTime: 0,
    };

    // Measure upload time
    const uploadStart = Date.now();
    await workflowPage.navigateToUpload();
    const documentId = await workflowPage.uploadDocument(TEST_PDF_PATH);
    performanceMetrics.uploadTime = Date.now() - uploadStart;

    // Measure analysis time
    const analysisStart = Date.now();
    await workflowPage.startAnalysis(documentId!);
    await workflowPage.waitForAnalysisComplete();
    performanceMetrics.analysisTime = Date.now() - analysisStart;

    // Measure results rendering time
    const renderStart = Date.now();
    await workflowPage.viewResults();
    await expect(page.locator('[data-testid="analysis-results"]')).toBeVisible();
    performanceMetrics.renderTime = Date.now() - renderStart;

    // Assert performance benchmarks
    expect(performanceMetrics.uploadTime).toBeLessThan(30000); // 30 seconds
    expect(performanceMetrics.analysisTime).toBeLessThan(120000); // 2 minutes
    expect(performanceMetrics.renderTime).toBeLessThan(5000); // 5 seconds

    console.log('Performance Metrics:', performanceMetrics);
  });
});