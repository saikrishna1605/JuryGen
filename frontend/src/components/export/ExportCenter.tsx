import React, { useState, useEffect } from 'react';
import {
  Download,
  FileText,
  FileSpreadsheet,
  File,
  Clock,
  CheckCircle,
  AlertCircle,
  X,
  RefreshCw,
} from 'lucide-react';
import { exportService, ExportOptions } from '../../services/exportService';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { AccessibleModal } from '../accessibility';
import { cn } from '../../utils';

interface ExportCenterProps {
  documentId: string;
  jobId: string;
  className?: string;
}

interface ExportJob {
  id: string;
  format: string;
  status: 'generating' | 'ready' | 'failed';
  progress: number;
  filename: string;
  downloadUrl?: string;
  error?: string;
  createdAt: string;
}

export const ExportCenter: React.FC<ExportCenterProps> = ({
  documentId,
  jobId,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<'pdf' | 'docx' | 'csv' | 'json'>('pdf');
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'pdf',
    includeAnnotations: true,
    includeRiskHighlights: true,
    includeComments: true,
    includeMetadata: true,
    template: 'detailed',
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const { announceSuccess, announceError, announceStatus } = useAriaAnnouncements();

  // Poll for export status updates
  useEffect(() => {
    if (exportJobs.length === 0) return;

    const interval = setInterval(async () => {
      const updatedJobs = await Promise.all(
        exportJobs.map(async (job) => {
          if (job.status === 'generating') {
            try {
              const status = await exportService.getExportStatus(job.id);
              return {
                ...job,
                status: status.status,
                progress: status.status === 'ready' ? 100 : job.progress,
                downloadUrl: status.downloadUrl,
              };
            } catch (error) {
              return {
                ...job,
                status: 'failed' as const,
                error: 'Failed to get export status',
              };
            }
          }
          return job;
        })
      );

      setExportJobs(updatedJobs);

      // Announce completed exports
      updatedJobs.forEach((job, index) => {
        const oldJob = exportJobs[index];
        if (oldJob?.status === 'generating' && job.status === 'ready') {
          announceSuccess(`${job.format.toUpperCase()} export completed: ${job.filename}`);
        } else if (oldJob?.status === 'generating' && job.status === 'failed') {
          announceError(`${job.format.toUpperCase()} export failed`);
        }
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [exportJobs, announceSuccess, announceError]);

  const handleExport = async () => {
    setIsGenerating(true);
    announceStatus('Starting export generation', selectedFormat.toUpperCase());

    try {
      const options = { ...exportOptions, format: selectedFormat };
      const response = await exportService.requestExport({
        documentId,
        jobId,
        options,
      });

      const newJob: ExportJob = {
        id: response.exportId,
        format: selectedFormat,
        status: response.status,
        progress: 0,
        filename: response.filename,
        downloadUrl: response.downloadUrl,
        createdAt: new Date().toISOString(),
      };

      setExportJobs(prev => [newJob, ...prev]);
      announceSuccess(`${selectedFormat.toUpperCase()} export started`);
    } catch (error) {
      announceError(`Failed to start ${selectedFormat.toUpperCase()} export`);
      console.error('Export error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (job: ExportJob) => {
    if (!job.downloadUrl) return;

    try {
      announceStatus('Starting download', job.filename);
      
      // Create download link
      const link = document.createElement('a');
      link.href = job.downloadUrl;
      link.download = job.filename;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      announceSuccess(`Downloaded ${job.filename}`);
    } catch (error) {
      announceError(`Failed to download ${job.filename}`);
      console.error('Download error:', error);
    }
  };

  const removeJob = (jobId: string) => {
    setExportJobs(prev => prev.filter(job => job.id !== jobId));
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <FileText className="w-5 h-5" />;
      case 'docx':
        return <File className="w-5 h-5" />;
      case 'csv':
        return <FileSpreadsheet className="w-5 h-5" />;
      case 'json':
        return <File className="w-5 h-5" />;
      default:
        return <File className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'generating':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="w-4 h-4" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4" />;
      case 'generating':
        return <RefreshCw className="w-4 h-4 animate-spin" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors',
          className
        )}
        aria-label="Open export center"
      >
        <Download className="w-4 h-4" />
        <span>Export</span>
      </button>

      <AccessibleModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Export Center"
        description="Generate and download document exports in various formats"
        size="lg"
      >
        <div className="space-y-6">
          {/* Export Format Selection */}
          <div>
            <h3 className="text-lg font-medium mb-4">Export Format</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { format: 'pdf', label: 'PDF', description: 'Highlighted document with annotations' },
                { format: 'docx', label: 'Word Document', description: 'Editable document with comments' },
                { format: 'csv', label: 'CSV Data', description: 'Clause analysis data' },
                { format: 'json', label: 'JSON Data', description: 'Complete analysis data' },
              ].map(({ format, label, description }) => (
                <button
                  key={format}
                  onClick={() => setSelectedFormat(format as any)}
                  className={cn(
                    'p-4 border rounded-lg text-left transition-colors',
                    selectedFormat === format
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                >
                  <div className="flex items-center space-x-3">
                    {getFormatIcon(format)}
                    <div>
                      <div className="font-medium">{label}</div>
                      <div className="text-sm text-gray-600">{description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Export Options */}
          <div>
            <h3 className="text-lg font-medium mb-4">Export Options</h3>
            <div className="space-y-3">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeAnnotations}
                  onChange={(e) =>
                    setExportOptions(prev => ({ ...prev, includeAnnotations: e.target.checked }))
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Include annotations and highlights</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeRiskHighlights}
                  onChange={(e) =>
                    setExportOptions(prev => ({ ...prev, includeRiskHighlights: e.target.checked }))
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Include risk highlights</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeComments}
                  onChange={(e) =>
                    setExportOptions(prev => ({ ...prev, includeComments: e.target.checked }))
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Include comments and suggestions</span>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeMetadata}
                  onChange={(e) =>
                    setExportOptions(prev => ({ ...prev, includeMetadata: e.target.checked }))
                  }
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Include metadata and analysis details</span>
              </label>
            </div>

            {/* Template Selection */}
            <div className="mt-4">
              <label className="block text-sm font-medium mb-2">Template</label>
              <select
                value={exportOptions.template}
                onChange={(e) =>
                  setExportOptions(prev => ({ ...prev, template: e.target.value as any }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="standard">Standard</option>
                <option value="detailed">Detailed</option>
                <option value="summary">Summary</option>
              </select>
            </div>
          </div>

          {/* Generate Button */}
          <div className="flex justify-end">
            <button
              onClick={handleExport}
              disabled={isGenerating}
              className={cn(
                'flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-md',
                'hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              )}
            >
              {isGenerating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              <span>{isGenerating ? 'Generating...' : 'Generate Export'}</span>
            </button>
          </div>

          {/* Export Jobs */}
          {exportJobs.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-4">Export History</h3>
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {exportJobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      {getFormatIcon(job.format)}
                      <div>
                        <div className="font-medium">{job.filename}</div>
                        <div className={cn('text-sm flex items-center space-x-1', getStatusColor(job.status))}>
                          {getStatusIcon(job.status)}
                          <span>
                            {job.status === 'generating' && `${job.progress}% complete`}
                            {job.status === 'ready' && 'Ready for download'}
                            {job.status === 'failed' && (job.error || 'Export failed')}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {job.status === 'ready' && (
                        <button
                          onClick={() => handleDownload(job)}
                          className="p-2 text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
                          aria-label={`Download ${job.filename}`}
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => removeJob(job.id)}
                        className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded-md"
                        aria-label={`Remove ${job.filename} from list`}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </AccessibleModal>
    </>
  );
};

export default ExportCenter;