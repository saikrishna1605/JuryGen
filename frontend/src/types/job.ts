import { z } from 'zod';
import { Document } from './document';

// Enums
export enum ProcessingStatus {
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum ProcessingStage {
  UPLOAD = 'upload',
  OCR = 'ocr',
  ANALYSIS = 'analysis',
  SUMMARIZATION = 'summarization',
  RISK_ASSESSMENT = 'risk_assessment',
  TRANSLATION = 'translation',
  AUDIO_GENERATION = 'audio_generation',
  EXPORT_GENERATION = 'export_generation',
}

// Zod schemas for validation
export const JobProgressSchema = z.object({
  stage: z.nativeEnum(ProcessingStage),
  progress: z.number().min(0).max(100),
  message: z.string().optional(),
  estimatedTimeRemaining: z.number().positive().optional(),
  startedAt: z.string().datetime().optional(),
  completedAt: z.string().datetime().optional(),
});

export const JobResultsSchema = z.object({
  documentId: z.string().uuid(),
  processingTime: z.number().positive(),
  stages: z.array(JobProgressSchema),
  outputs: z.record(z.string(), z.any()),
  metrics: z.record(z.string(), z.number()).optional(),
});

export const JobSchema = z.object({
  id: z.string().uuid(),
  documentId: z.string().uuid(),
  userId: z.string(),
  status: z.nativeEnum(ProcessingStatus),
  currentStage: z.nativeEnum(ProcessingStage),
  progressPercentage: z.number().min(0).max(100),
  createdAt: z.string().datetime(),
  startedAt: z.string().datetime().optional(),
  completedAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
  errorMessage: z.string().optional(),
  progressMessage: z.string().optional(),
  estimatedCompletion: z.string().datetime().optional(),
  results: JobResultsSchema.optional(),
  priority: z.number().min(1).max(4).default(2),
  retryCount: z.number().min(0).default(0),
  maxRetries: z.number().min(0).default(3),
});

// TypeScript types derived from schemas
export type JobProgress = z.infer<typeof JobProgressSchema>;
export type JobResults = z.infer<typeof JobResultsSchema>;
export type Job = z.infer<typeof JobSchema>;

// Extended job type with document information
export interface JobWithDocument extends Job {
  document?: Document;
}

// Job options schema
export const JobOptionsSchema = z.object({
  skipStages: z.array(z.nativeEnum(ProcessingStage)).optional(),
  customSettings: z.record(z.string(), z.any()).optional(),
  priority: z.number().min(1).max(4).optional(),
  timeout: z.number().positive().optional(),
  retryPolicy: z.object({
    maxRetries: z.number().min(0).optional(),
    backoffMultiplier: z.number().positive().optional(),
    maxBackoffTime: z.number().positive().optional(),
  }).optional(),
});

export type JobOptions = z.infer<typeof JobOptionsSchema>;

// Helper function to create job options
export const createJobOptions = (options: Partial<JobOptions> = {}): JobOptions => {
  return {
    priority: 2,
    timeout: 300000, // 5 minutes default
    ...options,
  };
};

// Helper function to create upload request
export const createUploadRequest = (
  documentId: string,
  options: Partial<JobOptions> = {}
): CreateJobRequest => {
  return {
    documentId,
    priority: options.priority || 2,
    options: createJobOptions(options),
  };
};

// Job creation request
export interface CreateJobRequest {
  documentId: string;
  priority?: number;
  options?: JobOptions;
}

// Job update request
export interface UpdateJobRequest {
  status?: ProcessingStatus;
  currentStage?: ProcessingStage;
  progressPercentage?: number;
  progressMessage?: string;
  errorMessage?: string;
  estimatedCompletion?: string;
}

// Job query parameters
export interface JobQueryParams {
  status?: ProcessingStatus[];
  userId?: string;
  documentId?: string;
  limit?: number;
  offset?: number;
  sortBy?: 'createdAt' | 'updatedAt' | 'priority';
  sortOrder?: 'asc' | 'desc';
}

// Job statistics
export interface JobStatistics {
  total: number;
  byStatus: Record<ProcessingStatus, number>;
  byStage: Record<ProcessingStage, number>;
  averageProcessingTime: number;
  successRate: number;
  recentJobs: Job[];
}

// Real-time job update event
export interface JobUpdateEvent {
  type: 'job_update';
  jobId: string;
  data: Partial<Job>;
  timestamp: string;
}

// System message event
export interface SystemMessageEvent {
  type: 'system_message';
  message: string;
  messageType: 'info' | 'warning' | 'error';
  timestamp: string;
}

// Connection status
export interface ConnectionStatus {
  isConnected: boolean;
  lastUpdate?: Date;
  error?: string;
}

// Job queue information
export interface QueueInfo {
  position: number;
  estimatedWaitTime: number;
  totalInQueue: number;
}

// Processing metrics
export interface ProcessingMetrics {
  stage: ProcessingStage;
  duration: number;
  memoryUsage?: number;
  cpuUsage?: number;
  apiCalls?: number;
  tokensProcessed?: number;
}

// Error details
export interface JobError {
  code: string;
  message: string;
  stage: ProcessingStage;
  timestamp: string;
  details?: Record<string, any>;
  retryable: boolean;
}

// Job configuration
export interface JobConfig {
  timeout: number;
  retryPolicy: {
    maxRetries: number;
    backoffMultiplier: number;
    maxBackoffTime: number;
  };
  resources: {
    memory: string;
    cpu: string;
  };
  environment: Record<string, string>;
}

// Batch job operations
export interface BatchJobRequest {
  jobIds: string[];
  action: 'cancel' | 'retry' | 'delete';
}

export interface BatchJobResponse {
  successful: string[];
  failed: Array<{
    jobId: string;
    error: string;
  }>;
}

// Job export options
export interface JobExportOptions {
  format: 'json' | 'csv' | 'xlsx';
  includeResults: boolean;
  includeMetrics: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
  filters?: JobQueryParams;
}

// Webhook configuration for job events
export interface JobWebhook {
  id: string;
  url: string;
  events: Array<'job.created' | 'job.started' | 'job.completed' | 'job.failed'>;
  secret: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
}