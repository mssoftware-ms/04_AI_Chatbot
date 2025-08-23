"""
FastAPI Dependencies for WhatsApp AI Chatbot

This module provides dependency injection functions for FastAPI endpoints,
including authentication, authorization, and database utilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
import jwt

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Änderung durch KI - Configuration with secure defaults
import os
import secrets

# Secure configuration loading
JWT_SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
    import warnings
    warnings.warn(
        "No SECRET_KEY found in environment variables. Using auto-generated key. "
        "Set SECRET_KEY environment variable for production.",
        UserWarning
    )

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours

# In-memory storage (replace with database in production)
projects_db: Dict[UUID, Dict[str, Any]] = {}
conversations_db: Dict[UUID, Dict[str, Any]] = {}

class AuthenticationError(Exception):
    """Custom authentication error."""
    pass

class AuthorizationError(Exception):
    """Custom authorization error."""
    pass

# Änderung durch KI - Enhanced type hints and security
def create_access_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User identifier
        additional_claims: Optional additional JWT claims
        
    Returns:
        JWT token string
    """
    try:
        # Änderung durch KI - Security enhancement: use timezone-aware datetime
        from datetime import timezone
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "exp": now.timestamp() + (JWT_EXPIRATION_MINUTES * 60),
            "iat": now.timestamp(),
            "type": "access_token",
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation tracking
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.info(f"Access token created for user {user_id}")
        return token
        
    except Exception as e:
        logger.error(f"Error creating access token for user {user_id}: {e}")
        raise AuthenticationError("Failed to create access token")

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check token type
        if payload.get("type") != "access_token":
            raise AuthenticationError("Invalid token type")
        
        # Änderung durch KI - Security enhancement: use timezone-aware datetime
        from datetime import timezone
        exp = payload.get("exp")
        if not exp or datetime.now(timezone.utc).timestamp() > exp:
            raise AuthenticationError("Token has expired")
        
        logger.debug(f"Token verified for user {payload.get('user_id')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise AuthenticationError("Token verification failed")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract and validate the current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID from the token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        if not credentials:
            raise AuthenticationError("Authorization header missing")
        
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise AuthenticationError("User ID not found in token")
        
        logger.debug(f"Authenticated user: {user_id}")
        return user_id
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_websocket(websocket: WebSocket) -> str:
    """
    Extract and validate the current user from WebSocket connection.
    
    Args:
        websocket: WebSocket connection instance
        
    Returns:
        User ID from the token
        
    Raises:
        WebSocketException: If authentication fails
    """
    try:
        # Get token from query parameters or headers
        token = None
        
        # Try query parameter first
        if "token" in websocket.query_params:
            token = websocket.query_params["token"]
        
        # Try Authorization header
        if not token:
            auth_header = websocket.headers.get("authorization")
            if auth_header:
                scheme, param = get_authorization_scheme_param(auth_header)
                if scheme.lower() == "bearer":
                    token = param
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
            raise AuthenticationError("No authentication token provided")
        
        payload = verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise AuthenticationError("User ID not found in token")
        
        logger.debug(f"WebSocket authenticated user: {user_id}")
        return user_id
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
        raise AuthenticationError("WebSocket authentication failed")

async def get_optional_user(request: Request) -> Optional[str]:
    """
    Extract user ID from token if present, but don't require authentication.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID if authenticated, None otherwise
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None
        
        scheme, param = get_authorization_scheme_param(auth_header)
        if scheme.lower() != "bearer" or not param:
            return None
        
        payload = verify_token(param)
        user_id = payload.get("user_id")
        
        logger.debug(f"Optional auth - User: {user_id}")
        return user_id
        
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None

async def validate_project_access(project_id: UUID, user_id: str) -> None:
    """
    Validate that a user has access to a specific project.
    
    Args:
        project_id: Project identifier
        user_id: User identifier
        
    Raises:
        HTTPException: If access is denied or project not found
    """
    try:
        logger.debug(f"Validating project access - Project: {project_id}, User: {user_id}")
        
        # In production, this would query the database
        # For now, use in-memory storage
        if project_id not in projects_db:
            logger.warning(f"Project {project_id} not found for user {user_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_db[project_id]
        
        if project["user_id"] != user_id:
            logger.warning(f"Access denied - Project {project_id} for user {user_id}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.debug(f"Project access validated - Project: {project_id}, User: {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating project access: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def validate_conversation_access(conversation_id: UUID, user_id: str) -> None:
    """
    Validate that a user has access to a specific conversation.
    
    Args:
        conversation_id: Conversation identifier
        user_id: User identifier
        
    Raises:
        HTTPException: If access is denied or conversation not found
    """
    try:
        logger.debug(f"Validating conversation access - Conversation: {conversation_id}, User: {user_id}")
        
        # In production, this would query the database
        if conversation_id not in conversations_db:
            logger.warning(f"Conversation {conversation_id} not found")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversations_db[conversation_id]
        project_id = conversation["project_id"]
        
        # Validate project access (which validates user access)
        await validate_project_access(project_id, user_id)
        
        logger.debug(f"Conversation access validated - Conversation: {conversation_id}, User: {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating conversation access: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_database_status() -> Dict[str, Any]:
    """
    Get current database connection status and health metrics.
    
    Returns:
        Dictionary with database status information
    """
    try:
        # In production, this would check actual database connectivity
        # For now, simulate database health check
        
        # Simulate database ping
        import asyncio
        await asyncio.sleep(0.01)  # Simulate network delay
        
        status_info = {
            "status": "healthy",
            "connection_pool": {
                "active": 5,
                "idle": 3,
                "max": 10
            },
            "response_time_ms": 10,
            "last_check": datetime.utcnow().isoformat()
        }
        
        logger.debug("Database health check completed successfully")
        return status_info
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

class RateLimitExceeded(Exception):
    """Custom rate limit exceeded error."""
    pass

async def check_rate_limit(request: Request, limit: int = 100, window: int = 60) -> None:
    """
    Check if the current request exceeds rate limits.
    
    Args:
        request: FastAPI request object
        limit: Number of requests allowed per window
        window: Time window in seconds
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    try:
        # Get client identifier (IP address or user ID)
        client_id = request.client.host if request.client else "unknown"
        
        # Try to get user ID if authenticated
        try:
            auth_header = request.headers.get("authorization")
            if auth_header:
                scheme, param = get_authorization_scheme_param(auth_header)
                if scheme.lower() == "bearer" and param:
                    payload = verify_token(param)
                    client_id = payload.get("user_id", client_id)
        except:
            pass  # Use IP address if token validation fails
        
        # In production, this would use Redis or similar for rate limiting
        # For now, just log the rate limit check
        logger.debug(f"Rate limit check - Client: {client_id}, Limit: {limit}/{window}s")
        
        # Simulate rate limiting logic
        # In production, implement proper rate limiting with sliding window
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        # Don't fail the request if rate limiting fails
        pass

# Dependency for admin users (example of role-based access)
async def get_admin_user(current_user: str = Depends(get_current_user)) -> str:
    """
    Validate that the current user has admin privileges.
    
    Args:
        current_user: Current authenticated user ID
        
    Returns:
        User ID if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    try:
        # In production, check user role in database
        # For now, assume users with "admin" in their ID are admins
        if "admin" not in current_user.lower():
            logger.warning(f"Admin access denied for user {current_user}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        logger.debug(f"Admin access granted for user {current_user}")
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking admin access: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility function to create a demo user token (for testing)
def create_demo_token(user_id: str = "demo_user") -> str:
    """
    Create a demo JWT token for testing purposes.
    
    Args:
        user_id: User ID for the demo token
        
    Returns:
        JWT token string
    """
    return create_access_token(user_id, {"demo": True})