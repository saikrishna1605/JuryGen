import { z } from 'zod';
import { ProcessingStatus, ProcessingStage } from './job';

export enum ClauseClassification {
  BENEFICIAL = 'beneficial',
  CAUTION = 'caution',
  RISKY = 'risky',
}

export enum UserRole {
  TENANT = 'tenant',
  LANDLORD = 'landlord',
  BORROWER = 'borrower',
  LENDER = 'lender',
  BUYER = 'buyer',
  SELLER = 'seller',
  EMPLOYEE = 'employee',
  EMPLOYER = 'employer',
  CONSUMER = 'consumer',
  BUSINESS = 'business',
}

// Zod schemas for validation
export const DocumentSchema = z.object({
  id: z.string().uuid(),
  filename: z.string().min(1).max(255),
  contentType: z.string(),
  sizeBytes: z.number().positive(),
  uploadTimestamp: z.string().datetime(),
  processingStatus: z.nativeEnum(ProcessingStatus),
  userId: z.string(),
  jurisdiction: z.string().optional(),
  userRole: z.nativeEnum(UserRole).optional(),
  pages: z.number().positive().optional(),
  wordCount: z.number().positive().optional(),
});

export const LegalCitationSchema = z.object({
  statute: z.string(),
  description: z.string(),
  url: z.string().url().optional(),
  jurisdiction: z.string(),
  relevance: z.number().min(0).max(1),
});

export const SaferAlternativeSchema = z.object({
  suggestedText: z.string(),
  rationale: z.string(),
  legalBasis: z.string().optional(),
  confidence: z.number().min(0).max(1),
});

export const RoleAnalysisSchema = z.object({
  classification: z.nativeEnum(ClauseClassification),
  rationale: z.string(),
  riskLevel: z.number().min(0).max(1),
  recommendations: z.array(z.string()),
});

export const ClauseSchema = z.object({
  id: z.string().uuid(),
  text: z.string(),
  clauseNumber: z.string().optional(),
  classification: z.nativeEnum(ClauseClassification),
  riskScore: z.number().min(0).max(1),
  impactScore: z.number().min(0).max(100),
  likelihoodScore: z.number().min(0).max(100),
  roleAnalysis: z.record(z.nativeEnum(UserRole), RoleAnalysisSchema),
  saferAlternatives: z.array(SaferAlternativeSchema),
  legalCitations: z.array(LegalCitationSchema),
  position: z.object({
    page: z.number().positive(),
    x: z.number(),
    y: z.number(),
    width: z.number(),
    height: z.number(),
  }).optional(),
});

export const DocumentSummarySchema = z.object({
  plainLanguage: z.string(),
  keyPoints: z.array(z.string()),
  readingLevel: z.string(),
  wordCount: z.number().positive(),
  estimatedReadingTime: z.number().positive(),
  overallTone: z.enum(['formal', 'neutral', 'friendly', 'aggressive']),
  complexity: z.enum(['low', 'medium', 'high']),
});

export const RiskAssessmentSchema = z.object({
  overallRisk: z.enum(['low', 'medium', 'high']),
  riskScore: z.number().min(0).max(1),
  highRiskClauses: z.number().nonnegative(),
  mediumRiskClauses: z.number().nonnegative(),
  lowRiskClauses: z.number().nonnegative(),
  recommendations: z.array(z.string()),
  negotiationPoints: z.array(z.string()),
  redFlags: z.array(z.string()),
});

export const AudioNarrationSchema = z.object({
  url: z.string().url(),
  duration: z.number().positive(),
  transcript: z.string(),
  language: z.string(),
  voice: z.string(),
  timestamps: z.array(z.object({
    start: z.number(),
    end: z.number(),
    text: z.string(),
    clauseId: z.string().optional(),
  })),
});

export const ExportUrlsSchema = z.object({
  highlightedPdf: z.string().url().optional(),
  summaryDocx: z.string().url().optional(),
  clausesCsv: z.string().url().optional(),
  audioNarration: z.string().url().optional(),
  transcriptSrt: z.string().url().optional(),
});

export const TranslationSchema = z.object({
  language: z.string(),
  summary: z.string(),
  audioUrl: z.string().url().optional(),
  confidence: z.number().min(0).max(1),
  translatedAt: z.string().datetime(),
});

export const ProcessedDocumentSchema = DocumentSchema.extend({
  structuredText: z.string(),
  clauses: z.array(ClauseSchema),
  summary: DocumentSummarySchema.optional(),
  riskAssessment: RiskAssessmentSchema.optional(),
  audioNarration: AudioNarrationSchema.optional(),
  exports: ExportUrlsSchema,
  translations: z.record(z.string(), TranslationSchema),
});

// TypeScript types derived from schemas
export type Document = z.infer<typeof DocumentSchema>;
export type LegalCitation = z.infer<typeof LegalCitationSchema>;
export type SaferAlternative = z.infer<typeof SaferAlternativeSchema>;
export type RoleAnalysis = z.infer<typeof RoleAnalysisSchema>;
export type Clause = z.infer<typeof ClauseSchema>;
export type DocumentSummary = z.infer<typeof DocumentSummarySchema>;
export type RiskAssessment = z.infer<typeof RiskAssessmentSchema>;
export type AudioNarration = z.infer<typeof AudioNarrationSchema>;
export type ExportUrls = z.infer<typeof ExportUrlsSchema>;
export type Translation = z.infer<typeof TranslationSchema>;
export type ProcessedDocument = z.infer<typeof ProcessedDocumentSchema>;

// Helper types
export interface ClausePosition {
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ClauseHighlight extends ClausePosition {
  clauseId: string;
  classification: ClauseClassification;
  opacity: number;
}

export interface DocumentMetadata {
  title?: string;
  author?: string;
  subject?: string;
  creator?: string;
  producer?: string;
  creationDate?: string;
  modificationDate?: string;
  keywords?: string[];
}