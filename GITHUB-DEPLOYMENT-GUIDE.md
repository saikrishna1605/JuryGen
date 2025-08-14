# 🚀 GitHub Deployment Guide for Legal Companion

## Step-by-Step Guide to Push to GitHub

### 1. Initialize Git Repository
```bash
# Navigate to your project root
cd /path/to/your/legal-companion-project

# Initialize git repository
git init

# Add all files to staging
git add .

# Create initial commit
git commit -m "🎉 Initial commit: Legal Companion AI-powered legal document analysis

✨ Features implemented:
- Complete React + TypeScript frontend with Firebase Auth
- FastAPI backend with Google Cloud AI integration
- Multi-modal document processing architecture
- Authentication & security infrastructure
- Comprehensive data models and validation
- Real-time processing pipeline ready
- Voice-to-voice Q&A system foundation
- Multi-language support framework
- Privacy-first design with encryption
- Accessibility features and responsive design

🔧 Tech Stack:
- Frontend: React 18, TypeScript, Vite, TailwindCSS, Firebase
- Backend: FastAPI, Python, Google Cloud AI, CrewAI
- Infrastructure: GCP, Cloud Run, Firestore, Cloud Storage
- AI: Vertex AI Gemini, Document AI, Translation, TTS/STT"
```

### 2. Connect to GitHub Repository
```bash
# Add remote origin (replace with your repository URL)
git remote add origin https://github.com/saikrishna1605/JuryGen.git

# Verify remote
git remote -v
```

### 3. Push to GitHub
```bash
# Push to main branch
git branch -M main
git push -u origin main
```

### 4. Set Up Branch Protection (Optional)
Go to GitHub repository settings and set up branch protection rules for `main` branch.

## 🔐 Environment Variables Setup

### Create GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:
```
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
FIREBASE_PRIVATE_KEY=your_firebase_private_key
FIREBASE_CLIENT_EMAIL=your_service_account_email
```

## 🚀 GitHub Actions CI/CD (Optional)

Create `.github/workflows/ci.yml`:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Type check
      run: |
        cd frontend
        npm run type-check
    
    - name: Build
      run: |
        cd frontend
        npm run build

  backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements-minimal.txt
    
    - name: Test import
      run: |
        cd backend
        python -c "from app.main import app; print('✅ Backend imports successfully')"
```

## 📁 Repository Structure

Your GitHub repository will have this structure:
```
JuryGen/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .kiro/
│   └── specs/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── requirements-minimal.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── infrastructure/
├── docs/
├── .gitignore
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── SETUP.md
└── API-KEYS-CONFIGURED.md
```

## 🌐 GitHub Pages Deployment (Frontend Only)

### 1. Create GitHub Pages Workflow
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install and build
      run: |
        cd frontend
        npm ci
        npm run build
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./frontend/dist
```

### 2. Enable GitHub Pages
1. Go to repository Settings
2. Scroll to Pages section
3. Select "Deploy from a branch"
4. Choose "gh-pages" branch
5. Your site will be available at: `https://saikrishna1605.github.io/JuryGen/`

## 🔧 Development Workflow

### Creating Feature Branches
```bash
# Create and switch to feature branch
git checkout -b feature/document-upload

# Make your changes
# ... code changes ...

# Commit changes
git add .
git commit -m "✨ Add document upload functionality"

# Push feature branch
git push origin feature/document-upload

# Create Pull Request on GitHub
```

### Keeping Fork Updated
```bash
# Add upstream remote (original repository)
git remote add upstream https://github.com/saikrishna1605/JuryGen.git

# Fetch upstream changes
git fetch upstream

# Merge upstream changes
git checkout main
git merge upstream/main

# Push updated main
git push origin main
```

## 📊 Repository Settings

### Recommended Settings
1. **General**:
   - Enable "Automatically delete head branches"
   - Disable "Allow merge commits" (use squash and merge)

2. **Branches**:
   - Set `main` as default branch
   - Enable branch protection rules
   - Require pull request reviews

3. **Security**:
   - Enable "Private vulnerability reporting"
   - Enable "Dependency graph"
   - Enable "Dependabot alerts"

## 🎯 Next Steps After GitHub Setup

1. **Set up continuous deployment** to Google Cloud Run
2. **Configure automated testing** with GitHub Actions
3. **Set up monitoring** and error tracking
4. **Create project documentation** wiki
5. **Set up issue templates** for bug reports and features

## 🤝 Collaboration Features

### Issue Templates
Create `.github/ISSUE_TEMPLATE/` with:
- `bug_report.md` - Bug report template
- `feature_request.md` - Feature request template
- `question.md` - Question template

### Pull Request Template
Create `.github/pull_request_template.md`:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots here
```

Your Legal Companion project is now ready for GitHub! 🚀✨