"""
Custom Exception Handlers for WhatsApp AI Chatbot

This module provides centralized exception handling for the FastAPI application,
including custom error responses, logging, and error formatting.
"""

import logging
import traceback
from typing import Union, Dict, Any
from datetime import datetime

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)

class ChatbotAPIError(Exception):
    """Base exception class for Chatbot API errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "API_ERROR",
        status_code: int = 500,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(ChatbotAPIError):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class AuthenticationError(ChatbotAPIError):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

class AuthorizationError(ChatbotAPIError):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )

class ResourceNotFoundError(ChatbotAPIError):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str = None, details: Dict[str, Any] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class ConflictError(ChatbotAPIError):
    """Exception for resource conflicts."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class RateLimitError(ChatbotAPIError):
    """Exception for rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = None,
        details: Dict[str, Any] = None
    ):
        if not details:
            details = {}
        
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )

class WebSocketError(ChatbotAPIError):
    """Exception for WebSocket-related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="WEBSOCKET_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

def format_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """
    Format a standardized error response.
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Request identifier for tracing
        
    Returns:
        Formatted error response dictionary
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return error_response

async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with custom formatting.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception instance
        
    Returns:
        JSON response with formatted error
    """
    try:
        request_id = getattr(request.state, 'request_id', None)
        
        # Log the exception
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail} - "
            f"Path: {request.url.path} - Request ID: {request_id}"
        )
        
        # Determine error code based on status
        error_code_mapping = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT"
        }
        
        error_code = error_code_mapping.get(exc.status_code, "HTTP_ERROR")
        
        error_response = format_error_response(
            error_code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers=getattr(exc, 'headers', None)
        )
        
    except Exception as e:
        logger.error(f"Error in HTTP exception handler: {e}")
        return JSONResponse(
            status_code=500,
            content=format_error_response(
                error_code="EXCEPTION_HANDLER_ERROR",
                message="Error processing exception",
                status_code=500
            )
        )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation exceptions with detailed field errors.
    
    Args:
        request: FastAPI request object
        exc: Validation exception instance
        
    Returns:
        JSON response with validation error details
    """
    try:
        request_id = getattr(request.state, 'request_id', None)
        
        # Extract validation errors
        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(x) for x in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        logger.warning(
            f"Validation error: {len(validation_errors)} field(s) failed validation - "
            f"Path: {request.url.path} - Request ID: {request_id}"
        )
        
        error_response = format_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": validation_errors},
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response
        )
        
    except Exception as e:
        logger.error(f"Error in validation exception handler: {e}")
        return JSONResponse(
            status_code=500,
            content=format_error_response(
                error_code="VALIDATION_HANDLER_ERROR",
                message="Error processing validation exception",
                status_code=500
            )
        )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSON response with generic error message
    """
    try:
        request_id = getattr(request.state, 'request_id', None)
        
        # Check if it's one of our custom exceptions
        if isinstance(exc, ChatbotAPIError):
            logger.warning(
                f"API error: {exc.error_code} - {exc.message} - "
                f"Path: {request.url.path} - Request ID: {request_id}"
            )
            
            error_response = format_error_response(
                error_code=exc.error_code,
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response
            )
        
        # Handle unexpected exceptions
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)} - "
            f"Path: {request.url.path} - Request ID: {request_id}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Don't expose internal error details in production
        error_message = "Internal server error"
        details = None
        
        # In development, include more details
        import os
        if os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            details = {"traceback": traceback.format_exc().split("\n")}
        
        error_response = format_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message=error_message,
            status_code=500,
            details=details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
        
    except Exception as handler_error:
        logger.critical(f"Critical error in exception handler: {handler_error}")
        
        # Return minimal error response
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "CRITICAL_ERROR",
                    "message": "A critical error occurred",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": 500
                }
            }
        )

# Custom exception classes for specific business logic
class ProjectNotFoundError(ResourceNotFoundError):
    """Exception for project not found errors."""
    
    def __init__(self, project_id: str, details: Dict[str, Any] = None):
        super().__init__(
            resource="Project",
            identifier=project_id,
            details=details
        )

class ConversationNotFoundError(ResourceNotFoundError):
    """Exception for conversation not found errors."""
    
    def __init__(self, conversation_id: str, details: Dict[str, Any] = None):
        super().__init__(
            resource="Conversation",
            identifier=conversation_id,
            details=details
        )

class MessageNotFoundError(ResourceNotFoundError):
    """Exception for message not found errors."""
    
    def __init__(self, message_id: str, details: Dict[str, Any] = None):
        super().__init__(
            resource="Message",
            identifier=message_id,
            details=details
        )

class InvalidWebhookError(ValidationError):
    """Exception for invalid webhook data."""
    
    def __init__(self, message: str = "Invalid webhook payload", details: Dict[str, Any] = None):
        super().__init__(message=message, details=details)

class WhatsAppAPIError(ChatbotAPIError):
    """Exception for WhatsApp API-related errors."""
    
    def __init__(
        self,
        message: str,
        whatsapp_error_code: str = None,
        details: Dict[str, Any] = None
    ):
        if not details:
            details = {}
        
        if whatsapp_error_code:
            details["whatsapp_error_code"] = whatsapp_error_code
        
        super().__init__(
            message=message,
            error_code="WHATSAPP_API_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )

# Error response models for OpenAPI documentation
class ErrorResponse(Dict[str, Any]):
    """Standard error response model."""
    pass

class ValidationErrorResponse(ErrorResponse):
    """Validation error response model."""
    pass

# Utility functions for error handling
def log_error_with_context(
    error: Exception,
    request: Request = None,
    user_id: str = None,
    additional_context: Dict[str, Any] = None
) -> None:
    """
    Log an error with additional context information.
    
    Args:
        error: Exception to log
        request: FastAPI request object
        user_id: User ID if available
        additional_context: Additional context information
    """
    context_info = []
    
    if request:
        request_id = getattr(request.state, 'request_id', None)
        context_info.extend([
            f"Path: {request.url.path}",
            f"Method: {request.method}",
            f"Request ID: {request_id}"
        ])
    
    if user_id:
        context_info.append(f"User: {user_id}")
    
    if additional_context:
        for key, value in additional_context.items():
            context_info.append(f"{key}: {value}")
    
    context_str = " - ".join(context_info) if context_info else "No additional context"
    
    logger.error(
        f"Error: {type(error).__name__} - {str(error)} - {context_str}\n"
        f"Traceback: {traceback.format_exc()}"
    )