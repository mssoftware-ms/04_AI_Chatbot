"""
SQLAlchemy models for WhatsApp AI Chatbot database.

Defines all database tables with relationships, indexes, and constraints
for optimal performance and data integrity.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class Project(Base):
    """
    Project model for isolating different chatbot instances.
    
    Each project has its own ChromaDB collection and conversation history.
    """
    __tablename__ = "projects"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ChromaDB integration
    vector_collection_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    
    # Configuration
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    memory_entries: Mapped[List["MemoryEntry"]] = relationship("MemoryEntry", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_projects_active_created", "is_active", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name})>"


class Conversation(Base):
    """
    Conversation model for tracking chat sessions.
    
    Groups messages by conversation context and maintains session state.
    """
    __tablename__ = "conversations"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation metadata
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Session information
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status and timestamps
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    user_sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_conversations_project_phone", "project_id", "phone_number"),
        Index("ix_conversations_active_activity", "is_active", "last_activity"),
        Index("ix_conversations_session_active", "session_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, phone_number={self.phone_number})>"


class Message(Base):
    """
    Message model for storing all chat messages.
    
    Supports both user and assistant messages with rich metadata and context.
    """
    __tablename__ = "messages"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'user', 'assistant', 'system'
    
    # WhatsApp specific fields
    whatsapp_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Processing status
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)  # 'pending', 'processing', 'completed', 'error'
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # AI context
    context_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Rich metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    # Indexes for performance-critical queries
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_messages_phone_created", "phone_number", "created_at"),
        Index("ix_messages_type_status", "message_type", "processing_status"),
        Index("ix_messages_whatsapp_id", "whatsapp_message_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, type={self.message_type}, phone_number={self.phone_number})>"


class Document(Base):
    """
    Document model for RAG system document storage.
    
    Tracks uploaded documents and their processing status for knowledge base.
    """
    __tablename__ = "documents"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document metadata
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    
    # Processing status
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    chunks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vectors_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_documents_project_status", "project_id", "processing_status"),
        Index("ix_documents_filename_project", "filename", "project_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    """
    Document chunk model for RAG system text chunks.
    
    Stores processed text chunks with embeddings references for vector search.
    """
    __tablename__ = "document_chunks"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Chunk content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Vector reference (ChromaDB document ID)
    vector_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    
    # Chunk metadata
    start_char: Mapped[int] = mapped_column(Integer, nullable=False)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Processing info
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    
    # Indexes
    __table_args__ = (
        Index("ix_chunks_document_index", "document_id", "chunk_index"),
    )
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class MemoryEntry(Base):
    """
    Memory entry model for conversation memory and context.
    
    Stores important information extracted from conversations for long-term memory.
    """
    __tablename__ = "memory_entries"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Memory content
    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'fact', 'preference', 'context', 'summary'
    
    # Context
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Importance and relevance
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, index=True)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Metadata
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="memory_entries")
    
    # Indexes
    __table_args__ = (
        Index("ix_memory_project_key", "project_id", "key"),
        Index("ix_memory_type_importance", "memory_type", "importance_score"),
        Index("ix_memory_phone_created", "phone_number", "created_at"),
        Index("ix_memory_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<MemoryEntry(id={self.id}, key={self.key}, type={self.memory_type})>"


class UserSession(Base):
    """
    User session model for tracking user interaction sessions.
    
    Manages session state and context for better conversation continuity.
    """
    __tablename__ = "user_sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session info
    session_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Session state
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="user_sessions")
    
    # Indexes
    __table_args__ = (
        Index("ix_sessions_phone_active", "phone_number", "is_active"),
        Index("ix_sessions_key_phone", "session_key", "phone_number"),
        Index("ix_sessions_activity", "last_activity"),
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, phone_number={self.phone_number}, active={self.is_active})>"


# Event listeners for automatic timestamp updates
@event.listens_for(Conversation, "before_update")
def update_conversation_activity(mapper, connection, target):
    """Update last_activity on conversation update."""
    target.last_activity = func.now()


@event.listens_for(UserSession, "before_update")
def update_session_activity(mapper, connection, target):
    """Update last_activity on session update."""
    target.last_activity = func.now()


@event.listens_for(MemoryEntry, "before_update")
def update_memory_access(mapper, connection, target):
    """Update last_accessed on memory entry update."""
    target.last_accessed = func.now()
    target.access_count += 1