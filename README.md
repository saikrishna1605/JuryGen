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

## 🐳 Quick Start with Docker (Recommended)

The easiest way to get started is using our simplified Docker setup:

```bash
# Clone the repository
git clone https://github.com/saikrishna1605/JuryGen.git
cd JuryGen

# Start development environment
docker-compose up --build

# Or use the deployment script
./scripts/deploy.sh development
```

**That's it!** The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Redis**: localhost:6379

### Docker Commands
```bash
# Development
docker-compose up --build              # Start all services
docker-compose logs -f                 # View logs
docker-compose down                    # Stop services

# Production
docker-compose -f docker-compose.prod.yml up --build

# Using deployment script
./scripts/deploy.sh development        # Start dev environment
./scripts/deploy.sh production         # Start prod environment
./scripts/deploy.sh stop              # Stop all services
```

For detailed Docker setup instructions, see [DOCKER_README.md](DOCKER_README.md).

### AI Services (Google Cloud)
- **Vertex AI Gemini** 1.5 Flash & Pro for analysis
- **Document AI** for OCR and layout understanding
- **Cloud Translation** for multi-language support
- **Text-to-Speech & Speech-to-Text** for voice features

## 🚀 Manual Setup (Alternative)

If you prefer to run services individually without Docker:

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Redis (optional, for caching)
- Google Cloud Platform account (for AI features)
- Firebase project (for authentication)

### 1. Clone the Repository
```bash
git clone https://github.com/saikrishna1605/JuryGen.git
cd JuryGen
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Choose your installation level:

# Option A: Full features (recommended)
pip install -r requirements.txt -r requirements-dev.txt

# Option B: Production only
pip install -r requirements.txt

# Option C: Minimal/testing (lightweight)
pip install -r requirements-minimal.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Environment Configuration
```bash
# Copy environment templates
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# Edit the .env files with your configuration
```

### 5. Start Development Servers
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 6. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Python Requirements Files Explained

The backend uses three different requirements files for different use cases:

### `requirements.txt` - 🏭 Production Dependencies
**Full feature set for production deployment**
- FastAPI, Uvicorn (web framework)
- Google Cloud AI services (Document AI, Translation, Speech, etc.)
- Firebase Admin SDK
- Document processing (PDF, DOCX, images)
- Authentication and security
- Monitoring and logging

```bash
pip install -r requirements.txt  # ~35 packages, ~2-3 min install
```

### `requirements-dev.txt` - 🛠️ Development Tools
**Development, testing, and code quality tools**
- Testing framework (pytest, coverage)
- Code formatting (black, isort, flake8, mypy)
- Development tools (ipython, debugger)
- Security scanning (safety, bandit)
- Documentation tools (mkdocs)

```bash
pip install -r requirements-dev.txt  # ~15 packages, ~1 min install
```

### `requirements-minimal.txt` - 🚀 Lightweight Version
**Bare minimum for basic functionality**
- Core FastAPI and essential utilities only
- No Google Cloud services
- No heavy AI/ML dependencies
- Perfect for quick testing or resource-constrained environments

```bash
pip install -r requirements-minimal.txt  # ~15 packages, ~30 sec install
```

### Usage Examples
```bash
# Full development setup (most common)
pip install -r requirements.txt -r requirements-dev.txt

# Production deployment
pip install -r requirements.txt

# Quick testing without AI features
pip install -r requirements-minimal.txt

# Check for security vulnerabilities
pip install -r requirements-dev.txt
safety check -r requirements.txt
```

## 📖 Documentation

- [**Docker Setup Guide**](DOCKER_README.md) - Complete Docker setup and usage
- [**Environment Configuration**](.env.example) - Environment variables reference
- [**API Documentation**](http://localhost:8000/docs) - Interactive API docs (when running)
- [**Task Specifications**](.kiro/specs/ai-legal-companion/) - Development roadmap

## 🔧 Development Tools

### Code Quality
```bash
# Format code
cd backend
black app/
isort app/

# Lint code
flake8 app/ --max-line-length=100
mypy app/ --ignore-missing-imports

# Run tests
pytest tests/ -v --cov=app
```

### Frontend Tools
```bash
cd frontend
npm run lint          # ESLint
npm run type-check     # TypeScript
npm run test          # Vitest
npm run build         # Production build
```

### Docker Development
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec frontend sh

# Rebuild specific service
docker-compose build backend
docker-compose up backend
```

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
- **Google Cloud AI** - AI/ML services (optional)
- **CrewAI** - Multi-agent orchestration (optional)

### Development & Deployment
- **Docker** - Containerization with simplified setup
- **Docker Compose** - Multi-service orchestration
- **GitHub Actions** - Simple CI/CD pipeline
- **Redis** - Caching and session storage

### Infrastructure (Optional)
- **Google Cloud Platform** - Cloud services and AI
- **Firebase** - Authentication and database
- **Cloud Run** - Serverless container platform
- **Cloud Storage** - File storage and CDN

## 🐳 Docker Architecture

Our simplified Docker setup includes:

### Development Environment (`docker-compose.yml`)
- **Frontend**: React dev server with hot reload (port 5173)
- **Backend**: FastAPI with auto-reload (port 8000)
- **Redis**: Caching and sessions (port 6379)

### Production Environment (`docker-compose.prod.yml`)
- **Frontend**: Nginx-served optimized build (port 80)
- **Backend**: Multi-worker FastAPI (port 8000)
- **Redis**: Persistent caching with resource limits

### Key Features
- ✅ **Simple**: Only 3 services instead of 15+
- ✅ **Fast**: Lightweight containers, quick startup
- ✅ **Scalable**: Easy to add services when needed
- ✅ **Secure**: Non-root users, health checks
- ✅ **Documented**: Clear setup instructions

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow
1. **Fork the repository**
2. **Clone and setup**:
   ```bash
   git clone https://github.com/your-username/JuryGen.git
   cd JuryGen
   docker-compose up --build  # Easiest way to start
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** and test them
5. **Run quality checks**:
   ```bash
   # Backend
   cd backend
   black app/ && isort app/ && flake8 app/ && pytest tests/
   
   # Frontend
   cd frontend
   npm run lint && npm run type-check && npm run test
   ```
6. **Submit a pull request**

### Quick Development Setup
```bash
# Option 1: Docker (recommended)
docker-compose up --build

# Option 2: Manual setup
cd backend && pip install -r requirements.txt -r requirements-dev.txt
cd frontend && npm install
```

### Project Structure
```
JuryGen/
├── frontend/           # React TypeScript app
├── backend/           # FastAPI Python app
├── docker-compose.yml # Development environment
├── scripts/          # Deployment helpers
└── .github/          # CI/CD workflows
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Cloud AI** for powerful AI services
- **Firebase** for authentication and real-time features
- **CrewAI** for multi-agent orchestration
- **React & FastAPI** communities for excellent frameworks

## 🆘 Troubleshooting

### Common Issues

**Docker port conflicts**:
```bash
# Check what's using the ports
netstat -tulpn | grep :5173
netstat -tulpn | grep :8000

# Change ports in docker-compose.yml if needed
```

**Python dependency issues**:
```bash
# Try minimal installation first
pip install -r requirements-minimal.txt

# Then add full features if needed
pip install -r requirements.txt
```

**Frontend build issues**:
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Container won't start**:
```bash
# Check logs
docker-compose logs [service-name]

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/saikrishna1605/JuryGen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/saikrishna1605/JuryGen/discussions)
- **Docker Help**: See [DOCKER_README.md](DOCKER_README.md) for detailed Docker instructions

---

**Built with ❤️ for making legal documents accessible to everyone**