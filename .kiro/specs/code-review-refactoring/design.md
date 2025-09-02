# Design Document

## Overview

This design document outlines the comprehensive refactoring and code quality improvements for the Legal Companion AI-powered legal document analysis application. The application consists of a React TypeScript frontend, FastAPI Python backend, and various Google Cloud services integrations. The refactoring will address security vulnerabilities, code quality issues, performance optimizations, and deployment readiness.

## Architecture

### Current Architecture Analysis

The application follows a modern microservices architecture with:

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: FastAPI + Python 3.11 + Pydantic
- **Database**: Google Firestore
- **AI Services**: Google Cloud Vertex AI, Document AI, Translation API
- **Authentication**: Firebase Auth
- **Storage**: Google Cloud Storage
- **Deployment**: Docker containers with Cloud Run

### Identified Issues

1. **Security Issues**:
   - Hardcoded API keys and project IDs in configuration files
   - Exposed Firebase credentials in git history
   - Insufficient environment variable validation
   - Missing security headers and CSRF protection

2. **Code Quality Issues**:
   - Inconsistent error handling patterns
   - Missing type annotations in Python code
   - Incomplete exception handling
   - TODO comments indicating unfinished features
   - Inconsistent logging patterns

3. **Performance Issues**:
   - No caching strategies implemented
   - Missing bundle optimization
   - Inefficient API call patterns
   - No connection pooling

4. **Deployment Issues**:
   - Hardcoded localhost URLs in configuration
   - Missing health check implementations
   - Incomplete Docker configurations
   - No proper environment separation

## Components and Interfaces

### 1. Configuration Management System

#### Backend Configuration (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # Environment validation with proper defaults
    ENVIRONMENT: Literal["development", "staging", "production"]
    DEBUG: bool = Field(default=False)
    
    # Security settings with validation
    SECRET_KEY: SecretStr = Field(min_length=32)
    ALLOWED_ORIGINS: List[AnyHttpUrl]
    ALLOWED_HOSTS: List[str]
    
    # Google Cloud settings with validation
    GOOGLE_CLOUD_PROJECT: str = Field(min_length=1)
    VERTEX_AI_LOCATION: str = Field(default="us-central1")
    
    # Database settings
    FIRESTORE_DATABASE_ID: str = Field(default="(default)")
    
    # Feature flags
    ENABLE_VOICE_FEATURES: bool = Field(default=True)
    ENABLE_TRANSLATION: bool = Field(default=True)
    
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if isinstance(v, SecretStr):
            secret = v.get_secret_value()
        else:
            secret = v
        if len(secret) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    def validate_origins(cls, v):
        if not v:
            raise ValueError('ALLOWED_ORIGINS cannot be empty')
        return v
```

#### Frontend Configuration (`src/config/environment.ts`)

```typescript
interface EnvironmentConfig {
  apiBaseUrl: string;
  firebase: {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
  };
  features: {
    enableAnalytics: boolean;
    enableVoiceFeatures: boolean;
    enableTranslation: boolean;
  };
}

const validateEnvironment = (): EnvironmentConfig => {
  const requiredVars = [
    'VITE_API_BASE_URL',
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN',
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_STORAGE_BUCKET',
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    'VITE_FIREBASE_APP_ID',
  ];

  const missing = requiredVars.filter(
    (varName) => !import.meta.env[varName]
  );

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}`
    );
  }

  return {
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
    firebase: {
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
      authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
      storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
      messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
      appId: import.meta.env.VITE_FIREBASE_APP_ID,
    },
    features: {
      enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
      enableVoiceFeatures: import.meta.env.VITE_ENABLE_VOICE_FEATURES !== 'false',
      enableTranslation: import.meta.env.VITE_ENABLE_TRANSLATION !== 'false',
    },
  };
};

export const config = validateEnvironment();
```

### 2. Enhanced Error Handling System

#### Backend Error Handling (`app/core/exceptions.py`)

```python
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
import structlog

logger = structlog.get_logger()

class LegalCompanionException(HTTPException):
    """Base exception for Legal Companion application."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "error": error_code,
                "message": message,
                "details": self.details,
            },
            headers=headers,
        )
        
        # Log the exception
        logger.error(
            "Application exception",
            error_code=error_code,
            message=message,
            details=self.details,
            status_code=status_code,
        )

class ValidationError(LegalCompanionException):
    def __init__(self, message: str, field: str = None, details: Dict = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message=message,
            details={"field": field, **(details or {})},
        )

class AuthenticationError(LegalCompanionException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            message=message,
        )

class AuthorizationError(LegalCompanionException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            message=message,
        )
```

#### Frontend Error Handling (`src/lib/errors.ts`)

```typescript
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiError';
  }

  static fromResponse(response: any): ApiError {
    const { status, data } = response;
    return new ApiError(
      status,
      data?.error || 'UNKNOWN_ERROR',
      data?.message || 'An unexpected error occurred',
      data?.details
    );
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network connection failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public field?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}
```

### 3. Logging and Monitoring System

#### Backend Logging (`app/core/logging.py`)

```python
import structlog
import logging
from typing import Any, Dict
from app.core.config import settings

def setup_logging():
    """Configure structured logging."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(message)s",
    )

class RequestLogger:
    """Request logging middleware."""
    
    def __init__(self):
        self.logger = structlog.get_logger()
    
    async def log_request(self, request, response, process_time: float):
        """Log request details."""
        self.logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            user_agent=request.headers.get("user-agent"),
            request_id=getattr(request.state, "request_id", None),
        )
```

#### Frontend Logging (`src/lib/logger.ts`)

```typescript
interface LogContext {
  userId?: string;
  sessionId?: string;
  requestId?: string;
  component?: string;
  action?: string;
  [key: string]: any;
}

class Logger {
  private context: LogContext = {};

  setContext(context: Partial<LogContext>) {
    this.context = { ...this.context, ...context };
  }

  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: any) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: this.context,
      data,
    };

    // Console logging for development
    if (import.meta.env.DEV) {
      console[level](message, logEntry);
    }

    // Send to monitoring service in production
    if (import.meta.env.PROD && level === 'error') {
      this.sendToMonitoring(logEntry);
    }
  }

  private async sendToMonitoring(logEntry: any) {
    try {
      // Send to monitoring service (e.g., Sentry, LogRocket)
      // Implementation depends on chosen service
    } catch (error) {
      console.error('Failed to send log to monitoring service:', error);
    }
  }

  debug(message: string, data?: any) {
    this.log('debug', message, data);
  }

  info(message: string, data?: any) {
    this.log('info', message, data);
  }

  warn(message: string, data?: any) {
    this.log('warn', message, data);
  }

  error(message: string, error?: Error | any) {
    this.log('error', message, error);
  }
}

export const logger = new Logger();
```

### 4. Security Enhancement System

#### Backend Security Middleware (`app/core/security.py`)

```python
from fastapi import Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from typing import Dict, Optional

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class FirebaseAuthBearer(HTTPBearer):
    """Firebase authentication bearer token handler."""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials = await super().__call__(request)
        if credentials:
            # Verify Firebase token here
            # Implementation depends on Firebase Admin SDK
            pass
        return credentials
```

### 5. Performance Optimization System

#### Frontend Performance (`src/lib/performance.ts`)

```typescript
// Lazy loading utilities
export const lazyImport = <T extends Record<string, any>>(
  importFn: () => Promise<T>
) => {
  return React.lazy(() => importFn());
};

// API caching with React Query
export const createApiClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        cacheTime: 10 * 60 * 1000, // 10 minutes
        retry: (failureCount, error: any) => {
          if (error?.status >= 400 && error?.status < 500) {
            return false; // Don't retry client errors
          }
          return failureCount < 3;
        },
      },
    },
  });
};

// Bundle optimization
export const preloadRoute = (routeComponent: () => Promise<any>) => {
  const componentImport = routeComponent();
  return componentImport;
};

// Performance monitoring
export const performanceMonitor = {
  markStart: (name: string) => {
    performance.mark(`${name}-start`);
  },
  
  markEnd: (name: string) => {
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
    
    const measure = performance.getEntriesByName(name)[0];
    if (measure.duration > 1000) { // Log slow operations
      console.warn(`Slow operation detected: ${name} took ${measure.duration}ms`);
    }
  },
};
```

#### Backend Performance (`app/core/performance.py`)

```python
import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
import structlog

logger = structlog.get_logger()

class PerformanceMonitor:
    """Performance monitoring utilities."""
    
    @staticmethod
    def monitor_async(func_name: Optional[str] = None):
        """Decorator to monitor async function performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                name = func_name or f"{func.__module__}.{func.__name__}"
                
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    logger.info(
                        "Function completed",
                        function=name,
                        duration=duration,
                        success=True,
                    )
                    
                    if duration > 5.0:  # Log slow operations
                        logger.warning(
                            "Slow operation detected",
                            function=name,
                            duration=duration,
                        )
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        "Function failed",
                        function=name,
                        duration=duration,
                        error=str(e),
                        success=False,
                    )
                    raise
                    
            return wrapper
        return decorator

class ConnectionPool:
    """Connection pooling for external services."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
    
    async def acquire(self):
        """Acquire a connection from the pool."""
        await self.semaphore.acquire()
    
    def release(self):
        """Release a connection back to the pool."""
        self.semaphore.release()
```

## Data Models

### Enhanced Model Validation

```python
# backend/app/models/enhanced_base.py
from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4

class EnhancedBaseModel(BaseModel):
    """Enhanced base model with comprehensive validation."""
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        # Use enum values
        use_enum_values = True
        # Allow population by field name
        allow_population_by_field_name = True
        # JSON encoders
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None."""
        if v == '':
            return None
        return v

class AuditableModel(EnhancedBaseModel):
    """Model with audit fields."""
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = Field(default=1)
    
    def update_audit_fields(self, user_id: str):
        """Update audit fields for modifications."""
        self.updated_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1
```

## Error Handling

### Comprehensive Error Handling Strategy

1. **Structured Error Responses**: All errors return consistent JSON structure
2. **Error Classification**: Errors are categorized by type and severity
3. **User-Friendly Messages**: Technical errors are translated to user-friendly messages
4. **Error Tracking**: All errors are logged with context for debugging
5. **Graceful Degradation**: Non-critical failures don't break the entire application

### Error Response Format

```json
{
  "error": "VALIDATION_ERROR",
  "message": "The uploaded file format is not supported",
  "details": {
    "field": "file",
    "allowed_formats": ["pdf", "docx", "txt"],
    "received_format": "xlsx"
  },
  "request_id": "req_123456789",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Testing Strategy

### 1. Unit Testing

- **Backend**: pytest with async support, mocking external services
- **Frontend**: Vitest with React Testing Library
- **Coverage Target**: 80% minimum for critical paths

### 2. Integration Testing

- **API Testing**: Test all endpoints with various scenarios
- **Database Testing**: Test data persistence and retrieval
- **External Service Testing**: Mock Google Cloud services

### 3. End-to-End Testing

- **User Workflows**: Test complete user journeys
- **Cross-Browser Testing**: Ensure compatibility across browsers
- **Accessibility Testing**: Automated accessibility checks

### 4. Performance Testing

- **Load Testing**: Test API performance under load
- **Bundle Analysis**: Monitor frontend bundle sizes
- **Memory Profiling**: Check for memory leaks

### Testing Infrastructure

```python
# backend/tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import Settings

@pytest.fixture
def test_settings():
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        SECRET_KEY="test-secret-key-32-characters-long",
        GOOGLE_CLOUD_PROJECT="test-project",
    )

@pytest.fixture
def client(test_settings):
    with TestClient(app) as client:
        yield client

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

```typescript
// frontend/src/test/setup.ts
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});

// Mock environment variables
vi.mock('../config/environment', () => ({
  config: {
    apiBaseUrl: 'http://localhost:8000',
    firebase: {
      apiKey: 'test-api-key',
      authDomain: 'test.firebaseapp.com',
      projectId: 'test-project',
      storageBucket: 'test.appspot.com',
      messagingSenderId: '123456789',
      appId: '1:123456789:web:test',
    },
    features: {
      enableAnalytics: false,
      enableVoiceFeatures: true,
      enableTranslation: true,
    },
  },
}));
```

This design provides a comprehensive foundation for refactoring the Legal Companion application with focus on security, performance, maintainability, and production readiness.