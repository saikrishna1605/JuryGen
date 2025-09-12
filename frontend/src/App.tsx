import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AccessibilityProvider } from './contexts/AccessibilityContext';
import { SkipNavigation } from './components/accessibility/SkipNavigation';
import { AccessibilityControls } from './components/accessibility/AccessibilityControls';
import { Settings, Sparkles, Zap, Shield, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import DocumentAnalysisPage from './pages/DocumentAnalysisPage';
import VoiceQAPage from './pages/VoiceQAPage';
import TranslationPage from './pages/TranslationPage';

// Firebase Test Component
import FirebaseTest from './components/FirebaseTest';

// UI Components
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';
import { GlowingOrb } from './components/ui/GlowingOrb';
import { AnimatedBackground } from './components/ui/AnimatedBackground';

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
    <motion.nav 
      id="navigation" 
      className="relative bg-dark-900/80 backdrop-blur-xl border-b border-dark-700/50 shadow-lg" 
      role="navigation" 
      aria-label="Main navigation"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link 
              to="/" 
              className="flex items-center space-x-2 text-xl font-bold text-white hover:text-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300"
              aria-label="Legal Companion - Home"
            >
              <GlowingOrb size="sm" animate={false} />
              <span className="bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                Legal Companion
              </span>
            </Link>
          </div>
          
          <div className="flex items-center space-x-2">
            <Link 
              to="/" 
              className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
            >
              About
            </Link>
            <Link 
              to="/firebase-test" 
              className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
            >
              Firebase Test
            </Link>
            
            {/* Accessibility Controls Toggle */}
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAccessibilityControls(!showAccessibilityControls)}
                aria-label="Toggle accessibility settings"
                aria-expanded={showAccessibilityControls}
                aria-haspopup="true"
                icon={<Settings className="w-4 h-4" />}
              >
                <span className="sr-only">Settings</span>
              </Button>
              
              {showAccessibilityControls && (
                <motion.div 
                  className="absolute right-0 top-full mt-2 z-50"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                >
                  <AccessibilityControls 
                    compact={true}
                    onClose={() => setShowAccessibilityControls(false)}
                  />
                </motion.div>
              )}
            </div>

            {currentUser ? (
              <>
                <Link 
                  to="/dashboard" 
                  className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/upload" 
                  className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
                >
                  Upload
                </Link>
                <Link 
                  to="/voice-qa" 
                  className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
                >
                  Voice Q&A
                </Link>
                <Link 
                  to="/translate" 
                  className="text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-3 py-2 transition-all duration-300 hover:bg-dark-800/50"
                >
                  Translate
                </Link>
                
                <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-dark-700">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                      {(currentUser.displayName || currentUser.email || 'U')[0].toUpperCase()}
                    </div>
                    <span className="text-sm text-dark-300 hidden sm:block">
                      {currentUser.displayName || currentUser.email || 'User'}
                    </span>
                  </div>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={handleLogout}
                  >
                    Sign Out
                  </Button>
                </div>
              </>
            ) : (
              <Button
                variant="neon"
                size="md"
                glow
                onClick={() => window.location.href = '/login'}
              >
                Sign In
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

// Home page component
const HomePage = () => {
  const { currentUser } = useAuth();

  const features = [
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: "AI-Powered Analysis",
      description: "Advanced document processing with intelligent clause classification",
      color: "primary"
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Voice-to-Voice Q&A",
      description: "Ask questions using voice and receive spoken responses",
      color: "accent"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Privacy-First",
      description: "End-to-end encryption with automatic PII protection",
      color: "success"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Multi-Language",
      description: "Support for 100+ languages with real-time translation",
      color: "warning"
    }
  ];

  return (
    <main id="main-content" className="relative min-h-screen bg-dark-900 overflow-hidden" role="main">
      {/* Animated Background */}
      <AnimatedBackground variant="mesh" />
      
      <div className="relative z-10 flex items-center justify-center min-h-screen px-4 py-16">
        <div className="max-w-4xl w-full">
          {/* Hero Section */}
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex justify-center mb-8">
              <GlowingOrb size="xl" intensity="high" />
            </div>
            
            <motion.h1 
              className="text-6xl md:text-7xl font-bold mb-6"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.8 }}
            >
              <span className="bg-gradient-to-r from-primary-400 via-accent-400 to-primary-400 bg-clip-text text-transparent bg-[length:200%_100%] animate-gradient">
                Legal Companion
              </span>
            </motion.h1>
            
            <motion.p 
              className="text-xl md:text-2xl text-dark-300 mb-8 max-w-2xl mx-auto leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.8 }}
            >
              Transform complex legal documents into accessible, actionable guidance with 
              <span className="text-primary-400 font-semibold"> AI-powered analysis</span>
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.8 }}
            >
              {currentUser ? (
                <Button
                  variant="neon"
                  size="xl"
                  glow
                  gradient
                  onClick={() => window.location.href = '/dashboard'}
                  className="text-lg px-8 py-4"
                >
                  Go to Dashboard
                </Button>
              ) : (
                <Button
                  variant="neon"
                  size="xl"
                  glow
                  gradient
                  onClick={() => window.location.href = '/login'}
                  className="text-lg px-8 py-4"
                >
                  Get Started
                </Button>
              )}
            </motion.div>
          </motion.div>

          {/* Features Grid */}
          <motion.div 
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.8 }}
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + index * 0.1, duration: 0.6 }}
              >
                <Card 
                  hover 
                  glow 
                  blur
                  className="p-6 h-full text-center group"
                >
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-r from-${feature.color}-500 to-${feature.color}-600 text-white mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-dark-300 text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </Card>
              </motion.div>
            ))}
          </motion.div>

          {/* Status Card */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.8 }}
            className="max-w-2xl mx-auto"
          >
            <Card neon blur className="p-8 text-center">
              <div className="flex items-center justify-center mb-4">
                <div className="w-3 h-3 bg-success-500 rounded-full animate-pulse mr-2"></div>
                <span className="text-success-400 font-semibold">System Status: Online</span>
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-4">
                {currentUser 
                  ? `Welcome back, ${currentUser.displayName || 'User'}!`
                  : 'Ready to Transform Legal Documents?'
                }
              </h2>
              
              <p className="text-dark-300 mb-6">
                {currentUser 
                  ? 'Your dashboard is ready with advanced AI tools for document analysis, voice Q&A, and multi-language support.'
                  : 'Join thousands of users who trust Legal Companion for intelligent document analysis and plain-language explanations.'
                }
              </p>

              <div className="flex flex-wrap justify-center gap-4">
                <div className="flex items-center text-sm text-dark-400">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mr-2"></div>
                  Multi-modal Processing
                </div>
                <div className="flex items-center text-sm text-dark-400">
                  <div className="w-2 h-2 bg-accent-500 rounded-full mr-2"></div>
                  Voice Interface
                </div>
                <div className="flex items-center text-sm text-dark-400">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                  100+ Languages
                </div>
                <div className="flex items-center text-sm text-dark-400">
                  <div className="w-2 h-2 bg-warning-500 rounded-full mr-2"></div>
                  Privacy-First
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </main>
  );
};

const AboutPage = () => {
  const techStack = [
    { name: "Vertex AI", description: "Advanced language models for analysis", icon: "🧠" },
    { name: "Document AI", description: "Intelligent document processing", icon: "📄" },
    { name: "Translation API", description: "Support for 100+ languages", icon: "🌍" },
    { name: "Speech Services", description: "Voice-to-voice interactions", icon: "🎤" },
  ];

  const accessibilityFeatures = [
    { name: "Theme Options", description: "Light, dark, and high-contrast themes", icon: "🎨" },
    { name: "Typography Controls", description: "Adjustable font size, family, and spacing", icon: "📝" },
    { name: "Motion Controls", description: "Reduced motion options for vestibular disorders", icon: "🔄" },
    { name: "Screen Reader Support", description: "Full ARIA implementation and announcements", icon: "🔊" },
    { name: "Keyboard Navigation", description: "Complete keyboard accessibility", icon: "⌨️" },
    { name: "Dyslexia Support", description: "Dyslexia-friendly fonts and spacing", icon: "👁️" },
  ];

  return (
    <main id="main-content" className="relative min-h-screen bg-dark-900 overflow-hidden" role="main">
      <AnimatedBackground variant="aurora" />
      
      <div className="relative z-10 py-16 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                About Legal Companion
              </span>
            </h1>
            <p className="text-xl text-dark-300 max-w-3xl mx-auto leading-relaxed">
              An AI-driven solution that demystifies complex legal documents by transforming them 
              into accessible, actionable guidance with cutting-edge technology.
            </p>
          </motion.div>

          {/* Main Features */}
          <motion.div 
            className="mb-16"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <Card blur glow className="p-8">
              <h2 className="text-3xl font-bold text-white mb-8 text-center">Key Features</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[
                  { title: "Multi-Modal Processing", desc: "Upload PDFs, images, DOCX, and scanned documents", icon: "📁" },
                  { title: "Intelligent Analysis", desc: "AI-powered risk assessment with role-specific analysis", icon: "🤖" },
                  { title: "Plain Language", desc: "Convert legal jargon to accessible language", icon: "💬" },
                  { title: "Voice Interface", desc: "Ask questions using voice and receive spoken responses", icon: "🎙️" },
                  { title: "Privacy-First", desc: "End-to-end encryption and PII protection", icon: "🔒" },
                  { title: "Accessibility-First", desc: "Full keyboard navigation and screen reader support", icon: "♿" },
                ].map((feature, index) => (
                  <motion.div
                    key={feature.title}
                    className="p-4 rounded-xl bg-dark-800/50 border border-dark-700/50 hover:border-primary-500/50 transition-all duration-300"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.1, duration: 0.6 }}
                  >
                    <div className="text-2xl mb-2">{feature.icon}</div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-dark-300 text-sm">{feature.desc}</p>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Tech Stack */}
          <motion.div 
            className="mb-16"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            <Card neon blur className="p-8">
              <h2 className="text-3xl font-bold text-white mb-8 text-center">
                Powered by Google Cloud AI
              </h2>
              <div className="grid md:grid-cols-2 gap-6">
                {techStack.map((tech, index) => (
                  <motion.div
                    key={tech.name}
                    className="flex items-start space-x-4 p-4 rounded-xl bg-gradient-to-r from-primary-500/10 to-accent-500/10 border border-primary-500/20"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.1, duration: 0.6 }}
                  >
                    <div className="text-2xl">{tech.icon}</div>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">{tech.name}</h3>
                      <p className="text-dark-300 text-sm">{tech.description}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Accessibility Features */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
          >
            <Card gradient blur className="p-8">
              <h2 className="text-3xl font-bold text-white mb-8 text-center">
                Accessibility Features
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {accessibilityFeatures.map((feature, index) => (
                  <motion.div
                    key={feature.name}
                    className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.7 + index * 0.1, duration: 0.6 }}
                  >
                    <div className="text-2xl mb-2">{feature.icon}</div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feature.name}</h3>
                    <p className="text-dark-300 text-sm">{feature.description}</p>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </main>
  );
};

function App() {
  return (
    <div className="dark">
      <AccessibilityProvider>
        <AuthProvider>
          <Router>
            <div className="App min-h-screen bg-dark-900 text-white">
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
              
              {/* Footer */}
              <motion.footer 
                id="footer" 
                className="relative bg-dark-900/80 backdrop-blur-xl border-t border-dark-700/50 py-12 mt-16" 
                role="contentinfo"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1, duration: 0.8 }}
              >
                <AnimatedBackground variant="particles" />
                <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="text-center">
                    <div className="flex justify-center mb-6">
                      <GlowingOrb size="md" intensity="low" />
                    </div>
                    
                    <motion.p 
                      className="text-lg text-dark-300 mb-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.2, duration: 0.6 }}
                    >
                      © 2024 Legal Companion. Built with accessibility in mind.
                    </motion.p>
                    
                    <motion.div 
                      className="flex flex-wrap justify-center gap-6 text-sm text-dark-400"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.4, duration: 0.6 }}
                    >
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-primary-500 rounded-full mr-2 animate-pulse"></div>
                        Powered by Google Cloud AI
                      </div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-success-500 rounded-full mr-2 animate-pulse"></div>
                        Privacy-First Design
                      </div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-accent-500 rounded-full mr-2 animate-pulse"></div>
                        WCAG 2.1 AA Compliant
                      </div>
                    </motion.div>
                  </div>
                </div>
              </motion.footer>
            </div>
          </Router>
        </AuthProvider>
      </AccessibilityProvider>
    </div>
  )
}

export default App