"""
Security utilities and authentication middleware.
"""

import time
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

try:
    import firebase_admin
    from firebase_admin import auth, credentials
    from .config import settings
    
    # Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        firebase_credentials = settings.get_firebase_credentials()
        if firebase_credentials:
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred)
            logger = structlog.get_logger()
            logger.info("Firebase Admin SDK initialized successfully")
        else:
            logger = structlog.get_logger()
            logger.warning("Firebase credentials not configured, authentication disabled")
    
    FIREBASE_AVAILABLE = True
except ImportError:
    logger = structlog.get_logger()
    logger.warning("Firebase Admin SDK not available, authentication disabled")
    FIREBASE_AVAILABLE = False
except Exception as e:
    logger = structlog.get_logger()
    logger.error("Failed to initialize Firebase Admin SDK", error=str(e))
    FIREBASE_AVAILABLE = False


# Security scheme
security = HTTPBearer(auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < window
            ]
        else:
            self.requests[key] = []
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def verify_firebase_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Verify Firebase ID token and return user information.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information dict or None if not authenticated
        
    Raises:
        HTTPException: If token is invalid
    """
    if not FIREBASE_AVAILABLE:
        # In development mode without Firebase, return mock user
        if settings.DEBUG:
            return {
                "uid": "dev-user",
                "email": "dev@example.com",
                "name": "Development User",
                "email_verified": True
            }
        return None
    
    if not credentials:
        return None
    
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "email_verified": decoded_token.get("email_verified", False),
            "firebase_claims": decoded_token
        }
    
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


async def require_auth(user: Optional[Dict[str, Any]] = Depends(verify_firebase_token)) -> Dict[str, Any]:
    """
    Require authentication for protected endpoints.
    
    Args:
        user: User information from token verification
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return user


async def optional_auth(user: Optional[Dict[str, Any]] = Depends(verify_firebase_token)) -> Optional[Dict[str, Any]]:
    """
    Optional authentication for endpoints that work with or without auth.
    
    Args:
        user: User information from token verification
        
    Returns:
        User information dict or None
    """
    return user


def require_roles(*required_roles: str):
    """
    Decorator to require specific roles for endpoint access.
    
    Args:
        required_roles: List of required roles
        
    Returns:
        Decorated function that checks user roles
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by FastAPI)
            user = kwargs.get('user')
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check roles (this would need to be implemented based on your role system)
            user_roles = user.get('firebase_claims', {}).get('custom_claims', {}).get('roles', [])
            
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint
        
    Returns:
        Response from next middleware/endpoint
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get user ID if authenticated
    user_id = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            if FIREBASE_AVAILABLE:
                decoded_token = auth.verify_id_token(token)
                user_id = decoded_token.get("uid")
        except:
            pass  # Ignore auth errors for rate limiting
    
    # Use user ID if available, otherwise IP
    rate_limit_key = user_id or client_ip
    
    # Check rate limit (60 requests per minute)
    if not rate_limiter.is_allowed(rate_limit_key, settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    remaining = max(0, settings.RATE_LIMIT_REQUESTS_PER_MINUTE - len(rate_limiter.requests.get(rate_limit_key, [])))
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response


def get_user_context(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user context for logging and processing.
    
    Args:
        user: User information from authentication
        
    Returns:
        User context dict
    """
    return {
        "user_id": user.get("uid"),
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
        "is_anonymous": user.get("firebase_claims", {}).get("firebase", {}).get("sign_in_provider") == "anonymous"
    }


async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to responses.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint
        
    Returns:
        Response with security headers
    """
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


class AuthorizationError(Exception):
    """Custom authorization error."""
    pass


def create_access_token(user_id: str, expires_delta: Optional[int] = None) -> str:
    """
    Create a custom access token (if needed for internal services).
    
    Args:
        user_id: User identifier
        expires_delta: Token expiration time in seconds
        
    Returns:
        JWT token string
    """
    # This would implement custom JWT token creation if needed
    # For now, we rely on Firebase tokens
    raise NotImplementedError("Custom tokens not implemented - use Firebase tokens")


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key for service-to-service communication.
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    # This would implement API key verification for internal services
    # For now, we rely on Firebase authentication
    return False