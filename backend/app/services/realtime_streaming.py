"""
Real-time Status Streaming service for job progress updates.

This service handles:
- Server-Sent Events (SSE) endpoint for job progress
- Firestore real-time listeners for status updates
- WebSocket fallback for real-time communication
- Connection management and cleanup
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any, AsyncGenerator
from datetime import datetime
import weakref
from contextlib import asynccontextmanager

from fastapi import Request
from fastapi.responses import StreamingResponse
from google.cloud import firestore
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..services.firestore import FirestoreService
from ..core.exceptions import WorkflowError

logger = logging.getLogger(__name__)
settings = get_settings()


class SSEConnection:
    """Represents a Server-Sent Events connection."""
    
    def __init__(self, connection_id: str, user_id: str, job_id: Optional[str] = None):
        self.connection_id = connection_id
        self.user_id = user_id
        self.job_id = job_id
        self.created_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.is_active = True
        
        # Event queue for this connection
        self.event_queue = asyncio.Queue(maxsize=100)
        
        # Connection metadata
        self.metadata = {}
    
    async def send_event(self, event_type: str, data: Dict[str, Any]):
        """Send an event to this connection."""
        try:
            if not self.is_active:
                return False
            
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": self.connection_id
            }
            
            # Add to queue (non-blocking)
            try:
                self.event_queue.put_nowait(event)
                return True
            except asyncio.QueueFull:
                logger.warning(f"Event queue full for connection {self.connection_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send event to connection {self.connection_id}: {str(e)}")
            return False
    
    async def get_events(self) -> AsyncGenerator[str, None]:
        """Get events from the queue as SSE formatted strings."""
        try:
            while self.is_active:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=30.0)
                    
                    # Format as SSE
                    sse_data = f"event: {event['type']}\n"
                    sse_data += f"data: {json.dumps(event['data'])}\n"
                    sse_data += f"id: {event['timestamp']}\n\n"
                    
                    yield sse_data
                    
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield "event: ping\ndata: {}\n\n"
                    self.last_ping = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Error getting events for connection {self.connection_id}: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Event stream error for connection {self.connection_id}: {str(e)}")
        finally:
            self.is_active = False
    
    def close(self):
        """Close the connection."""
        self.is_active = False


class WebSocketConnection:
    """Represents a WebSocket connection."""
    
    def __init__(self, websocket, connection_id: str, user_id: str, job_id: Optional[str] = None):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.job_id = job_id
        self.created_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.is_active = True
    
    async def send_event(self, event_type: str, data: Dict[str, Any]):
        """Send an event via WebSocket."""
        try:
            if not self.is_active:
                return False
            
            message = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": self.connection_id
            }
            
            await self.websocket.send_text(json.dumps(message))
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket event: {str(e)}")
            self.is_active = False
            return False
    
    async def close(self):
        """Close the WebSocket connection."""
        try:
            if self.is_active:
                await self.websocket.close()
        except Exception as e:
            logger.warning(f"Error closing WebSocket: {str(e)}")
        finally:
            self.is_active = False


class RealtimeStreamingService:
    """
    Service for real-time status streaming using SSE and WebSocket.
    
    Provides real-time job progress updates, Firestore listeners,
    and connection management for multiple clients.
    """
    
    def __init__(self):
        """Initialize the Real-time Streaming Service."""
        self.firestore_service = FirestoreService()
        
        # Connection management
        self.sse_connections: Dict[str, SSEConnection] = {}
        self.websocket_connections: Dict[str, WebSocketConnection] = {}
        
        # Firestore listeners
        self.firestore_listeners: Dict[str, Any] = {}
        
        # User subscriptions (user_id -> set of connection_ids)
        self.user_subscriptions: Dict[str, Set[str]] = {}
        
        # Job subscriptions (job_id -> set of connection_ids)
        self.job_subscriptions: Dict[str, Set[str]] = {}
        
        # Background tasks
        self._cleanup_task = None
        self._listener_task = None
        self._shutdown_event = asyncio.Event()
        
        # Background tasks will be started when needed
        self._cleanup_task = None
        self._listener_task = None
        self._tasks_started = False
    
    def _start_background_tasks(self):
        """Start background tasks for connection cleanup and listeners."""
        if not self._tasks_started:
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_connections())
                self._listener_task = asyncio.create_task(self._manage_firestore_listeners())
                self._tasks_started = True
            except RuntimeError:
                # No event loop running, tasks will be started later
                pass
    
    async def _ensure_tasks_started(self):
        """Ensure background tasks are started."""
        if not self._tasks_started:
            self._start_background_tasks()
    
    async def create_sse_stream(
        self,
        user_id: str,
        job_id: Optional[str] = None,
        connection_id: Optional[str] = None
    ) -> StreamingResponse:
        """
        Create a Server-Sent Events stream for real-time updates.
        
        Args:
            user_id: User ID for the connection
            job_id: Optional specific job ID to monitor
            connection_id: Optional custom connection ID
            
        Returns:
            StreamingResponse for SSE
        """
        await self._ensure_tasks_started()
        
        try:
            # Generate connection ID if not provided
            if not connection_id:
                connection_id = f"sse_{user_id}_{datetime.utcnow().timestamp()}"
            
            # Create SSE connection
            connection = SSEConnection(connection_id, user_id, job_id)
            self.sse_connections[connection_id] = connection
            
            # Add to subscriptions
            self._add_to_subscriptions(connection_id, user_id, job_id)
            
            # Set up Firestore listener for this connection
            await self._setup_firestore_listener(connection_id, user_id, job_id)
            
            logger.info(f"Created SSE stream for user {user_id}, job {job_id}")
            
            # Return streaming response
            return StreamingResponse(
                connection.get_events(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create SSE stream: {str(e)}")
            raise WorkflowError(f"Failed to create SSE stream: {str(e)}") from e
    
    async def handle_websocket_connection(
        self,
        websocket,
        user_id: str,
        job_id: Optional[str] = None,
        connection_id: Optional[str] = None
    ):
        """
        Handle a WebSocket connection for real-time updates.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID for the connection
            job_id: Optional specific job ID to monitor
            connection_id: Optional custom connection ID
        """
        try:
            # Generate connection ID if not provided
            if not connection_id:
                connection_id = f"ws_{user_id}_{datetime.utcnow().timestamp()}"
            
            # Accept WebSocket connection
            await websocket.accept()
            
            # Create WebSocket connection
            connection = WebSocketConnection(websocket, connection_id, user_id, job_id)
            self.websocket_connections[connection_id] = connection
            
            # Add to subscriptions
            self._add_to_subscriptions(connection_id, user_id, job_id)
            
            # Set up Firestore listener
            await self._setup_firestore_listener(connection_id, user_id, job_id)
            
            logger.info(f"Accepted WebSocket connection for user {user_id}, job {job_id}")
            
            # Send initial connection confirmation
            await connection.send_event("connected", {
                "connection_id": connection_id,
                "user_id": user_id,
                "job_id": job_id
            })
            
            # Keep connection alive and handle messages
            try:
                while connection.is_active:
                    try:
                        # Wait for messages (mainly for ping/pong)
                        message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        
                        # Handle ping messages
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await connection.send_event("pong", {"timestamp": datetime.utcnow().isoformat()})
                            connection.last_ping = datetime.utcnow()
                            
                    except asyncio.TimeoutError:
                        # Send keepalive ping
                        await connection.send_event("ping", {"timestamp": datetime.utcnow().isoformat()})
                        connection.last_ping = datetime.utcnow()
                        
            except Exception as e:
                logger.warning(f"WebSocket connection error: {str(e)}")
            finally:
                await self._cleanup_connection(connection_id)
                
        except Exception as e:
            logger.error(f"WebSocket connection handling failed: {str(e)}")
            if connection_id in self.websocket_connections:
                await self._cleanup_connection(connection_id)
    
    def _add_to_subscriptions(self, connection_id: str, user_id: str, job_id: Optional[str]):
        """Add connection to subscription lists."""
        # Add to user subscriptions
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(connection_id)
        
        # Add to job subscriptions if job_id provided
        if job_id:
            if job_id not in self.job_subscriptions:
                self.job_subscriptions[job_id] = set()
            self.job_subscriptions[job_id].add(connection_id)
    
    async def _setup_firestore_listener(
        self,
        connection_id: str,
        user_id: str,
        job_id: Optional[str]
    ):
        """Set up Firestore real-time listener for a connection."""
        try:
            if job_id:
                # Listen to specific job
                doc_ref = self.firestore_service.db.collection("jobs").document(job_id)
                
                def on_snapshot(doc_snapshot, changes, read_time):
                    asyncio.create_task(self._handle_job_update(connection_id, doc_snapshot))
                
                listener = doc_ref.on_snapshot(on_snapshot)
                self.firestore_listeners[f"{connection_id}_job"] = listener
            else:
                # Listen to all user jobs
                query = self.firestore_service.db.collection("jobs").where("user_id", "==", user_id)
                
                def on_snapshot(query_snapshot, changes, read_time):
                    for change in changes:
                        asyncio.create_task(self._handle_job_update(connection_id, change.document))
                
                listener = query.on_snapshot(on_snapshot)
                self.firestore_listeners[f"{connection_id}_user"] = listener
                
        except Exception as e:
            logger.error(f"Failed to setup Firestore listener: {str(e)}")
    
    async def _handle_job_update(self, connection_id: str, doc_snapshot):
        """Handle job update from Firestore listener."""
        try:
            if not doc_snapshot.exists:
                return
            
            job_data = doc_snapshot.to_dict()
            
            # Send update to specific connection
            await self._send_to_connection(connection_id, "job_update", job_data)
            
        except Exception as e:
            logger.error(f"Failed to handle job update: {str(e)}")
    
    async def broadcast_job_update(self, job_id: str, job_data: Dict[str, Any]):
        """
        Broadcast job update to all subscribed connections.
        
        Args:
            job_id: Job ID that was updated
            job_data: Updated job data
        """
        try:
            # Get connections subscribed to this job
            connections = self.job_subscriptions.get(job_id, set())
            
            # Also get connections for the user who owns this job
            user_id = job_data.get("user_id")
            if user_id:
                user_connections = self.user_subscriptions.get(user_id, set())
                connections.update(user_connections)
            
            # Send update to all relevant connections
            for connection_id in connections:
                await self._send_to_connection(connection_id, "job_update", job_data)
                
        except Exception as e:
            logger.error(f"Failed to broadcast job update: {str(e)}")
    
    async def broadcast_system_message(self, message: str, message_type: str = "info"):
        """
        Broadcast system message to all connections.
        
        Args:
            message: Message to broadcast
            message_type: Type of message (info, warning, error)
        """
        try:
            message_data = {
                "message": message,
                "type": message_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to all SSE connections
            for connection in self.sse_connections.values():
                await connection.send_event("system_message", message_data)
            
            # Send to all WebSocket connections
            for connection in self.websocket_connections.values():
                await connection.send_event("system_message", message_data)
                
        except Exception as e:
            logger.error(f"Failed to broadcast system message: {str(e)}")
    
    async def _send_to_connection(self, connection_id: str, event_type: str, data: Dict[str, Any]):
        """Send event to a specific connection."""
        try:
            # Try SSE connection first
            if connection_id in self.sse_connections:
                connection = self.sse_connections[connection_id]
                await connection.send_event(event_type, data)
                return
            
            # Try WebSocket connection
            if connection_id in self.websocket_connections:
                connection = self.websocket_connections[connection_id]
                await connection.send_event(event_type, data)
                return
                
        except Exception as e:
            logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up a specific connection."""
        try:
            # Remove from connections
            if connection_id in self.sse_connections:
                connection = self.sse_connections[connection_id]
                connection.close()
                del self.sse_connections[connection_id]
            
            if connection_id in self.websocket_connections:
                connection = self.websocket_connections[connection_id]
                await connection.close()
                del self.websocket_connections[connection_id]
            
            # Remove from subscriptions
            for user_connections in self.user_subscriptions.values():
                user_connections.discard(connection_id)
            
            for job_connections in self.job_subscriptions.values():
                job_connections.discard(connection_id)
            
            # Remove Firestore listeners
            listener_keys = [key for key in self.firestore_listeners.keys() if key.startswith(connection_id)]
            for key in listener_keys:
                try:
                    listener = self.firestore_listeners[key]
                    listener.unsubscribe()
                    del self.firestore_listeners[key]
                except Exception as e:
                    logger.warning(f"Error removing Firestore listener {key}: {str(e)}")
            
            logger.info(f"Cleaned up connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up connection {connection_id}: {str(e)}")
    
    async def _cleanup_connections(self):
        """Background task to clean up stale connections."""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                stale_connections = []
                
                # Check SSE connections
                for connection_id, connection in self.sse_connections.items():
                    if not connection.is_active:
                        stale_connections.append(connection_id)
                    elif (current_time - connection.last_ping).total_seconds() > 300:  # 5 minutes
                        stale_connections.append(connection_id)
                
                # Check WebSocket connections
                for connection_id, connection in self.websocket_connections.items():
                    if not connection.is_active:
                        stale_connections.append(connection_id)
                    elif (current_time - connection.last_ping).total_seconds() > 300:  # 5 minutes
                        stale_connections.append(connection_id)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    await self._cleanup_connection(connection_id)
                
                # Wait before next cleanup cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in connection cleanup task: {str(e)}")
                await asyncio.sleep(60)
    
    async def _manage_firestore_listeners(self):
        """Background task to manage Firestore listeners."""
        while not self._shutdown_event.is_set():
            try:
                # Monitor listener health and recreate if needed
                # This is a placeholder for more sophisticated listener management
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in Firestore listener management: {str(e)}")
                await asyncio.sleep(300)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections."""
        try:
            return {
                "sse_connections": len(self.sse_connections),
                "websocket_connections": len(self.websocket_connections),
                "total_connections": len(self.sse_connections) + len(self.websocket_connections),
                "user_subscriptions": len(self.user_subscriptions),
                "job_subscriptions": len(self.job_subscriptions),
                "firestore_listeners": len(self.firestore_listeners),
                "active_sse_connections": len([c for c in self.sse_connections.values() if c.is_active]),
                "active_websocket_connections": len([c for c in self.websocket_connections.values() if c.is_active])
            }
        except Exception as e:
            logger.error(f"Error getting connection stats: {str(e)}")
            return {}
    
    async def disconnect_user(self, user_id: str):
        """Disconnect all connections for a specific user."""
        try:
            user_connections = self.user_subscriptions.get(user_id, set()).copy()
            
            for connection_id in user_connections:
                await self._cleanup_connection(connection_id)
            
            logger.info(f"Disconnected all connections for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id}: {str(e)}")
    
    async def shutdown(self):
        """Shutdown the streaming service and clean up resources."""
        try:
            logger.info("Shutting down realtime streaming service")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._listener_task:
                self._listener_task.cancel()
            
            # Close all connections
            all_connections = list(self.sse_connections.keys()) + list(self.websocket_connections.keys())
            for connection_id in all_connections:
                await self._cleanup_connection(connection_id)
            
            # Clean up Firestore listeners
            for listener in self.firestore_listeners.values():
                try:
                    listener.unsubscribe()
                except Exception as e:
                    logger.warning(f"Error unsubscribing Firestore listener: {str(e)}")
            
            logger.info("Realtime streaming service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during streaming service shutdown: {str(e)}")


# Global streaming service instance
streaming_service = RealtimeStreamingService()