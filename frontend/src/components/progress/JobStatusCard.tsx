import React from 'react';
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  FileText, 
  Calendar,
  User,
  MapPin,
  ExternalLink
} from 'lucide-react';
import { Job, ProcessingStatus, ProcessingStage } from '../../types/job';
import { cn, formatDate, formatDuration } from '../../utils';

interface JobStatusCardProps {
  job: Job;
  onClick?: (job: Job) => void;
  onViewDocument?: (documentId: string) => void;
  showDetails?: boolean;
  className?: string;
}

const STATUS_CONFIG = {
  [ProcessingStatus.QUEUED]: {
    icon: Clock,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    label: 'Queued',
    description: 'Waiting to start processing',
  },
  [ProcessingStatus.PROCESSING]: {
    icon: Loader2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    label: 'Processing',
    description: 'Currently being processed',
  },
  [ProcessingStatus.COMPLETED]: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    label: 'Completed',
    description: 'Processing completed successfully',
  },
  [ProcessingStatus.FAILED]: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    label: 'Failed',
    description: 'Processing failed',
  },
  [ProcessingStatus.CANCELLED]: {
    icon: AlertCircle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    label: 'Cancelled',
    description: 'Processing was cancelled',
  },
};

const STAGE_LABELS = {
  [ProcessingStage.UPLOAD]: 'Uploading',
  [ProcessingStage.OCR]: 'Text Extraction',
  [ProcessingStage.ANALYSIS]: 'Clause Analysis',
  [ProcessingStage.SUMMARIZATION]: 'Summarization',
  [ProcessingStage.RISK_ASSESSMENT]: 'Risk Assessment',
  [ProcessingStage.TRANSLATION]: 'Translation',
  [ProcessingStage.AUDIO_GENERATION]: 'Audio Generation',
  [ProcessingStage.EXPORT_GENERATION]: 'Export Generation',
};

export const JobStatusCard: React.FC<JobStatusCardProps> = ({
  job,
  onClick,
  onViewDocument,
  showDetails = true,
  className,
}) => {
  const statusConfig = STATUS_CONFIG[job.status];
  const StatusIcon = statusConfig.icon;

  // Calculate processing duration
  const getProcessingDuration = () => {
    if (!job.startedAt) return null;
    
    const endTime = job.completedAt ? new Date(job.completedAt) : new Date();
    const startTime = new Date(job.startedAt);
    const durationMs = endTime.getTime() - startTime.getTime();
    
    return Math.round(durationMs / 1000);
  };

  const processingDuration = getProcessingDuration();

  // Handle card click
  const handleCardClick = () => {
    onClick?.(job);
  };

  // Handle view document click
  const handleViewDocument = (e: React.MouseEvent) => {
    e.stopPropagation();
    onViewDocument?.(job.documentId);
  };

  return (
    <div
      className={cn(
        'bg-white rounded-lg border shadow-sm transition-all duration-200',
        'hover:shadow-md hover:border-gray-300',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={handleCardClick}
    >
      {/* Header */}
      <div className={cn('p-4 border-b', statusConfig.bgColor, statusConfig.borderColor)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <StatusIcon 
              className={cn(
                'w-6 h-6',
                statusConfig.color,
                job.status === ProcessingStatus.PROCESSING && 'animate-spin'
              )} 
            />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {`Job ${job.id.slice(0, 8)}`}
              </h3>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span className={statusConfig.color}>
                  {statusConfig.label}
                </span>
                {job.status === ProcessingStatus.PROCESSING && (
                  <>
                    <span>•</span>
                    <span>{STAGE_LABELS[job.currentStage]}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Progress indicator */}
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(job.progressPercentage)}%
            </div>
            {job.status === ProcessingStatus.PROCESSING && job.estimatedCompletion && (
              <div className="text-xs text-gray-600">
                ETA: {formatDate(job.estimatedCompletion)}
              </div>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn(
                'h-2 rounded-full transition-all duration-300',
                job.status === ProcessingStatus.FAILED ? 'bg-red-500' : 'bg-blue-500'
              )}
              style={{ width: `${Math.max(0, Math.min(100, job.progressPercentage))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left column */}
            <div className="space-y-3">
              {/* Document info */}
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <FileText className="w-4 h-4" />
                <span>Document ID: {job.documentId.slice(0, 8)}</span>
              </div>

              {/* User ID */}
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <User className="w-4 h-4" />
                <span>User: {job.userId.slice(0, 8)}</span>
              </div>
            </div>

            {/* Right column */}
            <div className="space-y-3">
              {/* Created date */}
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Calendar className="w-4 h-4" />
                <span>Created {formatDate(job.createdAt)}</span>
              </div>

              {/* Processing duration */}
              {processingDuration && (
                <div className="text-sm text-gray-600">
                  Duration: {formatDuration(processingDuration)}
                </div>
              )}

              {/* View document button */}
              {job.status === ProcessingStatus.COMPLETED && onViewDocument && (
                <button
                  onClick={handleViewDocument}
                  className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>View Document</span>
                </button>
              )}
            </div>
          </div>

          {/* Error message */}
          {job.status === ProcessingStatus.FAILED && job.errorMessage && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
                <div>
                  <h5 className="text-sm font-medium text-red-800">Error Details</h5>
                  <p className="text-sm text-red-700 mt-1">{job.errorMessage}</p>
                </div>
              </div>
            </div>
          )}

          {/* Progress message */}
          {job.status === ProcessingStatus.PROCESSING && job.progressMessage && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 animate-pulse" />
                <div>
                  <h5 className="text-sm font-medium text-blue-800">Current Activity</h5>
                  <p className="text-sm text-blue-700 mt-1">{job.progressMessage}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Footer with timestamps */}
      <div className="px-4 py-3 bg-gray-50 border-t rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div>
            Job ID: {job.id.slice(0, 8)}...
          </div>
          <div>
            {job.updatedAt && `Updated ${formatDate(job.updatedAt)}`}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobStatusCard;