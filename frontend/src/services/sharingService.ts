import api from '../utils/api';

export interface ShareableLink {
  id: string;
  documentId: string;
  jobId: string;
  url: string;
  shortUrl: string;
  title: string;
  description?: string;
  permissions: SharePermissions;
  expiresAt?: string;
  createdAt: string;
  createdBy: string;
  accessCount: number;
  lastAccessedAt?: string;
  isActive: boolean;
}

export interface SharePermissions {
  canView: boolean;
  canComment: boolean;
  canDownload: boolean;
  canShare: boolean;
  requiresAuth: boolean;
  allowedUsers?: string[]; // Email addresses
  allowedDomains?: string[]; // Domain restrictions
}

export interface ShareRequest {
  documentId: string;
  jobId: string;
  title: string;
  description?: string;
  permissions: SharePermissions;
  expiresAt?: string; // ISO date string
  password?: string;
}

export interface CollaborationComment {
  id: string;
  shareId: string;
  userId: string;
  userName: string;
  userEmail: string;
  content: string;
  clauseId?: string; // Reference to specific clause
  position?: { x: number; y: number }; // Position on document
  replies: CollaborationComment[];
  createdAt: string;
  updatedAt: string;
  isResolved: boolean;
}

export interface ShareAnalytics {
  shareId: string;
  totalViews: number;
  uniqueViewers: number;
  viewsByDate: Array<{ date: string; views: number }>;
  topReferrers: Array<{ referrer: string; count: number }>;
  geographicData: Array<{ country: string; views: number }>;
  deviceTypes: Array<{ type: string; count: number }>;
}

export class SharingService {
  /**
   * Create a shareable link
   */
  async createShareableLink(request: ShareRequest): Promise<ShareableLink> {
    const response = await api.post('/sharing/create', request);
    return response.data;
  }

  /**
   * Get shareable link details
   */
  async getShareableLink(shareId: string): Promise<ShareableLink> {
    const response = await api.get(`/sharing/${shareId}`);
    return response.data;
  }

  /**
   * Update shareable link permissions
   */
  async updateShareableLink(
    shareId: string,
    updates: Partial<Pick<ShareableLink, 'title' | 'description' | 'permissions' | 'expiresAt'>>
  ): Promise<ShareableLink> {
    const response = await api.patch(`/sharing/${shareId}`, updates);
    return response.data;
  }

  /**
   * Deactivate shareable link
   */
  async deactivateShareableLink(shareId: string): Promise<void> {
    await api.delete(`/sharing/${shareId}`);
  }

  /**
   * Get all shareable links for a user
   */
  async getUserShareableLinks(): Promise<ShareableLink[]> {
    const response = await api.get('/sharing/my-links');
    return response.data;
  }

  /**
   * Access a shared document (public endpoint)
   */
  async accessSharedDocument(shareId: string, password?: string): Promise<{
    document: any;
    job: any;
    permissions: SharePermissions;
    canAccess: boolean;
  }> {
    const response = await api.post(`/sharing/${shareId}/access`, { password });
    return response.data;
  }

  /**
   * Add comment to shared document
   */
  async addComment(
    shareId: string,
    content: string,
    clauseId?: string,
    position?: { x: number; y: number },
    parentId?: string
  ): Promise<CollaborationComment> {
    const response = await api.post(`/sharing/${shareId}/comments`, {
      content,
      clauseId,
      position,
      parentId,
    });
    return response.data;
  }

  /**
   * Get comments for shared document
   */
  async getComments(shareId: string): Promise<CollaborationComment[]> {
    const response = await api.get(`/sharing/${shareId}/comments`);
    return response.data;
  }

  /**
   * Update comment
   */
  async updateComment(commentId: string, content: string): Promise<CollaborationComment> {
    const response = await api.patch(`/sharing/comments/${commentId}`, { content });
    return response.data;
  }

  /**
   * Delete comment
   */
  async deleteComment(commentId: string): Promise<void> {
    await api.delete(`/sharing/comments/${commentId}`);
  }

  /**
   * Resolve comment
   */
  async resolveComment(commentId: string, resolved: boolean = true): Promise<CollaborationComment> {
    const response = await api.patch(`/sharing/comments/${commentId}/resolve`, { resolved });
    return response.data;
  }

  /**
   * Get sharing analytics
   */
  async getShareAnalytics(shareId: string): Promise<ShareAnalytics> {
    const response = await api.get(`/sharing/${shareId}/analytics`);
    return response.data;
  }

  /**
   * Track share access (for analytics)
   */
  async trackAccess(shareId: string, metadata?: {
    referrer?: string;
    userAgent?: string;
    location?: string;
  }): Promise<void> {
    await api.post(`/sharing/${shareId}/track`, metadata);
  }

  /**
   * Generate QR code for shareable link
   */
  async generateQRCode(shareId: string, size: number = 200): Promise<Blob> {
    const response = await api.get(`/sharing/${shareId}/qr`, {
      params: { size },
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Send share notification via email
   */
  async sendShareNotification(
    shareId: string,
    recipients: string[],
    message?: string
  ): Promise<void> {
    await api.post(`/sharing/${shareId}/notify`, {
      recipients,
      message,
    });
  }

  /**
   * Get share templates
   */
  async getShareTemplates(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    permissions: SharePermissions;
  }>> {
    const response = await api.get('/sharing/templates');
    return response.data;
  }

  /**
   * Create share from template
   */
  async createFromTemplate(
    templateId: string,
    documentId: string,
    jobId: string,
    customizations?: Partial<ShareRequest>
  ): Promise<ShareableLink> {
    const response = await api.post('/sharing/from-template', {
      templateId,
      documentId,
      jobId,
      ...customizations,
    });
    return response.data;
  }

  /**
   * Bulk create shares
   */
  async bulkCreateShares(requests: ShareRequest[]): Promise<ShareableLink[]> {
    const response = await api.post('/sharing/bulk-create', { requests });
    return response.data;
  }

  /**
   * Export sharing data
   */
  async exportSharingData(format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await api.get('/sharing/export', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Get sharing activity feed
   */
  async getActivityFeed(limit: number = 50): Promise<Array<{
    id: string;
    type: 'share_created' | 'share_accessed' | 'comment_added' | 'share_expired';
    shareId: string;
    userId?: string;
    userName?: string;
    description: string;
    timestamp: string;
    metadata?: any;
  }>> {
    const response = await api.get('/sharing/activity', {
      params: { limit },
    });
    return response.data;
  }
}

export const sharingService = new SharingService();