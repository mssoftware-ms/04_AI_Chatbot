#!/usr/bin/env python
"""Demo startup script for WhatsApp AI Chatbot - runs with minimal dependencies."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Check which dependencies are available."""
    available = []
    missing = []
    
    deps = {
        "FastAPI": "fastapi",
        "Uvicorn": "uvicorn",
        "Flet": "flet",
        "SQLAlchemy": "sqlalchemy",
        "Pydantic": "pydantic",
        "ChromaDB": "chromadb",
        "OpenAI": "openai"
    }
    
    for name, module in deps.items():
        try:
            __import__(module)
            available.append(name)
        except ImportError:
            missing.append(name)
    
    return available, missing


def start_minimal_api():
    """Start minimal API server without all dependencies."""
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="WhatsApp AI Chatbot - Demo")
    
    @app.get("/")
    async def root():
        return {
            "message": "WhatsApp AI Chatbot API - Demo Mode",
            "status": "running",
            "endpoints": [
                "/health",
                "/api/projects",
                "/api/conversations", 
                "/api/messages"
            ]
        }
    
    @app.get("/health")
    async def health():
        available, missing = check_dependencies()
        return {
            "status": "healthy",
            "mode": "demo",
            "available_modules": available,
            "missing_modules": missing
        }
    
    @app.get("/api/projects")
    async def get_projects():
        return {
            "projects": [
                {"id": 1, "name": "Demo Project", "description": "A demo project for testing"}
            ]
        }
    
    @app.get("/api/conversations")
    async def get_conversations():
        return {
            "conversations": [
                {"id": 1, "project_id": 1, "title": "Demo Conversation"}
            ]
        }
    
    @app.get("/api/messages")
    async def get_messages():
        return {
            "messages": [
                {
                    "id": 1, 
                    "conversation_id": 1,
                    "role": "assistant",
                    "content": "Welcome to WhatsApp AI Chatbot! This is a demo message."
                },
                {
                    "id": 2,
                    "conversation_id": 1, 
                    "role": "user",
                    "content": "Hello! How can I test the chatbot?"
                },
                {
                    "id": 3,
                    "conversation_id": 1,
                    "role": "assistant",
                    "content": "You can test the chatbot by:\n1. Installing all dependencies\n2. Adding your OpenAI API key to .env\n3. Running: python app.py"
                }
            ]
        }
    
    print("\n" + "="*60)
    print("🚀 WhatsApp AI Chatbot - Demo Mode")
    print("="*60)
    print("\n📝 API running at: http://localhost:8000")
    print("📋 API docs at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("\n⚠️  Note: This is a demo mode with limited functionality")
    print("💡 To run full application, install all dependencies and run: python app.py")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


def start_minimal_ui():
    """Start minimal UI without all dependencies."""
    try:
        import flet as ft
        
        def main(page: ft.Page):
            page.title = "WhatsApp AI Chatbot - Demo"
            page.window_width = 1200
            page.window_height = 800
            
            # Header
            header = ft.Container(
                content=ft.Text(
                    "🤖 WhatsApp AI Chatbot - Demo Mode",
                    size=24,
                    weight="bold"
                ),
                padding=20,
                bgcolor=ft.colors.GREEN_700
            )
            
            # Status info
            available, missing = check_dependencies()
            
            missing_widgets = [ft.Text(f"  • {mod}", size=14) for mod in missing] if missing else [ft.Text("  All modules installed!", size=14, color=ft.colors.GREEN)]
            
            status_text = ft.Column([
                ft.Text("✅ Available Modules:", size=16, weight="bold"),
                *[ft.Text(f"  • {mod}", size=14) for mod in available],
                ft.Text("\n❌ Missing Modules:", size=16, weight="bold"),
                *missing_widgets
            ])
            
            # Demo chat
            messages = ft.ListView(
                expand=True,
                spacing=10,
                padding=ft.padding.all(10)
            )
            
            demo_messages = [
                ("assistant", "Welcome to WhatsApp AI Chatbot! 👋"),
                ("user", "How do I get started?"),
                ("assistant", "To get started:\n1. Install dependencies: pip install -r requirements.txt\n2. Add your OpenAI API key to .env\n3. Run: python app.py"),
                ("user", "What features are available?"),
                ("assistant", "Features include:\n• Multi-project support\n• RAG with document indexing\n• Real-time chat via WebSocket\n• File watching for auto-indexing\n• WhatsApp-like UI\n• And more!")
            ]
            
            for role, content in demo_messages:
                bubble = ft.Container(
                    content=ft.Text(content, selectable=True),
                    bgcolor=ft.colors.GREEN_200 if role == "user" else ft.colors.GREY_200,
                    border_radius=15,
                    padding=10,
                    margin=ft.margin.only(
                        left=100 if role == "user" else 0,
                        right=100 if role != "user" else 0
                    )
                )
                messages.controls.append(bubble)
            
            # Input area
            message_input = ft.TextField(
                hint_text="Type a message (demo mode - not functional)",
                expand=True,
                disabled=True
            )
            
            input_row = ft.Row([
                message_input,
                ft.IconButton(
                    icon=ft.icons.SEND,
                    bgcolor=ft.colors.GREEN_700,
                    icon_color=ft.colors.WHITE,
                    disabled=True
                )
            ])
            
            # Layout
            page.add(
                header,
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=status_text,
                            width=300,
                            padding=20,
                            bgcolor=ft.colors.GREY_100
                        ),
                        ft.VerticalDivider(width=1),
                        ft.Container(
                            content=ft.Column([
                                messages,
                                ft.Divider(height=1),
                                ft.Container(
                                    content=input_row,
                                    padding=10
                                )
                            ]),
                            expand=True
                        )
                    ], expand=True),
                    expand=True
                )
            )
        
        print("\n" + "="*60)
        print("🚀 WhatsApp AI Chatbot - UI Demo")
        print("="*60)
        print("\n🌐 Opening UI in browser...")
        print("⚠️  Note: This is a demo UI with limited functionality")
        print("💡 To run full application, install all dependencies")
        print("\nPress Ctrl+C to stop")
        print("="*60 + "\n")
        
        ft.app(target=main, port=8550, view=ft.WEB_BROWSER)
        
    except ImportError:
        print("❌ Flet is not installed. Install with: pip install flet")


def main():
    """Main entry point."""
    
    print("\n" + "="*60)
    print("🤖 WhatsApp AI Chatbot - Demo Launcher")
    print("="*60)
    
    available, missing = check_dependencies()
    
    print("\n📦 Dependency Check:")
    print(f"✅ Available: {', '.join(available) if available else 'None'}")
    print(f"❌ Missing: {', '.join(missing) if missing else 'None'}")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "api":
            if "FastAPI" in available and "Uvicorn" in available:
                start_minimal_api()
            else:
                print("\n❌ FastAPI or Uvicorn not installed")
                print("Install with: pip install fastapi uvicorn")
                
        elif mode == "ui":
            if "Flet" in available:
                start_minimal_ui()
            else:
                print("\n❌ Flet not installed")
                print("Install with: pip install flet")
                
        else:
            print(f"\n❌ Unknown mode: {mode}")
            print("\nUsage:")
            print("  python start_demo.py         # Show this help")
            print("  python start_demo.py api     # Start demo API")
            print("  python start_demo.py ui      # Start demo UI")
            
    else:
        print("\n📝 Usage:")
        print("  python start_demo.py api     # Start demo API server")
        print("  python start_demo.py ui      # Start demo UI")
        print("\n💡 To run the full application:")
        print("  1. Install all dependencies: pip install -r requirements.txt")
        print("  2. Set up your .env file with API keys")
        print("  3. Run: python app.py")
        
        if "FastAPI" in available and "Uvicorn" in available:
            print("\n✅ You can run the demo API: python start_demo.py api")
        if "Flet" in available:
            print("✅ You can run the demo UI: python start_demo.py ui")
    
    print("="*60)


if __name__ == "__main__":
    main()