"""
FastAPI Main Application for WhatsApp AI Chatbot

This module sets up the main FastAPI application with all necessary middleware,
routers, and configuration for production deployment.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api import projects, conversations, messages, websocket
from src.utils.exceptions import (
    custom_http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from src.utils.dependencies import get_database_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events including:
    - Database connection initialization
    - WebSocket connection manager setup
    - Cleanup operations
    """
    logger.info("Starting WhatsApp AI Chatbot API server...")
    
    # Startup operations
    try:
        # Initialize WebSocket manager
        from src.api.websocket import websocket_manager
        await websocket_manager.initialize()
        logger.info("WebSocket manager initialized")
        
        # Database health check
        db_status = await get_database_status()
        if db_status["status"] == "healthy":
            logger.info("Database connection established")
        else:
            logger.warning(f"Database connection issues: {db_status}")
            
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield  # Application is running
    
    # Shutdown operations
    logger.info("Shutting down WhatsApp AI Chatbot API server...")
    try:
        # Cleanup WebSocket connections
        from src.api.websocket import websocket_manager
        await websocket_manager.cleanup()
        logger.info("WebSocket connections cleaned up")
        
        logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="WhatsApp AI Chatbot API",
    description="Backend API for WhatsApp AI Chatbot with real-time messaging support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative frontend port
        "https://yourdomain.com",  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware for request logging and performance monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware for request logging and performance monitoring.
    
    Logs all incoming requests with timing information and adds
    request ID headers for tracing.
    """
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}-{hash(str(request.url))}"
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    logger.info(
        f"Request started: {request.method} {request.url} "
        f"- Request ID: {request_id}"
    )
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"Request completed: {request.method} {request.url} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.4f}s "
            f"- Request ID: {request_id}"
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url} "
            f"- Error: {str(e)} "
            f"- Time: {process_time:.4f}s "
            f"- Request ID: {request_id}"
        )
        raise

# Exception handlers
app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Health check endpoint
@app.get("/health", tags=["Health"])
@limiter.limit("30/minute")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint for monitoring application status.
    
    Returns:
        Dict containing application health status and database connectivity
    """
    try:
        db_status = await get_database_status()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "database": db_status,
            "websocket": {
                "status": "active",
                "connections": len(websocket.websocket_manager.active_connections)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "error": str(e)
        }

# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Dict with API information
    """
    return {
        "message": "WhatsApp AI Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include API routers with versioning
app.include_router(
    projects.router,
    prefix="/api/v1/projects",
    tags=["Projects"]
)

app.include_router(
    conversations.router,
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)

app.include_router(
    messages.router,
    prefix="/api/v1/messages",
    tags=["Messages"]
)

app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        loop="uvloop"
    )