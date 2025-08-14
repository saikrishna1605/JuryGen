"""
Authentication endpoints.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.security import require_auth, optional_auth, get_user_context
from app.models.base import ApiResponse
import structlog

router = APIRouter()
logger = structlog.get_logger()


class UserProfileResponse(BaseModel):
    """User profile response model."""
    uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    email_verified: bool = False
    is_anonymous: bool = False
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Update profile request model."""
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@router.get("/profile", response_model=ApiResponse)
async def get_user_profile(
    user: Dict[str, Any] = Depends(require_auth)
) -> ApiResponse:
    """
    Get current user profile.
    
    Returns:
        User profile information
    """
    try:
        firebase_claims = user.get("firebase_claims", {})
        
        profile = UserProfileResponse(
            uid=user["uid"],
            email=user.get("email"),
            display_name=user.get("name"),
            email_verified=user.get("email_verified", False),
            is_anonymous=firebase_claims.get("firebase", {}).get("sign_in_provider") == "anonymous",
            created_at=firebase_claims.get("auth_time"),
        )
        
        logger.info("User profile retrieved", user_id=user["uid"])
        
        return ApiResponse(
            success=True,
            data=profile.model_dump(),
            message="Profile retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Failed to get user profile", error=str(e), user_id=user.get("uid"))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile", response_model=ApiResponse)
async def update_user_profile(
    request: UpdateProfileRequest,
    user: Dict[str, Any] = Depends(require_auth)
) -> ApiResponse:
    """
    Update user profile.
    
    Args:
        request: Profile update request
        user: Authenticated user
        
    Returns:
        Updated profile information
    """
    try:
        # In a real implementation, you would update the user profile
        # in your database (Firestore) and possibly in Firebase Auth
        
        # For now, we'll just return the current user info
        # with any updates that don't require database changes
        
        logger.info(
            "User profile update requested",
            user_id=user["uid"],
            updates=request.model_dump(exclude_none=True)
        )
        
        return ApiResponse(
            success=True,
            data={"message": "Profile update functionality will be implemented with database integration"},
            message="Profile update requested"
        )
        
    except Exception as e:
        logger.error("Failed to update user profile", error=str(e), user_id=user.get("uid"))
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )


@router.get("/me", response_model=ApiResponse)
async def get_current_user(
    user: Dict[str, Any] = Depends(require_auth)
) -> ApiResponse:
    """
    Get current authenticated user information.
    
    Returns:
        Current user information
    """
    try:
        user_context = get_user_context(user)
        
        logger.info("Current user info requested", **user_context)
        
        return ApiResponse(
            success=True,
            data=user_context,
            message="User information retrieved"
        )
        
    except Exception as e:
        logger.error("Failed to get current user", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information"
        )


@router.post("/verify", response_model=ApiResponse)
async def verify_token(
    user: Optional[Dict[str, Any]] = Depends(optional_auth)
) -> ApiResponse:
    """
    Verify authentication token.
    
    Returns:
        Token verification result
    """
    if user:
        user_context = get_user_context(user)
        logger.info("Token verified successfully", **user_context)
        
        return ApiResponse(
            success=True,
            data={
                "authenticated": True,
                "user": user_context
            },
            message="Token is valid"
        )
    else:
        return ApiResponse(
            success=True,
            data={
                "authenticated": False,
                "user": None
            },
            message="No valid token provided"
        )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    user: Dict[str, Any] = Depends(require_auth)
) -> ApiResponse:
    """
    Logout user (invalidate token on client side).
    
    Note: Firebase tokens are stateless, so logout is handled client-side.
    This endpoint is mainly for logging purposes.
    
    Returns:
        Logout confirmation
    """
    try:
        user_context = get_user_context(user)
        logger.info("User logged out", **user_context)
        
        return ApiResponse(
            success=True,
            data={"message": "Logout successful"},
            message="User logged out successfully"
        )
        
    except Exception as e:
        logger.error("Logout error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Logout failed"
        )


@router.get("/status", response_model=ApiResponse)
async def auth_status(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(optional_auth)
) -> ApiResponse:
    """
    Get authentication status and system information.
    
    Returns:
        Authentication status and system info
    """
    try:
        status_info = {
            "authenticated": user is not None,
            "user": get_user_context(user) if user else None,
            "timestamp": request.state.request_id if hasattr(request.state, 'request_id') else None,
            "auth_methods": [
                "firebase_id_token",
                "google_oauth",
                "email_password",
                "anonymous"
            ]
        }
        
        return ApiResponse(
            success=True,
            data=status_info,
            message="Authentication status retrieved"
        )
        
    except Exception as e:
        logger.error("Failed to get auth status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve authentication status"
        )