/**
 * Unit tests for DocumentUpload component.
 * 
 * Tests file upload functionality, validation, progress tracking,
 * and error handling.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import DocumentUpload from '../DocumentUpload';
import { useAuth } from '../../hooks/useAuth';
import { documentService } from '../../services/documentService';

// Mock dependencies
vi.mock('../../hooks/useAuth');
vi.mock('../../services/documentService');

const mockUseAuth = vi.mocked(useAuth);
const mockDocumentService = vi.mocked(documentService);

// Test wrapper with React Query
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('DocumentUpload', () => {
  const mockUser = {
    uid: 'test-user-123',
    email: 'test@example.com',
    displayName: 'Test User',
  };

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: mockUser,
      loading: false,
      error: null,
      signIn: vi.fn(),
      signOut: vi.fn(),
    });

    mockDocumentService.uploadDocument.mockResolvedValue({
      status: 'success',
      document_id: 'test-doc-123',
      filename: 'test.pdf',
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload component correctly', () => {
    const Wrapper = createTestWrapper();
    
    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={vi.fn()} />
      </Wrapper>
    );

    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
    expect(screen.getByText(/browse files/i)).toBeInTheDocument();
    expect(screen.getByText(/pdf, docx, doc/i)).toBeInTheDocument();
  });

  it('handles file selection via input', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    // Create a test file
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(mockDocumentService.uploadDocument).toHaveBeenCalledWith(
        file,
        mockUser.uid
      );
    });

    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith({
        status: 'success',
        document_id: 'test-doc-123',
        filename: 'test.pdf',
      });
    });
  });

  it('handles drag and drop file upload', async () => {
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    const dropZone = screen.getByTestId('drop-zone');
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    // Simulate drag and drop
    fireEvent.dragEnter(dropZone);
    fireEvent.dragOver(dropZone);
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
      },
    });

    await waitFor(() => {
      expect(mockDocumentService.uploadDocument).toHaveBeenCalledWith(
        file,
        mockUser.uid
      );
    });
  });

  it('validates file type', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    // Create invalid file type
    const file = new File(['test content'], 'test.txt', {
      type: 'text/plain',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument();
    });

    expect(mockDocumentService.uploadDocument).not.toHaveBeenCalled();
  });

  it('validates file size', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    // Create large file (> 50MB)
    const largeContent = 'x'.repeat(51 * 1024 * 1024);
    const file = new File([largeContent], 'large.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/file too large/i)).toBeInTheDocument();
    });

    expect(mockDocumentService.uploadDocument).not.toHaveBeenCalled();
  });

  it('shows upload progress', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    // Mock upload with progress
    mockDocumentService.uploadDocument.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              status: 'success',
              document_id: 'test-doc-123',
              filename: 'test.pdf',
            });
          }, 100);
        })
    );

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    // Should show uploading state
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalled();
    });
  });

  it('handles upload errors', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    // Mock upload error
    mockDocumentService.uploadDocument.mockRejectedValue(
      new Error('Upload failed')
    );

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
    });

    expect(onUploadComplete).not.toHaveBeenCalled();
  });

  it('supports multiple file upload', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} multiple />
      </Wrapper>
    );

    const files = [
      new File(['content 1'], 'test1.pdf', { type: 'application/pdf' }),
      new File(['content 2'], 'test2.pdf', { type: 'application/pdf' }),
    ];

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, files);

    await waitFor(() => {
      expect(mockDocumentService.uploadDocument).toHaveBeenCalledTimes(2);
    });
  });

  it('shows file preview before upload', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} showPreview />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    // Should show file preview
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(screen.getByText(/application\/pdf/i)).toBeInTheDocument();
    
    // Should show upload button
    const uploadButton = screen.getByText(/upload/i);
    expect(uploadButton).toBeInTheDocument();

    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockDocumentService.uploadDocument).toHaveBeenCalled();
    });
  });

  it('allows file removal from preview', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} showPreview />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    // Should show remove button
    const removeButton = screen.getByLabelText(/remove file/i);
    await user.click(removeButton);

    // File should be removed
    expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
  });

  it('handles authentication errors', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    // Mock unauthenticated user
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      error: null,
      signIn: vi.fn(),
      signOut: vi.fn(),
    });

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/please sign in/i)).toBeInTheDocument();
    });

    expect(mockDocumentService.uploadDocument).not.toHaveBeenCalled();
  });

  it('supports custom file types', () => {
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    render(
      <Wrapper>
        <DocumentUpload
          onUploadComplete={onUploadComplete}
          acceptedTypes={['image/jpeg', 'image/png']}
        />
      </Wrapper>
    );

    expect(screen.getByText(/jpeg, png/i)).toBeInTheDocument();
  });

  it('shows upload queue for multiple files', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    // Mock delayed uploads
    mockDocumentService.uploadDocument
      .mockResolvedValueOnce({
        status: 'success',
        document_id: 'doc-1',
        filename: 'test1.pdf',
      })
      .mockResolvedValueOnce({
        status: 'success',
        document_id: 'doc-2',
        filename: 'test2.pdf',
      });

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} multiple showQueue />
      </Wrapper>
    );

    const files = [
      new File(['content 1'], 'test1.pdf', { type: 'application/pdf' }),
      new File(['content 2'], 'test2.pdf', { type: 'application/pdf' }),
    ];

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, files);

    // Should show upload queue
    expect(screen.getByText(/upload queue/i)).toBeInTheDocument();
    expect(screen.getByText('test1.pdf')).toBeInTheDocument();
    expect(screen.getByText('test2.pdf')).toBeInTheDocument();
  });

  it('handles network errors gracefully', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    // Mock network error
    mockDocumentService.uploadDocument.mockRejectedValue(
      new Error('Network error')
    );

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });

    // Should show retry button
    const retryButton = screen.getByText(/retry/i);
    expect(retryButton).toBeInTheDocument();
  });

  it('supports upload cancellation', async () => {
    const user = userEvent.setup();
    const onUploadComplete = vi.fn();
    const Wrapper = createTestWrapper();

    // Mock long upload
    const abortController = new AbortController();
    mockDocumentService.uploadDocument.mockImplementation(
      () =>
        new Promise((resolve, reject) => {
          abortController.signal.addEventListener('abort', () => {
            reject(new Error('Upload cancelled'));
          });
          setTimeout(resolve, 5000);
        })
    );

    render(
      <Wrapper>
        <DocumentUpload onUploadComplete={onUploadComplete} />
      </Wrapper>
    );

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByLabelText(/browse files/i);
    await user.upload(fileInput, file);

    // Should show cancel button during upload
    const cancelButton = await screen.findByText(/cancel/i);
    await user.click(cancelButton);

    await waitFor(() => {
      expect(screen.getByText(/upload cancelled/i)).toBeInTheDocument();
    });
  });
});