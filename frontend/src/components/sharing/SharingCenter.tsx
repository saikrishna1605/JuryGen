import React, { useState, useEffect } from 'react';
import {
  Share2,
  Link,
  Copy,
  Mail,
  QrCode,
  Settings,
  Eye,
  MessageSquare,
  Download,
  Users,
  Calendar,
  Lock,
  Globe,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import {
  sharingService,
  ShareableLink,
  SharePermissions,
  ShareRequest,
} from '../../services/sharingService';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { AccessibleModal, AccessibleForm, FormField } from '../accessibility';
import { cn } from '../../lib/utils';

interface SharingCenterProps {
  documentId: string;
  jobId: string;
  documentTitle: string;
  className?: string;
}

export const SharingCenter: React.FC<SharingCenterProps> = ({
  documentId,
  jobId,
  documentTitle,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [shareableLinks, setShareableLinks] = useState<ShareableLink[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [shareTitle, setShareTitle] = useState(documentTitle);
  const [shareDescription, setShareDescription] = useState('');
  const [permissions, setPermissions] = useState<SharePermissions>({
    canView: true,
    canComment: false,
    canDownload: false,
    canShare: false,
    requiresAuth: false,
  });
  const [expirationDate, setExpirationDate] = useState('');
  const [password, setPassword] = useState('');
  const [allowedUsers, setAllowedUsers] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');

  const { announceSuccess, announceError } = useAriaAnnouncements();

  // Load existing shareable links
  useEffect(() => {
    if (isOpen) {
      loadShareableLinks();
    }
  }, [isOpen]);

  const loadShareableLinks = async () => {
    try {
      const links = await sharingService.getUserShareableLinks();
      const documentLinks = links.filter(link => 
        link.documentId === documentId && link.jobId === jobId
      );
      setShareableLinks(documentLinks);
    } catch (error) {
      announceError('Failed to load shareable links');
      console.error('Error loading shareable links:', error);
    }
  };

  const handleCreateShare = async () => {
    setIsCreating(true);

    try {
      const shareRequest: ShareRequest = {
        documentId,
        jobId,
        title: shareTitle,
        description: shareDescription || undefined,
        permissions: {
          ...permissions,
          allowedUsers: allowedUsers ? allowedUsers.split(',').map(email => email.trim()) : undefined,
        },
        expiresAt: expirationDate || undefined,
        password: password || undefined,
      };

      const newShare = await sharingService.createShareableLink(shareRequest);
      setShareableLinks(prev => [newShare, ...prev]);
      
      // Reset form
      setShowCreateForm(false);
      setShareTitle(documentTitle);
      setShareDescription('');
      setPermissions({
        canView: true,
        canComment: false,
        canDownload: false,
        canShare: false,
        requiresAuth: false,
      });
      setExpirationDate('');
      setPassword('');
      setAllowedUsers('');

      announceSuccess('Shareable link created successfully');
    } catch (error) {
      announceError('Failed to create shareable link');
      console.error('Error creating share:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleCopyLink = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      announceSuccess('Link copied to clipboard');
    } catch (error) {
      announceError('Failed to copy link');
      console.error('Copy error:', error);
    }
  };

  const handleSendEmail = async (shareId: string) => {
    try {
      const recipients = prompt('Enter email addresses (comma-separated):');
      if (!recipients) return;

      const message = prompt('Optional message:');
      
      await sharingService.sendShareNotification(
        shareId,
        recipients.split(',').map(email => email.trim()),
        message || undefined
      );

      announceSuccess('Share notification sent');
    } catch (error) {
      announceError('Failed to send notification');
      console.error('Email error:', error);
    }
  };

  const handleGenerateQR = async (shareId: string) => {
    try {
      const qrBlob = await sharingService.generateQRCode(shareId);
      const url = URL.createObjectURL(qrBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `qr-code-${shareId}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      announceSuccess('QR code downloaded');
    } catch (error) {
      announceError('Failed to generate QR code');
      console.error('QR code error:', error);
    }
  };

  const handleDeactivateShare = async (shareId: string) => {
    if (!confirm('Are you sure you want to deactivate this share? This action cannot be undone.')) {
      return;
    }

    try {
      await sharingService.deactivateShareableLink(shareId);
      setShareableLinks(prev => prev.filter(link => link.id !== shareId));
      announceSuccess('Share deactivated');
    } catch (error) {
      announceError('Failed to deactivate share');
      console.error('Deactivate error:', error);
    }
  };

  const getPermissionSummary = (perms: SharePermissions): string => {
    const permissions = [];
    if (perms.canView) permissions.push('View');
    if (perms.canComment) permissions.push('Comment');
    if (perms.canDownload) permissions.push('Download');
    if (perms.canShare) permissions.push('Share');
    return permissions.join(', ') || 'No permissions';
  };

  const getExpirationStatus = (expiresAt?: string) => {
    if (!expiresAt) return { status: 'never', text: 'Never expires', color: 'text-green-600' };
    
    const expiration = new Date(expiresAt);
    const now = new Date();
    
    if (expiration < now) {
      return { status: 'expired', text: 'Expired', color: 'text-red-600' };
    }
    
    const daysUntilExpiration = Math.ceil((expiration.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysUntilExpiration <= 1) {
      return { status: 'expiring', text: 'Expires today', color: 'text-orange-600' };
    } else if (daysUntilExpiration <= 7) {
      return { status: 'expiring', text: `Expires in ${daysUntilExpiration} days`, color: 'text-orange-600' };
    } else {
      return { status: 'active', text: `Expires in ${daysUntilExpiration} days`, color: 'text-gray-600' };
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700',
          'focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors',
          className
        )}
        aria-label="Open sharing center"
      >
        <Share2 className="w-4 h-4" />
        <span>Share</span>
      </button>

      <AccessibleModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Sharing Center"
        description="Create and manage shareable links for your document analysis"
        size="lg"
      >
        <div className="space-y-6">
          {/* Create New Share Button */}
          {!showCreateForm && (
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Shareable Links</h3>
              <button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
              >
                <Link className="w-4 h-4" />
                <span>Create New Link</span>
              </button>
            </div>
          )}

          {/* Create Share Form */}
          {showCreateForm && (
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <h4 className="font-medium">Create Shareable Link</h4>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded-md p-1"
                >
                  ×
                </button>
              </div>

              <AccessibleForm
                onSubmit={(e) => {
                  e.preventDefault();
                  handleCreateShare();
                }}
                className="space-y-4"
              >
                <FormField
                  id="share-title"
                  label="Title"
                  value={shareTitle}
                  onChange={setShareTitle}
                  required
                  placeholder="Enter a title for this share"
                />

                <FormField
                  id="share-description"
                  label="Description"
                  type="textarea"
                  value={shareDescription}
                  onChange={setShareDescription}
                  placeholder="Optional description"
                  rows={3}
                />

                {/* Permissions */}
                <div>
                  <label className="block text-sm font-medium mb-3">Permissions</label>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={permissions.canView}
                        onChange={(e) => setPermissions(prev => ({ ...prev, canView: e.target.checked }))}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <span className="font-medium">View</span>
                        <div className="text-sm text-gray-600">Allow viewers to see the document analysis</div>
                      </div>
                    </label>

                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={permissions.canComment}
                        onChange={(e) => setPermissions(prev => ({ ...prev, canComment: e.target.checked }))}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <span className="font-medium">Comment</span>
                        <div className="text-sm text-gray-600">Allow viewers to add comments and feedback</div>
                      </div>
                    </label>

                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={permissions.canDownload}
                        onChange={(e) => setPermissions(prev => ({ ...prev, canDownload: e.target.checked }))}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <span className="font-medium">Download</span>
                        <div className="text-sm text-gray-600">Allow viewers to download exports</div>
                      </div>
                    </label>

                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={permissions.canShare}
                        onChange={(e) => setPermissions(prev => ({ ...prev, canShare: e.target.checked }))}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <span className="font-medium">Share</span>
                        <div className="text-sm text-gray-600">Allow viewers to create their own shares</div>
                      </div>
                    </label>

                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={permissions.requiresAuth}
                        onChange={(e) => setPermissions(prev => ({ ...prev, requiresAuth: e.target.checked }))}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <span className="font-medium">Require Authentication</span>
                        <div className="text-sm text-gray-600">Viewers must sign in to access</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Advanced Options */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    id="expiration-date"
                    label="Expiration Date (Optional)"
                    type="date"
                    value={expirationDate}
                    onChange={setExpirationDate}
                    helperText="Leave empty for no expiration"
                  />

                  <FormField
                    id="password"
                    label="Password (Optional)"
                    type="password"
                    value={password}
                    onChange={setPassword}
                    placeholder="Optional password protection"
                  />
                </div>

                <FormField
                  id="allowed-users"
                  label="Allowed Users (Optional)"
                  value={allowedUsers}
                  onChange={setAllowedUsers}
                  placeholder="email1@example.com, email2@example.com"
                  helperText="Comma-separated email addresses. Leave empty to allow anyone with the link."
                />

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreating}
                    className={cn(
                      'flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md',
                      'hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2',
                      'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
                    )}
                  >
                    {isCreating ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <Link className="w-4 h-4" />
                        <span>Create Link</span>
                      </>
                    )}
                  </button>
                </div>
              </AccessibleForm>
            </div>
          )}

          {/* Existing Shares */}
          <div className="space-y-4">
            {shareableLinks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No shareable links created yet
              </div>
            ) : (
              shareableLinks.map((share) => {
                const expiration = getExpirationStatus(share.expiresAt);
                
                return (
                  <div key={share.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{share.title}</h4>
                        {share.description && (
                          <p className="text-sm text-gray-600 mt-1">{share.description}</p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                          <div className="flex items-center space-x-1">
                            <Eye className="w-4 h-4" />
                            <span>{share.accessCount} views</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Calendar className="w-4 h-4" />
                            <span className={expiration.color}>{expiration.text}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            {share.permissions.requiresAuth ? (
                              <Lock className="w-4 h-4" />
                            ) : (
                              <Globe className="w-4 h-4" />
                            )}
                            <span>{getPermissionSummary(share.permissions)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {share.isActive ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : (
                          <AlertCircle className="w-5 h-5 text-red-500" />
                        )}
                      </div>
                    </div>

                    {/* Share URL */}
                    <div className="bg-gray-50 rounded-md p-3 mb-3">
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={share.shortUrl}
                          readOnly
                          className="flex-1 bg-transparent border-none focus:outline-none text-sm"
                        />
                        <button
                          onClick={() => handleCopyLink(share.shortUrl)}
                          className="p-2 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500 rounded-md"
                          aria-label="Copy link"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleSendEmail(share.id)}
                          className="flex items-center space-x-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
                        >
                          <Mail className="w-4 h-4" />
                          <span>Email</span>
                        </button>

                        <button
                          onClick={() => handleGenerateQR(share.id)}
                          className="flex items-center space-x-1 px-3 py-1 text-sm text-purple-600 hover:text-purple-800 focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-md"
                        >
                          <QrCode className="w-4 h-4" />
                          <span>QR Code</span>
                        </button>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {/* TODO: Open analytics modal */}}
                          className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded-md"
                        >
                          <Settings className="w-4 h-4" />
                          <span>Analytics</span>
                        </button>

                        <button
                          onClick={() => handleDeactivateShare(share.id)}
                          className="px-3 py-1 text-sm text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded-md"
                        >
                          Deactivate
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </AccessibleModal>
    </>
  );
};

export default SharingCenter;