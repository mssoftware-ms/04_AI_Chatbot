"""
Global pytest configuration and fixtures for WhatsApp AI Chatbot testing.

This module provides common fixtures, test utilities, and configuration
that are shared across all test modules.
"""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test environment configuration
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["VECTOR_DATABASE_PATH"] = "./test_vector_db"
os.environ["LOG_LEVEL"] = "DEBUG"

# Disable OpenAI API calls during testing by default
os.environ["OPENAI_API_KEY"] = "test-key-not-real"
os.environ["GITHUB_TOKEN"] = "test-token-not-real"

fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config() -> Dict:
    """Provide test configuration settings."""
    return {
        "database": {
            "url": "sqlite:///./test.db",
            "echo": False,
        },
        "vector_db": {
            "path": "./test_vector_db",
            "collection_name": "test_collection",
        },
        "openai": {
            "api_key": "test-key",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 1000,
        },
        "github": {
            "token": "test-token",
            "base_url": "https://api.github.com",
        },
        "app": {
            "debug": True,
            "testing": True,
            "host": "127.0.0.1",
            "port": 8000,
        },
    }


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for testing."""
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Import and create tables
    # Note: This will be updated when actual models are created
    # from src.database.models import Base
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = AsyncMock()
    
    # Mock chat completion
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test AI response."
    mock_response.usage.total_tokens = 50
    mock_client.chat.completions.create.return_value = mock_response
    
    # Mock embeddings
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = [0.1] * 1536  # OpenAI embedding size
    mock_client.embeddings.create.return_value = mock_embedding_response
    
    return mock_client


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client for testing."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Mock collection operations
    mock_collection.add.return_value = None
    mock_collection.query.return_value = {
        "documents": [["Test document 1", "Test document 2"]],
        "metadatas": [[{"source": "test1.txt"}, {"source": "test2.txt"}]],
        "distances": [[0.1, 0.2]],
        "ids": [["doc1", "doc2"]],
    }
    mock_collection.count.return_value = 2
    
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client.get_collection.return_value = mock_collection
    mock_client.list_collections.return_value = [mock_collection]
    
    return mock_client


@pytest.fixture
def mock_github_client():
    """Mock GitHub API client for testing."""
    mock_client = MagicMock()
    
    # Mock repository data
    mock_repo = MagicMock()
    mock_repo.name = "test-repo"
    mock_repo.full_name = "user/test-repo"
    mock_repo.description = "Test repository"
    mock_repo.clone_url = "https://github.com/user/test-repo.git"
    
    # Mock file content
    mock_content = MagicMock()
    mock_content.decoded_content = b"# Test File\nThis is test content."
    mock_content.name = "README.md"
    mock_content.path = "README.md"
    
    mock_client.get_repo.return_value = mock_repo
    mock_client.get_contents.return_value = [mock_content]
    
    return mock_client


@pytest.fixture
async def test_app():
    """Create a test FastAPI application instance."""
    # Note: This will be implemented when the actual app is created
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI(title="Test WhatsApp AI Chatbot")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "testing": True}
    
    return app


@pytest.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing FastAPI endpoints."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_documents() -> List[Dict]:
    """Generate sample documents for testing."""
    return [
        {
            "id": str(uuid.uuid4()),
            "content": fake.text(max_nb_chars=1000),
            "metadata": {
                "source": "test_doc_1.txt",
                "type": "text",
                "created_at": fake.date_time().isoformat(),
            },
        },
        {
            "id": str(uuid.uuid4()),
            "content": fake.text(max_nb_chars=800),
            "metadata": {
                "source": "test_doc_2.md",
                "type": "markdown",
                "created_at": fake.date_time().isoformat(),
            },
        },
        {
            "id": str(uuid.uuid4()),
            "content": "# Code Example\n\ndef hello_world():\n    print('Hello, World!')",
            "metadata": {
                "source": "example.py",
                "type": "code",
                "language": "python",
                "created_at": fake.date_time().isoformat(),
            },
        },
    ]


@pytest.fixture
def sample_project() -> Dict:
    """Generate a sample project for testing."""
    return {
        "id": 1,
        "name": fake.company(),
        "description": fake.text(max_nb_chars=200),
        "github_repo": f"https://github.com/{fake.user_name()}/{fake.word()}",
        "settings": {
            "rag_model": "gpt-4o-mini",
            "chunk_size": 500,
            "chunk_overlap": 50,
        },
        "vector_collection_name": f"project_1",
        "created_at": fake.date_time().isoformat(),
    }


@pytest.fixture
def sample_conversation() -> Dict:
    """Generate a sample conversation for testing."""
    return {
        "id": 1,
        "project_id": 1,
        "title": fake.sentence(nb_words=4),
        "type": "chat",
        "metadata": {},
        "last_message_at": fake.date_time().isoformat(),
        "message_count": fake.random_int(min=1, max=50),
        "created_at": fake.date_time().isoformat(),
    }


@pytest.fixture
def sample_messages() -> List[Dict]:
    """Generate sample messages for testing."""
    return [
        {
            "id": 1,
            "conversation_id": 1,
            "role": "user",
            "content": fake.question(),
            "message_type": "text",
            "status": "delivered",
            "metadata": {},
            "token_count": fake.random_int(min=10, max=100),
            "created_at": fake.date_time().isoformat(),
        },
        {
            "id": 2,
            "conversation_id": 1,
            "role": "assistant",
            "content": fake.text(max_nb_chars=500),
            "message_type": "text",
            "status": "delivered",
            "metadata": {
                "sources": ["doc1.txt", "doc2.md"],
                "confidence": 0.85,
                "processing_time_ms": 1200,
            },
            "token_count": fake.random_int(min=50, max=200),
            "processing_time_ms": fake.random_int(min=500, max=3000),
            "created_at": fake.date_time().isoformat(),
        },
    ]


@pytest.fixture
def mock_file_watcher():
    """Mock file watcher for testing."""
    mock_watcher = MagicMock()
    mock_watcher.start.return_value = None
    mock_watcher.stop.return_value = None
    mock_watcher.is_running = True
    return mock_watcher


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    
    # Cleanup test database files
    test_db_files = ["test.db", "test.db-shm", "test.db-wal"]
    for db_file in test_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except OSError:
                pass
    
    # Cleanup test vector database
    if os.path.exists("./test_vector_db"):
        import shutil
        try:
            shutil.rmtree("./test_vector_db")
        except OSError:
            pass


@pytest.fixture
def performance_benchmark():
    """Fixture for performance benchmarking."""
    def _benchmark(func, *args, **kwargs):
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    return _benchmark


# Custom pytest markers for test categorization
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as a database test"
    )
    config.addinivalue_line(
        "markers", "rag: mark test as a RAG system test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "fast: mark test as fast running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add markers based on test file location
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "ui/" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        
        # Add slow marker for tests that might take longer
        if any(keyword in item.name.lower() for keyword in ["load", "stress", "benchmark"]):
            item.add_marker(pytest.mark.slow)