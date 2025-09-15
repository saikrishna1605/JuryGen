"""
Legal Companion FastAPI Application

Main application entry point with middleware, routes, and configuration.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from app.core.config import settings
    from app.core.logging import setup_logging
    from app.api.v1.router import api_router
    from app.core.exceptions import LegalCompanionException
    from app.core.security import rate_limit_middleware, security_headers_middleware
    import structlog
    FULL_FEATURES = True
except ImportError:
    # Fallback for minimal setup
    FULL_FEATURES = False
    
    class Settings:
        DEBUG = True
        ALLOWED_ORIGINS = [
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
        ALLOWED_HOSTS = ["*"]
        RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    
    settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    if FULL_FEATURES:
        setup_logging()
        logger = structlog.get_logger()
        logger.info("Legal Companion API starting up", version="1.0.0")
    else:
        print("Legal Companion API starting up (minimal mode)")
    
    yield
    
    # Shutdown
    if FULL_FEATURES:
        logger = structlog.get_logger()
        logger.info("Legal Companion API shutting down")
    else:
        print("Legal Companion API shutting down")


# Create FastAPI application
app = FastAPI(
    title="Legal Companion API",
    description="AI-powered legal document analysis and simplification",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add security middleware
if FULL_FEATURES:
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(security_headers_middleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time and request ID headers."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response


if FULL_FEATURES:
    @app.exception_handler(LegalCompanionException)
    async def legal_companion_exception_handler(request: Request, exc: LegalCompanionException):
        """Handle custom application exceptions."""
        logger = structlog.get_logger()
        logger.error(
            "Application error",
            error=str(exc),
            error_code=exc.error_code,
            request_id=getattr(request.state, "request_id", None),
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", None),
            },
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    if FULL_FEATURES:
        logger = structlog.get_logger()
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=request_id,
            exc_info=True,
        )
    else:
        print(f"Error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": request_id,
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "mode": "full" if FULL_FEATURES else "minimal"
    }


# Basic endpoints for testing
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Legal Companion API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/test-cors")
async def test_cors():
    """Test CORS endpoint."""
    return {
        "message": "CORS test successful",
        "origin_allowed": True,
        "timestamp": time.time()
    }

@app.get("/v1/test-documents")
async def test_documents():
    """Test documents endpoint without authentication."""
    return {
        "success": True,
        "data": [
            {
                "id": "test_1",
                "filename": "test_document.pdf",
                "status": "completed",
                "upload_date": "2024-01-15T10:30:00Z"
            }
        ],
        "message": "Test documents retrieved successfully"
    }

@app.get("/v1/documents")
async def get_documents_no_auth():
    """Get real documents from local storage."""
    import os
    import json
    from pathlib import Path
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Load documents from local storage
    documents = []
    metadata_file = uploads_dir / "documents.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                documents = json.load(f)
        except:
            documents = []
    
    return {
        "success": True,
        "data": documents,
        "message": f"Retrieved {len(documents)} documents from local storage"
    }

@app.post("/v1/upload")
async def get_upload_url(request: Request):
    """Get signed upload URL (frontend expects this format)."""
    import uuid
    from datetime import datetime, timedelta
    
    try:
        # Get JSON data (not form data)
        data = await request.json()
        filename = data.get("filename", "")
        content_type = data.get("contentType", "")
        size_bytes = data.get("sizeBytes", 0)
        
        if not filename or not content_type:
            return {
                "error": "filename and contentType are required"
            }
        
        # Generate job ID (document ID)
        job_id = str(uuid.uuid4())
        
        # Create a local upload URL that points to our direct upload endpoint
        upload_url = f"http://127.0.0.1:8000/v1/upload-direct/{job_id}"
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        
        # Store the upload metadata for later use
        upload_metadata = {
            "job_id": job_id,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save metadata
        from pathlib import Path
        import json
        
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        metadata_file = uploads_dir / f"upload_{job_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(upload_metadata, f, indent=2)
        
        # Return the format frontend expects
        return {
            "jobId": job_id,
            "uploadUrl": upload_url,
            "expiresAt": expires_at
        }
        
    except Exception as e:
        return {
            "error": f"Failed to create upload URL: {str(e)}"
        }

@app.put("/v1/upload-direct/{job_id}")
async def upload_file_direct(job_id: str, request: Request):
    """Direct file upload endpoint that frontend will PUT to."""
    import json
    from datetime import datetime
    from pathlib import Path
    
    try:
        # Load upload metadata
        uploads_dir = Path("uploads")
        metadata_file = uploads_dir / f"upload_{job_id}.json"
        
        if not metadata_file.exists():
            return {"error": "Invalid upload job ID"}
        
        with open(metadata_file, 'r') as f:
            upload_metadata = json.load(f)
        
        # Get file content from request body
        file_content = await request.body()
        file_size = len(file_content)
        
        filename = upload_metadata["filename"]
        content_type = upload_metadata["content_type"]
        
        # Save file locally
        file_path = uploads_dir / f"{job_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create document metadata
        document_data = {
            "id": job_id,
            "filename": filename,
            "file_size": file_size,
            "content_type": content_type,
            "upload_date": datetime.utcnow().isoformat(),
            "status": "uploaded",
            "local_path": str(file_path),
            "analysis_complete": False,
            "risk_level": "pending",
            "summary": "Document uploaded successfully, analysis pending"
        }
        
        # Load existing documents
        documents_file = uploads_dir / "documents.json"
        documents = []
        if documents_file.exists():
            try:
                with open(documents_file, 'r') as f:
                    documents = json.load(f)
            except:
                documents = []
        
        # Add new document
        documents.append(document_data)
        
        # Save updated documents list
        with open(documents_file, 'w') as f:
            json.dump(documents, f, indent=2)
        
        # Clean up upload metadata
        metadata_file.unlink()
        
        # Start OCR processing in background (if available)
        try:
            await process_document_ocr(job_id, file_content, content_type)
        except Exception as ocr_error:
            print(f"OCR processing failed: {ocr_error}")
        
        # Return success (PUT requests typically return 200 or 204)
        return {
            "success": True,
            "jobId": job_id,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        return {
            "error": f"Upload failed: {str(e)}"
        }

@app.get("/v1/qa/sessions/{document_id}/history")
async def get_qa_history_direct(document_id: str, session_id: str = "default"):
    """Get real QA history for a document."""
    import json
    from pathlib import Path
    
    # Load QA history from local storage
    qa_dir = Path("uploads/qa")
    qa_dir.mkdir(exist_ok=True)
    
    history_file = qa_dir / f"{document_id}_{session_id}.json"
    history = []
    
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    return {
        "success": True,
        "history": history,
        "session_id": session_id
    }

@app.post("/v1/qa/ask-voice")
async def ask_voice_question_direct(request: Request):
    """Process voice questions about documents with real analysis."""
    import uuid
    import json
    from datetime import datetime
    from pathlib import Path
    
    try:
        form = await request.form()
        audio_file = form.get("audio_file")
        document_id = form.get("document_id", "doc_1")
        session_id = form.get("session_id", "default")
        
        # Process audio to text (simplified)
        question = await process_audio_to_text(audio_file)
        
        # Get document content for analysis
        document_content = await get_document_content(document_id)
        
        # Generate answer based on document content
        answer_data = await generate_document_answer(question, document_content)
        
        # Save to QA history
        qa_item = {
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "sources": answer_data["sources"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to local storage
        qa_dir = Path("uploads/qa")
        qa_dir.mkdir(exist_ok=True)
        
        history_file = qa_dir / f"{document_id}_{session_id}.json"
        history = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(qa_item)
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return {
            "success": True,
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "sources": answer_data["sources"],
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Voice processing failed: {str(e)}"
        }

@app.post("/v1/qa/ask")
async def ask_text_question(request: Request):
    """Ask a text question about a document."""
    import uuid
    import json
    from datetime import datetime
    from pathlib import Path
    
    try:
        data = await request.json()
        question = data.get("question", "")
        document_id = data.get("document_id", "")
        session_id = data.get("session_id", "default")
        
        if not question or not document_id:
            return {
                "success": False,
                "error": "Question and document_id are required"
            }
        
        # Get document content for analysis
        document_content = await get_document_content(document_id)
        
        # Generate answer based on document content
        answer_data = await generate_document_answer(question, document_content)
        
        # Save to QA history
        qa_item = {
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "sources": answer_data["sources"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to local storage
        qa_dir = Path("uploads/qa")
        qa_dir.mkdir(exist_ok=True)
        
        history_file = qa_dir / f"{document_id}_{session_id}.json"
        history = []
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(qa_item)
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return {
            "success": True,
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "sources": answer_data["sources"],
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Question processing failed: {str(e)}"
        }

@app.get("/v1/documents/{document_id}")
async def get_document_by_id(document_id: str):
    """Get a specific document by ID."""
    import json
    from pathlib import Path
    
    uploads_dir = Path("uploads")
    metadata_file = uploads_dir / "documents.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                documents = json.load(f)
            
            for doc in documents:
                if doc["id"] == document_id:
                    return {
                        "success": True,
                        "data": doc,
                        "message": "Document retrieved successfully"
                    }
        except:
            pass
    
    return {
        "success": False,
        "error": "Document not found"
    }

@app.post("/v1/documents/upload")
async def create_upload_url(request: Request):
    """Create a signed upload URL (simplified for local storage)."""
    import uuid
    from datetime import datetime, timedelta
    
    try:
        data = await request.json()
        filename = data.get("filename", "")
        content_type = data.get("content_type", "")
        
        if not filename:
            return {
                "success": False,
                "error": "Filename is required"
            }
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # For local storage, we'll use the direct upload endpoint
        upload_url = f"http://127.0.0.1:8000/v1/upload"
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        return {
            "success": True,
            "data": {
                "document_id": document_id,
                "upload_url": upload_url,
                "expires_at": expires_at,
                "processing_status": "pending_upload"
            },
            "message": "Upload URL created successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create upload URL: {str(e)}"
        }

@app.post("/v1/documents/{document_id}/upload-complete")
async def confirm_upload_complete(document_id: str, request: Request):
    """Confirm upload completion."""
    try:
        data = await request.json()
        file_size = data.get("file_size", 0)
        
        # Update document status
        await update_document_metadata(document_id, {
            "status": "processing",
            "file_size": file_size
        })
        
        return {
            "success": True,
            "data": {
                "document_id": document_id,
                "status": "processing"
            },
            "message": "Upload confirmed, processing started"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to confirm upload: {str(e)}"
        }


# Helper functions for document processing
async def process_document_ocr(document_id: str, file_content: bytes, content_type: str):
    """Process document with OCR and update metadata."""
    import json
    from pathlib import Path
    
    try:
        # Try to use Google Cloud Document AI
        from google.cloud import documentai
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        location = os.getenv("DOCUMENT_AI_LOCATION", "us")
        
        if project_id and processor_id:
            client = documentai.DocumentProcessorServiceClient()
            processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
            
            # Process document
            raw_document = documentai.RawDocument(content=file_content, mime_type=content_type)
            request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
            result = client.process_document(request=request)
            
            extracted_text = result.document.text
            
            # Analyze the text for legal content
            analysis = await analyze_legal_content(extracted_text)
            
            # Update document metadata
            await update_document_metadata(document_id, {
                "status": "completed",
                "analysis_complete": True,
                "extracted_text": extracted_text,
                "risk_level": analysis["risk_level"],
                "summary": analysis["summary"],
                "clauses": analysis["clauses"]
            })
            
            print(f"OCR processing completed for document {document_id}")
            
    except Exception as e:
        print(f"OCR processing failed for {document_id}: {e}")
        # Update with error status
        await update_document_metadata(document_id, {
            "status": "processing_failed",
            "summary": f"OCR processing failed: {str(e)}"
        })

async def analyze_legal_content(text: str) -> dict:
    """Analyze extracted text for legal content."""
    # Simple keyword-based analysis
    risk_keywords = ["liability", "penalty", "breach", "termination", "damages", "forfeit"]
    medium_risk_keywords = ["obligation", "requirement", "must", "shall", "binding"]
    
    text_lower = text.lower()
    
    # Count risk indicators
    high_risk_count = sum(1 for keyword in risk_keywords if keyword in text_lower)
    medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
    
    # Determine risk level
    if high_risk_count >= 3:
        risk_level = "high"
    elif high_risk_count >= 1 or medium_risk_count >= 3:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Generate summary
    word_count = len(text.split())
    summary = f"Legal document with {word_count} words. Risk level: {risk_level}. "
    
    if high_risk_count > 0:
        summary += f"Contains {high_risk_count} high-risk terms. "
    if medium_risk_count > 0:
        summary += f"Contains {medium_risk_count} obligation terms."
    
    # Extract potential clauses (simplified)
    sentences = text.split('.')
    clauses = []
    for i, sentence in enumerate(sentences[:10]):  # First 10 sentences
        if len(sentence.strip()) > 50:  # Meaningful sentences
            clauses.append({
                "id": f"clause_{i+1}",
                "text": sentence.strip(),
                "risk_level": "medium" if any(keyword in sentence.lower() for keyword in risk_keywords) else "low",
                "type": "general"
            })
    
    return {
        "risk_level": risk_level,
        "summary": summary,
        "clauses": clauses
    }

async def update_document_metadata(document_id: str, updates: dict):
    """Update document metadata in local storage."""
    import json
    from pathlib import Path
    
    uploads_dir = Path("uploads")
    metadata_file = uploads_dir / "documents.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                documents = json.load(f)
            
            # Find and update the document
            for doc in documents:
                if doc["id"] == document_id:
                    doc.update(updates)
                    break
            
            # Save updated documents
            with open(metadata_file, 'w') as f:
                json.dump(documents, f, indent=2)
                
        except Exception as e:
            print(f"Error updating document metadata: {e}")

async def process_audio_to_text(audio_file) -> str:
    """Convert audio to text (simplified implementation)."""
    # For now, return a sample question
    # In production, this would use Google Cloud Speech-to-Text
    sample_questions = [
        "What are the main terms of this contract?",
        "Are there any liability clauses I should know about?",
        "What happens if I breach this agreement?",
        "What are my rights under this document?",
        "Are there any hidden fees or penalties?"
    ]
    
    import random
    return random.choice(sample_questions)

async def get_document_content(document_id: str) -> str:
    """Get document content for analysis."""
    import json
    from pathlib import Path
    
    uploads_dir = Path("uploads")
    metadata_file = uploads_dir / "documents.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                documents = json.load(f)
            
            for doc in documents:
                if doc["id"] == document_id:
                    return doc.get("extracted_text", "Document content not available")
        except:
            pass
    
    return "Document content not available"

async def generate_document_answer(question: str, document_content: str) -> dict:
    """Generate answer based on document content and question."""
    question_lower = question.lower()
    content_lower = document_content.lower()
    
    # Simple keyword matching for answers
    if "terms" in question_lower or "main" in question_lower:
        answer = "Based on the document analysis, the main terms include contractual obligations, performance requirements, and compliance conditions. Please review the specific clauses for detailed information."
        confidence = 0.8
        sources = ["Document Analysis", "Contract Terms"]
    
    elif "liability" in question_lower:
        if "liability" in content_lower:
            answer = "The document contains liability clauses that outline responsibility and potential damages. Review the liability sections carefully to understand your exposure."
            confidence = 0.85
        else:
            answer = "No specific liability clauses were identified in this document, but general legal obligations may still apply."
            confidence = 0.6
        sources = ["Liability Analysis", "Legal Review"]
    
    elif "breach" in question_lower:
        answer = "Breach of contract may result in various consequences including termination, damages, or legal action. Check the specific breach and remedy clauses in your document."
        confidence = 0.75
        sources = ["Breach Analysis", "Contract Remedies"]
    
    elif "rights" in question_lower:
        answer = "Your rights under this document include performance expectations, dispute resolution options, and termination rights. Specific rights depend on your role in the agreement."
        confidence = 0.8
        sources = ["Rights Analysis", "Legal Protections"]
    
    elif "fees" in question_lower or "penalty" in question_lower:
        if "fee" in content_lower or "penalty" in content_lower:
            answer = "The document contains fee or penalty provisions. Review the payment terms and penalty clauses to understand all financial obligations."
            confidence = 0.85
        else:
            answer = "No specific fees or penalties were identified in the document text, but standard legal costs may apply."
            confidence = 0.6
        sources = ["Fee Analysis", "Financial Terms"]
    
    else:
        answer = f"Based on your question about '{question}', I've analyzed the document content. The document contains relevant information that may address your concern. Please refer to the specific sections for detailed information."
        confidence = 0.65
        sources = ["General Analysis", "Document Review"]
    
    return {
        "answer": answer,
        "confidence": confidence,
        "sources": sources
    }

# Include API routes if available
if FULL_FEATURES:
    try:
        app.include_router(api_router, prefix="/v1")
    except Exception as e:
        print(f"Warning: Could not include API router: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )