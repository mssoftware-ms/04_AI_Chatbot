#!/usr/bin/env python3
"""
Enhanced launcher for WhatsApp AI Chatbot with multiple interface options.
Supports both web-based (Flet) and native GUI (Tkinter) interfaces.
"""

import asyncio
import sys
import os
import platform
import subprocess
import threading
import time
from pathlib import Path

# Configure logging
import logging
from src.config.logging_config import setup_logging

# Setup logging
logger = setup_logging()

def show_launcher_menu():
    """Show the launcher menu with interface options."""
    print("\n" + "="*60)
    print("        🚀 WhatsApp AI Chatbot - Enhanced Launcher")
    print("="*60)
    print(f"💻 Platform: {platform.system()} ({platform.machine()})")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📂 Working Dir: {os.getcwd()}")
    print("\n📋 Available Interface Options:")
    print("-" * 40)
    print("1. 🌐 Web Interface (Flet) - Recommended")
    print("   └─ Modern web-based UI with advanced features")
    print("   └─ URL: http://localhost:8550")
    print()
    print("2. 🖥️  Native GUI (Tkinter) - Standalone")  
    print("   └─ Traditional desktop application")
    print("   └─ No browser required")
    print()
    print("3. 🔀 Both Interfaces (Parallel)")
    print("   └─ Run both web and native simultaneously")
    print("   └─ Best of both worlds")
    print()
    print("4. 🛠️  Backend Only")
    print("   └─ Start only the API server")
    print("   └─ URL: http://localhost:8000")
    print()
    print("5. ❌ Exit")
    print("-" * 40)


def start_backend():
    """Start the backend API server."""
    logger.info("🚀 Starting backend API server...")
    
    try:
        # Import and start backend
        from src.main import create_app
        import uvicorn
        
        app = create_app()
        
        # Start backend in a separate thread
        def run_backend():
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
        
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Wait for backend to be ready
        time.sleep(3)
        logger.info("✅ Backend API ready at http://localhost:8000")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to start backend: {e}")
        return False


async def start_web_interface():
    """Start the web-based Flet interface."""
    logger.info("🌐 Starting web interface (Flet)...")
    
    try:
        import flet as ft
        from src.ui.chat_app import ChatApp
        
        async def main(page: ft.Page):
            """Main Flet app entry point."""
            try:
                app = ChatApp()
                await app.main(page)
            except Exception as e:
                logger.error(f"❌ Web UI error: {e}")
                page.add(ft.Text(f"UI Error: {e}", color="red"))
        
        # Start Flet app
        await ft.app_async(
            target=main,
            port=8550,
            web_renderer=ft.WebRenderer.CANVAS_KIT
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start web interface: {e}")


def start_native_interface():
    """Start the native Tkinter interface."""
    logger.info("🖥️  Starting native GUI interface...")
    
    try:
        from src.ui.native_chat_app import NativeChatApp
        
        app = NativeChatApp()
        app.run()
        
    except Exception as e:
        logger.error(f"❌ Failed to start native interface: {e}")


def start_both_interfaces():
    """Start both web and native interfaces."""
    logger.info("🔀 Starting both interfaces...")
    
    # Start web interface in a separate process
    def start_web_process():
        try:
            import asyncio
            asyncio.run(start_web_interface())
        except Exception as e:
            logger.error(f"❌ Web interface error: {e}")
    
    web_thread = threading.Thread(target=start_web_process, daemon=True)
    web_thread.start()
    
    # Wait a moment for web interface to start
    time.sleep(2)
    
    # Start native interface (blocking)
    start_native_interface()


def check_requirements():
    """Check if all requirements are met."""
    logger.info("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ required")
        return False
    
    # Check required packages
    required_packages = ['flet', 'fastapi', 'uvicorn', 'requests', 'websockets']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
        logger.info("💡 Install with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All requirements met")
    return True


def main():
    """Main launcher function."""
    try:
        # Check requirements
        if not check_requirements():
            input("Press Enter to exit...")
            return
        
        # Show menu and get user choice
        while True:
            show_launcher_menu()
            
            try:
                choice = input("\\n🎯 Select option (1-5): ").strip()
                
                if choice == "1":
                    # Web interface
                    print("\\n🌐 Starting Web Interface...")
                    
                    # Start backend
                    if not start_backend():
                        input("Press Enter to continue...")
                        continue
                    
                    # Start web interface
                    try:
                        asyncio.run(start_web_interface())
                    except KeyboardInterrupt:
                        logger.info("\\n👋 Web interface stopped by user")
                    
                elif choice == "2":
                    # Native interface
                    print("\\n🖥️  Starting Native GUI...")
                    
                    # Start backend
                    if not start_backend():
                        input("Press Enter to continue...")
                        continue
                    
                    # Start native interface
                    try:
                        start_native_interface()
                    except KeyboardInterrupt:
                        logger.info("\\n👋 Native interface stopped by user")
                
                elif choice == "3":
                    # Both interfaces
                    print("\\n🔀 Starting Both Interfaces...")
                    
                    # Start backend
                    if not start_backend():
                        input("Press Enter to continue...")
                        continue
                    
                    # Start both interfaces
                    try:
                        start_both_interfaces()
                    except KeyboardInterrupt:
                        logger.info("\\n👋 Both interfaces stopped by user")
                
                elif choice == "4":
                    # Backend only
                    print("\\n🛠️  Starting Backend Only...")
                    
                    if start_backend():
                        logger.info("🌐 Backend running at http://localhost:8000")
                        logger.info("📖 API Documentation: http://localhost:8000/docs")
                        logger.info("\\n💡 Press Ctrl+C to stop")
                        
                        try:
                            # Keep backend running
                            while True:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            logger.info("\\n👋 Backend stopped by user")
                    else:
                        input("Press Enter to continue...")
                        continue
                
                elif choice == "5":
                    # Exit
                    print("\\n👋 Goodbye!")
                    break
                
                else:
                    print("\\n❌ Invalid choice. Please select 1-5.")
                    time.sleep(1)
                    continue
                
                # Ask if user wants to restart
                print("\\n" + "="*60)
                restart = input("🔄 Return to menu? (y/n): ").strip().lower()
                if restart != 'y':
                    break
                    
            except KeyboardInterrupt:
                print("\\n\\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                input("Press Enter to continue...")
                continue
    
    except Exception as e:
        logger.error(f"❌ Launcher error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()