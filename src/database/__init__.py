"""
Database package for WhatsApp AI Chatbot.

This package provides database models, session management, and CRUD operations
using SQLAlchemy 2.0 with async support and SQLite with WAL mode optimization.
"""

from .session import DatabaseSession, get_db_session, init_database
from .models import (
    Base,
    Project,
    Conversation,
    Message,
    Document,
    DocumentChunk,
    MemoryEntry,
    UserSession,
)
from .crud import (
    ProjectCRUD,
    ConversationCRUD,
    MessageCRUD,
    DocumentCRUD,
    MemoryCRUD,
)

__all__ = [
    # Session management
    "DatabaseSession",
    "get_db_session",
    "init_database",
    # Models
    "Base",
    "Project",
    "Conversation",
    "Message",
    "Document",
    "DocumentChunk",
    "MemoryEntry",
    "UserSession",
    # CRUD operations
    "ProjectCRUD",
    "ConversationCRUD",
    "MessageCRUD",
    "DocumentCRUD",
    "MemoryCRUD",
]