#!/usr/bin/env python3
"""
Fixed WhatsApp AI Chatbot launcher with proper threading support.
This version handles Flet UI threading issues correctly.
"""

import asyncio
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging_config import setup_logging
from config.settings import settings

# Set up logging
setup_logging(settings.log_level)
import logging
logger = logging.getLogger(__name__)


def start_ui_safe():
    """Start Flet UI in main thread (safer approach)."""
    try:
        import flet as ft
        from src.ui.chat_app import ChatApp
        
        def main(page: ft.Page):
            try:
                app = ChatApp()
                app.main(page)
            except Exception as e:
                logger.error(f"ChatApp error: {e}")
                page.add(ft.Text(f"UI Error: {e}", color="red"))
        
        logger.info(f"Starting Flet UI on port {settings.ui_port}")
        logger.info(f"UI will be available at: http://localhost:{settings.ui_port}")
        
        ft.app(
            target=main,
            port=settings.ui_port,
            view=ft.WEB_BROWSER,
            assets_dir="assets"
        )
        
    except Exception as e:
        logger.error(f"Failed to start UI: {e}")
        logger.info("UI not available, but backend should still work")


async def start_backend_safe():
    """Start FastAPI backend safely."""
    try:
        import uvicorn
        from src.main import app
        
        logger.info(f"Starting backend on {settings.host}:{settings.port}")
        
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,  # Disable reload in production
            log_level=settings.log_level.lower()
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Backend error: {e}")
        raise


def start_backend_only():
    """Start only backend server."""
    logger.info("=" * 60)
    logger.info("🚀 WhatsApp AI Chatbot - Backend Only")
    logger.info("=" * 60)
    
    asyncio.run(start_backend_safe())


def start_ui_only():
    """Start only UI server.""" 
    logger.info("=" * 60)
    logger.info("🖥️  WhatsApp AI Chatbot - UI Only")
    logger.info("=" * 60)
    logger.info("Note: Make sure backend is running separately!")
    
    start_ui_safe()


def start_full_app():
    """Start both backend and UI (sequential approach)."""
    logger.info("=" * 60)
    logger.info("🚀 WhatsApp AI Chatbot - Full Application")
    logger.info("=" * 60)
    
    # Start backend in background thread
    backend_thread = threading.Thread(
        target=lambda: asyncio.run(start_backend_safe()),
        daemon=True
    )
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Check if backend is alive
    if backend_thread.is_alive():
        logger.info("✅ Backend started successfully")
        logger.info(f"✅ API available at: http://localhost:{settings.port}")
        
        # Start UI in main thread
        logger.info("Starting UI...")
        start_ui_safe()
    else:
        logger.error("❌ Backend failed to start")
        sys.exit(1)


def main():
    """Main entry point with better error handling."""
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "backend":
            start_backend_only()
        elif mode == "ui":
            start_ui_only() 
        elif mode == "full":
            start_full_app()
        elif mode == "test":
            logger.info("Running tests...")
            import pytest
            pytest.main(["-v", "tests/"])
        else:
            print("\nUsage:")
            print("  python start_app_fixed.py backend  # Backend only")
            print("  python start_app_fixed.py ui       # UI only")
            print("  python start_app_fixed.py full     # Both (recommended)")
            print("  python start_app_fixed.py test     # Run tests")
    else:
        # Default: start full application
        start_full_app()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
        sys.exit(1)