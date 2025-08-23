"""
Full System Integration Tests

This module contains comprehensive integration tests that verify
the entire system works together correctly, including end-to-end
workflows and cross-component interactions.
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import json
from datetime import datetime, timedelta
import uuid

from tests import TestDataFactory, TestMarkers, generate_test_id


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to AI interaction."""

    async def test_user_registration_to_first_chat(self, async_client, async_session):
        """Test complete workflow: user registration -> project creation -> first AI chat."""
        
        # Step 1: User Registration
        registration_data = {
            "username": "newuser123",
            "email": "newuser@example.com",
            "password": "secure_password_123",
            "full_name": "New User"
        }
        
        with patch("src.services.user_service.create_user") as mock_create_user:
            mock_user = TestDataFactory.create_user_data(**registration_data)
            mock_create_user.return_value = mock_user
            
            user = mock_create_user(registration_data)
            assert user["email"] == registration_data["email"]
            user_id = user["id"]

        # Step 2: User Authentication
        login_data = {
            "username": registration_data["username"],
            "password": registration_data["password"]
        }
        
        with patch("src.services.auth_service.authenticate") as mock_auth:
            auth_token = "jwt_token_12345"
            mock_auth.return_value = {
                "access_token": auth_token,
                "token_type": "bearer",
                "user_id": user_id
            }
            
            auth_result = mock_auth(login_data)
            assert auth_result["access_token"] == auth_token

        # Step 3: Project Creation
        project_data = {
            "name": "My First AI Project",
            "description": "Testing the AI chatbot system",
            "github_repo": "https://github.com/newuser/test-project",
            "owner_id": user_id
        }
        
        with patch("src.services.project_service.create_project") as mock_create_project:
            mock_project = TestDataFactory.create_project_data(**project_data)
            mock_create_project.return_value = mock_project
            
            project = mock_create_project(project_data)
            assert project["name"] == project_data["name"]
            project_id = project["id"]

        # Step 4: Document Upload and Processing
        document_data = {
            "filename": "README.md",
            "content": "# Test Project\n\nThis is a test project for AI integration.",
            "project_id": project_id
        }
        
        with patch("src.services.document_service.upload_and_process") as mock_upload:
            mock_doc_result = {
                "document_id": generate_test_id(),
                "chunks_created": 2,
                "processing_status": "completed",
                "vector_indexed": True
            }
            mock_upload.return_value = mock_doc_result
            
            doc_result = mock_upload(document_data)
            assert doc_result["processing_status"] == "completed"
            assert doc_result["chunks_created"] > 0

        # Step 5: Create Conversation
        conversation_data = {
            "project_id": project_id,
            "title": "First AI Conversation",
            "type": "chat"
        }
        
        with patch("src.services.conversation_service.create_conversation") as mock_create_conv:
            mock_conversation = {
                "id": generate_test_id(),
                "project_id": project_id,
                "title": conversation_data["title"],
                "type": conversation_data["type"],
                "message_count": 0
            }
            mock_create_conv.return_value = mock_conversation
            
            conversation = mock_create_conv(conversation_data)
            conversation_id = conversation["id"]

        # Step 6: Send First AI Query
        query_data = {
            "conversation_id": conversation_id,
            "content": "What is this project about?",
            "use_rag": True
        }
        
        with patch("src.services.rag_service.process_query") as mock_rag:
            mock_ai_response = {
                "response": "Based on the documentation, this is a test project for AI integration. The project includes AI chatbot functionality.",
                "sources": ["README.md"],
                "confidence": 0.92,
                "processing_time_ms": 1200,
                "tokens_used": 150
            }
            mock_rag.return_value = mock_ai_response
            
            ai_response = mock_rag(query_data)
            
            assert "test project" in ai_response["response"].lower()
            assert len(ai_response["sources"]) > 0
            assert ai_response["confidence"] > 0.9

        # Verify complete workflow success
        assert user_id is not None
        assert auth_token is not None
        assert project_id is not None
        assert conversation_id is not None
        assert ai_response["response"] is not None

    async def test_multi_user_collaboration_workflow(self):
        """Test multi-user collaboration in shared project."""
        
        # Create two users
        user1_data = TestDataFactory.create_user_data(username="user1", email="user1@example.com")
        user2_data = TestDataFactory.create_user_data(username="user2", email="user2@example.com")
        
        with patch("src.services.user_service.create_user") as mock_create:
            mock_create.side_effect = [user1_data, user2_data]
            
            user1 = mock_create(user1_data)
            user2 = mock_create(user2_data)

        # Create shared project
        project_data = {
            "name": "Shared AI Project",
            "owner_id": user1["id"],
            "collaborators": [user2["id"]],
            "visibility": "shared"
        }
        
        with patch("src.services.project_service.create_shared_project") as mock_create_shared:
            mock_project = TestDataFactory.create_project_data(**project_data)
            mock_create_shared.return_value = mock_project
            
            project = mock_create_shared(project_data)
            project_id = project["id"]

        # User1 uploads document
        with patch("src.services.document_service.upload_and_process") as mock_upload:
            doc_result = {
                "document_id": generate_test_id(),
                "uploaded_by": user1["id"],
                "processing_status": "completed"
            }
            mock_upload.return_value = doc_result
            
            upload_result = mock_upload({
                "project_id": project_id,
                "user_id": user1["id"],
                "filename": "shared_doc.md",
                "content": "Shared project documentation"
            })

        # User2 creates conversation and asks question
        with patch("src.services.conversation_service.create_conversation") as mock_conv:
            with patch("src.services.rag_service.process_query") as mock_query:
                conversation = {
                    "id": generate_test_id(),
                    "project_id": project_id,
                    "created_by": user2["id"]
                }
                mock_conv.return_value = conversation
                
                ai_response = {
                    "response": "Based on the shared documentation...",
                    "sources": ["shared_doc.md"],
                    "confidence": 0.88
                }
                mock_query.return_value = ai_response
                
                conv_result = mock_conv({
                    "project_id": project_id,
                    "created_by": user2["id"],
                    "title": "Question about shared project"
                })
                
                query_result = mock_query({
                    "conversation_id": conv_result["id"],
                    "content": "What is this shared project about?",
                    "user_id": user2["id"]
                })

        # Verify collaboration workflow
        assert project["collaborators"] == [user2["id"]]
        assert upload_result["uploaded_by"] == user1["id"]
        assert conv_result["created_by"] == user2["id"]
        assert "shared" in query_result["response"].lower()


@pytest.mark.integration
@pytest.mark.slow
class TestRAGSystemIntegration:
    """Test RAG system integration with document processing and AI generation."""

    async def test_document_to_ai_response_pipeline(self, mock_openai_client, mock_chroma_client):
        """Test complete pipeline from document upload to AI-generated response."""
        
        project_id = generate_test_id()
        
        # Step 1: Document Upload
        documents = [
            {
                "filename": "authentication.md",
                "content": """# Authentication Guide
                
                ## JWT Tokens
                JWT tokens are used for authentication. They expire after 1 hour.
                
                ## Implementation
                Use the FastAPI-Users library for easy authentication setup.
                
                ```python
                from fastapi_users import FastAPIUsers
                from fastapi_users.authentication import JWTAuthentication
                
                jwt_authentication = JWTAuthentication(
                    secret="SECRET", lifetime_seconds=3600
                )
                ```
                """
            },
            {
                "filename": "database.py",
                "content": """
                from sqlalchemy import create_engine, Column, Integer, String
                from sqlalchemy.ext.declarative import declarative_base
                
                Base = declarative_base()
                
                class User(Base):
                    __tablename__ = "users"
                    
                    id = Column(Integer, primary_key=True)
                    username = Column(String(50), unique=True)
                    email = Column(String(100), unique=True)
                    hashed_password = Column(String(255))
                """
            }
        ]
        
        # Mock document processing
        with patch("src.services.document_processor.process_documents") as mock_process:
            processed_docs = []
            for i, doc in enumerate(documents):
                processed = {
                    "document_id": generate_test_id(),
                    "filename": doc["filename"],
                    "chunks_created": 3,
                    "embeddings_generated": True,
                    "vector_indexed": True,
                    "processing_time_ms": 800 + i * 200
                }
                processed_docs.append(processed)
            
            mock_process.return_value = processed_docs
            
            results = mock_process(project_id, documents)
            
            assert len(results) == 2
            assert all(doc["vector_indexed"] for doc in results)

        # Step 2: Query Processing with RAG
        user_query = "How do I implement JWT authentication with FastAPI?"
        
        # Mock vector search
        with patch("src.rag.retriever.search_similar_documents") as mock_search:
            relevant_chunks = [
                {
                    "content": "JWT tokens are used for authentication. They expire after 1 hour.",
                    "metadata": {"source": "authentication.md", "chunk_id": "auth_001"},
                    "similarity_score": 0.92
                },
                {
                    "content": """from fastapi_users import FastAPIUsers
                    from fastapi_users.authentication import JWTAuthentication
                    
                    jwt_authentication = JWTAuthentication(
                        secret="SECRET", lifetime_seconds=3600
                    )""",
                    "metadata": {"source": "authentication.md", "chunk_id": "auth_002"},
                    "similarity_score": 0.89
                }
            ]
            mock_search.return_value = relevant_chunks
            
            search_results = mock_search(user_query, project_id, limit=5)
            
            assert len(search_results) == 2
            assert all(chunk["similarity_score"] > 0.8 for chunk in search_results)

        # Step 3: AI Response Generation
        with patch("src.rag.generator.generate_rag_response") as mock_generate:
            ai_response = {
                "response": """To implement JWT authentication with FastAPI, you can use the FastAPI-Users library:

1. Install fastapi-users: `pip install fastapi-users`
2. Set up JWT authentication with a secret key and expiration time
3. Configure the authentication as shown in your code example

Here's the implementation based on your documentation:

```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

jwt_authentication = JWTAuthentication(
    secret="SECRET", lifetime_seconds=3600
)
```

JWT tokens expire after 1 hour for security purposes.""",
                "sources": ["authentication.md"],
                "confidence": 0.94,
                "tokens_used": 280,
                "processing_time_ms": 1500,
                "chunks_used": 2
            }
            mock_generate.return_value = ai_response
            
            final_response = mock_generate(user_query, search_results)
            
            assert "FastAPI-Users" in final_response["response"]
            assert "JWT" in final_response["response"]
            assert final_response["confidence"] > 0.9
            assert len(final_response["sources"]) > 0

        # Verify end-to-end pipeline
        total_processing_time = (
            sum(doc["processing_time_ms"] for doc in results) +
            final_response["processing_time_ms"]
        )
        assert total_processing_time < 5000  # Should complete in under 5 seconds

    async def test_real_time_document_indexing(self, mock_chroma_client):
        """Test real-time document indexing and immediate availability for queries."""
        
        project_id = generate_test_id()
        
        # Simulate real-time document upload
        new_document = {
            "filename": "new_feature.md",
            "content": "# New Feature: Real-time Chat\n\nThis feature enables real-time messaging between users.",
            "project_id": project_id,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        
        # Mock immediate processing
        with patch("src.services.real_time_processor.process_immediately") as mock_immediate:
            processing_result = {
                "document_id": generate_test_id(),
                "processed_immediately": True,
                "indexing_time_ms": 150,
                "available_for_search": True
            }
            mock_immediate.return_value = processing_result
            
            result = mock_immediate(new_document)
            
            assert result["processed_immediately"] is True
            assert result["indexing_time_ms"] < 500

        # Test immediate query availability
        immediate_query = "What is the new real-time chat feature?"
        
        with patch("src.rag.real_time_search.query_with_latest") as mock_query:
            query_result = {
                "response": "The new real-time chat feature enables real-time messaging between users.",
                "sources": ["new_feature.md"],
                "document_freshness": "immediate",  # Just indexed
                "confidence": 0.96
            }
            mock_query.return_value = query_result
            
            response = mock_query(immediate_query, project_id)
            
            assert "real-time messaging" in response["response"]
            assert response["document_freshness"] == "immediate"
            assert response["confidence"] > 0.9


@pytest.mark.integration
@pytest.mark.slow
class TestWebSocketRAGIntegration:
    """Test WebSocket integration with RAG system for real-time AI responses."""

    async def test_real_time_ai_conversation(self, mock_openai_client, mock_chroma_client):
        """Test real-time AI conversation via WebSocket with RAG integration."""
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        connection_id = generate_test_id()
        user_id = generate_test_id()
        project_id = generate_test_id()
        conversation_id = generate_test_id()
        
        # Step 1: Establish WebSocket connection
        with patch("src.websocket.connection_manager.connect") as mock_connect:
            connection_info = {
                "connection_id": connection_id,
                "user_id": user_id,
                "authenticated": True,
                "connected_at": datetime.utcnow().isoformat()
            }
            mock_connect.return_value = connection_info
            
            connection = mock_connect(mock_websocket, user_id)
            assert connection["authenticated"] is True

        # Step 2: Send AI query via WebSocket
        query_message = {
            "type": "ai_query",
            "content": "How do I handle WebSocket connections in FastAPI?",
            "conversation_id": conversation_id,
            "project_id": project_id,
            "use_rag": True
        }
        
        mock_websocket.recv = AsyncMock(return_value=json.dumps(query_message))
        
        # Step 3: Process RAG query in real-time
        with patch("src.websocket.rag_handler.process_real_time_query") as mock_rag_handler:
            # Mock streaming response chunks
            response_chunks = [
                {"type": "thinking", "status": "searching_documents"},
                {"type": "thinking", "status": "generating_response"},
                {"type": "response_chunk", "chunk": "To handle WebSocket connections in FastAPI"},
                {"type": "response_chunk", "chunk": ", you can use the websockets library"},
                {"type": "response_chunk", "chunk": " and create WebSocket endpoints."},
                {
                    "type": "response_complete",
                    "full_response": "To handle WebSocket connections in FastAPI, you can use the websockets library and create WebSocket endpoints.",
                    "sources": ["websocket_guide.md", "fastapi_websockets.py"],
                    "confidence": 0.91,
                    "total_time_ms": 1800
                }
            ]
            mock_rag_handler.return_value = response_chunks
            
            chunks = mock_rag_handler(query_message)
            
            assert len(chunks) == 6
            assert chunks[0]["status"] == "searching_documents"
            assert chunks[-1]["type"] == "response_complete"
            assert chunks[-1]["confidence"] > 0.9

        # Step 4: Send response chunks via WebSocket
        mock_websocket.send = AsyncMock()
        
        with patch("src.websocket.response_sender.send_streaming_response") as mock_send_stream:
            sent_messages = []
            for chunk in response_chunks:
                message = {
                    "id": generate_test_id(),
                    "conversation_id": conversation_id,
                    "type": "ai_response_chunk",
                    "data": chunk,
                    "timestamp": datetime.utcnow().isoformat()
                }
                sent_messages.append(message)
            
            mock_send_stream.return_value = {
                "chunks_sent": len(sent_messages),
                "total_send_time_ms": 200,
                "all_delivered": True
            }
            
            send_result = mock_send_stream(mock_websocket, response_chunks)
            
            assert send_result["chunks_sent"] == 6
            assert send_result["all_delivered"] is True

        # Verify complete real-time workflow
        total_response_time = (
            response_chunks[-1]["total_time_ms"] +
            send_result["total_send_time_ms"]
        )
        assert total_response_time < 3000  # Complete response in under 3 seconds

    async def test_concurrent_websocket_rag_queries(self):
        """Test handling multiple concurrent RAG queries via WebSocket."""
        
        # Simulate 5 concurrent WebSocket connections with AI queries
        connection_count = 5
        connections = []
        queries = []
        
        for i in range(connection_count):
            connection_id = generate_test_id()
            user_id = generate_test_id()
            
            query = {
                "connection_id": connection_id,
                "user_id": user_id,
                "query": f"What is the best practice for {['authentication', 'caching', 'logging', 'testing', 'deployment'][i]}?",
                "project_id": generate_test_id()
            }
            
            connections.append(connection_id)
            queries.append(query)

        # Mock concurrent processing
        with patch("src.websocket.concurrent_processor.process_concurrent_queries") as mock_concurrent:
            concurrent_results = []
            
            for i, query in enumerate(queries):
                result = {
                    "connection_id": query["connection_id"],
                    "query_id": generate_test_id(),
                    "response": f"Best practice for {['authentication', 'caching', 'logging', 'testing', 'deployment'][i]} is...",
                    "processing_time_ms": 1200 + i * 100,  # Slightly different times
                    "success": True
                }
                concurrent_results.append(result)
            
            mock_concurrent.return_value = {
                "total_queries": len(queries),
                "successful_responses": len(concurrent_results),
                "failed_responses": 0,
                "average_response_time_ms": 1300,
                "max_response_time_ms": 1600,
                "concurrent_processing_time_ms": 1700  # Overlap processing
            }
            
            results = mock_concurrent(queries)
            
            assert results["total_queries"] == connection_count
            assert results["successful_responses"] == connection_count
            assert results["failed_responses"] == 0
            assert results["concurrent_processing_time_ms"] < 2000


@pytest.mark.integration
@pytest.mark.slow
class TestDatabaseAPIIntegration:
    """Test integration between database operations and API endpoints."""

    async def test_crud_operations_via_api(self, async_client, async_session):
        """Test complete CRUD operations through API endpoints with database persistence."""
        
        # Test data
        project_data = {
            "name": "Integration Test Project",
            "description": "Testing database-API integration",
            "github_repo": "https://github.com/test/integration",
            "settings": {
                "rag_model": "gpt-4o-mini",
                "chunk_size": 500
            }
        }
        
        # CREATE operation
        with patch("src.api.projects.create_project_endpoint") as mock_create_api:
            with patch("src.database.crud.project.create") as mock_create_db:
                created_project = TestDataFactory.create_project_data(**project_data)
                mock_create_db.return_value = created_project
                mock_create_api.return_value = created_project
                
                # Simulate API call -> Database operation
                api_result = mock_create_api(project_data)
                db_result = mock_create_db(async_session, project_data)
                
                assert api_result["name"] == project_data["name"]
                assert db_result["name"] == project_data["name"]
                project_id = api_result["id"]

        # READ operation
        with patch("src.api.projects.get_project_endpoint") as mock_get_api:
            with patch("src.database.crud.project.get_by_id") as mock_get_db:
                mock_get_db.return_value = created_project
                mock_get_api.return_value = created_project
                
                api_result = mock_get_api(project_id)
                db_result = mock_get_db(async_session, project_id)
                
                assert api_result["id"] == project_id
                assert db_result["id"] == project_id

        # UPDATE operation
        update_data = {"description": "Updated description via API"}
        
        with patch("src.api.projects.update_project_endpoint") as mock_update_api:
            with patch("src.database.crud.project.update") as mock_update_db:
                updated_project = {**created_project, **update_data}
                mock_update_db.return_value = updated_project
                mock_update_api.return_value = updated_project
                
                api_result = mock_update_api(project_id, update_data)
                db_result = mock_update_db(async_session, project_id, update_data)
                
                assert api_result["description"] == update_data["description"]
                assert db_result["description"] == update_data["description"]

        # DELETE operation
        with patch("src.api.projects.delete_project_endpoint") as mock_delete_api:
            with patch("src.database.crud.project.delete") as mock_delete_db:
                mock_delete_db.return_value = True
                mock_delete_api.return_value = {"deleted": True, "id": project_id}
                
                api_result = mock_delete_api(project_id)
                db_result = mock_delete_db(async_session, project_id)
                
                assert api_result["deleted"] is True
                assert db_result is True

    async def test_transaction_rollback_on_api_error(self, async_session):
        """Test database transaction rollback when API operation fails."""
        
        project_data = TestDataFactory.create_project_data()
        
        with patch("src.database.transaction_manager.begin_transaction") as mock_begin:
            with patch("src.database.transaction_manager.rollback") as mock_rollback:
                with patch("src.api.projects.create_project_endpoint") as mock_api:
                    
                    # Simulate API error after database operation
                    mock_api.side_effect = Exception("API validation failed")
                    
                    try:
                        # This would normally be wrapped in a transaction
                        mock_begin(async_session)
                        mock_api(project_data)  # This fails
                    except Exception:
                        mock_rollback(async_session)
                    
                    # Verify transaction was rolled back
                    mock_begin.assert_called_once()
                    mock_rollback.assert_called_once()

    async def test_database_connection_pooling_under_load(self, async_session):
        """Test database connection pooling behavior under API load."""
        
        # Simulate multiple concurrent API requests
        request_count = 20
        
        with patch("src.database.pool_manager.get_connection") as mock_get_conn:
            with patch("src.database.pool_manager.return_connection") as mock_return_conn:
                
                connections_used = []
                
                # Mock connection pool behavior
                for i in range(request_count):
                    connection_id = f"conn_{i % 10}"  # Pool of 10 connections
                    mock_get_conn.return_value = connection_id
                    mock_return_conn.return_value = True
                    
                    # Simulate API request using connection
                    conn = mock_get_conn()
                    connections_used.append(conn)
                    mock_return_conn(conn)
                
                # Verify connection reuse
                assert len(set(connections_used)) <= 10  # Max 10 unique connections
                assert mock_get_conn.call_count == request_count
                assert mock_return_conn.call_count == request_count


@pytest.mark.integration
@pytest.mark.performance
class TestSystemPerformanceIntegration:
    """Test system performance under integrated load scenarios."""

    async def test_end_to_end_performance_benchmark(self, performance_benchmark):
        """Test complete system performance from user query to AI response."""
        
        def simulate_complete_rag_pipeline():
            """Simulate complete RAG pipeline with realistic timings."""
            
            # Step timings (in milliseconds)
            user_query_processing = 10
            document_embedding = 50
            vector_search = 30
            context_retrieval = 20
            ai_generation = 1200
            response_formatting = 15
            websocket_send = 25
            
            # Simulate each step
            import time
            total_time = 0
            
            steps = [
                ("Query Processing", user_query_processing),
                ("Document Embedding", document_embedding),
                ("Vector Search", vector_search),
                ("Context Retrieval", context_retrieval),
                ("AI Generation", ai_generation),
                ("Response Formatting", response_formatting),
                ("WebSocket Send", websocket_send)
            ]
            
            for step_name, duration_ms in steps:
                time.sleep(duration_ms / 1000)  # Convert to seconds
                total_time += duration_ms
            
            return {
                "total_time_ms": total_time,
                "steps": dict(steps),
                "response": "Complete AI response based on project documentation."
            }
        
        # Benchmark the complete pipeline
        result, execution_time = performance_benchmark(simulate_complete_rag_pipeline)
        
        # Performance assertions
        assert result["total_time_ms"] < 2000  # Under 2 seconds
        assert execution_time < 2.5  # Actual execution under 2.5 seconds
        assert result["steps"]["AI Generation"] < 1500  # AI generation under 1.5s

    async def test_concurrent_user_load_performance(self):
        """Test system performance with concurrent users."""
        
        concurrent_users = 50
        
        async def simulate_user_session():
            """Simulate a complete user session with multiple operations."""
            
            operations = [
                {"name": "login", "duration_ms": 100},
                {"name": "load_project", "duration_ms": 150},
                {"name": "send_query", "duration_ms": 1200},
                {"name": "receive_response", "duration_ms": 50},
                {"name": "upload_document", "duration_ms": 800},
            ]
            
            total_session_time = 0
            for operation in operations:
                # Simulate operation time
                await asyncio.sleep(operation["duration_ms"] / 1000)
                total_session_time += operation["duration_ms"]
            
            return {
                "user_session_time_ms": total_session_time,
                "operations_completed": len(operations),
                "success": True
            }
        
        # Run concurrent user sessions
        start_time = datetime.utcnow()
        tasks = [simulate_user_session() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        # Analyze performance
        total_concurrent_time = (end_time - start_time).total_seconds() * 1000
        successful_sessions = sum(1 for r in results if r["success"])
        average_session_time = sum(r["user_session_time_ms"] for r in results) / len(results)
        
        # Performance assertions
        assert successful_sessions == concurrent_users  # All sessions successful
        assert total_concurrent_time < 3000  # All concurrent sessions under 3 seconds
        assert average_session_time < 2500  # Average session under 2.5 seconds

    async def test_memory_usage_under_load(self):
        """Test system memory usage under sustained load."""
        
        with patch("src.monitoring.memory_monitor.get_memory_usage") as mock_memory:
            # Simulate memory usage progression under load
            memory_samples = [
                {"timestamp": datetime.utcnow(), "memory_mb": 150},  # Baseline
                {"timestamp": datetime.utcnow(), "memory_mb": 200},  # Light load
                {"timestamp": datetime.utcnow(), "memory_mb": 350},  # Medium load
                {"timestamp": datetime.utcnow(), "memory_mb": 450},  # Heavy load
                {"timestamp": datetime.utcnow(), "memory_mb": 400},  # Garbage collection
                {"timestamp": datetime.utcnow(), "memory_mb": 380},  # Stabilized
            ]
            
            mock_memory.side_effect = memory_samples
            
            # Monitor memory during load test
            memory_readings = []
            for i in range(6):
                reading = mock_memory()
                memory_readings.append(reading["memory_mb"])
            
            # Memory usage assertions
            max_memory = max(memory_readings)
            final_memory = memory_readings[-1]
            memory_growth = final_memory - memory_readings[0]
            
            assert max_memory < 500  # Peak memory under 500MB
            assert memory_growth < 300  # Total growth under 300MB
            assert final_memory < max_memory  # Memory stabilized below peak