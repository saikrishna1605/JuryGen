import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, FileText, Users, Lock } from 'lucide-react';

interface ComplianceMetrics {
  totalDocuments: number;
  compliantDocuments: number;
  pendingReview: number;
  violations: number;
  lastAudit: string;
  dataRetentionCompliance: number;
  encryptionStatus: 'compliant' | 'partial' | 'non-compliant';
}

interface ComplianceIssue {
  id: string;
  type: 'pii_exposure' | 'retention_violation' | 'encryption_missing' | 'access_violation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  documentId?: string;
  createdAt: string;
  status: 'open' | 'in_progress' | 'resolved';
}

const ComplianceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<ComplianceMetrics>({
    totalDocuments: 0,
    compliantDocuments: 0,
    pendingReview: 0,
    violations: 0,
    lastAudit: new Date().toISOString(),
    dataRetentionCompliance: 95,
    encryptionStatus: 'compliant'
  });

  const [issues, setIssues] = useState<ComplianceIssue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const fetchComplianceData = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API calls
      setMetrics({
        totalDocuments: 156,
        compliantDocuments: 148,
        pendingReview: 5,
        violations: 3,
        lastAudit: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        dataRetentionCompliance: 95,
        encryptionStatus: 'compliant'
      });

      setIssues([
        {
          id: '1',
          type: 'pii_exposure',
          severity: 'medium',
          description: 'Social Security Number detected in document without proper masking',
          documentId: 'doc-123',
          createdAt: new Date().toISOString(),
          status: 'open'
        },
        {
          id: '2',
          type: 'retention_violation',
          severity: 'low',
          description: 'Document exceeds retention policy by 30 days',
          documentId: 'doc-456',
          createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          status: 'in_progress'
        }
      ]);
    } catch (error) {
      console.error('Failed to fetch compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplianceScore = () => {
    if (metrics.totalDocuments === 0) return 100;
    return Math.round((metrics.compliantDocuments / metrics.totalDocuments) * 100);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="w-4 h-4" />;
      case 'medium':
        return <Clock className="w-4 h-4" />;
      case 'low':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Compliance Score */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Overall Compliance Score</h3>
          <div className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-green-500" />
            <span className="text-2xl font-bold text-green-600">{getComplianceScore()}%</span>
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-green-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${getComplianceScore()}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {metrics.compliantDocuments} of {metrics.totalDocuments} documents are fully compliant
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.totalDocuments}</p>
            </div>
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Compliant</p>
              <p className="text-2xl font-bold text-green-600">{metrics.compliantDocuments}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Review</p>
              <p className="text-2xl font-bold text-yellow-600">{metrics.pendingReview}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Violations</p>
              <p className="text-2xl font-bold text-red-600">{metrics.violations}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Compliance Areas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Protection</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Lock className="w-4 h-4 text-green-500" />
                <span className="text-sm text-gray-700">Encryption Status</span>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                metrics.encryptionStatus === 'compliant' 
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {metrics.encryptionStatus.toUpperCase()}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-gray-700">Access Controls</span>
              </div>
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ACTIVE
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-gray-700">Data Retention</span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {metrics.dataRetentionCompliance}% compliant
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Issues</h3>
          <div className="space-y-3">
            {issues.length > 0 ? (
              issues.slice(0, 3).map((issue) => (
                <div key={issue.id} className={`border rounded-lg p-3 ${getSeverityColor(issue.severity)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-2">
                      {getSeverityIcon(issue.severity)}
                      <div>
                        <p className="text-sm font-medium">{issue.description}</p>
                        <p className="text-xs opacity-75 mt-1">
                          {new Date(issue.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      issue.status === 'resolved' 
                        ? 'bg-green-100 text-green-800'
                        : issue.status === 'in_progress'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {issue.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4">
                <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm text-gray-600">No compliance issues found</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Audit Trail */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Audit Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Last Audit</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Date(metrics.lastAudit).toLocaleDateString()}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Next Scheduled</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString()}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Compliance Officer</p>
            <p className="text-lg font-semibold text-gray-900">System Admin</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceDashboard;