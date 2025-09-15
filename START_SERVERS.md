# 🚀 Legal Companion - Start Servers Guide

## ✅ **Setup Status:**

### Backend: READY ✅
- Google Cloud Project: `kiro-hackathon23`
- Document AI Processor: `833b693cdf47189e` (Form Parser)
- Cloud Storage Bucket: `kiro-hackathon23-legal-documents`
- Translation API: Enabled and working
- Service Account: Configured with proper permissions

### Frontend: READY ✅
- Firebase Configuration: Complete
- Environment Variables: Set in `.env` file
- Build: Successful (no TypeScript errors)

## 🚀 **Start Instructions:**

### 1. Start Backend Server

```bash
cd backend
python start_server_simple.py
```

**Expected Output:**
```
Starting Legal Companion Backend Server...
==================================================
Real OCR processing (Google Document AI)
Real file storage (Google Cloud Storage)
Real translation (Google Translate API)
No mock or demo functionality
==================================================
Server starting at: http://127.0.0.1:8000
API Documentation: http://127.0.0.1:8000/docs
```

### 2. Start Frontend Development Server

**In a new terminal:**

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
> legal-companion-frontend@1.0.0 dev
> vite

  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

## 🔧 **If Environment Variables Not Loading:**

### Frontend Fix:
1. Stop the frontend server (Ctrl+C)
2. Clear Vite cache: `rm -rf node_modules/.vite` (or delete the folder)
3. Restart: `npm run dev`

### Backend Fix:
1. Verify `.env` file exists in `backend/` directory
2. Check service account key: `backend/service-account-key.json`
3. Restart server

## 🧪 **Test Everything is Working:**

### Test Backend Services:
```bash
cd backend
python test_services_simple.py
```

**Expected Output:**
```
Testing Google Cloud Services...
========================================
Cloud Storage: Connected to kiro-hackathon23-legal-documents
Translation API: Working - Hola
Document AI: Connected to legal-document-processor
Google Cloud services are ready!
```

### Test Frontend Build:
```bash
cd frontend
npm run build
```

**Should complete without errors.**

## 🎯 **What You Can Do:**

### 1. Upload Documents
- Go to http://localhost:5173
- Click "Upload Document"
- Select a PDF or image file
- Real OCR processing will extract text

### 2. Translate Text
- Use the translation feature
- Real Google Translate API
- Supports 100+ languages

### 3. View API Documentation
- Visit http://127.0.0.1:8000/docs
- Interactive Swagger UI
- Test all endpoints

## 🚨 **Troubleshooting:**

### Port Already in Use:
```bash
# Kill process on port 8000 (backend)
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F

# Kill process on port 5173 (frontend)
netstat -ano | findstr :5173
taskkill /PID [PID_NUMBER] /F
```

### Firebase Environment Variables Not Loading:
1. Check `.env` file exists in `frontend/` directory
2. Restart development server: `npm run dev`
3. Clear browser cache and reload

### Google Cloud Services Not Working:
1. Check service account key file exists
2. Verify environment variables in `backend/.env`
3. Run: `python test_services_simple.py` from backend directory

## 🎉 **Success Indicators:**

### Backend Working:
- Server starts without errors
- API docs accessible at http://127.0.0.1:8000/docs
- Test services script passes

### Frontend Working:
- Development server starts
- No environment variable errors in console
- Firebase initializes successfully
- Can access http://localhost:5173

### Full Integration Working:
- Can upload documents
- OCR processing works
- Translation works
- No 404 errors in browser console

---

## 🚀 **Your Legal Companion is ready for production use with real Google Cloud services!**

**No mock data, no demo functionality - everything is real and functional.**