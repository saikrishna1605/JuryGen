"""
Real-time streaming API endpoints for job progress updates.

This module provides endpoints for:
- Server-Sent Events (SSE) for job progress
- WebSocket connections for real-time updates
- Connection management and status
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse

from ....core.security import require_auth, optional_auth
from ....models.base import ApiResponse
from ....services.realtime_streaming import streaming_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming", tags=["streaming"])


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    job_id: UUID,
    current_user: dict = Depends(require_auth)
) -> StreamingResponse:
    """
    Create a Server-Sent Events stream for job progress updates.
    
    This endpoint provides real-time updates for a specific job using SSE.
    The stream will send events for job status changes, progress updates,
    and completion notifications.
    
    Args:
        job_id: ID of the job to monitor
        current_user: Authenticated user information
        
    Returns:
        StreamingResponse with SSE stream
    """
    try:
        logger.info(f"Creating SSE stream for job {job_id}, user {current_user['uid']}")
        
        # Create SSE stream
        return await streaming_service.create_sse_stream(
            user_id=current_user["uid"],
            job_id=str(job_id)
        )
        
    except Exception as e:
        logger.error(f"Failed to create job stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job progress stream"
        )


@router.get("/user/stream")
async def stream_user_updates(
    current_user: dict = Depends(require_auth)
) -> StreamingResponse:
    """
    Create a Server-Sent Events stream for all user job updates.
    
    This endpoint provides real-time updates for all jobs belonging to the user.
    Useful for dashboard views that show multiple job statuses.
    
    Args:
        current_user: Authenticated user information
        
    Returns:
        StreamingResponse with SSE stream
    """
    try:
        logger.info(f"Creating user SSE stream for user {current_user['uid']}")
        
        # Create SSE stream for all user jobs
        return await streaming_service.create_sse_stream(
            user_id=current_user["uid"],
            job_id=None  # Monitor all user jobs
        )
        
    except Exception as e:
        logger.error(f"Failed to create user stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user updates stream"
        )


@router.websocket("/jobs/{job_id}/ws")
async def websocket_job_progress(
    websocket: WebSocket,
    job_id: UUID,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for job progress updates.
    
    This provides an alternative to SSE for clients that prefer WebSocket
    connections. Requires authentication token as query parameter.
    
    Args:
        websocket: WebSocket connection
        job_id: ID of the job to monitor
        token: Authentication token (query parameter)
    """
    try:
        # Authenticate user (simplified for WebSocket)
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # TODO: Implement proper token validation
        # For now, extract user_id from token (this should be properly validated)
        user_id = "anonymous"  # Placeholder
        
        logger.info(f"WebSocket connection for job {job_id}, user {user_id}")
        
        # Handle WebSocket connection
        await streaming_service.handle_websocket_connection(
            websocket=websocket,
            user_id=user_id,
            job_id=str(job_id)
        )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


@router.websocket("/user/ws")
async def websocket_user_updates(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for all user job updates.
    
    Args:
        websocket: WebSocket connection
        token: Authentication token (query parameter)
    """
    try:
        # Authenticate user (simplified for WebSocket)
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # TODO: Implement proper token validation
        user_id = "anonymous"  # Placeholder
        
        logger.info(f"WebSocket connection for user {user_id}")
        
        # Handle WebSocket connection
        await streaming_service.handle_websocket_connection(
            websocket=websocket,
            user_id=user_id,
            job_id=None  # Monitor all user jobs
        )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


@router.get("/status")
async def get_streaming_status(
    current_user: dict = Depends(require_auth)
) -> ApiResponse:
    """
    Get the status of the streaming service.
    
    Returns connection statistics and service health information.
    
    Args:
        current_user: Authenticated user information
        
    Returns:
        ApiResponse with streaming service status
    """
    try:
        stats = await streaming_service.get_connection_stats()
        
        return ApiResponse(
            success=True,
            data={
                "service_status": "healthy",
                "connection_stats": stats,
                "supported_protocols": ["sse", "websocket"],
                "features": [
                    "job_progress_streaming",
                    "user_updates_streaming", 
                    "firestore_real_time_listeners",
                    "connection_management",
                    "automatic_cleanup"
                ]
            },
            message="Streaming service status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get streaming service status"
        )


@router.post("/broadcast")
async def broadcast_system_message(
    message: str,
    message_type: str = "info",
    current_user: dict = Depends(require_auth)
) -> ApiResponse:
    """
    Broadcast a system message to all connected clients.
    
    This endpoint is typically used by administrators to send
    system-wide notifications or maintenance messages.
    
    Args:
        message: Message to broadcast
        message_type: Type of message (info, warning, error)
        current_user: Authenticated user information
        
    Returns:
        ApiResponse confirming broadcast
    """
    try:
        # TODO: Add admin role check
        # For now, allow any authenticated user
        
        await streaming_service.broadcast_system_message(message, message_type)
        
        logger.info(f"System message broadcasted by user {current_user['uid']}: {message}")
        
        return ApiResponse(
            success=True,
            data={
                "message": message,
                "type": message_type,
                "broadcasted_by": current_user["uid"]
            },
            message="System message broadcasted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error broadcasting system message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast system message"
        )


@router.delete("/connections/{user_id}")
async def disconnect_user(
    user_id: str,
    current_user: dict = Depends(require_auth)
) -> ApiResponse:
    """
    Disconnect all connections for a specific user.
    
    This endpoint is typically used by administrators for user management
    or by users to disconnect their own sessions.
    
    Args:
        user_id: ID of the user to disconnect
        current_user: Authenticated user information
        
    Returns:
        ApiResponse confirming disconnection
    """
    try:
        # Allow users to disconnect themselves or admins to disconnect anyone
        if user_id != current_user["uid"]:
            # TODO: Add admin role check
            pass
        
        await streaming_service.disconnect_user(user_id)
        
        logger.info(f"User {user_id} disconnected by {current_user['uid']}")
        
        return ApiResponse(
            success=True,
            data={"disconnected_user": user_id},
            message="User connections disconnected successfully"
        )
        
    except Exception as e:
        logger.error(f"Error disconnecting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect user"
        )