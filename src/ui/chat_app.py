"""
Main WhatsApp-like chat application using Flet.
Provides a complete three-panel chat interface.
"""

import asyncio
import flet as ft
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os

from .components.sidebar import Sidebar
from .components.chat_area import ChatArea
from .components.input_area import InputArea
from .websocket_client import WebSocketClient


class ChatApp:
    """Main chat application with WhatsApp-like interface."""
    
    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.sidebar: Optional[Sidebar] = None
        self.chat_area: Optional[ChatArea] = None
        self.input_area: Optional[InputArea] = None
        self.websocket_client: Optional[WebSocketClient] = None
        
        # Application state
        self.current_project_id: Optional[str] = None
        self.current_conversation_id: Optional[str] = None
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        
        # Theme colors (WhatsApp-like)
        self.colors = {
            "primary": "#00a884",
            "primary_dark": "#008f72",
            "background": "#111b21",
            "sidebar": "#202c33",
            "chat": "#0b141a",
            "bubble_sent": "#005c4b",
            "bubble_received": "#202c33",
            "text_primary": "#e9edef",
            "text_secondary": "#8696a0",
            "border": "#313d45",
            "hover": "#2a3942"
        }
    
    async def main(self, page: ft.Page):
        """Main application entry point."""
        self.page = page
        await self.setup_page()
        await self.setup_components()
        await self.setup_layout()
        await self.connect_websocket()
        await self.load_initial_data()
    
    async def setup_page(self):
        """Configure the main page."""
        self.page.title = "AI Chatbot - WhatsApp Style"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = self.colors["background"]
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 800
        self.page.window_min_height = 600
        self.page.padding = 0
        self.page.spacing = 0
        
        # Custom theme
        self.page.theme = ft.Theme(
            color_scheme_seed=self.colors["primary"],
            use_material3=True
        )
    
    async def setup_components(self):
        """Initialize all UI components."""
        self.sidebar = Sidebar(
            colors=self.colors,
            on_project_select=self.on_project_select,
            on_conversation_select=self.on_conversation_select,
            on_new_project=self.on_new_project,
            on_new_conversation=self.on_new_conversation
        )
        
        self.chat_area = ChatArea(
            colors=self.colors,
            on_scroll_top=self.on_load_more_messages
        )
        
        self.input_area = InputArea(
            colors=self.colors,
            on_send_message=self.on_send_message,
            on_file_attach=self.on_file_attach,
            page=self.page
        )
    
    async def setup_layout(self):
        """Setup the main three-panel layout."""
        # Main container with three panels
        main_row = ft.Row(
            controls=[
                # Sidebar (left panel)
                ft.Container(
                    content=self.sidebar.build(),
                    width=320,
                    bgcolor=self.colors["sidebar"],
                    border=ft.border.only(right=ft.BorderSide(1, self.colors["border"])),
                    expand=False
                ),
                # Chat area (center panel)
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Chat header
                            await self.create_chat_header(),
                            # Chat messages
                            ft.Container(
                                content=self.chat_area.build(),
                                expand=True,
                                bgcolor=self.colors["chat"]
                            ),
                            # Input area
                            ft.Container(
                                content=self.input_area.build(),
                                bgcolor=self.colors["sidebar"],
                                border=ft.border.only(top=ft.BorderSide(1, self.colors["border"])),
                                padding=ft.padding.all(10)
                            )
                        ],
                        spacing=0,
                        expand=True
                    ),
                    expand=True,
                    bgcolor=self.colors["chat"]
                )
            ],
            spacing=0,
            expand=True
        )
        
        self.page.add(main_row)
        self.page.update()
    
    async def create_chat_header(self) -> ft.Container:
        """Create the chat area header."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.WHITE),
                                bgcolor=self.colors["primary"],
                                radius=20
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "AI Assistant",
                                        color=self.colors["text_primary"],
                                        size=16,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "Online",
                                        color=self.colors["text_secondary"],
                                        size=12
                                    )
                                ],
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER
                            )
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.SEARCH,
                                icon_color=self.colors["text_secondary"],
                                tooltip="Search messages",
                                on_click=self.on_search_messages
                            ),
                            ft.IconButton(
                                icon=ft.Icons.MORE_VERT,
                                icon_color=self.colors["text_secondary"],
                                tooltip="More options",
                                on_click=self.on_chat_options
                            )
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=self.colors["sidebar"],
            border=ft.border.only(bottom=ft.BorderSide(1, self.colors["border"])),
            padding=ft.padding.all(15),
            height=70
        )
    
    async def connect_websocket(self):
        """Connect to WebSocket server for real-time updates."""
        try:
            self.websocket_client = WebSocketClient(
                url="ws://localhost:8000/ws",
                on_message=self.on_websocket_message,
                on_typing=self.on_typing_indicator,
                on_status_change=self.on_connection_status_change
            )
            await self.websocket_client.connect()
        except Exception as e:
            print(f"Failed to connect to WebSocket: {e}")
            # Continue without WebSocket - offline mode
    
    async def load_initial_data(self):
        """Load initial projects and conversations."""
        # Load from local storage or API
        try:
            # For now, create some sample data
            sample_project = {
                "id": "default",
                "name": "General Chat",
                "description": "General AI conversations",
                "created_at": datetime.now().isoformat(),
                "conversations": ["conv_1"]
            }
            
            self.projects["default"] = sample_project
            self.conversations["conv_1"] = []
            
            await self.sidebar.update_projects(self.projects)
            await self.on_project_select("default")
            
        except Exception as e:
            print(f"Failed to load initial data: {e}")
    
    # Event handlers
    async def on_project_select(self, project_id: str):
        """Handle project selection."""
        self.current_project_id = project_id
        project = self.projects.get(project_id)
        
        if project and project.get("conversations"):
            # Load first conversation or create new one
            conv_id = project["conversations"][0]
            await self.on_conversation_select(conv_id)
        else:
            # Create new conversation for empty project
            await self.on_new_conversation()
    
    async def on_conversation_select(self, conversation_id: str):
        """Handle conversation selection."""
        self.current_conversation_id = conversation_id
        messages = self.conversations.get(conversation_id, [])
        await self.chat_area.load_messages(messages)
        await self.input_area.enable()
    
    async def on_new_project(self, name: str, description: str = ""):
        """Handle new project creation."""
        project_id = f"proj_{len(self.projects) + 1}"
        project = {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "conversations": []
        }
        
        self.projects[project_id] = project
        await self.sidebar.update_projects(self.projects)
        await self.on_project_select(project_id)
    
    async def on_new_conversation(self):
        """Handle new conversation creation."""
        if not self.current_project_id:
            return
        
        conv_id = f"conv_{len(self.conversations) + 1}"
        self.conversations[conv_id] = []
        
        # Add to current project
        project = self.projects[self.current_project_id]
        project["conversations"].append(conv_id)
        
        await self.sidebar.update_projects(self.projects)
        await self.on_conversation_select(conv_id)
    
    async def on_send_message(self, message_text: str, attachments: Optional[List[str]] = None):
        """Handle sending a new message."""
        if not self.current_conversation_id or not message_text.strip():
            return
        
        # Create user message
        user_message = {
            "id": f"msg_{datetime.now().timestamp()}",
            "type": "user",
            "content": message_text.strip(),
            "timestamp": datetime.now().isoformat(),
            "status": "sent",
            "attachments": attachments or []
        }
        
        # Add to conversation
        self.conversations[self.current_conversation_id].append(user_message)
        await self.chat_area.add_message(user_message)
        
        # Show typing indicator
        await self.chat_area.show_typing_indicator()
        
        # Send to AI via WebSocket or API
        if self.websocket_client and self.websocket_client.connected:
            await self.websocket_client.send_message({
                "type": "user_message",
                "conversation_id": self.current_conversation_id,
                "message": user_message
            })
        else:
            # Fallback to direct API call
            await self.send_to_ai_api(user_message)
    
    async def send_to_ai_api(self, message: Dict[str, Any]):
        """Send message to AI API when WebSocket is not available."""
        try:
            # Simulate AI response for now
            await asyncio.sleep(2)  # Simulate processing time
            
            ai_response = {
                "id": f"msg_{datetime.now().timestamp()}",
                "type": "assistant",
                "content": f"I received your message: '{message['content']}'. This is a demo response.",
                "timestamp": datetime.now().isoformat(),
                "status": "received",
                "sources": ["Demo Source"],
                "attachments": []
            }
            
            await self.on_ai_response(ai_response)
            
        except Exception as e:
            print(f"Failed to send message to AI: {e}")
            await self.chat_area.hide_typing_indicator()
    
    async def on_ai_response(self, response: Dict[str, Any]):
        """Handle AI response."""
        if not self.current_conversation_id:
            return
        
        # Add to conversation
        self.conversations[self.current_conversation_id].append(response)
        
        # Hide typing indicator and show message
        await self.chat_area.hide_typing_indicator()
        await self.chat_area.add_message(response)
    
    async def on_file_attach(self, file_paths: List[str]):
        """Handle file attachment."""
        # Process and upload files
        attachments = []
        for file_path in file_paths:
            # In a real implementation, upload to server and get URLs
            attachments.append({
                "name": os.path.basename(file_path),
                "path": file_path,
                "type": self.get_file_type(file_path),
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            })
        
        await self.input_area.show_attachments(attachments)
    
    def get_file_type(self, file_path: str) -> str:
        """Determine file type from extension."""
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.pdf': 'document',
            '.doc': 'document', '.docx': 'document',
            '.txt': 'text', '.md': 'text',
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.mp3': 'audio', '.wav': 'audio',
            '.mp4': 'video', '.avi': 'video'
        }
        return type_map.get(ext, 'file')
    
    async def on_load_more_messages(self):
        """Load more messages when scrolling to top."""
        if not self.current_conversation_id:
            return
        
        # In a real implementation, load older messages from API
        print("Loading more messages...")
    
    async def on_search_messages(self, e):
        """Handle message search."""
        # Implement search functionality
        print("Search messages")
    
    async def on_chat_options(self, e):
        """Handle chat options menu."""
        # Implement options menu
        print("Chat options")
    
    # WebSocket event handlers
    async def on_websocket_message(self, message: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        msg_type = message.get("type")
        
        if msg_type == "ai_response":
            await self.on_ai_response(message.get("data"))
        elif msg_type == "typing_start":
            await self.chat_area.show_typing_indicator()
        elif msg_type == "typing_stop":
            await self.chat_area.hide_typing_indicator()
        elif msg_type == "message_status":
            # Update message status (delivered, read, etc.)
            await self.update_message_status(message.get("message_id"), message.get("status"))
    
    async def on_typing_indicator(self, is_typing: bool):
        """Handle typing indicator changes."""
        if is_typing:
            await self.chat_area.show_typing_indicator()
        else:
            await self.chat_area.hide_typing_indicator()
    
    async def on_connection_status_change(self, connected: bool):
        """Handle WebSocket connection status changes."""
        # Update UI to show connection status
        status_text = "Online" if connected else "Connecting..."
        # Update header status
        print(f"Connection status: {status_text}")
    
    async def update_message_status(self, message_id: str, status: str):
        """Update message delivery status."""
        if not self.current_conversation_id:
            return
        
        messages = self.conversations[self.current_conversation_id]
        for msg in messages:
            if msg["id"] == message_id:
                msg["status"] = status
                await self.chat_area.update_message_status(message_id, status)
                break


def run_app():
    """Run the chat application."""
    app = ChatApp()
    ft.app(target=app.main, assets_dir="assets", view=ft.WEB_BROWSER)


if __name__ == "__main__":
    run_app()