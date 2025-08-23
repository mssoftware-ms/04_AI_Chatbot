"""
Conversations API endpoints for WhatsApp AI Chatbot

This module provides CRUD operations for managing conversations within projects.
Each conversation represents a chat session with a specific WhatsApp contact.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.utils.dependencies import get_current_user, validate_project_access

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Pydantic models
class ConversationBase(BaseModel):
    """Base model for conversation data."""
    project_id: UUID = Field(..., description="Associated project ID")
    contact_phone: str = Field(..., description="WhatsApp contact phone number")
    contact_name: Optional[str] = Field(None, max_length=100, description="Contact display name")
    status: str = Field("active", description="Conversation status")
    tags: Optional[List[str]] = Field(default_factory=list, description="Conversation tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(ConversationBase):
    """Model for creating a new conversation."""
    pass

class ConversationUpdate(BaseModel):
    """Model for updating an existing conversation."""
    contact_name: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class Conversation(ConversationBase):
    """Complete conversation model with metadata."""
    id: UUID = Field(..., description="Unique conversation identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    message_count: int = Field(0, description="Total number of messages")
    unread_count: int = Field(0, description="Number of unread messages")
    
    model_config = ConfigDict(from_attributes=True)

class ConversationSummary(BaseModel):
    """Conversation summary with basic info."""
    id: UUID
    contact_phone: str
    contact_name: Optional[str]
    status: str
    last_message_at: Optional[datetime]
    message_count: int
    unread_count: int

class ConversationStats(BaseModel):
    """Conversation statistics model."""
    total_messages: int
    user_messages: int
    bot_messages: int
    avg_response_time: float
    first_message_at: Optional[datetime]
    last_message_at: Optional[datetime]
    session_duration: Optional[float]  # in seconds

# In-memory storage (replace with database in production)
conversations_db: Dict[UUID, Dict[str, Any]] = {}

@router.get("", response_model=List[Conversation])
@limiter.limit("100/minute")
async def list_conversations(
    request: Request,
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of conversations to return"),
    status: Optional[str] = Query(None, description="Filter by conversation status"),
    search: Optional[str] = Query(None, description="Search term for contact name or phone"),
    has_unread: Optional[bool] = Query(None, description="Filter by unread messages"),
    current_user: str = Depends(get_current_user)
) -> List[Conversation]:
    """
    Retrieve a list of conversations.
    
    Args:
        project_id: Optional project ID filter
        skip: Number of conversations to skip for pagination
        limit: Maximum number of conversations to return
        status: Optional status filter
        search: Optional search term
        has_unread: Optional filter for conversations with unread messages
        current_user: Current authenticated user ID
        
    Returns:
        List of conversations matching the criteria
    """
    try:
        logger.info(f"Listing conversations for user {current_user}")
        
        # Get all conversations for accessible projects
        user_conversations = []
        for conversation in conversations_db.values():
            # In production, validate project access through database join
            # For now, assume all conversations are accessible
            user_conversations.append(conversation)
        
        # Apply filters
        if project_id:
            user_conversations = [
                conv for conv in user_conversations
                if conv["project_id"] == project_id
            ]
        
        if status:
            user_conversations = [
                conv for conv in user_conversations
                if conv["status"] == status
            ]
        
        if search:
            search_lower = search.lower()
            user_conversations = [
                conv for conv in user_conversations
                if (search_lower in conv["contact_phone"] or
                    (conv.get("contact_name") and search_lower in conv["contact_name"].lower()))
            ]
        
        if has_unread is not None:
            if has_unread:
                user_conversations = [
                    conv for conv in user_conversations
                    if conv.get("unread_count", 0) > 0
                ]
            else:
                user_conversations = [
                    conv for conv in user_conversations
                    if conv.get("unread_count", 0) == 0
                ]
        
        # Sort by last_message_at descending (most recent first)
        user_conversations.sort(
            key=lambda x: x.get("last_message_at") or x["created_at"],
            reverse=True
        )
        
        # Apply pagination
        paginated_conversations = user_conversations[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_conversations)} conversations")
        return [Conversation(**conv) for conv in paginated_conversations]
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=Conversation, status_code=201)
@limiter.limit("50/minute")
async def create_conversation(
    request: Request,
    conversation_data: ConversationCreate,
    current_user: str = Depends(get_current_user)
) -> Conversation:
    """
    Create a new conversation.
    
    Args:
        conversation_data: Conversation creation data
        current_user: Current authenticated user ID
        
    Returns:
        Created conversation with generated ID and timestamps
        
    Raises:
        HTTPException: If conversation creation fails or validation errors occur
    """
    try:
        logger.info(f"Creating conversation for project {conversation_data.project_id}")
        
        # Validate project access (in production, check database)
        await validate_project_access(conversation_data.project_id, current_user)
        
        # Check for duplicate conversation (same project + contact)
        existing_conversation = None
        for conv in conversations_db.values():
            if (conv["project_id"] == conversation_data.project_id and
                conv["contact_phone"] == conversation_data.contact_phone):
                existing_conversation = conv
                break
        
        if existing_conversation:
            # Return existing conversation instead of creating duplicate
            logger.info(f"Returning existing conversation for {conversation_data.contact_phone}")
            return Conversation(**existing_conversation)
        
        # Create new conversation
        conversation_id = uuid4()
        now = datetime.utcnow()
        
        new_conversation = {
            "id": conversation_id,
            "project_id": conversation_data.project_id,
            "contact_phone": conversation_data.contact_phone,
            "contact_name": conversation_data.contact_name,
            "status": conversation_data.status,
            "tags": conversation_data.tags or [],
            "metadata": conversation_data.metadata or {},
            "created_at": now,
            "updated_at": now,
            "last_message_at": None,
            "message_count": 0,
            "unread_count": 0
        }
        
        conversations_db[conversation_id] = new_conversation
        
        logger.info(f"Conversation {conversation_id} created successfully")
        return Conversation(**new_conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{conversation_id}", response_model=Conversation)
@limiter.limit("200/minute")
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    current_user: str = Depends(get_current_user)
) -> Conversation:
    """
    Retrieve a specific conversation by ID.
    
    Args:
        conversation_id: Unique conversation identifier
        current_user: Current authenticated user ID
        
    Returns:
        Conversation details
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Retrieving conversation {conversation_id}")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        
        # Validate project access (in production, check through database join)
        await validate_project_access(conversation["project_id"], current_user)
        
        return Conversation(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{conversation_id}", response_model=Conversation)
@limiter.limit("100/minute")
async def update_conversation(
    request: Request,
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    current_user: str = Depends(get_current_user)
) -> Conversation:
    """
    Update an existing conversation.
    
    Args:
        conversation_id: Unique conversation identifier
        conversation_data: Updated conversation data
        current_user: Current authenticated user ID
        
    Returns:
        Updated conversation
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Updating conversation {conversation_id}")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        
        # Validate project access
        await validate_project_access(conversation["project_id"], current_user)
        
        # Update conversation fields
        update_data = conversation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            conversation[field] = value
        
        conversation["updated_at"] = datetime.utcnow()
        
        logger.info(f"Conversation {conversation_id} updated successfully")
        return Conversation(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{conversation_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_conversation(
    request: Request,
    conversation_id: UUID,
    current_user: str = Depends(get_current_user)
) -> None:
    """
    Delete a conversation and all associated messages.
    
    Args:
        conversation_id: Unique conversation identifier
        current_user: Current authenticated user ID
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Deleting conversation {conversation_id}")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        
        # Validate project access
        await validate_project_access(conversation["project_id"], current_user)
        
        # Delete conversation (in production, this would cascade delete messages)
        del conversations_db[conversation_id]
        
        logger.info(f"Conversation {conversation_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{conversation_id}/stats", response_model=ConversationStats)
@limiter.limit("100/minute")
async def get_conversation_stats(
    request: Request,
    conversation_id: UUID,
    current_user: str = Depends(get_current_user)
) -> ConversationStats:
    """
    Get detailed statistics for a conversation.
    
    Args:
        conversation_id: Unique conversation identifier
        current_user: Current authenticated user ID
        
    Returns:
        Conversation statistics including message counts and timing data
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Retrieving stats for conversation {conversation_id}")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        
        # Validate project access
        await validate_project_access(conversation["project_id"], current_user)
        
        # In production, these would be calculated from database queries
        stats = ConversationStats(
            total_messages=conversation.get("message_count", 0),
            user_messages=0,  # Would be calculated from message data
            bot_messages=0,   # Would be calculated from message data
            avg_response_time=2.5,  # Would be calculated from message timestamps
            first_message_at=conversation["created_at"],
            last_message_at=conversation.get("last_message_at"),
            session_duration=0.0  # Would be calculated from first/last message times
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stats for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/{conversation_id}/mark-read", response_model=Conversation)
@limiter.limit("200/minute")
async def mark_conversation_read(
    request: Request,
    conversation_id: UUID,
    current_user: str = Depends(get_current_user)
) -> Conversation:
    """
    Mark all messages in a conversation as read.
    
    Args:
        conversation_id: Unique conversation identifier
        current_user: Current authenticated user ID
        
    Returns:
        Updated conversation with unread_count reset to 0
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Marking conversation {conversation_id} as read")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        
        # Validate project access
        await validate_project_access(conversation["project_id"], current_user)
        
        # Mark as read
        conversation["unread_count"] = 0
        conversation["updated_at"] = datetime.utcnow()
        
        logger.info(f"Conversation {conversation_id} marked as read")
        return Conversation(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking conversation {conversation_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/{conversation_id}/status", response_model=Conversation)
@limiter.limit("100/minute")
async def update_conversation_status(
    request: Request,
    conversation_id: UUID,
    status: str = Query(..., description="New conversation status"),
    current_user: str = Depends(get_current_user)
) -> Conversation:
    """
    Update conversation status (active, archived, closed, etc.).
    
    Args:
        conversation_id: Unique conversation identifier
        status: New status value
        current_user: Current authenticated user ID
        
    Returns:
        Updated conversation with new status
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    try:
        logger.info(f"Updating status for conversation {conversation_id} to {status}")
        
        if conversation_id not in conversations_db:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        
        # Validate project access
        await validate_project_access(conversation["project_id"], current_user)
        
        # Update status
        conversation["status"] = status
        conversation["updated_at"] = datetime.utcnow()
        
        logger.info(f"Conversation {conversation_id} status updated to {status}")
        return Conversation(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")