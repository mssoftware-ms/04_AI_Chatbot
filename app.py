"""Main application entry point for WhatsApp AI Chatbot."""

import asyncio
import sys
from pathlib import Path
import logging
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging_config import setup_logging
from config.settings import settings

# Set up logging
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


async def start_backend():
    """Start the FastAPI backend server."""
    import uvicorn
    from src.main import app
    
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
    server = uvicorn.Server(config)
    await server.serve()


def start_ui():
    """Start the Flet UI application."""
    import flet as ft
    from src.ui.chat_app import ChatApp
    
    def main(page: ft.Page):
        try:
            app = ChatApp()
            app.main(page)
        except Exception as e:
            logger.error(f"UI error: {e}")
    
    try:
        # WSL fix: Don't try to open Windows browser from WSL thread
        logger.info(f"🌐 UI will be available at: http://localhost:{settings.ui_port}")
        logger.info("💡 Open this URL manually in Windows browser if running in WSL")
        
        ft.app(
            target=main,
            port=settings.ui_port,
            view=None,  # Don't auto-open browser (fixes WSL issues)
            assets_dir="assets"
        )
    except ValueError as e:
        if "signal only works in main thread" in str(e):
            logger.warning("🔧 WSL detected - UI started without signal handling")
            ft.app(
                target=main,
                port=settings.ui_port,
                view=None,
                assets_dir="assets"
            )
        else:
            raise


async def main():
    """Main application entry point."""
    
    logger.info("=" * 60)
    logger.info("🚀 WhatsApp AI Chatbot Starting...")
    logger.info("=" * 60)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "backend":
            logger.info("Starting backend server only...")
            await start_backend()
            
        elif mode == "ui":
            logger.info("Starting UI only...")
            logger.info(f"UI will be available at: http://localhost:{settings.ui_port}")
            start_ui()
            
        elif mode == "test":
            logger.info("Running tests...")
            import pytest
            pytest.main(["-v", "tests/"])
            
        else:
            logger.error(f"Unknown mode: {mode}")
            print("\nUsage:")
            print("  python app.py          # Start both backend and UI")
            print("  python app.py backend  # Start backend only")
            print("  python app.py ui       # Start UI only")
            print("  python app.py test     # Run tests")
            sys.exit(1)
    else:
        # Start both backend and UI
        logger.info("Starting full application (backend + UI)...")
        
        # Create tasks for both services
        backend_task = asyncio.create_task(start_backend())
        
        # Start UI in a separate thread (Flet requirement)
        import threading
        ui_thread = threading.Thread(target=start_ui, daemon=True)
        ui_thread.start()
        
        # Wait for backend
        try:
            await backend_task
        except KeyboardInterrupt:
            logger.info("Shutting down...")


if __name__ == "__main__":
    try:
        # Run the main application
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
        sys.exit(1)