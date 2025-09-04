import React, { useMemo, useCallback } from 'react';
import { Clause, ClauseClassification } from '../../types/document';
import { cn } from '../../lib/utils';

interface ClauseHeatmapProps {
  clauses: Clause[];
  totalPages: number;
  currentPage: number;
  selectedClauseId?: string;
  onPageSelect?: (page: number) => void;
  onClauseSelect?: (clauseId: string) => void;
  className?: string;
}

interface PageStats {
  page: number;
  totalClauses: number;
  beneficialCount: number;
  cautionCount: number;
  riskyCount: number;
  averageRiskScore: number;
  clauses: Clause[];
}

const RISK_COLORS = {
  [ClauseClassification.BENEFICIAL]: '#22c55e', // green-500
  [ClauseClassification.CAUTION]: '#eab308', // yellow-500
  [ClauseClassification.RISKY]: '#ef4444', // red-500
};

export const ClauseHeatmap: React.FC<ClauseHeatmapProps> = ({
  clauses,
  totalPages,
  currentPage,
  selectedClauseId,
  onPageSelect,
  onClauseSelect,
  className,
}) => {
  // Calculate page statistics
  const pageStats = useMemo(() => {
    const stats: PageStats[] = [];
    
    for (let page = 1; page <= totalPages; page++) {
      const pageClauses = clauses.filter(clause => 
        clause.position && clause.position.page === page
      );
      
      const beneficialCount = pageClauses.filter(c => c.classification === ClauseClassification.BENEFICIAL).length;
      const cautionCount = pageClauses.filter(c => c.classification === ClauseClassification.CAUTION).length;
      const riskyCount = pageClauses.filter(c => c.classification === ClauseClassification.RISKY).length;
      
      const averageRiskScore = pageClauses.length > 0
        ? pageClauses.reduce((sum, clause) => sum + clause.riskScore, 0) / pageClauses.length
        : 0;
      
      stats.push({
        page,
        totalClauses: pageClauses.length,
        beneficialCount,
        cautionCount,
        riskyCount,
        averageRiskScore,
        clauses: pageClauses,
      });
    }
    
    return stats;
  }, [clauses, totalPages]);

  // Get color intensity based on risk score
  const getRiskIntensity = useCallback((riskScore: number) => {
    if (riskScore < 0.3) return 0.3;
    if (riskScore < 0.6) return 0.6;
    return 0.9;
  }, []);

  // Get dominant risk color for a page
  const getPageColor = useCallback((stats: PageStats) => {
    if (stats.totalClauses === 0) return '#f3f4f6'; // gray-100
    
    const { beneficialCount, cautionCount, riskyCount, averageRiskScore } = stats;
    
    // Determine dominant classification
    if (riskyCount > beneficialCount && riskyCount > cautionCount) {
      return RISK_COLORS[ClauseClassification.RISKY];
    } else if (cautionCount > beneficialCount && cautionCount >= riskyCount) {
      return RISK_COLORS[ClauseClassification.CAUTION];
    } else if (beneficialCount > 0) {
      return RISK_COLORS[ClauseClassification.BENEFICIAL];
    }
    
    // Fallback to average risk score
    if (averageRiskScore > 0.6) return RISK_COLORS[ClauseClassification.RISKY];
    if (averageRiskScore > 0.3) return RISK_COLORS[ClauseClassification.CAUTION];
    return RISK_COLORS[ClauseClassification.BENEFICIAL];
  }, []);

  // Handle page click
  const handlePageClick = useCallback((page: number) => {
    onPageSelect?.(page);
  }, [onPageSelect]);

  // Handle clause click
  const handleClauseClick = useCallback((clauseId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    onClauseSelect?.(clauseId);
  }, [onClauseSelect]);

  // Calculate grid dimensions
  const gridCols = Math.ceil(Math.sqrt(totalPages));
  const gridRows = Math.ceil(totalPages / gridCols);

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">Document Heatmap</h3>
        <p className="text-sm text-gray-600 mt-1">
          Visual overview of clause risk distribution across all pages
        </p>
      </div>

      {/* Legend */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div 
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: RISK_COLORS[ClauseClassification.BENEFICIAL] }}
              />
              <span className="text-sm text-gray-700">Beneficial</span>
            </div>
            <div className="flex items-center space-x-2">
              <div 
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: RISK_COLORS[ClauseClassification.CAUTION] }}
              />
              <span className="text-sm text-gray-700">Caution</span>
            </div>
            <div className="flex items-center space-x-2">
              <div 
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: RISK_COLORS[ClauseClassification.RISKY] }}
              />
              <span className="text-sm text-gray-700">Risky</span>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            {clauses.length} total clauses
          </div>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="p-4">
        <div 
          className="grid gap-2"
          style={{ 
            gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`,
            gridTemplateRows: `repeat(${gridRows}, minmax(0, 1fr))`,
          }}
        >
          {pageStats.map((stats) => {
            const isCurrentPage = stats.page === currentPage;
            const pageColor = getPageColor(stats);
            const intensity = getRiskIntensity(stats.averageRiskScore);
            
            return (
              <div
                key={stats.page}
                className={cn(
                  'relative aspect-[3/4] rounded border-2 cursor-pointer transition-all duration-200',
                  'hover:scale-105 hover:shadow-md',
                  isCurrentPage ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'
                )}
                style={{
                  backgroundColor: stats.totalClauses > 0 
                    ? `${pageColor}${Math.round(intensity * 255).toString(16).padStart(2, '0')}`
                    : '#f9fafb',
                }}
                onClick={() => handlePageClick(stats.page)}
                title={`Page ${stats.page}: ${stats.totalClauses} clauses (${stats.riskyCount} risky, ${stats.cautionCount} caution, ${stats.beneficialCount} beneficial)`}
              >
                {/* Page number */}
                <div className="absolute top-1 left-1 text-xs font-medium text-gray-700 bg-white bg-opacity-80 px-1 rounded">
                  {stats.page}
                </div>

                {/* Clause count */}
                {stats.totalClauses > 0 && (
                  <div className="absolute bottom-1 right-1 text-xs font-medium text-gray-700 bg-white bg-opacity-80 px-1 rounded">
                    {stats.totalClauses}
                  </div>
                )}

                {/* Risk indicator */}
                {stats.totalClauses > 0 && (
                  <div className="absolute top-1 right-1">
                    <div 
                      className="w-2 h-2 rounded-full border border-white"
                      style={{ backgroundColor: pageColor }}
                    />
                  </div>
                )}

                {/* Clause dots for detailed view */}
                {stats.totalClauses > 0 && stats.totalClauses <= 10 && (
                  <div className="absolute inset-2 flex flex-wrap gap-1 items-center justify-center">
                    {stats.clauses.map((clause) => (
                      <div
                        key={clause.id}
                        className={cn(
                          'w-1.5 h-1.5 rounded-full cursor-pointer transition-all duration-200',
                          'hover:scale-150',
                          selectedClauseId === clause.id && 'ring-1 ring-blue-500 scale-150'
                        )}
                        style={{ backgroundColor: RISK_COLORS[clause.classification] }}
                        onClick={(e) => handleClauseClick(clause.id, e)}
                        title={`${clause.classification}: ${clause.text.substring(0, 50)}...`}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="p-4 border-t bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-green-600">
              {pageStats.reduce((sum, stats) => sum + stats.beneficialCount, 0)}
            </div>
            <div className="text-sm text-gray-600">Beneficial</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-600">
              {pageStats.reduce((sum, stats) => sum + stats.cautionCount, 0)}
            </div>
            <div className="text-sm text-gray-600">Caution</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {pageStats.reduce((sum, stats) => sum + stats.riskyCount, 0)}
            </div>
            <div className="text-sm text-gray-600">Risky</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-700">
              {Math.round(
                pageStats.reduce((sum, stats) => sum + stats.averageRiskScore, 0) / 
                pageStats.filter(stats => stats.totalClauses > 0).length * 100
              ) || 0}%
            </div>
            <div className="text-sm text-gray-600">Avg Risk</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClauseHeatmap;