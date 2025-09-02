import { z } from 'zod';
import { ProcessingStatus, ProcessingStage } from './job';
import { ClauseClassification } from './document';
import { JobOptionsSchema } from './job';

// API Response wrapper schemas
export const ApiResponseSchema = z.object({
  success: z.boolean(),
  data: z.any().optional(),
  error: z.string().optional(),
  message: z.string().optional(),
  requestId: z.string().optional(),
  timestamp: z.string().datetime(),
});

export const PaginatedResponseSchema = z.object({
  data: z.array(z.any()),
  pagination: z.object({
    page: z.number().positive(),
    limit: z.number().positive(),
    total: z.number().nonnegative(),
    totalPages: z.number().nonnegative(),
    hasNext: z.boolean(),
    hasPrev: z.boolean(),
  }),
});

// Error response schemas
export const ApiErrorSchema = z.object({
  error: z.string(),
  message: z.string(),
  details: z.record(z.any()).optional(),
  requestId: z.string().optional(),
  timestamp: z.string().datetime(),
  statusCode: z.number(),
});

export const ValidationErrorSchema = z.object({
  field: z.string(),
  message: z.string(),
  code: z.string(),
  value: z.any().optional(),
});

// Upload API schemas
export const UploadUrlRequestSchema = z.object({
  filename: z.string(),
  contentType: z.string(),
  sizeBytes: z.number().positive(),
  jurisdiction: z.string().optional(),
  userRole: z.string().optional(),
  options: JobOptionsSchema.optional(),
});

export const UploadUrlResponseSchema = z.object({
  jobId: z.string().uuid(),
  uploadUrl: z.string().url(),
  expiresAt: z.string().datetime(),
  fields: z.record(z.string()).optional(),
});

// Job API schemas
export const JobStatusResponseSchema = z.object({
  jobId: z.string().uuid(),
  status: z.nativeEnum(ProcessingStatus),
  currentStage: z.nativeEnum(ProcessingStage),
  progressPercentage: z.number().min(0).max(100),
  createdAt: z.string().datetime(),
  startedAt: z.string().datetime().optional(),
  completedAt: z.string().datetime().optional(),
  estimatedCompletion: z.string().datetime().optional(),
  error: z.object({
    type: z.string(),
    message: z.string(),
    retryable: z.boolean(),
  }).optional(),
});

export const JobResultsResponseSchema = z.object({
  jobId: z.string().uuid(),
  document: z.object({
    id: z.string().uuid(),
    filename: z.string(),
    pages: z.number().positive(),
    wordCount: z.number().positive(),
  }),
  summary: z.object({
    plainLanguage: z.string(),
    keyPoints: z.array(z.string()),
    readingLevel: z.string(),
  }),
  clauses: z.array(z.object({
    id: z.string().uuid(),
    text: z.string(),
    clauseNumber: z.string().optional(),
    classification: z.nativeEnum(ClauseClassification),
    riskScore: z.number().min(0).max(1),
    impactScore: z.number().min(0).max(100),
    likelihoodScore: z.number().min(0).max(100),
    saferAlternatives: z.array(z.object({
      suggestedText: z.string(),
      rationale: z.string(),
    })),
    legalCitations: z.array(z.object({
      statute: z.string(),
      description: z.string(),
      url: z.string().url().optional(),
    })),
  })),
  riskAssessment: z.object({
    overallRisk: z.enum(['low', 'medium', 'high']),
    highRiskClauses: z.number().nonnegative(),
    recommendations: z.array(z.string()),
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
  })),
});

// Q&A API schemas
export const QARequestSchema = z.object({
  jobId: z.string().uuid(),
  query: z.string().min(1).max(1000),
  audioUrl: z.string().url().optional(),
  role: z.string().optional(),
  jurisdiction: z.string().optional(),
  locale: z.string().default('en-US'),
  responseFormat: z.enum(['text', 'audio', 'both']).default('text'),
});

export const QAResponseSchema = z.object({
  question: z.string(),
  answer: z.string(),
  confidence: z.number().min(0).max(1),
  sources: z.array(z.object({
    clauseId: z.string().uuid(),
    clauseText: z.string(),
    relevance: z.number().min(0).max(1),
  })),
  audioResponse: z.object({
    url: z.string().url(),
    duration: z.number().positive(),
    transcript: z.string(),
  }).optional(),
  relatedQuestions: z.array(z.string()),
});

// Export API schemas
export const ExportRequestSchema = z.object({
  jobId: z.string().uuid(),
  formats: z.array(z.enum(['pdf', 'docx', 'csv', 'mp3', 'srt'])),
  options: z.object({
    includeAnnotations: z.boolean().default(true),
    highlightRisks: z.boolean().default(true),
    language: z.string().default('en'),
    audioVoice: z.string().optional(),
  }).optional(),
});

export const ExportResponseSchema = z.object({
  exportId: z.string().uuid(),
  status: z.enum(['generating', 'completed', 'failed']),
  estimatedCompletion: z.string().datetime().optional(),
  downloadUrls: z.record(z.string(), z.string().url()).optional(),
});

// Health check schema
export const HealthCheckResponseSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  version: z.string(),
  timestamp: z.number(),
  services: z.record(z.string(), z.object({
    status: z.enum(['up', 'down', 'degraded']),
    responseTime: z.number().optional(),
    lastCheck: z.string().datetime(),
  })).optional(),
});

// WebSocket/SSE event schemas
export const SSEEventTypeSchema = z.enum([
  'job_created',
  'job_started',
  'job_progress',
  'job_completed',
  'job_failed',
  'job_cancelled',
  'export_ready',
  'error',
]);

export const SSEMessageSchema = z.object({
  type: SSEEventTypeSchema,
  data: z.record(z.any()),
  timestamp: z.string().datetime(),
  jobId: z.string().uuid().optional(),
});

// Rate limiting schemas
export const RateLimitHeadersSchema = z.object({
  'x-ratelimit-limit': z.string(),
  'x-ratelimit-remaining': z.string(),
  'x-ratelimit-reset': z.string(),
  'x-ratelimit-retry-after': z.string().optional(),
});

// TypeScript types
export type ApiResponse<T = any> = z.infer<typeof ApiResponseSchema> & { data?: T };
export type PaginatedResponse<T = any> = z.infer<typeof PaginatedResponseSchema> & { data: T[] };
export type ApiError = z.infer<typeof ApiErrorSchema>;
export type ValidationError = z.infer<typeof ValidationErrorSchema>;

export type UploadUrlRequest = z.infer<typeof UploadUrlRequestSchema>;
export type UploadUrlResponse = z.infer<typeof UploadUrlResponseSchema>;

export type JobStatusResponse = z.infer<typeof JobStatusResponseSchema>;
export type JobResultsResponse = z.infer<typeof JobResultsResponseSchema>;

export type QARequest = z.infer<typeof QARequestSchema>;
export type QAResponse = z.infer<typeof QAResponseSchema>;

export type ExportRequest = z.infer<typeof ExportRequestSchema>;
export type ExportResponse = z.infer<typeof ExportResponseSchema>;

export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>;
export type SSEMessage = z.infer<typeof SSEMessageSchema>;
export type RateLimitHeaders = z.infer<typeof RateLimitHeadersSchema>;

// API client configuration
export interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  retryDelay: number;
  headers?: Record<string, string>;
}

// Request/Response interceptor types
export interface RequestInterceptor {
  onRequest?: (config: any) => any;
  onRequestError?: (error: any) => any;
}

export interface ResponseInterceptor {
  onResponse?: (response: any) => any;
  onResponseError?: (error: any) => any;
}

// Pagination parameters
export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filter?: Record<string, any>;
}

// File upload progress
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed?: number;
  timeRemaining?: number;
}

// API endpoint paths
export const API_ENDPOINTS = {
  // Health
  HEALTH: '/health',
  
  // Upload
  UPLOAD: '/upload',
  
  // Jobs
  JOBS: '/jobs',
  JOB_STATUS: (jobId: string) => `/jobs/${jobId}/status`,
  JOB_STREAM: (jobId: string) => `/jobs/${jobId}/stream`,
  JOB_ANALYZE: (jobId: string) => `/jobs/${jobId}/analyze`,
  JOB_RESULTS: (jobId: string) => `/jobs/${jobId}/results`,
  
  // Q&A
  QA: '/qa',
  
  // Exports
  EXPORTS: '/exports',
  EXPORT_GENERATE: (jobId: string) => `/exports/${jobId}/generate`,
  EXPORT_DOWNLOAD: (exportId: string) => `/exports/${exportId}`,
  
  // User
  USER_PROFILE: '/user/profile',
  USER_USAGE: '/user/usage',
  USER_PREFERENCES: '/user/preferences',
} as const;

// HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const;