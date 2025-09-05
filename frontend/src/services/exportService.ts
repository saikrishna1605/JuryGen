import api from '../utils/api';

export interface ExportOptions {
  format: 'pdf' | 'docx' | 'csv' | 'json';
  includeAnnotations?: boolean;
  includeRiskHighlights?: boolean;
  includeComments?: boolean;
  includeMetadata?: boolean;
  template?: 'standard' | 'detailed' | 'summary';
  language?: string;
}

export interface ExportRequest {
  documentId: string;
  jobId: string;
  options: ExportOptions;
}

export interface ExportResponse {
  exportId: string;
  downloadUrl: string;
  filename: string;
  size: number;
  expiresAt: string;
  status: 'generating' | 'ready' | 'failed';
}

export interface ExportProgress {
  exportId: string;
  progress: number; // 0-100
  stage: string;
  estimatedTimeRemaining?: number;
}

export class ExportService {
  /**
   * Request export generation
   */
  async requestExport(request: ExportRequest): Promise<ExportResponse> {
    const response = await api.post('/exports/generate', request);
    return response.data;
  }

  /**
   * Get export status and progress
   */
  async getExportStatus(exportId: string): Promise<ExportResponse> {
    const response = await api.get(`/exports/${exportId}/status`);
    return response.data;
  }

  /**
   * Download export file
   */
  async downloadExport(exportId: string): Promise<Blob> {
    const response = await api.get(`/exports/${exportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Get export progress stream
   */
  getExportProgressStream(exportId: string): EventSource {
    return new EventSource(`/api/exports/${exportId}/progress`);
  }

  /**
   * Generate PDF with highlighted clauses and annotations
   */
  async generatePDF(documentId: string, jobId: string, options: Partial<ExportOptions> = {}): Promise<ExportResponse> {
    return this.requestExport({
      documentId,
      jobId,
      options: {
        format: 'pdf',
        includeAnnotations: true,
        includeRiskHighlights: true,
        includeComments: true,
        template: 'detailed',
        ...options,
      },
    });
  }

  /**
   * Generate DOCX with track changes and comments
   */
  async generateDOCX(documentId: string, jobId: string, options: Partial<ExportOptions> = {}): Promise<ExportResponse> {
    return this.requestExport({
      documentId,
      jobId,
      options: {
        format: 'docx',
        includeAnnotations: true,
        includeComments: true,
        template: 'detailed',
        ...options,
      },
    });
  }

  /**
   * Generate CSV with clause analysis data
   */
  async generateCSV(documentId: string, jobId: string, options: Partial<ExportOptions> = {}): Promise<ExportResponse> {
    return this.requestExport({
      documentId,
      jobId,
      options: {
        format: 'csv',
        includeMetadata: true,
        ...options,
      },
    });
  }

  /**
   * Generate JSON with complete analysis data
   */
  async generateJSON(documentId: string, jobId: string, options: Partial<ExportOptions> = {}): Promise<ExportResponse> {
    return this.requestExport({
      documentId,
      jobId,
      options: {
        format: 'json',
        includeMetadata: true,
        includeAnnotations: true,
        includeComments: true,
        ...options,
      },
    });
  }

  /**
   * Get available export templates
   */
  async getExportTemplates(): Promise<Array<{ id: string; name: string; description: string; formats: string[] }>> {
    const response = await api.get('/exports/templates');
    return response.data;
  }

  /**
   * Cancel export generation
   */
  async cancelExport(exportId: string): Promise<void> {
    await api.delete(`/exports/${exportId}`);
  }

  /**
   * Get export history for a user
   */
  async getExportHistory(limit: number = 20): Promise<ExportResponse[]> {
    const response = await api.get('/exports/history', {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Bulk export multiple documents
   */
  async bulkExport(requests: ExportRequest[]): Promise<{ batchId: string; exports: ExportResponse[] }> {
    const response = await api.post('/exports/bulk', { requests });
    return response.data;
  }

  /**
   * Get export analytics
   */
  async getExportAnalytics(): Promise<{
    totalExports: number;
    exportsByFormat: Record<string, number>;
    exportsByTemplate: Record<string, number>;
    averageGenerationTime: number;
  }> {
    const response = await api.get('/exports/analytics');
    return response.data;
  }
}

export const exportService = new ExportService();