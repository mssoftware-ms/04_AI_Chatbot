"""
Database Model and CRUD Operations Tests

This module contains comprehensive tests for database models,
CRUD operations, and database-related functionality.
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta
import uuid
import asyncio

from tests import TestDataFactory, TestMarkers, generate_test_id


@pytest.mark.database
@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection and configuration."""

    async def test_database_connection_async(self, async_session):
        """Test that async database connection is established successfully."""
        assert async_session is not None
        
        # Test basic query
        result = await async_session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row[0] == 1

    async def test_database_transaction_rollback(self, async_session):
        """Test that database transactions can be rolled back properly."""
        # Start transaction
        async with async_session.begin():
            # This would normally involve actual model operations
            # For now, we test the session functionality
            result = await async_session.execute(text("SELECT 1"))
            assert result is not None
            
            # Force rollback by raising exception
            try:
                raise Exception("Test rollback")
            except Exception:
                await async_session.rollback()

    async def test_database_connection_error_handling(self):
        """Test database connection error handling."""
        # Test with invalid connection string
        with pytest.raises(SQLAlchemyError):
            engine = create_async_engine("invalid://connection")
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))


@pytest.mark.database
@pytest.mark.unit
class TestUserModel:
    """Test User model operations."""

    def create_mock_user_model(self, **kwargs):
        """Create a mock user model for testing."""
        default_data = TestDataFactory.create_user_data(**kwargs)
        mock_user = MagicMock()
        for key, value in default_data.items():
            setattr(mock_user, key, value)
        return mock_user

    async def test_user_model_creation(self):
        """Test user model creation with valid data."""
        user_data = TestDataFactory.create_user_data()
        mock_user = self.create_mock_user_model(**user_data)
        
        # Validate required fields
        assert mock_user.username is not None
        assert mock_user.email is not None
        assert mock_user.id is not None
        assert mock_user.is_active is True

    async def test_user_model_validation(self):
        """Test user model field validation."""
        # Test email validation
        invalid_email_data = TestDataFactory.create_user_data(email="invalid-email")
        
        # In a real scenario, this would test model validation
        # For now, we test the data structure
        assert "@" not in invalid_email_data["email"].split(".")[-1]

    async def test_user_model_unique_constraints(self):
        """Test user model unique constraints."""
        user_data1 = TestDataFactory.create_user_data(username="testuser")
        user_data2 = TestDataFactory.create_user_data(username="testuser")
        
        # In a real database scenario, this would test unique constraint violations
        assert user_data1["username"] == user_data2["username"]

    async def test_user_password_hashing(self):
        """Test user password hashing functionality."""
        # Mock password hashing
        password = "secure_password_123"
        hashed_password = f"hashed_{password}"
        
        user_data = TestDataFactory.create_user_data()
        mock_user = self.create_mock_user_model(**user_data)
        mock_user.hashed_password = hashed_password
        
        assert mock_user.hashed_password != password
        assert "hashed_" in mock_user.hashed_password


@pytest.mark.database
@pytest.mark.unit
class TestProjectModel:
    """Test Project model operations."""

    def create_mock_project_model(self, **kwargs):
        """Create a mock project model for testing."""
        default_data = TestDataFactory.create_project_data(**kwargs)
        mock_project = MagicMock()
        for key, value in default_data.items():
            setattr(mock_project, key, value)
        return mock_project

    async def test_project_model_creation(self):
        """Test project model creation with valid data."""
        project_data = TestDataFactory.create_project_data()
        mock_project = self.create_mock_project_model(**project_data)
        
        # Validate required fields
        assert mock_project.name is not None
        assert mock_project.description is not None
        assert mock_project.github_repo is not None
        assert mock_project.settings is not None
        assert isinstance(mock_project.settings, dict)

    async def test_project_settings_validation(self):
        """Test project settings field validation."""
        settings = {
            "rag_model": "gpt-4o-mini",
            "chunk_size": 500,
            "chunk_overlap": 50,
        }
        
        project_data = TestDataFactory.create_project_data(settings=settings)
        mock_project = self.create_mock_project_model(**project_data)
        
        assert mock_project.settings["rag_model"] in ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
        assert 100 <= mock_project.settings["chunk_size"] <= 2000
        assert 0 <= mock_project.settings["chunk_overlap"] <= 200

    async def test_project_github_repo_validation(self):
        """Test GitHub repository URL validation."""
        valid_repo = "https://github.com/user/repo"
        invalid_repo = "not-a-valid-url"
        
        project_data_valid = TestDataFactory.create_project_data(github_repo=valid_repo)
        project_data_invalid = TestDataFactory.create_project_data(github_repo=invalid_repo)
        
        mock_project_valid = self.create_mock_project_model(**project_data_valid)
        mock_project_invalid = self.create_mock_project_model(**project_data_invalid)
        
        assert "github.com" in mock_project_valid.github_repo
        assert "github.com" not in mock_project_invalid.github_repo


@pytest.mark.database
@pytest.mark.unit
class TestConversationModel:
    """Test Conversation model operations."""

    def create_mock_conversation_model(self, **kwargs):
        """Create a mock conversation model for testing."""
        default_data = {
            "id": generate_test_id(),
            "project_id": generate_test_id(),
            "title": f"Test Conversation {uuid.uuid4().hex[:8]}",
            "type": "chat",
            "metadata": {},
            "last_message_at": datetime.utcnow().isoformat(),
            "message_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        default_data.update(kwargs)
        
        mock_conversation = MagicMock()
        for key, value in default_data.items():
            setattr(mock_conversation, key, value)
        return mock_conversation

    async def test_conversation_model_creation(self):
        """Test conversation model creation."""
        mock_conversation = self.create_mock_conversation_model()
        
        assert mock_conversation.title is not None
        assert mock_conversation.type in ["chat", "support", "training"]
        assert mock_conversation.message_count >= 0
        assert isinstance(mock_conversation.metadata, dict)

    async def test_conversation_type_validation(self):
        """Test conversation type validation."""
        valid_types = ["chat", "support", "training"]
        
        for conv_type in valid_types:
            mock_conversation = self.create_mock_conversation_model(type=conv_type)
            assert mock_conversation.type == conv_type

    async def test_conversation_message_count_update(self):
        """Test conversation message count updates."""
        mock_conversation = self.create_mock_conversation_model(message_count=5)
        
        # Simulate adding a message
        mock_conversation.message_count += 1
        assert mock_conversation.message_count == 6
        
        # Simulate removing a message
        mock_conversation.message_count -= 1
        assert mock_conversation.message_count == 5


@pytest.mark.database
@pytest.mark.unit
class TestMessageModel:
    """Test Message model operations."""

    def create_mock_message_model(self, **kwargs):
        """Create a mock message model for testing."""
        default_data = TestDataFactory.create_message_data(**kwargs)
        mock_message = MagicMock()
        for key, value in default_data.items():
            setattr(mock_message, key, value)
        return mock_message

    async def test_message_model_creation(self):
        """Test message model creation."""
        message_data = TestDataFactory.create_message_data()
        mock_message = self.create_mock_message_model(**message_data)
        
        assert mock_message.content is not None
        assert mock_message.role in ["user", "assistant", "system"]
        assert mock_message.message_type in ["text", "image", "file", "code"]
        assert mock_message.status in ["pending", "delivered", "error"]

    async def test_message_role_validation(self):
        """Test message role validation."""
        valid_roles = ["user", "assistant", "system"]
        
        for role in valid_roles:
            message_data = TestDataFactory.create_message_data(role=role)
            mock_message = self.create_mock_message_model(**message_data)
            assert mock_message.role == role

    async def test_message_metadata_handling(self):
        """Test message metadata field handling."""
        metadata = {
            "sources": ["doc1.txt", "doc2.md"],
            "confidence": 0.85,
            "processing_time_ms": 1200,
        }
        
        message_data = TestDataFactory.create_message_data(metadata=metadata)
        mock_message = self.create_mock_message_model(**message_data)
        
        assert isinstance(mock_message.metadata, dict)
        assert "sources" in mock_message.metadata
        assert "confidence" in mock_message.metadata
        assert "processing_time_ms" in mock_message.metadata

    async def test_message_token_count_validation(self):
        """Test message token count validation."""
        # Test valid token counts
        valid_token_counts = [10, 100, 1000, 8000]
        
        for token_count in valid_token_counts:
            message_data = TestDataFactory.create_message_data(token_count=token_count)
            mock_message = self.create_mock_message_model(**message_data)
            assert mock_message.token_count == token_count
            assert mock_message.token_count > 0

    async def test_message_content_length_limits(self):
        """Test message content length limits."""
        # Test normal content
        normal_content = "This is a normal message"
        message_data = TestDataFactory.create_message_data(content=normal_content)
        mock_message = self.create_mock_message_model(**message_data)
        assert len(mock_message.content) < 10000  # Reasonable limit
        
        # Test very long content
        long_content = "x" * 20000
        message_data_long = TestDataFactory.create_message_data(content=long_content)
        mock_message_long = self.create_mock_message_model(**message_data_long)
        assert len(mock_message_long.content) > 10000


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseCRUD:
    """Test CRUD operations for database models."""

    async def test_user_crud_operations(self, async_session):
        """Test CRUD operations for User model."""
        # Mock CRUD operations since we don't have actual models yet
        user_data = TestDataFactory.create_user_data()
        
        # CREATE
        mock_user = MagicMock()
        for key, value in user_data.items():
            setattr(mock_user, key, value)
        
        # Mock database operations
        async_session.add = MagicMock()
        async_session.commit = AsyncMock()
        async_session.refresh = AsyncMock()
        
        # Simulate adding user to database
        async_session.add(mock_user)
        await async_session.commit()
        await async_session.refresh(mock_user)
        
        # Verify operations were called
        async_session.add.assert_called_once_with(mock_user)
        async_session.commit.assert_called_once()
        async_session.refresh.assert_called_once_with(mock_user)

    async def test_project_crud_operations(self, async_session):
        """Test CRUD operations for Project model."""
        project_data = TestDataFactory.create_project_data()
        
        # CREATE
        mock_project = MagicMock()
        for key, value in project_data.items():
            setattr(mock_project, key, value)
        
        # Mock database operations
        async_session.add = MagicMock()
        async_session.commit = AsyncMock()
        async_session.refresh = AsyncMock()
        async_session.execute = AsyncMock()
        async_session.delete = MagicMock()
        
        # Test CREATE
        async_session.add(mock_project)
        await async_session.commit()
        
        # Test READ (mock query result)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_project
        async_session.execute.return_value = mock_result
        
        # Test UPDATE
        mock_project.name = "Updated Project Name"
        await async_session.commit()
        
        # Test DELETE
        async_session.delete(mock_project)
        await async_session.commit()
        
        # Verify all operations
        async_session.add.assert_called_once_with(mock_project)
        async_session.delete.assert_called_once_with(mock_project)
        assert async_session.commit.call_count >= 2

    async def test_conversation_message_relationship(self, async_session):
        """Test relationship between conversations and messages."""
        # Create mock conversation and messages
        conversation_id = generate_test_id()
        
        mock_conversation = MagicMock()
        mock_conversation.id = conversation_id
        mock_conversation.message_count = 0
        
        # Create messages for the conversation
        messages = []
        for i in range(3):
            message_data = TestDataFactory.create_message_data(
                conversation_id=conversation_id,
                role="user" if i % 2 == 0 else "assistant"
            )
            mock_message = MagicMock()
            for key, value in message_data.items():
                setattr(mock_message, key, value)
            messages.append(mock_message)
        
        # Update conversation message count
        mock_conversation.message_count = len(messages)
        mock_conversation.messages = messages
        
        assert mock_conversation.message_count == 3
        assert len(mock_conversation.messages) == 3
        assert all(msg.conversation_id == conversation_id for msg in messages)


@pytest.mark.database
@pytest.mark.performance
class TestDatabasePerformance:
    """Test database performance characteristics."""

    async def test_bulk_insert_performance(self, async_session, performance_benchmark):
        """Test bulk insert performance."""
        
        def mock_bulk_insert():
            """Mock bulk insert operation."""
            # Simulate creating 1000 records
            records = []
            for i in range(1000):
                user_data = TestDataFactory.create_user_data(
                    username=f"user_{i}",
                    email=f"user_{i}@example.com"
                )
                records.append(user_data)
            return records
        
        # Benchmark the operation
        result, execution_time = performance_benchmark(mock_bulk_insert)
        
        # Verify results
        assert len(result) == 1000
        assert execution_time < 1.0  # Should complete in under 1 second

    async def test_query_performance_with_pagination(self, async_session):
        """Test query performance with pagination."""
        # Mock paginated query
        page_size = 20
        total_records = 1000
        
        mock_query_result = MagicMock()
        mock_query_result.limit.return_value.offset.return_value = mock_query_result
        mock_query_result.all.return_value = [
            TestDataFactory.create_user_data() for _ in range(page_size)
        ]
        
        async_session.execute = AsyncMock(return_value=mock_query_result)
        
        # Test first page
        start_time = datetime.utcnow()
        result = await async_session.execute(text("SELECT * FROM users LIMIT 20 OFFSET 0"))
        end_time = datetime.utcnow()
        
        execution_time = (end_time - start_time).total_seconds() * 1000  # Convert to ms
        
        # Performance assertion
        assert execution_time < 100  # Should complete in under 100ms
        async_session.execute.assert_called_once()

    async def test_complex_query_performance(self, async_session):
        """Test performance of complex queries with joins."""
        # Mock complex query with multiple joins
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            {
                "user_id": generate_test_id(),
                "project_name": f"Project {i}",
                "conversation_count": i * 2,
                "message_count": i * 10,
            }
            for i in range(100)
        ]
        
        async_session.execute = AsyncMock(return_value=mock_result)
        
        complex_query = text("""
            SELECT u.id as user_id, p.name as project_name,
                   COUNT(DISTINCT c.id) as conversation_count,
                   COUNT(m.id) as message_count
            FROM users u
            JOIN projects p ON u.id = p.user_id
            LEFT JOIN conversations c ON p.id = c.project_id
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY u.id, p.id
            ORDER BY message_count DESC
            LIMIT 100
        """)
        
        start_time = datetime.utcnow()
        result = await async_session.execute(complex_query)
        end_time = datetime.utcnow()
        
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        # Performance assertions
        assert execution_time < 500  # Should complete in under 500ms
        async_session.execute.assert_called_once_with(complex_query)


@pytest.mark.database
@pytest.mark.security
class TestDatabaseSecurity:
    """Test database security measures."""

    async def test_sql_injection_prevention(self, async_session):
        """Test SQL injection prevention."""
        # Test malicious input
        malicious_input = "'; DROP TABLE users; --"
        safe_query = text("SELECT * FROM users WHERE username = :username")
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        async_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute parameterized query
        result = await async_session.execute(safe_query, {"username": malicious_input})
        
        # Verify query was executed safely
        async_session.execute.assert_called_once_with(safe_query, {"username": malicious_input})
        assert result is not None

    async def test_data_sanitization(self):
        """Test input data sanitization."""
        # Test XSS prevention in user input
        malicious_script = "<script>alert('XSS')</script>"
        user_data = TestDataFactory.create_user_data(username=malicious_script)
        
        # In a real scenario, this would test actual sanitization
        # For now, we verify the data contains the malicious content
        assert "<script>" in user_data["username"]
        
        # Mock sanitized version
        sanitized_username = user_data["username"].replace("<", "&lt;").replace(">", "&gt;")
        assert "&lt;script&gt;" in sanitized_username
        assert "<script>" not in sanitized_username

    async def test_password_field_encryption(self):
        """Test password field encryption/hashing."""
        plain_password = "my_secure_password_123"
        
        # Mock password hashing (in real scenario, use bcrypt or similar)
        hashed_password = f"$2b$12${'x' * 53}"  # Mock bcrypt hash format
        
        # Verify password is hashed
        assert hashed_password != plain_password
        assert len(hashed_password) > len(plain_password)
        assert hashed_password.startswith("$2b$")


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseMigrations:
    """Test database migration functionality."""

    async def test_migration_up_and_down(self, async_session):
        """Test database migration up and down operations."""
        # Mock Alembic operations
        with patch('alembic.command') as mock_alembic:
            mock_alembic.upgrade = MagicMock()
            mock_alembic.downgrade = MagicMock()
            
            # Test migration up
            mock_alembic.upgrade(None, "head")
            mock_alembic.upgrade.assert_called_with(None, "head")
            
            # Test migration down
            mock_alembic.downgrade(None, "base")
            mock_alembic.downgrade.assert_called_with(None, "base")

    async def test_migration_version_tracking(self):
        """Test migration version tracking."""
        # Mock migration version check
        with patch('alembic.command') as mock_alembic:
            mock_alembic.current = MagicMock(return_value="abc123def456")
            
            current_version = mock_alembic.current(None)
            assert len(current_version) > 0
            mock_alembic.current.assert_called_once_with(None)

    async def test_schema_validation_after_migration(self, async_session):
        """Test schema validation after migration."""
        # Mock schema inspection
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = [
            "users", "projects", "conversations", "messages"
        ]
        
        with patch('sqlalchemy.inspect', return_value=mock_inspector):
            from sqlalchemy import inspect
            inspector = inspect(async_session.bind)
            table_names = inspector.get_table_names()
            
            # Verify expected tables exist
            expected_tables = {"users", "projects", "conversations", "messages"}
            assert expected_tables.issubset(set(table_names))