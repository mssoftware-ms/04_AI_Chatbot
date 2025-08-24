#!/usr/bin/env python3
"""
Windows-native WhatsApp AI Chatbot launcher.
Optimized for Windows CMD/PowerShell execution.
"""

import asyncio
import sys
import os
import subprocess
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


def is_windows():
    """Detect if running on Windows."""
    return os.name == 'nt' or sys.platform.startswith('win')


def find_browser_windows():
    """Find available browser on Windows."""
    browsers = [
        'chrome.exe',
        'msedge.exe', 
        'firefox.exe',
        'iexplore.exe'
    ]
    
    # Check common installation paths
    common_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Check PATH
    for browser in browsers:
        try:
            result = subprocess.run(['where', browser], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            continue
    
    return None


def open_browser_windows(url):
    """Open browser on Windows."""
    try:
        # Try default browser first
        webbrowser.open(url)
        return True
    except:
        # Fallback to manual browser detection
        browser = find_browser_windows()
        if browser:
            try:
                subprocess.Popen([browser, url])
                return True
            except:
                pass
    return False


def start_ui_windows():
    """Start Flet UI optimized for Windows."""
    try:
        import flet as ft
        from src.ui.chat_app import ChatApp
        
        async def main(page: ft.Page):
            try:
                app = ChatApp()
                await app.main(page)
            except Exception as e:
                logger.error(f"ChatApp error: {e}")
                page.add(ft.Text(f"UI Error: {e}", color="red"))
        
        if is_windows():
            logger.info("🖥️  Windows environment detected")
            logger.info(f"🌐 Starting UI server on Windows...")
            logger.info(f"📝 URL: http://localhost:{settings.ui_port}")
            
            # Windows-optimized settings
            ft.app(
                target=main,
                port=settings.ui_port,
                host="127.0.0.1",  # Windows localhost
                view=ft.WEB_BROWSER,  # Auto-open browser
                assets_dir="assets",
                web_renderer="canvaskit"  # Better performance
            )
        else:
            logger.info("🐧 Non-Windows environment")
            ft.app(
                target=main,
                port=settings.ui_port,
                view=None,
                assets_dir="assets"
            )
            
    except Exception as e:
        logger.error(f"UI startup failed: {e}")
        logger.info(f"💡 Manual access: http://localhost:{settings.ui_port}")


async def start_backend_windows():
    """Start FastAPI backend for Windows."""
    try:
        import uvicorn
        from src.main import app
        
        logger.info(f"🚀 Starting Windows backend on {settings.host}:{settings.port}")
        
        config = uvicorn.Config(
            app,
            host="127.0.0.1",  # Windows localhost
            port=settings.port,
            reload=False,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Backend error: {e}")
        raise


def show_windows_status():
    """Show Windows-optimized status."""
    browser = find_browser_windows()
    
    print("\n" + "="*60)
    print("🖥️  WhatsApp AI Chatbot - Windows Edition")
    print("="*60)
    print(f"💻 Platform: Windows ({os.name})")
    print(f"🌐 Browser: {browser.split('\\')[-1] if browser else 'Default browser'}")
    print(f"📂 Working Dir: {os.getcwd()}")
    print()
    print("📍 Application URLs:")
    print(f"   🚀 Backend API: http://localhost:{settings.port}")
    print(f"   📖 API Docs: http://localhost:{settings.port}/docs") 
    print(f"   🖥️  UI App: http://localhost:{settings.ui_port}")
    print()
    print("🎯 Browser will open automatically!")
    print("="*60)


def start_full_windows():
    """Start full application on Windows."""
    logger.info("🖥️  Starting Windows full application...")
    
    show_windows_status()
    
    # Start backend in background thread
    backend_thread = threading.Thread(
        target=lambda: asyncio.run(start_backend_windows()),
        daemon=True
    )
    backend_thread.start()
    
    # Wait for backend
    logger.info("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    if backend_thread.is_alive():
        logger.info("✅ Backend ready")
        
        # Open browser manually if needed
        url = f"http://localhost:{settings.ui_port}"
        if open_browser_windows(url):
            logger.info(f"🌐 Browser opening: {url}")
        
        # Start UI (will also open browser)
        logger.info("🖥️  Starting UI server...")
        start_ui_windows()
    else:
        logger.error("❌ Backend failed to start")
        sys.exit(1)


def main():
    """Main entry point for Windows."""
    
    if not is_windows():
        print("⚠️  This launcher is optimized for Windows!")
        print("💡 For WSL/Linux, use: python start_with_browser.py")
        print("🤔 Continue anyway? (y/n)")
        if input().lower() != 'y':
            sys.exit(0)
    
    logger.info("🖥️  WhatsApp AI Chatbot - Windows Launcher")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "backend":
            logger.info("🔧 Starting backend only...")
            asyncio.run(start_backend_windows())
            
        elif mode == "ui":
            logger.info("🖥️  Starting UI only...")
            start_ui_windows()
            
        elif mode == "test":
            logger.info("🧪 Running tests...")
            import pytest
            pytest.main(["-v", "tests/"])
            
        elif mode == "browser-test":
            logger.info("🌐 Testing browser detection...")
            browser = find_browser_windows()
            print(f"Found browser: {browser}")
            if browser:
                test_url = "http://localhost:8550"
                print(f"Testing browser open: {test_url}")
                open_browser_windows(test_url)
            
        else:
            print("\nWindows Usage:")
            print("  python start_windows.py                # Full app (recommended)")
            print("  python start_windows.py backend        # Backend only")
            print("  python start_windows.py ui             # UI only") 
            print("  python start_windows.py browser-test   # Test browser detection")
            print("  python start_windows.py test           # Run tests")
            
    else:
        # Default: start full application
        start_full_windows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        input("Press Enter to exit...")
        sys.exit(1)