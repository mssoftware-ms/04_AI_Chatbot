"""
WebSocket API for real-time messaging in WhatsApp AI Chatbot

This module provides WebSocket endpoints and connection management for
real-time communication between clients and the chatbot system.
"""

import logging
import json
import asyncio
# Änderung durch KI - Enhanced type hints
from typing import Dict, Set, List, Any, Optional, Union, Callable
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, ValidationError

from src.utils.dependencies import get_current_user_websocket

logger = logging.getLogger(__name__)

router = APIRouter()

class WebSocketMessage(BaseModel):
    """Model for WebSocket message structure."""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    conversation_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

class ConnectionInfo(BaseModel):
    """Model for connection information."""
    user_id: str
    project_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    connected_at: datetime
    last_ping: Optional[datetime] = None

class WebSocketManager:
    """
    WebSocket connection manager for handling multiple concurrent connections.
    
    Supports:
    - Per-project connections
    - Per-conversation connections
    - User-specific connections
    - Heartbeat mechanism
    - Error recovery
    """
    
    # Änderung durch KI - Added type hints
    def __init__(self) -> None:
        # Active connections organized by different criteria
        self.active_connections: Dict[WebSocket, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        self.project_connections: Dict[UUID, Set[WebSocket]] = {}
        self.conversation_connections: Dict[UUID, Set[WebSocket]] = {}
        
        # Änderung durch KI - Enhanced connection stats and limits
        self.connection_count = 0
        self.total_connections = 0
        self.failed_connections = 0
        self.max_connections = 100  # Configurable limit
        
        # Performance optimization: use sets for faster lookups
        self._connection_lookup = set()  # Fast connection existence check
        
        # Heartbeat task
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # seconds
        
    # Änderung durch KI - Added type hints
    async def initialize(self) -> None:
        """Initialize the WebSocket manager and start background tasks."""
        logger.info("Initializing WebSocket manager")
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
    # Änderung durch KI - Added type hints
    async def cleanup(self) -> None:
        """Clean up resources and close all connections."""
        logger.info("Cleaning up WebSocket manager")
        
        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        close_tasks = []
        for websocket in list(self.active_connections.keys()):
            close_tasks.append(self._close_connection(websocket, code=1001, reason="Server shutdown"))
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            
        logger.info("WebSocket manager cleanup completed")
    
    # Änderung durch KI - Added type hints and optimization
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        project_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None
    ) -> None:
        """
        Accept a new WebSocket connection and register it.
        
        Args:
            websocket: WebSocket connection instance
            user_id: Authenticated user ID
            project_id: Optional project filter
            conversation_id: Optional conversation filter
        """
        try:
            # Änderung durch KI - Check connection limits before accepting
            if self.connection_count >= self.max_connections:
                await websocket.close(code=1013, reason="Server at capacity")
                logger.warning(f"Connection rejected: server at capacity ({self.max_connections})")
                self.failed_connections += 1
                return
                
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(
                user_id=user_id,
                project_id=project_id,
                conversation_id=conversation_id,
                connected_at=datetime.utcnow()
            )
            
            # Änderung durch KI - Register connection with performance optimization
            self.active_connections[websocket] = connection_info
            self._connection_lookup.add(websocket)
            
            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            
            # Add to project connections if specified
            if project_id:
                if project_id not in self.project_connections:
                    self.project_connections[project_id] = set()
                self.project_connections[project_id].add(websocket)
            
            # Add to conversation connections if specified
            if conversation_id:
                if conversation_id not in self.conversation_connections:
                    self.conversation_connections[conversation_id] = set()
                self.conversation_connections[conversation_id].add(websocket)
            
            self.connection_count += 1
            self.total_connections += 1
            
            # Send connection confirmation
            await self.send_personal_message(websocket, {
                "type": "connection_confirmed",
                "data": {
                    "user_id": user_id,
                    "project_id": str(project_id) if project_id else None,
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "connected_at": connection_info.connected_at.isoformat()
                }
            })
            
            logger.info(
                f"WebSocket connected - User: {user_id}, "
                f"Project: {project_id}, Conversation: {conversation_id}, "
                f"Total connections: {self.connection_count}"
            )
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            self.failed_connections += 1
            raise
    
    # Änderung durch KI - Added type hints
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect a WebSocket and clean up references.
        
        Args:
            websocket: WebSocket connection instance
        """
        try:
            connection_info = self.active_connections.get(websocket)
            if not connection_info:
                return
            
            user_id = connection_info.user_id
            project_id = connection_info.project_id
            conversation_id = connection_info.conversation_id
            
            # Änderung durch KI - Remove from all tracking dictionaries with performance optimization
            self.active_connections.pop(websocket, None)
            self._connection_lookup.discard(websocket)
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from project connections
            if project_id and project_id in self.project_connections:
                self.project_connections[project_id].discard(websocket)
                if not self.project_connections[project_id]:
                    del self.project_connections[project_id]
            
            # Remove from conversation connections
            if conversation_id and conversation_id in self.conversation_connections:
                self.conversation_connections[conversation_id].discard(websocket)
                if not self.conversation_connections[conversation_id]:
                    del self.conversation_connections[conversation_id]
            
            self.connection_count = max(0, self.connection_count - 1)
            
            logger.info(
                f"WebSocket disconnected - User: {user_id}, "
                f"Project: {project_id}, Conversation: {conversation_id}, "
                f"Remaining connections: {self.connection_count}"
            )
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")
    
    # Änderung durch KI - Added type hints and error handling
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message data to send
        """
        try:
            if websocket.client_state != WebSocketState.CONNECTED:
                return
            
            ws_message = WebSocketMessage(
                type=message.get("type", "message"),
                data=message.get("data", {}),
                timestamp=datetime.utcnow()
            )
            
            # Änderung durch KI - Better error handling
            await websocket.send_text(ws_message.model_dump_json())
            return True
            
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self._handle_connection_error(websocket)
            return False
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Broadcast a message to all connections for a specific user.
        
        Args:
            user_id: Target user ID
            message: Message data to broadcast
        """
        if user_id not in self.user_connections:
            return
        
        tasks = []
        for websocket in list(self.user_connections[user_id]):
            tasks.append(self.send_personal_message(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_project(self, project_id: UUID, message: Dict[str, Any]):
        """
        Broadcast a message to all connections for a specific project.
        
        Args:
            project_id: Target project ID
            message: Message data to broadcast
        """
        if project_id not in self.project_connections:
            return
        
        tasks = []
        for websocket in list(self.project_connections[project_id]):
            tasks.append(self.send_personal_message(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_conversation(self, conversation_id: UUID, message: Dict[str, Any]):
        """
        Broadcast a message to all connections for a specific conversation.
        
        Args:
            conversation_id: Target conversation ID
            message: Message data to broadcast
        """
        if conversation_id not in self.conversation_connections:
            return
        
        tasks = []
        for websocket in list(self.conversation_connections[conversation_id]):
            message_copy = message.copy()
            message_copy["conversation_id"] = str(conversation_id)
            tasks.append(self.send_personal_message(websocket, message_copy))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Broadcast a message to all active connections.
        
        Args:
            message: Message data to broadcast
        """
        tasks = []
        for websocket in list(self.active_connections.keys()):
            tasks.append(self.send_personal_message(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        return {
            "active_connections": self.connection_count,
            "total_connections": self.total_connections,
            "failed_connections": self.failed_connections,
            "users_connected": len(self.user_connections),
            "projects_connected": len(self.project_connections),
            "conversations_connected": len(self.conversation_connections)
        }
    
    async def _heartbeat_loop(self):
        """Background task for maintaining connection health."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                # Send heartbeat to all connections
                heartbeat_message = {
                    "type": "heartbeat",
                    "data": {"timestamp": datetime.utcnow().isoformat()}
                }
                
                failed_connections = []
                for websocket, connection_info in list(self.active_connections.items()):
                    try:
                        await self.send_personal_message(websocket, heartbeat_message)
                        connection_info.last_ping = datetime.utcnow()
                    except Exception as e:
                        logger.warning(f"Heartbeat failed for connection: {e}")
                        failed_connections.append(websocket)
                
                # Clean up failed connections
                for websocket in failed_connections:
                    await self._handle_connection_error(websocket)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _handle_connection_error(self, websocket: WebSocket):
        """
        Handle connection errors and cleanup.
        
        Args:
            websocket: Failed WebSocket connection
        """
        try:
            await self.disconnect(websocket)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=1001, reason="Connection error")
        except Exception as e:
            logger.error(f"Error handling connection error: {e}")
    
    async def _close_connection(self, websocket: WebSocket, code: int = 1000, reason: str = "Normal closure"):
        """
        Safely close a WebSocket connection.
        
        Args:
            websocket: WebSocket to close
            code: Close code
            reason: Close reason
        """
        try:
            await self.disconnect(websocket)
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.error(f"Error closing WebSocket connection: {e}")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: Optional[UUID] = Query(None, description="Project ID filter"),
    conversation_id: Optional[UUID] = Query(None, description="Conversation ID filter"),
    user_id: str = Depends(get_current_user_websocket)
):
    """
    Main WebSocket endpoint for real-time chat communication.
    
    Args:
        websocket: WebSocket connection instance
        project_id: Optional project filter
        conversation_id: Optional conversation filter
        user_id: Authenticated user ID from token
    """
    try:
        # Connect the WebSocket
        await websocket_manager.connect(
            websocket,
            user_id,
            project_id,
            conversation_id
        )
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                
                try:
                    # Parse incoming message
                    message_data = json.loads(data)
                    message = WebSocketMessage(**message_data)
                    
                    # Handle different message types
                    await handle_websocket_message(websocket, user_id, message)
                    
                except ValidationError as e:
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "error",
                        "data": {
                            "error": "Invalid message format",
                            "details": str(e)
                        }
                    })
                    
                except json.JSONDecodeError:
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "error",
                        "data": {"error": "Invalid JSON format"}
                    })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error in WebSocket communication for user {user_id}: {e}")
        
        finally:
            await websocket_manager.disconnect(websocket)
    
    except Exception as e:
        logger.error(f"Error setting up WebSocket for user {user_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass

async def handle_websocket_message(websocket: WebSocket, user_id: str, message: WebSocketMessage):
    """
    Handle incoming WebSocket messages based on their type.
    
    Args:
        websocket: WebSocket connection instance
        user_id: Authenticated user ID
        message: Parsed WebSocket message
    """
    try:
        logger.info(f"Handling WebSocket message type '{message.type}' from user {user_id}")
        
        if message.type == "ping":
            # Respond to ping with pong
            await websocket_manager.send_personal_message(websocket, {
                "type": "pong",
                "data": {"timestamp": datetime.utcnow().isoformat()}
            })
        
        elif message.type == "join_conversation":
            # Join a specific conversation
            conversation_id = message.data.get("conversation_id")
            if conversation_id:
                try:
                    conv_id = UUID(conversation_id)
                    # Add connection to conversation
                    if conv_id not in websocket_manager.conversation_connections:
                        websocket_manager.conversation_connections[conv_id] = set()
                    websocket_manager.conversation_connections[conv_id].add(websocket)
                    
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "joined_conversation",
                        "data": {"conversation_id": conversation_id}
                    })
                except ValueError:
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "error",
                        "data": {"error": "Invalid conversation ID format"}
                    })
        
        elif message.type == "leave_conversation":
            # Leave a specific conversation
            conversation_id = message.data.get("conversation_id")
            if conversation_id:
                try:
                    conv_id = UUID(conversation_id)
                    if conv_id in websocket_manager.conversation_connections:
                        websocket_manager.conversation_connections[conv_id].discard(websocket)
                        if not websocket_manager.conversation_connections[conv_id]:
                            del websocket_manager.conversation_connections[conv_id]
                    
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "left_conversation",
                        "data": {"conversation_id": conversation_id}
                    })
                except ValueError:
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "error",
                        "data": {"error": "Invalid conversation ID format"}
                    })
        
        elif message.type == "typing_start":
            # Broadcast typing indicator
            conversation_id = message.data.get("conversation_id")
            if conversation_id:
                try:
                    conv_id = UUID(conversation_id)
                    await websocket_manager.broadcast_to_conversation(conv_id, {
                        "type": "user_typing",
                        "data": {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "typing": True
                        }
                    })
                except ValueError:
                    pass
        
        elif message.type == "typing_stop":
            # Stop typing indicator
            conversation_id = message.data.get("conversation_id")
            if conversation_id:
                try:
                    conv_id = UUID(conversation_id)
                    await websocket_manager.broadcast_to_conversation(conv_id, {
                        "type": "user_typing",
                        "data": {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "typing": False
                        }
                    })
                except ValueError:
                    pass
        
        elif message.type == "get_stats":
            # Return connection statistics
            stats = websocket_manager.get_connection_stats()
            await websocket_manager.send_personal_message(websocket, {
                "type": "stats",
                "data": stats
            })
        
        else:
            # Unknown message type
            await websocket_manager.send_personal_message(websocket, {
                "type": "error",
                "data": {"error": f"Unknown message type: {message.type}"}
            })
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket_manager.send_personal_message(websocket, {
            "type": "error",
            "data": {"error": "Internal server error"}
        })

@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Current connection statistics
    """
    return websocket_manager.get_connection_stats()