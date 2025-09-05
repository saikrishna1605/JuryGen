"""
Authentication utilities using Firebase Admin SDK
"""

from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .firebase import firebase_admin
import structlog

logger = structlog.get_logger()

# Security scheme
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current authenticated user from Firebase token
    """
    try:
        # Verify the token
        decoded_token = firebase_admin.verify_token(credentials.credentials)
        
        if not decoded_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        logger.info("User authenticated successfully", uid=decoded_token.get('uid'))
        return decoded_token
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current authenticated user (optional)
    """
    if not credentials:
        return None
        
    try:
        return firebase_admin.verify_token(credentials.credentials)
    except:
        return None


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require admin role for the current user
    """
    if not current_user.get('admin', False):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return current_user