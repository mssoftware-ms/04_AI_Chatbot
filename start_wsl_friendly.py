#!/usr/bin/env python3
"""
WSL-Friendly WhatsApp AI Chatbot launcher.
This version is optimized for WSL + Windows browser combination.
"""

import asyncio
import sys
import os
import threading
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logging_config import setup_logging
from config.settings import settings

# Set up logging
setup_logging(settings.log_level)
import logging
logger = logging.getLogger(__name__)


def is_wsl():
    """Detect if running in WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False


def start_ui_wsl_safe():
    """Start Flet UI with WSL compatibility."""
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
        
        wsl_detected = is_wsl()
        if wsl_detected:
            logger.info("🐧 WSL environment detected")
            logger.info("🌐 Starting UI server (manual browser open required)")
            logger.info(f"📝 Open this URL in Windows browser: http://localhost:{settings.ui_port}")
            
            # WSL-safe approach: no browser auto-open, no signal handling
            ft.app(
                target=main,
                port=settings.ui_port,
                view=None,  # Never auto-open browser in WSL
                assets_dir="assets"
            )
        else:
            logger.info("🖥️  Native environment detected")
            logger.info(f"🌐 Opening browser automatically: http://localhost:{settings.ui_port}")
            
            ft.app(
                target=main,
                port=settings.ui_port,
                view=ft.WEB_BROWSER,
                assets_dir="assets"
            )
            
    except Exception as e:
        logger.error(f"UI startup failed: {e}")
        logger.info("💡 Manual access available at: http://localhost:{settings.ui_port}")


async def start_backend_safe():
    """Start FastAPI backend."""
    try:
        import uvicorn
        from src.main import app
        
        logger.info(f"🚀 Starting backend on {settings.host}:{settings.port}")
        
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,  # Disable reload in WSL
            log_level=settings.log_level.lower()
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Backend error: {e}")
        raise


def show_urls():
    """Show all available URLs."""
    wsl_note = " (WSL detected - open manually in Windows browser)" if is_wsl() else ""
    
    print("\n" + "="*60)
    print("🎉 WhatsApp AI Chatbot - Ready!")
    print("="*60)
    print(f"🌐 Backend API: http://localhost:{settings.port}{wsl_note}")
    print(f"📖 API Docs: http://localhost:{settings.port}/docs{wsl_note}")
    print(f"🖥️  UI App: http://localhost:{settings.ui_port}{wsl_note}")
    if is_wsl():
        print("\n💡 WSL Tip: Copy URLs to Windows browser")
    print("="*60)


def start_backend_only():
    """Start only backend server."""
    logger.info("🚀 WhatsApp AI Chatbot - Backend Only")
    asyncio.run(start_backend_safe())


def start_ui_only():
    """Start only UI server.""" 
    logger.info("🖥️  WhatsApp AI Chatbot - UI Only")
    logger.info("⚠️  Note: Make sure backend is running separately!")
    start_ui_wsl_safe()


def start_full_app():
    """Start both backend and UI with WSL support."""
    logger.info("🚀 WhatsApp AI Chatbot - Full Application")
    
    if is_wsl():
        logger.info("🐧 WSL environment detected - using WSL-optimized startup")
    
    # Start backend in background
    backend_thread = threading.Thread(
        target=lambda: asyncio.run(start_backend_safe()),
        daemon=True
    )
    backend_thread.start()
    
    # Wait for backend
    time.sleep(2)
    
    if backend_thread.is_alive():
        logger.info("✅ Backend started successfully")
        show_urls()
        
        # Start UI (WSL-safe)
        logger.info("🖥️  Starting UI server...")
        start_ui_wsl_safe()
    else:
        logger.error("❌ Backend failed to start")
        sys.exit(1)


def main():
    """Main entry point with WSL detection."""
    
    # Show environment info
    if is_wsl():
        logger.info("🐧 Running in WSL environment")
        logger.info("💡 Browser will need to be opened manually in Windows")
    else:
        logger.info("🖥️  Running in native environment")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "backend":
            start_backend_only()
        elif mode == "ui":
            start_ui_only() 
        elif mode == "full":
            start_full_app()
        elif mode == "test":
            logger.info("🧪 Running tests...")
            import pytest
            pytest.main(["-v", "tests/"])
        else:
            print("\nUsage:")
            print("  python start_wsl_friendly.py backend  # Backend only")
            print("  python start_wsl_friendly.py ui       # UI only") 
            print("  python start_wsl_friendly.py full     # Both (recommended)")
            print("  python start_wsl_friendly.py test     # Run tests")
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