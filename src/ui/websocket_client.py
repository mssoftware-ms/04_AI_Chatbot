"""
WebSocket client for real-time communication with the AI backend.
Handles message sending, receiving, and connection management.
"""

import asyncio
import websockets
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for real-time chat communication."""
    
    def __init__(
        self,
        url: str,
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_typing: Optional[Callable[[bool], None]] = None,
        on_status_change: Optional[Callable[[bool], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        self.url = url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Callbacks
        self.on_message = on_message
        self.on_typing = on_typing
        self.on_status_change = on_status_change
        self.on_error = on_error
        
        # Connection state
        self.connection_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_data: Dict[str, Any] = {}
        
        # Message queue for offline mode
        self.message_queue: List[Dict[str, Any]] = []
        self.max_queue_size = 100
        
        # Heartbeat
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Event loop
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.receive_task: Optional[asyncio.Task] = None
    
    async def connect(self, user_id: Optional[str] = None, session_data: Optional[Dict[str, Any]] = None):
        """Connect to WebSocket server."""
        self.user_id = user_id or f"user_{datetime.now().timestamp()}"
        self.session_data = session_data or {}
        
        try:
            logger.info(f"Connecting to WebSocket server: {self.url}")
            
            # Add connection parameters
            connect_url = f"{self.url}?user_id={self.user_id}"
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                connect_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            self.reconnect_attempts = 0
            
            logger.info("WebSocket connected successfully")
            
            # Start receiving messages
            self.receive_task = asyncio.create_task(self._receive_messages())
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat())
            
            # Send connection acknowledgment
            await self._send_system_message("connection", {
                "user_id": self.user_id,
                "session_data": self.session_data,
                "timestamp": datetime.now().isoformat()
            })
            
            # Process queued messages
            await self._process_message_queue()
            
            # Notify status change
            if self.on_status_change:
                await self.on_status_change(True)
                
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.connected = False
            
            if self.on_error:
                await self.on_error(e)
            
            # Attempt reconnection
            await self._attempt_reconnect()
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        logger.info("Disconnecting from WebSocket server")
        
        self.connected = False
        
        # Cancel tasks
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        # Notify status change
        if self.on_status_change:
            await self.on_status_change(False)
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to server."""
        if not self.connected or not self.websocket:
            # Queue message for later sending
            if len(self.message_queue) < self.max_queue_size:
                self.message_queue.append(message)
                logger.warning("WebSocket not connected, message queued")
            else:
                logger.error("Message queue full, dropping message")
            return
        
        try:
            # Add metadata
            enhanced_message = {
                **message,
                "user_id": self.user_id,
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send message
            await self.websocket.send(json.dumps(enhanced_message))
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            
            # Queue message for retry
            if len(self.message_queue) < self.max_queue_size:
                self.message_queue.append(message)
            
            if self.on_error:
                await self.on_error(e)
    
    async def send_user_message(self, content: str, conversation_id: str, attachments: Optional[List[str]] = None):
        """Send user message."""
        message = {
            "type": "user_message",
            "conversation_id": conversation_id,
            "content": content,
            "attachments": attachments or []
        }
        await self.send_message(message)
    
    async def send_typing_indicator(self, conversation_id: str, is_typing: bool = True):
        """Send typing indicator."""
        message = {
            "type": "typing_indicator",
            "conversation_id": conversation_id,
            "is_typing": is_typing
        }
        await self.send_message(message)
    
    async def send_message_status(self, message_id: str, status: str):
        """Send message status update (read, delivered, etc.)."""
        message = {
            "type": "message_status",
            "message_id": message_id,
            "status": status
        }
        await self.send_message(message)
    
    async def join_conversation(self, conversation_id: str):
        """Join a conversation room."""
        message = {
            "type": "join_conversation",
            "conversation_id": conversation_id
        }
        await self.send_message(message)
    
    async def leave_conversation(self, conversation_id: str):
        """Leave a conversation room."""
        message = {
            "type": "leave_conversation",
            "conversation_id": conversation_id
        }
        await self.send_message(message)
    
    async def _receive_messages(self):
        """Receive messages from WebSocket."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_received_message(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error handling received message: {e}")
                    if self.on_error:
                        await self.on_error(e)
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.connected = False
            await self._attempt_reconnect()
            
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            self.connected = False
            if self.on_error:
                await self.on_error(e)
    
    async def _handle_received_message(self, data: Dict[str, Any]):
        """Handle received WebSocket message."""
        message_type = data.get("type")
        
        logger.debug(f"Received message type: {message_type}")
        
        if message_type == "connection_ack":
            # Connection acknowledged
            self.connection_id = data.get("connection_id")
            logger.info(f"Connection acknowledged: {self.connection_id}")
            
        elif message_type == "ai_response":
            # AI message response
            if self.on_message:
                await self.on_message(data)
                
        elif message_type == "typing_indicator":
            # Typing indicator
            is_typing = data.get("is_typing", False)
            if self.on_typing:
                await self.on_typing(is_typing)
                
        elif message_type == "message_status":
            # Message status update
            if self.on_message:
                await self.on_message(data)
                
        elif message_type == "system_notification":
            # System notification
            logger.info(f"System notification: {data.get('message', '')}")
            
        elif message_type == "error":
            # Error message
            error_msg = data.get("message", "Unknown error")
            logger.error(f"Server error: {error_msg}")
            if self.on_error:
                await self.on_error(Exception(error_msg))
                
        elif message_type == "heartbeat_ack":
            # Heartbeat acknowledgment
            logger.debug("Heartbeat acknowledged")
            
        else:
            # Unknown message type, pass to general handler
            if self.on_message:
                await self.on_message(data)
    
    async def _send_system_message(self, system_type: str, data: Dict[str, Any]):
        """Send system message."""
        message = {
            "type": "system",
            "system_type": system_type,
            "data": data
        }
        
        if self.websocket and self.websocket.open:
            await self.websocket.send(json.dumps(message))
    
    async def _heartbeat(self):
        """Send periodic heartbeat messages."""
        while self.connected and self.websocket:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.connected and self.websocket:
                    await self._send_system_message("heartbeat", {
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def _process_message_queue(self):
        """Process queued messages after reconnection."""
        if not self.message_queue:
            return
        
        logger.info(f"Processing {len(self.message_queue)} queued messages")
        
        queued_messages = self.message_queue.copy()
        self.message_queue.clear()
        
        for message in queued_messages:
            try:
                await self.send_message(message)
                await asyncio.sleep(0.1)  # Small delay between messages
            except Exception as e:
                logger.error(f"Failed to send queued message: {e}")
                # Re-queue failed messages
                if len(self.message_queue) < self.max_queue_size:
                    self.message_queue.append(message)
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to WebSocket server."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return
        
        self.reconnect_attempts += 1
        delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 60)
        
        logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay} seconds")
        
        await asyncio.sleep(delay)
        
        try:
            await self.connect(self.user_id, self.session_data)
        except Exception as e:
            logger.error(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
            
            # Try again if within limits
            if self.reconnect_attempts < self.max_reconnect_attempts:
                await self._attempt_reconnect()
    
    # Connection status methods
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.connected and self.websocket is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "connected": self.connected,
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "url": self.url,
            "reconnect_attempts": self.reconnect_attempts,
            "queued_messages": len(self.message_queue)
        }
    
    def get_queue_size(self) -> int:
        """Get number of queued messages."""
        return len(self.message_queue)
    
    def clear_message_queue(self):
        """Clear the message queue."""
        self.message_queue.clear()
    
    async def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """Wait for WebSocket connection to be established."""
        start_time = asyncio.get_event_loop().time()
        
        while not self.connected:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            await asyncio.sleep(0.1)
        
        return True
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# WebSocket message types and utilities
class MessageTypes:
    """WebSocket message type constants."""
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    TYPING_INDICATOR = "typing_indicator"
    MESSAGE_STATUS = "message_status"
    CONNECTION_ACK = "connection_ack"
    SYSTEM = "system"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"


class ConnectionStatus:
    """Connection status constants."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


def create_websocket_client(
    url: str = "ws://localhost:8000/ws",
    **kwargs
) -> WebSocketClient:
    """Create a WebSocket client with default configuration."""
    return WebSocketClient(url, **kwargs)