import React, { useMemo } from 'react';
import { AlertTriangle, CheckCircle, AlertCircle, ExternalLink, Copy, BookOpen } from 'lucide-react';
import { Clause, ClauseClassification, UserRole } from '../../types/document';
import { cn } from '../../utils';

interface ClauseDetailsPanelProps {
  clause: Clause | null;
  userRole?: UserRole;
  onNavigateToClause?: (clauseId: string) => void;
  onCopyText?: (text: string) => void;
  className?: string;
}

const CLASSIFICATION_CONFIG = {
  [ClauseClassification.BENEFICIAL]: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    label: 'Beneficial',
    description: 'This clause is favorable to your interests',
  },
  [ClauseClassification.CAUTION]: {
    icon: AlertCircle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    label: 'Caution',
    description: 'This clause requires careful consideration',
  },
  [ClauseClassification.RISKY]: {
    icon: AlertTriangle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    label: 'Risky',
    description: 'This clause may pose significant risks',
  },
};

export const ClauseDetailsPanel: React.FC<ClauseDetailsPanelProps> = ({
  clause,
  userRole,
  onNavigateToClause,
  onCopyText,
  className,
}) => {
  // Get role-specific analysis
  const roleAnalysis = useMemo(() => {
    if (!clause || !userRole) return null;
    return clause.roleAnalysis[userRole];
  }, [clause, userRole]);

  // Handle copy text
  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    onCopyText?.(text);
  };

  // Handle navigate to clause
  const handleNavigateToClause = () => {
    if (clause) {
      onNavigateToClause?.(clause.id);
    }
  };

  if (!clause) {
    return (
      <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
        <div className="p-6 text-center text-gray-500">
          <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Clause Selected</h3>
          <p className="text-sm">
            Click on a highlighted clause in the document or select one from the heatmap to view details.
          </p>
        </div>
      </div>
    );
  }

  const config = CLASSIFICATION_CONFIG[clause.classification];
  const IconComponent = config.icon;

  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* Header */}
      <div className={cn('p-4 border-b', config.bgColor, config.borderColor)}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <IconComponent className={cn('w-6 h-6 mt-0.5', config.color)} />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {config.label} Clause
                {clause.clauseNumber && (
                  <span className="ml-2 text-sm font-normal text-gray-600">
                    (Section {clause.clauseNumber})
                  </span>
                )}
              </h3>
              <p className={cn('text-sm mt-1', config.color)}>
                {config.description}
              </p>
            </div>
          </div>
          <button
            onClick={handleNavigateToClause}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-white hover:bg-opacity-50"
            title="Navigate to clause in document"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Risk Scores */}
      <div className="p-4 border-b bg-gray-50">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(clause.riskScore * 100)}%
            </div>
            <div className="text-sm text-gray-600">Overall Risk</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {clause.impactScore}
            </div>
            <div className="text-sm text-gray-600">Impact Score</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {clause.likelihoodScore}
            </div>
            <div className="text-sm text-gray-600">Likelihood</div>
          </div>
        </div>
      </div>

      {/* Clause Text */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
            Clause Text
          </h4>
          <button
            onClick={() => handleCopyText(clause.text)}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
            title="Copy clause text"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
        <div className="prose prose-sm max-w-none">
          <p className="text-gray-700 leading-relaxed">
            {clause.text}
          </p>
        </div>
      </div>

      {/* Role-Specific Analysis */}
      {roleAnalysis && (
        <div className="p-4 border-b">
          <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
            Analysis for {userRole?.replace('_', ' ').toUpperCase()}
          </h4>
          
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-1">Rationale</h5>
              <p className="text-sm text-gray-600">{roleAnalysis.rationale}</p>
            </div>

            {roleAnalysis.recommendations.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h5>
                <ul className="space-y-1">
                  {roleAnalysis.recommendations.map((recommendation, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0" />
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Safer Alternatives */}
      {clause.saferAlternatives.length > 0 && (
        <div className="p-4 border-b">
          <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
            Safer Alternatives
          </h4>
          <div className="space-y-4">
            {clause.saferAlternatives.map((alternative, index) => (
              <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="text-sm font-medium text-green-800">
                    Alternative {index + 1}
                  </h5>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-green-600">
                      {Math.round(alternative.confidence * 100)}% confidence
                    </span>
                    <button
                      onClick={() => handleCopyText(alternative.suggestedText)}
                      className="p-1 text-green-600 hover:text-green-800 rounded"
                      title="Copy alternative text"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-700 mb-2 italic">
                  "{alternative.suggestedText}"
                </p>
                <p className="text-xs text-gray-600">
                  <strong>Why this is safer:</strong> {alternative.rationale}
                </p>
                {alternative.legalBasis && (
                  <p className="text-xs text-gray-600 mt-1">
                    <strong>Legal basis:</strong> {alternative.legalBasis}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legal Citations */}
      {clause.legalCitations.length > 0 && (
        <div className="p-4">
          <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
            Legal References
          </h4>
          <div className="space-y-3">
            {clause.legalCitations.map((citation, index) => (
              <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className="text-sm font-medium text-blue-800 mb-1">
                      {citation.statute}
                    </h5>
                    <p className="text-sm text-gray-700 mb-1">
                      {citation.description}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-600">
                      <span>
                        <strong>Jurisdiction:</strong> {citation.jurisdiction}
                      </span>
                      <span>
                        <strong>Relevance:</strong> {Math.round(citation.relevance * 100)}%
                      </span>
                    </div>
                  </div>
                  {citation.url && (
                    <a
                      href={citation.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1 text-blue-600 hover:text-blue-800 rounded"
                      title="View legal reference"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ClauseDetailsPanel;