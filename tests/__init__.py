"""
WhatsApp AI Chatbot Testing Framework

This package contains comprehensive tests for the WhatsApp AI Chatbot application,
including unit tests, integration tests, performance benchmarks, and UI tests.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interaction
- performance/: Performance and benchmark tests
- ui/: User interface tests
- fixtures/: Test data and shared fixtures

Usage:
    # Run all tests
    pytest
    
    # Run specific test categories
    pytest -m unit
    pytest -m integration
    pytest -m api
    pytest -m database
    pytest -m rag
    pytest -m performance
    
    # Run with coverage
    pytest --cov=src --cov-report=html
    
    # Run in parallel
    pytest -n auto
"""

__version__ = "1.0.0"
__author__ = "WhatsApp AI Chatbot Team"

# Test configuration
TEST_CONFIG = {
    "database_url": "sqlite:///./test.db",
    "vector_db_path": "./test_vector_db",
    "test_timeout": 300,
    "coverage_threshold": 80,
    "performance_baseline_ms": 1000,
}

# Common test utilities
from typing import Any, Dict, List, Optional
import uuid
import asyncio
from unittest.mock import MagicMock, AsyncMock


def generate_test_id() -> str:
    """Generate a unique test ID."""
    return str(uuid.uuid4())


def create_mock_response(data: Any, status_code: int = 200) -> MagicMock:
    """Create a mock HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = data
    mock_response.text = str(data)
    return mock_response


def create_async_mock_response(data: Any, status_code: int = 200) -> AsyncMock:
    """Create an async mock HTTP response."""
    mock_response = AsyncMock()
    mock_response.status_code = status_code
    mock_response.json = AsyncMock(return_value=data)
    mock_response.text = str(data)
    return mock_response


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_user_data(**overrides) -> Dict[str, Any]:
        """Create test user data."""
        default_data = {
            "id": generate_test_id(),
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
        }
        default_data.update(overrides)
        return default_data
    
    @staticmethod
    def create_project_data(**overrides) -> Dict[str, Any]:
        """Create test project data."""
        default_data = {
            "id": generate_test_id(),
            "name": f"Test Project {uuid.uuid4().hex[:8]}",
            "description": "A test project for automated testing",
            "github_repo": f"https://github.com/test/project-{uuid.uuid4().hex[:8]}",
            "settings": {
                "rag_model": "gpt-4o-mini",
                "chunk_size": 500,
                "chunk_overlap": 50,
            },
            "created_at": "2024-01-01T00:00:00Z",
        }
        default_data.update(overrides)
        return default_data
    
    @staticmethod
    def create_message_data(**overrides) -> Dict[str, Any]:
        """Create test message data."""
        default_data = {
            "id": generate_test_id(),
            "conversation_id": generate_test_id(),
            "role": "user",
            "content": "This is a test message",
            "message_type": "text",
            "status": "delivered",
            "metadata": {},
            "token_count": 10,
            "created_at": "2024-01-01T00:00:00Z",
        }
        default_data.update(overrides)
        return default_data


# Test markers for easy categorization
class TestMarkers:
    """Test markers for categorizing tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    API = "api"
    DATABASE = "database"
    RAG = "rag"
    UI = "ui"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SLOW = "slow"
    FAST = "fast"
    REQUIRES_OPENAI = "requires_openai"
    REQUIRES_GITHUB = "requires_github"
    REQUIRES_NETWORK = "requires_network"


# Performance testing utilities
class PerformanceAssertions:
    """Utilities for performance testing assertions."""
    
    @staticmethod
    def assert_response_time(actual_ms: float, expected_ms: float, tolerance: float = 0.1):
        """Assert that response time is within acceptable range."""
        max_allowed = expected_ms * (1 + tolerance)
        assert actual_ms <= max_allowed, (
            f"Response time {actual_ms}ms exceeds maximum allowed {max_allowed}ms "
            f"(expected: {expected_ms}ms, tolerance: {tolerance*100}%)"
        )
    
    @staticmethod
    def assert_memory_usage(actual_mb: float, expected_mb: float, tolerance: float = 0.2):
        """Assert that memory usage is within acceptable range."""
        max_allowed = expected_mb * (1 + tolerance)
        assert actual_mb <= max_allowed, (
            f"Memory usage {actual_mb}MB exceeds maximum allowed {max_allowed}MB "
            f"(expected: {expected_mb}MB, tolerance: {tolerance*100}%)"
        )


# Database testing utilities
class DatabaseTestUtils:
    """Utilities for database testing."""
    
    @staticmethod
    async def clean_database(session):
        """Clean all data from test database."""
        # This will be implemented when actual models are created
        pass
    
    @staticmethod
    async def seed_test_data(session, data_type: str, count: int = 5):
        """Seed database with test data."""
        # This will be implemented when actual models are created
        pass


__all__ = [
    "TEST_CONFIG",
    "generate_test_id",
    "create_mock_response",
    "create_async_mock_response",
    "TestDataFactory",
    "TestMarkers",
    "PerformanceAssertions",
    "DatabaseTestUtils",
]