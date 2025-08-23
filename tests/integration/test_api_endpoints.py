"""
Integration tests for FastAPI endpoints.

Tests the complete API functionality including request/response handling,
authentication, validation, and integration with backend services.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import json
from typing import Dict, List

# Note: These imports will be updated when actual API is implemented
# from src.main import app
# from src.api.models import ProjectCreate, ConversationCreate, MessageCreate


class TestHealthEndpoints:
    """Test health check and status endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_health_check(self, async_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_health_check_with_dependencies(self, async_client: AsyncClient):
        """Test health check that includes dependency status."""
        # This would test a more comprehensive health check
        # that verifies database, vector store, and external API connectivity
        pass


class TestProjectEndpoints:
    """Test project management API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.database
    async def test_create_project(self, async_client: AsyncClient, async_session):
        """Test project creation endpoint."""
        project_data = {
            "name": "Test Project",
            "description": "A test project for API testing",
            "github_repo": "https://github.com/user/test-repo",
            "settings": {
                "rag_model": "gpt-4o-mini",
                "chunk_size": 500,
                "chunk_overlap": 50
            }
        }
        
        response = await async_client.post("/api/projects", json=project_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["github_repo"] == project_data["github_repo"]
        assert "id" in data
        assert "created_at" in data
        assert "vector_collection_name" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_create_project_validation_errors(self, async_client: AsyncClient):
        """Test project creation with invalid data."""
        invalid_projects = [
            {},  # Missing required fields
            {"name": ""},  # Empty name
            {"name": "x" * 101},  # Name too long
            {"name": "Valid Name", "github_repo": "invalid-url"},  # Invalid URL
        ]
        
        for invalid_data in invalid_projects:
            response = await async_client.post("/api/projects", json=invalid_data)
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_get_project(self, async_client: AsyncClient, sample_project):
        """Test retrieving a specific project."""
        project_id = sample_project["id"]
        
        response = await async_client.get(f"/api/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == sample_project["name"]
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_get_nonexistent_project(self, async_client: AsyncClient):
        """Test retrieving a project that doesn't exist."""
        response = await async_client.get("/api/projects/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_list_projects(self, async_client: AsyncClient):
        """Test listing all projects."""
        response = await async_client.get("/api/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Additional assertions based on test data setup
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_update_project(self, async_client: AsyncClient, sample_project):
        """Test updating project information."""
        project_id = sample_project["id"]
        update_data = {
            "description": "Updated description",
            "settings": {
                "rag_model": "gpt-4",
                "chunk_size": 750
            }
        }
        
        response = await async_client.patch(f"/api/projects/{project_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["settings"]["rag_model"] == "gpt-4"
        assert data["settings"]["chunk_size"] == 750
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_delete_project(self, async_client: AsyncClient, sample_project):
        """Test project deletion."""
        project_id = sample_project["id"]
        
        response = await async_client.delete(f"/api/projects/{project_id}")
        
        assert response.status_code == 204
        
        # Verify project is actually deleted
        get_response = await async_client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404


class TestConversationEndpoints:
    """Test conversation management API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_create_conversation(self, async_client: AsyncClient, sample_project):
        """Test conversation creation."""
        conversation_data = {
            "project_id": sample_project["id"],
            "title": "Test Conversation",
            "type": "chat",
            "metadata": {"topic": "testing"}
        }
        
        response = await async_client.post("/api/conversations", json=conversation_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == conversation_data["title"]
        assert data["project_id"] == sample_project["id"]
        assert data["type"] == "chat"
        assert "id" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_get_conversation(self, async_client: AsyncClient, sample_conversation):
        """Test retrieving a conversation."""
        conversation_id = sample_conversation["id"]
        
        response = await async_client.get(f"/api/conversations/{conversation_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == sample_conversation["title"]
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_list_conversations_by_project(self, async_client: AsyncClient, sample_project):
        """Test listing conversations for a project."""
        project_id = sample_project["id"]
        
        response = await async_client.get(f"/api/projects/{project_id}/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All conversations should belong to the project
        for conv in data:
            assert conv["project_id"] == project_id
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_update_conversation(self, async_client: AsyncClient, sample_conversation):
        """Test updating conversation information."""
        conversation_id = sample_conversation["id"]
        update_data = {
            "title": "Updated Conversation Title",
            "type": "archived"
        }
        
        response = await async_client.patch(f"/api/conversations/{conversation_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["type"] == "archived"


class TestMessageEndpoints:
    """Test message handling API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.rag
    async def test_send_message(self, async_client: AsyncClient, sample_conversation, mock_openai_client):
        """Test sending a message and receiving AI response."""
        with patch('src.core.rag_system.ChatOpenAI') as mock_llm:
            mock_llm.return_value.ainvoke.return_value.content = "AI response to the message"
            
            message_data = {
                "conversation_id": sample_conversation["id"],
                "content": "Hello, AI assistant! How are you?",
                "role": "user"
            }
            
            response = await async_client.post("/api/messages", json=message_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["content"] == message_data["content"]
            assert data["role"] == "user"
            assert data["conversation_id"] == sample_conversation["id"]
            assert "id" in data
            assert "created_at" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_get_messages_for_conversation(self, async_client: AsyncClient, sample_conversation):
        """Test retrieving messages for a conversation."""
        conversation_id = sample_conversation["id"]
        
        response = await async_client.get(f"/api/conversations/{conversation_id}/messages")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All messages should belong to the conversation
        for msg in data:
            assert msg["conversation_id"] == conversation_id
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_message_pagination(self, async_client: AsyncClient, sample_conversation):
        """Test message pagination for conversations with many messages."""
        conversation_id = sample_conversation["id"]
        
        # Test with pagination parameters
        response = await async_client.get(
            f"/api/conversations/{conversation_id}/messages",
            params={"limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_message_search(self, async_client: AsyncClient, sample_conversation):
        """Test searching messages within a conversation."""
        conversation_id = sample_conversation["id"]
        search_query = "test query"
        
        response = await async_client.get(
            f"/api/conversations/{conversation_id}/messages/search",
            params={"q": search_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDocumentEndpoints:
    """Test document upload and processing endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.rag
    async def test_upload_document(self, async_client: AsyncClient, sample_project, temp_dir):
        """Test document upload to a project."""
        # Create a test file
        test_file = temp_dir / "test_document.txt"
        test_file.write_text("This is a test document for upload.")
        
        project_id = sample_project["id"]
        
        with open(test_file, "rb") as f:
            response = await async_client.post(
                f"/api/projects/{project_id}/documents",
                files={"file": ("test_document.txt", f, "text/plain")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_document.txt"
        assert data["project_id"] == project_id
        assert "id" in data
        assert "processing_status" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_upload_multiple_documents(self, async_client: AsyncClient, sample_project, temp_dir):
        """Test uploading multiple documents at once."""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = temp_dir / f"test_doc_{i}.txt"
            test_file.write_text(f"This is test document {i}.")
            files.append(("files", (f"test_doc_{i}.txt", open(test_file, "rb"), "text/plain")))
        
        project_id = sample_project["id"]
        
        try:
            response = await async_client.post(
                f"/api/projects/{project_id}/documents/bulk",
                files=files
            )
            
            assert response.status_code == 201
            data = response.json()
            assert len(data) == 3
            assert all(doc["project_id"] == project_id for doc in data)
        finally:
            # Clean up file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_list_project_documents(self, async_client: AsyncClient, sample_project):
        """Test listing documents for a project."""
        project_id = sample_project["id"]
        
        response = await async_client.get(f"/api/projects/{project_id}/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_delete_document(self, async_client: AsyncClient, sample_project):
        """Test deleting a document from a project."""
        # This test would require setting up a document first
        pass
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_document_processing_status(self, async_client: AsyncClient, sample_project):
        """Test checking document processing status."""
        # This test would check the status of document processing
        pass


class TestGitHubIntegrationEndpoints:
    """Test GitHub integration API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.requires_github
    async def test_clone_github_repository(self, async_client: AsyncClient, sample_project, mock_github_client):
        """Test cloning a GitHub repository into a project."""
        with patch('src.integrations.github.GitHubClient') as mock_client:
            mock_client.return_value = mock_github_client
            
            project_id = sample_project["id"]
            repo_data = {
                "repository_url": "https://github.com/user/test-repo",
                "include_patterns": ["*.py", "*.md"],
                "exclude_patterns": ["*.pyc", "__pycache__"]
            }
            
            response = await async_client.post(
                f"/api/projects/{project_id}/github/clone",
                json=repo_data
            )
            
            assert response.status_code == 202  # Accepted for processing
            data = response.json()
            assert "task_id" in data
            assert data["status"] == "processing"
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.requires_github
    async def test_sync_github_repository(self, async_client: AsyncClient, sample_project):
        """Test syncing changes from GitHub repository."""
        project_id = sample_project["id"]
        
        response = await async_client.post(f"/api/projects/{project_id}/github/sync")
        
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_github_webhook_handler(self, async_client: AsyncClient):
        """Test GitHub webhook for automatic repository updates."""
        webhook_payload = {
            "action": "push",
            "repository": {
                "full_name": "user/test-repo",
                "clone_url": "https://github.com/user/test-repo.git"
            },
            "commits": [
                {
                    "id": "abc123",
                    "message": "Update documentation",
                    "added": ["README.md"],
                    "modified": ["docs/guide.md"],
                    "removed": []
                }
            ]
        }
        
        response = await async_client.post("/api/webhooks/github", json=webhook_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"


class TestWebSocketEndpoints:
    """Test WebSocket functionality for real-time chat."""
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.slow
    async def test_websocket_connection(self, async_client: AsyncClient, sample_project, sample_conversation):
        """Test establishing WebSocket connection for chat."""
        project_id = sample_project["id"]
        conversation_id = sample_conversation["id"]
        
        async with async_client.websocket_connect(f"/ws/{project_id}/{conversation_id}") as websocket:
            # Test connection is established
            assert websocket.client_state == "CONNECTED"
            
            # Send a test message
            await websocket.send_json({
                "type": "chat_message",
                "content": "Hello via WebSocket!",
                "timestamp": "2024-01-01T12:00:00Z"
            })
            
            # Receive response
            response = await websocket.receive_json()
            assert response["type"] == "message"
            assert "content" in response
            assert "timestamp" in response
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_websocket_authentication(self, async_client: AsyncClient):
        """Test WebSocket authentication and authorization."""
        # Test connection with invalid credentials
        pass
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_websocket_error_handling(self, async_client: AsyncClient, sample_project, sample_conversation):
        """Test WebSocket error handling."""
        project_id = sample_project["id"]
        conversation_id = sample_conversation["id"]
        
        async with async_client.websocket_connect(f"/ws/{project_id}/{conversation_id}") as websocket:
            # Send invalid message format
            await websocket.send_json({"invalid": "message"})
            
            # Should receive error response
            response = await websocket.receive_json()
            assert response["type"] == "error"
            assert "message" in response


class TestErrorHandling:
    """Test API error handling and responses."""
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_404_error_handling(self, async_client: AsyncClient):
        """Test 404 error responses."""
        response = await async_client.get("/api/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_validation_error_responses(self, async_client: AsyncClient):
        """Test validation error responses with detailed field information."""
        invalid_data = {
            "name": "",  # Required field empty
            "invalid_field": "value"  # Unknown field
        }
        
        response = await async_client.post("/api/projects", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_internal_server_error_handling(self, async_client: AsyncClient):
        """Test internal server error handling."""
        # This would test scenarios that cause 500 errors
        # and verify they're handled gracefully
        pass
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_rate_limiting(self, async_client: AsyncClient):
        """Test API rate limiting."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for _ in range(100):  # Exceed rate limit
            response = await async_client.get("/health")
            responses.append(response)
        
        # Some requests should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests


class TestAPIPerformance:
    """Test API performance characteristics."""
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_endpoint_response_times(self, async_client: AsyncClient, performance_benchmark):
        """Test that API endpoints respond within acceptable time limits."""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/projects"),
        ]
        
        for method, endpoint in endpoints:
            async def make_request():
                if method == "GET":
                    return await async_client.get(endpoint)
                elif method == "POST":
                    return await async_client.post(endpoint, json={})
            
            result, execution_time = performance_benchmark(make_request)
            assert execution_time < 1.0  # Should respond within 1 second
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.performance
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """Test API handling of concurrent requests."""
        import asyncio
        
        # Make multiple concurrent requests
        tasks = [async_client.get("/health") for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.performance
    async def test_large_payload_handling(self, async_client: AsyncClient, sample_project):
        """Test handling of large request payloads."""
        # Create a large message
        large_content = "x" * 10000  # 10KB message
        
        message_data = {
            "conversation_id": 1,
            "content": large_content,
            "role": "user"
        }
        
        response = await async_client.post("/api/messages", json=message_data)
        
        # Should handle large payloads appropriately
        assert response.status_code in [201, 413]  # Created or Payload Too Large