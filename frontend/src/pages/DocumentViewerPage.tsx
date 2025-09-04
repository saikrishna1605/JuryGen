import React, { useState, useCallback, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Share2, Eye, EyeOff } from 'lucide-react';
import { PDFViewer, ClauseHeatmap, ClauseDetailsPanel } from '../components/pdf';
import { UserRole } from '../types/document';
import { useDocument } from '../hooks/useDocument';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';

interface ViewerSettings {
  showAnnotations: boolean;
  showHeatmap: boolean;
  showClauseDetails: boolean;
  userRole: UserRole | undefined;
}

export const DocumentViewerPage: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();

  
  // Document data
  const { document, isLoading, error } = useDocument(documentId);
  
  // Viewer state
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [settings, setSettings] = useState<ViewerSettings>({
    showAnnotations: true,
    showHeatmap: true,
    showClauseDetails: true,
    userRole: document?.userRole,
  });

  // Update user role when document loads
  useEffect(() => {
    if (document?.userRole) {
      setSettings(prev => ({ ...prev, userRole: document.userRole }));
    }
  }, [document]);

  // Get selected clause
  const selectedClause = selectedClauseId 
    ? document?.clauses.find(clause => clause.id === selectedClauseId) || null
    : null;

  // Handle clause selection
  const handleClauseSelect = useCallback((clauseId: string) => {
    setSelectedClauseId(clauseId);
  }, []);

  // Handle page navigation
  const handlePageSelect = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  // Handle settings change
  const handleSettingsChange = useCallback((key: keyof ViewerSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  // Handle back navigation
  const handleBack = useCallback(() => {
    navigate('/documents');
  }, [navigate]);

  // Handle download
  const handleDownload = useCallback(() => {
    if (document?.exports.highlightedPdf) {
      window.open(document.exports.highlightedPdf, '_blank');
    }
  }, [document]);

  // Handle share
  const handleShare = useCallback(async () => {
    if (navigator.share && document) {
      try {
        await navigator.share({
          title: document.filename,
          text: `Legal document analysis: ${document.filename}`,
          url: window.location.href,
        });
      } catch (error) {
        // Fallback to copying URL
        navigator.clipboard.writeText(window.location.href);
      }
    } else {
      // Fallback to copying URL
      navigator.clipboard.writeText(window.location.href);
    }
  }, [document]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Document</h2>
          <p className="text-gray-600">Please wait while we load your document...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !document) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Document Not Found</h2>
          <p className="text-gray-600 mb-4">
            {error || 'The document you are looking for could not be found.'}
          </p>
          <button
            onClick={handleBack}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            Back to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left side */}
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                title="Back to documents"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900 truncate max-w-md">
                  {document.filename}
                </h1>
                <p className="text-sm text-gray-600">
                  {document.clauses.length} clauses analyzed
                </p>
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center space-x-2">
              {/* View toggles */}
              <div className="flex items-center space-x-1 bg-gray-100 rounded-md p-1">
                <button
                  onClick={() => handleSettingsChange('showAnnotations', !settings.showAnnotations)}
                  className={cn(
                    'p-2 rounded text-sm font-medium transition-colors',
                    settings.showAnnotations
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  )}
                  title="Toggle annotations"
                >
                  {settings.showAnnotations ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
              </div>

              {/* User role selector */}
              <select
                value={settings.userRole || ''}
                onChange={(e) => handleSettingsChange('userRole', e.target.value as UserRole)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Role</option>
                {Object.values(UserRole).map(role => (
                  <option key={role} value={role}>
                    {role.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>

              {/* Action buttons */}
              <button
                onClick={handleDownload}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                title="Download PDF"
                disabled={!document.exports.highlightedPdf}
              >
                <Download className="w-5 h-5" />
              </button>
              
              <button
                onClick={handleShare}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                title="Share document"
              >
                <Share2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* PDF Viewer */}
          <div className={cn(
            'col-span-12',
            settings.showHeatmap && settings.showClauseDetails ? 'lg:col-span-6' :
            settings.showHeatmap || settings.showClauseDetails ? 'lg:col-span-8' :
            'lg:col-span-12'
          )}>
            <PDFViewer
              fileUrl={`/api/v1/documents/${document.id}/download`}
              clauses={document.clauses}
              selectedClauseId={selectedClauseId || undefined}
              onClauseSelect={handleClauseSelect}
              showAnnotations={settings.showAnnotations}
              className="h-[calc(100vh-12rem)]"
            />
          </div>

          {/* Side panels */}
          <div className={cn(
            'col-span-12 space-y-6',
            settings.showHeatmap && settings.showClauseDetails ? 'lg:col-span-6' :
            settings.showHeatmap || settings.showClauseDetails ? 'lg:col-span-4' :
            'hidden'
          )}>
            {/* Heatmap */}
            {settings.showHeatmap && (
              <ClauseHeatmap
                clauses={document.clauses}
                totalPages={document.pages || 1}
                currentPage={currentPage}
                selectedClauseId={selectedClauseId || undefined}
                onPageSelect={handlePageSelect}
                onClauseSelect={handleClauseSelect}
              />
            )}

            {/* Clause details */}
            {settings.showClauseDetails && (
              <ClauseDetailsPanel
                clause={selectedClause}
                userRole={settings.userRole}
                onNavigateToClause={handleClauseSelect}
                onCopyText={(text) => {
                  navigator.clipboard.writeText(text);
                  // Could show a toast notification here
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewerPage;