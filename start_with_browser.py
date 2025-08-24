#!/usr/bin/env python3
"""
WhatsApp AI Chatbot launcher with WSL browser support.
Automatically detects and uses available browsers.
"""

import asyncio
import sys
import os
import subprocess
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


def find_browser():
    """Find available browser in WSL."""
    browsers = ['google-chrome', 'chromium-browser', 'chromium', 'firefox']
    
    for browser in browsers:
        try:
            result = subprocess.run(['which', browser], capture_output=True, text=True)
            if result.returncode == 0:
                return browser.strip()
        except:
            continue
    return None


def has_display():
    """Check if display is available."""
    return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))


def start_ui_with_browser():
    """Start Flet UI with automatic browser detection."""
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
        
        # Detect environment
        wsl_detected = is_wsl()
        browser = find_browser()
        display_available = has_display()
        
        logger.info(f"🐧 WSL detected: {wsl_detected}")
        logger.info(f"🌐 Browser found: {browser or 'None'}")
        logger.info(f"🖥️  Display available: {display_available}")
        
        # Determine view mode
        if browser and display_available:
            logger.info(f"🚀 Using native WSL browser: {browser}")
            view_mode = ft.WEB_BROWSER
        else:
            logger.info("📝 Manual browser open required")
            logger.info(f"🌐 Open in browser: http://localhost:{settings.ui_port}")
            view_mode = None
        
        # Start Flet
        ft.app(
            target=main,
            port=settings.ui_port,
            view=view_mode,
            assets_dir="assets"
        )
            
    except Exception as e:
        logger.error(f"UI startup failed: {e}")
        logger.info(f"💡 Manual access: http://localhost:{settings.ui_port}")


async def start_backend():
    """Start FastAPI backend."""
    try:
        import uvicorn
        from src.main import app
        
        logger.info(f"🚀 Starting backend on {settings.host}:{settings.port}")
        
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level=settings.log_level.lower()
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Backend error: {e}")
        raise


def show_status():
    """Show system status and URLs."""
    wsl = is_wsl()
    browser = find_browser()
    display = has_display()
    
    print("\n" + "="*60)
    print("🎉 WhatsApp AI Chatbot - System Status")
    print("="*60)
    print(f"🐧 WSL Environment: {'Yes' if wsl else 'No'}")
    print(f"🌐 Browser Available: {browser or 'None found'}")
    print(f"🖥️  Display Support: {'Yes' if display else 'No'}")
    print()
    print("📍 Available URLs:")
    print(f"   🚀 Backend API: http://localhost:{settings.port}")
    print(f"   📖 API Docs: http://localhost:{settings.port}/docs")
    print(f"   🖥️  UI App: http://localhost:{settings.ui_port}")
    
    if not browser or not display:
        print()
        print("💡 Browser Installation:")
        print("   Run: ./install_wsl_browser.sh")
        print("   Or manually: sudo apt install chromium-browser")
    
    print("="*60)


def main():
    """Main entry point."""
    logger.info("🚀 WhatsApp AI Chatbot - Enhanced WSL Support")
    
    show_status()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "backend":
            logger.info("🔧 Starting backend only...")
            asyncio.run(start_backend())
            
        elif mode == "ui":
            logger.info("🖥️  Starting UI only...")
            start_ui_with_browser()
            
        elif mode == "install-browser":
            logger.info("🌐 Installing browser...")
            os.system("./install_wsl_browser.sh")
            return
            
        elif mode == "test":
            logger.info("🧪 Running tests...")
            import pytest
            pytest.main(["-v", "tests/"])
            
        else:
            print("\nUsage:")
            print("  python start_with_browser.py backend         # Backend only")
            print("  python start_with_browser.py ui              # UI only")
            print("  python start_with_browser.py install-browser # Install WSL browser")
            print("  python start_with_browser.py test            # Run tests")
            print("  python start_with_browser.py                 # Full app (default)")
            
    else:
        # Default: start full application
        logger.info("🚀 Starting full application...")
        
        # Start backend in background
        backend_thread = threading.Thread(
            target=lambda: asyncio.run(start_backend()),
            daemon=True
        )
        backend_thread.start()
        
        # Wait for backend
        time.sleep(2)
        
        if backend_thread.is_alive():
            logger.info("✅ Backend ready")
            
            # Start UI
            logger.info("🖥️  Starting UI...")
            start_ui_with_browser()
        else:
            logger.error("❌ Backend failed")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)