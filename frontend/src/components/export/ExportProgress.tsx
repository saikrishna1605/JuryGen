import React, { useEffect, useState } from 'react';
import {
  FileText,
  File,
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Clock,
} from 'lucide-react';
import { exportService, ExportResponse } from '../../services/exportService';
import { useAriaAnnouncements } from '../../hooks/useAriaAnnouncements';
import { ProgressAnnouncement } from '../accessibility/ScreenReaderUtils';
import { cn } from '../../utils';

interface ExportProgressProps {
  exportId: string;
  onComplete?: (exportData: ExportResponse) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface ProgressStage {
  name: string;
  description: string;
  completed: boolean;
  current: boolean;
}

export const ExportProgress: React.FC<ExportProgressProps> = ({
  exportId,
  onComplete,
  onError,
  className,
}) => {
  const [exportData, setExportData] = useState<ExportResponse | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('');
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { announceSuccess, announceError } = useAriaAnnouncements();

  // Define export stages
  const stages: ProgressStage[] = [
    { name: 'Preparing', description: 'Initializing export process', completed: false, current: false },
    { name: 'Processing', description: 'Analyzing document content', completed: false, current: false },
    { name: 'Formatting', description: 'Applying formatting and styles', completed: false, current: false },
    { name: 'Generating', description: 'Creating export file', completed: false, current: false },
    { name: 'Finalizing', description: 'Preparing download', completed: false, current: false },
  ];

  const [progressStages, setProgressStages] = useState(stages);

  // Poll for export status
  useEffect(() => {
    if (!exportId) return;

    const pollStatus = async () => {
      try {
        const status = await exportService.getExportStatus(exportId);
        setExportData(status);

        if (status.status === 'ready') {
          setProgress(100);
          setProgressStages(prev => prev.map(stage => ({ ...stage, completed: true, current: false })));
          announceSuccess(`Export completed: ${status.filename}`);
          onComplete?.(status);
        } else if (status.status === 'failed') {
          setError('Export generation failed');
          announceError('Export generation failed');
          onError?.('Export generation failed');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to get export status';
        setError(errorMessage);
        announceError(errorMessage);
        onError?.(errorMessage);
      }
    };

    // Initial status check
    pollStatus();

    // Set up polling interval
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [exportId, onComplete, onError, announceSuccess, announceError]);

  // Set up SSE for real-time progress updates
  useEffect(() => {
    if (!exportId) return;

    const eventSource = exportService.getExportProgressStream(exportId);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.progress !== undefined) {
          setProgress(data.progress);
        }
        
        if (data.stage) {
          setCurrentStage(data.stage);
          
          // Update stage progress
          setProgressStages(prev => prev.map((stage, index) => {
            const stageProgress = Math.floor((data.progress / 100) * prev.length);
            return {
              ...stage,
              completed: index < stageProgress,
              current: index === stageProgress,
            };
          }));
        }
        
        if (data.estimatedTimeRemaining) {
          setEstimatedTime(data.estimatedTimeRemaining);
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [exportId]);

  const getFormatIcon = (format?: string) => {
    switch (format) {
      case 'pdf':
        return <FileText className="w-6 h-6" />;
      case 'docx':
        return <File className="w-6 h-6" />;
      case 'csv':
        return <FileSpreadsheet className="w-6 h-6" />;
      case 'json':
        return <File className="w-6 h-6" />;
      default:
        return <File className="w-6 h-6" />;
    }
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const handleDownload = () => {
    if (exportData?.downloadUrl) {
      const link = document.createElement('a');
      link.href = exportData.downloadUrl;
      link.download = exportData.filename;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  if (error) {
    return (
      <div className={cn('p-4 border border-red-200 rounded-lg bg-red-50', className)}>
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="font-medium text-red-900">Export Failed</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!exportData) {
    return (
      <div className={cn('p-4 border border-gray-200 rounded-lg', className)}>
        <div className="flex items-center space-x-3">
          <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
          <div>
            <h3 className="font-medium text-gray-900">Initializing Export</h3>
            <p className="text-sm text-gray-600">Setting up export process...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('p-4 border border-gray-200 rounded-lg bg-white', className)}>
      {/* Progress Announcement for Screen Readers */}
      <ProgressAnnouncement
        current={progress}
        total={100}
        label="Export generation"
        announceInterval={25}
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getFormatIcon(exportData.filename.split('.').pop())}
          <div>
            <h3 className="font-medium text-gray-900">{exportData.filename}</h3>
            <p className="text-sm text-gray-600">
              {exportData.status === 'ready' ? 'Export completed' : 'Generating export...'}
            </p>
          </div>
        </div>

        {exportData.status === 'ready' && (
          <button
            onClick={handleDownload}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            aria-label={`Download ${exportData.filename}`}
          >
            <Download className="w-4 h-4" />
            <span>Download</span>
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>{progress}% complete</span>
          {estimatedTime && exportData.status !== 'ready' && (
            <span>~{formatTime(estimatedTime)} remaining</span>
          )}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={cn(
              'h-2 rounded-full transition-all duration-300',
              exportData.status === 'ready' ? 'bg-green-500' : 'bg-blue-500'
            )}
            style={{ width: `${progress}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Export progress: ${progress}% complete`}
          />
        </div>
      </div>

      {/* Stage Progress */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Progress Stages</h4>
        <div className="space-y-2">
          {progressStages.map((stage) => (
            <div key={stage.name} className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                {stage.completed ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : stage.current ? (
                  <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
                ) : (
                  <Clock className="w-4 h-4 text-gray-300" />
                )}
              </div>
              <div className="flex-1">
                <div className={cn(
                  'text-sm',
                  stage.completed ? 'text-green-700 font-medium' :
                  stage.current ? 'text-blue-700 font-medium' :
                  'text-gray-500'
                )}>
                  {stage.name}
                </div>
                <div className="text-xs text-gray-500">{stage.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current Stage Info */}
      {currentStage && exportData.status !== 'ready' && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
            <span className="text-sm text-blue-800">
              Current stage: {currentStage}
            </span>
          </div>
        </div>
      )}

      {/* File Info */}
      {exportData.size && (
        <div className="mt-4 text-xs text-gray-500">
          File size: {(exportData.size / 1024 / 1024).toFixed(2)} MB
        </div>
      )}
    </div>
  );
};

export default ExportProgress;