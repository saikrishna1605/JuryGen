import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ZoomIn, ZoomOut, RotateCw, Download, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Clause, ClauseClassification } from '../../types/document';
import { cn } from '../../utils';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

interface PDFViewerProps {
  fileUrl: string;
  clauses?: Clause[];
  selectedClauseId?: string;
  onClauseSelect?: (clauseId: string) => void;
  onClauseHover?: (clauseId: string | null) => void;
  showAnnotations?: boolean;
  className?: string;
}

interface ViewerState {
  numPages: number;
  currentPage: number;
  scale: number;
  rotation: number;
  isLoading: boolean;
  error: string | null;
}

const RISK_COLORS = {
  [ClauseClassification.BENEFICIAL]: {
    background: 'rgba(34, 197, 94, 0.2)', // green-500 with opacity
    border: 'rgb(34, 197, 94)',
    hover: 'rgba(34, 197, 94, 0.3)',
  },
  [ClauseClassification.CAUTION]: {
    background: 'rgba(251, 191, 36, 0.2)', // yellow-500 with opacity
    border: 'rgb(251, 191, 36)',
    hover: 'rgba(251, 191, 36, 0.3)',
  },
  [ClauseClassification.RISKY]: {
    background: 'rgba(239, 68, 68, 0.2)', // red-500 with opacity
    border: 'rgb(239, 68, 68)',
    hover: 'rgba(239, 68, 68, 0.3)',
  },
};

export const PDFViewer: React.FC<PDFViewerProps> = ({
  fileUrl,
  clauses = [],
  selectedClauseId,
  onClauseSelect,
  onClauseHover,
  showAnnotations = true,
  className,
}) => {
  const [viewerState, setViewerState] = useState<ViewerState>({
    numPages: 0,
    currentPage: 1,
    scale: 1.0,
    rotation: 0,
    isLoading: true,
    error: null,
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [hoveredClauseId, setHoveredClauseId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Get clauses for current page
  const getCurrentPageClauses = useCallback(() => {
    return clauses.filter(clause => 
      clause.position && clause.position.page === viewerState.currentPage
    );
  }, [clauses, viewerState.currentPage]);

  // Handle document load success
  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setViewerState(prev => ({
      ...prev,
      numPages,
      isLoading: false,
      error: null,
    }));
  }, []);

  // Handle document load error
  const onDocumentLoadError = useCallback((error: Error) => {
    setViewerState(prev => ({
      ...prev,
      isLoading: false,
      error: error.message,
    }));
  }, []);

  // Navigation functions
  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= viewerState.numPages) {
      setViewerState(prev => ({ ...prev, currentPage: page }));
    }
  }, [viewerState.numPages]);

  const nextPage = useCallback(() => {
    goToPage(viewerState.currentPage + 1);
  }, [goToPage, viewerState.currentPage]);

  const prevPage = useCallback(() => {
    goToPage(viewerState.currentPage - 1);
  }, [goToPage, viewerState.currentPage]);

  // Zoom functions
  const zoomIn = useCallback(() => {
    setViewerState(prev => ({
      ...prev,
      scale: Math.min(prev.scale * 1.2, 3.0),
    }));
  }, []);

  const zoomOut = useCallback(() => {
    setViewerState(prev => ({
      ...prev,
      scale: Math.max(prev.scale / 1.2, 0.5),
    }));
  }, []);

  const resetZoom = useCallback(() => {
    setViewerState(prev => ({ ...prev, scale: 1.0 }));
  }, []);

  // Rotation function
  const rotate = useCallback(() => {
    setViewerState(prev => ({
      ...prev,
      rotation: (prev.rotation + 90) % 360,
    }));
  }, []);

  // Handle clause click
  const handleClauseClick = useCallback((clauseId: string) => {
    onClauseSelect?.(clauseId);
  }, [onClauseSelect]);

  // Handle clause hover
  const handleClauseHover = useCallback((clauseId: string | null) => {
    setHoveredClauseId(clauseId);
    onClauseHover?.(clauseId);
  }, [onClauseHover]);

  // Navigate to clause
  const navigateToClause = useCallback((clauseId: string) => {
    const clause = clauses.find(c => c.id === clauseId);
    if (clause?.position) {
      goToPage(clause.position.page);
      // Scroll to clause position after page loads
      setTimeout(() => {
        const pageElement = pageRefs.current.get(clause.position!.page);
        if (pageElement) {
          const clauseElement = pageElement.querySelector(`[data-clause-id="${clauseId}"]`);
          clauseElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  }, [clauses, goToPage]);

  // Effect to navigate to selected clause
  useEffect(() => {
    if (selectedClauseId) {
      navigateToClause(selectedClauseId);
    }
  }, [selectedClauseId, navigateToClause]);

  // Render clause annotations
  const renderClauseAnnotations = useCallback((pageNumber: number) => {
    if (!showAnnotations) return null;

    const pageClauses = clauses.filter(clause => 
      clause.position && clause.position.page === pageNumber
    );

    return pageClauses.map(clause => {
      if (!clause.position) return null;

      const isSelected = selectedClauseId === clause.id;
      const isHovered = hoveredClauseId === clause.id;
      const colors = RISK_COLORS[clause.classification];

      return (
        <div
          key={clause.id}
          data-clause-id={clause.id}
          className={cn(
            'absolute cursor-pointer transition-all duration-200 border-2 rounded',
            isSelected && 'ring-2 ring-blue-500 ring-offset-2',
            'hover:shadow-lg'
          )}
          style={{
            left: `${clause.position.x * viewerState.scale}px`,
            top: `${clause.position.y * viewerState.scale}px`,
            width: `${clause.position.width * viewerState.scale}px`,
            height: `${clause.position.height * viewerState.scale}px`,
            backgroundColor: isHovered ? colors.hover : colors.background,
            borderColor: colors.border,
            zIndex: isSelected ? 20 : isHovered ? 15 : 10,
          }}
          onClick={() => handleClauseClick(clause.id)}
          onMouseEnter={() => handleClauseHover(clause.id)}
          onMouseLeave={() => handleClauseHover(null)}
          title={`${clause.classification.toUpperCase()}: ${clause.text.substring(0, 100)}...`}
        />
      );
    });
  }, [
    showAnnotations,
    clauses,
    selectedClauseId,
    hoveredClauseId,
    viewerState.scale,
    handleClauseClick,
    handleClauseHover,
  ]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return;

      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          prevPage();
          break;
        case 'ArrowRight':
          event.preventDefault();
          nextPage();
          break;
        case '+':
        case '=':
          event.preventDefault();
          zoomIn();
          break;
        case '-':
          event.preventDefault();
          zoomOut();
          break;
        case '0':
          event.preventDefault();
          resetZoom();
          break;
        case 'r':
          event.preventDefault();
          rotate();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [prevPage, nextPage, zoomIn, zoomOut, resetZoom, rotate]);

  if (viewerState.error) {
    return (
      <div className={cn('flex items-center justify-center h-96 bg-gray-50 rounded-lg', className)}>
        <div className="text-center">
          <div className="text-red-500 text-lg font-semibold mb-2">Error loading PDF</div>
          <div className="text-gray-600">{viewerState.error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col h-full bg-gray-100', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-white border-b shadow-sm">
        <div className="flex items-center space-x-2">
          {/* Navigation */}
          <button
            onClick={prevPage}
            disabled={viewerState.currentPage <= 1}
            className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Previous page (←)"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <div className="flex items-center space-x-2">
            <input
              type="number"
              value={viewerState.currentPage}
              onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
              className="w-16 px-2 py-1 text-center border rounded"
              min={1}
              max={viewerState.numPages}
            />
            <span className="text-sm text-gray-600">
              of {viewerState.numPages}
            </span>
          </div>

          <button
            onClick={nextPage}
            disabled={viewerState.currentPage >= viewerState.numPages}
            className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Next page (→)"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Zoom and rotation controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={zoomOut}
            className="p-2 rounded-md hover:bg-gray-100"
            title="Zoom out (-)"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          
          <span className="text-sm text-gray-600 min-w-[4rem] text-center">
            {Math.round(viewerState.scale * 100)}%
          </span>
          
          <button
            onClick={zoomIn}
            className="p-2 rounded-md hover:bg-gray-100"
            title="Zoom in (+)"
          >
            <ZoomIn className="w-5 h-5" />
          </button>

          <button
            onClick={rotate}
            className="p-2 rounded-md hover:bg-gray-100"
            title="Rotate (R)"
          >
            <RotateCw className="w-5 h-5" />
          </button>
        </div>

        {/* Search and download */}
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search in document..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <button
            onClick={() => window.open(fileUrl, '_blank')}
            className="p-2 rounded-md hover:bg-gray-100"
            title="Download PDF"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto bg-gray-200 p-4"
      >
        <div className="flex justify-center">
          <div className="relative bg-white shadow-lg">
            <Document
              file={fileUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex items-center justify-center h-96">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              }
            >
              <div
                ref={(el) => {
                  if (el) pageRefs.current.set(viewerState.currentPage, el);
                }}
                className="relative"
              >
                <Page
                  pageNumber={viewerState.currentPage}
                  scale={viewerState.scale}
                  rotate={viewerState.rotation}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                />
                
                {/* Clause annotations overlay */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="relative w-full h-full pointer-events-auto">
                    {renderClauseAnnotations(viewerState.currentPage)}
                  </div>
                </div>
              </div>
            </Document>
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-t text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>Page {viewerState.currentPage} of {viewerState.numPages}</span>
          {showAnnotations && (
            <span>{getCurrentPageClauses().length} clauses on this page</span>
          )}
        </div>
        
        {showAnnotations && (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded border-2" style={{ backgroundColor: RISK_COLORS.beneficial.background, borderColor: RISK_COLORS.beneficial.border }}></div>
              <span>Beneficial</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded border-2" style={{ backgroundColor: RISK_COLORS.caution.background, borderColor: RISK_COLORS.caution.border }}></div>
              <span>Caution</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded border-2" style={{ backgroundColor: RISK_COLORS.risky.background, borderColor: RISK_COLORS.risky.border }}></div>
              <span>Risky</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFViewer;