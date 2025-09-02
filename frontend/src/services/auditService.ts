/**
 * Audit Service
 * 
 * Handles API calls for audit logging and compliance including:
 * - Audit log querying and analysis
 * - Compliance reporting
 * - Security event monitoring
 * - User activity tracking
 */

import { apiClient } from '../lib/api';

export interface AuditLogQuery {
  startTime?: Date;
  endTime?: Date;
  userId?: string;
  eventType?: string;
  resourceType?: string;
  resourceId?: string;
  limit?: number;
  offset?: number;
}

export interface AuditLog {
  event_id: string;
  event_type: string;
  timestamp: string;
  user_id?: string;
  session_id?: string;
  ip_address?: string;
  user_agent?: string;
  resource_type?: string;
  resource_id?: string;
  action: string;
  details: Record<string, any>;
  result: string;
  compliance_frameworks: string[];
}

export interface AuditLogsResponse {
  audit_logs: AuditLog[];
  count: number;
  filters: Record<string, any>;
  retrieved_at: string;
}

export interface UserActivitySummary {
  user_id: string;
  period_days: number;
  total_events: number;
  event_types: Record<string, number>;
  daily_activity: Record<string, number>;
  resource_access: Record<string, number>;
  compliance_events: Record<string, number>;
  security_events: number;
  last_activity?: string;
  most_active_day?: string;
  risk_score: number;
}

export interface SecurityEventRequest {
  event_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  source_ip?: string;
  indicators?: Record<string, any>;
  auto_mitigate?: boolean;
}

export interface SecurityEvent {
  event_id: string;
  event_type: string;
  severity: string;
  timestamp: string;
  source_ip?: string;
  user_id?: string;
  description: string;
  indicators: Record<string, any>;
  mitigated: boolean;
  mitigation_actions: string[];
}

export interface ComplianceReportRequest {
  framework: 'GDPR' | 'CCPA' | 'HIPAA' | 'SOX' | 'PCI_DSS' | 'ISO_27001';
  start_date: Date;
  end_date: Date;
}

export interface ComplianceReport {
  report_id: string;
  framework: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  total_events: number;
  compliant_events: number;
  non_compliant_events: number;
  compliance_score: number;
  findings: Array<{
    type: string;
    severity: string;
    description: string;
    recommendation: string;
  }>;
  recommendations: string[];
}

export interface AuditStatistics {
  period_days: number;
  total_events: number;
  event_types: Record<string, number>;
  users: Record<string, number>;
  results: Record<string, number>;
  compliance_frameworks: Record<string, number>;
  daily_activity: Record<string, number>;
  top_resources: Record<string, number>;
  generated_at: string;
}

export interface AvailableOptions {
  event_types: Array<{
    value: string;
    name: string;
    description: string;
  }>;
  compliance_frameworks: Array<{
    value: string;
    name: string;
    description: string;
  }>;
  security_severities: Array<{
    value: string;
    name: string;
    description: string;
  }>;
}

class AuditService {
  private baseUrl = '/api/v1/audit';

  /**
   * Query audit logs with filters
   */
  async queryAuditLogs(query: AuditLogQuery): Promise<AuditLogsResponse> {
    const params = new URLSearchParams();
    
    if (query.startTime) {
      params.append('start_time', query.startTime.toISOString());
    }
    if (query.endTime) {
      params.append('end_time', query.endTime.toISOString());
    }
    if (query.userId) {
      params.append('user_id', query.userId);
    }
    if (query.eventType) {
      params.append('event_type', query.eventType);
    }
    if (query.resourceType) {
      params.append('resource_type', query.resourceType);
    }
    if (query.resourceId) {
      params.append('resource_id', query.resourceId);
    }
    if (query.limit) {
      params.append('limit', query.limit.toString());
    }

    const response = await apiClient.get(`${this.baseUrl}/logs?${params.toString()}`);
    return response.data;
  }

  /**
   * Get audit logs for a specific user
   */
  async getUserAuditLogs(userId: string, days: number = 30, limit: number = 100): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/logs/user/${userId}?days=${days}&limit=${limit}`);
    return response.data;
  }

  /**
   * Get user activity summary
   */
  async getUserActivitySummary(userId: string, days: number = 30): Promise<{ activity_summary: UserActivitySummary }> {
    const response = await apiClient.get(`${this.baseUrl}/activity/user/${userId}?days=${days}`);
    return response.data;
  }

  /**
   * Log a security event
   */
  async logSecurityEvent(request: SecurityEventRequest): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/security-events`, request);
    return response.data;
  }

  /**
   * Get recent security events
   */
  async getSecurityEvents(hours: number = 24, severity?: string, limit: number = 100): Promise<{ security_events: SecurityEvent[] }> {
    let url = `${this.baseUrl}/security-events?hours=${hours}&limit=${limit}`;
    if (severity) {
      url += `&severity=${severity}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  }

  /**
   * Generate a compliance report
   */
  async generateComplianceReport(request: ComplianceReportRequest): Promise<{ compliance_report: ComplianceReport }> {
    const response = await apiClient.post(`${this.baseUrl}/compliance/reports`, {
      framework: request.framework,
      start_date: request.start_date.toISOString(),
      end_date: request.end_date.toISOString()
    });
    return response.data;
  }

  /**
   * Get existing compliance reports
   */
  async getComplianceReports(framework?: string, limit: number = 50): Promise<{ compliance_reports: ComplianceReport[] }> {
    let url = `${this.baseUrl}/compliance/reports?limit=${limit}`;
    if (framework) {
      url += `&framework=${framework}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  }

  /**
   * Get current compliance status overview
   */
  async getComplianceStatus(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/compliance/status`);
    return response.data;
  }

  /**
   * Clean up expired audit logs
   */
  async cleanupExpiredLogs(batchSize: number = 100): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/cleanup?batch_size=${batchSize}`);
    return response.data;
  }

  /**
   * Get audit log statistics
   */
  async getAuditStatistics(days: number = 30): Promise<{ audit_statistics: AuditStatistics }> {
    const response = await apiClient.get(`${this.baseUrl}/statistics?days=${days}`);
    return response.data;
  }

  /**
   * Get available event types and options
   */
  async getAvailableEventTypes(): Promise<AvailableOptions> {
    const response = await apiClient.get(`${this.baseUrl}/event-types`);
    return response.data;
  }

  /**
   * Export audit logs as CSV
   */
  async exportAuditLogs(query: AuditLogQuery): Promise<string> {
    const params = new URLSearchParams();
    
    if (query.startTime) {
      params.append('start_time', query.startTime.toISOString());
    }
    if (query.endTime) {
      params.append('end_time', query.endTime.toISOString());
    }
    if (query.userId) {
      params.append('user_id', query.userId);
    }
    if (query.eventType) {
      params.append('event_type', query.eventType);
    }
    if (query.resourceType) {
      params.append('resource_type', query.resourceType);
    }
    if (query.resourceId) {
      params.append('resource_id', query.resourceId);
    }

    const response = await apiClient.get(`${this.baseUrl}/logs/export?${params.toString()}`, {
      responseType: 'text'
    });
    return response.data;
  }

  /**
   * Get audit dashboard data
   */
  async getAuditDashboardData(days: number = 30): Promise<any> {
    try {
      const [statistics, complianceStatus, securityEvents] = await Promise.all([
        this.getAuditStatistics(days),
        this.getComplianceStatus(),
        this.getSecurityEvents(days * 24)
      ]);

      return {
        statistics: statistics.audit_statistics,
        compliance: complianceStatus.compliance_status,
        security_events: securityEvents.security_events,
        summary: {
          total_events: statistics.audit_statistics.total_events,
          compliance_score: this.calculateOverallComplianceScore(complianceStatus.compliance_status),
          security_incidents: securityEvents.security_events.filter((e: SecurityEvent) => 
            e.severity === 'HIGH' || e.severity === 'CRITICAL'
          ).length,
          top_event_type: this.getTopEventType(statistics.audit_statistics.event_types),
          most_active_user: this.getMostActiveUser(statistics.audit_statistics.users)
        }
      };
    } catch (error) {
      console.error('Error getting audit dashboard data:', error);
      throw error;
    }
  }

  /**
   * Search audit logs by text
   */
  async searchAuditLogs(searchTerm: string, days: number = 30): Promise<AuditLogsResponse> {
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - (days * 24 * 60 * 60 * 1000));

    // Get all logs in the time range and filter client-side
    // In a real implementation, this would be done server-side
    const allLogs = await this.queryAuditLogs({
      startTime,
      endTime,
      limit: 1000
    });

    const filteredLogs = allLogs.audit_logs.filter(log => 
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.user_id && log.user_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      JSON.stringify(log.details).toLowerCase().includes(searchTerm.toLowerCase())
    );

    return {
      ...allLogs,
      audit_logs: filteredLogs,
      count: filteredLogs.length
    };
  }

  /**
   * Get compliance trends over time
   */
  async getComplianceTrends(framework: string, days: number = 90): Promise<any> {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (days * 24 * 60 * 60 * 1000));

    // Generate weekly reports for the period
    const trends = [];
    const weekMs = 7 * 24 * 60 * 60 * 1000;
    
    for (let date = new Date(startDate); date < endDate; date = new Date(date.getTime() + weekMs)) {
      const weekEnd = new Date(Math.min(date.getTime() + weekMs, endDate.getTime()));
      
      try {
        const report = await this.generateComplianceReport({
          framework: framework as any,
          start_date: date,
          end_date: weekEnd
        });

        trends.push({
          week_start: date.toISOString(),
          week_end: weekEnd.toISOString(),
          compliance_score: report.compliance_report.compliance_score,
          total_events: report.compliance_report.total_events,
          compliant_events: report.compliance_report.compliant_events,
          non_compliant_events: report.compliance_report.non_compliant_events
        });
      } catch (error) {
        console.error(`Error generating compliance report for week ${date.toISOString()}:`, error);
      }
    }

    return {
      framework,
      period_days: days,
      trends,
      generated_at: new Date().toISOString()
    };
  }

  /**
   * Get user risk assessment
   */
  async getUserRiskAssessment(userId: string, days: number = 30): Promise<any> {
    const [activity, auditLogs] = await Promise.all([
      this.getUserActivitySummary(userId, days),
      this.getUserAuditLogs(userId, days, 500)
    ]);

    const riskFactors = {
      failed_operations: auditLogs.audit_logs.filter((log: AuditLog) => log.result === 'failure').length,
      admin_actions: auditLogs.audit_logs.filter((log: AuditLog) => log.event_type === 'admin_action').length,
      data_deletions: auditLogs.audit_logs.filter((log: AuditLog) => log.event_type === 'data_delete').length,
      unusual_hours: this.calculateUnusualHoursActivity(auditLogs.audit_logs),
      multiple_ips: this.countUniqueIPs(auditLogs.audit_logs),
      rapid_actions: this.detectRapidActions(auditLogs.audit_logs)
    };

    const riskScore = this.calculateRiskScore(riskFactors);

    return {
      user_id: userId,
      period_days: days,
      risk_score: riskScore,
      risk_level: this.getRiskLevel(riskScore),
      risk_factors: riskFactors,
      activity_summary: activity.activity_summary,
      recommendations: this.generateRiskRecommendations(riskFactors, riskScore),
      assessed_at: new Date().toISOString()
    };
  }

  // Helper methods
  private calculateOverallComplianceScore(complianceStatus: Record<string, any>): number {
    const scores = Object.values(complianceStatus)
      .filter((status: any) => typeof status.compliance_rate === 'number')
      .map((status: any) => status.compliance_rate);
    
    return scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 100;
  }

  private getTopEventType(eventTypes: Record<string, number>): string {
    return Object.entries(eventTypes).reduce((a, b) => a[1] > b[1] ? a : b)[0];
  }

  private getMostActiveUser(users: Record<string, number>): string {
    return Object.entries(users).reduce((a, b) => a[1] > b[1] ? a : b)[0];
  }

  private calculateUnusualHoursActivity(logs: AuditLog[]): number {
    const unusualHours = logs.filter(log => {
      const hour = new Date(log.timestamp).getHours();
      return hour < 6 || hour > 22; // Outside normal business hours
    }).length;
    
    return unusualHours;
  }

  private countUniqueIPs(logs: AuditLog[]): number {
    const ips = new Set(logs.map(log => log.ip_address).filter(Boolean));
    return ips.size;
  }

  private detectRapidActions(logs: AuditLog[]): number {
    let rapidActions = 0;
    const sortedLogs = logs.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    
    for (let i = 1; i < sortedLogs.length; i++) {
      const timeDiff = new Date(sortedLogs[i].timestamp).getTime() - new Date(sortedLogs[i-1].timestamp).getTime();
      if (timeDiff < 1000) { // Less than 1 second between actions
        rapidActions++;
      }
    }
    
    return rapidActions;
  }

  private calculateRiskScore(riskFactors: Record<string, number>): number {
    let score = 0;
    
    score += riskFactors.failed_operations * 2;
    score += riskFactors.admin_actions * 3;
    score += riskFactors.data_deletions * 5;
    score += riskFactors.unusual_hours * 1;
    score += Math.max(0, riskFactors.multiple_ips - 2) * 2; // More than 2 IPs is suspicious
    score += riskFactors.rapid_actions * 1;
    
    return Math.min(score, 100); // Cap at 100
  }

  private getRiskLevel(score: number): string {
    if (score < 10) return 'LOW';
    if (score < 30) return 'MEDIUM';
    if (score < 60) return 'HIGH';
    return 'CRITICAL';
  }

  private generateRiskRecommendations(riskFactors: Record<string, number>, riskScore: number): string[] {
    const recommendations = [];
    
    if (riskFactors.failed_operations > 10) {
      recommendations.push('Review failed operations and provide additional training');
    }
    
    if (riskFactors.admin_actions > 5) {
      recommendations.push('Monitor administrative actions more closely');
    }
    
    if (riskFactors.data_deletions > 0) {
      recommendations.push('Implement additional approval process for data deletions');
    }
    
    if (riskFactors.unusual_hours > 10) {
      recommendations.push('Investigate activity outside normal business hours');
    }
    
    if (riskFactors.multiple_ips > 3) {
      recommendations.push('Verify user identity and consider IP restrictions');
    }
    
    if (riskFactors.rapid_actions > 20) {
      recommendations.push('Implement rate limiting to prevent automated actions');
    }
    
    if (riskScore > 50) {
      recommendations.push('Consider temporary access restrictions pending investigation');
    }
    
    return recommendations;
  }
}

// Export singleton instance
export const auditService = new AuditService();