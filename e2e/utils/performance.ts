/**
 * Performance testing utilities for E2E tests.
 * 
 * Provides tools for measuring and validating performance metrics
 * across different scenarios and load conditions.
 */

import { Page, Browser } from '@playwright/test';

export interface PerformanceMetrics {
  // Timing metrics
  pageLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  
  // Custom metrics
  uploadTime: number;
  analysisTime: number;
  renderTime: number;
  
  // Resource metrics
  totalRequests: number;
  totalBytes: number;
  jsBytes: number;
  cssBytes: number;
  imageBytes: number;
  
  // Memory metrics
  heapUsed: number;
  heapTotal: number;
}

export interface PerformanceBenchmarks {
  pageLoadTime: { target: number; max: number };
  firstContentfulPaint: { target: number; max: number };
  largestContentfulPaint: { target: number; max: number };
  cumulativeLayoutShift: { target: number; max: number };
  uploadTime: { target: number; max: number };
  analysisTime: { target: number; max: number };
  renderTime: { target: number; max: number };
}

export const DEFAULT_BENCHMARKS: PerformanceBenchmarks = {
  pageLoadTime: { target: 2000, max: 5000 },
  firstContentfulPaint: { target: 1500, max: 3000 },
  largestContentfulPaint: { target: 2500, max: 4000 },
  cumulativeLayoutShift: { target: 0.1, max: 0.25 },
  uploadTime: { target: 10000, max: 30000 },
  analysisTime: { target: 60000, max: 120000 },
  renderTime: { target: 1000, max: 5000 },
};

export class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private startTimes: Map<string, number> = new Map();

  constructor(private page: Page) {}

  async startTimer(name: string): Promise<void> {
    this.startTimes.set(name, Date.now());
  }

  async endTimer(name: string): Promise<number> {
    const startTime = this.startTimes.get(name);
    if (!startTime) {
      throw new Error(`Timer '${name}' was not started`);
    }
    
    const duration = Date.now() - startTime;
    this.startTimes.delete(name);
    
    return duration;
  }

  async measurePageLoad(): Promise<void> {
    const startTime = Date.now();
    
    await this.page.waitForLoadState('networkidle');
    
    this.metrics.pageLoadTime = Date.now() - startTime;
    
    // Get Web Vitals
    const vitals = await this.page.evaluate(() => {
      return new Promise((resolve) => {
        const metrics: any = {};
        
        // First Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.name === 'first-contentful-paint') {
              metrics.firstContentfulPaint = entry.startTime;
            }
          });
        }).observe({ entryTypes: ['paint'] });
        
        // Largest Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          metrics.largestContentfulPaint = lastEntry.startTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });
        
        // Cumulative Layout Shift
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
          metrics.cumulativeLayoutShift = clsValue;
        }).observe({ entryTypes: ['layout-shift'] });
        
        // First Input Delay
        new PerformanceObserver((list) => {
          const firstInput = list.getEntries()[0];
          if (firstInput) {
            metrics.firstInputDelay = (firstInput as any).processingStart - firstInput.startTime;
          }
        }).observe({ entryTypes: ['first-input'] });
        
        // Wait a bit for metrics to be collected
        setTimeout(() => resolve(metrics), 2000);
      });
    });
    
    Object.assign(this.metrics, vitals);
  }

  async measureResourceUsage(): Promise<void> {
    const resourceMetrics = await this.page.evaluate(() => {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      
      let totalBytes = 0;
      let jsBytes = 0;
      let cssBytes = 0;
      let imageBytes = 0;
      
      resources.forEach((resource) => {
        const size = resource.transferSize || 0;
        totalBytes += size;
        
        if (resource.name.includes('.js')) {
          jsBytes += size;
        } else if (resource.name.includes('.css')) {
          cssBytes += size;
        } else if (resource.name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) {
          imageBytes += size;
        }
      });
      
      return {
        totalRequests: resources.length,
        totalBytes,
        jsBytes,
        cssBytes,
        imageBytes,
      };
    });
    
    Object.assign(this.metrics, resourceMetrics);
  }

  async measureMemoryUsage(): Promise<void> {
    const memoryMetrics = await this.page.evaluate(() => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        return {
          heapUsed: memory.usedJSHeapSize,
          heapTotal: memory.totalJSHeapSize,
        };
      }
      return { heapUsed: 0, heapTotal: 0 };
    });
    
    Object.assign(this.metrics, memoryMetrics);
  }

  async measureUploadPerformance(uploadFn: () => Promise<void>): Promise<number> {
    await this.startTimer('upload');
    await uploadFn();
    const uploadTime = await this.endTimer('upload');
    
    this.metrics.uploadTime = uploadTime;
    return uploadTime;
  }

  async measureAnalysisPerformance(analysisFn: () => Promise<void>): Promise<number> {
    await this.startTimer('analysis');
    await analysisFn();
    const analysisTime = await this.endTimer('analysis');
    
    this.metrics.analysisTime = analysisTime;
    return analysisTime;
  }

  async measureRenderPerformance(renderFn: () => Promise<void>): Promise<number> {
    await this.startTimer('render');
    await renderFn();
    const renderTime = await this.endTimer('render');
    
    this.metrics.renderTime = renderTime;
    return renderTime;
  }

  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  validateBenchmarks(benchmarks: PerformanceBenchmarks = DEFAULT_BENCHMARKS): {
    passed: boolean;
    failures: string[];
    warnings: string[];
  } {
    const failures: string[] = [];
    const warnings: string[] = [];
    
    const checks = [
      { metric: 'pageLoadTime', value: this.metrics.pageLoadTime },
      { metric: 'firstContentfulPaint', value: this.metrics.firstContentfulPaint },
      { metric: 'largestContentfulPaint', value: this.metrics.largestContentfulPaint },
      { metric: 'cumulativeLayoutShift', value: this.metrics.cumulativeLayoutShift },
      { metric: 'uploadTime', value: this.metrics.uploadTime },
      { metric: 'analysisTime', value: this.metrics.analysisTime },
      { metric: 'renderTime', value: this.metrics.renderTime },
    ];
    
    checks.forEach(({ metric, value }) => {
      if (value === undefined) return;
      
      const benchmark = benchmarks[metric as keyof PerformanceBenchmarks];
      if (!benchmark) return;
      
      if (value > benchmark.max) {
        failures.push(`${metric}: ${value}ms exceeds maximum ${benchmark.max}ms`);
      } else if (value > benchmark.target) {
        warnings.push(`${metric}: ${value}ms exceeds target ${benchmark.target}ms`);
      }
    });
    
    return {
      passed: failures.length === 0,
      failures,
      warnings,
    };
  }

  generateReport(): string {
    const metrics = this.getMetrics();
    const validation = this.validateBenchmarks();
    
    let report = '=== Performance Report ===\n\n';
    
    // Core Web Vitals
    report += 'Core Web Vitals:\n';
    report += `  First Contentful Paint: ${metrics.firstContentfulPaint || 'N/A'}ms\n`;
    report += `  Largest Contentful Paint: ${metrics.largestContentfulPaint || 'N/A'}ms\n`;
    report += `  Cumulative Layout Shift: ${metrics.cumulativeLayoutShift || 'N/A'}\n`;
    report += `  First Input Delay: ${metrics.firstInputDelay || 'N/A'}ms\n\n`;
    
    // Custom Metrics
    report += 'Custom Metrics:\n';
    report += `  Page Load Time: ${metrics.pageLoadTime || 'N/A'}ms\n`;
    report += `  Upload Time: ${metrics.uploadTime || 'N/A'}ms\n`;
    report += `  Analysis Time: ${metrics.analysisTime || 'N/A'}ms\n`;
    report += `  Render Time: ${metrics.renderTime || 'N/A'}ms\n\n`;
    
    // Resource Usage
    report += 'Resource Usage:\n';
    report += `  Total Requests: ${metrics.totalRequests || 'N/A'}\n`;
    report += `  Total Bytes: ${formatBytes(metrics.totalBytes || 0)}\n`;
    report += `  JavaScript: ${formatBytes(metrics.jsBytes || 0)}\n`;
    report += `  CSS: ${formatBytes(metrics.cssBytes || 0)}\n`;
    report += `  Images: ${formatBytes(metrics.imageBytes || 0)}\n\n`;
    
    // Memory Usage
    report += 'Memory Usage:\n';
    report += `  Heap Used: ${formatBytes(metrics.heapUsed || 0)}\n`;
    report += `  Heap Total: ${formatBytes(metrics.heapTotal || 0)}\n\n`;
    
    // Validation Results
    report += 'Benchmark Validation:\n';
    report += `  Status: ${validation.passed ? 'PASSED' : 'FAILED'}\n`;
    
    if (validation.failures.length > 0) {
      report += '  Failures:\n';
      validation.failures.forEach(failure => {
        report += `    - ${failure}\n`;
      });
    }
    
    if (validation.warnings.length > 0) {
      report += '  Warnings:\n';
      validation.warnings.forEach(warning => {
        report += `    - ${warning}\n`;
      });
    }
    
    return report;
  }
}

export class LoadTester {
  constructor(private browser: Browser) {}

  async runConcurrentUsers(
    testFn: (page: Page) => Promise<void>,
    userCount: number,
    rampUpTime: number = 0
  ): Promise<{
    totalTime: number;
    averageTime: number;
    successCount: number;
    errorCount: number;
    errors: string[];
  }> {
    const results: Array<{ success: boolean; time: number; error?: string }> = [];
    const startTime = Date.now();
    
    const userPromises: Promise<void>[] = [];
    
    for (let i = 0; i < userCount; i++) {
      const userPromise = (async () => {
        // Ramp up delay
        if (rampUpTime > 0) {
          await new Promise(resolve => setTimeout(resolve, (i * rampUpTime) / userCount));
        }
        
        const page = await this.browser.newPage();
        const userStartTime = Date.now();
        
        try {
          await testFn(page);
          results.push({
            success: true,
            time: Date.now() - userStartTime,
          });
        } catch (error) {
          results.push({
            success: false,
            time: Date.now() - userStartTime,
            error: error instanceof Error ? error.message : String(error),
          });
        } finally {
          await page.close();
        }
      })();
      
      userPromises.push(userPromise);
    }
    
    await Promise.all(userPromises);
    
    const totalTime = Date.now() - startTime;
    const successResults = results.filter(r => r.success);
    const errorResults = results.filter(r => !r.success);
    
    return {
      totalTime,
      averageTime: successResults.length > 0 
        ? successResults.reduce((sum, r) => sum + r.time, 0) / successResults.length 
        : 0,
      successCount: successResults.length,
      errorCount: errorResults.length,
      errors: errorResults.map(r => r.error || 'Unknown error'),
    };
  }

  async runStressTest(
    testFn: (page: Page) => Promise<void>,
    maxUsers: number,
    stepSize: number = 5,
    stepDuration: number = 30000
  ): Promise<Array<{
    userCount: number;
    successRate: number;
    averageResponseTime: number;
    errorRate: number;
  }>> {
    const results: Array<{
      userCount: number;
      successRate: number;
      averageResponseTime: number;
      errorRate: number;
    }> = [];
    
    for (let userCount = stepSize; userCount <= maxUsers; userCount += stepSize) {
      console.log(`Testing with ${userCount} concurrent users...`);
      
      const testResult = await this.runConcurrentUsers(testFn, userCount);
      
      const successRate = (testResult.successCount / userCount) * 100;
      const errorRate = (testResult.errorCount / userCount) * 100;
      
      results.push({
        userCount,
        successRate,
        averageResponseTime: testResult.averageTime,
        errorRate,
      });
      
      // Break if success rate drops below 90%
      if (successRate < 90) {
        console.log(`Breaking stress test at ${userCount} users due to low success rate: ${successRate}%`);
        break;
      }
      
      // Wait between steps
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    return results;
  }
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}