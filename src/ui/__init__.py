"""
WhatsApp-like UI package for AI Chatbot.
Provides a complete chat interface using Flet framework.
"""

from .chat_app import ChatApp
from .websocket_client import WebSocketClient

__all__ = ["ChatApp", "WebSocketClient"]