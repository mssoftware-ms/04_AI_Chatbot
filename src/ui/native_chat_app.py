"""
Native Python GUI version of the WhatsApp AI Chatbot using Tkinter.
Provides an alternative to the web-based Flet interface.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import json
import websockets
from datetime import datetime
import requests
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path


class NativeChatApp:
    """Native Tkinter implementation of the WhatsApp AI Chatbot."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp AI Chatbot - Native")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure dark theme colors
        self.colors = {
            "bg_primary": "#111b21",
            "bg_secondary": "#202c33",
            "bg_chat": "#0b141a",
            "bg_input": "#2a3942",
            "text_primary": "#e9edef",
            "text_secondary": "#8696a0",
            "accent": "#00a884",
            "sent_bubble": "#005c4b",
            "received_bubble": "#202c33",
            "border": "#313d45"
        }
        
        # Configure root
        self.root.configure(bg=self.colors["bg_primary"])
        
        # Application state
        self.messages: List[Dict[str, Any]] = []
        self.websocket = None
        self.is_connected = False
        
        # Setup UI
        self.setup_ui()
        self.setup_websocket_connection()
        
        # Load initial messages
        self.load_sample_messages()
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Create main container
        main_container = tk.Frame(self.root, bg=self.colors["bg_primary"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create three-panel layout
        self.create_sidebar(main_container)
        self.create_chat_area(main_container)
        self.create_input_area(main_container)
    
    def create_sidebar(self, parent):
        """Create the left sidebar with projects and conversations."""
        sidebar_frame = tk.Frame(
            parent, 
            bg=self.colors["bg_secondary"], 
            width=320,
            relief=tk.RAISED,
            bd=1
        )
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        sidebar_frame.pack_propagate(False)
        
        # Header
        header_frame = tk.Frame(sidebar_frame, bg=self.colors["bg_secondary"], height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="AI Assistant",
            font=("Arial", 14, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_secondary"]
        )
        title_label.pack(pady=10)
        
        # Search
        search_frame = tk.Frame(sidebar_frame, bg=self.colors["bg_secondary"])
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=self.colors["bg_input"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief=tk.FLAT,
            bd=5
        )
        search_entry.pack(fill=tk.X)
        search_entry.insert(0, "Search conversations...")
        search_entry.bind('<FocusIn>', self.on_search_focus_in)
        search_entry.bind('<FocusOut>', self.on_search_focus_out)
        
        # Conversations list
        conversations_frame = tk.LabelFrame(
            sidebar_frame,
            text="Conversations",
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"]
        )
        conversations_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Conversation items
        conversations = [
            {"name": "General Chat", "last_message": "Hello! How can I help you?", "time": "10:30"},
            {"name": "Code Review", "last_message": "Let me check that function...", "time": "09:15"},
            {"name": "Project Planning", "last_message": "The API design looks good", "time": "Yesterday"},
        ]
        
        for conv in conversations:
            self.create_conversation_item(conversations_frame, conv)
    
    def create_conversation_item(self, parent, conversation):
        """Create a conversation list item."""
        item_frame = tk.Frame(
            parent,
            bg=self.colors["bg_secondary"],
            relief=tk.FLAT,
            bd=1
        )
        item_frame.pack(fill=tk.X, pady=1)
        
        # Conversation info
        info_frame = tk.Frame(item_frame, bg=self.colors["bg_secondary"])
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Name and time
        name_time_frame = tk.Frame(info_frame, bg=self.colors["bg_secondary"])
        name_time_frame.pack(fill=tk.X)
        
        name_label = tk.Label(
            name_time_frame,
            text=conversation["name"],
            font=("Arial", 11, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_secondary"],
            anchor="w"
        )
        name_label.pack(side=tk.LEFT)
        
        time_label = tk.Label(
            name_time_frame,
            text=conversation["time"],
            font=("Arial", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
            anchor="e"
        )
        time_label.pack(side=tk.RIGHT)
        
        # Last message
        msg_label = tk.Label(
            info_frame,
            text=conversation["last_message"],
            font=("Arial", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
            anchor="w",
            wraplength=280
        )
        msg_label.pack(fill=tk.X, pady=(2, 0))
        
        # Hover effect
        def on_enter(e):
            item_frame.configure(bg=self.colors["bg_input"])
            info_frame.configure(bg=self.colors["bg_input"])
            name_time_frame.configure(bg=self.colors["bg_input"])
            name_label.configure(bg=self.colors["bg_input"])
            time_label.configure(bg=self.colors["bg_input"])
            msg_label.configure(bg=self.colors["bg_input"])
        
        def on_leave(e):
            item_frame.configure(bg=self.colors["bg_secondary"])
            info_frame.configure(bg=self.colors["bg_secondary"])
            name_time_frame.configure(bg=self.colors["bg_secondary"])
            name_label.configure(bg=self.colors["bg_secondary"])
            time_label.configure(bg=self.colors["bg_secondary"])
            msg_label.configure(bg=self.colors["bg_secondary"])
        
        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
        for widget in [info_frame, name_time_frame, name_label, time_label, msg_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    
    def create_chat_area(self, parent):
        """Create the main chat area."""
        chat_container = tk.Frame(parent, bg=self.colors["bg_primary"])
        chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        # Chat header
        header_frame = tk.Frame(
            chat_container, 
            bg=self.colors["bg_secondary"], 
            height=60,
            relief=tk.RAISED,
            bd=1
        )
        header_frame.pack(fill=tk.X, pady=(0, 2))
        header_frame.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header_frame, bg=self.colors["bg_secondary"])
        header_content.pack(fill=tk.BOTH, padx=15, pady=10)
        
        # Avatar and name
        info_frame = tk.Frame(header_content, bg=self.colors["bg_secondary"])
        info_frame.pack(side=tk.LEFT)
        
        # AI Avatar (simple circle)
        avatar_frame = tk.Frame(info_frame, bg=self.colors["accent"], width=40, height=40)
        avatar_frame.pack(side=tk.LEFT)
        avatar_frame.pack_propagate(False)
        
        avatar_label = tk.Label(
            avatar_frame,
            text="AI",
            font=("Arial", 12, "bold"),
            fg="white",
            bg=self.colors["accent"]
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Name and status
        name_frame = tk.Frame(info_frame, bg=self.colors["bg_secondary"])
        name_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        name_label = tk.Label(
            name_frame,
            text="AI Assistant",
            font=("Arial", 12, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_secondary"]
        )
        name_label.pack(anchor="w")
        
        self.status_label = tk.Label(
            name_frame,
            text="Online",
            font=("Arial", 9),
            fg=self.colors["accent"],
            bg=self.colors["bg_secondary"]
        )
        self.status_label.pack(anchor="w")
        
        # Header buttons
        buttons_frame = tk.Frame(header_content, bg=self.colors["bg_secondary"])
        buttons_frame.pack(side=tk.RIGHT)
        
        search_btn = tk.Button(
            buttons_frame,
            text="🔍",
            font=("Arial", 12),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"],
            relief=tk.FLAT,
            bd=0,
            padx=10,
            command=self.on_search_messages
        )
        search_btn.pack(side=tk.LEFT, padx=2)
        
        menu_btn = tk.Button(
            buttons_frame,
            text="⋮",
            font=("Arial", 14),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"],
            relief=tk.FLAT,
            bd=0,
            padx=10,
            command=self.show_menu
        )
        menu_btn.pack(side=tk.LEFT, padx=2)
        
        # Messages area
        messages_frame = tk.Frame(chat_container, bg=self.colors["bg_chat"])
        messages_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2))
        
        # Scrollable messages
        self.messages_canvas = tk.Canvas(
            messages_frame,
            bg=self.colors["bg_chat"],
            highlightthickness=0
        )
        self.messages_scrollbar = ttk.Scrollbar(
            messages_frame,
            orient="vertical",
            command=self.messages_canvas.yview
        )
        self.scrollable_messages = tk.Frame(self.messages_canvas, bg=self.colors["bg_chat"])
        
        self.scrollable_messages.bind(
            "<Configure>",
            lambda e: self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all"))
        )
        
        self.messages_canvas.create_window((0, 0), window=self.scrollable_messages, anchor="nw")
        self.messages_canvas.configure(yscrollcommand=self.messages_scrollbar.set)
        
        self.messages_canvas.pack(side="left", fill="both", expand=True)
        self.messages_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.messages_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.messages_canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def create_input_area(self, parent):
        """Create the message input area."""
        input_container = tk.Frame(parent, bg=self.colors["bg_primary"])
        input_container.pack(fill=tk.X, side=tk.BOTTOM, pady=(2, 0))
        
        # Input frame
        input_frame = tk.Frame(
            input_container,
            bg=self.colors["bg_secondary"],
            relief=tk.RAISED,
            bd=1
        )
        input_frame.pack(fill=tk.X, padx=0)
        
        # Input controls
        controls_frame = tk.Frame(input_frame, bg=self.colors["bg_secondary"])
        controls_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Attach button
        attach_btn = tk.Button(
            controls_frame,
            text="📎",
            font=("Arial", 12),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"],
            relief=tk.FLAT,
            bd=0,
            padx=8,
            command=self.attach_file
        )
        attach_btn.pack(side=tk.LEFT)
        
        # Message input
        self.message_entry = tk.Text(
            controls_frame,
            height=1,
            bg=self.colors["bg_input"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief=tk.FLAT,
            bd=5,
            wrap=tk.WORD,
            font=("Arial", 11)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 5))
        
        # Bind Enter key
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.bind("<KeyRelease>", self.on_typing)
        
        # Send button
        self.send_btn = tk.Button(
            controls_frame,
            text="➤",
            font=("Arial", 14),
            bg=self.colors["accent"],
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            state=tk.DISABLED,
            command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT)
    
    def add_message_bubble(self, message: Dict[str, Any]):
        """Add a message bubble to the chat."""
        is_user = message.get("type") == "user"
        content = message.get("content", "")
        timestamp = message.get("timestamp", datetime.now().strftime("%H:%M"))
        
        # Message container
        msg_container = tk.Frame(self.scrollable_messages, bg=self.colors["bg_chat"])
        msg_container.pack(fill=tk.X, padx=15, pady=2)
        
        # Message bubble
        bubble_color = self.colors["sent_bubble"] if is_user else self.colors["received_bubble"]
        
        bubble_frame = tk.Frame(
            msg_container,
            bg=bubble_color,
            relief=tk.FLAT,
            bd=10
        )
        
        if is_user:
            bubble_frame.pack(side=tk.RIGHT, anchor="e")
        else:
            bubble_frame.pack(side=tk.LEFT, anchor="w")
        
        # Message content
        msg_label = tk.Label(
            bubble_frame,
            text=content,
            font=("Arial", 11),
            fg=self.colors["text_primary"],
            bg=bubble_color,
            wraplength=400,
            justify="left",
            anchor="w"
        )
        msg_label.pack(padx=12, pady=8)
        
        # Timestamp
        time_label = tk.Label(
            bubble_frame,
            text=timestamp,
            font=("Arial", 8),
            fg=self.colors["text_secondary"],
            bg=bubble_color,
            anchor="e"
        )
        time_label.pack(anchor="e", padx=12, pady=(0, 8))
        
        # Auto-scroll to bottom
        self.root.after(10, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll messages to bottom."""
        self.messages_canvas.update_idletasks()
        self.messages_canvas.yview_moveto(1)
    
    def send_message(self, event=None):
        """Send a message."""
        content = self.message_entry.get("1.0", tk.END).strip()
        if not content:
            return "break" if event else None
        
        # Add user message
        user_message = {
            "id": f"msg_{len(self.messages)}",
            "type": "user",
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        
        self.messages.append(user_message)
        self.add_message_bubble(user_message)
        
        # Clear input
        self.message_entry.delete("1.0", tk.END)
        self.send_btn.configure(state=tk.DISABLED)
        
        # Send to backend (simulate for now)
        threading.Thread(target=self.send_to_backend, args=(content,), daemon=True).start()
        
        return "break" if event else None
    
    def send_to_backend(self, content: str):
        """Send message to backend API."""
        try:
            # Simulate AI thinking
            self.root.after(0, lambda: self.status_label.configure(text="Typing..."))
            
            # Try to send to actual backend
            response = requests.post(
                "http://localhost:8000/chat/send",
                json={"message": content, "conversation_id": "default"},
                timeout=10
            )
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "I received your message!")
            else:
                ai_response = f"I'm having trouble connecting to the backend (Status: {response.status_code})"
                
        except requests.exceptions.RequestException:
            # Fallback response when backend is not available
            ai_responses = [
                f"I understand you said: '{content}'. How can I help you further?",
                "That's an interesting point! Could you tell me more?",
                "I'm processing your message. What would you like to know?",
                "Thanks for your message! I'm here to help with any questions.",
                f"You mentioned '{content[:50]}{'...' if len(content) > 50 else ''}'. What's your next question?"
            ]
            
            import random
            ai_response = random.choice(ai_responses)
        
        # Add AI response
        def add_ai_response():
            ai_message = {
                "id": f"msg_{len(self.messages)}",
                "type": "assistant", 
                "content": ai_response,
                "timestamp": datetime.now().strftime("%H:%M")
            }
            
            self.messages.append(ai_message)
            self.add_message_bubble(ai_message)
            self.status_label.configure(text="Online")
        
        # Add response after delay
        self.root.after(1500, add_ai_response)
    
    def on_typing(self, event=None):
        """Handle typing in message input."""
        content = self.message_entry.get("1.0", tk.END).strip()
        if content:
            self.send_btn.configure(state=tk.NORMAL)
        else:
            self.send_btn.configure(state=tk.DISABLED)
    
    def attach_file(self):
        """Handle file attachment."""
        filename = filedialog.askopenfilename(
            title="Select file to attach",
            filetypes=[
                ("All files", "*.*"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Documents", "*.pdf *.doc *.docx *.txt"),
                ("Code", "*.py *.js *.html *.css *.json")
            ]
        )
        
        if filename:
            file_path = Path(filename)
            # Add file attachment message
            attachment_msg = {
                "id": f"msg_{len(self.messages)}",
                "type": "user",
                "content": f"📎 Attached: {file_path.name}",
                "timestamp": datetime.now().strftime("%H:%M")
            }
            
            self.messages.append(attachment_msg)
            self.add_message_bubble(attachment_msg)
    
    def on_search_focus_in(self, event):
        """Handle search field focus."""
        if self.search_var.get() == "Search conversations...":
            event.widget.delete(0, tk.END)
            event.widget.configure(fg=self.colors["text_primary"])
    
    def on_search_focus_out(self, event):
        """Handle search field blur."""
        if not self.search_var.get():
            event.widget.insert(0, "Search conversations...")
            event.widget.configure(fg=self.colors["text_secondary"])
    
    def on_search_messages(self):
        """Handle message search."""
        messagebox.showinfo("Search", "Message search feature coming soon!")
    
    def show_menu(self):
        """Show context menu."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Export Chat", command=self.export_chat)
        menu.add_command(label="Clear Chat", command=self.clear_chat)
        menu.add_separator()
        menu.add_command(label="Settings", command=self.show_settings)
        menu.add_command(label="About", command=self.show_about)
        
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()
    
    def export_chat(self):
        """Export chat history."""
        if not self.messages:
            messagebox.showinfo("Export", "No messages to export!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.messages, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        for msg in self.messages:
                            sender = "You" if msg["type"] == "user" else "AI"
                            f.write(f"[{msg['timestamp']}] {sender}: {msg['content']}\\n")
                
                messagebox.showinfo("Export", f"Chat exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export chat: {e}")
    
    def clear_chat(self):
        """Clear chat history."""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear all messages?"):
            self.messages.clear()
            for widget in self.scrollable_messages.winfo_children():
                widget.destroy()
    
    def show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings panel coming soon!")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """WhatsApp AI Chatbot - Native GUI
        
Version: 1.0.0
Created with Python & Tkinter

Features:
• Native Windows interface
• Real-time chat with AI
• File attachments
• Export functionality
• WhatsApp-inspired design

Backend API: http://localhost:8000"""
        
        messagebox.showinfo("About", about_text)
    
    def load_sample_messages(self):
        """Load some sample messages."""
        sample_messages = [
            {
                "id": "msg_0",
                "type": "assistant",
                "content": "Hello! I'm your AI assistant. How can I help you today?",
                "timestamp": "10:00"
            },
            {
                "id": "msg_1", 
                "type": "user",
                "content": "Hi! Can you help me with a Python question?",
                "timestamp": "10:01"
            },
            {
                "id": "msg_2",
                "type": "assistant", 
                "content": "Of course! I'd be happy to help with Python. What specific question do you have?",
                "timestamp": "10:01"
            }
        ]
        
        for msg in sample_messages:
            self.messages.append(msg)
            self.add_message_bubble(msg)
    
    def setup_websocket_connection(self):
        """Setup WebSocket connection to backend."""
        # This would connect to the backend WebSocket
        # For now, we'll use HTTP requests
        pass
    
    def run(self):
        """Start the native chat application."""
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # Start main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass


def main():
    """Main entry point."""
    app = NativeChatApp()
    app.run()


if __name__ == "__main__":
    main()