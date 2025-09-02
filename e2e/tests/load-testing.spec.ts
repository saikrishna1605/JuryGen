/**
 * Load testing scenarios for AI Legal Companion.
 * 
 * Tests system performance under various load conditions
 * including concurrent users, document processing, and API stress testing.
 */

import { test, expect, Browser } from '@playwright/test';
import path from 'path';
import { LoadTester, PerformanceMonitor } from '../utils/performance';

const TEST_PDF_PATH = path.join(__dirname, '../fixtures/sample-contract.pdf');
const TEST_USER_EMAIL = 'loadtest@example.com';
const TEST_USER_PASSWORD = 'loadtestpassword123';

test.describe('Load Testing', () => {
  let loadTester: LoadTester;

  test.beforeAll(async ({ browser }) => {
    loadTester = new LoadTester(browser);
  });

  test('concurrent document uploads', async ({ browser }) => {
    const uploadTest = async (page: any) => {
      const performanceMonitor = new PerformanceMonitor(page);
      
      // Sign in
      await page.goto('/signin');
      await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
      await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
      await page.click('[data-testid="signin-btn"]');
      await page.waitForURL('/dashboard');
      
      // Navigate to upload
      await page.goto('/upload');
      await page.waitForLoadState('networkidle');
      
      // Upload document
      await performanceMonitor.measureUploadPerformance(async () => {
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_PDF_PATH);
        await page.waitForSelector('[data-testid="upload-success"]', { timeout: 30000 });
      });
      
      const metrics = performanceMonitor.getMetrics();
      expect(metrics.uploadTime).toBeLessThan(30000); // 30 seconds max
    };

    // Test with 10 concurrent users
    const result = await loadTester.runConcurrentUsers(uploadTest, 10, 5000);
    
    expect(result.successCount).toBeGreaterThanOrEqual(8); // 80% success rate minimum
    expect(result.averageTime).toBeLessThan(45000); // 45 seconds average
    
    console.log('Concurrent Upload Results:', {
      successRate: `${(result.successCount / 10) * 100}%`,
      averageTime: `${result.averageTime}ms`,
      errors: result.errors,
    });
  });

  test('concurrent document analysis', async ({ browser }) => {
    const analysisTest = async (page: any) => {
      const performanceMonitor = new PerformanceMonitor(page);
      
      // Sign in
      await page.goto('/signin');
      await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
      await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
      await page.click('[data-testid="signin-btn"]');
      await page.waitForURL('/dashboard');
      
      // Upload document first
      await page.goto('/upload');
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(TEST_PDF_PATH);
      await page.waitForSelector('[data-testid="upload-success"]', { timeout: 30000 });
      
      const documentId = await page.getAttribute(
        '[data-testid="document-id"]',
        'data-document-id'
      );
      
      // Start analysis
      await page.goto(`/documents/${documentId}`);
      
      await performanceMonitor.measureAnalysisPerformance(async () => {
        await page.click('[data-testid="start-analysis-btn"]');
        await page.waitForSelector('[data-testid="analysis-complete"]', { timeout: 180000 });
      });
      
      const metrics = performanceMonitor.getMetrics();
      expect(metrics.analysisTime).toBeLessThan(180000); // 3 minutes max
    };

    // Test with 5 concurrent analysis jobs
    const result = await loadTester.runConcurrentUsers(analysisTest, 5, 10000);
    
    expect(result.successCount).toBeGreaterThanOrEqual(4); // 80% success rate minimum
    expect(result.averageTime).toBeLessThan(200000); // 3.3 minutes average
    
    console.log('Concurrent Analysis Results:', {
      successRate: `${(result.successCount / 5) * 100}%`,
      averageTime: `${result.averageTime}ms`,
      errors: result.errors,
    });
  });

  test('stress test - increasing load', async ({ browser }) => {
    const basicWorkflowTest = async (page: any) => {
      // Sign in
      await page.goto('/signin');
      await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
      await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
      await page.click('[data-testid="signin-btn"]');
      await page.waitForURL('/dashboard');
      
      // Navigate around the app
      await page.goto('/documents');
      await page.waitForLoadState('networkidle');
      
      await page.goto('/upload');
      await page.waitForLoadState('networkidle');
      
      // Quick upload test
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(TEST_PDF_PATH);
      await page.waitForSelector('[data-testid="upload-success"]', { timeout: 30000 });
    };

    const stressResults = await loadTester.runStressTest(
      basicWorkflowTest,
      50, // max users
      5,  // step size
      30000 // step duration
    );
    
    // Find the breaking point
    const breakingPoint = stressResults.find(result => result.successRate < 90);
    
    console.log('Stress Test Results:');
    stressResults.forEach(result => {
      console.log(`${result.userCount} users: ${result.successRate.toFixed(1)}% success, ${result.averageResponseTime}ms avg`);
    });
    
    if (breakingPoint) {
      console.log(`System breaking point: ${breakingPoint.userCount} concurrent users`);
      expect(breakingPoint.userCount).toBeGreaterThanOrEqual(20); // Should handle at least 20 users
    } else {
      console.log('System handled maximum load successfully');
    }
  });

  test('memory leak detection', async ({ browser }) => {
    const memoryTest = async (page: any) => {
      const performanceMonitor = new PerformanceMonitor(page);
      
      // Sign in
      await page.goto('/signin');
      await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
      await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
      await page.click('[data-testid="signin-btn"]');
      
      const initialMemory = await performanceMonitor.measureMemoryUsage();
      
      // Perform multiple operations
      for (let i = 0; i < 10; i++) {
        await page.goto('/documents');
        await page.waitForLoadState('networkidle');
        
        await page.goto('/upload');
        await page.waitForLoadState('networkidle');
        
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
      }
      
      const finalMemory = await performanceMonitor.measureMemoryUsage();
      const metrics = performanceMonitor.getMetrics();
      
      // Check for significant memory increase
      const memoryIncrease = (metrics.heapUsed || 0) - (initialMemory.heapUsed || 0);
      const memoryIncreasePercent = (memoryIncrease / (initialMemory.heapUsed || 1)) * 100;
      
      console.log(`Memory increase: ${memoryIncrease} bytes (${memoryIncreasePercent.toFixed(1)}%)`);
      
      // Memory increase should be reasonable (less than 50% increase)
      expect(memoryIncreasePercent).toBeLessThan(50);
    };

    const page = await browser.newPage();
    await memoryTest(page);
    await page.close();
  });

  test('API endpoint stress testing', async ({ request }) => {
    // Test authentication endpoint
    const authResults = await Promise.allSettled(
      Array.from({ length: 20 }, async () => {
        const response = await request.post('/api/v1/auth/signin', {
          data: {
            email: TEST_USER_EMAIL,
            password: TEST_USER_PASSWORD,
          },
        });
        return response.status();
      })
    );

    const authSuccesses = authResults.filter(
      result => result.status === 'fulfilled' && result.value === 200
    ).length;

    expect(authSuccesses).toBeGreaterThanOrEqual(18); // 90% success rate

    // Test document listing endpoint (requires auth)
    // This would need proper authentication setup
    console.log(`Auth endpoint: ${authSuccesses}/20 successful requests`);
  });

  test('database connection pooling', async ({ browser }) => {
    const dbTest = async (page: any) => {
      // Sign in
      await page.goto('/signin');
      await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
      await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
      await page.click('[data-testid="signin-btn"]');
      
      // Make multiple database-heavy requests
      await page.goto('/documents');
      await page.waitForLoadState('networkidle');
      
      // Trigger multiple API calls
      await page.evaluate(() => {
        // Simulate multiple concurrent API calls
        const promises = [];
        for (let i = 0; i < 10; i++) {
          promises.push(
            fetch('/api/v1/documents', {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
              },
            })
          );
        }
        return Promise.all(promises);
      });
    };

    // Test with multiple concurrent users making DB requests
    const result = await loadTester.runConcurrentUsers(dbTest, 15, 2000);
    
    expect(result.successCount).toBeGreaterThanOrEqual(12); // 80% success rate
    
    console.log('Database Connection Test:', {
      successRate: `${(result.successCount / 15) * 100}%`,
      averageTime: `${result.averageTime}ms`,
    });
  });

  test('file upload size limits', async ({ browser }) => {
    const page = await browser.newPage();
    
    // Sign in
    await page.goto('/signin');
    await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
    await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
    await page.click('[data-testid="signin-btn"]');
    
    await page.goto('/upload');
    
    // Test with maximum allowed file size (50MB)
    const largeFileContent = 'x'.repeat(50 * 1024 * 1024); // 50MB
    const largeFile = new File([largeFileContent], 'large.pdf', {
      type: 'application/pdf',
    });
    
    // This should work (at the limit)
    await page.setInputFiles('input[type="file"]', {
      name: 'large.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from(largeFileContent),
    });
    
    // Should show upload progress
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
    
    // Test with oversized file (51MB)
    const oversizedContent = 'x'.repeat(51 * 1024 * 1024); // 51MB
    
    await page.setInputFiles('input[type="file"]', {
      name: 'oversized.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from(oversizedContent),
    });
    
    // Should show error
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-error"]')).toContainText('File too large');
    
    await page.close();
  });

  test('real-time connection stability', async ({ browser }) => {
    const page = await browser.newPage();
    
    // Sign in and start document analysis
    await page.goto('/signin');
    await page.fill('[data-testid="email-input"]', TEST_USER_EMAIL);
    await page.fill('[data-testid="password-input"]', TEST_USER_PASSWORD);
    await page.click('[data-testid="signin-btn"]');
    
    // Upload and start analysis
    await page.goto('/upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_PDF_PATH);
    await page.waitForSelector('[data-testid="upload-success"]', { timeout: 30000 });
    
    const documentId = await page.getAttribute(
      '[data-testid="document-id"]',
      'data-document-id'
    );
    
    await page.goto(`/documents/${documentId}`);
    await page.click('[data-testid="start-analysis-btn"]');
    
    // Monitor WebSocket connection stability
    let connectionDrops = 0;
    let reconnections = 0;
    
    page.on('websocket', ws => {
      ws.on('close', () => {
        connectionDrops++;
      });
      
      ws.on('framereceived', event => {
        const data = JSON.parse(event.payload as string);
        if (data.type === 'connection_restored') {
          reconnections++;
        }
      });
    });
    
    // Wait for analysis to complete
    await page.waitForSelector('[data-testid="analysis-complete"]', { timeout: 180000 });
    
    // Check connection stability
    console.log(`Connection drops: ${connectionDrops}, Reconnections: ${reconnections}`);
    
    // Should have minimal connection issues
    expect(connectionDrops).toBeLessThanOrEqual(2);
    
    await page.close();
  });
});