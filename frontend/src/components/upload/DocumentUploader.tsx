import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, X, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { UploadUrlRequest, JobOptions, UserRole, UploadUrlResponse } from '../../types';
import { createJobOptions } from '../../types/job';
import { useMultiFileUpload } from '../../hooks/useFileUpload';

interface DocumentUploaderProps {
  onUploadComplete?: (response: UploadUrlResponse) => void;
  onError?: (error: string) => void;
  className?: string;
  disabled?: boolean;
  maxFileSize?: number;
  acceptedFileTypes?: string[];
}

interface UploadFile extends File {
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  jobId?: string;
}

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/tiff': ['.tiff', '.tif'],
  'image/bmp': ['.bmp'],
};

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  onUploadComplete,
  onError,
  className,
  disabled = false,
  maxFileSize = MAX_FILE_SIZE,
  acceptedFileTypes = Object.keys(ACCEPTED_FILE_TYPES),
}) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [jurisdiction, setJurisdiction] = useState<string>('');
  const [userRole, setUserRole] = useState<UserRole | ''>('');
  const [jobOptions, setJobOptions] = useState<JobOptions>(createJobOptions());

  const multiUpload = useMultiFileUpload({
    onSuccess: (response) => {
      onUploadComplete?.(response);
    },
    onError: (error) => {
      onError?.(error.message);
    },
  });

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const errors = rejectedFiles.map((file) => {
          const error = file.errors[0];
          return `${file.file.name}: ${error.message}`;
        });
        onError?.(errors.join(', '));
        return;
      }

      // Add accepted files to upload queue
      const newFiles: UploadFile[] = acceptedFiles.map((file) => ({
        ...file,
        id: crypto.randomUUID(),
        progress: 0,
        status: 'pending' as const,
      }));

      setFiles((prev) => [...prev, ...newFiles]);
    },
    [onError]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: acceptedFileTypes.reduce((acc, type) => {
      acc[type] = ACCEPTED_FILE_TYPES[type as keyof typeof ACCEPTED_FILE_TYPES] || [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize: maxFileSize,
    disabled,
    multiple: true,
  });

  const removeFile = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((file) => file.id !== fileId));
  }, []);

  const uploadFile = useCallback(
    async (file: UploadFile) => {
      try {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: 'uploading', progress: 0 } : f
          )
        );

        const uploadRequest: UploadUrlRequest = {
          filename: file.name,
          contentType: file.type,
          sizeBytes: file.size,
          options: jobOptions,
          jurisdiction: jurisdiction || undefined,
          userRole: userRole || undefined,
        };

        const result = await multiUpload.uploadFile(file.id, uploadRequest, file);

        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? { ...f, status: 'success', progress: 100, jobId: result.jobId }
              : f
          )
        );

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? { ...f, status: 'error', error: errorMessage }
              : f
          )
        );

        throw error;
      }
    },
    [multiUpload, jurisdiction, userRole, jobOptions]
  );

  const retryUpload = useCallback(
    async (file: UploadFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === file.id ? { ...f, status: 'pending', error: undefined } : f
        )
      );
      await uploadFile(file);
    },
    [uploadFile]
  );

  const uploadAllFiles = useCallback(async () => {
    const pendingFiles = files.filter((file) => file.status === 'pending');
    
    for (const file of pendingFiles) {
      try {
        await uploadFile(file);
      } catch (error) {
        // Error is already handled in uploadFile
        console.error('Upload failed for file:', file.name, error);
      }
    }
  }, [files, uploadFile]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending':
        return <FileText className="h-5 w-5 text-gray-400" />;
      case 'uploading':
        return (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        );
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  return (
    <div className={clsx('w-full space-y-6', className)}>
      {/* Upload Options */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="jurisdiction" className="block text-sm font-medium text-gray-700">
            Jurisdiction (Optional)
          </label>
          <input
            type="text"
            id="jurisdiction"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            placeholder="e.g., California, New York, Ontario"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            disabled={disabled}
          />
        </div>

        <div>
          <label htmlFor="userRole" className="block text-sm font-medium text-gray-700">
            Your Role (Optional)
          </label>
          <select
            id="userRole"
            value={userRole}
            onChange={(e) => setUserRole(e.target.value as UserRole | '')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            disabled={disabled}
          >
            <option value="">Select your role</option>
            <option value={UserRole.TENANT}>Tenant</option>
            <option value={UserRole.LANDLORD}>Landlord</option>
            <option value={UserRole.BORROWER}>Borrower</option>
            <option value={UserRole.LENDER}>Lender</option>
            <option value={UserRole.BUYER}>Buyer</option>
            <option value={UserRole.SELLER}>Seller</option>
            <option value={UserRole.EMPLOYEE}>Employee</option>
            <option value={UserRole.EMPLOYER}>Employer</option>
            <option value={UserRole.CONSUMER}>Consumer</option>
            <option value={UserRole.BUSINESS}>Business</option>
          </select>
        </div>
      </div>

      {/* Processing Options */}
      <div className="rounded-lg border border-gray-200 p-4">
        <h3 className="mb-3 text-sm font-medium text-gray-900">Processing Options</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={jobOptions.customSettings?.enableTranslation || false}
              onChange={(e) =>
                setJobOptions((prev) => ({ 
                  ...prev, 
                  customSettings: { 
                    ...prev.customSettings, 
                    enableTranslation: e.target.checked 
                  } 
                }))
              }
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              disabled={disabled}
            />
            <span className="ml-2 text-sm text-gray-700">Enable Translation</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={jobOptions.customSettings?.enableAudio || false}
              onChange={(e) =>
                setJobOptions((prev) => ({ 
                  ...prev, 
                  customSettings: { 
                    ...prev.customSettings, 
                    enableAudio: e.target.checked 
                  } 
                }))
              }
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              disabled={disabled}
            />
            <span className="ml-2 text-sm text-gray-700">Generate Audio Narration</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={jobOptions.customSettings?.highlightRisks || false}
              onChange={(e) =>
                setJobOptions((prev) => ({ 
                  ...prev, 
                  customSettings: { 
                    ...prev.customSettings, 
                    highlightRisks: e.target.checked 
                  } 
                }))
              }
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              disabled={disabled}
            />
            <span className="ml-2 text-sm text-gray-700">Highlight Risk Areas</span>
          </label>

          <div>
            <label htmlFor="readingLevel" className="block text-sm font-medium text-gray-700">
              Reading Level
            </label>
            <select
              id="readingLevel"
              value={jobOptions.customSettings?.readingLevel || 'college'}
              onChange={(e) =>
                setJobOptions((prev) => ({
                  ...prev,
                  customSettings: { 
                    ...prev.customSettings, 
                    readingLevel: e.target.value 
                  }
                }))
              }
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              disabled={disabled}
            >
              <option value="elementary">Elementary</option>
              <option value="middle">Middle School</option>
              <option value="high">High School</option>
              <option value="college">College</option>
            </select>
          </div>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'relative cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          {
            'border-blue-300 bg-blue-50': isDragActive && !isDragReject,
            'border-red-300 bg-red-50': isDragReject,
            'border-gray-300 hover:border-gray-400': !isDragActive && !disabled,
            'border-gray-200 bg-gray-50 cursor-not-allowed': disabled,
          }
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          <Upload
            className={clsx('h-12 w-12', {
              'text-blue-500': isDragActive && !isDragReject,
              'text-red-500': isDragReject,
              'text-gray-400': !isDragActive,
            })}
          />
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive
                ? isDragReject
                  ? 'Some files are not supported'
                  : 'Drop files here'
                : 'Upload legal documents'}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              Drag and drop files here, or click to browse
            </p>
            <p className="mt-2 text-xs text-gray-400">
              Supports PDF, DOCX, DOC, and image files up to {formatFileSize(maxFileSize)}
            </p>
          </div>
        </div>
      </div>

      {/* File List */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-900">
                Files ({files.length})
              </h3>
              {files.some((file) => file.status === 'pending') && (
                <button
                  onClick={uploadAllFiles}
                  disabled={disabled}
                  className="rounded-md bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  Upload All
                </button>
              )}
            </div>

            <div className="space-y-2">
              {files.map((file) => (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="rounded-lg border border-gray-200 p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(file.status)}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-gray-900">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(file.size)}
                          {file.status === 'uploading' && ` • ${file.progress}%`}
                          {file.error && ` • ${file.error}`}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {file.status === 'pending' && (
                        <button
                          onClick={() => uploadFile(file)}
                          disabled={disabled}
                          className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
                        >
                          Upload
                        </button>
                      )}
                      {file.status === 'error' && (
                        <button
                          onClick={() => retryUpload(file)}
                          disabled={disabled}
                          className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
                        >
                          <RefreshCw className="h-3 w-3" />
                          <span>Retry</span>
                        </button>
                      )}
                      {file.status === 'success' && file.jobId && (
                        <span className="text-xs text-green-600">
                          Job ID: {file.jobId.slice(0, 8)}...
                        </span>
                      )}
                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-gray-400 hover:text-gray-600"
                        disabled={file.status === 'uploading'}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {file.status === 'uploading' && (
                    <div className="mt-2">
                      <div className="h-2 w-full rounded-full bg-gray-200">
                        <motion.div
                          className="h-2 rounded-full bg-blue-500"
                          initial={{ width: 0 }}
                          animate={{ width: `${file.progress}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};