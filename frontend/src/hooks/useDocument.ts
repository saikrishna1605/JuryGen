import { useState, useEffect } from 'react';
import { ProcessedDocument } from '../types/document';
import api from '../utils/api';

interface UseDocumentResult {
  document: ProcessedDocument | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useDocument = (documentId: string | undefined): UseDocumentResult => {
  const [document, setDocument] = useState<ProcessedDocument | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocument = async () => {
    if (!documentId) {
      setError('No document ID provided');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await api.get(`/documents/${documentId}`);
      
      if (response.data.success) {
        setDocument(response.data.data);
      } else {
        setError(response.data.message || 'Failed to fetch document');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Failed to fetch document');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocument();
  }, [documentId]);

  return {
    document,
    isLoading,
    error,
    refetch: fetchDocument,
  };
};