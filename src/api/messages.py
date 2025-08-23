"""
Messages API endpoints for WhatsApp AI Chatbot

This module provides endpoints for handling messages within conversations,
including sending, receiving, and managing message history with real-time updates.
"""

import logging
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.utils.dependencies import get_current_user, validate_project_access
from src.api.websocket import websocket_manager

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Pydantic models
class MessageBase(BaseModel):
    """Base model for message data."""
    conversation_id: UUID = Field(..., description="Associated conversation ID")
    content: str = Field(..., min_length=1, max_length=4096, description="Message content")
    message_type: Literal["text", "image", "audio", "video", "document", "location"] = Field(
        "text", description="Type of message content"
    )
    sender_type: Literal["user", "bot", "system"] = Field(..., description="Who sent the message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(MessageBase):
    """Model for creating a new message."""
    pass

class MessageUpdate(BaseModel):
    """Model for updating message metadata."""
    metadata: Optional[Dict[str, Any]] = None
    is_read: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)

class Message(MessageBase):
    """Complete message model with metadata."""
    id: UUID = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(..., description="Message timestamp")
    is_read: bool = Field(False, description="Whether message has been read")
    delivery_status: Literal["pending", "sent", "delivered", "read", "failed"] = Field(
        "pending", description="Message delivery status"
    )
    reply_to: Optional[UUID] = Field(None, description="ID of message being replied to")
    
    model_config = ConfigDict(from_attributes=True)

class MessageWithReply(Message):
    """Message model that includes replied-to message content."""
    replied_message: Optional[Message] = None

class MessageStats(BaseModel):
    """Message statistics for a conversation or project."""
    total_messages: int
    user_messages: int
    bot_messages: int
    system_messages: int
    unread_messages: int
    avg_response_time: float
    messages_today: int

class BulkMessageOperation(BaseModel):
    """Model for bulk operations on messages."""
    message_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation: Literal["mark_read", "delete", "archive"] = Field(..., description="Operation to perform")

# In-memory storage (replace with database in production)
messages_db: Dict[UUID, Dict[str, Any]] = {}
conversations_db: Dict[UUID, Dict[str, Any]] = {}  # Import from conversations module

@router.get("", response_model=List[Message])
@limiter.limit("200/minute")
async def list_messages(
    request: Request,
    conversation_id: Optional[UUID] = Query(None, description="Filter by conversation ID"),
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of messages to return"),
    sender_type: Optional[str] = Query(None, description="Filter by sender type"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    unread_only: bool = Query(False, description="Show only unread messages"),
    since: Optional[datetime] = Query(None, description="Show messages since timestamp"),
    current_user: str = Depends(get_current_user)
) -> List[Message]:
    """
    Retrieve messages with filtering and pagination.
    
    Args:
        conversation_id: Optional conversation filter
        skip: Number of messages to skip for pagination
        limit: Maximum number of messages to return
        sender_type: Optional filter by sender type
        message_type: Optional filter by message type
        unread_only: Show only unread messages
        since: Show messages since this timestamp
        current_user: Current authenticated user ID
        
    Returns:
        List of messages matching the criteria
    """
    try:
        logger.info(f"Listing messages for user {current_user}")
        
        # Filter messages based on conversation access
        user_messages = []
        for message in messages_db.values():
            # In production, validate access through database joins
            if conversation_id and message["conversation_id"] != conversation_id:
                continue
            user_messages.append(message)
        
        # Apply filters
        if sender_type:
            user_messages = [
                msg for msg in user_messages
                if msg["sender_type"] == sender_type
            ]
        
        if message_type:
            user_messages = [
                msg for msg in user_messages
                if msg["message_type"] == message_type
            ]
        
        if unread_only:
            user_messages = [
                msg for msg in user_messages
                if not msg.get("is_read", False)
            ]
        
        if since:
            user_messages = [
                msg for msg in user_messages
                if msg["timestamp"] >= since
            ]
        
        # Sort by timestamp descending (most recent first)
        user_messages.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply pagination
        paginated_messages = user_messages[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_messages)} messages")
        return [Message(**msg) for msg in paginated_messages]
        
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=Message, status_code=201)
@limiter.limit("100/minute")
async def create_message(
    request: Request,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
) -> Message:
    """
    Create a new message and broadcast to WebSocket connections.
    
    Args:
        message_data: Message creation data
        background_tasks: FastAPI background tasks for async operations
        current_user: Current authenticated user ID
        
    Returns:
        Created message with generated ID and timestamp
        
    Raises:
        HTTPException: If message creation fails or validation errors occur
    """
    try:
        logger.info(f"Creating message for conversation {message_data.conversation_id}")
        
        # Validate conversation exists and user has access
        if message_data.conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[message_data.conversation_id]
        await validate_project_access(conversation["project_id"], current_user)
        
        # Create new message
        message_id = uuid4()
        now = datetime.utcnow()
        
        new_message = {
            "id": message_id,
            "conversation_id": message_data.conversation_id,
            "content": message_data.content,
            "message_type": message_data.message_type,
            "sender_type": message_data.sender_type,
            "metadata": message_data.metadata or {},
            "timestamp": now,
            "is_read": False,
            "delivery_status": "sent",
            "reply_to": None
        }
        
        messages_db[message_id] = new_message
        
        # Update conversation stats
        conversation["message_count"] = conversation.get("message_count", 0) + 1
        conversation["last_message_at"] = now
        conversation["updated_at"] = now
        
        if message_data.sender_type == "user":
            conversation["unread_count"] = conversation.get("unread_count", 0) + 1
        
        # Broadcast to WebSocket connections
        background_tasks.add_task(
            websocket_manager.broadcast_to_conversation,
            message_data.conversation_id,
            {
                "type": "new_message",
                "data": new_message
            }
        )
        
        # If this is a user message, trigger bot response (in background)
        if message_data.sender_type == "user":
            background_tasks.add_task(
                generate_bot_response,
                message_data.conversation_id,
                new_message
            )
        
        logger.info(f"Message {message_id} created successfully")
        return Message(**new_message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{message_id}", response_model=MessageWithReply)
@limiter.limit("300/minute")
async def get_message(
    request: Request,
    message_id: UUID,
    include_reply: bool = Query(False, description="Include replied-to message"),
    current_user: str = Depends(get_current_user)
) -> MessageWithReply:
    """
    Retrieve a specific message by ID.
    
    Args:
        message_id: Unique message identifier
        include_reply: Whether to include the replied-to message
        current_user: Current authenticated user ID
        
    Returns:
        Message details with optional replied message
        
    Raises:
        HTTPException: If message not found or access denied
    """
    try:
        logger.info(f"Retrieving message {message_id}")
        
        if message_id not in messages_db:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message = messages_db[message_id]
        
        # Validate conversation access
        conversation = conversations_db.get(message["conversation_id"])
        if not conversation:
            raise HTTPException(status_code=404, detail="Associated conversation not found")
        
        await validate_project_access(conversation["project_id"], current_user)
        
        # Create response with optional replied message
        message_response = MessageWithReply(**message)
        
        if include_reply and message.get("reply_to"):
            replied_message_data = messages_db.get(message["reply_to"])
            if replied_message_data:
                message_response.replied_message = Message(**replied_message_data)
        
        return message_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{message_id}", response_model=Message)
@limiter.limit("50/minute")
async def update_message(
    request: Request,
    message_id: UUID,
    message_data: MessageUpdate,
    current_user: str = Depends(get_current_user)
) -> Message:
    """
    Update message metadata or read status.
    
    Args:
        message_id: Unique message identifier
        message_data: Updated message data
        current_user: Current authenticated user ID
        
    Returns:
        Updated message
        
    Raises:
        HTTPException: If message not found or access denied
    """
    try:
        logger.info(f"Updating message {message_id}")
        
        if message_id not in messages_db:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message = messages_db[message_id]
        
        # Validate conversation access
        conversation = conversations_db.get(message["conversation_id"])
        if not conversation:
            raise HTTPException(status_code=404, detail="Associated conversation not found")
        
        await validate_project_access(conversation["project_id"], current_user)
        
        # Update message fields
        update_data = message_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            message[field] = value
        
        # Update delivery status if marking as read
        if message_data.is_read and not message.get("is_read", False):
            message["delivery_status"] = "read"
            
            # Decrease unread count in conversation
            if conversation.get("unread_count", 0) > 0:
                conversation["unread_count"] -= 1
                conversation["updated_at"] = datetime.utcnow()
        
        logger.info(f"Message {message_id} updated successfully")
        return Message(**message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{message_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_message(
    request: Request,
    message_id: UUID,
    current_user: str = Depends(get_current_user)
) -> None:
    """
    Delete a message.
    
    Args:
        message_id: Unique message identifier
        current_user: Current authenticated user ID
        
    Raises:
        HTTPException: If message not found or access denied
    """
    try:
        logger.info(f"Deleting message {message_id}")
        
        if message_id not in messages_db:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message = messages_db[message_id]
        
        # Validate conversation access
        conversation = conversations_db.get(message["conversation_id"])
        if not conversation:
            raise HTTPException(status_code=404, detail="Associated conversation not found")
        
        await validate_project_access(conversation["project_id"], current_user)
        
        # Update conversation stats
        conversation["message_count"] = max(0, conversation.get("message_count", 1) - 1)
        conversation["updated_at"] = datetime.utcnow()
        
        if not message.get("is_read", False):
            conversation["unread_count"] = max(0, conversation.get("unread_count", 1) - 1)
        
        # Delete message
        del messages_db[message_id]
        
        logger.info(f"Message {message_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/bulk", response_model=Dict[str, Any])
@limiter.limit("20/minute")
async def bulk_message_operation(
    request: Request,
    operation_data: BulkMessageOperation,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform bulk operations on multiple messages.
    
    Args:
        operation_data: Bulk operation data
        current_user: Current authenticated user ID
        
    Returns:
        Operation results with success/failure counts
        
    Raises:
        HTTPException: If operation fails or access denied
    """
    try:
        logger.info(f"Performing bulk {operation_data.operation} on {len(operation_data.message_ids)} messages")
        
        success_count = 0
        failed_count = 0
        failed_ids = []
        
        for message_id in operation_data.message_ids:
            try:
                if message_id not in messages_db:
                    failed_count += 1
                    failed_ids.append(str(message_id))
                    continue
                
                message = messages_db[message_id]
                
                # Validate access
                conversation = conversations_db.get(message["conversation_id"])
                if not conversation:
                    failed_count += 1
                    failed_ids.append(str(message_id))
                    continue
                
                await validate_project_access(conversation["project_id"], current_user)
                
                # Perform operation
                if operation_data.operation == "mark_read":
                    if not message.get("is_read", False):
                        message["is_read"] = True
                        message["delivery_status"] = "read"
                        conversation["unread_count"] = max(0, conversation.get("unread_count", 1) - 1)
                
                elif operation_data.operation == "delete":
                    del messages_db[message_id]
                    conversation["message_count"] = max(0, conversation.get("message_count", 1) - 1)
                    if not message.get("is_read", False):
                        conversation["unread_count"] = max(0, conversation.get("unread_count", 1) - 1)
                
                elif operation_data.operation == "archive":
                    message["metadata"]["archived"] = True
                
                success_count += 1
                conversation["updated_at"] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error processing message {message_id}: {e}")
                failed_count += 1
                failed_ids.append(str(message_id))
        
        result = {
            "operation": operation_data.operation,
            "total_processed": len(operation_data.message_ids),
            "successful": success_count,
            "failed": failed_count,
            "failed_ids": failed_ids
        }
        
        logger.info(f"Bulk operation completed: {success_count} successful, {failed_count} failed")
        return result
        
    except Exception as e:
        logger.error(f"Error performing bulk operation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversation/{conversation_id}/stats", response_model=MessageStats)
@limiter.limit("100/minute")
async def get_conversation_message_stats(
    request: Request,
    conversation_id: UUID,
    current_user: str = Depends(get_current_user)
) -> MessageStats:
    """
    Get message statistics for a conversation.
    
    Args:
        conversation_id: Conversation identifier
        current_user: Current authenticated user ID
        
    Returns:
        Message statistics for the conversation
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Retrieving message stats for conversation {conversation_id}")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        await validate_project_access(conversation["project_id"], current_user)
        
        # Calculate stats from messages
        conversation_messages = [
            msg for msg in messages_db.values()
            if msg["conversation_id"] == conversation_id
        ]
        
        user_messages = len([msg for msg in conversation_messages if msg["sender_type"] == "user"])
        bot_messages = len([msg for msg in conversation_messages if msg["sender_type"] == "bot"])
        system_messages = len([msg for msg in conversation_messages if msg["sender_type"] == "system"])
        unread_messages = len([msg for msg in conversation_messages if not msg.get("is_read", False)])
        
        # Messages today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = len([
            msg for msg in conversation_messages
            if msg["timestamp"] >= today
        ])
        
        stats = MessageStats(
            total_messages=len(conversation_messages),
            user_messages=user_messages,
            bot_messages=bot_messages,
            system_messages=system_messages,
            unread_messages=unread_messages,
            avg_response_time=2.1,  # Would be calculated from actual response times
            messages_today=messages_today
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving message stats for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Background task for generating bot responses
async def generate_bot_response(conversation_id: UUID, user_message: Dict[str, Any]) -> None:
    """
    Generate and send a bot response to a user message.
    
    Args:
        conversation_id: Conversation ID
        user_message: User message that triggered the response
    """
    try:
        logger.info(f"Generating bot response for conversation {conversation_id}")
        
        # Simulate AI processing delay
        import asyncio
        await asyncio.sleep(1)
        
        # Generate bot response (in production, this would call an AI service)
        bot_response_content = f"Thank you for your message: '{user_message['content']}'. How can I help you further?"
        
        # Create bot message
        bot_message_id = uuid4()
        now = datetime.utcnow()
        
        bot_message = {
            "id": bot_message_id,
            "conversation_id": conversation_id,
            "content": bot_response_content,
            "message_type": "text",
            "sender_type": "bot",
            "metadata": {"response_to": str(user_message["id"])},
            "timestamp": now,
            "is_read": False,
            "delivery_status": "sent",
            "reply_to": user_message["id"]
        }
        
        messages_db[bot_message_id] = bot_message
        
        # Update conversation stats
        conversation = conversations_db[conversation_id]
        conversation["message_count"] = conversation.get("message_count", 0) + 1
        conversation["last_message_at"] = now
        conversation["updated_at"] = now
        
        # Broadcast bot response to WebSocket connections
        await websocket_manager.broadcast_to_conversation(
            conversation_id,
            {
                "type": "new_message",
                "data": bot_message
            }
        )
        
        logger.info(f"Bot response generated and sent for conversation {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error generating bot response for conversation {conversation_id}: {e}")