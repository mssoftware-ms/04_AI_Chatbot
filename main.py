"""
FastAPI application entry point.

This is the main application file that sets up the FastAPI server,
middleware, routes, and starts the application.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

# Änderung durch KI - Import config with fallback
try:
    from config.config import settings
except ImportError:
    from config.settings import settings

try:
    from src.utils.logging_config import setup_logging
except ImportError:
    from config.logging_config import setup_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create FastAPI instance
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description="A modern WhatsApp-like AI Chatbot with project management capabilities",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Add trusted host middleware for production
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with application information."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "Documentation disabled in production",
            "health": "/health"
        }
    
    # Mount static files (when UI is implemented)
    # app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Import and include routers (will be implemented later)
    # from src.api import auth, chat, projects, files
    # app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    # app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    # app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
    # app.include_router(files.router, prefix="/api/files", tags=["Files"])
    
    logger.info(f"FastAPI application created successfully")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly."""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )