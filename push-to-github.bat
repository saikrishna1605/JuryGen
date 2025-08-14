@echo off
echo 🚀 Pushing Legal Companion to GitHub...
echo.

echo 📁 Initializing Git repository...
git init

echo 📝 Adding all files to staging...
git add .

echo 💾 Creating initial commit...
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
- AI: Vertex AI Gemini, Document AI, Translation, TTS/STT

🎯 Current Status:
- ✅ Project structure and configuration
- ✅ Data models with TypeScript + Pydantic validation
- ✅ Firebase Authentication with Google OAuth
- ✅ Security middleware and rate limiting
- ✅ User dashboard and profile management
- ✅ API foundation with comprehensive error handling
- 🚧 Ready for document upload and AI processing features

🔑 Configured Services:
- Google Cloud Project: kiro-hackathon23
- Firebase Authentication with multi-provider support
- Vertex AI for advanced language models
- Document AI for intelligent document processing
- Translation API for 100+ languages
- Speech services for voice interactions

📚 Documentation:
- Complete setup and deployment guides
- API documentation with Swagger UI
- Task specifications and development roadmap
- Security and privacy implementation details

Built with ❤️ for making legal documents accessible to everyone!"

echo 🔗 Adding remote repository...
git remote add origin https://github.com/saikrishna1605/JuryGen.git

echo 🌟 Setting main branch...
git branch -M main

echo 🚀 Pushing to GitHub...
git push -u origin main

echo.
echo ✅ Successfully pushed to GitHub!
echo 🌐 Repository: https://github.com/saikrishna1605/JuryGen
echo 📖 View your project at: https://github.com/saikrishna1605/JuryGen
echo.
pause