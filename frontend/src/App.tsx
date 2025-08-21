import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { UploadPage } from './pages/UploadPage'
import './App.css'

// Navigation component with auth state
const Navigation = () => {
  const { currentUser, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              Legal Companion
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/" className="text-gray-700 hover:text-gray-900">Home</Link>
            <Link to="/about" className="text-gray-700 hover:text-gray-900">About</Link>
            {currentUser ? (
              <>
                <Link to="/dashboard" className="text-gray-700 hover:text-gray-900">Dashboard</Link>
                <Link to="/upload" className="text-gray-700 hover:text-gray-900">Upload</Link>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {currentUser.displayName || currentUser.email || 'User'}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-500"
                  >
                    Sign Out
                  </button>
                </div>
              </>
            ) : (
              <Link
                to="/login"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Home page component
const HomePage = () => {
  const { currentUser } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Legal Companion
          </h1>
          <p className="text-gray-600 mb-6">
            AI-powered legal document analysis and simplification
          </p>
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">🚀 Getting Started</h3>
              <p className="text-blue-700 text-sm">
                {currentUser 
                  ? 'Go to your dashboard to upload and analyze legal documents'
                  : 'Sign in to upload and analyze legal documents with AI'
                }
              </p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">✨ Features</h3>
              <ul className="text-green-700 text-sm space-y-1">
                <li>• Multi-modal document processing</li>
                <li>• Intelligent clause analysis</li>
                <li>• Voice-to-voice Q&A</li>
                <li>• Multi-language support</li>
              </ul>
            </div>
            {currentUser ? (
              <Link
                to="/dashboard"
                className="block w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-center"
              >
                Go to Dashboard
              </Link>
            ) : (
              <Link
                to="/login"
                className="block w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-center"
              >
                Get Started
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const AboutPage = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="max-w-2xl w-full bg-white rounded-lg shadow-md p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">About Legal Companion</h1>
      <div className="prose prose-gray max-w-none">
        <p>
          Legal Companion is an AI-driven solution that demystifies complex legal documents
          by transforming them into accessible, actionable guidance.
        </p>
        <h2>Key Features:</h2>
        <ul>
          <li><strong>Multi-Modal Processing:</strong> Upload PDFs, images, DOCX, and scanned documents</li>
          <li><strong>Intelligent Analysis:</strong> AI-powered risk assessment with role-specific analysis</li>
          <li><strong>Plain Language:</strong> Convert legal jargon to accessible language</li>
          <li><strong>Voice Interface:</strong> Ask questions using voice and receive spoken responses</li>
          <li><strong>Privacy-First:</strong> End-to-end encryption and PII protection</li>
        </ul>
        <h2>Powered by Google Cloud AI:</h2>
        <ul>
          <li><strong>Vertex AI:</strong> Advanced language models for analysis</li>
          <li><strong>Document AI:</strong> Intelligent document processing</li>
          <li><strong>Translation API:</strong> Support for 100+ languages</li>
          <li><strong>Speech Services:</strong> Voice-to-voice interactions</li>
        </ul>
      </div>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Navigation />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App