import { apiClient } from '../lib/api';

export interface PIIFinding {
  start: number;
  end: number;
  type: string;
  text: string;
  likelihood: string;
  confidence: number;
  suggested_masking: string;
  masked_text?: string;
}

export interface PIIPreview {
  original_content: string;
  pii_locations: PIIFinding[];
  summary: {
    total_findings: number;
    by_type: Record<string, number>;
    risk_level: 'low' | 'medium' | 'high';
  };
}

export interface MaskingConfig {
  [piiType: string]: 'redact' | 'mask' | 'hash' | 'replace' | 'partial';
}

export interface PIIDetectionRequest {
  content: string;
  content_type?: string;
  info_types?: string[];
  min_likelihood?: string;
  create_preview?: boolean;
}

export interface PIIMaskingRequest {
  content: string;
  findings: PIIFinding[];
  masking_config?: MaskingConfig;
}

export interface PIIMaskingResponse {
  masked_content: string;
  findings: PIIFinding[];
  validation: {
    is_valid: boolean;
    issues: Array<{
      type: string;
      message?: string;
      pii_type?: string;
      text?: string;
    }>;
    coverage: number;
    leakage_detected: boolean;
  };
}

export interface ComplianceReport {
  period: {
    start: string | null;
    end: string | null;
  };
  summary: {
    total_operations: number;
    unique_users: number;
    unique_documents: number;
    total_pii_findings: number;
  };
  by_action: Record<string, number>;
  by_pii_type: Record<string, number>;
  high_risk_activities: Array<{
    timestamp: string;
    user_id: string;
    document_id: string;
    action: string;
    high_confidence_findings: number;
  }>;
}

class PIIService {
  /**
   * Detect PII in content and optionally create preview
   */
  async detectPII(request: PIIDetectionRequest): Promise<PIIPreview> {
    const response = await apiClient.post<PIIPreview>('/pii/detect', request);
    return response.data;
  }

  /**
   * Apply masking to detected PII
   */
  async maskPII(request: PIIMaskingRequest): Promise<PIIMaskingResponse> {
    const response = await apiClient.post<PIIMaskingResponse>('/pii/mask', request);
    return response.data;
  }

  /**
   * Detect and mask PII in one operation
   */
  async detectAndMaskPII(
    content: string,
    options: {
      content_type?: string;
      info_types?: string[];
      masking_config?: MaskingConfig;
      min_likelihood?: string;
    } = {}
  ): Promise<PIIMaskingResponse> {
    const response = await apiClient.post<PIIMaskingResponse>('/pii/detect-and-mask', {
      content,
      ...options
    });
    return response.data;
  }

  /**
   * Create redaction preview for client-side review
   */
  async createRedactionPreview(
    content: string,
    findings: PIIFinding[]
  ): Promise<PIIPreview> {
    const response = await apiClient.post<PIIPreview>('/pii/preview', {
      content,
      findings
    });
    return response.data;
  }

  /**
   * Validate masking quality
   */
  async validateMasking(
    originalContent: string,
    maskedContent: string,
    findings: PIIFinding[]
  ): Promise<{
    is_valid: boolean;
    issues: Array<{
      type: string;
      message?: string;
      pii_type?: string;
      text?: string;
    }>;
    coverage: number;
    leakage_detected: boolean;
  }> {
    const response = await apiClient.post('/pii/validate', {
      original_content: originalContent,
      masked_content: maskedContent,
      findings
    });
    return response.data;
  }

  /**
   * Get compliance report for PII processing activities
   */
  async getComplianceReport(options: {
    user_id?: string;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<ComplianceReport> {
    const params = new URLSearchParams();
    if (options.user_id) params.append('user_id', options.user_id);
    if (options.start_date) params.append('start_date', options.start_date);
    if (options.end_date) params.append('end_date', options.end_date);

    const response = await apiClient.get<ComplianceReport>(
      `/pii/compliance-report?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Get supported PII types
   */
  getSupportedPIITypes(): Array<{
    type: string;
    name: string;
    description: string;
    risk_level: 'low' | 'medium' | 'high';
  }> {
    return [
      {
        type: 'EMAIL_ADDRESS',
        name: 'Email Address',
        description: 'Email addresses',
        risk_level: 'low'
      },
      {
        type: 'PHONE_NUMBER',
        name: 'Phone Number',
        description: 'Phone numbers',
        risk_level: 'low'
      },
      {
        type: 'PERSON_NAME',
        name: 'Person Name',
        description: 'Names of individuals',
        risk_level: 'medium'
      },
      {
        type: 'US_SOCIAL_SECURITY_NUMBER',
        name: 'Social Security Number',
        description: 'US Social Security Numbers',
        risk_level: 'high'
      },
      {
        type: 'CREDIT_CARD_NUMBER',
        name: 'Credit Card Number',
        description: 'Credit card numbers',
        risk_level: 'high'
      },
      {
        type: 'DATE_OF_BIRTH',
        name: 'Date of Birth',
        description: 'Birth dates',
        risk_level: 'medium'
      },
      {
        type: 'STREET_ADDRESS',
        name: 'Street Address',
        description: 'Physical addresses',
        risk_level: 'medium'
      },
      {
        type: 'PASSPORT',
        name: 'Passport Number',
        description: 'Passport numbers',
        risk_level: 'high'
      },
      {
        type: 'US_DRIVERS_LICENSE_NUMBER',
        name: 'Driver License',
        description: 'US driver license numbers',
        risk_level: 'high'
      },
      {
        type: 'US_BANK_ROUTING_MICR',
        name: 'Bank Account',
        description: 'Bank routing and account numbers',
        risk_level: 'high'
      },
      {
        type: 'IP_ADDRESS',
        name: 'IP Address',
        description: 'IP addresses',
        risk_level: 'low'
      },
      {
        type: 'MEDICAL_RECORD_NUMBER',
        name: 'Medical Record',
        description: 'Medical record numbers',
        risk_level: 'high'
      },
      {
        type: 'US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER',
        name: 'Tax ID',
        description: 'US Individual Taxpayer ID',
        risk_level: 'high'
      }
    ];
  }

  /**
   * Get masking type descriptions
   */
  getMaskingTypes(): Array<{
    type: string;
    name: string;
    description: string;
    example: string;
  }> {
    return [
      {
        type: 'redact',
        name: 'Redact',
        description: 'Completely remove the PII',
        example: '[REDACTED]'
      },
      {
        type: 'mask',
        name: 'Mask',
        description: 'Replace with asterisks',
        example: '***********'
      },
      {
        type: 'hash',
        name: 'Hash',
        description: 'Replace with cryptographic hash',
        example: '[HASH:a1b2c3d4]'
      },
      {
        type: 'replace',
        name: 'Replace',
        description: 'Replace with generic label',
        example: '[EMAIL], [NAME], [PHONE]'
      },
      {
        type: 'partial',
        name: 'Partial',
        description: 'Show first and last characters',
        example: 'jo***@ex*****.com'
      }
    ];
  }

  /**
   * Get recommended masking configuration for different contexts
   */
  getRecommendedMaskingConfig(context: 'legal' | 'medical' | 'financial' | 'general'): MaskingConfig {
    const configs = {
      legal: {
        'EMAIL_ADDRESS': 'partial',
        'PHONE_NUMBER': 'partial',
        'PERSON_NAME': 'replace',
        'US_SOCIAL_SECURITY_NUMBER': 'mask',
        'CREDIT_CARD_NUMBER': 'mask',
        'DATE_OF_BIRTH': 'partial',
        'STREET_ADDRESS': 'replace',
        'PASSPORT': 'mask',
        'US_DRIVERS_LICENSE_NUMBER': 'mask',
        'US_BANK_ROUTING_MICR': 'mask',
        'IP_ADDRESS': 'mask',
        'MEDICAL_RECORD_NUMBER': 'mask',
        'US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER': 'mask'
      },
      medical: {
        'EMAIL_ADDRESS': 'partial',
        'PHONE_NUMBER': 'partial',
        'PERSON_NAME': 'replace',
        'US_SOCIAL_SECURITY_NUMBER': 'redact',
        'CREDIT_CARD_NUMBER': 'redact',
        'DATE_OF_BIRTH': 'replace',
        'STREET_ADDRESS': 'replace',
        'PASSPORT': 'redact',
        'US_DRIVERS_LICENSE_NUMBER': 'redact',
        'US_BANK_ROUTING_MICR': 'redact',
        'IP_ADDRESS': 'mask',
        'MEDICAL_RECORD_NUMBER': 'replace',
        'US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER': 'redact'
      },
      financial: {
        'EMAIL_ADDRESS': 'partial',
        'PHONE_NUMBER': 'partial',
        'PERSON_NAME': 'replace',
        'US_SOCIAL_SECURITY_NUMBER': 'redact',
        'CREDIT_CARD_NUMBER': 'redact',
        'DATE_OF_BIRTH': 'partial',
        'STREET_ADDRESS': 'replace',
        'PASSPORT': 'redact',
        'US_DRIVERS_LICENSE_NUMBER': 'mask',
        'US_BANK_ROUTING_MICR': 'redact',
        'IP_ADDRESS': 'mask',
        'MEDICAL_RECORD_NUMBER': 'redact',
        'US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER': 'redact'
      },
      general: {
        'EMAIL_ADDRESS': 'partial',
        'PHONE_NUMBER': 'partial',
        'PERSON_NAME': 'replace',
        'US_SOCIAL_SECURITY_NUMBER': 'mask',
        'CREDIT_CARD_NUMBER': 'mask',
        'DATE_OF_BIRTH': 'partial',
        'STREET_ADDRESS': 'replace',
        'PASSPORT': 'mask',
        'US_DRIVERS_LICENSE_NUMBER': 'mask',
        'US_BANK_ROUTING_MICR': 'mask',
        'IP_ADDRESS': 'mask',
        'MEDICAL_RECORD_NUMBER': 'mask',
        'US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER': 'mask'
      }
    };

    return configs[context] as MaskingConfig;
  }
}

export const piiService = new PIIService();