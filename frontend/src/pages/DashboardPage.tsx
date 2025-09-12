import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { UserProfile } from '../components/auth/UserProfile';
import { useAuth } from '../contexts/AuthContext';
import { DocumentUploader } from '../components/upload';
import { VoiceQA } from '../components/voice';
import { UploadUrlResponse } from '../types';
import { 
  FileText, 
  Upload, 
  Mic, 
  Languages, 
  Eye, 
  BarChart3, 
  CheckCircle, 
  AlertTriangle,
  Users,
  Globe
} from 'lucide-react';
import { getApiUrl } from '../utils/api';

interface Document {
  id: string;
  filename: string;
  status: 'processing' | 'completed' | 'error';
  created_at: string;
  summary?: {
    document_type: string;
    plain_language: string;
    key_points: string[];
  };
  analysis?: {
    risk_level: 'low' | 'medium' | 'high';
    clause_count: number;
    beneficial_clauses: number;
    risky_clauses: number;
  };
}

const DashboardPage: React.FC = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [activeView, setActiveView] = useState<'dashboard' | 'upload' | 'voice'>('dashboard');
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    completedAnalyses: 0,
    totalQuestions: 0,
    translationsCount: 0
  });

  useEffect(() => {
    if (currentUser) {
      fetchDashboardData();
    }
  }, [currentUser]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = await currentUser?.getIdToken();
      
      // Fetch recent documents
      const documentsResponse = await fetch(getApiUrl('v1/documents'), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (documentsResponse.ok) {
        const documentsData = await documentsResponse.json();
        setRecentDocuments(documentsData.data || []);
        
        // Calculate stats
        const docs = documentsData.data || [];
        setStats({
          totalDocuments: docs.length,
          completedAnalyses: docs.filter((doc: Document) => doc.status === 'completed').length,
          totalQuestions: 0, // This would come from Q&A history
          translationsCount: 0 // This would come from translation history
        });
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadComplete = (response: UploadUrlResponse) => {
    console.log('Upload completed:', response);
    // Refresh dashboard data
    fetchDashboardData();
    setSelectedDocumentId(response.jobId);
    // Navigate to document analysis page
    navigate(`/document/${response.jobId}`);
  };

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error);
    alert(`Upload failed: ${error}`);
  };

  const handleVoiceError = (error: string) => {
    console.error('Voice Q&A error:', error);
    alert(`Voice Q&A error: ${error}`);
  };

  // Render different views based on activeView
  const renderContent = () => {
    switch (activeView) {
      case 'upload':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Upload Documents</h2>
                <p className="text-gray-600 mt-1">Upload your legal documents for AI-powered analysis</p>
              </div>
              <button
                onClick={() => setActiveView('dashboard')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Back to Dashboard
              </button>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <DocumentUploader
                onUploadComplete={handleUploadComplete}
                onError={handleUploadError}
              />
            </div>
          </div>
        );
      
      case 'voice':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Voice Q&A</h2>
                <p className="text-gray-600 mt-1">Ask questions about your documents using voice or text</p>
              </div>
              <button
                onClick={() => setActiveView('dashboard')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Back to Dashboard
              </button>
            </div>
            {selectedDocumentId ? (
              <div className="bg-white rounded-lg shadow-md" style={{ height: '600px' }}>
                <VoiceQA
                  documentId={selectedDocumentId}
                  onError={handleVoiceError}
                  className="h-full"
                />
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Document Selected</h3>
                <p className="text-gray-500 mb-4">Please upload a document first to use Voice Q&A</p>
                <button
                  onClick={() => setActiveView('upload')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Upload Document
                </button>
              </div>
            )}
          </div>
        );
      
      default:
        return renderDashboard();
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back{currentUser?.displayName ? `, ${currentUser.displayName}` : ''}!
        </h1>
        <p className="text-gray-600 mt-2">
          Your Legal Companion dashboard - analyze documents, get AI insights, and more.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Documents</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalDocuments}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-green-600">{stats.completedAnalyses}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Q&A Sessions</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.totalQuestions}</p>
                </div>
                <Mic className="w-8 h-8 text-purple-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Translations</p>
                  <p className="text-2xl font-bold text-orange-600">{stats.translationsCount}</p>
                </div>
                <Languages className="w-8 h-8 text-orange-500" />
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Link
                to="/upload"
                className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors group"
              >
                <div className="text-center">
                  <Upload className="w-8 h-8 mx-auto text-gray-400 group-hover:text-blue-500 mb-2" />
                  <p className="text-sm font-medium text-gray-900 group-hover:text-blue-900">Upload Document</p>
                  <p className="text-xs text-gray-500">Analyze legal documents with AI</p>
                </div>
              </Link>

              <Link
                to="/voice-qa"
                className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors group"
              >
                <div className="text-center">
                  <Mic className="w-8 h-8 mx-auto text-gray-400 group-hover:text-green-500 mb-2" />
                  <p className="text-sm font-medium text-gray-900 group-hover:text-green-900">Voice Q&A</p>
                  <p className="text-xs text-gray-500">Ask questions about your documents</p>
                </div>
              </Link>

              <Link
                to="/translate"
                className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors group"
              >
                <div className="text-center">
                  <Languages className="w-8 h-8 mx-auto text-gray-400 group-hover:text-orange-500 mb-2" />
                  <p className="text-sm font-medium text-gray-900 group-hover:text-orange-900">Translate</p>
                  <p className="text-xs text-gray-500">100+ languages supported</p>
                </div>
              </Link>

              <button 
                onClick={() => setActiveView('voice')}
                disabled={!selectedDocumentId && recentDocuments.length === 0}
                className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="text-center">
                  <BarChart3 className="w-8 h-8 mx-auto text-gray-400 group-hover:text-purple-500 mb-2" />
                  <p className="text-sm font-medium text-gray-900 group-hover:text-purple-900">Analytics</p>
                  <p className="text-xs text-gray-500">View document insights</p>
                </div>
              </button>
            </div>
          </div>

          {/* Recent Documents */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Recent Documents</h2>
              <Link to="/upload" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                Upload New
              </Link>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-center space-x-3 p-3">
                      <div className="w-8 h-8 bg-gray-200 rounded"></div>
                      <div className="flex-1">
                        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recentDocuments.length > 0 ? (
              <div className="space-y-3">
                {recentDocuments.slice(0, 5).map((doc) => (
                  <div 
                    key={doc.id}
                    className="p-4 border rounded-lg hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-8 h-8 text-blue-500" />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              doc.status === 'completed' ? 'bg-green-100 text-green-800' :
                              doc.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {doc.status}
                            </span>
                          </div>
                          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                            <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                            {doc.summary?.document_type && (
                              <span>• {doc.summary.document_type}</span>
                            )}
                            {doc.analysis && (
                              <span className={`• ${
                                doc.analysis.risk_level === 'high' ? 'text-red-600' :
                                doc.analysis.risk_level === 'medium' ? 'text-yellow-600' :
                                'text-green-600'
                              }`}>
                                {doc.analysis.risk_level.toUpperCase()} RISK
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Link
                          to={`/document/${doc.id}`}
                          className="p-2 text-blue-600 hover:text-blue-800 rounded"
                          title="View analysis"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        <Link
                          to={`/voice-qa?document=${doc.id}`}
                          className="p-2 text-green-600 hover:text-green-800 rounded"
                          title="Ask questions"
                        >
                          <Mic className="w-4 h-4" />
                        </Link>
                      </div>
                    </div>
                    {doc.summary?.plain_language && (
                      <div className="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-700">
                        {doc.summary.plain_language.substring(0, 150)}...
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No documents yet</p>
                <p className="text-sm text-gray-400 mt-1 mb-4">Upload your first legal document to get started</p>
                <Link
                  to="/upload"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Document
                </Link>
              </div>
            )}
          </div>

          {/* Features Overview */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Platform Features</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <BarChart3 className="w-4 h-4 text-blue-600" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">AI Analysis</h3>
                  <p className="text-xs text-gray-500">Intelligent clause classification and risk assessment</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <Globe className="w-4 h-4 text-green-600" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Multi-Language</h3>
                  <p className="text-xs text-gray-500">Translation and analysis in 100+ languages</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <Mic className="w-4 h-4 text-purple-600" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Voice Interface</h3>
                  <p className="text-xs text-gray-500">Ask questions and get spoken responses</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 text-orange-600" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Privacy First</h3>
                  <p className="text-xs text-gray-500">End-to-end encryption and data protection</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Risk Assessment</h3>
                  <p className="text-xs text-gray-500">Identify and mitigate legal risks</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                    <Users className="w-4 h-4 text-indigo-600" />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Role-Based Analysis</h3>
                  <p className="text-xs text-gray-500">Tailored insights for your specific role</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* User Profile */}
          <UserProfile />

          {/* Usage Stats */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage This Month</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">Documents Analyzed</span>
                  <span className="text-sm font-medium text-gray-900">{stats.completedAnalyses} / 50</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${Math.min((stats.completedAnalyses / 50) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">AI Queries</span>
                  <span className="text-sm font-medium text-gray-900">{stats.totalQuestions} / 500</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${Math.min((stats.totalQuestions / 500) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">Translations</span>
                  <span className="text-sm font-medium text-gray-900">{stats.translationsCount} / 200</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-orange-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${Math.min((stats.translationsCount / 200) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Plan</span>
                  <span className="font-medium text-blue-600">Professional</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            {renderContent()}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
};

export default DashboardPage;