import React, { useState } from 'react';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { UserProfile } from '../components/auth/UserProfile';
import { useAuth } from '../contexts/AuthContext';
import { DocumentUploader } from '../components/upload';
import { VoiceQA } from '../components/voice';
import { UploadUrlResponse } from '../types';

const DashboardPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [activeView, setActiveView] = useState<'dashboard' | 'upload' | 'voice'>('dashboard');
  const [recentDocuments, setRecentDocuments] = useState<any[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  const handleUploadComplete = (response: UploadUrlResponse) => {
    console.log('Upload completed:', response);
    // Add to recent documents
    const newDoc = {
      id: response.jobId,
      name: 'Uploaded Document',
      uploadedAt: new Date().toISOString(),
      status: 'processing'
    };
    setRecentDocuments(prev => [newDoc, ...prev]);
    setSelectedDocumentId(response.jobId);
    // Show success message or navigate to document view
    alert('Document uploaded successfully! Processing started.');
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
          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button 
                onClick={() => setActiveView('upload')}
                className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors group"
              >
                <div className="text-center">
                  <svg className="w-8 h-8 mx-auto text-gray-400 group-hover:text-blue-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm font-medium text-gray-900 group-hover:text-blue-900">Upload Document</p>
                  <p className="text-xs text-gray-500">Analyze legal documents with AI</p>
                </div>
              </button>

              <button 
                onClick={() => setActiveView('voice')}
                disabled={!selectedDocumentId && recentDocuments.length === 0}
                className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="text-center">
                  <svg className="w-8 h-8 mx-auto text-gray-400 group-hover:text-green-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                  <p className="text-sm font-medium text-gray-900 group-hover:text-green-900">Voice Q&A</p>
                  <p className="text-xs text-gray-500">Ask questions about your documents</p>
                </div>
              </button>
            </div>
          </div>

          {/* Recent Documents */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Documents</h2>
            {recentDocuments.length > 0 ? (
              <div className="space-y-3">
                {recentDocuments.slice(0, 5).map((doc) => (
                  <div 
                    key={doc.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedDocumentId === doc.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedDocumentId(doc.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(doc.uploadedAt).toLocaleDateString()} • {doc.status}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedDocumentId(doc.id);
                            setActiveView('voice');
                          }}
                          className="p-1 text-green-600 hover:text-green-800 rounded"
                          title="Ask questions"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-500">No documents yet</p>
                <p className="text-sm text-gray-400 mt-1">Upload your first legal document to get started</p>
              </div>
            )}
          </div>

          {/* Features Overview */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Features</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
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
                    <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                    </svg>
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
                    <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
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
                    <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Privacy First</h3>
                  <p className="text-xs text-gray-500">End-to-end encryption and data protection</p>
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
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage This Month</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Documents Analyzed</span>
                <span className="text-sm font-medium text-gray-900">0 / 10</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '0%' }}></div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">AI Queries</span>
                <span className="text-sm font-medium text-gray-900">0 / 100</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{ width: '0%' }}></div>
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