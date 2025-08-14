# Contributing to Legal Companion

Thank you for your interest in contributing to Legal Companion! This document provides guidelines and information for contributors.

## 🎯 How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or request features
- Provide detailed information including steps to reproduce
- Include relevant logs, screenshots, or error messages

### Submitting Changes
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- Google Cloud Platform account (for full features)
- Firebase project

### Local Development
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/JuryGen.git
cd JuryGen

# Install dependencies
cd frontend && npm install
cd ../backend && pip install -r requirements-minimal.txt

# Start development servers
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm run dev
```

## 📝 Code Style

### Frontend (TypeScript/React)
- Use TypeScript for all new code
- Follow React hooks patterns
- Use functional components
- Implement proper error boundaries
- Add proper TypeScript types

### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public functions
- Use Pydantic models for data validation
- Implement proper error handling

### General Guidelines
- Write clear, descriptive commit messages
- Keep functions small and focused
- Add comments for complex logic
- Update documentation for new features
- Ensure accessibility compliance

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
npm run test
npm run type-check
```

### Backend Testing
```bash
cd backend
pytest
black . --check
isort . --check-only
```

## 📚 Documentation

- Update README.md for new features
- Add API documentation for new endpoints
- Include code comments for complex logic
- Update setup guides if needed

## 🔒 Security

- Never commit API keys or secrets
- Use environment variables for configuration
- Follow security best practices
- Report security issues privately

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] Branch is up to date with main

### PR Description
- Describe what changes were made
- Explain why the changes were necessary
- Include screenshots for UI changes
- Reference related issues

## 🎨 UI/UX Guidelines

- Follow accessibility standards (WCAG 2.1 AA)
- Ensure mobile responsiveness
- Use consistent design patterns
- Test with screen readers
- Support keyboard navigation

## 🌍 Internationalization

- Use translation keys for user-facing text
- Support RTL languages
- Consider cultural differences
- Test with different locales

## 📦 Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Create GitHub release
6. Deploy to production

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Follow the code of conduct
- Celebrate contributions

## 📞 Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Join our community channels
- Reach out to maintainers

Thank you for contributing to Legal Companion! 🎉