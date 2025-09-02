/**
 * Data Lifecycle Service
 * 
 * Handles API calls for data lifecycle management including:
 * - Retention policy management
 * - User consent management
 * - Data residency controls
 * - Data export and deletion
 */

import { apiClient } from '../lib/api';

export interface RetentionPolicy {
  data_category: string;
  retention_period: string;
  custom_days?: number;
}

export interface ConsentSettings {
  consent_type: string;
  granted: boolean;
  metadata?: Record<string, any>;
}

export interface DataResidencyRequest {
  residency: string;
}

export interface DataSummary {
  user_id: string;
  data_residency: string;
  total_documents: number;
  storage_usage_bytes: number;
  storage_by_category: Record<string, number>;
  retention_policies: Record<string, any>;
  consents: Record<string, any>;
  generated_at: string;
}

export interface ConsentStatus {
  consent_status: Record<string, boolean>;
  detailed_consents: Record<string, any>;
}

export interface AvailableOptions {
  data_categories: Array<{
    value: string;
    name: string;
    description: string;
  }>;
  retention_periods: Array<{
    value: string;
    name: string;
    days: number;
  }>;
  data_residency_options: Array<{
    value: string;
    name: string;
    description: string;
  }>;
  consent_types: Array<{
    value: string;
    name: string;
    description: string;
  }>;
}

export interface ExportData {
  export_data: any;
  export_format: string;
  export_version: string;
  message: string;
}

export interface DeletionResult {
  deletion_counts: Record<string, number>;
  total_items_deleted: number;
  deletion_timestamp: string;
  message: string;
}

class DataLifecycleService {
  private baseUrl = '/api/v1/data-lifecycle';

  /**
   * Create or update a retention policy
   */
  async createRetentionPolicy(policy: RetentionPolicy): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/retention-policies`, policy);
    return response.data;
  }

  /**
   * Get all retention policies for the current user
   */
  async getRetentionPolicies(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/retention-policies`);
    return response.data;
  }

  /**
   * Update user consent for data usage
   */
  async updateConsent(consent: ConsentSettings): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/consent`, consent);
    return response.data;
  }

  /**
   * Get current consent status for all consent types
   */
  async getConsentStatus(): Promise<ConsentStatus> {
    const response = await apiClient.get(`${this.baseUrl}/consent`);
    return response.data;
  }

  /**
   * Set data residency preference
   */
  async setDataResidency(residency: string): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/data-residency`, { residency });
    return response.data;
  }

  /**
   * Get comprehensive data summary
   */
  async getDataSummary(): Promise<DataSummary> {
    const response = await apiClient.get(`${this.baseUrl}/data-summary`);
    return response.data;
  }

  /**
   * Export all user data for GDPR compliance
   */
  async exportUserData(): Promise<ExportData> {
    const response = await apiClient.post(`${this.baseUrl}/export-data`);
    return response.data;
  }

  /**
   * Delete all user data (right to be forgotten)
   */
  async deleteAllUserData(confirm: boolean): Promise<DeletionResult> {
    const response = await apiClient.delete(`${this.baseUrl}/delete-all-data?confirm=${confirm}`);
    return response.data;
  }

  /**
   * Manually trigger cleanup of expired data
   */
  async cleanupExpiredData(batchSize: number = 100): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/cleanup-expired?batch_size=${batchSize}`);
    return response.data;
  }

  /**
   * Get available options for data lifecycle management
   */
  async getAvailableOptions(): Promise<AvailableOptions> {
    const response = await apiClient.get(`${this.baseUrl}/available-options`);
    return response.data;
  }

  /**
   * Apply retention policy to a specific document
   */
  async applyRetentionToDocument(documentId: string, dataCategory: string): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/apply-retention`, {
      document_id: documentId,
      data_category: dataCategory
    });
    return response.data;
  }

  /**
   * Get retention policy for a specific document
   */
  async getDocumentRetentionInfo(documentId: string): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/document-retention/${documentId}`);
    return response.data;
  }

  /**
   * Check if user has granted specific consent
   */
  async checkSpecificConsent(consentType: string): Promise<boolean> {
    try {
      const consentStatus = await this.getConsentStatus();
      return consentStatus.consent_status[consentType] || false;
    } catch (error) {
      console.error('Error checking consent:', error);
      return false;
    }
  }

  /**
   * Bulk update multiple consent settings
   */
  async bulkUpdateConsents(consents: ConsentSettings[]): Promise<any> {
    const promises = consents.map(consent => this.updateConsent(consent));
    return Promise.all(promises);
  }

  /**
   * Get data retention summary by category
   */
  async getRetentionSummary(): Promise<Record<string, any>> {
    const summary = await this.getDataSummary();
    return {
      policies: summary.retention_policies,
      storage: summary.storage_by_category,
      total_documents: summary.total_documents,
      total_storage: summary.storage_usage_bytes
    };
  }

  /**
   * Schedule data deletion for a specific date
   */
  async scheduleDataDeletion(deletionDate: string, categories?: string[]): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/schedule-deletion`, {
      deletion_date: deletionDate,
      categories: categories || []
    });
    return response.data;
  }

  /**
   * Get scheduled deletions for the user
   */
  async getScheduledDeletions(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/scheduled-deletions`);
    return response.data;
  }

  /**
   * Cancel a scheduled deletion
   */
  async cancelScheduledDeletion(scheduleId: string): Promise<any> {
    const response = await apiClient.delete(`${this.baseUrl}/scheduled-deletions/${scheduleId}`);
    return response.data;
  }

  /**
   * Get data processing audit log
   */
  async getDataProcessingAudit(limit: number = 50): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/audit-log?limit=${limit}`);
    return response.data;
  }

  /**
   * Request data portability (structured export)
   */
  async requestDataPortability(format: 'json' | 'csv' | 'xml' = 'json'): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/data-portability`, { format });
    return response.data;
  }

  /**
   * Get compliance report
   */
  async getComplianceReport(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/compliance-report`);
    return response.data;
  }

  /**
   * Update data processing preferences
   */
  async updateDataProcessingPreferences(preferences: Record<string, any>): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/processing-preferences`, preferences);
    return response.data;
  }

  /**
   * Get data processing preferences
   */
  async getDataProcessingPreferences(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/processing-preferences`);
    return response.data;
  }
}

// Export singleton instance
export const dataLifecycleService = new DataLifecycleService();