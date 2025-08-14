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
        ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
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
    allow_origins=settings.ALLOWED_ORIGINS,
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