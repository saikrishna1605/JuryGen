import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  FileText, 
  Download, 
  Share2, 
  MessageCircle, 
  Eye, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Languages,
  Mic,
  Play,
  Pause
} from 'lucide-react';

interface DocumentAnalysis {
  id: string;
  filename: string;
  status: 'processing' | 'completed' | 'error';
  summary?: {
    plain_language: string;
    key_points: string[];
    document_type: string;
    word_count: number;
    reading_level: string;
  };
  clauses?: Array<{
    id: string;
    text: string;
    classification: 'beneficial' | 'caution' | 'risky';
    explanation: string;
    impact_score: number;
    likelihood_score: number;
    alternatives?: string[];
  }>;
  risks?: Array<{
    type: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    mitigation: string;
  }>;
  created_at: string;
  processed_at?: string;
}

const DocumentAnalysisPage = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [document, setDocument] = useState<DocumentAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'clauses' | 'risks' | 'qa'>('summary');
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!currentUser || !documentId) {
      navigate('/login');
      return;
    }
    
    fetchDocumentAnalysis();
  }, [currentUser, documentId, navigate]);

  const fetchDocumentAnalysis = async () => {
    try {
      setLoading(true);
      const token = await currentUser?.getIdToken();
      
      const response = await fetch(`/api/v1/documents/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch document analysis');
      }

      const data = await response.json();
      setDocument(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayAudio = async () => {
    if (!audioUrl && document?.summary) {
      try {
        const token = await currentUser?.getIdToken();
        const response = await fetch(`/api/v1/speech/synthesize`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: document.summary.plain_language,
            language_code: 'en-US',
            voice_gender: 'NEUTRAL',
          }),
        });

        if (response.ok) {
          const audioBlob = await response.blob();
          const url = URL.createObjectURL(audioBlob);
          setAudioUrl(url);
          
          const audio = new Audio(url);
          audio.play();
          setIsPlaying(true);
          
          audio.onended = () => setIsPlaying(false);
        }
      } catch (err) {
        console.error('Failed to generate audio:', err);
      }
    } else if (audioUrl) {
      const audio = new Audio(audioUrl);
      if (isPlaying) {
        audio.pause();
        setIsPlaying(false);
      } else {
        audio.play();
        setIsPlaying(true);
        audio.onended = () => setIsPlaying(false);
      }
    }
  };

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'beneficial': return 'text-green-600 bg-green-50 border-green-200';
      case 'caution': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'risky': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getClassificationIcon = (classification: string) => {
    switch (classification) {
      case 'beneficial': return <CheckCircle className="w-5 h-5" />;
      case 'caution': return <Clock className="w-5 h-5" />;
      case 'risky': return <AlertTriangle className="w-5 h-5" />;
      default: return <FileText className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Document</h2>
          <p className="text-gray-600 mb-4">{error || 'Document not found'}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{document.filename}</h1>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="flex items-center">
                  <FileText className="w-4 h-4 mr-1" />
                  {document.summary?.document_type || 'Legal Document'}
                </span>
                <span className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {new Date(document.created_at).toLocaleDateString()}
                </span>
                {document.summary?.word_count && (
                  <span>{document.summary.word_count.toLocaleString()} words</span>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handlePlayAudio}
                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                {isPlaying ? 'Pause' : 'Listen'}
              </button>
              <button className="flex items-center px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
              <button className="flex items-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'summary', label: 'Summary', icon: FileText },
                { id: 'clauses', label: 'Clause Analysis', icon: Eye },
                { id: 'risks', label: 'Risk Assessment', icon: AlertTriangle },
                { id: 'qa', label: 'Q&A', icon: MessageCircle },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id as any)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Summary Tab */}
            {activeTab === 'summary' && document.summary && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Plain Language Summary</h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-gray-800 leading-relaxed">{document.summary.plain_language}</p>
                  </div>
                </div>

                {document.summary.key_points && document.summary.key_points.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Points</h3>
                    <ul className="space-y-2">
                      {document.summary.key_points.map((point, index) => (
                        <li key={index} className="flex items-start">
                          <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-1">Document Type</h4>
                    <p className="text-gray-600">{document.summary.document_type}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-1">Reading Level</h4>
                    <p className="text-gray-600">{document.summary.reading_level}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-1">Word Count</h4>
                    <p className="text-gray-600">{document.summary.word_count.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Clauses Tab */}
            {activeTab === 'clauses' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Clause Analysis</h3>
                {document.clauses && document.clauses.length > 0 ? (
                  <div className="space-y-4">
                    {document.clauses.map((clause) => (
                      <div
                        key={clause.id}
                        className={`border rounded-lg p-4 ${getClassificationColor(clause.classification)}`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center">
                            {getClassificationIcon(clause.classification)}
                            <span className="ml-2 font-medium capitalize">{clause.classification}</span>
                          </div>
                          <div className="flex space-x-2 text-sm">
                            <span>Impact: {clause.impact_score}/10</span>
                            <span>Likelihood: {clause.likelihood_score}/10</span>
                          </div>
                        </div>
                        <p className="text-gray-800 mb-3 font-mono text-sm bg-white bg-opacity-50 p-3 rounded">
                          {clause.text}
                        </p>
                        <p className="text-gray-700 mb-3">{clause.explanation}</p>
                        {clause.alternatives && clause.alternatives.length > 0 && (
                          <div>
                            <h5 className="font-medium mb-2">Suggested Alternatives:</h5>
                            <ul className="list-disc list-inside space-y-1">
                              {clause.alternatives.map((alt, index) => (
                                <li key={index} className="text-sm text-gray-600">{alt}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">No clause analysis available yet.</p>
                )}
              </div>
            )}

            {/* Risks Tab */}
            {activeTab === 'risks' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Risk Assessment</h3>
                {document.risks && document.risks.length > 0 ? (
                  <div className="space-y-4">
                    {document.risks.map((risk, index) => (
                      <div
                        key={index}
                        className={`border rounded-lg p-4 ${
                          risk.severity === 'high' ? 'border-red-200 bg-red-50' :
                          risk.severity === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                          'border-green-200 bg-green-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{risk.type}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            risk.severity === 'high' ? 'bg-red-100 text-red-800' :
                            risk.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {risk.severity.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-gray-700 mb-3">{risk.description}</p>
                        <div className="bg-white bg-opacity-50 p-3 rounded">
                          <h5 className="font-medium text-gray-900 mb-1">Mitigation:</h5>
                          <p className="text-gray-700 text-sm">{risk.mitigation}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">No risk assessment available yet.</p>
                )}
              </div>
            )}

            {/* Q&A Tab */}
            {activeTab === 'qa' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Ask Questions</h3>
                  <button
                    onClick={() => navigate(`/voice-qa?document=${documentId}`)}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    <Mic className="w-4 h-4 mr-2" />
                    Voice Q&A
                  </button>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Suggested Questions:</h4>
                  <div className="space-y-2">
                    {[
                      "What are the main obligations in this document?",
                      "What are the key risks I should be aware of?",
                      "Are there any important deadlines or dates?",
                      "What happens if I want to terminate this agreement?",
                      "What are the payment terms and conditions?",
                    ].map((question, index) => (
                      <button
                        key={index}
                        className="block w-full text-left p-3 bg-white rounded border hover:bg-blue-50 hover:border-blue-200"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <textarea
                    placeholder="Type your question about this document..."
                    className="w-full h-24 p-3 border rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <div className="flex justify-between items-center mt-3">
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Languages className="w-4 h-4" />
                      <span>English</span>
                    </div>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                      Ask Question
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentAnalysisPage;