import api from '../lib/api';

export interface QAResponse {
  question: string;
  answer: string;
  confidence: number;
  sources: Array<{
    type: string;
    content: string;
  }>;
  audioResponse?: {
    audioContentBase64: string;
    voiceName: string;
    languageCode: string;
    audioFormat: string;
    duration: number;
  };
  processingTime: number;
  contextUsed: string[];
  createdAt: string;
}

export interface ConversationHistory {
  interactions: Array<{
    timestamp: string;
    question: string;
    answer: string;
    confidence: number;
  }>;
  sessionId: string;
  documentId: string;
  totalInteractions: number;
}

export interface VoiceQAOptions {
  languageCode?: string;
  voiceGender?: 'MALE' | 'FEMALE' | 'NEUTRAL';
  speakingRate?: number;
  sessionId?: string;
}

export interface TextQAOptions {
  sessionId?: string;
}

class QAService {
  /**
   * Ask a text question about a document
   */
  async askTextQuestion(
    question: string,
    documentId: string,
    options: TextQAOptions = {}
  ): Promise<QAResponse> {
    const response = await api.post('/qa/ask', {
      question,
      document_id: documentId,
      session_id: options.sessionId,
    });

    return response.data.data;
  }

  /**
   * Ask a voice question about a document
   */
  async askVoiceQuestion(
    audioFile: File,
    documentId: string,
    options: VoiceQAOptions = {}
  ): Promise<QAResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('document_id', documentId);
    
    if (options.sessionId) {
      formData.append('session_id', options.sessionId);
    }
    if (options.languageCode) {
      formData.append('language_code', options.languageCode);
    }
    if (options.voiceGender) {
      formData.append('voice_gender', options.voiceGender);
    }
    if (options.speakingRate) {
      formData.append('speaking_rate', options.speakingRate.toString());
    }

    const response = await api.post('/qa/ask-voice', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Get conversation history for a session
   */
  async getConversationHistory(
    documentId: string,
    sessionId: string
  ): Promise<ConversationHistory> {
    const response = await api.get(`/qa/sessions/${documentId}/history`, {
      params: { session_id: sessionId },
    });

    return response.data.data;
  }

  /**
   * Clear a conversation session
   */
  async clearSession(documentId: string, sessionId: string): Promise<void> {
    await api.delete(`/qa/sessions/${documentId}/clear`, {
      params: { session_id: sessionId },
    });
  }

  /**
   * Get suggested questions for a document
   */
  async getSuggestedQuestions(
    documentId: string,
    context?: string
  ): Promise<string[]> {
    const formData = new FormData();
    formData.append('document_id', documentId);
    if (context) {
      formData.append('context', context);
    }

    const response = await api.post('/qa/suggest-questions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data.data;
  }

  /**
   * Check Q&A service health
   */
  async healthCheck(): Promise<any> {
    const response = await api.get('/qa/health');
    return response.data.data;
  }

  /**
   * Generate a unique session ID
   */
  generateSessionId(documentId: string, userId?: string): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    const userPart = userId ? userId.substring(0, 8) : 'anon';
    const docPart = documentId.substring(0, 8);
    
    return `${userPart}_${docPart}_${timestamp}_${random}`;
  }

  /**
   * Estimate question complexity (for UI purposes)
   */
  estimateQuestionComplexity(question: string): 'simple' | 'moderate' | 'complex' {
    const words = question.trim().split(/\s+/).length;
    const hasLegalTerms = /\b(contract|agreement|clause|liability|obligation|breach|terminate|penalty|damages|jurisdiction|arbitration|indemnify|warranty|covenant|consideration)\b/i.test(question);
    const hasComplexStructure = /\b(if|when|unless|provided that|notwithstanding|whereas|therefore|furthermore|however|nevertheless)\b/i.test(question);

    if (words > 20 || (hasLegalTerms && hasComplexStructure)) {
      return 'complex';
    } else if (words > 10 || hasLegalTerms || hasComplexStructure) {
      return 'moderate';
    } else {
      return 'simple';
    }
  }

  /**
   * Format confidence score for display
   */
  formatConfidence(confidence: number): string {
    const percentage = Math.round(confidence * 100);
    if (percentage >= 90) return `${percentage}% (Very High)`;
    if (percentage >= 80) return `${percentage}% (High)`;
    if (percentage >= 70) return `${percentage}% (Good)`;
    if (percentage >= 60) return `${percentage}% (Moderate)`;
    return `${percentage}% (Low)`;
  }

  /**
   * Get confidence color for UI
   */
  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  }

  /**
   * Validate question before sending
   */
  validateQuestion(question: string): { valid: boolean; error?: string } {
    const trimmed = question.trim();
    
    if (!trimmed) {
      return { valid: false, error: 'Question cannot be empty' };
    }
    
    if (trimmed.length < 3) {
      return { valid: false, error: 'Question is too short' };
    }
    
    if (trimmed.length > 1000) {
      return { valid: false, error: 'Question is too long (max 1000 characters)' };
    }
    
    // Check for potentially inappropriate content
    const inappropriatePatterns = [
      /\b(hack|crack|bypass|exploit)\b/i,
      /\b(illegal|unlawful|criminal)\b/i,
    ];
    
    for (const pattern of inappropriatePatterns) {
      if (pattern.test(trimmed)) {
        return { valid: false, error: 'Question contains inappropriate content' };
      }
    }
    
    return { valid: true };
  }

  /**
   * Extract key topics from a question
   */
  extractKeyTopics(question: string): string[] {
    const topics: string[] = [];
    
    // Legal concepts
    const legalConcepts = [
      'contract', 'agreement', 'clause', 'liability', 'obligation', 'breach',
      'terminate', 'penalty', 'damages', 'jurisdiction', 'arbitration',
      'indemnify', 'warranty', 'covenant', 'consideration', 'force majeure',
      'confidentiality', 'non-disclosure', 'intellectual property', 'copyright',
      'trademark', 'patent', 'licensing', 'royalty', 'assignment', 'sublicense'
    ];
    
    // Financial terms
    const financialTerms = [
      'payment', 'fee', 'cost', 'price', 'invoice', 'billing', 'refund',
      'deposit', 'escrow', 'interest', 'late fee', 'penalty', 'discount',
      'tax', 'expense', 'reimbursement', 'budget', 'financial'
    ];
    
    // Time-related terms
    const timeTerms = [
      'deadline', 'due date', 'expiration', 'renewal', 'term', 'duration',
      'notice period', 'grace period', 'extension', 'schedule', 'timeline'
    ];
    
    const questionLower = question.toLowerCase();
    
    // Check for legal concepts
    legalConcepts.forEach(concept => {
      if (questionLower.includes(concept)) {
        topics.push('legal');
      }
    });
    
    // Check for financial terms
    financialTerms.forEach(term => {
      if (questionLower.includes(term)) {
        topics.push('financial');
      }
    });
    
    // Check for time-related terms
    timeTerms.forEach(term => {
      if (questionLower.includes(term)) {
        topics.push('temporal');
      }
    });
    
    // Check for risk-related questions
    if (/\b(risk|danger|problem|issue|concern|warning|caution)\b/i.test(question)) {
      topics.push('risk');
    }
    
    // Check for definition requests
    if (/\b(what is|define|meaning|means|definition)\b/i.test(question)) {
      topics.push('definition');
    }
    
    // Check for procedural questions
    if (/\b(how to|process|procedure|steps|method)\b/i.test(question)) {
      topics.push('procedural');
    }
    
    return [...new Set(topics)]; // Remove duplicates
  }

  /**
   * Generate follow-up questions based on the response
   */
  generateFollowUpQuestions(response: QAResponse): string[] {
    const followUps: string[] = [];
    const answer = response.answer.toLowerCase();
    
    // If response mentions risks
    if (answer.includes('risk') || answer.includes('danger') || answer.includes('problem')) {
      followUps.push('How can I mitigate these risks?');
      followUps.push('What are the consequences if these risks occur?');
    }
    
    // If response mentions obligations
    if (answer.includes('obligation') || answer.includes('must') || answer.includes('required')) {
      followUps.push('What happens if I don\'t fulfill these obligations?');
      followUps.push('Are there any exceptions to these obligations?');
    }
    
    // If response mentions deadlines or dates
    if (answer.includes('deadline') || answer.includes('date') || answer.includes('day')) {
      followUps.push('Can these deadlines be extended?');
      followUps.push('What happens if I miss these deadlines?');
    }
    
    // If response mentions payments or fees
    if (answer.includes('payment') || answer.includes('fee') || answer.includes('cost')) {
      followUps.push('Are there any additional fees I should know about?');
      followUps.push('What are the payment terms and methods?');
    }
    
    // If response mentions termination
    if (answer.includes('terminate') || answer.includes('end') || answer.includes('cancel')) {
      followUps.push('What is the process for termination?');
      followUps.push('Are there any penalties for early termination?');
    }
    
    // Generic follow-ups based on confidence
    if (response.confidence < 0.7) {
      followUps.push('Can you provide more specific information about this?');
      followUps.push('Are there any related clauses I should review?');
    }
    
    return followUps.slice(0, 3); // Return max 3 follow-ups
  }
}

export const qaService = new QAService();