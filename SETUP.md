# Legal Companion - Setup Instructions

This guide will help you set up and run the Legal Companion application locally.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 18+** and npm/yarn
- **Python 3.11+**
- **Git**

## Quick Start

### 1. Install Dependencies

#### Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
```

#### Backend Setup (Minimal - for basic functionality)
```bash
cd backend
pip install -r requirements-minimal.txt
```

#### Backend Setup (Full - for complete functionality)
```bash
cd backend
pip install -r requirements.txt
```
*Note: Full setup requires Google Cloud services configuration*

### 2. Environment Configuration

Environment files are already created with demo values. For basic testing, no changes are needed.

#### Frontend Environment
The file `frontend/.env` is already configured with demo values:
- API points to `http://localhost:8000/v1`
- Debug mode enabled
- Voice features enabled

#### Backend Environment  
The file `backend/.env` is already configured with demo values:
- Development mode enabled
- CORS configured for frontend
- Basic security settings

**For production or full functionality**, update these files with your actual:
- Firebase project credentials
- Google Cloud project settings
- API keys and secrets

### 3. Run the Application

#### Option A: Use Batch Files (Windows)
```bash
# Start backend (double-click or run in terminal)
start-backend.bat

# Start frontend (double-click or run in terminal)  
start-frontend.bat
```

#### Option B: Manual Commands

**Start Backend Server**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend Development Server**
```bash
cd frontend
npm run dev
```

The backend will be available at: http://localhost:8000
The frontend will be available at: http://localhost:3000

### 4. Verify Installation

1. **Backend Health Check**: Visit http://localhost:8000/health
2. **Frontend**: Visit http://localhost:3000
3. **API Documentation**: Visit http://localhost:8000/docs (Swagger UI)

## Development Workflow

### Frontend Development
```bash
cd frontend

# Start development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Run tests
npm run test
```

### Backend Development
```bash
cd backend

# Start development server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .

# Sort imports
isort .

# Type checking
mypy .
```

## Project Structure

```
legal-companion/
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/             # Route components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API clients
│   │   ├── stores/            # Zustand stores
│   │   ├── utils/             # Helper functions
│   │   └── types/             # TypeScript definitions
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/               # FastAPI routes
│   │   ├── core/              # Configuration
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Business logic
│   │   └── utils/             # Helper functions
│   ├── requirements.txt
│   └── Dockerfile
├── infrastructure/              # IaC and deployment
└── docs/                       # Documentation
```

## Available Scripts

### Frontend Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run type-check` - Run TypeScript type checking
- `npm run test` - Run tests

### Backend Scripts
- `uvicorn app.main:app --reload` - Start development server
- `pytest` - Run tests
- `black .` - Format code
- `isort .` - Sort imports
- `mypy .` - Type checking

## Troubleshooting

### Common Issues

#### Port Already in Use
If you get a "port already in use" error:
```bash
# Kill process on port 3000 (frontend)
npx kill-port 3000

# Kill process on port 8000 (backend)
npx kill-port 8000
```

#### Python Dependencies
If you have issues with Python dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Node Dependencies
If you have issues with Node dependencies:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Development Tips

1. **Hot Reload**: Both frontend and backend support hot reload during development
2. **API Documentation**: Visit http://localhost:8000/docs for interactive API documentation
3. **Type Safety**: The project uses TypeScript for frontend and Pydantic for backend type safety
4. **Code Quality**: ESLint, Prettier, Black, and isort are configured for code formatting

## Next Steps

Once you have the basic application running:

1. **Configure Google Cloud Services** (for full functionality):
   - Set up Firebase project
   - Enable Vertex AI, Document AI, Translation, TTS services
   - Configure service account credentials

2. **Implement Additional Features**:
   - Follow the implementation tasks in `.kiro/specs/ai-legal-companion/tasks.md`
   - Start with authentication and document upload features

3. **Deploy to Production**:
   - Follow the deployment guide in `docs/DEPLOYMENT.md`
   - Set up CI/CD pipeline with Cloud Build

## Getting Help

- Check the API documentation at http://localhost:8000/docs
- Review the project specifications in `.kiro/specs/ai-legal-companion/`
- Check the troubleshooting section above
- Review logs in the terminal for error messages

Happy coding! 🚀