"""
Input area component with message input, file attachment, and send functionality.
Includes drag & drop support and attachment previews.
"""

import flet as ft
from typing import Dict, Any, List, Callable, Optional
import os
import asyncio
from pathlib import Path


class InputArea:
    """Message input area with file attachment support."""
    
    def __init__(
        self,
        colors: Dict[str, str],
        on_send_message: Callable[[str, Optional[List[str]]], None],
        on_file_attach: Callable[[List[str]], None],
        page: Optional[ft.Page] = None
    ):
        self.colors = colors
        self.on_send_message = on_send_message
        self.on_file_attach = on_file_attach
        self.page = page
        
        # Components
        self.message_input: Optional[ft.TextField] = None
        self.send_button: Optional[ft.IconButton] = None
        self.attach_button: Optional[ft.IconButton] = None
        self.emoji_button: Optional[ft.IconButton] = None
        self.voice_button: Optional[ft.IconButton] = None
        self.file_picker: Optional[ft.FilePicker] = None
        self.attachments_preview: Optional[ft.Container] = None
        
        # State
        self.is_enabled = True
        self.current_attachments: List[Dict[str, Any]] = []
        self.is_recording = False
        self.drag_active = False
        
        # Input constraints
        self.max_message_length = 4096
        self.max_attachments = 10
        self.allowed_file_types = [
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.mp3', '.wav', '.ogg', '.m4a',
            '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.zip', '.rar', '.7z', '.tar', '.gz'
        ]
    
    def build(self):
        """Build the input area UI."""
        # File picker for attachments
        self.file_picker = ft.FilePicker(
            on_result=self.on_file_picker_result
        )
        
        # Attachments preview (hidden by default)
        self.attachments_preview = ft.Container(
            content=ft.Column(
                controls=[],
                spacing=8
            ),
            visible=False,
            padding=ft.padding.all(10),
            border=ft.border.only(bottom=ft.BorderSide(1, self.colors["border"]))
        )
        
        # Message input field
        self.message_input = ft.TextField(
            hint_text="Type a message...",
            hint_style=ft.TextStyle(color=self.colors["text_secondary"]),
            text_style=ft.TextStyle(color=self.colors["text_primary"]),
            bgcolor=self.colors["background"],
            border_color="transparent",
            focused_border_color="transparent",
            multiline=True,
            min_lines=1,
            max_lines=5,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=15, vertical=12),
            on_change=self.on_input_change,
            on_submit=self.on_input_submit,
            border_radius=25
        )
        
        # Action buttons
        self.attach_button = ft.IconButton(
            icon=ft.icons.ATTACH_FILE,
            icon_color=self.colors["text_secondary"],
            tooltip="Attach file",
            on_click=self.on_attach_click
        )
        
        self.emoji_button = ft.IconButton(
            icon=ft.icons.EMOJI_EMOTIONS,
            icon_color=self.colors["text_secondary"],
            tooltip="Emoji",
            on_click=self.on_emoji_click
        )
        
        self.voice_button = ft.IconButton(
            icon=ft.icons.MIC,
            icon_color=self.colors["text_secondary"],
            tooltip="Voice message",
            on_click=self.on_voice_click
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND,
            icon_color=ft.colors.WHITE,
            bgcolor=self.colors["primary"],
            tooltip="Send message",
            on_click=self.on_send_click,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder()
            )
        )
        
        # Input container with drag & drop
        input_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.attach_button,
                    self.message_input,
                    self.emoji_button,
                    self.voice_button,
                    self.send_button
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.END
            ),
            bgcolor=self.colors["sidebar"],
            border_radius=25,
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            border=ft.border.all(1, "transparent"),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        )
        
        # Drag & drop overlay
        drop_overlay = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.icons.CLOUD_UPLOAD,
                        size=48,
                        color=self.colors["primary"]
                    ),
                    ft.Text(
                        "Drop files here to attach",
                        color=self.colors["primary"],
                        size=16,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"Supports: {', '.join(self.allowed_file_types[:5])}...",
                        color=self.colors["text_secondary"],
                        size=12
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=self.colors["primary"] + "20",
            border=ft.border.all(2, self.colors["primary"]),
            border_radius=15,
            padding=ft.padding.all(20),
            visible=False,
            animate_opacity=200
        )
        
        # Main container with stack for drag & drop
        main_container = ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Column(
                        controls=[
                            self.attachments_preview,
                            input_container
                        ],
                        spacing=0
                    ),
                    drop_overlay
                ]
            ),
            on_hover=self.on_drag_hover
        )
        
        # Add file picker to page overlay if page is available
        if self.page and self.file_picker:
            self.page.overlay.append(self.file_picker)
        
        return main_container
    
    def create_attachment_preview(self, attachment: Dict[str, Any]) -> ft.Container:
        """Create attachment preview item."""
        file_type = attachment.get("type", "file")
        name = attachment.get("name", "Unknown")
        size = attachment.get("size", 0)
        
        # Icon based on file type
        icon_map = {
            "image": ft.icons.IMAGE,
            "document": ft.icons.DESCRIPTION,
            "audio": ft.icons.AUDIOTRACK,
            "video": ft.icons.VIDEOCAM,
            "text": ft.icons.TEXT_SNIPPET,
            "file": ft.icons.ATTACH_FILE
        }
        
        icon = ft.Icon(
            icon_map.get(file_type, ft.icons.ATTACH_FILE),
            color=self.colors["primary"],
            size=20
        )
        
        # Thumbnail for images
        thumbnail = None
        if file_type == "image" and attachment.get("path"):
            thumbnail = ft.Container(
                content=ft.Image(
                    src=attachment["path"],
                    width=40,
                    height=40,
                    fit=ft.ImageFit.COVER,
                    border_radius=4
                ),
                width=40,
                height=40,
                border_radius=4,
                clip_behavior=ft.ClipBehavior.HARD_EDGE
            )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    thumbnail or icon,
                    ft.Column(
                        controls=[
                            ft.Text(
                                name,
                                color=self.colors["text_primary"],
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(
                                f"{self.format_file_size(size)} • {file_type.title()}",
                                color=self.colors["text_secondary"],
                                size=12
                            )
                        ],
                        spacing=2,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_color=self.colors["text_secondary"],
                        icon_size=16,
                        tooltip="Remove",
                        on_click=lambda _: self.remove_attachment(attachment["id"])
                    )
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            ),
            bgcolor=self.colors["background"],
            border_radius=8,
            padding=ft.padding.all(8),
            margin=ft.margin.only(bottom=4)
        )
    
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
    
    def get_file_type(self, file_path: str) -> str:
        """Determine file type from extension."""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return "image"
        elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
            return "document"
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac']:
            return "audio"
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']:
            return "video"
        elif ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']:
            return "text"
        else:
            return "file"
    
    # Event handlers
    async def on_input_change(self, e):
        """Handle input text changes."""
        text = e.control.value
        has_text = bool(text.strip())
        has_attachments = len(self.current_attachments) > 0
        
        # Update send button state
        if self.send_button:
            self.send_button.disabled = not (has_text or has_attachments)
            await self.send_button.update_async()
        
        # Update character count (if needed)
        if len(text) > self.max_message_length:
            e.control.value = text[:self.max_message_length]
            await e.control.update_async()
    
    async def on_input_submit(self, e):
        """Handle Enter key in input field."""
        await self.send_message()
    
    async def on_send_click(self, e):
        """Handle send button click."""
        await self.send_message()
    
    async def on_attach_click(self, e):
        """Handle attach button click."""
        if self.file_picker:
            await self.file_picker.pick_files_async(
                dialog_title="Select files to attach",
                file_type=ft.FilePickerFileType.ANY,
                allow_multiple=True
            )
    
    async def on_emoji_click(self, e):
        """Handle emoji button click."""
        # Show emoji picker (simplified implementation)
        emoji_dialog = ft.AlertDialog(
            title=ft.Text("Emojis"),
            content=ft.Container(
                content=ft.GridView(
                    runs_count=6,
                    max_extent=40,
                    child_aspect_ratio=1.0,
                    spacing=5,
                    run_spacing=5,
                    controls=[
                        ft.TextButton(
                            emoji,
                            on_click=lambda e, em=emoji: self.insert_emoji(em)
                        )
                        for emoji in ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", 
                                     "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰",
                                     "😘", "😗", "😙", "😚", "😋", "😛", "😝", "😜",
                                     "🤪", "🤨", "🧐", "🤓", "😎", "🤩", "🥳", "😏",
                                     "👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙"]
                    ]
                ),
                width=300,
                height=200
            ),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda _: self.close_emoji_dialog()
                )
            ]
        )
        
        self.page.dialog = emoji_dialog
        emoji_dialog.open = True
        await self.page.update_async()
    
    async def insert_emoji(self, emoji: str):
        """Insert emoji into message input."""
        if self.message_input:
            current_text = self.message_input.value or ""
            self.message_input.value = current_text + emoji
            await self.message_input.update_async()
        
        await self.close_emoji_dialog()
    
    async def close_emoji_dialog(self):
        """Close emoji dialog."""
        if self.page.dialog:
            self.page.dialog.open = False
            await self.page.update_async()
    
    async def on_voice_click(self, e):
        """Handle voice button click."""
        if not self.is_recording:
            await self.start_voice_recording()
        else:
            await self.stop_voice_recording()
    
    async def start_voice_recording(self):
        """Start voice message recording."""
        self.is_recording = True
        
        if self.voice_button:
            self.voice_button.icon = ft.icons.STOP
            self.voice_button.bgcolor = ft.colors.RED_400
            self.voice_button.tooltip = "Stop recording"
            await self.voice_button.update_async()
        
        # Show recording indicator
        recording_dialog = ft.AlertDialog(
            title=ft.Text("Recording voice message..."),
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.MIC, color=ft.colors.RED_400, size=48),
                    ft.Text("Tap to stop recording", text_align=ft.TextAlign.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                height=100
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: self.cancel_voice_recording()
                ),
                ft.ElevatedButton(
                    "Stop",
                    on_click=lambda _: self.stop_voice_recording(),
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.RED_400,
                        color=ft.colors.WHITE
                    )
                )
            ]
        )
        
        self.page.dialog = recording_dialog
        recording_dialog.open = True
        await self.page.update_async()
    
    async def stop_voice_recording(self):
        """Stop voice message recording."""
        self.is_recording = False
        
        # Reset voice button
        if self.voice_button:
            self.voice_button.icon = ft.icons.MIC
            self.voice_button.bgcolor = None
            self.voice_button.tooltip = "Voice message"
            await self.voice_button.update_async()
        
        # Close recording dialog
        if self.page.dialog:
            self.page.dialog.open = False
            await self.page.update_async()
        
        # In a real implementation, process the recorded audio
        # For now, just show a placeholder
        await self.add_voice_attachment("voice_message.mp3", 5.2)
    
    async def cancel_voice_recording(self):
        """Cancel voice message recording."""
        self.is_recording = False
        
        if self.voice_button:
            self.voice_button.icon = ft.icons.MIC
            self.voice_button.bgcolor = None
            await self.voice_button.update_async()
        
        if self.page.dialog:
            self.page.dialog.open = False
            await self.page.update_async()
    
    async def on_file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker results."""
        if e.files:
            file_paths = [f.path for f in e.files if f.path]
            await self.add_file_attachments(file_paths)
    
    async def on_drag_hover(self, e):
        """Handle drag and drop hover events."""
        # Simplified drag & drop implementation
        # In a real implementation, this would handle drag enter/leave/drop events
        pass
    
    # Attachment management
    async def add_file_attachments(self, file_paths: List[str]):
        """Add file attachments."""
        if len(self.current_attachments) + len(file_paths) > self.max_attachments:
            await self.show_error(f"Maximum {self.max_attachments} attachments allowed")
            return
        
        new_attachments = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
            
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.allowed_file_types:
                await self.show_error(f"File type {file_ext} not supported")
                continue
            
            attachment = {
                "id": f"att_{len(self.current_attachments) + len(new_attachments) + 1}",
                "name": os.path.basename(file_path),
                "path": file_path,
                "type": self.get_file_type(file_path),
                "size": os.path.getsize(file_path)
            }
            new_attachments.append(attachment)
        
        if new_attachments:
            self.current_attachments.extend(new_attachments)
            await self.update_attachments_preview()
            await self.on_file_attach([att["path"] for att in new_attachments])
    
    async def add_voice_attachment(self, file_name: str, duration: float):
        """Add voice message attachment."""
        attachment = {
            "id": f"voice_{len(self.current_attachments) + 1}",
            "name": file_name,
            "path": f"temp/{file_name}",  # Temporary path
            "type": "audio",
            "size": 1024 * int(duration * 10),  # Estimate size
            "duration": duration
        }
        
        self.current_attachments.append(attachment)
        await self.update_attachments_preview()
    
    async def remove_attachment(self, attachment_id: str):
        """Remove attachment by ID."""
        self.current_attachments = [
            att for att in self.current_attachments 
            if att["id"] != attachment_id
        ]
        await self.update_attachments_preview()
    
    async def update_attachments_preview(self):
        """Update attachments preview display."""
        if not self.attachments_preview:
            return
        
        preview_controls = []
        
        if self.current_attachments:
            # Header
            preview_controls.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            f"Attachments ({len(self.current_attachments)})",
                            color=self.colors["text_primary"],
                            size=14,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.TextButton(
                            "Clear all",
                            on_click=lambda _: self.clear_attachments(),
                            style=ft.ButtonStyle(
                                color=self.colors["text_secondary"]
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            )
            
            # Attachment items
            for attachment in self.current_attachments:
                preview_controls.append(self.create_attachment_preview(attachment))
        
        self.attachments_preview.content.controls = preview_controls
        self.attachments_preview.visible = len(self.current_attachments) > 0
        
        await self.attachments_preview.update_async()
        
        # Update send button state
        await self.on_input_change(type('Event', (), {'control': self.message_input})())
    
    async def clear_attachments(self):
        """Clear all attachments."""
        self.current_attachments.clear()
        await self.update_attachments_preview()
    
    # Message sending
    async def send_message(self):
        """Send the current message."""
        if not self.is_enabled:
            return
        
        message_text = self.message_input.value.strip() if self.message_input else ""
        
        if not message_text and not self.current_attachments:
            return
        
        # Get attachment paths
        attachment_paths = [att["path"] for att in self.current_attachments]
        
        # Send message
        await self.on_send_message(message_text, attachment_paths if attachment_paths else None)
        
        # Clear input
        await self.clear_input()
    
    async def clear_input(self):
        """Clear message input and attachments."""
        if self.message_input:
            self.message_input.value = ""
            await self.message_input.update_async()
        
        await self.clear_attachments()
    
    # Utility methods
    async def show_error(self, message: str):
        """Show error message."""
        error_snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.colors.RED_400,
            duration=3000
        )
        self.page.show_snack_bar(error_snackbar)
    
    async def enable(self):
        """Enable input area."""
        self.is_enabled = True
        if self.message_input:
            self.message_input.disabled = False
            await self.message_input.update_async()
    
    async def disable(self):
        """Disable input area."""
        self.is_enabled = False
        if self.message_input:
            self.message_input.disabled = True
            await self.message_input.update_async()
    
    async def show_attachments(self, attachments: List[Dict[str, Any]]):
        """Show attachments in preview area."""
        self.current_attachments = attachments
        await self.update_attachments_preview()
    
    async def focus_input(self):
        """Focus the message input field."""
        if self.message_input:
            await self.message_input.focus_async()
    
    async def set_placeholder(self, text: str):
        """Set input placeholder text."""
        if self.message_input:
            self.message_input.hint_text = text
            await self.message_input.update_async()
    
    def get_message_text(self) -> str:
        """Get current message text."""
        return self.message_input.value if self.message_input else ""
    
    def has_content(self) -> bool:
        """Check if there's content to send."""
        has_text = bool(self.get_message_text().strip())
        has_attachments = len(self.current_attachments) > 0
        return has_text or has_attachments
    
    def get_attachment_count(self) -> int:
        """Get number of current attachments."""
        return len(self.current_attachments)
