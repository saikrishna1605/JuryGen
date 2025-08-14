import { z } from 'zod';
import { ProcessingStatus, ProcessingStage } from './document';

// Job-related enums
export enum JobPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

export enum ErrorType {
  VALIDATION_ERROR = 'validation_error',
  UPLOAD_ERROR = 'upload_error',
  OCR_ERROR = 'ocr_error',
  ANALYSIS_ERROR = 'analysis_error',
  AI_SERVICE_ERROR = 'ai_service_error',
  STORAGE_ERROR = 'storage_error',
  TIMEOUT_ERROR = 'timeout_error',
  QUOTA_EXCEEDED = 'quota_exceeded',
  INTERNAL_ERROR = 'internal_error',
}

// Zod schemas
export const JobOptionsSchema = z.object({
  enableTranslation: z.boolean().default(true),
  enableAudio: z.boolean().default(true),
  targetLanguages: z.array(z.string()).default([]),
  audioVoice: z.string().optional(),
  readingLevel: z.enum(['elementary', 'middle', 'high', 'college']).default('middle'),
  includeExplanations: z.boolean().default(true),
  highlightRisks: z.boolean().default(true),
});

export const JobErrorSchema = z.object({
  type: z.nativeEnum(ErrorType),
  message: z.string(),
  details: z.record(z.any()).optional(),
  timestamp: z.string().datetime(),
  retryable: z.boolean(),
  retryCount: z.number().nonnegative().default(0),
});

export const JobProgressSchema = z.object({
  stage: z.nativeEnum(ProcessingStage),
  percentage: z.number().min(0).max(100),
  message: z.string().optional(),
  estimatedTimeRemaining: z.number().positive().optional(),
  startedAt: z.string().datetime().optional(),
  completedAt: z.string().datetime().optional(),
});

export const JobSchema = z.object({
  id: z.string().uuid(),
  documentId: z.string().uuid(),
  userId: z.string(),
  status: z.nativeEnum(ProcessingStatus),
  currentStage: z.nativeEnum(ProcessingStage),
  progressPercentage: z.number().min(0).max(100).default(0),
  priority: z.nativeEnum(JobPriority).default(JobPriority.NORMAL),
  options: JobOptionsSchema,
  createdAt: z.string().datetime(),
  startedAt: z.string().datetime().optional(),
  completedAt: z.string().datetime().optional(),
  estimatedCompletion: z.string().datetime().optional(),
  error: JobErrorSchema.optional(),
  progress: z.array(JobProgressSchema).default([]),
  retryCount: z.number().nonnegative().default(0),
  maxRetries: z.number().nonnegative().default(3),
});

export const JobResultsSchema = z.object({
  jobId: z.string().uuid(),
  documentId: z.string().uuid(),
  completedAt: z.string().datetime(),
  processingTime: z.number().positive(),
  summary: z.object({
    totalClauses: z.number().nonnegative(),
    riskyClauses: z.number().nonnegative(),
    cautionClauses: z.number().nonnegative(),
    beneficialClauses: z.number().nonnegative(),
    overallRiskScore: z.number().min(0).max(1),
  }),
  exports: z.object({
    highlightedPdf: z.string().url().optional(),
    summaryDocx: z.string().url().optional(),
    clausesCsv: z.string().url().optional(),
    audioNarration: z.string().url().optional(),
    transcriptSrt: z.string().url().optional(),
  }),
  translations: z.record(z.string(), z.object({
    summary: z.string(),
    audioUrl: z.string().url().optional(),
    confidence: z.number().min(0).max(1),
  })),
  metadata: z.object({
    aiModelsUsed: z.array(z.string()),
    processingCost: z.number().positive().optional(),
    tokensUsed: z.number().positive().optional(),
    apiCallsCount: z.number().positive().optional(),
  }),
});

export const UploadRequestSchema = z.object({
  filename: z.string().min(1).max(255),
  contentType: z.string(),
  sizeBytes: z.number().positive().max(50 * 1024 * 1024), // 50MB limit
  jurisdiction: z.string().optional(),
  userRole: z.string().optional(),
  options: JobOptionsSchema.optional(),
});

export const UploadResponseSchema = z.object({
  jobId: z.string().uuid(),
  uploadUrl: z.string().url(),
  expiresAt: z.string().datetime(),
  maxFileSize: z.number().positive(),
  allowedContentTypes: z.array(z.string()),
});

// Server-Sent Events schemas
export const SSEEventSchema = z.object({
  type: z.enum(['job_update', 'error', 'complete']),
  data: z.record(z.any()),
  timestamp: z.string().datetime(),
  requestId: z.string().optional(),
});

export const JobUpdateEventSchema = z.object({
  jobId: z.string().uuid(),
  status: z.nativeEnum(ProcessingStatus),
  stage: z.nativeEnum(ProcessingStage),
  progress: z.number().min(0).max(100),
  message: z.string().optional(),
  estimatedCompletion: z.string().datetime().optional(),
});

// TypeScript types
export type JobOptions = z.infer<typeof JobOptionsSchema>;
export type JobError = z.infer<typeof JobErrorSchema>;
export type JobProgress = z.infer<typeof JobProgressSchema>;
export type Job = z.infer<typeof JobSchema>;
export type JobResults = z.infer<typeof JobResultsSchema>;
export type UploadRequest = z.infer<typeof UploadRequestSchema>;
export type UploadResponse = z.infer<typeof UploadResponseSchema>;
export type SSEEvent = z.infer<typeof SSEEventSchema>;
export type JobUpdateEvent = z.infer<typeof JobUpdateEventSchema>;

// Helper types
export interface JobStatistics {
  totalJobs: number;
  completedJobs: number;
  failedJobs: number;
  averageProcessingTime: number;
  successRate: number;
}

export interface ProcessingMetrics {
  stage: ProcessingStage;
  duration: number;
  tokensUsed?: number;
  apiCalls?: number;
  cost?: number;
}

export interface JobQueue {
  position: number;
  estimatedWaitTime: number;
  queueLength: number;
}

// Job creation helpers
export const createJobOptions = (overrides?: Partial<JobOptions>): JobOptions => {
  return JobOptionsSchema.parse({
    enableTranslation: true,
    enableAudio: true,
    targetLanguages: [],
    readingLevel: 'middle',
    includeExplanations: true,
    highlightRisks: true,
    ...overrides,
  });
};

export const createUploadRequest = (
  filename: string,
  file: File,
  options?: Partial<UploadRequest>
): UploadRequest => {
  return UploadRequestSchema.parse({
    filename,
    contentType: file.type,
    sizeBytes: file.size,
    ...options,
  });
};