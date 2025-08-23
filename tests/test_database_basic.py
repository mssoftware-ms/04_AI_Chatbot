"""
Basic database functionality tests for WhatsApp AI Chatbot.

Tests database initialization, model creation, and basic CRUD operations.
"""

import asyncio
import pytest
from pathlib import Path
import tempfile
import os

from src.database import (
    init_database,
    get_db_session,
    ProjectCRUD,
    ConversationCRUD,
    MessageCRUD,
    DocumentCRUD,
    MemoryCRUD,
)


@pytest.fixture
async def temp_db():
    """Create temporary database for testing."""
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    # Initialize database
    db_session = await init_database(db_url)
    
    yield db_session
    
    # Cleanup
    await db_session.close()
    if db_path.exists():
        os.unlink(db_path)
    os.rmdir(temp_dir)


@pytest.mark.asyncio
async def test_database_initialization(temp_db):
    """Test database initialization and health check."""
    # Test health check
    health_check = await temp_db.health_check()
    assert health_check is True
    
    # Test session creation
    async with temp_db.get_session() as session:
        assert session is not None


@pytest.mark.asyncio
async def test_project_crud(temp_db):
    """Test Project CRUD operations."""
    project_crud = ProjectCRUD()
    
    async with temp_db.get_session() as session:
        # Create project
        project = await project_crud.create(
            session=session,
            name="Test Project",
            vector_collection_name="test_collection",
            description="A test project",
            settings={"test": "value"},
        )
        
        assert project is not None
        assert project.name == "Test Project"
        assert project.vector_collection_name == "test_collection"
        assert project.settings["test"] == "value"
        
        # Get by ID
        retrieved = await project_crud.get_by_id(session, project.id)
        assert retrieved is not None
        assert retrieved.id == project.id
        
        # Get by name
        by_name = await project_crud.get_by_name(session, "Test Project")
        assert by_name is not None
        assert by_name.id == project.id
        
        # List active projects
        projects = await project_crud.list_active(session)
        assert len(projects) == 1
        assert projects[0].id == project.id


@pytest.mark.asyncio
async def test_conversation_crud(temp_db):
    """Test Conversation CRUD operations."""
    project_crud = ProjectCRUD()
    conversation_crud = ConversationCRUD()
    
    async with temp_db.get_session() as session:
        # Create project first
        project = await project_crud.create(
            session=session,
            name="Test Project",
            vector_collection_name="test_collection",
        )
        
        # Create conversation
        conversation = await conversation_crud.create(
            session=session,
            project_id=project.id,
            phone_number="+1234567890",
            contact_name="Test User",
        )
        
        assert conversation is not None
        assert conversation.phone_number == "+1234567890"
        assert conversation.project_id == project.id
        
        # Get or create active conversation
        active_conv = await conversation_crud.get_or_create_active(
            session=session,
            project_id=project.id,
            phone_number="+1234567890",
        )
        
        # Should return the same conversation
        assert active_conv.id == conversation.id


@pytest.mark.asyncio
async def test_message_crud(temp_db):
    """Test Message CRUD operations."""
    project_crud = ProjectCRUD()
    conversation_crud = ConversationCRUD()
    message_crud = MessageCRUD()
    
    async with temp_db.get_session() as session:
        # Create project and conversation
        project = await project_crud.create(
            session=session,
            name="Test Project",
            vector_collection_name="test_collection",
        )
        
        conversation = await conversation_crud.create(
            session=session,
            project_id=project.id,
            phone_number="+1234567890",
        )
        
        # Create message
        message = await message_crud.create(
            session=session,
            conversation_id=conversation.id,
            content="Test message",
            message_type="user",
            phone_number="+1234567890",
            whatsapp_message_id="wa_123",
        )
        
        assert message is not None
        assert message.content == "Test message"
        assert message.message_type == "user"
        
        # Get by WhatsApp ID
        by_wa_id = await message_crud.get_by_whatsapp_id(session, "wa_123")
        assert by_wa_id is not None
        assert by_wa_id.id == message.id
        
        # List by conversation
        messages = await message_crud.list_by_conversation(
            session=session,
            conversation_id=conversation.id,
        )
        assert len(messages) == 1
        assert messages[0].id == message.id


@pytest.mark.asyncio
async def test_memory_crud(temp_db):
    """Test MemoryEntry CRUD operations."""
    project_crud = ProjectCRUD()
    memory_crud = MemoryCRUD()
    
    async with temp_db.get_session() as session:
        # Create project
        project = await project_crud.create(
            session=session,
            name="Test Project",
            vector_collection_name="test_collection",
        )
        
        # Create memory entry
        memory = await memory_crud.create_or_update(
            session=session,
            project_id=project.id,
            key="user_preference",
            value="Prefers brief responses",
            memory_type="preference",
            phone_number="+1234567890",
            importance_score=0.8,
        )
        
        assert memory is not None
        assert memory.key == "user_preference"
        assert memory.value == "Prefers brief responses"
        assert memory.importance_score == 0.8
        
        # Get by key
        retrieved = await memory_crud.get_by_key(
            session=session,
            project_id=project.id,
            key="user_preference",
            phone_number="+1234567890",
        )
        assert retrieved is not None
        assert retrieved.id == memory.id
        
        # Search memories
        results = await memory_crud.search_memories(
            session=session,
            project_id=project.id,
            query="brief",
            phone_number="+1234567890",
        )
        assert len(results) == 1
        assert results[0].id == memory.id


@pytest.mark.asyncio
async def test_document_crud(temp_db):
    """Test Document CRUD operations."""
    project_crud = ProjectCRUD()
    document_crud = DocumentCRUD()
    
    async with temp_db.get_session() as session:
        # Create project
        project = await project_crud.create(
            session=session,
            name="Test Project",
            vector_collection_name="test_collection",
        )
        
        # Create document
        document = await document_crud.create(
            session=session,
            project_id=project.id,
            filename="test.txt",
            original_path="/path/to/test.txt",
            file_size=1024,
            mime_type="text/plain",
            file_hash="abc123",
        )
        
        assert document is not None
        assert document.filename == "test.txt"
        assert document.file_size == 1024
        
        # Get by hash
        by_hash = await document_crud.get_by_hash(session, "abc123")
        assert by_hash is not None
        assert by_hash.id == document.id
        
        # List by project
        documents = await document_crud.list_by_project(
            session=session,
            project_id=project.id,
        )
        assert len(documents) == 1
        assert documents[0].id == document.id


if __name__ == "__main__":
    # Run a simple test
    async def main():
        print("Running basic database tests...")
        
        # Create temporary database
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        db_url = f"sqlite+aiosqlite:///{db_path}"
        
        try:
            # Initialize database
            db_session = await init_database(db_url)
            
            # Test health check
            health = await db_session.health_check()
            print(f"Database health check: {'✓' if health else '✗'}")
            
            # Test project creation
            project_crud = ProjectCRUD()
            async with db_session.get_session() as session:
                project = await project_crud.create(
                    session=session,
                    name="Test Project",
                    vector_collection_name="test_collection",
                    description="Test project for basic functionality",
                )
                print(f"Project created: {'✓' if project else '✗'}")
                
                if project:
                    print(f"  - ID: {project.id}")
                    print(f"  - Name: {project.name}")
                    print(f"  - Collection: {project.vector_collection_name}")
            
            # Close database
            await db_session.close()
            print("Database closed successfully: ✓")
            
        except Exception as e:
            print(f"Test failed: ✗")
            print(f"Error: {e}")
        finally:
            # Cleanup
            if db_path.exists():
                os.unlink(db_path)
            os.rmdir(temp_dir)
        
        print("Basic database tests completed!")
    
    # Run the test
    asyncio.run(main())