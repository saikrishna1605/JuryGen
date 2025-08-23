import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PDFViewer } from '../components/pdf/PDFViewer';
import { ClauseClassification } from '../types/document';

// Mock react-pdf
vi.mock('react-pdf', () => ({
  Document: ({ children, onLoadSuccess }: any) => {
    // Simulate successful load
    setTimeout(() => onLoadSuccess({ numPages: 3 }), 100);
    return <div data-testid="pdf-document">{children}</div>;
  },
  Page: ({ pageNumber }: any) => (
    <div data-testid={`pdf-page-${pageNumber}`}>Page {pageNumber}</div>
  ),
  pdfjs: {
    GlobalWorkerOptions: { workerSrc: '' },
    version: '3.0.0',
  },
}));

const mockClauses = [
  {
    id: 'clause-1',
    text: 'This is a beneficial clause that favors the tenant.',
    clauseNumber: '1.1',
    classification: ClauseClassification.BENEFICIAL,
    riskScore: 0.2,
    impactScore: 20,
    likelihoodScore: 15,
    roleAnalysis: {},
    saferAlternatives: [],
    legalCitations: [],
    position: {
      page: 1,
      x: 100,
      y: 200,
      width: 300,
      height: 50,
    },
  },
  {
    id: 'clause-2',
    text: 'This is a risky clause that may cause problems.',
    clauseNumber: '2.1',
    classification: ClauseClassification.RISKY,
    riskScore: 0.8,
    impactScore: 85,
    likelihoodScore: 70,
    roleAnalysis: {},
    saferAlternatives: [],
    legalCitations: [],
    position: {
      page: 1,
      x: 100,
      y: 300,
      width: 300,
      height: 50,
    },
  },
];

describe('PDFViewer', () => {
  it('renders PDF viewer with toolbar', () => {
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        showAnnotations={true}
      />
    );

    // Check if toolbar elements are present
    expect(screen.getByTitle('Previous page (←)')).toBeInTheDocument();
    expect(screen.getByTitle('Next page (→)')).toBeInTheDocument();
    expect(screen.getByTitle('Zoom in (+)')).toBeInTheDocument();
    expect(screen.getByTitle('Zoom out (-)')).toBeInTheDocument();
    expect(screen.getByTitle('Rotate (R)')).toBeInTheDocument();
    expect(screen.getByTitle('Download PDF')).toBeInTheDocument();
  });

  it('displays clause annotations when enabled', async () => {
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        showAnnotations={true}
      />
    );

    // Wait for PDF to load
    await screen.findByTestId('pdf-document');

    // Check if clause annotations are rendered
    const clauseAnnotations = screen.getAllByRole('generic').filter(
      el => el.getAttribute('data-clause-id')
    );
    
    expect(clauseAnnotations).toHaveLength(2);
  });

  it('handles clause selection', async () => {
    const onClauseSelect = vi.fn();
    
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        onClauseSelect={onClauseSelect}
        showAnnotations={true}
      />
    );

    // Wait for PDF to load
    await screen.findByTestId('pdf-document');

    // Find and click a clause annotation
    const clauseAnnotation = screen.getByTestId('clause-1') || 
      document.querySelector('[data-clause-id="clause-1"]');
    
    if (clauseAnnotation) {
      fireEvent.click(clauseAnnotation);
      expect(onClauseSelect).toHaveBeenCalledWith('clause-1');
    }
  });

  it('handles zoom controls', () => {
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        showAnnotations={true}
      />
    );

    const zoomInButton = screen.getByTitle('Zoom in (+)');
    const zoomOutButton = screen.getByTitle('Zoom out (-)');

    // Test zoom in
    fireEvent.click(zoomInButton);
    expect(screen.getByText(/120%/)).toBeInTheDocument();

    // Test zoom out
    fireEvent.click(zoomOutButton);
    fireEvent.click(zoomOutButton);
    expect(screen.getByText(/83%/)).toBeInTheDocument();
  });

  it('handles page navigation', () => {
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        showAnnotations={true}
      />
    );

    const nextButton = screen.getByTitle('Next page (→)');
    const prevButton = screen.getByTitle('Previous page (←)');

    // Initially on page 1, prev should be disabled
    expect(prevButton).toBeDisabled();

    // Navigate to next page
    fireEvent.click(nextButton);
    
    // Now prev should be enabled
    expect(prevButton).not.toBeDisabled();
  });

  it('displays legend with risk classifications', () => {
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        showAnnotations={true}
      />
    );

    expect(screen.getByText('Beneficial')).toBeInTheDocument();
    expect(screen.getByText('Caution')).toBeInTheDocument();
    expect(screen.getByText('Risky')).toBeInTheDocument();
  });

  it('hides annotations when showAnnotations is false', () => {
    render(
      <PDFViewer
        fileUrl="test.pdf"
        clauses={mockClauses}
        showAnnotations={false}
      />
    );

    // Legend should not be visible
    expect(screen.queryByText('Beneficial')).not.toBeInTheDocument();
    expect(screen.queryByText('Caution')).not.toBeInTheDocument();
    expect(screen.queryByText('Risky')).not.toBeInTheDocument();
  });
});