"""
Message bubble component for WhatsApp-style chat messages.
Handles different message types, status indicators, and interactions.
"""

import flet as ft
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import asyncio


class MessageBubble:
    """Individual message bubble component."""
    
    def __init__(
        self,
        message: Dict[str, Any],
        colors: Dict[str, str],
        on_retry: Optional[Callable[[str], None]] = None,
        on_copy: Optional[Callable[[str], None]] = None
    ):
        pass  # No super() needed
        self.message = message
        self.colors = colors
        self.on_retry = on_retry
        self.on_copy = on_copy
        
        # Message properties
        self.is_user = message.get("type") == "user"
        self.message_id = message.get("id", "")
        self.content = message.get("content", "")
        self.timestamp = message.get("timestamp", "")
        self.status = message.get("status", "sent")
        self.attachments = message.get("attachments", [])
        self.sources = message.get("sources", [])
        
        # UI state
        self.is_highlighted = False
        self.show_options = False
    
    def build(self):
        """Build the message bubble UI."""
        # Message content components
        content_controls = []
        
        # Add attachments if any
        if self.attachments:
            content_controls.extend(self.create_attachment_previews())
        
        # Add text content
        if self.content:
            content_controls.append(self.create_text_content())
        
        # Add sources if any (AI messages only)
        if self.sources and not self.is_user:
            content_controls.append(self.create_sources_section())
        
        # Message metadata (timestamp and status)
        metadata = self.create_message_metadata()
        content_controls.append(metadata)
        
        # Main message container
        message_container = ft.Container(
            content=ft.Column(
                controls=content_controls,
                spacing=8,
                tight=True
            ),
            bgcolor=self.colors["bubble_sent"] if self.is_user else self.colors["bubble_received"],
            border_radius=ft.border_radius.only(
                top_left=18 if not self.is_user else 18,
                top_right=18 if self.is_user else 18,
                bottom_left=2 if not self.is_user else 18,
                bottom_right=18 if not self.is_user else 2
            ),
            padding=ft.padding.all(12),
            margin=ft.margin.only(
                left=60 if self.is_user else 0,
                right=0 if self.is_user else 60,
                bottom=2
            ),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_long_press=self.show_message_options,
            on_hover=self.on_hover
        )
        
        # Avatar (for AI messages)
        avatar = None
        if not self.is_user:
            avatar = ft.CircleAvatar(
                content=ft.Icon(
                    ft.icons.SMART_TOY,
                    color=ft.colors.WHITE,
                    size=16
                ),
                bgcolor=self.colors["primary"],
                radius=15
            )
        
        # Options menu (hidden by default)
        options_menu = self.create_options_menu()
        
        # Main row layout
        controls = []
        if not self.is_user and avatar:
            controls.append(avatar)
        
        controls.append(
            ft.Stack(
                controls=[
                    message_container,
                    options_menu
                ]
            )
        )
        
        return ft.Container(
            content=ft.Row(
                controls=controls,
                spacing=8,
                alignment=ft.MainAxisAlignment.END if self.is_user else ft.MainAxisAlignment.START
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=4)
        )
    
    def create_text_content(self) -> ft.Container:
        """Create text content with proper formatting."""
        # Parse content for links, formatting, etc.
        text_content = ft.SelectionArea(
            content=ft.Text(
                self.content,
                color=self.colors["text_primary"],
                size=14,
                selectable=True
            )
        )
        
        return ft.Container(
            content=text_content,
            expand=True
        )
    
    def create_attachment_previews(self) -> List[ft.Control]:
        """Create attachment preview components."""
        previews = []
        
        for attachment in self.attachments:
            attachment_type = attachment.get("type", "file")
            name = attachment.get("name", "Unknown file")
            size = attachment.get("size", 0)
            
            if attachment_type == "image":
                preview = self.create_image_preview(attachment)
            elif attachment_type == "document":
                preview = self.create_document_preview(attachment)
            elif attachment_type == "audio":
                preview = self.create_audio_preview(attachment)
            elif attachment_type == "video":
                preview = self.create_video_preview(attachment)
            else:
                preview = self.create_file_preview(attachment)
            
            previews.append(preview)
        
        return previews
    
    def create_image_preview(self, attachment: Dict[str, Any]) -> ft.Container:
        """Create image attachment preview."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Image(
                            src=attachment.get("path", ""),
                            width=200,
                            height=150,
                            fit=ft.ImageFit.COVER,
                            border_radius=8
                        ),
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),
                    ft.Text(
                        attachment.get("name", ""),
                        color=self.colors["text_secondary"],
                        size=12,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.START
            ),
            margin=ft.margin.only(bottom=8)
        )
    
    def create_document_preview(self, attachment: Dict[str, Any]) -> ft.Container:
        """Create document attachment preview."""
        size_str = self.format_file_size(attachment.get("size", 0))
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.icons.DESCRIPTION,
                        color=self.colors["primary"],
                        size=24
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                attachment.get("name", ""),
                                color=self.colors["text_primary"],
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(
                                f"Document • {size_str}",
                                color=self.colors["text_secondary"],
                                size=12
                            )
                        ],
                        spacing=2,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.DOWNLOAD,
                        icon_color=self.colors["text_secondary"],
                        icon_size=20,
                        tooltip="Download",
                        on_click=lambda _: self.download_attachment(attachment)
                    )
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            ),
            bgcolor=self.colors["background"] + "40",
            border_radius=8,
            padding=ft.padding.all(10),
            margin=ft.margin.only(bottom=8)
        )
    
    def create_audio_preview(self, attachment: Dict[str, Any]) -> ft.Container:
        """Create audio attachment preview."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.PLAY_ARROW,
                        icon_color=self.colors["primary"],
                        bgcolor=self.colors["primary"] + "20",
                        tooltip="Play audio"
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                attachment.get("name", ""),
                                color=self.colors["text_primary"],
                                size=14,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(
                                "Audio message",
                                color=self.colors["text_secondary"],
                                size=12
                            )
                        ],
                        spacing=2,
                        expand=True
                    )
                ],
                spacing=10
            ),
            bgcolor=self.colors["background"] + "40",
            border_radius=20,
            padding=ft.padding.all(8),
            margin=ft.margin.only(bottom=8)
        )
    
    def create_video_preview(self, attachment: Dict[str, Any]) -> ft.Container:
        """Create video attachment preview."""
        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.icons.VIDEOCAM,
                            color=ft.colors.WHITE,
                            size=40
                        ),
                        width=200,
                        height=120,
                        bgcolor=self.colors["background"],
                        border_radius=8,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.icons.PLAY_CIRCLE_FILL,
                            icon_color=ft.colors.WHITE,
                            icon_size=50,
                            bgcolor=ft.colors.BLACK54,
                            style=ft.ButtonStyle(
                                shape=ft.CircleBorder()
                            )
                        ),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(
                            attachment.get("name", ""),
                            color=ft.colors.WHITE,
                            size=12,
                            weight=ft.FontWeight.BOLD
                        ),
                        alignment=ft.alignment.bottom_left,
                        padding=ft.padding.all(8)
                    )
                ]
            ),
            margin=ft.margin.only(bottom=8)
        )
    
    def create_file_preview(self, attachment: Dict[str, Any]) -> ft.Container:
        """Create generic file attachment preview."""
        size_str = self.format_file_size(attachment.get("size", 0))
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.icons.ATTACH_FILE,
                        color=self.colors["text_secondary"],
                        size=24
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                attachment.get("name", ""),
                                color=self.colors["text_primary"],
                                size=14,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(
                                f"File • {size_str}",
                                color=self.colors["text_secondary"],
                                size=12
                            )
                        ],
                        spacing=2,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.DOWNLOAD,
                        icon_color=self.colors["text_secondary"],
                        icon_size=20,
                        tooltip="Download",
                        on_click=lambda _: self.download_attachment(attachment)
                    )
                ],
                spacing=10
            ),
            bgcolor=self.colors["background"] + "40",
            border_radius=8,
            padding=ft.padding.all(10),
            margin=ft.margin.only(bottom=8)
        )
    
    def create_sources_section(self) -> ft.Container:
        """Create sources section for AI messages."""
        source_chips = []
        for i, source in enumerate(self.sources[:3]):  # Limit to 3 sources
            chip = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.icons.SOURCE,
                            size=12,
                            color=self.colors["text_secondary"]
                        ),
                        ft.Text(
                            f"Source {i+1}",
                            color=self.colors["text_secondary"],
                            size=11
                        )
                    ],
                    spacing=4,
                    tight=True
                ),
                bgcolor=self.colors["background"] + "60",
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                tooltip=str(source)
            )
            source_chips.append(chip)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Sources:",
                        color=self.colors["text_secondary"],
                        size=11,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row(
                        controls=source_chips,
                        spacing=4,
                        wrap=True
                    )
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.START
            ),
            margin=ft.margin.only(top=8)
        )
    
    def create_message_metadata(self) -> ft.Container:
        """Create timestamp and status indicators."""
        metadata_controls = []
        
        # Timestamp
        timestamp_text = self.format_timestamp(self.timestamp)
        if timestamp_text:
            metadata_controls.append(
                ft.Text(
                    timestamp_text,
                    color=self.colors["text_secondary"],
                    size=11
                )
            )
        
        # Status indicators (user messages only)
        if self.is_user:
            status_icon = self.get_status_icon()
            if status_icon:
                metadata_controls.append(status_icon)
        
        return ft.Container(
            content=ft.Row(
                controls=metadata_controls,
                spacing=4,
                alignment=ft.MainAxisAlignment.END,
                tight=True
            ),
            margin=ft.margin.only(top=4)
        )
    
    def get_status_icon(self) -> Optional[ft.Icon]:
        """Get status icon based on message status."""
            status_icons = {
            "sending": ft.icons.SCHEDULE,
            "sent": ft.icons.DONE,
            "delivered": ft.icons.DONE_ALL,
            "read": ft.icons.DONE_ALL,
            "failed": ft.icons.ERROR
        }
        
        icon = status_icons.get(self.status)
        if not icon:
            return None
        
        color = self.colors["text_secondary"]
        if self.status == "read":
            color = self.colors["primary"]
        elif self.status == "failed":
            color = ft.colors.RED_400
        
        return ft.Icon(
            icon,
            size=12,
            color=color
        )
    
    def create_options_menu(self) -> ft.Container:
        """Create message options menu."""
        options = []
        
        # Copy option
        if self.content:
            options.append(
                ft.MenuItemButton(
                    content=ft.Row(
                        controls=[
                        ft.Icon(ft.icons.COPY, size=16),
                            ft.Text("Copy", size=14)
                        ],
                        spacing=8
                    ),
                    on_click=lambda _: self.copy_message()
                )
            )
        
        # Retry option (failed user messages)
        if self.is_user and self.status == "failed" and self.on_retry:
            options.append(
                ft.MenuItemButton(
                    content=ft.Row(
                        controls=[
                        ft.Icon(ft.icons.REFRESH, size=16),
                            ft.Text("Retry", size=14)
                        ],
                        spacing=8
                    ),
                    on_click=lambda _: self.retry_message()
                )
            )
        
        # Delete option
        options.append(
            ft.MenuItemButton(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.DELETE, size=16, color=ft.colors.RED_400),
                        ft.Text("Delete", size=14, color=ft.colors.RED_400)
                    ],
                    spacing=8
                ),
                on_click=lambda _: self.delete_message()
            )
        )
        
        return ft.Container(
            content=ft.MenuBar(
                controls=options,
                style=ft.MenuStyle(
                    bgcolor=self.colors["sidebar"],
                    surface_tint_color=self.colors["primary"]
                )
            ),
            visible=False,
            top=0,
            right=0 if self.is_user else None,
            left=0 if not self.is_user else None
        )
    
    def format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        if not timestamp:
            return ""
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return ""
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    # Event handlers
    async def on_hover(self, e):
        """Handle hover effects."""
        if e.data == "true":  # Mouse enter
            e.control.scale = 1.02
        else:  # Mouse leave
            e.control.scale = 1.0
        
        await e.control.update_async()
    
    async def show_message_options(self, e):
        """Show message options menu."""
        self.show_options = True
        # Implementation would show context menu
        print(f"Show options for message: {self.message_id}")
    
    async def copy_message(self):
        """Copy message content to clipboard."""
        if self.on_copy:
            await self.on_copy(self.message_id)
    
    async def retry_message(self):
        """Retry sending failed message."""
        if self.on_retry:
            await self.on_retry(self.message_id)
    
    async def delete_message(self):
        """Delete message."""
        # Implementation would remove message from conversation
        print(f"Delete message: {self.message_id}")
    
    async def download_attachment(self, attachment: Dict[str, Any]):
        """Download attachment file."""
        # Implementation would download the file
        print(f"Download attachment: {attachment.get('name', '')}")
    
    # Public methods
    async def update_status(self, new_status: str):
        """Update message status."""
        self.status = new_status
        self.message["status"] = new_status
        await self.update_async()
    
    async def highlight(self, duration: int = 2000):
        """Highlight message temporarily."""
        if hasattr(self, 'controls') and self.controls:
            container = self.controls[0].content.controls[-1]  # Message container
            
            # Add highlight effect
            original_bgcolor = container.bgcolor
            container.bgcolor = self.colors["primary"] + "40"
            await container.update_async()
            
            # Remove highlight after duration
            await asyncio.sleep(duration / 1000)
            container.bgcolor = original_bgcolor
            await container.update_async()
    
    async def animate_in(self):
        """Animate message appearance."""
        if hasattr(self, 'controls') and self.controls:
            container = self.controls[0].content.controls[-1]
            
            # Start with small scale and fade
            container.scale = 0.8
            container.opacity = 0
            await container.update_async()
            
            # Animate to full size and opacity
            container.scale = 1.0
            container.opacity = 1.0
            await container.update_async()
    
    def get_message_data(self) -> Dict[str, Any]:
        """Get current message data."""
        return self.message.copy()
    
    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.is_user
    
    def has_attachments(self) -> bool:
        """Check if message has attachments."""
        return len(self.attachments) > 0
    
    def has_sources(self) -> bool:
        """Check if message has sources."""
        return len(self.sources) > 0
