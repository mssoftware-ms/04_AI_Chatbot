"""
Sidebar component with projects and conversations list.
WhatsApp-like left panel for navigation.
"""

import flet as ft
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime


class Sidebar:
    """Projects and conversations sidebar."""
    
    def __init__(
        self,
        colors: Dict[str, str],
        on_project_select: Callable[[str], None],
        on_conversation_select: Callable[[str], None],
        on_new_project: Callable[[str, str], None],
        on_new_conversation: Callable[[], None]
    ):
        pass  # No super() needed
        self.colors = colors
        self.on_project_select = on_project_select
        self.on_conversation_select = on_conversation_select
        self.on_new_project = on_new_project
        self.on_new_conversation = on_new_conversation
        
        self.projects: Dict[str, Any] = {}
        self.current_project_id: Optional[str] = None
        self.current_conversation_id: Optional[str] = None
        
        # UI components
        self.search_field: Optional[ft.TextField] = None
        self.projects_list: Optional[ft.ListView] = None
        self.conversations_list: Optional[ft.ListView] = None
        
        # State
        self.search_query = ""
        self.show_conversations = False
    
    def build(self):
        """Build the sidebar UI."""
        # Header with search
        header = ft.Container(
            content=ft.Column(
                controls=[
                    # Top bar with menu and new chat
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.MENU,
                                icon_color=self.colors["text_secondary"],
                                tooltip="Menu",
                                on_click=self.on_menu_click
                            ),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.icons.ADD_COMMENT,
                                        icon_color=self.colors["text_secondary"],
                                        tooltip="New conversation",
                                        on_click=self.on_new_conversation_click
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.CREATE_NEW_FOLDER,
                                        icon_color=self.colors["text_secondary"],
                                        tooltip="New project",
                                        on_click=self.on_new_project_click
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.MORE_VERT,
                                        icon_color=self.colors["text_secondary"],
                                        tooltip="More options",
                                        on_click=self.on_more_options
                                    )
                                ]
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    # Search field
                    self.create_search_field()
                ],
                spacing=10
            ),
            padding=ft.padding.all(10),
            border=ft.border.only(bottom=ft.BorderSide(1, self.colors["border"]))
        )
        
        # Navigation tabs
        tabs = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Projects",
                            color=self.colors["text_primary"] if not self.show_conversations else self.colors["text_secondary"],
                            size=14,
                            weight=ft.FontWeight.BOLD if not self.show_conversations else ft.FontWeight.NORMAL
                        ),
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                        bgcolor=self.colors["primary"] if not self.show_conversations else None,
                        on_click=lambda _: self.switch_to_projects()
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Conversations",
                            color=self.colors["text_primary"] if self.show_conversations else self.colors["text_secondary"],
                            size=14,
                            weight=ft.FontWeight.BOLD if self.show_conversations else ft.FontWeight.NORMAL
                        ),
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                        bgcolor=self.colors["primary"] if self.show_conversations else None,
                        on_click=lambda _: self.switch_to_conversations()
                    )
                ],
                spacing=5
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border=ft.border.only(bottom=ft.BorderSide(1, self.colors["border"]))
        )
        
        # Lists container
        lists_container = ft.Container(
            content=ft.Column(
                controls=[
                    # Projects list
                    ft.Container(
                        content=self.create_projects_list(),
                        visible=not self.show_conversations,
                        expand=True
                    ),
                    # Conversations list
                    ft.Container(
                        content=self.create_conversations_list(),
                        visible=self.show_conversations,
                        expand=True
                    )
                ],
                expand=True
            ),
            expand=True
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[header, tabs, lists_container],
                spacing=0,
                expand=True
            ),
            width=320,
            bgcolor=self.colors["sidebar"],
            expand=True
        )
    
    def create_search_field(self) -> ft.TextField:
        """Create search input field."""
        self.search_field = ft.TextField(
            hint_text="Search projects and conversations...",
            hint_style=ft.TextStyle(color=self.colors["text_secondary"]),
            text_style=ft.TextStyle(color=self.colors["text_primary"]),
            bgcolor=self.colors["background"],
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            prefix_icon=ft.icons.SEARCH,
            border_radius=25,
            content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
            on_change=self.on_search_change
        )
        return self.search_field
    
    def create_projects_list(self) -> ft.ListView:
        """Create projects list view."""
        self.projects_list = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.padding.all(5)
        )
        return self.projects_list
    
    def create_conversations_list(self) -> ft.ListView:
        """Create conversations list view."""
        self.conversations_list = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.padding.all(5)
        )
        return self.conversations_list
    
    def create_project_item(self, project: Dict[str, Any]) -> ft.Container:
        """Create a single project list item."""
        is_selected = project["id"] == self.current_project_id
        conv_count = len(project.get("conversations", []))
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    # Project icon
                    ft.Container(
                        content=ft.Icon(
                            ft.icons.FOLDER,
                            color=self.colors["primary"] if is_selected else self.colors["text_secondary"],
                            size=20
                        ),
                        width=40,
                        height=40,
                        bgcolor=self.colors["primary"] + "20" if is_selected else None,
                        border_radius=20,
                        alignment=ft.alignment.center
                    ),
                    # Project info
                    ft.Column(
                        controls=[
                            ft.Text(
                                project["name"],
                                color=self.colors["text_primary"],
                                size=14,
                                weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"{conv_count} conversation{'s' if conv_count != 1 else ''}",
                                        color=self.colors["text_secondary"],
                                        size=12,
                                        max_lines=1
                                    ),
                                    ft.Text(
                                        self.format_date(project.get("created_at", "")),
                                        color=self.colors["text_secondary"],
                                        size=12
                                    )
                                ],
                                spacing=10
                            )
                        ],
                        spacing=2,
                        expand=True
                    ),
                    # More options
                    ft.IconButton(
                        icon=ft.icons.MORE_VERT,
                        icon_color=self.colors["text_secondary"],
                        icon_size=16,
                        tooltip="Project options",
                        on_click=lambda _: self.show_project_options(project["id"])
                    )
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            ),
            bgcolor=self.colors["hover"] if is_selected else None,
            border_radius=10,
            padding=ft.padding.all(10),
            margin=ft.margin.symmetric(horizontal=5, vertical=2),
            on_click=lambda _: self.select_project(project["id"]),
            on_hover=self.on_item_hover
        )
    
    def create_conversation_item(self, conversation_id: str, messages: List[Dict[str, Any]]) -> ft.Container:
        """Create a single conversation list item."""
        is_selected = conversation_id == self.current_conversation_id
        
        # Get last message for preview
        last_message = messages[-1] if messages else None
        preview_text = ""
        timestamp = ""
        
        if last_message:
            content = last_message.get("content", "")
            preview_text = content[:50] + "..." if len(content) > 50 else content
            timestamp = self.format_date(last_message.get("timestamp", ""))
        else:
            preview_text = "No messages yet"
            timestamp = "Now"
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    # Avatar
                    ft.CircleAvatar(
                        content=ft.Icon(
                            ft.icons.CHAT,
                            color=ft.colors.WHITE,
                            size=16
                        ),
                        bgcolor=self.colors["primary"] if is_selected else self.colors["text_secondary"],
                        radius=20
                    ),
                    # Conversation info
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"Conversation {conversation_id.split('_')[1]}",
                                        color=self.colors["text_primary"],
                                        size=14,
                                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                                        expand=True
                                    ),
                                    ft.Text(
                                        timestamp,
                                        color=self.colors["text_secondary"],
                                        size=12
                                    )
                                ],
                                spacing=5
                            ),
                            ft.Text(
                                preview_text,
                                color=self.colors["text_secondary"],
                                size=12,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ],
                        spacing=2,
                        expand=True
                    ),
                    # Unread indicator (if needed)
                    ft.Container(
                        content=ft.Text(
                            "●",
                            color=self.colors["primary"],
                            size=8
                        ),
                        visible=False  # Set based on unread status
                    )
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            ),
            bgcolor=self.colors["hover"] if is_selected else None,
            border_radius=10,
            padding=ft.padding.all(10),
            margin=ft.margin.symmetric(horizontal=5, vertical=2),
            on_click=lambda _: self.select_conversation(conversation_id),
            on_hover=self.on_item_hover
        )
    
    def format_date(self, date_str: str) -> str:
        """Format date for display."""
        if not date_str:
            return ""
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                return dt.strftime("%H:%M")
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return dt.strftime("%A")
            else:
                return dt.strftime("%m/%d/%y")
        except:
            return ""
    
    # Event handlers
    async def on_search_change(self, e):
        """Handle search input changes."""
        self.search_query = e.control.value.lower()
        await self.filter_items()
    
    def on_item_hover(self, e):
        """Handle item hover effects."""
        if e.data == "true":  # Mouse enter
            e.control.bgcolor = self.colors["hover"] + "80"
        else:  # Mouse leave
            # Reset to selection color or transparent
            is_selected = (
                (self.show_conversations and getattr(e.control, 'conversation_id', None) == self.current_conversation_id) or
                (not self.show_conversations and getattr(e.control, 'project_id', None) == self.current_project_id)
            )
            e.control.bgcolor = self.colors["hover"] if is_selected else None
        
        e.control.update()
    
    async def select_project(self, project_id: str):
        """Select a project."""
        self.current_project_id = project_id
        await self.update_project_selection()
        await self.on_project_select(project_id)
    
    async def select_conversation(self, conversation_id: str):
        """Select a conversation."""
        self.current_conversation_id = conversation_id
        await self.update_conversation_selection()
        await self.on_conversation_select(conversation_id)
    
    async def switch_to_projects(self):
        """Switch to projects view."""
        self.show_conversations = False
        await self.update_view()
    
    async def switch_to_conversations(self):
        """Switch to conversations view."""
        self.show_conversations = True
        await self.update_view()
    
    async def on_menu_click(self, e):
        """Handle menu button click."""
        # Show app menu
        pass
    
    async def on_new_project_click(self, e):
        """Handle new project button click."""
        await self.show_new_project_dialog()
    
    async def on_new_conversation_click(self, e):
        """Handle new conversation button click."""
        await self.on_new_conversation()
    
    async def on_more_options(self, e):
        """Handle more options button click."""
        # Show options menu
        pass
    
    async def show_project_options(self, project_id: str):
        """Show project options menu."""
        # Implement project options (rename, delete, etc.)
        pass
    
    async def show_new_project_dialog(self):
        """Show dialog to create new project."""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create New Project"),
            content=ft.Column(
                controls=[
                    ft.TextField(
                        label="Project Name",
                        hint_text="Enter project name",
                        autofocus=True,
                        ref=ft.Ref[ft.TextField]()
                    ),
                    ft.TextField(
                        label="Description (optional)",
                        hint_text="Enter project description",
                        multiline=True,
                        min_lines=2,
                        max_lines=4,
                        ref=ft.Ref[ft.TextField]()
                    )
                ],
                height=200,
                spacing=10
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: self.close_dialog()
                ),
                ft.ElevatedButton(
                    "Create",
                    on_click=lambda _: self.create_project_from_dialog(),
                    style=ft.ButtonStyle(
                        bgcolor=self.colors["primary"],
                        color=ft.colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        # Store dialog reference for closing
        self.current_dialog = dialog
        
        # Show dialog
        self.page.dialog = dialog
        dialog.open = True
        await self.page.update_async()
    
    async def close_dialog(self):
        """Close current dialog."""
        if hasattr(self, 'current_dialog'):
            self.current_dialog.open = False
            await self.page.update_async()
    
    async def create_project_from_dialog(self):
        """Create project from dialog inputs."""
        # Get input values (simplified - in real app would use refs)
        name = "New Project"  # Get from dialog
        description = ""  # Get from dialog
        
        await self.close_dialog()
        await self.on_new_project(name, description)
    
    # Public methods
    async def update_projects(self, projects: Dict[str, Any]):
        """Update the projects list."""
        self.projects = projects
        await self.refresh_projects_list()
    
    async def refresh_projects_list(self):
        """Refresh the projects list display."""
        if not self.projects_list:
            return
        
        self.projects_list.controls.clear()
        
        # Filter projects based on search
        filtered_projects = self.filter_projects()
        
        for project in filtered_projects.values():
            item = self.create_project_item(project)
            self.projects_list.controls.append(item)
        
        await self.projects_list.update_async()
    
    async def refresh_conversations_list(self):
        """Refresh the conversations list display."""
        if not self.conversations_list or not self.current_project_id:
            return
        
        self.conversations_list.controls.clear()
        
        project = self.projects.get(self.current_project_id)
        if not project:
            return
        
        # Get conversations for current project
        conversations = project.get("conversations", [])
        
        for conv_id in conversations:
            messages = []  # Get from conversations store
            item = self.create_conversation_item(conv_id, messages)
            self.conversations_list.controls.append(item)
        
        await self.conversations_list.update_async()
    
    def filter_projects(self) -> Dict[str, Any]:
        """Filter projects based on search query."""
        if not self.search_query:
            return self.projects
        
        filtered = {}
        for pid, project in self.projects.items():
            if (self.search_query in project["name"].lower() or 
                self.search_query in project.get("description", "").lower()):
                filtered[pid] = project
        
        return filtered
    
    async def filter_items(self):
        """Filter displayed items based on search."""
        if self.show_conversations:
            await self.refresh_conversations_list()
        else:
            await self.refresh_projects_list()
    
    async def update_project_selection(self):
        """Update UI to reflect current project selection."""
        await self.refresh_projects_list()
    
    async def update_conversation_selection(self):
        """Update UI to reflect current conversation selection."""
        await self.refresh_conversations_list()
    
    async def update_view(self):
        """Update the view when switching between projects/conversations."""
        # Update tab appearance and list visibility
        await self.update_async()
