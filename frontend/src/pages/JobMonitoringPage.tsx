import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Download, Share2 } from 'lucide-react';
import { RealTimeStatusDisplay, JobStatusCard } from '../components/progress';
import { Job, ProcessingStatus } from '../types/job';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';
import { cn } from '../utils';

interface JobMonitoringPageProps {
  // Optional props for embedding in other pages
  embedded?: boolean;
  onJobComplete?: (job: Job) => void;
  onJobError?: (error: string) => void;
}

export const JobMonitoringPage: React.FC<JobMonitoringPageProps> = ({
  embedded = false,
  onJobComplete,
  onJobError,
}) => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [relatedJobs, setRelatedJobs] = useState<Job[]>([]);

  // Fetch job details
  const fetchJob = useCallback(async () => {
    if (!jobId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await api.get(`/jobs/${jobId}`);
      
      if (response.data.success) {
        setJob(response.data.data);
        
        // Fetch related jobs for the same document
        if (response.data.data.documentId) {
          const relatedResponse = await api.get(`/jobs`, {
            params: {
              documentId: response.data.data.documentId,
              limit: 5,
            },
          });
          
          if (relatedResponse.data.success) {
            // Filter out current job
            const related = relatedResponse.data.data.filter(
              (j: Job) => j.id !== jobId
            );
            setRelatedJobs(related);
          }
        }
      } else {
        setError(response.data.message || 'Failed to fetch job');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Failed to fetch job');
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  // Handle job completion
  const handleJobComplete = useCallback((completedJob: Job) => {
    setJob(completedJob);
    onJobComplete?.(completedJob);
  }, [onJobComplete]);

  // Handle job error
  const handleJobError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    onJobError?.(errorMessage);
  }, [onJobError]);

  // Handle back navigation
  const handleBack = useCallback(() => {
    if (embedded) return;
    navigate('/jobs');
  }, [navigate, embedded]);

  // Handle job cancellation
  const handleCancelJob = useCallback(async () => {
    if (!job || job.status !== ProcessingStatus.PROCESSING) return;

    try {
      await api.post(`/jobs/${job.id}/cancel`);
      await fetchJob(); // Refresh job data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to cancel job');
    }
  }, [job, fetchJob]);

  // Handle job retry
  const handleRetryJob = useCallback(async () => {
    if (!job || job.status !== ProcessingStatus.FAILED) return;

    try {
      await api.post(`/jobs/${job.id}/retry`);
      await fetchJob(); // Refresh job data
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to retry job');
    }
  }, [job, fetchJob]);

  // Handle view document
  const handleViewDocument = useCallback((documentId: string) => {
    navigate(`/documents/${documentId}`);
  }, [navigate]);

  // Handle download results
  const handleDownloadResults = useCallback(async () => {
    if (!job || job.status !== ProcessingStatus.COMPLETED) return;

    try {
      const response = await api.get(`/jobs/${job.id}/results/download`, {
        responseType: 'blob',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `job-${job.id}-results.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to download results');
    }
  }, [job]);

  // Handle share job
  const handleShareJob = useCallback(async () => {
    if (!job) return;

    const shareData = {
      title: `Job ${job.id}`,
      text: `Document processing job: ${job.status}`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        // Fallback to copying URL
        navigator.clipboard.writeText(window.location.href);
      }
    } else {
      // Fallback to copying URL
      navigator.clipboard.writeText(window.location.href);
    }
  }, [job]);

  // Initial fetch
  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  // Loading state
  if (isLoading) {
    return (
      <div className={cn(
        'flex items-center justify-center',
        embedded ? 'h-64' : 'min-h-screen bg-gray-50'
      )}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Job</h2>
          <p className="text-gray-600">Please wait while we load job details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !job) {
    return (
      <div className={cn(
        'flex items-center justify-center',
        embedded ? 'h-64' : 'min-h-screen bg-gray-50'
      )}>
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Job Not Found</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          {!embedded && (
            <button
              onClick={handleBack}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
            >
              Back to Jobs
            </button>
          )}
        </div>
      </div>
    );
  }

  const containerClass = embedded 
    ? 'space-y-6' 
    : 'min-h-screen bg-gray-50';

  return (
    <div className={containerClass}>
      {/* Header - only show if not embedded */}
      {!embedded && (
        <header className="bg-white border-b shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Left side */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleBack}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                  title="Back to jobs"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">
                    Job Monitoring
                  </h1>
                  <p className="text-sm text-gray-600">
                    {job?.id && `Job ID: ${job.id.slice(0, 8)}...`}
                  </p>
                </div>
              </div>

              {/* Right side */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={fetchJob}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                  title="Refresh"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>

                {job?.status === ProcessingStatus.COMPLETED && (
                  <button
                    onClick={handleDownloadResults}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                    title="Download results"
                  >
                    <Download className="w-5 h-5" />
                  </button>
                )}

                <button
                  onClick={handleShareJob}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                  title="Share job"
                >
                  <Share2 className="w-5 h-5" />
                </button>

                {job?.status === ProcessingStatus.PROCESSING && (
                  <button
                    onClick={handleCancelJob}
                    className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                    title="Cancel job"
                  >
                    Cancel
                  </button>
                )}

                {job?.status === ProcessingStatus.FAILED && (
                  <button
                    onClick={handleRetryJob}
                    className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    title="Retry job"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Main content */}
      <div className={cn(
        'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
        embedded ? '' : 'py-6'
      )}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Real-time status display */}
            {jobId && (
              <RealTimeStatusDisplay
                jobId={jobId}
                onJobComplete={handleJobComplete}
                onJobError={handleJobError}
              />
            )}

            {/* Error display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <div className="text-red-500">⚠️</div>
                  <div>
                    <h4 className="text-sm font-medium text-red-800">Error</h4>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Current job card */}
            {job && (
              <JobStatusCard
                job={job}
                onViewDocument={handleViewDocument}
                showDetails={true}
              />
            )}

            {/* Related jobs */}
            {relatedJobs.length > 0 && (
              <div className="bg-white rounded-lg border shadow-sm">
                <div className="p-4 border-b">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Related Jobs
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Other jobs for the same document
                  </p>
                </div>
                <div className="p-4 space-y-4">
                  {relatedJobs.map((relatedJob) => (
                    <JobStatusCard
                      key={relatedJob.id}
                      job={relatedJob}
                      onClick={(job) => navigate(`/jobs/${job.id}`)}
                      showDetails={false}
                      className="border-l-4 border-l-gray-200"
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Quick actions */}
            {job && (
              <div className="bg-white rounded-lg border shadow-sm p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Quick Actions
                </h3>
                <div className="space-y-2">
                  {job.status === ProcessingStatus.COMPLETED && job.documentId && (
                    <button
                      onClick={() => handleViewDocument(job.documentId)}
                      className="w-full px-4 py-2 text-left text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors"
                    >
                      View Processed Document
                    </button>
                  )}
                  
                  <button
                    onClick={fetchJob}
                    className="w-full px-4 py-2 text-left text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
                  >
                    Refresh Job Status
                  </button>
                  
                  {job.status === ProcessingStatus.COMPLETED && (
                    <button
                      onClick={handleDownloadResults}
                      className="w-full px-4 py-2 text-left text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors"
                    >
                      Download Results
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobMonitoringPage;