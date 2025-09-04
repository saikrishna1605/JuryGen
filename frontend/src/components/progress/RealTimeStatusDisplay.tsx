import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react';
import { ProcessingStage, ProcessingStatus, Job } from '../../types/job';
import { ProgressTimeline } from './ProgressTimeline';
import { cn } from '../../lib/utils';

interface RealTimeStatusDisplayProps {
  jobId: string;
  apiBaseUrl?: string;
  authToken?: string;
  onJobComplete?: (job: Job) => void;
  onJobError?: (error: string) => void;
  className?: string;
}

interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
}

interface JobUpdate {
  id: string;
  status: ProcessingStatus;
  current_stage: ProcessingStage;
  progress_percentage: number;
  error_message?: string;
  estimated_completion?: string;
  progress_message?: string;
}

export const RealTimeStatusDisplay: React.FC<RealTimeStatusDisplayProps> = ({
  jobId,
  apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  onJobComplete,
  onJobError,
  className,
}) => {
  const [job, setJob] = useState<Job | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
  });
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000; // Start with 1 second

  // Calculate estimated time remaining
  const calculateEstimatedTime = useCallback((job: Job) => {
    if (!job.estimatedCompletion) return null;
    
    const completionTime = new Date(job.estimatedCompletion);
    const now = new Date();
    const remainingMs = completionTime.getTime() - now.getTime();
    
    return Math.max(0, Math.round(remainingMs / 1000));
  }, []);

  // Connect to SSE stream
  const connectToStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setConnectionState(prev => ({ ...prev, isConnecting: true, error: null }));

    const url = `${apiBaseUrl}/v1/streaming/jobs/${jobId}/stream`;
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      console.log('✅ Connected to job progress stream');
      setConnectionState({
        isConnected: true,
        isConnecting: false,
        error: null,
        reconnectAttempts: 0,
      });
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 Message received:', data);
        setLastUpdate(new Date());
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };

    // Handle job updates
    eventSource.addEventListener('job_update', (event) => {
      try {
        const jobData: JobUpdate = JSON.parse(event.data);
        console.log('🔄 Job update:', jobData);
        
        // Update job state
        const updatedJob = {
          ...job,
          id: jobData.id,
          status: jobData.status,
          currentStage: jobData.current_stage || job?.currentStage,
          progressPercentage: jobData.progress_percentage || job?.progressPercentage || 0,
          errorMessage: jobData.error_message,
          estimatedCompletion: jobData.estimated_completion,
          progressMessage: jobData.progress_message,
          updatedAt: new Date().toISOString(),
          documentId: job?.documentId || '',
          userId: job?.userId || '',
          createdAt: job?.createdAt || new Date().toISOString(),
        } as Job;

        setJob(updatedJob);
        setLastUpdate(new Date());

        // Handle job completion
        if (jobData.status === ProcessingStatus.COMPLETED) {
          onJobComplete?.(updatedJob);
        } else if (jobData.status === ProcessingStatus.FAILED) {
          onJobError?.(jobData.error_message || 'Job processing failed');
        }
      } catch (error) {
        console.error('Failed to parse job update:', error);
      }
    });

    // Handle system messages
    eventSource.addEventListener('system_message', (event) => {
      try {
        const messageData = JSON.parse(event.data);
        console.log('📢 System message:', messageData);
        // Could show toast notification here
      } catch (error) {
        console.error('Failed to parse system message:', error);
      }
    });

    // Handle ping/keepalive
    eventSource.addEventListener('ping', () => {
      console.log('🏓 Ping received');
      setLastUpdate(new Date());
    });

    // Handle errors
    eventSource.onerror = (event) => {
      console.error('❌ Stream error:', event);
      
      setConnectionState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: 'Connection lost',
      }));

      // Attempt reconnection
      if (connectionState.reconnectAttempts < maxReconnectAttempts) {
        const delay = reconnectDelay * Math.pow(2, connectionState.reconnectAttempts);
        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${connectionState.reconnectAttempts + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          setConnectionState(prev => ({
            ...prev,
            reconnectAttempts: prev.reconnectAttempts + 1,
          }));
          connectToStream();
        }, delay);
      } else {
        setConnectionState(prev => ({
          ...prev,
          error: 'Max reconnection attempts reached',
        }));
      }
    };

    eventSourceRef.current = eventSource;
  }, [jobId, apiBaseUrl, connectionState.reconnectAttempts, onJobComplete, onJobError]);

  // Manual reconnect
  const handleReconnect = useCallback(() => {
    setConnectionState(prev => ({ ...prev, reconnectAttempts: 0 }));
    connectToStream();
  }, [connectToStream]);

  // Initialize connection
  useEffect(() => {
    connectToStream();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectToStream]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Format last update time
  const formatLastUpdate = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    
    if (diffSeconds < 60) {
      return `${diffSeconds}s ago`;
    }
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    }
    const diffHours = Math.floor(diffMinutes / 60);
    return `${diffHours}h ago`;
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Connection Status */}
      <div className="bg-white rounded-lg border shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {connectionState.isConnected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : connectionState.isConnecting ? (
              <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            
            <div>
              <h4 className="text-sm font-medium text-gray-900">
                Real-time Updates
              </h4>
              <p className="text-xs text-gray-600">
                {connectionState.isConnected && 'Connected - receiving live updates'}
                {connectionState.isConnecting && 'Connecting to live updates...'}
                {!connectionState.isConnected && !connectionState.isConnecting && (
                  connectionState.error || 'Disconnected'
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                Updated {formatLastUpdate(lastUpdate)}
              </span>
            )}
            
            {!connectionState.isConnected && !connectionState.isConnecting && (
              <button
                onClick={handleReconnect}
                className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                disabled={connectionState.reconnectAttempts >= maxReconnectAttempts}
              >
                Reconnect
              </button>
            )}
          </div>
        </div>

        {/* Connection error */}
        {connectionState.error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-700">{connectionState.error}</span>
            </div>
            {connectionState.reconnectAttempts >= maxReconnectAttempts && (
              <p className="text-xs text-red-600 mt-1">
                Unable to establish connection. Please refresh the page or check your internet connection.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Progress Timeline */}
      {job && (
        <ProgressTimeline
          currentStage={job.currentStage}
          status={job.status}
          progress={job.progressPercentage}
          error={job.errorMessage}
          estimatedTimeRemaining={calculateEstimatedTime(job) || undefined}
        />
      )}

      {/* Progress Message */}
      {job?.progressMessage && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 animate-pulse" />
            <div>
              <h4 className="text-sm font-medium text-blue-900">Current Activity</h4>
              <p className="text-sm text-blue-700 mt-1">{job.progressMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Fallback for no job data */}
      {!job && !connectionState.isConnecting && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <div className="text-gray-400 mb-2">
            <RefreshCw className="w-8 h-8 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Waiting for Job Data
          </h3>
          <p className="text-sm text-gray-600">
            Connecting to real-time updates for job {jobId}...
          </p>
        </div>
      )}
    </div>
  );
};

export default RealTimeStatusDisplay;