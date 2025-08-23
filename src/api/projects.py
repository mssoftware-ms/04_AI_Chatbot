"""
Projects API endpoints for WhatsApp AI Chatbot

This module provides CRUD operations for managing chatbot projects.
Each project represents a distinct WhatsApp chatbot instance with
its own configuration and conversation history.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
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
class ProjectBase(BaseModel):
    """Base model for project data."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    webhook_url: Optional[str] = Field(None, description="WhatsApp webhook URL")
    phone_number: Optional[str] = Field(None, description="Associated WhatsApp phone number")
    is_active: bool = Field(True, description="Whether the project is active")
    
    model_config = ConfigDict(from_attributes=True)

class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    pass

class ProjectUpdate(BaseModel):
    """Model for updating an existing project."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)

class Project(ProjectBase):
    """Complete project model with metadata."""
    id: UUID = Field(..., description="Unique project identifier")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    conversation_count: int = Field(0, description="Number of conversations")
    message_count: int = Field(0, description="Total number of messages")
    
    model_config = ConfigDict(from_attributes=True)

class ProjectStats(BaseModel):
    """Project statistics model."""
    total_conversations: int
    active_conversations: int
    total_messages: int
    messages_today: int
    avg_response_time: float
    last_activity: Optional[datetime]

# In-memory storage (replace with database in production)
projects_db: Dict[UUID, Dict[str, Any]] = {}

@router.get("", response_model=List[Project])
@limiter.limit("100/minute")
async def list_projects(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of projects to return"),
    search: Optional[str] = Query(None, description="Search term for project name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: str = Depends(get_current_user)
) -> List[Project]:
    """
    Retrieve a list of projects for the current user.
    
    Args:
        skip: Number of projects to skip for pagination
        limit: Maximum number of projects to return
        search: Optional search term to filter projects
        is_active: Optional filter for active/inactive projects
        current_user: Current authenticated user ID
        
    Returns:
        List of projects matching the criteria
    """
    try:
        logger.info(f"Listing projects for user {current_user}")
        
        # Filter projects by user
        user_projects = [
            project for project in projects_db.values()
            if project["user_id"] == current_user
        ]
        
        # Apply filters
        if search:
            search_lower = search.lower()
            user_projects = [
                project for project in user_projects
                if search_lower in project["name"].lower() or
                (project.get("description") and search_lower in project["description"].lower())
            ]
        
        if is_active is not None:
            user_projects = [
                project for project in user_projects
                if project["is_active"] == is_active
            ]
        
        # Sort by updated_at descending
        user_projects.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # Apply pagination
        paginated_projects = user_projects[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_projects)} projects for user {current_user}")
        return [Project(**project) for project in paginated_projects]
        
    except Exception as e:
        logger.error(f"Error listing projects for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=Project, status_code=201)
@limiter.limit("20/minute")
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    current_user: str = Depends(get_current_user)
) -> Project:
    """
    Create a new project.
    
    Args:
        project_data: Project creation data
        current_user: Current authenticated user ID
        
    Returns:
        Created project with generated ID and timestamps
        
    Raises:
        HTTPException: If project creation fails or validation errors occur
    """
    try:
        logger.info(f"Creating project '{project_data.name}' for user {current_user}")
        
        # Check for duplicate project names for the user
        existing_names = [
            project["name"] for project in projects_db.values()
            if project["user_id"] == current_user
        ]
        
        if project_data.name in existing_names:
            raise HTTPException(
                status_code=409,
                detail=f"Project with name '{project_data.name}' already exists"
            )
        
        # Create new project
        project_id = uuid4()
        now = datetime.utcnow()
        
        new_project = {
            "id": project_id,
            "user_id": current_user,
            "name": project_data.name,
            "description": project_data.description,
            "webhook_url": project_data.webhook_url,
            "phone_number": project_data.phone_number,
            "is_active": project_data.is_active,
            "created_at": now,
            "updated_at": now,
            "conversation_count": 0,
            "message_count": 0
        }
        
        projects_db[project_id] = new_project
        
        logger.info(f"Project {project_id} created successfully for user {current_user}")
        return Project(**new_project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{project_id}", response_model=Project)
@limiter.limit("200/minute")
async def get_project(
    request: Request,
    project_id: UUID,
    current_user: str = Depends(get_current_user)
) -> Project:
    """
    Retrieve a specific project by ID.
    
    Args:
        project_id: Unique project identifier
        current_user: Current authenticated user ID
        
    Returns:
        Project details
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        logger.info(f"Retrieving project {project_id} for user {current_user}")
        
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_db[project_id]
        
        # Validate user access
        if project["user_id"] != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return Project(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{project_id}", response_model=Project)
@limiter.limit("50/minute")
async def update_project(
    request: Request,
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: str = Depends(get_current_user)
) -> Project:
    """
    Update an existing project.
    
    Args:
        project_id: Unique project identifier
        project_data: Updated project data
        current_user: Current authenticated user ID
        
    Returns:
        Updated project
        
    Raises:
        HTTPException: If project not found, access denied, or validation errors
    """
    try:
        logger.info(f"Updating project {project_id} for user {current_user}")
        
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_db[project_id]
        
        # Validate user access
        if project["user_id"] != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check for name conflicts if name is being updated
        if project_data.name and project_data.name != project["name"]:
            existing_names = [
                p["name"] for p in projects_db.values()
                if p["user_id"] == current_user and p["id"] != project_id
            ]
            
            if project_data.name in existing_names:
                raise HTTPException(
                    status_code=409,
                    detail=f"Project with name '{project_data.name}' already exists"
                )
        
        # Update project fields
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            project[field] = value
        
        project["updated_at"] = datetime.utcnow()
        
        logger.info(f"Project {project_id} updated successfully")
        return Project(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{project_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_project(
    request: Request,
    project_id: UUID,
    current_user: str = Depends(get_current_user)
) -> None:
    """
    Delete a project and all associated data.
    
    Args:
        project_id: Unique project identifier
        current_user: Current authenticated user ID
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        logger.info(f"Deleting project {project_id} for user {current_user}")
        
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_db[project_id]
        
        # Validate user access
        if project["user_id"] != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete project (in production, this would cascade delete conversations and messages)
        del projects_db[project_id]
        
        logger.info(f"Project {project_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{project_id}/stats", response_model=ProjectStats)
@limiter.limit("100/minute")
async def get_project_stats(
    request: Request,
    project_id: UUID,
    current_user: str = Depends(get_current_user)
) -> ProjectStats:
    """
    Get detailed statistics for a project.
    
    Args:
        project_id: Unique project identifier
        current_user: Current authenticated user ID
        
    Returns:
        Project statistics including conversation and message counts
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        logger.info(f"Retrieving stats for project {project_id}")
        
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_db[project_id]
        
        # Validate user access
        if project["user_id"] != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # In production, these would be calculated from database queries
        stats = ProjectStats(
            total_conversations=project.get("conversation_count", 0),
            active_conversations=0,  # Would be calculated from active conversations
            total_messages=project.get("message_count", 0),
            messages_today=0,  # Would be calculated from today's messages
            avg_response_time=1.2,  # Would be calculated from message timestamps
            last_activity=project.get("updated_at")
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stats for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")