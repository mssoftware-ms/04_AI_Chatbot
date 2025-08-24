"""
Main chat area component displaying messages in WhatsApp style.
Handles message display, scrolling, and typing indicators.
"""

import flet as ft
import asyncio
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

from .message_bubble import MessageBubble


class ChatArea:
    """Main chat area for displaying messages."""
    
    def __init__(
        self,
        colors: Dict[str, str],
        on_scroll_top: Optional[Callable[[], None]] = None
    ):
        pass  # No super() needed
        self.colors = colors
        self.on_scroll_top = on_scroll_top
        
        # Components
        self.messages_list: Optional[ft.ListView] = None
        self.typing_indicator: Optional[ft.Container] = None
        self.scroll_to_bottom_button: Optional[ft.FloatingActionButton] = None
        
        # State
        self.messages: List[Dict[str, Any]] = []
        self.is_typing = False
        self.show_scroll_button = False
        self.auto_scroll = True
        
        # Message status tracking
        self.message_widgets: Dict[str, MessageBubble] = {}
    
    def build(self):
        """Build the chat area UI."""
        # Messages list with auto-scroll
        self.messages_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.all(15),
            auto_scroll=True,
            on_scroll=self.on_scroll_change
        )
        
        # Typing indicator
        self.typing_indicator = self.create_typing_indicator()
        
        # Scroll to bottom button
        self.scroll_to_bottom_button = ft.FloatingActionButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            bgcolor=self.colors["primary"],
            mini=True,
            visible=False,
            on_click=self.scroll_to_bottom
        )
        
        # Main container with background pattern
        chat_container = ft.Container(
            content=ft.Stack(
                controls=[
                    # Background pattern (optional)
                    ft.Container(
                        bgcolor=self.colors["chat"],
                        expand=True
                    ),
                    # Messages container
                    ft.Column(
                        controls=[
                            # Messages list
                            ft.Container(
                                content=self.messages_list,
                                expand=True
                            ),
                            # Typing indicator
                            self.typing_indicator
                        ],
                        spacing=0,
                        expand=True
                    ),
                    # Scroll to bottom button
                    ft.Container(
                        content=self.scroll_to_bottom_button,
                        alignment=ft.alignment.bottom_right,
                        padding=ft.padding.only(right=20, bottom=20)
                    )
                ]
            ),
            bgcolor=self.colors["chat"],
            expand=True
        )
        
        return chat_container
    
    def create_typing_indicator(self) -> ft.Container:
        """Create animated typing indicator."""
        # Animated dots
        dots = ft.Row(
            controls=[
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=self.colors["text_secondary"],
                    border_radius=4,
                    animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
                ),
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=self.colors["text_secondary"],
                    border_radius=4,
                    animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
                ),
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=self.colors["text_secondary"],
                    border_radius=4,
                    animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
                )
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(
                            ft.Icons.SMART_TOY,
                            color=ft.Colors.WHITE,
                            size=16
                        ),
                        bgcolor=self.colors["primary"],
                        radius=15
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "AI Assistant is typing",
                                    color=self.colors["text_secondary"],
                                    size=12,
                                    italic=True
                                ),
                                dots
                            ],
                            spacing=5,
                            horizontal_alignment=ft.CrossAxisAlignment.START
                        ),
                        bgcolor=self.colors["bubble_received"],
                        border_radius=ft.border_radius.only(
                            top_left=2,
                            top_right=18,
                            bottom_left=18,
                            bottom_right=18
                        ),
                        padding=ft.padding.all(12),
                        margin=ft.margin.only(right=60)
                    )
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            visible=False,
            animate_opacity=300
        )
    
    async def add_message(self, message: Dict[str, Any]):
        """Add a new message to the chat."""
        if not self.messages_list:
            return
        
        # Create message bubble
        bubble = MessageBubble(
            message=message,
            colors=self.colors,
            on_retry=self.on_message_retry if message["type"] == "user" else None,
            on_copy=self.on_message_copy
        )
        
        # Store reference for status updates
        self.message_widgets[message["id"]] = bubble
        
        # Add to list
        self.messages_list.controls.append(bubble)
        self.messages.append(message)
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            await self.scroll_to_bottom()
        else:
            self.show_scroll_button = True
            if self.scroll_to_bottom_button:
                self.scroll_to_bottom_button.visible = True
        
        await self.messages_list.update_async()
        if self.scroll_to_bottom_button:
            await self.scroll_to_bottom_button.update_async()
    
    async def load_messages(self, messages: List[Dict[str, Any]]):
        """Load and display a list of messages."""
        if not self.messages_list:
            return
        
        # Clear current messages
        self.messages_list.controls.clear()
        self.messages.clear()
        self.message_widgets.clear()
        
        # Add messages
        for message in messages:
            bubble = MessageBubble(
                message=message,
                colors=self.colors,
                on_retry=self.on_message_retry if message["type"] == "user" else None,
                on_copy=self.on_message_copy
            )
            
            self.message_widgets[message["id"]] = bubble
            self.messages_list.controls.append(bubble)
            self.messages.append(message)
        
        await self.messages_list.update_async()
        await self.scroll_to_bottom()
    
    async def show_typing_indicator(self):
        """Show typing indicator with animation."""
        if not self.typing_indicator:
            return
        
        self.is_typing = True
        self.typing_indicator.visible = True
        await self.typing_indicator.update_async()
        
        # Start dot animation
        await self.animate_typing_dots()
        
        # Auto-scroll to show typing indicator
        if self.auto_scroll:
            await self.scroll_to_bottom()
    
    async def hide_typing_indicator(self):
        """Hide typing indicator."""
        if not self.typing_indicator:
            return
        
        self.is_typing = False
        self.typing_indicator.visible = False
        await self.typing_indicator.update_async()
    
    async def animate_typing_dots(self):
        """Animate typing indicator dots."""
        if not self.is_typing or not self.typing_indicator:
            return
        
        # Get dots containers
        dots_row = self.typing_indicator.content.controls[1].content.controls[1]
        dots = dots_row.controls
        
        # Animate each dot with delay
        for i, dot in enumerate(dots):
            if not self.is_typing:
                break
            
            # Fade up animation
            dot.opacity = 0.3
            await dot.update_async()
            
            # Small delay between dots
            await asyncio.sleep(0.2)
            
            dot.opacity = 1.0
            await dot.update_async()
        
        # Continue animation loop while typing
        if self.is_typing:
            await asyncio.sleep(0.5)
            await self.animate_typing_dots()
    
    async def update_message_status(self, message_id: str, status: str):
        """Update message delivery status."""
        bubble = self.message_widgets.get(message_id)
        if bubble:
            await bubble.update_status(status)
        
        # Update message data
        for message in self.messages:
            if message["id"] == message_id:
                message["status"] = status
                break
    
    async def scroll_to_bottom(self, e=None):
        """Scroll to bottom of messages."""
        if self.messages_list:
            self.messages_list.scroll_to(
                offset=-1,  # Scroll to end
                duration=300
            )
            await self.messages_list.update_async()
        
        # Hide scroll button
        self.show_scroll_button = False
        if self.scroll_to_bottom_button:
            self.scroll_to_bottom_button.visible = False
            await self.scroll_to_bottom_button.update_async()
    
    async def on_scroll_change(self, e):
        """Handle scroll position changes."""
        if not self.messages_list:
            return
        
        # Check if scrolled to top (load more messages)
        if e.pixels <= 100 and self.on_scroll_top:
            await self.on_scroll_top()
        
        # Check if scrolled away from bottom (show scroll button)
        max_scroll = e.max_scroll_extent
        current_scroll = e.pixels
        
        if max_scroll - current_scroll > 100:
            # Not at bottom, show scroll button
            if not self.show_scroll_button:
                self.show_scroll_button = True
                if self.scroll_to_bottom_button:
                    self.scroll_to_bottom_button.visible = True
                    await self.scroll_to_bottom_button.update_async()
            self.auto_scroll = False
        else:
            # Near bottom, hide scroll button and enable auto-scroll
            if self.show_scroll_button:
                self.show_scroll_button = False
                if self.scroll_to_bottom_button:
                    self.scroll_to_bottom_button.visible = False
                    await self.scroll_to_bottom_button.update_async()
            self.auto_scroll = True
    
    async def on_message_retry(self, message_id: str):
        """Handle message retry request."""
        # Find and resend message
        for message in self.messages:
            if message["id"] == message_id:
                message["status"] = "sending"
                await self.update_message_status(message_id, "sending")
                # Trigger resend logic in parent component
                break
    
    async def on_message_copy(self, message_id: str):
        """Handle message copy request."""
        for message in self.messages:
            if message["id"] == message_id:
                # Copy message content to clipboard
                if self.page:
                    self.page.set_clipboard(message.get("content", ""))
                    # Show confirmation
                    await self.show_copy_confirmation()
                break
    
    async def show_copy_confirmation(self):
        """Show copy confirmation snackbar."""
        if self.page:
            snackbar = ft.SnackBar(
                content=ft.Text("Message copied to clipboard"),
                bgcolor=self.colors["primary"],
                duration=2000
            )
            self.page.show_snack_bar(snackbar)
    
    def get_last_message_time(self) -> Optional[datetime]:
        """Get timestamp of last message for grouping."""
        if not self.messages:
            return None
        
        last_msg = self.messages[-1]
        timestamp_str = last_msg.get("timestamp")
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                pass
        
        return None
    
    def should_show_timestamp(self, message: Dict[str, Any]) -> bool:
        """Determine if timestamp should be shown for message."""
        if not self.messages:
            return True
        
        try:
            msg_time = datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
            last_time = self.get_last_message_time()
            
            if not last_time:
                return True
            
            # Show timestamp if more than 5 minutes apart
            time_diff = msg_time - last_time
            return time_diff.total_seconds() > 300
            
        except:
            return True
    
    async def clear_messages(self):
        """Clear all messages from chat."""
        if self.messages_list:
            self.messages_list.controls.clear()
            await self.messages_list.update_async()
        
        self.messages.clear()
        self.message_widgets.clear()
    
    async def search_messages(self, query: str) -> List[Dict[str, Any]]:
        """Search messages by content."""
        if not query:
            return self.messages
        
        query_lower = query.lower()
        results = []
        
        for message in self.messages:
            content = message.get("content", "").lower()
            if query_lower in content:
                results.append(message)
        
        return results
    
    async def highlight_message(self, message_id: str):
        """Highlight a specific message (for search results)."""
        bubble = self.message_widgets.get(message_id)
        if bubble:
            await bubble.highlight()
    
    async def export_messages(self, format_type: str = "txt") -> str:
        """Export messages to text format."""
        if format_type == "txt":
            lines = []
            for message in self.messages:
                timestamp = message.get("timestamp", "")
                sender = "You" if message["type"] == "user" else "AI Assistant"
                content = message.get("content", "")
                lines.append(f"[{timestamp}] {sender}: {content}")
            return "\n".join(lines)
        
        # Add other formats as needed (JSON, HTML, etc.)
        return ""
    
    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation statistics and summary."""
        user_messages = sum(1 for msg in self.messages if msg["type"] == "user")
        ai_messages = sum(1 for msg in self.messages if msg["type"] == "assistant")
        
        first_message = self.messages[0] if self.messages else None
        last_message = self.messages[-1] if self.messages else None
        
        return {
            "total_messages": len(self.messages),
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "first_message_time": first_message.get("timestamp") if first_message else None,
            "last_message_time": last_message.get("timestamp") if last_message else None,
            "last_message_preview": last_message.get("content", "")[:100] if last_message else ""
        }