"""
CRUD operations for WhatsApp AI Chatbot database models.

Provides comprehensive database operations with error handling,
pagination, filtering, and optimized queries.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Conversation,
    Document,
    DocumentChunk,
    MemoryEntry,
    Message,
    Project,
    UserSession,
)

logger = logging.getLogger(__name__)


class BaseCRUD:
    """Base CRUD operations for all models."""
    
    def __init__(self, model_class):
        self.model_class = model_class
    
    async def get_by_id(self, session: AsyncSession, record_id: str) -> Optional[Any]:
        """Get record by ID."""
        try:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == record_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {record_id}: {e}")
            return None
    
    async def delete(self, session: AsyncSession, record_id: str) -> bool:
        """Delete record by ID."""
        try:
            record = await self.get_by_id(session, record_id)
            if record:
                await session.delete(record)
                await session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__} {record_id}: {e}")
            await session.rollback()
            return False


class ProjectCRUD(BaseCRUD):
    """CRUD operations for Project model."""
    
    def __init__(self):
        super().__init__(Project)
    
    async def create(
        self,
        session: AsyncSession,
        name: str,
        vector_collection_name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[Project]:
        """Create new project."""
        try:
            project = Project(
                name=name,
                description=description,
                vector_collection_name=vector_collection_name,
                settings=settings or {},
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
            logger.info(f"Created project: {project.id}")
            return project
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await session.rollback()
            return None
    
    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Project]:
        """Get project by name."""
        try:
            result = await session.execute(
                select(Project).where(Project.name == name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting project by name {name}: {e}")
            return None
    
    async def get_by_collection_name(self, session: AsyncSession, collection_name: str) -> Optional[Project]:
        """Get project by vector collection name."""
        try:
            result = await session.execute(
                select(Project).where(Project.vector_collection_name == collection_name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting project by collection name {collection_name}: {e}")
            return None
    
    async def list_active(
        self,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Project]:
        """List active projects with pagination."""
        try:
            result = await session.execute(
                select(Project)
                .where(Project.is_active == True)
                .order_by(desc(Project.created_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing active projects: {e}")
            return []
    
    async def update_settings(
        self,
        session: AsyncSession,
        project_id: str,
        settings: Dict[str, Any],
    ) -> bool:
        """Update project settings."""
        try:
            await session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(settings=settings, updated_at=func.now())
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating project settings {project_id}: {e}")
            await session.rollback()
            return False
    
    async def deactivate(self, session: AsyncSession, project_id: str) -> bool:
        """Deactivate project."""
        try:
            await session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(is_active=False, updated_at=func.now())
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deactivating project {project_id}: {e}")
            await session.rollback()
            return False


class ConversationCRUD(BaseCRUD):
    """CRUD operations for Conversation model."""
    
    def __init__(self):
        super().__init__(Conversation)
    
    async def create(
        self,
        session: AsyncSession,
        project_id: str,
        phone_number: str,
        contact_name: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Conversation]:
        """Create new conversation."""
        try:
            conversation = Conversation(
                project_id=project_id,
                phone_number=phone_number,
                contact_name=contact_name,
                session_id=session_id,
                metadata=metadata or {},
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            logger.info(f"Created conversation: {conversation.id}")
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            await session.rollback()
            return None
    
    async def get_or_create_active(
        self,
        session: AsyncSession,
        project_id: str,
        phone_number: str,
        contact_name: Optional[str] = None,
    ) -> Optional[Conversation]:
        """Get active conversation or create new one."""
        try:
            # Try to find active conversation
            result = await session.execute(
                select(Conversation)
                .where(
                    and_(
                        Conversation.project_id == project_id,
                        Conversation.phone_number == phone_number,
                        Conversation.is_active == True,
                    )
                )
                .order_by(desc(Conversation.last_activity))
            )
            conversation = result.scalar_one_or_none()
            
            if conversation:
                # Update last activity
                conversation.last_activity = func.now()
                await session.commit()
                return conversation
            
            # Create new conversation
            return await self.create(
                session=session,
                project_id=project_id,
                phone_number=phone_number,
                contact_name=contact_name,
            )
        except Exception as e:
            logger.error(f"Error getting or creating conversation: {e}")
            return None
    
    async def get_with_messages(
        self,
        session: AsyncSession,
        conversation_id: str,
        message_limit: int = 50,
    ) -> Optional[Conversation]:
        """Get conversation with recent messages."""
        try:
            result = await session.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages).limit(message_limit))
                .where(Conversation.id == conversation_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting conversation with messages {conversation_id}: {e}")
            return None
    
    async def list_by_phone(
        self,
        session: AsyncSession,
        phone_number: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Conversation]:
        """List conversations by phone number."""
        try:
            query = select(Conversation).where(Conversation.phone_number == phone_number)
            
            if project_id:
                query = query.where(Conversation.project_id == project_id)
            
            query = query.order_by(desc(Conversation.last_activity)).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing conversations by phone {phone_number}: {e}")
            return []
    
    async def update_context_summary(
        self,
        session: AsyncSession,
        conversation_id: str,
        context_summary: str,
    ) -> bool:
        """Update conversation context summary."""
        try:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    context_summary=context_summary,
                    updated_at=func.now(),
                    last_activity=func.now(),
                )
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating context summary {conversation_id}: {e}")
            await session.rollback()
            return False
    
    async def deactivate_old_conversations(
        self,
        session: AsyncSession,
        hours_threshold: int = 24,
    ) -> int:
        """Deactivate conversations inactive for specified hours."""
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)
            
            result = await session.execute(
                update(Conversation)
                .where(
                    and_(
                        Conversation.is_active == True,
                        Conversation.last_activity < threshold_time,
                    )
                )
                .values(is_active=False, updated_at=func.now())
            )
            await session.commit()
            return result.rowcount
        except Exception as e:
            logger.error(f"Error deactivating old conversations: {e}")
            await session.rollback()
            return 0


class MessageCRUD(BaseCRUD):
    """CRUD operations for Message model."""
    
    def __init__(self):
        super().__init__(Message)
    
    async def create(
        self,
        session: AsyncSession,
        conversation_id: str,
        content: str,
        message_type: str,
        phone_number: str,
        whatsapp_message_id: Optional[str] = None,
        context_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Message]:
        """Create new message."""
        try:
            message = Message(
                conversation_id=conversation_id,
                content=content,
                message_type=message_type,
                phone_number=phone_number,
                whatsapp_message_id=whatsapp_message_id,
                context_used=context_used,
                metadata=metadata or {},
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            logger.info(f"Created message: {message.id}")
            return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            await session.rollback()
            return None
    
    async def get_by_whatsapp_id(
        self,
        session: AsyncSession,
        whatsapp_message_id: str,
    ) -> Optional[Message]:
        """Get message by WhatsApp message ID."""
        try:
            result = await session.execute(
                select(Message).where(Message.whatsapp_message_id == whatsapp_message_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting message by WhatsApp ID {whatsapp_message_id}: {e}")
            return None
    
    async def list_by_conversation(
        self,
        session: AsyncSession,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
        message_type: Optional[str] = None,
    ) -> List[Message]:
        """List messages by conversation."""
        try:
            query = select(Message).where(Message.conversation_id == conversation_id)
            
            if message_type:
                query = query.where(Message.message_type == message_type)
            
            query = query.order_by(desc(Message.created_at)).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing messages by conversation {conversation_id}: {e}")
            return []
    
    async def get_conversation_history(
        self,
        session: AsyncSession,
        conversation_id: str,
        limit: int = 20,
    ) -> List[Message]:
        """Get recent conversation history."""
        try:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)  # Ascending for chronological order
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting conversation history {conversation_id}: {e}")
            return []
    
    async def update_processing_status(
        self,
        session: AsyncSession,
        message_id: str,
        status: str,
        error_message: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> bool:
        """Update message processing status."""
        try:
            update_data = {
                "processing_status": status,
                "processed_at": func.now() if status == "completed" else None,
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if tokens_used:
                update_data["tokens_used"] = tokens_used
            
            await session.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(**update_data)
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating message processing status {message_id}: {e}")
            await session.rollback()
            return False
    
    async def get_pending_messages(
        self,
        session: AsyncSession,
        limit: int = 10,
    ) -> List[Message]:
        """Get messages pending processing."""
        try:
            result = await session.execute(
                select(Message)
                .where(Message.processing_status == "pending")
                .order_by(Message.created_at)
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting pending messages: {e}")
            return []


class DocumentCRUD(BaseCRUD):
    """CRUD operations for Document model."""
    
    def __init__(self):
        super().__init__(Document)
    
    async def create(
        self,
        session: AsyncSession,
        project_id: str,
        filename: str,
        original_path: str,
        file_size: int,
        mime_type: str,
        file_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Document]:
        """Create new document."""
        try:
            document = Document(
                project_id=project_id,
                filename=filename,
                original_path=original_path,
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                metadata=metadata or {},
            )
            session.add(document)
            await session.commit()
            await session.refresh(document)
            logger.info(f"Created document: {document.id}")
            return document
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            await session.rollback()
            return None
    
    async def get_by_hash(self, session: AsyncSession, file_hash: str) -> Optional[Document]:
        """Get document by file hash."""
        try:
            result = await session.execute(
                select(Document).where(Document.file_hash == file_hash)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting document by hash {file_hash}: {e}")
            return None
    
    async def list_by_project(
        self,
        session: AsyncSession,
        project_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """List documents by project."""
        try:
            query = select(Document).where(Document.project_id == project_id)
            
            if status:
                query = query.where(Document.processing_status == status)
            
            query = query.order_by(desc(Document.uploaded_at)).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing documents by project {project_id}: {e}")
            return []
    
    async def update_processing_status(
        self,
        session: AsyncSession,
        document_id: str,
        status: str,
        chunks_count: Optional[int] = None,
        vectors_generated: Optional[bool] = None,
    ) -> bool:
        """Update document processing status."""
        try:
            update_data = {
                "processing_status": status,
                "processed_at": func.now() if status == "completed" else None,
            }
            
            if chunks_count is not None:
                update_data["chunks_count"] = chunks_count
            
            if vectors_generated is not None:
                update_data["vectors_generated"] = vectors_generated
            
            await session.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(**update_data)
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating document processing status {document_id}: {e}")
            await session.rollback()
            return False
    
    async def get_pending_documents(
        self,
        session: AsyncSession,
        limit: int = 5,
    ) -> List[Document]:
        """Get documents pending processing."""
        try:
            result = await session.execute(
                select(Document)
                .where(Document.processing_status == "pending")
                .order_by(Document.uploaded_at)
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting pending documents: {e}")
            return []


class MemoryCRUD(BaseCRUD):
    """CRUD operations for MemoryEntry model."""
    
    def __init__(self):
        super().__init__(MemoryEntry)
    
    async def create_or_update(
        self,
        session: AsyncSession,
        project_id: str,
        key: str,
        value: str,
        memory_type: str = "fact",
        phone_number: Optional[str] = None,
        conversation_id: Optional[str] = None,
        importance_score: float = 1.0,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryEntry]:
        """Create new memory entry or update existing one."""
        try:
            # Check if memory entry exists
            result = await session.execute(
                select(MemoryEntry).where(
                    and_(
                        MemoryEntry.project_id == project_id,
                        MemoryEntry.key == key,
                        MemoryEntry.phone_number == phone_number,
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing entry
                existing.value = value
                existing.memory_type = memory_type
                existing.importance_score = importance_score
                existing.expires_at = expires_at
                existing.metadata = metadata or {}
                existing.last_accessed = func.now()
                existing.access_count += 1
                
                await session.commit()
                return existing
            else:
                # Create new entry
                memory_entry = MemoryEntry(
                    project_id=project_id,
                    key=key,
                    value=value,
                    memory_type=memory_type,
                    phone_number=phone_number,
                    conversation_id=conversation_id,
                    importance_score=importance_score,
                    expires_at=expires_at,
                    metadata=metadata or {},
                )
                session.add(memory_entry)
                await session.commit()
                await session.refresh(memory_entry)
                logger.info(f"Created memory entry: {memory_entry.id}")
                return memory_entry
        except Exception as e:
            logger.error(f"Error creating/updating memory entry: {e}")
            await session.rollback()
            return None
    
    async def get_by_key(
        self,
        session: AsyncSession,
        project_id: str,
        key: str,
        phone_number: Optional[str] = None,
    ) -> Optional[MemoryEntry]:
        """Get memory entry by key."""
        try:
            query = select(MemoryEntry).where(
                and_(
                    MemoryEntry.project_id == project_id,
                    MemoryEntry.key == key,
                )
            )
            
            if phone_number:
                query = query.where(MemoryEntry.phone_number == phone_number)
            
            result = await session.execute(query)
            memory = result.scalar_one_or_none()
            
            if memory:
                # Update access tracking
                memory.last_accessed = func.now()
                memory.access_count += 1
                await session.commit()
            
            return memory
        except Exception as e:
            logger.error(f"Error getting memory by key {key}: {e}")
            return None
    
    async def search_memories(
        self,
        session: AsyncSession,
        project_id: str,
        query: str,
        phone_number: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Search memories by value content."""
        try:
            query_condition = select(MemoryEntry).where(
                and_(
                    MemoryEntry.project_id == project_id,
                    or_(
                        MemoryEntry.key.contains(query),
                        MemoryEntry.value.contains(query),
                    ),
                )
            )
            
            if phone_number:
                query_condition = query_condition.where(MemoryEntry.phone_number == phone_number)
            
            if memory_type:
                query_condition = query_condition.where(MemoryEntry.memory_type == memory_type)
            
            query_condition = query_condition.order_by(
                desc(MemoryEntry.importance_score),
                desc(MemoryEntry.last_accessed),
            ).limit(limit)
            
            result = await session.execute(query_condition)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def list_by_type(
        self,
        session: AsyncSession,
        project_id: str,
        memory_type: str,
        phone_number: Optional[str] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """List memories by type."""
        try:
            query = select(MemoryEntry).where(
                and_(
                    MemoryEntry.project_id == project_id,
                    MemoryEntry.memory_type == memory_type,
                )
            )
            
            if phone_number:
                query = query.where(MemoryEntry.phone_number == phone_number)
            
            query = query.order_by(
                desc(MemoryEntry.importance_score),
                desc(MemoryEntry.created_at),
            ).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing memories by type {memory_type}: {e}")
            return []
    
    async def cleanup_expired(self, session: AsyncSession) -> int:
        """Remove expired memory entries."""
        try:
            current_time = datetime.utcnow()
            
            # Get expired entries
            result = await session.execute(
                select(MemoryEntry).where(
                    and_(
                        MemoryEntry.expires_at.is_not(None),
                        MemoryEntry.expires_at < current_time,
                    )
                )
            )
            expired_entries = list(result.scalars().all())
            
            # Delete expired entries
            for entry in expired_entries:
                await session.delete(entry)
            
            await session.commit()
            logger.info(f"Cleaned up {len(expired_entries)} expired memory entries")
            return len(expired_entries)
        except Exception as e:
            logger.error(f"Error cleaning up expired memories: {e}")
            await session.rollback()
            return 0