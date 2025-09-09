import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AccessibilityProvider } from './contexts/AccessibilityContext';
import { SkipNavigation } from './components/accessibility/SkipNavigation';
import { AccessibilityControls } from './components/accessibility/AccessibilityControls';
import { Settings } from 'lucide-react';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import DocumentAnalysisPage from './pages/DocumentAnalysisPage';
import VoiceQAPage from './pages/VoiceQAPage';
import TranslationPage from './pages/TranslationPage';

// Firebase Test Component
import FirebaseTest from './components/FirebaseTest';

// Styles
import './index.css';
import './styles/accessibility.css';

// Navigation component with auth state
const Navigation = () => {
  const { currentUser, logout } = useAuth();
  const [showAccessibilityControls, setShowAccessibilityControls] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <nav id="navigation" className="bg-white shadow-sm border-b" role="navigation" aria-label="Main navigation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link 
              to="/" 
              className="text-xl font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
              aria-label="Legal Companion - Home"
            >
              Legal Companion
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link 
              to="/" 
              className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
            >
              About
            </Link>
            <Link 
              to="/firebase-test" 
              className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
            >
              Firebase Test
            </Link>
            
            {/* Accessibility Controls Toggle */}
            <div className="relative">
              <button
                onClick={() => setShowAccessibilityControls(!showAccessibilityControls)}
                className="p-2 text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md"
                aria-label="Toggle accessibility settings"
                aria-expanded={showAccessibilityControls}
                aria-haspopup="true"
              >
                <Settings className="w-5 h-5" />
              </button>
              
              {showAccessibilityControls && (
                <div className="absolute right-0 top-full mt-2 z-50">
                  <AccessibilityControls 
                    compact={true}
                    onClose={() => setShowAccessibilityControls(false)}
                  />
                </div>
              )}
            </div>

            {currentUser ? (
              <>
                <Link 
                  to="/dashboard" 
                  className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/upload" 
                  className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
                >
                  Upload
                </Link>
                <Link 
                  to="/voice-qa" 
                  className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
                >
                  Voice Q&A
                </Link>
                <Link 
                  to="/translate" 
                  className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
                >
                  Translate
                </Link>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {currentUser.displayName || currentUser.email || 'User'}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded-md px-2 py-1"
                  >
                    Sign Out
                  </button>
                </div>
              </>
            ) : (
              <Link
                to="/login"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
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
    <main id="main-content" className="min-h-screen bg-gray-50 flex items-center justify-center" role="main">
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
              <h2 className="font-semibold text-blue-900 mb-2">🚀 Getting Started</h2>
              <p className="text-blue-700 text-sm">
                {currentUser 
                  ? 'Go to your dashboard to upload and analyze legal documents'
                  : 'Sign in to upload and analyze legal documents with AI'
                }
              </p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h2 className="font-semibold text-green-900 mb-2">✨ Features</h2>
              <ul className="text-green-700 text-sm space-y-1" role="list">
                <li role="listitem">• Multi-modal document processing</li>
                <li role="listitem">• Intelligent clause analysis</li>
                <li role="listitem">• Voice-to-voice Q&A</li>
                <li role="listitem">• Multi-language support</li>
                <li role="listitem">• Accessibility-first design</li>
              </ul>
            </div>
            {currentUser ? (
              <Link
                to="/dashboard"
                className="block w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors text-center"
              >
                Go to Dashboard
              </Link>
            ) : (
              <Link
                to="/login"
                className="block w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors text-center"
              >
                Get Started
              </Link>
            )}
          </div>
        </div>
      </div>
    </main>
  );
};

const AboutPage = () => (
  <main id="main-content" className="min-h-screen bg-gray-50 flex items-center justify-center" role="main">
    <div className="max-w-2xl w-full bg-white rounded-lg shadow-md p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">About Legal Companion</h1>
      <div className="prose prose-gray max-w-none">
        <p>
          Legal Companion is an AI-driven solution that demystifies complex legal documents
          by transforming them into accessible, actionable guidance.
        </p>
        <h2>Key Features:</h2>
        <ul role="list">
          <li role="listitem"><strong>Multi-Modal Processing:</strong> Upload PDFs, images, DOCX, and scanned documents</li>
          <li role="listitem"><strong>Intelligent Analysis:</strong> AI-powered risk assessment with role-specific analysis</li>
          <li role="listitem"><strong>Plain Language:</strong> Convert legal jargon to accessible language</li>
          <li role="listitem"><strong>Voice Interface:</strong> Ask questions using voice and receive spoken responses</li>
          <li role="listitem"><strong>Privacy-First:</strong> End-to-end encryption and PII protection</li>
          <li role="listitem"><strong>Accessibility-First:</strong> Full keyboard navigation, screen reader support, and customizable themes</li>
        </ul>
        <h2>Powered by Google Cloud AI:</h2>
        <ul role="list">
          <li role="listitem"><strong>Vertex AI:</strong> Advanced language models for analysis</li>
          <li role="listitem"><strong>Document AI:</strong> Intelligent document processing</li>
          <li role="listitem"><strong>Translation API:</strong> Support for 100+ languages</li>
          <li role="listitem"><strong>Speech Services:</strong> Voice-to-voice interactions</li>
        </ul>
        <h2>Accessibility Features:</h2>
        <ul role="list">
          <li role="listitem"><strong>Theme Options:</strong> Light, dark, and high-contrast themes</li>
          <li role="listitem"><strong>Typography Controls:</strong> Adjustable font size, family, and spacing</li>
          <li role="listitem"><strong>Motion Controls:</strong> Reduced motion options for vestibular disorders</li>
          <li role="listitem"><strong>Screen Reader Support:</strong> Full ARIA implementation and announcements</li>
          <li role="listitem"><strong>Keyboard Navigation:</strong> Complete keyboard accessibility</li>
          <li role="listitem"><strong>Dyslexia Support:</strong> Dyslexia-friendly fonts and spacing</li>
        </ul>
      </div>
    </div>
  </main>
);

function App() {
  return (
    <AccessibilityProvider>
      <AuthProvider>
        <Router>
          <div className="App">
            <SkipNavigation />
            <Navigation />
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/firebase-test" element={<FirebaseTest />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/document/:documentId" element={<DocumentAnalysisPage />} />
              <Route path="/voice-qa" element={<VoiceQAPage />} />
              <Route path="/translate" element={<TranslationPage />} />
            </Routes>
            <footer id="footer" className="bg-gray-800 text-white py-8 mt-auto" role="contentinfo">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                  <p className="text-sm text-gray-300">
                    © 2024 Legal Companion. Built with accessibility in mind.
                  </p>
                  <p className="text-xs text-gray-400 mt-2">
                    Powered by Google Cloud AI • Privacy-First Design • WCAG 2.1 AA Compliant
                  </p>
                </div>
              </div>
            </footer>
          </div>
        </Router>
      </AuthProvider>
    </AccessibilityProvider>
  )
}

export default App