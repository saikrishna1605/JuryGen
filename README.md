# 🏛️ Legal Companion - AI-Powered Legal Document Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Firebase](https://img.shields.io/badge/Firebase-10.7.1-orange.svg)](https://firebase.google.com/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-AI%20Services-blue.svg)](https://cloud.google.com/)

> **Transform complex legal documents into accessible, actionable guidance with AI-powered analysis, multi-language support, and voice-to-voice interactions.**

## 🌟 Features

### 🤖 AI-Powered Analysis
- **Intelligent Clause Classification**: Automatically categorize clauses as Beneficial, Caution, or Risky
- **Role-Specific Analysis**: Tailored insights for tenants, landlords, borrowers, lenders, and more
- **Risk Assessment**: Impact and likelihood scoring with safer alternative suggestions
- **Plain Language Summaries**: Convert legal jargon to 8th-grade reading level

### 🎤 Multi-Modal Interface
- **Document Upload**: Support for PDFs, DOCX, images, and scanned documents
- **Voice-to-Voice Q&A**: Ask questions using voice and receive spoken responses
- **OCR Processing**: Advanced document digitization with layout understanding
- **Real-Time Processing**: Live progress updates with Server-Sent Events

### 🌍 Accessibility & Inclusion
- **100+ Languages**: Translation and analysis in multiple languages
- **Accessibility Features**: High contrast, dyslexia-friendly fonts, screen reader support
- **Voice Synthesis**: Text-to-speech with synchronized captions
- **Mobile Responsive**: Progressive Web App with offline capabilities

### 🔒 Privacy & Security
- **End-to-End Encryption**: CMEK encryption for all stored documents
- **PII Protection**: Automatic detection and masking of sensitive information
- **Data Lifecycle**: Configurable retention periods with automatic deletion
- **Firebase Authentication**: Secure multi-provider authentication

## 🏗️ Architecture

### Frontend (React + TypeScript)
- **React 18** with Vite for fast development
- **TailwindCSS** for responsive, accessible design
- **Firebase SDK** for authentication and real-time features
- **TypeScript** for type safety and better developer experience

### Backend (FastAPI + Python)
- **FastAPI** for high-performance async API
- **CrewAI** for multi-agent orchestration
- **Google Cloud AI** services integration
- **Firebase Admin SDK** for secure authentication

### AI Services (Google Cloud)
- **Vertex AI Gemini** 1.5 Flash & Pro for analysis
- **Document AI** for OCR and layout understanding
- **Cloud Translation** for multi-language support
- **Text-to-Speech & Speech-to-Text** for voice features

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Google Cloud Platform account
- Firebase project

### 1. Clone the Repository
```bash
git clone https://github.com/saikrishna1605/JuryGen.git
cd JuryGen
```

### 2. Install Dependencies
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
pip install -r requirements-minimal.txt
```

### 3. Configure Environment
```bash
# Frontend - Copy and configure
cp frontend/.env.example frontend/.env

# Backend - Copy and configure
cp backend/.env.example backend/.env
```

### 4. Start Development Servers
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Documentation

- [**Setup Guide**](SETUP.md) - Detailed installation and configuration
- [**API Documentation**](docs/API.md) - Complete API reference
- [**Deployment Guide**](docs/DEPLOYMENT.md) - Production deployment instructions
- [**Task Specifications**](.kiro/specs/ai-legal-companion/) - Development roadmap

## 🎯 Current Status

### ✅ Completed Features
- **Project Structure**: Complete frontend/backend architecture
- **Data Models**: TypeScript + Pydantic validation
- **Authentication**: Firebase Auth with Google OAuth
- **Security**: Rate limiting, CORS, security headers
- **UI Components**: Login, dashboard, profile management
- **API Foundation**: FastAPI with comprehensive error handling

### 🚧 In Development
- Document upload and processing
- AI-powered clause analysis
- Voice-to-voice Q&A system
- Multi-language translation
- Export and sharing features

## 🛠️ Technology Stack

### Frontend
- **React 18** - Modern React with hooks and context
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Firebase SDK** - Authentication and real-time features

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and serialization
- **Firebase Admin** - Server-side authentication
- **Google Cloud AI** - AI/ML services
- **CrewAI** - Multi-agent orchestration

### Infrastructure
- **Google Cloud Platform** - Cloud services and AI
- **Firebase** - Authentication and database
- **Cloud Run** - Serverless container platform
- **Cloud Storage** - File storage and CDN

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Cloud AI** for powerful AI services
- **Firebase** for authentication and real-time features
- **CrewAI** for multi-agent orchestration
- **React & FastAPI** communities for excellent frameworks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/saikrishna1605/JuryGen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/saikrishna1605/JuryGen/discussions)
- **Documentation**: [Project Wiki](https://github.com/saikrishna1605/JuryGen/wiki)

---

**Built with ❤️ for making legal documents accessible to everyone**