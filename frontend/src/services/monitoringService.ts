/**
 * Monitoring Service
 * 
 * Handles API calls for monitoring and observability including:
 * - Health checks and system status
 * - Metrics dashboard data
 * - Alert management
 * - Performance monitoring
 * - Error reporting
 */

import { apiClient } from '../utils/api';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: Record<string, {
    status: string;
    timestamp: string;
    error?: string;
  }>;
  message: string;
}

export interface SystemMetrics {
  system_metrics: {
    cpu: {
      usage_percent: number;
      count: number;
      count_logical: number;
    };
    memory: {
      total: number;
      available: number;
      percent: number;
      used: number;
    };
    disk: {
      total: number;
      used: number;
      free: number;
      percent: number;
    };
    network: {
      bytes_sent: number;
      bytes_recv: number;
      packets_sent: number;
      packets_recv: number;
    };
    timestamp: string;
  };
  message: string;
}

export interface PerformanceSummary {
  performance_summary: {
    time_range_hours: number;
    request_metrics: {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      success_rate: number;
      average_response_time_ms: number;
      p95_response_time_ms: number;
      p99_response_time_ms: number;
    };
    error_metrics: {
      total_errors: number;
      error_rate: number;
      top_errors: Array<{ type: string; count: number }>;
    };
    resource_usage: {
      avg_cpu_percent: number;
      max_cpu_percent: number;
      avg_memory_percent: number;
      max_memory_percent: number;
    };
    ai_model_metrics: {
      total_calls: number;
      average_latency_ms: number;
      success_rate: number;
      cost_estimate_usd: number;
    };
    generated_at: string;
  };
  message: string;
}

export interface Alert {
  id: string;
  name: string;
  severity: 'CRITICAL' | 'ERROR' | 'WARNING' | 'INFO';
  status: 'ACTIVE' | 'RESOLVED';
  triggered_at: string;
  condition: string;
  current_value: string;
  threshold: string;
}

export interface ActiveAlerts {
  active_alerts: Alert[];
  count: number;
  retrieved_at: string;
}

export interface DashboardMetrics {
  dashboard_data: {
    time_range: {
      start: string;
      end: string;
    };
    metrics: {
      request_count: number;
      error_rate: number;
      avg_processing_time: number;
      active_users: number;
    };
    system_health: HealthStatus;
  };
  generated_at: string;
  time_range_hours: number;
}

export interface UptimeStatus {
  status: string;
  uptime_percent: number;
  current_uptime_hours: number;
  last_incident: string;
  services: Record<string, {
    status: string;
    uptime_percent: number;
  }>;
  response_times: {
    api_avg_ms: number;
    document_processing_avg_ms: number;
    ai_services_avg_ms: number;
  };
  last_updated: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  user_id?: string;
  operation?: string;
  error_type?: string;
  resource?: string;
  usage_percent?: number;
  retry_count?: number;
}

export interface RecentLogs {
  logs: LogEntry[];
  count: number;
  limit: number;
  level_filter?: string;
  retrieved_at: string;
}

export interface MetricRequest {
  metric_type: string;
  value: number;
  labels?: Record<string, string>;
}

export interface ErrorReportRequest {
  error_message: string;
  error_type: string;
  context?: Record<string, any>;
  stack_trace?: string;
}

export interface AlertPolicyRequest {
  name: string;
  condition: Record<string, any>;
  notification_channels: string[];
  severity: 'CRITICAL' | 'ERROR' | 'WARNING' | 'INFO';
}

class MonitoringService {
  private baseUrl = '/api/v1/monitoring';

  /**
   * Get comprehensive health status of the system
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await apiClient.get(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * Get simple health check for load balancers
   */
  async getSimpleHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await apiClient.get(`${this.baseUrl}/health/simple`);
    return response.data;
  }

  /**
   * Get metrics data for monitoring dashboard
   */
  async getDashboardMetrics(hours: number = 24): Promise<DashboardMetrics> {
    const response = await apiClient.get(`${this.baseUrl}/metrics/dashboard?hours=${hours}`);
    return response.data;
  }

  /**
   * Record a custom metric value
   */
  async recordMetric(request: MetricRequest): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/metrics/record`, request);
    return response.data;
  }

  /**
   * Report an application error
   */
  async reportError(request: ErrorReportRequest): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/errors/report`, request);
    return response.data;
  }

  /**
   * Create a new alert policy
   */
  async createAlertPolicy(request: AlertPolicyRequest): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/alerts/policies`, request);
    return response.data;
  }

  /**
   * Get current system metrics
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await apiClient.get(`${this.baseUrl}/system/metrics`);
    return response.data;
  }

  /**
   * Get performance summary for the specified time range
   */
  async getPerformanceSummary(hours: number = 1): Promise<PerformanceSummary> {
    const response = await apiClient.get(`${this.baseUrl}/performance/summary?hours=${hours}`);
    return response.data;
  }

  /**
   * Get system uptime and availability metrics
   */
  async getUptimeStatus(): Promise<UptimeStatus> {
    const response = await apiClient.get(`${this.baseUrl}/uptime`);
    return response.data;
  }

  /**
   * Start the monitoring loop
   */
  async startMonitoring(interval: number = 60): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/monitoring/start?interval=${interval}`);
    return response.data;
  }

  /**
   * Get recent application logs
   */
  async getRecentLogs(limit: number = 100, level?: string): Promise<RecentLogs> {
    let url = `${this.baseUrl}/logs/recent?limit=${limit}`;
    if (level) {
      url += `&level=${level}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  }

  /**
   * Get currently active alerts
   */
  async getActiveAlerts(): Promise<ActiveAlerts> {
    const response = await apiClient.get(`${this.baseUrl}/alerts/active`);
    return response.data;
  }

  /**
   * Get monitoring statistics
   */
  async getMonitoringStats(): Promise<any> {
    try {
      const [health, metrics, performance, alerts] = await Promise.all([
        this.getHealthStatus(),
        this.getSystemMetrics(),
        this.getPerformanceSummary(24),
        this.getActiveAlerts()
      ]);

      return {
        health,
        metrics,
        performance,
        alerts,
        summary: {
          overall_health: health.status,
          active_alerts_count: alerts.count,
          cpu_usage: metrics.system_metrics.cpu.usage_percent,
          memory_usage: metrics.system_metrics.memory.percent,
          disk_usage: metrics.system_metrics.disk.percent,
          success_rate: performance.performance_summary.request_metrics.success_rate,
          avg_response_time: performance.performance_summary.request_metrics.average_response_time_ms,
          error_rate: performance.performance_summary.error_metrics.error_rate
        }
      };
    } catch (error) {
      console.error('Error getting monitoring stats:', error);
      throw error;
    }
  }

  /**
   * Check if system is healthy
   */
  async isSystemHealthy(): Promise<boolean> {
    try {
      const health = await this.getSimpleHealth();
      return health.status === 'OK';
    } catch (error) {
      console.error('Error checking system health:', error);
      return false;
    }
  }

  /**
   * Get system status summary for status page
   */
  async getStatusPageData(): Promise<any> {
    try {
      const [uptime, health] = await Promise.all([
        this.getUptimeStatus(),
        this.getHealthStatus()
      ]);

      return {
        overall_status: uptime.status,
        uptime_percent: uptime.uptime_percent,
        services: uptime.services,
        response_times: uptime.response_times,
        health_checks: health.checks,
        last_updated: uptime.last_updated,
        incidents: {
          last_incident: uptime.last_incident,
          current_uptime_hours: uptime.current_uptime_hours
        }
      };
    } catch (error) {
      console.error('Error getting status page data:', error);
      throw error;
    }
  }

  /**
   * Report client-side error
   */
  async reportClientError(error: Error, context?: Record<string, any>): Promise<void> {
    try {
      await this.reportError({
        error_message: error.message,
        error_type: error.name,
        context: {
          ...context,
          user_agent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
          client_side: true
        },
        stack_trace: error.stack
      });
    } catch (reportError) {
      console.error('Failed to report client error:', reportError);
    }
  }

  /**
   * Track performance metric
   */
  async trackPerformance(operation: string, duration: number, success: boolean): Promise<void> {
    try {
      await this.recordMetric({
        metric_type: 'custom.googleapis.com/ai_legal_companion/client_operation_duration',
        value: duration,
        labels: {
          operation,
          success: success.toString(),
          client_side: 'true'
        }
      });
    } catch (error) {
      console.error('Failed to track performance metric:', error);
    }
  }

  /**
   * Monitor API call performance
   */
  monitorApiCall<T>(apiCall: () => Promise<T>, operation: string): Promise<T> {
    const startTime = performance.now();
    
    return apiCall()
      .then((result) => {
        const duration = performance.now() - startTime;
        this.trackPerformance(operation, duration, true);
        return result;
      })
      .catch((error) => {
        const duration = performance.now() - startTime;
        this.trackPerformance(operation, duration, false);
        this.reportClientError(error, { operation, duration });
        throw error;
      });
  }

  /**
   * Get real-time monitoring data
   */
  async getRealTimeData(): Promise<any> {
    return this.monitorApiCall(
      () => this.getMonitoringStats(),
      'get_realtime_monitoring_data'
    );
  }

  /**
   * Subscribe to monitoring updates (WebSocket or SSE)
   */
  subscribeToUpdates(callback: (data: any) => void): () => void {
    // This would implement WebSocket or SSE connection
    // For now, use polling
    const interval = setInterval(async () => {
      try {
        const data = await this.getRealTimeData();
        callback(data);
      } catch (error) {
        console.error('Error getting monitoring updates:', error);
      }
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }
}

// Export singleton instance
export const monitoringService = new MonitoringService();