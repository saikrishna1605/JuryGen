import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  Languages, 
  FileText, 
  Download, 
  Copy, 
  Volume2, 
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Globe,
  Zap
} from 'lucide-react';

interface Document {
  id: string;
  filename: string;
  summary?: {
    document_type: string;
    plain_language: string;
  };
}

interface Translation {
  id: string;
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  confidence: number;
  quality_score: number;
  processing_time: number;
  cached: boolean;
  alternatives: string[];
  created_at: string;
}

interface Language {
  code: string;
  name: string;
  native_name: string;
}

const TranslationPage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string>('');
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [translationMode, setTranslationMode] = useState<'document' | 'text'>('document');
  const [customText, setCustomText] = useState('');
  const [translation, setTranslation] = useState<Translation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableLanguages, setAvailableLanguages] = useState<Language[]>([]);
  const [translationHistory, setTranslationHistory] = useState<Translation[]>([]);

  useEffect(() => {
    if (!currentUser) {
      navigate('/login');
      return;
    }
    
    fetchDocuments();
    fetchAvailableLanguages();
    fetchTranslationHistory();
  }, [currentUser, navigate]);

  const fetchDocuments = async () => {
    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch('/api/v1/documents', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const fetchAvailableLanguages = async () => {
    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch('/api/v1/translation/languages', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableLanguages(data.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch languages:', err);
      // Fallback to common languages
      setAvailableLanguages([
        { code: 'auto', name: 'Auto-detect', native_name: 'Auto-detect' },
        { code: 'en', name: 'English', native_name: 'English' },
        { code: 'es', name: 'Spanish', native_name: 'Español' },
        { code: 'fr', name: 'French', native_name: 'Français' },
        { code: 'de', name: 'German', native_name: 'Deutsch' },
        { code: 'it', name: 'Italian', native_name: 'Italiano' },
        { code: 'pt', name: 'Portuguese', native_name: 'Português' },
        { code: 'ru', name: 'Russian', native_name: 'Русский' },
        { code: 'ja', name: 'Japanese', native_name: '日本語' },
        { code: 'ko', name: 'Korean', native_name: '한국어' },
        { code: 'zh', name: 'Chinese', native_name: '中文' },
        { code: 'ar', name: 'Arabic', native_name: 'العربية' },
        { code: 'hi', name: 'Hindi', native_name: 'हिन्दी' },
      ]);
    }
  };

  const fetchTranslationHistory = async () => {
    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch('/api/v1/translation/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTranslationHistory(data.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch translation history:', err);
    }
  };

  const translateText = async () => {
    if (translationMode === 'document' && !selectedDocument) {
      setError('Please select a document to translate');
      return;
    }
    
    if (translationMode === 'text' && !customText.trim()) {
      setError('Please enter text to translate');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = await currentUser?.getIdToken();
      
      let requestBody;
      if (translationMode === 'document') {
        const selectedDoc = documents.find(doc => doc.id === selectedDocument);
        requestBody = {
          text: selectedDoc?.summary?.plain_language || '',
          source_language: sourceLanguage,
          target_language: targetLanguage,
          document_id: selectedDocument,
        };
      } else {
        requestBody = {
          text: customText,
          source_language: sourceLanguage,
          target_language: targetLanguage,
        };
      }

      const response = await fetch('/api/v1/translation/translate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        setTranslation(data.data);
        fetchTranslationHistory(); // Refresh history
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Translation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
    } finally {
      setLoading(false);
    }
  };

  const detectLanguage = async () => {
    const textToDetect = translationMode === 'document' 
      ? documents.find(doc => doc.id === selectedDocument)?.summary?.plain_language || ''
      : customText;

    if (!textToDetect.trim()) return;

    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch('/api/v1/translation/detect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: textToDetect }),
      });

      if (response.ok) {
        const data = await response.json();
        setSourceLanguage(data.data.language);
      }
    } catch (err) {
      console.error('Language detection failed:', err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const speakText = async (text: string, languageCode: string) => {
    try {
      const token = await currentUser?.getIdToken();
      const response = await fetch('/api/v1/speech/synthesize', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          language_code: languageCode,
          voice_gender: 'NEUTRAL',
        }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    } catch (err) {
      console.error('Text-to-speech failed:', err);
    }
  };

  const downloadTranslation = () => {
    if (!translation) return;

    const content = `Original Text (${translation.source_language}):\n${translation.original_text}\n\nTranslation (${translation.target_language}):\n${translation.translated_text}\n\nConfidence: ${Math.round(translation.confidence * 100)}%\nQuality Score: ${Math.round(translation.quality_score * 100)}%\nProcessing Time: ${translation.processing_time}ms\nGenerated: ${new Date(translation.created_at).toLocaleString()}`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translation-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLanguageName = (code: string) => {
    const lang = availableLanguages.find(l => l.code === code);
    return lang ? `${lang.name} (${lang.native_name})` : code;
  };

  const selectedDoc = documents.find(doc => doc.id === selectedDocument);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Document Translation</h1>
              <p className="text-gray-600">Translate legal documents into 100+ languages with AI-powered accuracy</p>
            </div>
            <div className="flex items-center space-x-2 text-blue-600">
              <Globe className="w-6 h-6" />
              <span className="font-medium">100+ Languages</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Translation Controls */}
          <div className="lg:col-span-2 space-y-6">
            {/* Mode Selection */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Translation Mode</h2>
              <div className="flex space-x-4">
                <button
                  onClick={() => setTranslationMode('document')}
                  className={`flex items-center px-4 py-2 rounded-md ${
                    translationMode === 'document'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Document
                </button>
                <button
                  onClick={() => setTranslationMode('text')}
                  className={`flex items-center px-4 py-2 rounded-md ${
                    translationMode === 'text'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Languages className="w-4 h-4 mr-2" />
                  Custom Text
                </button>
              </div>
            </div>

            {/* Source Content */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Source Content</h2>
              
              {translationMode === 'document' ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Document
                    </label>
                    <select
                      value={selectedDocument}
                      onChange={(e) => setSelectedDocument(e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Choose a document...</option>
                      {documents.map((doc) => (
                        <option key={doc.id} value={doc.id}>
                          {doc.filename} {doc.summary?.document_type && `(${doc.summary.document_type})`}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {selectedDoc?.summary?.plain_language && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">Document Summary</h4>
                      <p className="text-gray-700 text-sm leading-relaxed">
                        {selectedDoc.summary.plain_language.substring(0, 500)}
                        {selectedDoc.summary.plain_language.length > 500 && '...'}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter Text to Translate
                  </label>
                  <textarea
                    value={customText}
                    onChange={(e) => setCustomText(e.target.value)}
                    placeholder="Enter the text you want to translate..."
                    className="w-full h-32 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  />
                  <div className="flex justify-between items-center mt-2 text-sm text-gray-600">
                    <span>{customText.length} characters</span>
                    <button
                      onClick={detectLanguage}
                      className="flex items-center text-blue-600 hover:text-blue-700"
                    >
                      <Zap className="w-4 h-4 mr-1" />
                      Detect Language
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Language Selection */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Language Settings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From
                  </label>
                  <select
                    value={sourceLanguage}
                    onChange={(e) => setSourceLanguage(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {availableLanguages.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name} ({lang.native_name})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    To
                  </label>
                  <select
                    value={targetLanguage}
                    onChange={(e) => setTargetLanguage(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {availableLanguages.filter(lang => lang.code !== 'auto').map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name} ({lang.native_name})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <button
                onClick={translateText}
                disabled={loading || (translationMode === 'document' && !selectedDocument) || (translationMode === 'text' && !customText.trim())}
                className="w-full mt-4 flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Translating...
                  </>
                ) : (
                  <>
                    <Languages className="w-4 h-4 mr-2" />
                    Translate
                  </>
                )}
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                  <p className="text-red-800">{error}</p>
                </div>
              </div>
            )}

            {/* Translation Result */}
            {translation && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Translation Result</h2>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => copyToClipboard(translation.translated_text)}
                      className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-800"
                    >
                      <Copy className="w-4 h-4 mr-1" />
                      Copy
                    </button>
                    <button
                      onClick={() => speakText(translation.translated_text, translation.target_language)}
                      className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-800"
                    >
                      <Volume2 className="w-4 h-4 mr-1" />
                      Listen
                    </button>
                    <button
                      onClick={downloadTranslation}
                      className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      Original ({getLanguageName(translation.source_language)})
                    </h4>
                    <p className="text-gray-700">{translation.original_text}</p>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      Translation ({getLanguageName(translation.target_language)})
                    </h4>
                    <p className="text-gray-800 font-medium">{translation.translated_text}</p>
                  </div>

                  {/* Quality Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                        <span className="text-sm font-medium text-gray-900">Confidence</span>
                      </div>
                      <p className="text-lg font-bold text-green-600">
                        {Math.round(translation.confidence * 100)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <CheckCircle className="w-4 h-4 text-blue-500 mr-1" />
                        <span className="text-sm font-medium text-gray-900">Quality</span>
                      </div>
                      <p className="text-lg font-bold text-blue-600">
                        {Math.round(translation.quality_score * 100)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <Zap className="w-4 h-4 text-yellow-500 mr-1" />
                        <span className="text-sm font-medium text-gray-900">Speed</span>
                      </div>
                      <p className="text-lg font-bold text-yellow-600">
                        {translation.processing_time}ms
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center mb-1">
                        <RefreshCw className="w-4 h-4 text-purple-500 mr-1" />
                        <span className="text-sm font-medium text-gray-900">Cached</span>
                      </div>
                      <p className="text-lg font-bold text-purple-600">
                        {translation.cached ? 'Yes' : 'No'}
                      </p>
                    </div>
                  </div>

                  {/* Alternative Translations */}
                  {translation.alternatives && translation.alternatives.length > 0 && (
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="font-medium text-gray-900 mb-2">Alternative Translations</h4>
                      <div className="space-y-2">
                        {translation.alternatives.map((alt, index) => (
                          <div key={index} className="bg-gray-50 rounded p-3">
                            <p className="text-gray-700">{alt}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Translation History Sidebar */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Translations</h2>
              {translationHistory.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {translationHistory.slice(0, 10).map((item) => (
                    <div key={item.id} className="border rounded-lg p-3 hover:bg-gray-50 cursor-pointer">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-500">
                          {getLanguageName(item.source_language)} → {getLanguageName(item.target_language)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 truncate">
                        {item.original_text.substring(0, 50)}...
                      </p>
                      <p className="text-sm text-gray-900 font-medium truncate">
                        {item.translated_text.substring(0, 50)}...
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-sm">No translations yet</p>
              )}
            </div>

            {/* Language Stats */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Supported Languages</h2>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">100+</div>
                <p className="text-gray-600 text-sm mb-4">Languages supported</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-blue-50 rounded p-2">
                    <div className="font-medium text-blue-900">European</div>
                    <div className="text-blue-700">25+ languages</div>
                  </div>
                  <div className="bg-green-50 rounded p-2">
                    <div className="font-medium text-green-900">Asian</div>
                    <div className="text-green-700">30+ languages</div>
                  </div>
                  <div className="bg-yellow-50 rounded p-2">
                    <div className="font-medium text-yellow-900">African</div>
                    <div className="text-yellow-700">20+ languages</div>
                  </div>
                  <div className="bg-purple-50 rounded p-2">
                    <div className="font-medium text-purple-900">Americas</div>
                    <div className="text-purple-700">25+ languages</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranslationPage;