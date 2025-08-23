import React, { useMemo } from 'react';
import { 
  Upload, 
  FileText, 
  Search, 
  BookOpen, 
  Shield, 
  Languages, 
  Volume2, 
  Download,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { ProcessingStage, ProcessingStatus } from '../../types/job';
import { cn } from '../../lib/utils';

interface ProgressTimelineProps {
  currentStage: ProcessingStage;
  status: ProcessingStatus;
  progress: number;
  stages?: ProcessingStage[];
  error?: string;
  estimatedTimeRemaining?: number;
  className?: string;
}

interface StageConfig {
  stage: ProcessingStage;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  estimatedDuration: number; // in seconds
}

const STAGE_CONFIGS: StageConfig[] = [
  {
    stage: ProcessingStage.UPLOAD,
    label: 'Upload',
    description: 'Uploading document to secure storage',
    icon: Upload,
    estimatedDuration: 5,
  },
  {
    stage: ProcessingStage.OCR,
    label: 'Text Extraction',
    description: 'Extracting text and analyzing document structure',
    icon: FileText,
    estimatedDuration: 30,
  },
  {
    stage: ProcessingStage.ANALYSIS,
    label: 'Clause Analysis',
    description: 'Identifying and classifying legal clauses',
    icon: Search,
    estimatedDuration: 45,
  },
  {
    stage: ProcessingStage.SUMMARIZATION,
    label: 'Summarization',
    description: 'Creating plain language summaries',
    icon: BookOpen,
    estimatedDuration: 25,
  },
  {
    stage: ProcessingStage.RISK_ASSESSMENT,
    label: 'Risk Assessment',
    description: 'Evaluating risks and generating recommendations',
    icon: Shield,
    estimatedDuration: 20,
  },
  {
    stage: ProcessingStage.TRANSLATION,
    label: 'Translation',
    description: 'Translating content to selected languages',
    icon: Languages,
    estimatedDuration: 15,
  },
  {
    stage: ProcessingStage.AUDIO_GENERATION,
    label: 'Audio Generation',
    description: 'Creating audio narration and voice synthesis',
    icon: Volume2,
    estimatedDuration: 20,
  },
  {
    stage: ProcessingStage.EXPORT_GENERATION,
    label: 'Export Generation',
    description: 'Generating downloadable files and reports',
    icon: Download,
    estimatedDuration: 10,
  },
];

export const ProgressTimeline: React.FC<ProgressTimelineProps> = ({
  currentStage,
  status,
  progress,
  stages = Object.values(ProcessingStage),
  error,
  estimatedTimeRemaining,
  className,
}) => {
  // Filter stages to only show relevant ones
  const relevantStages = useMemo(() => {
    return STAGE_CONFIGS.filter(config => stages.includes(config.stage));
  }, [stages]);

  // Get current stage index
  const currentStageIndex = useMemo(() => {
    return relevantStages.findIndex(config => config.stage === currentStage);
  }, [relevantStages, currentStage]);

  // Calculate stage status
  const getStageStatus = (stageIndex: number) => {
    if (status === ProcessingStatus.FAILED && stageIndex === currentStageIndex) {
      return 'error';
    }
    if (stageIndex < currentStageIndex) {
      return 'completed';
    }
    if (stageIndex === currentStageIndex) {
      if (status === ProcessingStatus.COMPLETED) {
        return 'completed';
      }
      return 'active';
    }
    return 'pending';
  };

  // Format time remaining
  const formatTimeRemaining = (seconds: number) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  };

  // Get status color and icon
  const getStatusDisplay = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          icon: CheckCircle,
          message: 'Processing completed successfully!',
        };
      case ProcessingStatus.FAILED:
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          icon: AlertCircle,
          message: error || 'Processing failed. Please try again.',
        };
      case ProcessingStatus.PROCESSING:
        return {
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          icon: Loader2,
          message: 'Processing your document...',
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          icon: Clock,
          message: 'Waiting to start processing...',
        };
    }
  };

  const statusDisplay = getStatusDisplay();
  const StatusIcon = statusDisplay.icon;

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className={cn('p-4 border-b', statusDisplay.bgColor, statusDisplay.borderColor)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <StatusIcon 
              className={cn(
                'w-6 h-6',
                statusDisplay.color,
                status === ProcessingStatus.PROCESSING && 'animate-spin'
              )} 
            />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Document Processing
              </h3>
              <p className={cn('text-sm', statusDisplay.color)}>
                {statusDisplay.message}
              </p>
            </div>
          </div>
          
          {/* Progress percentage */}
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(progress)}%
            </div>
            {estimatedTimeRemaining && estimatedTimeRemaining > 0 && status === ProcessingStatus.PROCESSING && (
              <div className="text-sm text-gray-600">
                ~{formatTimeRemaining(estimatedTimeRemaining)} remaining
              </div>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn(
                'h-2 rounded-full transition-all duration-300',
                status === ProcessingStatus.FAILED ? 'bg-red-500' : 'bg-blue-500'
              )}
              style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="p-4">
        <div className="space-y-4">
          {relevantStages.map((stageConfig, index) => {
            const stageStatus = getStageStatus(index);
            const IconComponent = stageConfig.icon;
            
            return (
              <div key={stageConfig.stage} className="flex items-start space-x-4">
                {/* Timeline connector */}
                <div className="flex flex-col items-center">
                  {/* Stage icon */}
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300',
                      stageStatus === 'completed' && 'bg-green-500 border-green-500 text-white',
                      stageStatus === 'active' && 'bg-blue-500 border-blue-500 text-white',
                      stageStatus === 'error' && 'bg-red-500 border-red-500 text-white',
                      stageStatus === 'pending' && 'bg-gray-100 border-gray-300 text-gray-400'
                    )}
                  >
                    {stageStatus === 'completed' ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : stageStatus === 'active' && status === ProcessingStatus.PROCESSING ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : stageStatus === 'error' ? (
                      <AlertCircle className="w-5 h-5" />
                    ) : (
                      <IconComponent className="w-5 h-5" />
                    )}
                  </div>
                  
                  {/* Connector line */}
                  {index < relevantStages.length - 1 && (
                    <div
                      className={cn(
                        'w-0.5 h-8 mt-2 transition-all duration-300',
                        stageStatus === 'completed' ? 'bg-green-300' : 'bg-gray-200'
                      )}
                    />
                  )}
                </div>

                {/* Stage content */}
                <div className="flex-1 min-w-0 pb-4">
                  <div className="flex items-center justify-between">
                    <h4
                      className={cn(
                        'text-sm font-medium transition-colors duration-300',
                        stageStatus === 'completed' && 'text-green-700',
                        stageStatus === 'active' && 'text-blue-700',
                        stageStatus === 'error' && 'text-red-700',
                        stageStatus === 'pending' && 'text-gray-500'
                      )}
                    >
                      {stageConfig.label}
                    </h4>
                    
                    {/* Stage status indicator */}
                    <div className="flex items-center space-x-2">
                      {stageStatus === 'active' && status === ProcessingStatus.PROCESSING && (
                        <div className="flex items-center space-x-1 text-xs text-blue-600">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          <span>Processing...</span>
                        </div>
                      )}
                      {stageStatus === 'completed' && (
                        <div className="flex items-center space-x-1 text-xs text-green-600">
                          <CheckCircle className="w-3 h-3" />
                          <span>Complete</span>
                        </div>
                      )}
                      {stageStatus === 'error' && (
                        <div className="flex items-center space-x-1 text-xs text-red-600">
                          <AlertCircle className="w-3 h-3" />
                          <span>Failed</span>
                        </div>
                      )}
                      {stageStatus === 'pending' && (
                        <div className="text-xs text-gray-400">
                          Pending
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <p
                    className={cn(
                      'text-sm mt-1 transition-colors duration-300',
                      stageStatus === 'completed' && 'text-green-600',
                      stageStatus === 'active' && 'text-blue-600',
                      stageStatus === 'error' && 'text-red-600',
                      stageStatus === 'pending' && 'text-gray-400'
                    )}
                  >
                    {stageConfig.description}
                  </p>

                  {/* Stage-specific progress for active stage */}
                  {stageStatus === 'active' && status === ProcessingStatus.PROCESSING && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div
                          className="h-1 bg-blue-500 rounded-full transition-all duration-300"
                          style={{ 
                            width: `${Math.max(0, Math.min(100, (progress - (index * (100 / relevantStages.length)))))}%` 
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer with additional info */}
      {(status === ProcessingStatus.PROCESSING || status === ProcessingStatus.COMPLETED) && (
        <div className="px-4 py-3 bg-gray-50 border-t rounded-b-lg">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              Stage {currentStageIndex + 1} of {relevantStages.length}
            </div>
            {status === ProcessingStatus.COMPLETED && (
              <div className="text-green-600 font-medium">
                Processing completed successfully!
              </div>
            )}
            {status === ProcessingStatus.PROCESSING && estimatedTimeRemaining && (
              <div>
                Estimated completion: {formatTimeRemaining(estimatedTimeRemaining)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressTimeline;