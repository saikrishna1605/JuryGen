import { z } from 'zod';
import { UserRole } from './document';

// User-related enums
export enum AuthProvider {
  GOOGLE = 'google',
  EMAIL = 'email',
  PHONE = 'phone',
  ANONYMOUS = 'anonymous',
}

export enum SubscriptionTier {
  FREE = 'free',
  BASIC = 'basic',
  PREMIUM = 'premium',
  ENTERPRISE = 'enterprise',
}

export enum AccessibilityFeature {
  HIGH_CONTRAST = 'high_contrast',
  LARGE_FONTS = 'large_fonts',
  DYSLEXIC_FONT = 'dyslexic_font',
  SCREEN_READER = 'screen_reader',
  KEYBOARD_NAVIGATION = 'keyboard_navigation',
  REDUCED_MOTION = 'reduced_motion',
}

// Zod schemas
export const AccessibilitySettingsSchema = z.object({
  enabledFeatures: z.array(z.nativeEnum(AccessibilityFeature)).default([]),
  fontSize: z.enum(['small', 'medium', 'large', 'extra-large']).default('medium'),
  contrast: z.enum(['normal', 'high', 'extra-high']).default('normal'),
  colorScheme: z.enum(['light', 'dark', 'auto']).default('auto'),
  reducedMotion: z.boolean().default(false),
  screenReaderOptimized: z.boolean().default(false),
  keyboardNavigationOnly: z.boolean().default(false),
});

export const UserPreferencesSchema = z.object({
  language: z.string().default('en'),
  jurisdiction: z.string().optional(),
  defaultRole: z.nativeEnum(UserRole).optional(),
  timezone: z.string().default('UTC'),
  dateFormat: z.enum(['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD']).default('MM/DD/YYYY'),
  timeFormat: z.enum(['12h', '24h']).default('12h'),
  currency: z.string().default('USD'),
  notifications: z.object({
    email: z.boolean().default(true),
    push: z.boolean().default(true),
    sms: z.boolean().default(false),
    jobCompletion: z.boolean().default(true),
    securityAlerts: z.boolean().default(true),
    marketingEmails: z.boolean().default(false),
  }).default({}),
  privacy: z.object({
    allowAnalytics: z.boolean().default(false),
    allowModelTraining: z.boolean().default(false),
    shareUsageData: z.boolean().default(false),
    dataRetentionDays: z.number().min(1).max(365).default(30),
  }).default({}),
  accessibility: AccessibilitySettingsSchema.default({}),
});

export const UserUsageSchema = z.object({
  documentsProcessed: z.number().nonnegative().default(0),
  totalTokensUsed: z.number().nonnegative().default(0),
  apiCallsThisMonth: z.number().nonnegative().default(0),
  storageUsedBytes: z.number().nonnegative().default(0),
  lastActiveAt: z.string().datetime().optional(),
  monthlyLimits: z.object({
    documents: z.number().positive().default(10),
    tokens: z.number().positive().default(100000),
    apiCalls: z.number().positive().default(1000),
    storageBytes: z.number().positive().default(1024 * 1024 * 1024), // 1GB
  }).default({}),
});

export const UserSubscriptionSchema = z.object({
  tier: z.nativeEnum(SubscriptionTier).default(SubscriptionTier.FREE),
  status: z.enum(['active', 'inactive', 'cancelled', 'past_due']).default('active'),
  startDate: z.string().datetime().optional(),
  endDate: z.string().datetime().optional(),
  autoRenew: z.boolean().default(false),
  paymentMethod: z.string().optional(),
  billingCycle: z.enum(['monthly', 'yearly']).optional(),
});

export const UserSchema = z.object({
  uid: z.string(),
  email: z.string().email().optional(),
  emailVerified: z.boolean().default(false),
  displayName: z.string().optional(),
  photoURL: z.string().url().optional(),
  phoneNumber: z.string().optional(),
  provider: z.nativeEnum(AuthProvider),
  isAnonymous: z.boolean().default(false),
  createdAt: z.string().datetime(),
  lastLoginAt: z.string().datetime().optional(),
  preferences: UserPreferencesSchema.default({}),
  usage: UserUsageSchema.default({}),
  subscription: UserSubscriptionSchema.default({}),
  roles: z.array(z.string()).default(['user']),
  permissions: z.array(z.string()).default([]),
  isActive: z.boolean().default(true),
  metadata: z.record(z.any()).default({}),
});

export const AuthStateSchema = z.object({
  isAuthenticated: z.boolean(),
  isLoading: z.boolean(),
  user: UserSchema.optional(),
  token: z.string().optional(),
  refreshToken: z.string().optional(),
  expiresAt: z.string().datetime().optional(),
  error: z.string().optional(),
});

export const LoginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  rememberMe: z.boolean().default(false),
});

export const RegisterRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
    'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
  ),
  displayName: z.string().min(2).max(50),
  acceptTerms: z.boolean().refine(val => val === true, 'Must accept terms and conditions'),
  preferences: UserPreferencesSchema.optional(),
});

export const PasswordResetRequestSchema = z.object({
  email: z.string().email(),
});

export const UpdateProfileRequestSchema = z.object({
  displayName: z.string().min(2).max(50).optional(),
  photoURL: z.string().url().optional(),
  preferences: UserPreferencesSchema.optional(),
});

// TypeScript types
export type AccessibilitySettings = z.infer<typeof AccessibilitySettingsSchema>;
export type UserPreferences = z.infer<typeof UserPreferencesSchema>;
export type UserUsage = z.infer<typeof UserUsageSchema>;
export type UserSubscription = z.infer<typeof UserSubscriptionSchema>;
export type User = z.infer<typeof UserSchema>;
export type AuthState = z.infer<typeof AuthStateSchema>;
export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type PasswordResetRequest = z.infer<typeof PasswordResetRequestSchema>;
export type UpdateProfileRequest = z.infer<typeof UpdateProfileRequestSchema>;

// Helper types
export interface UserSession {
  user: User;
  token: string;
  expiresAt: Date;
  refreshToken?: string;
}

export interface UserActivity {
  timestamp: string;
  action: string;
  resource?: string;
  metadata?: Record<string, any>;
}

export interface UserStats {
  totalDocuments: number;
  totalClauses: number;
  averageRiskScore: number;
  mostCommonRole: UserRole;
  favoriteJurisdiction: string;
  timeSpentMinutes: number;
}

// Subscription limits by tier
export const SUBSCRIPTION_LIMITS: Record<SubscriptionTier, UserUsage['monthlyLimits']> = {
  [SubscriptionTier.FREE]: {
    documents: 5,
    tokens: 50000,
    apiCalls: 500,
    storageBytes: 100 * 1024 * 1024, // 100MB
  },
  [SubscriptionTier.BASIC]: {
    documents: 25,
    tokens: 250000,
    apiCalls: 2500,
    storageBytes: 500 * 1024 * 1024, // 500MB
  },
  [SubscriptionTier.PREMIUM]: {
    documents: 100,
    tokens: 1000000,
    apiCalls: 10000,
    storageBytes: 2 * 1024 * 1024 * 1024, // 2GB
  },
  [SubscriptionTier.ENTERPRISE]: {
    documents: 1000,
    tokens: 10000000,
    apiCalls: 100000,
    storageBytes: 10 * 1024 * 1024 * 1024, // 10GB
  },
};

// Helper functions
export const hasPermission = (user: User, permission: string): boolean => {
  return user.permissions.includes(permission) || user.roles.includes('admin');
};

export const isSubscriptionActive = (subscription: UserSubscription): boolean => {
  return subscription.status === 'active' && 
         (!subscription.endDate || new Date(subscription.endDate) > new Date());
};

export const getRemainingUsage = (usage: UserUsage): Partial<UserUsage['monthlyLimits']> => {
  const limits = usage.monthlyLimits;
  return {
    documents: Math.max(0, limits.documents - usage.documentsProcessed),
    tokens: Math.max(0, limits.tokens - usage.totalTokensUsed),
    apiCalls: Math.max(0, limits.apiCalls - usage.apiCallsThisMonth),
    storageBytes: Math.max(0, limits.storageBytes - usage.storageUsedBytes),
  };
};