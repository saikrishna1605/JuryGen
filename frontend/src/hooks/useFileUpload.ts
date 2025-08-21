import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { UploadRequest, UploadResponse, UploadProgress } from '../types';
import { apiClient } from '../lib/api';

interface UseFileUploadOptions {
  onProgress?: (progress: UploadProgress) => void;
  onSuccess?: (response: UploadResponse) => void;
  onError?: (error: Error) => void;
}

interface UploadState {
  isUploading: boolean;
  progress: UploadProgress | null;
  error: string | null;
}

export const useFileUpload = (options: UseFileUploadOptions = {}) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    isUploading: false,
    progress: null,
    error: null,
  });

  // Get signed upload URL
  const getUploadUrlMutation = useMutation({
    mutationFn: async (request: UploadRequest): Promise<UploadResponse> => {
      const response = await apiClient.post('/v1/upload', request);
      return response.data;
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get upload URL';
      setUploadState(prev => ({ ...prev, error: errorMessage }));
      options.onError?.(error instanceof Error ? error : new Error(errorMessage));
    },
  });

  // Upload file to signed URL
  const uploadToSignedUrl = useCallback(
    async (file: File, uploadUrl: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress: UploadProgress = {
              loaded: event.loaded,
              total: event.total,
              percentage: Math.round((event.loaded / event.total) * 100),
            };

            // Calculate upload speed and time remaining
            const now = Date.now();
            const timeDiff = now - startTime;
            if (timeDiff > 1000) { // Only calculate after 1 second
              progress.speed = event.loaded / (timeDiff / 1000); // bytes per second
              progress.timeRemaining = (event.total - event.loaded) / progress.speed;
            }

            setUploadState(prev => ({ ...prev, progress }));
            options.onProgress?.(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            setUploadState(prev => ({
              ...prev,
              isUploading: false,
              progress: { loaded: file.size, total: file.size, percentage: 100 },
            }));
            resolve();
          } else {
            const error = new Error(`Upload failed with status ${xhr.status}`);
            setUploadState(prev => ({
              ...prev,
              isUploading: false,
              error: error.message,
            }));
            reject(error);
          }
        });

        xhr.addEventListener('error', () => {
          const error = new Error('Upload failed due to network error');
          setUploadState(prev => ({
            ...prev,
            isUploading: false,
            error: error.message,
          }));
          reject(error);
        });

        xhr.addEventListener('abort', () => {
          const error = new Error('Upload was cancelled');
          setUploadState(prev => ({
            ...prev,
            isUploading: false,
            error: error.message,
          }));
          reject(error);
        });

        const startTime = Date.now();
        setUploadState(prev => ({
          ...prev,
          isUploading: true,
          progress: { loaded: 0, total: file.size, percentage: 0 },
          error: null,
        }));

        // For Google Cloud Storage signed URLs, we typically use PUT
        xhr.open('PUT', uploadUrl);
        xhr.setRequestHeader('Content-Type', file.type);
        xhr.send(file);
      });
    },
    [options]
  );

  // Main upload function
  const uploadFile = useCallback(
    async (request: UploadRequest, file: File): Promise<UploadResponse> => {
      try {
        // Reset state
        setUploadState({
          isUploading: false,
          progress: null,
          error: null,
        });

        // Get signed upload URL
        const uploadResponse = await getUploadUrlMutation.mutateAsync(request);

        // Upload file to signed URL
        await uploadToSignedUrl(file, uploadResponse.uploadUrl);

        options.onSuccess?.(uploadResponse);
        return uploadResponse;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        setUploadState(prev => ({ ...prev, error: errorMessage }));
        options.onError?.(error instanceof Error ? error : new Error(errorMessage));
        throw error;
      }
    },
    [getUploadUrlMutation, uploadToSignedUrl, options]
  );

  // Retry upload function
  const retryUpload = useCallback(() => {
    setUploadState(prev => ({ ...prev, error: null }));
  }, []);

  // Cancel upload function
  const cancelUpload = useCallback(() => {
    // Note: In a real implementation, you'd need to store the XMLHttpRequest
    // instance to be able to call xhr.abort()
    setUploadState({
      isUploading: false,
      progress: null,
      error: 'Upload cancelled',
    });
  }, []);

  return {
    uploadFile,
    retryUpload,
    cancelUpload,
    isUploading: uploadState.isUploading || getUploadUrlMutation.isPending,
    progress: uploadState.progress,
    error: uploadState.error || getUploadUrlMutation.error?.message,
    isError: !!uploadState.error || getUploadUrlMutation.isError,
    isSuccess: !uploadState.isUploading && !uploadState.error && uploadState.progress?.percentage === 100,
  };
};

// Hook for multiple file uploads
export const useMultiFileUpload = (options: UseFileUploadOptions = {}) => {
  const [uploads, setUploads] = useState<Map<string, UploadState>>(new Map());

  const uploadFile = useCallback(
    async (fileId: string, request: UploadRequest, file: File): Promise<UploadResponse> => {
      // Initialize upload state
      setUploads(prev => new Map(prev.set(fileId, {
        isUploading: true,
        progress: { loaded: 0, total: file.size, percentage: 0 },
        error: null,
      })));

      try {
        // Get signed upload URL
        const response = await apiClient.post('/v1/upload', request);
        const uploadResponse: UploadResponse = response.data;

        // Upload file with progress tracking
        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest();

          xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
              const progress: UploadProgress = {
                loaded: event.loaded,
                total: event.total,
                percentage: Math.round((event.loaded / event.total) * 100),
              };

              setUploads(prev => new Map(prev.set(fileId, {
                isUploading: true,
                progress,
                error: null,
              })));
              options.onProgress?.(progress);
            }
          });

          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              setUploads(prev => new Map(prev.set(fileId, {
                isUploading: false,
                progress: { loaded: file.size, total: file.size, percentage: 100 },
                error: null,
              })));
              resolve();
            } else {
              const error = new Error(`Upload failed with status ${xhr.status}`);
              setUploads(prev => new Map(prev.set(fileId, {
                isUploading: false,
                progress: null,
                error: error.message,
              })));
              reject(error);
            }
          });

          xhr.addEventListener('error', () => {
            const error = new Error('Upload failed due to network error');
            setUploads(prev => new Map(prev.set(fileId, {
              isUploading: false,
              progress: null,
              error: error.message,
            })));
            reject(error);
          });

          xhr.open('PUT', uploadResponse.uploadUrl);
          xhr.setRequestHeader('Content-Type', file.type);
          xhr.send(file);
        });

        options.onSuccess?.(uploadResponse);
        return uploadResponse;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        setUploads(prev => new Map(prev.set(fileId, {
          isUploading: false,
          progress: null,
          error: errorMessage,
        })));
        options.onError?.(error instanceof Error ? error : new Error(errorMessage));
        throw error;
      }
    },
    [options]
  );

  const getUploadState = useCallback((fileId: string): UploadState => {
    return uploads.get(fileId) || {
      isUploading: false,
      progress: null,
      error: null,
    };
  }, [uploads]);

  const removeUpload = useCallback((fileId: string) => {
    setUploads(prev => {
      const newMap = new Map(prev);
      newMap.delete(fileId);
      return newMap;
    });
  }, []);

  const clearAllUploads = useCallback(() => {
    setUploads(new Map());
  }, []);

  return {
    uploadFile,
    getUploadState,
    removeUpload,
    clearAllUploads,
    totalUploads: uploads.size,
    activeUploads: Array.from(uploads.values()).filter(state => state.isUploading).length,
    completedUploads: Array.from(uploads.values()).filter(
      state => !state.isUploading && !state.error && state.progress?.percentage === 100
    ).length,
    failedUploads: Array.from(uploads.values()).filter(state => state.error).length,
  };
};