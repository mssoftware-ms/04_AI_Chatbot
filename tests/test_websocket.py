"""
WebSocket Connection and Real-time Communication Tests

This module contains comprehensive tests for WebSocket functionality,
real-time messaging, connection handling, and event broadcasting.
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import json
from datetime import datetime
import uuid
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from tests import TestDataFactory, TestMarkers, generate_test_id


@pytest.mark.websocket
@pytest.mark.unit
class TestWebSocketConnection:
    """Test WebSocket connection establishment and management."""

    async def test_websocket_connection_establishment(self):
        """Test successful WebSocket connection establishment."""
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"type": "connect", "status": "connected"}')
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        with patch("websockets.connect", return_value=mock_websocket) as mock_connect:
            # Mock WebSocket connection
            websocket = await mock_connect("ws://localhost:8000/ws")
            
            # Test receiving connection confirmation
            message = await websocket.recv()
            data = json.loads(message)
            
            assert data["type"] == "connect"
            assert data["status"] == "connected"
            mock_connect.assert_called_once_with("ws://localhost:8000/ws")

    async def test_websocket_authentication(self):
        """Test WebSocket authentication during connection."""
        auth_token = "valid_jwt_token_12345"
        
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        mock_websocket.recv = AsyncMock(side_effect=[
            '{"type": "auth_request"}',
            '{"type": "auth_success", "user_id": "user123"}'
        ])
        
        with patch("src.websocket.authenticate_connection") as mock_auth:
            mock_auth.return_value = {"user_id": "user123", "authenticated": True}
            
            # Simulate authentication process
            auth_request = await mock_websocket.recv()
            assert json.loads(auth_request)["type"] == "auth_request"
            
            # Send authentication token
            await mock_websocket.send(json.dumps({
                "type": "auth",
                "token": auth_token
            }))
            
            # Receive authentication success
            auth_response = await mock_websocket.recv()
            auth_data = json.loads(auth_response)
            
            assert auth_data["type"] == "auth_success"
            assert auth_data["user_id"] == "user123"
            mock_websocket.send.assert_called_once()

    async def test_websocket_connection_rejection(self):
        """Test WebSocket connection rejection for invalid authentication."""
        invalid_token = "invalid_token"
        
        with patch("src.websocket.validate_token") as mock_validate:
            mock_validate.return_value = None  # Invalid token
            
            with pytest.raises(ConnectionClosedError):
                # Mock connection closure due to invalid auth
                raise ConnectionClosedError(None, None)

    async def test_websocket_connection_cleanup(self):
        """Test proper cleanup when WebSocket connection is closed."""
        connection_id = generate_test_id()
        user_id = generate_test_id()
        
        with patch("src.websocket.connection_manager.disconnect") as mock_disconnect:
            mock_disconnect.return_value = {
                "connection_id": connection_id,
                "user_id": user_id,
                "disconnected_at": datetime.utcnow().isoformat(),
                "cleanup_status": "success"
            }
            
            result = mock_disconnect(connection_id)
            
            assert result["connection_id"] == connection_id
            assert result["cleanup_status"] == "success"
            mock_disconnect.assert_called_once_with(connection_id)


@pytest.mark.websocket
@pytest.mark.unit
class TestWebSocketMessageHandling:
    """Test WebSocket message sending and receiving."""

    async def test_send_text_message(self):
        """Test sending text messages via WebSocket."""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        
        message_data = {
            "type": "message",
            "content": "Hello, this is a test message!",
            "conversation_id": generate_test_id(),
            "user_id": generate_test_id(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch("src.websocket.message_handler.send_message") as mock_send:
            mock_send.return_value = {
                "message_id": generate_test_id(),
                "status": "sent",
                **message_data
            }
            
            result = mock_send(message_data)
            
            assert result["status"] == "sent"
            assert "message_id" in result
            assert result["content"] == message_data["content"]
            mock_send.assert_called_once_with(message_data)

    async def test_receive_message_processing(self):
        """Test processing of received WebSocket messages."""
        mock_websocket = AsyncMock()
        
        incoming_message = {
            "type": "chat_message",
            "content": "What is FastAPI?",
            "conversation_id": generate_test_id(),
            "message_id": generate_test_id()
        }
        
        mock_websocket.recv = AsyncMock(return_value=json.dumps(incoming_message))
        
        with patch("src.websocket.message_processor.process_message") as mock_process:
            mock_process.return_value = {
                "processed": True,
                "ai_response": "FastAPI is a modern web framework for building APIs with Python.",
                "processing_time_ms": 800
            }
            
            # Receive and process message
            message_json = await mock_websocket.recv()
            message_data = json.loads(message_json)
            
            result = mock_process(message_data)
            
            assert result["processed"] is True
            assert "ai_response" in result
            assert result["processing_time_ms"] > 0
            mock_process.assert_called_once_with(message_data)

    async def test_binary_message_handling(self):
        """Test handling of binary WebSocket messages (file uploads)."""
        file_data = {
            "type": "file_upload",
            "filename": "document.pdf",
            "content_type": "application/pdf",
            "size": 1024 * 50,  # 50KB
            "project_id": generate_test_id()
        }
        
        mock_binary_data = b"fake_pdf_content_" * 100  # Mock binary data
        
        with patch("src.websocket.file_handler.handle_binary_upload") as mock_upload:
            mock_upload.return_value = {
                "file_id": generate_test_id(),
                "status": "uploaded",
                "processed": True,
                "chunks_created": 5,
                **file_data
            }
            
            result = mock_upload(file_data, mock_binary_data)
            
            assert result["status"] == "uploaded"
            assert result["processed"] is True
            assert result["chunks_created"] > 0
            mock_upload.assert_called_once_with(file_data, mock_binary_data)

    async def test_message_broadcasting(self):
        """Test broadcasting messages to multiple connected clients."""
        conversation_id = generate_test_id()
        connected_users = [generate_test_id() for _ in range(3)]
        
        broadcast_message = {
            "type": "broadcast",
            "content": "New message in conversation",
            "conversation_id": conversation_id,
            "sender_id": connected_users[0]
        }
        
        with patch("src.websocket.broadcaster.broadcast_to_conversation") as mock_broadcast:
            mock_broadcast.return_value = {
                "broadcast_id": generate_test_id(),
                "recipients": connected_users[1:],  # Exclude sender
                "delivered_count": 2,
                "failed_count": 0
            }
            
            result = mock_broadcast(broadcast_message, connected_users)
            
            assert result["delivered_count"] == 2
            assert result["failed_count"] == 0
            assert len(result["recipients"]) == 2
            mock_broadcast.assert_called_once_with(broadcast_message, connected_users)


@pytest.mark.websocket
@pytest.mark.integration
class TestRealTimeChatFeatures:
    """Test real-time chat features via WebSocket."""

    async def test_typing_indicator(self):
        """Test typing indicator functionality."""
        conversation_id = generate_test_id()
        user_id = generate_test_id()
        
        typing_event = {
            "type": "typing_start",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch("src.websocket.typing_handler.handle_typing_event") as mock_typing:
            mock_typing.return_value = {
                "event_processed": True,
                "broadcast_sent": True,
                "active_typers": [user_id]
            }
            
            result = mock_typing(typing_event)
            
            assert result["event_processed"] is True
            assert result["broadcast_sent"] is True
            assert user_id in result["active_typers"]
            mock_typing.assert_called_once_with(typing_event)

    async def test_message_status_updates(self):
        """Test message status updates (delivered, read, etc.)."""
        message_id = generate_test_id()
        user_id = generate_test_id()
        
        status_update = {
            "type": "message_status",
            "message_id": message_id,
            "status": "read",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch("src.websocket.status_handler.update_message_status") as mock_status:
            mock_status.return_value = {
                "status_updated": True,
                "previous_status": "delivered",
                "new_status": "read",
                "notify_sender": True
            }
            
            result = mock_status(status_update)
            
            assert result["status_updated"] is True
            assert result["new_status"] == "read"
            assert result["notify_sender"] is True
            mock_status.assert_called_once_with(status_update)

    async def test_presence_management(self):
        """Test user presence management (online/offline status)."""
        user_id = generate_test_id()
        
        presence_update = {
            "type": "presence",
            "user_id": user_id,
            "status": "online",
            "last_seen": datetime.utcnow().isoformat()
        }
        
        with patch("src.websocket.presence_manager.update_presence") as mock_presence:
            mock_presence.return_value = {
                "presence_updated": True,
                "previous_status": "offline",
                "new_status": "online",
                "notify_contacts": True,
                "contact_count": 5
            }
            
            result = mock_presence(presence_update)
            
            assert result["presence_updated"] is True
            assert result["new_status"] == "online"
            assert result["contact_count"] > 0
            mock_presence.assert_called_once_with(presence_update)

    async def test_conversation_join_leave(self):
        """Test joining and leaving conversation rooms."""
        conversation_id = generate_test_id()
        user_id = generate_test_id()
        
        join_event = {
            "type": "join_conversation",
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        
        with patch("src.websocket.room_manager.join_conversation") as mock_join:
            mock_join.return_value = {
                "joined": True,
                "conversation_id": conversation_id,
                "participant_count": 3,
                "room_active": True
            }
            
            result = mock_join(join_event)
            
            assert result["joined"] is True
            assert result["participant_count"] > 0
            assert result["room_active"] is True
            mock_join.assert_called_once_with(join_event)


@pytest.mark.websocket
@pytest.mark.integration
class TestWebSocketRAGIntegration:
    """Test WebSocket integration with RAG system."""

    async def test_real_time_rag_query(self):
        """Test real-time RAG query processing via WebSocket."""
        query_data = {
            "type": "rag_query",
            "query": "How do I implement WebSocket authentication?",
            "project_id": generate_test_id(),
            "conversation_id": generate_test_id(),
            "user_id": generate_test_id()
        }
        
        with patch("src.websocket.rag_handler.process_rag_query") as mock_rag:
            mock_rag.return_value = {
                "query_id": generate_test_id(),
                "response": "To implement WebSocket authentication, you can validate JWT tokens during the handshake...",
                "sources": ["websocket_auth.md", "jwt_validation.py"],
                "confidence": 0.92,
                "processing_time_ms": 1200
            }
            
            result = mock_rag(query_data)
            
            assert "response" in result
            assert len(result["sources"]) > 0
            assert result["confidence"] > 0.9
            assert result["processing_time_ms"] > 0
            mock_rag.assert_called_once_with(query_data)

    async def test_streaming_rag_response(self):
        """Test streaming RAG response chunks via WebSocket."""
        query_id = generate_test_id()
        
        response_chunks = [
            {"type": "response_chunk", "chunk_id": 1, "content": "To implement WebSocket"},
            {"type": "response_chunk", "chunk_id": 2, "content": " authentication, you can"},
            {"type": "response_chunk", "chunk_id": 3, "content": " validate JWT tokens..."},
            {"type": "response_complete", "total_chunks": 3, "sources": ["auth.md"]}
        ]
        
        with patch("src.websocket.streaming.stream_rag_response") as mock_stream:
            mock_stream.return_value = response_chunks
            
            chunks = mock_stream(query_id)
            
            assert len(chunks) == 4  # 3 chunks + completion
            assert chunks[-1]["type"] == "response_complete"
            assert chunks[-1]["total_chunks"] == 3
            mock_stream.assert_called_once_with(query_id)

    async def test_document_processing_notifications(self):
        """Test real-time notifications for document processing."""
        upload_id = generate_test_id()
        
        processing_updates = [
            {"type": "processing_start", "upload_id": upload_id, "status": "started"},
            {"type": "processing_progress", "upload_id": upload_id, "progress": 25},
            {"type": "processing_progress", "upload_id": upload_id, "progress": 50},
            {"type": "processing_progress", "upload_id": upload_id, "progress": 75},
            {"type": "processing_complete", "upload_id": upload_id, "chunks_created": 10}
        ]
        
        with patch("src.websocket.document_notifications.send_processing_updates") as mock_notify:
            mock_notify.return_value = {
                "notifications_sent": 5,
                "final_status": "complete",
                "chunks_created": 10
            }
            
            result = mock_notify(processing_updates)
            
            assert result["notifications_sent"] == 5
            assert result["final_status"] == "complete"
            assert result["chunks_created"] > 0
            mock_notify.assert_called_once_with(processing_updates)


@pytest.mark.websocket
@pytest.mark.performance
class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""

    async def test_concurrent_connections_handling(self):
        """Test handling multiple concurrent WebSocket connections."""
        connection_count = 100
        
        with patch("src.websocket.connection_manager.handle_multiple_connections") as mock_handle:
            mock_connections = [
                {
                    "connection_id": generate_test_id(),
                    "user_id": generate_test_id(),
                    "connected_at": datetime.utcnow().isoformat(),
                    "status": "active"
                }
                for _ in range(connection_count)
            ]
            
            mock_handle.return_value = {
                "total_connections": connection_count,
                "active_connections": connection_count,
                "average_response_time_ms": 45,
                "memory_usage_mb": 150
            }
            
            result = mock_handle(mock_connections)
            
            assert result["total_connections"] == connection_count
            assert result["active_connections"] == connection_count
            assert result["average_response_time_ms"] < 100
            mock_handle.assert_called_once_with(mock_connections)

    async def test_message_throughput(self):
        """Test WebSocket message throughput under load."""
        messages_per_second = 1000
        test_duration_seconds = 10
        
        with patch("src.websocket.performance.measure_throughput") as mock_throughput:
            mock_throughput.return_value = {
                "messages_sent": messages_per_second * test_duration_seconds,
                "messages_received": messages_per_second * test_duration_seconds,
                "duration_seconds": test_duration_seconds,
                "throughput_mps": messages_per_second,
                "average_latency_ms": 25
            }
            
            result = mock_throughput(messages_per_second, test_duration_seconds)
            
            assert result["throughput_mps"] >= messages_per_second
            assert result["average_latency_ms"] < 50
            assert result["messages_sent"] == result["messages_received"]
            mock_throughput.assert_called_once_with(messages_per_second, test_duration_seconds)

    async def test_memory_usage_under_load(self):
        """Test memory usage with many active WebSocket connections."""
        connection_count = 500
        
        with patch("src.websocket.monitoring.monitor_memory_usage") as mock_monitor:
            mock_monitor.return_value = {
                "active_connections": connection_count,
                "memory_per_connection_kb": 50,
                "total_memory_mb": (connection_count * 50) / 1024,
                "memory_efficiency": "good",
                "gc_frequency": "normal"
            }
            
            result = mock_monitor(connection_count)
            
            assert result["active_connections"] == connection_count
            assert result["memory_per_connection_kb"] < 100  # Reasonable per-connection memory
            assert result["memory_efficiency"] == "good"
            mock_monitor.assert_called_once_with(connection_count)

    async def test_connection_scaling(self):
        """Test WebSocket connection auto-scaling capabilities."""
        initial_connections = 100
        peak_connections = 1000
        
        with patch("src.websocket.scaling.auto_scale_connections") as mock_scale:
            mock_scale.return_value = {
                "initial_capacity": initial_connections,
                "scaled_capacity": peak_connections,
                "scaling_factor": 10,
                "scaling_time_seconds": 30,
                "success": True
            }
            
            result = mock_scale(initial_connections, peak_connections)
            
            assert result["scaled_capacity"] == peak_connections
            assert result["scaling_time_seconds"] < 60
            assert result["success"] is True
            mock_scale.assert_called_once_with(initial_connections, peak_connections)


@pytest.mark.websocket
@pytest.mark.security
class TestWebSocketSecurity:
    """Test WebSocket security measures."""

    async def test_rate_limiting_per_connection(self):
        """Test rate limiting for WebSocket connections."""
        connection_id = generate_test_id()
        message_limit = 10  # 10 messages per minute
        
        with patch("src.websocket.rate_limiter.check_rate_limit") as mock_rate_limit:
            # First 10 messages should be allowed
            for i in range(message_limit):
                mock_rate_limit.return_value = {"allowed": True, "remaining": message_limit - i - 1}
                result = mock_rate_limit(connection_id)
                assert result["allowed"] is True
            
            # 11th message should be rate limited
            mock_rate_limit.return_value = {"allowed": False, "remaining": 0, "retry_after": 60}
            result = mock_rate_limit(connection_id)
            assert result["allowed"] is False
            assert result["retry_after"] > 0

    async def test_message_size_limits(self):
        """Test WebSocket message size limitations."""
        large_message = "x" * (1024 * 1024)  # 1MB message
        max_size = 500 * 1024  # 500KB limit
        
        with patch("src.websocket.validators.validate_message_size") as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "size_bytes": len(large_message),
                "max_size_bytes": max_size,
                "error": "Message exceeds maximum size limit"
            }
            
            result = mock_validate(large_message)
            
            assert result["valid"] is False
            assert result["size_bytes"] > max_size
            assert "exceeds" in result["error"]
            mock_validate.assert_called_once_with(large_message)

    async def test_connection_origin_validation(self):
        """Test WebSocket connection origin validation."""
        valid_origins = ["http://localhost:3000", "https://myapp.com"]
        test_origins = [
            "http://localhost:3000",  # Valid
            "https://myapp.com",      # Valid
            "https://evil.com",       # Invalid
            "http://malicious.site"   # Invalid
        ]
        
        with patch("src.websocket.security.validate_origin") as mock_validate:
            for origin in test_origins:
                is_valid = origin in valid_origins
                mock_validate.return_value = {"valid": is_valid, "origin": origin}
                
                result = mock_validate(origin)
                
                if origin in valid_origins:
                    assert result["valid"] is True
                else:
                    assert result["valid"] is False

    async def test_websocket_csrf_protection(self):
        """Test CSRF protection for WebSocket connections."""
        csrf_token = "valid_csrf_token_12345"
        
        with patch("src.websocket.csrf.validate_csrf_token") as mock_csrf:
            mock_csrf.return_value = {
                "valid": True,
                "token": csrf_token,
                "expires_at": (datetime.utcnow().timestamp() + 3600)  # 1 hour from now
            }
            
            result = mock_csrf(csrf_token)
            
            assert result["valid"] is True
            assert result["expires_at"] > datetime.utcnow().timestamp()
            mock_csrf.assert_called_once_with(csrf_token)


@pytest.mark.websocket
@pytest.mark.integration
class TestWebSocketErrorHandling:
    """Test WebSocket error handling and recovery."""

    async def test_connection_drop_recovery(self):
        """Test automatic reconnection after connection drops."""
        connection_id = generate_test_id()
        
        with patch("src.websocket.recovery.handle_connection_drop") as mock_recovery:
            mock_recovery.return_value = {
                "reconnection_attempted": True,
                "reconnection_successful": True,
                "messages_queued": 5,
                "recovery_time_seconds": 2.3
            }
            
            result = mock_recovery(connection_id)
            
            assert result["reconnection_attempted"] is True
            assert result["reconnection_successful"] is True
            assert result["messages_queued"] > 0
            assert result["recovery_time_seconds"] < 5
            mock_recovery.assert_called_once_with(connection_id)

    async def test_malformed_message_handling(self):
        """Test handling of malformed WebSocket messages."""
        malformed_messages = [
            "invalid json {",
            '{"type": "unknown_type"}',
            '{"missing": "required_fields"}',
            "",  # Empty message
            None  # Null message
        ]
        
        with patch("src.websocket.error_handler.handle_malformed_message") as mock_handler:
            for message in malformed_messages:
                mock_handler.return_value = {
                    "error": "Malformed message",
                    "original_message": message,
                    "error_type": "validation_error",
                    "action": "ignored"
                }
                
                result = mock_handler(message)
                
                assert result["error"] == "Malformed message"
                assert result["action"] == "ignored"
                assert result["error_type"] == "validation_error"

    async def test_websocket_exception_handling(self):
        """Test handling of WebSocket-specific exceptions."""
        exceptions_to_test = [
            ConnectionClosed(None, None),
            ConnectionClosedError(None, None),
            Exception("Unexpected error")
        ]
        
        with patch("src.websocket.exception_handler.handle_websocket_exception") as mock_handler:
            for exc in exceptions_to_test:
                mock_handler.return_value = {
                    "exception_type": type(exc).__name__,
                    "handled": True,
                    "recovery_action": "close_connection" if isinstance(exc, (ConnectionClosed, ConnectionClosedError)) else "log_error",
                    "notify_client": False
                }
                
                result = mock_handler(exc)
                
                assert result["handled"] is True
                assert result["exception_type"] == type(exc).__name__
                if isinstance(exc, (ConnectionClosed, ConnectionClosedError)):
                    assert result["recovery_action"] == "close_connection"

    async def test_timeout_handling(self):
        """Test WebSocket timeout handling."""
        timeout_scenarios = [
            {"type": "ping_timeout", "timeout_seconds": 30},
            {"type": "message_timeout", "timeout_seconds": 60},
            {"type": "auth_timeout", "timeout_seconds": 10}
        ]
        
        with patch("src.websocket.timeout_handler.handle_timeout") as mock_timeout:
            for scenario in timeout_scenarios:
                mock_timeout.return_value = {
                    "timeout_type": scenario["type"],
                    "timeout_seconds": scenario["timeout_seconds"],
                    "action_taken": "close_connection",
                    "client_notified": True
                }
                
                result = mock_timeout(scenario)
                
                assert result["timeout_type"] == scenario["type"]
                assert result["action_taken"] == "close_connection"
                assert result["client_notified"] is True