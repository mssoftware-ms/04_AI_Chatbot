"""
Test Data Fixtures and Sample Data

This module provides comprehensive test data fixtures for all components
of the WhatsApp AI Chatbot system, including realistic sample data for
testing various scenarios.
"""

import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from faker import Faker
import uuid
import json
import random
import string

fake = Faker()


@pytest.fixture
def sample_users() -> List[Dict[str, Any]]:
    """Generate sample user data for testing."""
    users = []
    for i in range(10):
        user = {
            "id": str(uuid.uuid4()),
            "username": fake.user_name(),
            "email": fake.email(),
            "full_name": fake.name(),
            "phone_number": fake.phone_number(),
            "is_active": random.choice([True, True, True, False]),  # 75% active
            "is_verified": random.choice([True, True, False]),      # 67% verified
            "profile_image": f"https://avatar.example.com/{fake.uuid4()}.jpg",
            "bio": fake.text(max_nb_chars=200),
            "timezone": fake.timezone(),
            "language": random.choice(["en", "es", "fr", "de", "it"]),
            "preferences": {
                "notifications": random.choice([True, False]),
                "theme": random.choice(["light", "dark", "auto"]),
                "ai_assistance": random.choice([True, False])
            },
            "created_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat(),
            "updated_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            "last_login": fake.date_time_between(start_date="-7d", end_date="now").isoformat()
        }
        users.append(user)
    return users


@pytest.fixture
def sample_projects() -> List[Dict[str, Any]]:
    """Generate sample project data for testing."""
    projects = []
    for i in range(5):
        project = {
            "id": str(uuid.uuid4()),
            "name": fake.catch_phrase().replace(",", ""),
            "description": fake.text(max_nb_chars=500),
            "github_repo": f"https://github.com/{fake.user_name()}/{fake.slug()}",
            "owner_id": str(uuid.uuid4()),
            "visibility": random.choice(["public", "private", "internal"]),
            "status": random.choice(["active", "archived", "draft"]),
            "settings": {
                "rag_model": random.choice(["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]),
                "chunk_size": random.choice([300, 500, 800, 1000]),
                "chunk_overlap": random.choice([20, 50, 100]),
                "temperature": round(random.uniform(0.1, 1.0), 2),
                "max_tokens": random.choice([1000, 2000, 4000, 8000]),
                "enable_rag": random.choice([True, False]),
                "auto_index": random.choice([True, False])
            },
            "vector_collection_name": f"project_{i}_collection",
            "document_count": random.randint(0, 100),
            "total_size_bytes": random.randint(1024, 10 * 1024 * 1024),  # 1KB to 10MB
            "tags": random.sample(["python", "javascript", "react", "fastapi", "ai", "ml", "web", "mobile"], k=random.randint(1, 4)),
            "created_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            "updated_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            "last_activity": fake.date_time_between(start_date="-7d", end_date="now").isoformat()
        }
        projects.append(project)
    return projects


@pytest.fixture
def sample_conversations() -> List[Dict[str, Any]]:
    """Generate sample conversation data for testing."""
    conversations = []
    for i in range(15):
        conversation = {
            "id": str(uuid.uuid4()),
            "project_id": str(uuid.uuid4()),
            "title": fake.sentence(nb_words=random.randint(3, 8)).rstrip('.'),
            "type": random.choice(["chat", "support", "training", "debug"]),
            "status": random.choice(["active", "archived", "closed"]),
            "priority": random.choice(["low", "medium", "high", "urgent"]),
            "participants": [str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
            "metadata": {
                "source": random.choice(["web", "mobile", "api", "webhook"]),
                "client_version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "user_agent": fake.user_agent(),
                "ip_address": fake.ipv4(),
                "session_id": str(uuid.uuid4()),
                "context": random.choice(["support", "development", "training", "general"])
            },
            "settings": {
                "ai_enabled": random.choice([True, False]),
                "rag_enabled": random.choice([True, False]),
                "auto_response": random.choice([True, False]),
                "language": random.choice(["en", "es", "fr", "de"])
            },
            "stats": {
                "message_count": random.randint(0, 200),
                "user_messages": random.randint(0, 100),
                "ai_messages": random.randint(0, 100),
                "average_response_time_ms": random.randint(500, 3000),
                "total_tokens_used": random.randint(0, 10000)
            },
            "created_at": fake.date_time_between(start_date="-6m", end_date="now").isoformat(),
            "updated_at": fake.date_time_between(start_date="-1d", end_date="now").isoformat(),
            "last_message_at": fake.date_time_between(start_date="-1d", end_date="now").isoformat()
        }
        conversations.append(conversation)
    return conversations


@pytest.fixture
def sample_messages() -> List[Dict[str, Any]]:
    """Generate sample message data for testing."""
    messages = []
    conversation_id = str(uuid.uuid4())
    
    for i in range(50):
        # Alternate between user and assistant messages
        role = "user" if i % 2 == 0 else "assistant"
        
        if role == "user":
            content = random.choice([
                fake.question(),
                fake.sentence(),
                "How do I implement " + fake.word() + "?",
                "What is the best way to " + fake.sentence().lower(),
                "Can you help me with " + fake.word() + "?",
                "I'm having trouble with " + fake.word(),
                fake.text(max_nb_chars=200)
            ])
            message_type = random.choice(["text", "file", "image", "code", "voice"])
        else:
            content = random.choice([
                f"To implement {fake.word()}, you can follow these steps: {fake.text(max_nb_chars=300)}",
                f"Here's how you can {fake.word()}: {fake.text(max_nb_chars=200)}",
                f"Based on the documentation, {fake.text(max_nb_chars=250)}",
                fake.text(max_nb_chars=400),
                f"I found relevant information about {fake.word()}: {fake.text(max_nb_chars=300)}"
            ])
            message_type = "text"
        
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "message_type": message_type,
            "status": random.choice(["sent", "delivered", "read", "failed"]),
            "metadata": {
                "model_used": random.choice(["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]) if role == "assistant" else None,
                "temperature": round(random.uniform(0.1, 1.0), 2) if role == "assistant" else None,
                "sources": [fake.file_name() for _ in range(random.randint(0, 3))] if role == "assistant" else None,
                "confidence": round(random.uniform(0.7, 1.0), 2) if role == "assistant" else None,
                "ip_address": fake.ipv4() if role == "user" else None,
                "user_agent": fake.user_agent() if role == "user" else None,
                "attachments": [
                    {
                        "id": str(uuid.uuid4()),
                        "filename": fake.file_name(),
                        "size": random.randint(1024, 1024*1024),
                        "type": random.choice(["image/jpeg", "application/pdf", "text/plain"])
                    }
                ] if message_type in ["file", "image"] else None
            },
            "token_count": random.randint(10, 500),
            "processing_time_ms": random.randint(200, 3000) if role == "assistant" else None,
            "edit_history": [],
            "reactions": random.sample(["👍", "👎", "❤️", "😊", "🤔"], k=random.randint(0, 2)),
            "created_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            "updated_at": fake.date_time_between(start_date="-1d", end_date="now").isoformat(),
            "read_at": fake.date_time_between(start_date="-1d", end_date="now").isoformat() if random.choice([True, False]) else None
        }
        messages.append(message)
    
    return messages


@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """Generate sample document data for testing."""
    documents = []
    file_types = {
        ".md": "markdown",
        ".py": "python",
        ".js": "javascript",
        ".txt": "text",
        ".json": "json",
        ".yml": "yaml",
        ".html": "html",
        ".css": "css"
    }
    
    for i in range(25):
        file_extension = random.choice(list(file_types.keys()))
        file_type = file_types[file_extension]
        
        # Generate appropriate content based on file type
        if file_type == "python":
            content = f"""
def {fake.word()}():
    '''
    {fake.sentence()}
    '''
    {fake.sentence().lower().replace(' ', '_')} = "{fake.word()}"
    return {fake.sentence().lower().replace(' ', '_')}

class {fake.word().title()}:
    def __init__(self):
        self.{fake.word()} = "{fake.word()}"
    
    def {fake.word()}(self, {fake.word()}):
        return f"{fake.sentence()}"
"""
        elif file_type == "markdown":
            content = f"""# {fake.catch_phrase()}

## Overview
{fake.paragraph()}

## Features
- {fake.sentence()}
- {fake.sentence()}
- {fake.sentence()}

## Usage
```python
{fake.word()} = {fake.word()}()
result = {fake.word()}.{fake.word()}()
```

## API Reference
{fake.text(max_nb_chars=300)}
"""
        elif file_type == "json":
            content = json.dumps({
                "name": fake.word(),
                "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "description": fake.sentence(),
                "author": fake.name(),
                "dependencies": {fake.word(): f"^{random.randint(1, 5)}.0.0" for _ in range(random.randint(1, 5))},
                "scripts": {fake.word(): f"{fake.word()} {fake.word()}" for _ in range(random.randint(1, 3))},
                "keywords": [fake.word() for _ in range(random.randint(1, 5))]
            }, indent=2)
        else:
            content = fake.text(max_nb_chars=random.randint(200, 2000))
        
        document = {
            "id": str(uuid.uuid4()),
            "project_id": str(uuid.uuid4()),
            "filename": fake.file_name(extension=file_extension),
            "file_path": f"{fake.word()}/{fake.word()}{file_extension}",
            "content": content,
            "file_type": file_type,
            "size_bytes": len(content.encode('utf-8')),
            "hash": fake.sha256(),
            "metadata": {
                "encoding": "utf-8",
                "mime_type": random.choice(["text/plain", "text/markdown", "application/json", "text/html"]),
                "language": file_type if file_type in ["python", "javascript"] else "text",
                "lines": content.count('\n') + 1,
                "words": len(content.split()),
                "characters": len(content),
                "has_code": file_type in ["python", "javascript", "html", "css"],
                "complexity_score": round(random.uniform(0.1, 1.0), 2),
                "readability_score": round(random.uniform(0.3, 1.0), 2)
            },
            "processing_status": random.choice(["pending", "processing", "completed", "failed"]),
            "chunks_created": random.randint(1, 10),
            "vector_indexed": random.choice([True, False]),
            "last_processed": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            "tags": random.sample(["documentation", "code", "config", "test", "example", "guide"], k=random.randint(0, 3)),
            "created_at": fake.date_time_between(start_date="-90d", end_date="now").isoformat(),
            "updated_at": fake.date_time_between(start_date="-7d", end_date="now").isoformat()
        }
        documents.append(document)
    
    return documents


@pytest.fixture
def sample_rag_queries() -> List[Dict[str, Any]]:
    """Generate sample RAG query data for testing."""
    queries = []
    query_templates = [
        "How do I implement {feature} in {technology}?",
        "What is the best way to {action} with {technology}?",
        "Can you explain how {concept} works?",
        "Show me an example of {feature} implementation",
        "What are the best practices for {concept}?",
        "How to debug {problem} in {technology}?",
        "What is the difference between {concept1} and {concept2}?",
        "How to optimize {feature} for better performance?",
        "What are the common errors when using {technology}?",
        "How to set up {technology} for production?"
    ]
    
    technologies = ["FastAPI", "React", "Python", "JavaScript", "Docker", "PostgreSQL", "Redis", "AWS"]
    features = ["authentication", "caching", "logging", "testing", "deployment", "monitoring"]
    concepts = ["middleware", "decorators", "async programming", "database migrations", "API design"]
    actions = ["handle errors", "validate input", "manage state", "process files", "cache data"]
    
    for i in range(30):
        template = random.choice(query_templates)
        query_text = template.format(
            feature=random.choice(features),
            technology=random.choice(technologies),
            action=random.choice(actions),
            concept=random.choice(concepts),
            concept1=random.choice(concepts),
            concept2=random.choice(concepts),
            problem=random.choice(["memory leaks", "slow queries", "connection timeouts", "import errors"])
        )
        
        query = {
            "id": str(uuid.uuid4()),
            "project_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "query_text": query_text,
            "query_type": random.choice(["question", "request", "clarification", "example"]),
            "context": {
                "previous_messages": random.randint(0, 10),
                "conversation_topic": random.choice(concepts + features),
                "user_expertise": random.choice(["beginner", "intermediate", "advanced"]),
                "project_context": random.choice(technologies)
            },
            "processing_info": {
                "embedding_time_ms": random.randint(20, 100),
                "search_time_ms": random.randint(10, 50),
                "generation_time_ms": random.randint(500, 2000),
                "total_time_ms": random.randint(600, 2500),
                "tokens_used": random.randint(100, 1000)
            },
            "results": {
                "answer_generated": True,
                "sources_found": random.randint(1, 8),
                "confidence_score": round(random.uniform(0.6, 0.98), 2),
                "relevance_score": round(random.uniform(0.7, 0.95), 2),
                "completeness_score": round(random.uniform(0.6, 0.9), 2)
            },
            "feedback": {
                "user_rating": random.choice([None, 1, 2, 3, 4, 5]),
                "helpful": random.choice([None, True, False]),
                "follow_up_questions": random.randint(0, 3)
            },
            "created_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat()
        }
        queries.append(query)
    
    return queries


@pytest.fixture
def sample_websocket_events() -> List[Dict[str, Any]]:
    """Generate sample WebSocket event data for testing."""
    events = []
    event_types = [
        "connection", "disconnection", "message", "typing_start", "typing_stop",
        "user_joined", "user_left", "message_read", "message_delivered",
        "presence_update", "file_upload", "voice_message", "system_notification"
    ]
    
    for i in range(40):
        event_type = random.choice(event_types)
        
        # Base event structure
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": fake.date_time_between(start_date="-7d", end_date="now").isoformat(),
            "connection_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
            "session_id": str(uuid.uuid4()),
        }
        
        # Add type-specific data
        if event_type == "message":
            event.update({
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "content": fake.sentence(),
                "message_type": random.choice(["text", "image", "file", "voice"]),
                "size_bytes": random.randint(10, 10000)
            })
        elif event_type in ["typing_start", "typing_stop"]:
            event.update({
                "conversation_id": str(uuid.uuid4()),
                "typing_duration_ms": random.randint(1000, 30000)
            })
        elif event_type in ["user_joined", "user_left"]:
            event.update({
                "conversation_id": str(uuid.uuid4()),
                "participant_count": random.randint(1, 10)
            })
        elif event_type == "presence_update":
            event.update({
                "status": random.choice(["online", "offline", "away", "busy"]),
                "last_seen": fake.date_time_between(start_date="-1d", end_date="now").isoformat()
            })
        elif event_type == "file_upload":
            event.update({
                "filename": fake.file_name(),
                "file_size": random.randint(1024, 10*1024*1024),
                "file_type": random.choice(["image/jpeg", "application/pdf", "text/plain", "video/mp4"]),
                "upload_duration_ms": random.randint(1000, 60000)
            })
        
        # Add performance metrics
        event["metrics"] = {
            "processing_time_ms": random.randint(1, 100),
            "queue_time_ms": random.randint(0, 50),
            "network_latency_ms": random.randint(10, 200),
            "payload_size_bytes": random.randint(100, 5000)
        }
        
        events.append(event)
    
    return events


@pytest.fixture
def sample_api_requests() -> List[Dict[str, Any]]:
    """Generate sample API request data for testing."""
    requests = []
    endpoints = [
        "/api/v1/projects", "/api/v1/conversations", "/api/v1/messages",
        "/api/v1/documents", "/api/v1/users", "/api/v1/auth/login",
        "/api/v1/auth/refresh", "/api/v1/rag/query", "/api/v1/files/upload",
        "/health", "/docs", "/api/v1/search"
    ]
    
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    status_codes = [200, 201, 400, 401, 403, 404, 422, 500]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "curl/7.68.0", "PostmanRuntime/7.28.0", "axios/0.24.0"
    ]
    
    for i in range(100):
        endpoint = random.choice(endpoints)
        method = random.choice(methods)
        status_code = random.choice(status_codes)
        
        # Make realistic method/endpoint combinations
        if endpoint == "/health":
            method = "GET"
            status_code = 200
        elif "/auth/" in endpoint:
            method = "POST"
            status_code = random.choice([200, 401, 422])
        elif endpoint.endswith("/upload"):
            method = "POST"
            status_code = random.choice([201, 400, 413])
        
        request = {
            "id": str(uuid.uuid4()),
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time_ms": random.randint(10, 2000),
            "request_size_bytes": random.randint(100, 10000),
            "response_size_bytes": random.randint(200, 50000),
            "user_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
            "ip_address": fake.ipv4(),
            "user_agent": random.choice(user_agents),
            "referer": fake.url() if random.choice([True, False]) else None,
            "headers": {
                "content-type": random.choice(["application/json", "multipart/form-data", "text/plain"]),
                "authorization": f"Bearer {fake.sha256()[:32]}" if random.choice([True, False]) else None,
                "x-request-id": str(uuid.uuid4())
            },
            "query_params": {
                "page": random.randint(1, 10),
                "limit": random.choice([10, 20, 50, 100])
            } if method == "GET" else None,
            "error_details": {
                "error_code": f"E{random.randint(1000, 9999)}",
                "error_message": fake.sentence()
            } if status_code >= 400 else None,
            "performance": {
                "db_query_time_ms": random.randint(5, 200),
                "cache_hit": random.choice([True, False]),
                "external_api_calls": random.randint(0, 3),
                "memory_usage_mb": round(random.uniform(10, 200), 2)
            },
            "timestamp": fake.date_time_between(start_date="-7d", end_date="now").isoformat()
        }
        requests.append(request)
    
    return requests


@pytest.fixture
def sample_performance_metrics() -> Dict[str, Any]:
    """Generate sample performance metrics for testing."""
    return {
        "system_metrics": {
            "cpu_usage_percent": round(random.uniform(10, 85), 2),
            "memory_usage_percent": round(random.uniform(20, 80), 2),
            "disk_usage_percent": round(random.uniform(15, 70), 2),
            "network_io_mbps": round(random.uniform(1, 100), 2),
            "disk_io_mbps": round(random.uniform(5, 500), 2),
            "open_file_descriptors": random.randint(100, 1000),
            "active_threads": random.randint(10, 100),
            "uptime_seconds": random.randint(3600, 604800)  # 1 hour to 1 week
        },
        "application_metrics": {
            "active_connections": random.randint(10, 500),
            "requests_per_second": round(random.uniform(1, 100), 2),
            "average_response_time_ms": round(random.uniform(50, 500), 2),
            "error_rate_percent": round(random.uniform(0, 5), 2),
            "cache_hit_rate_percent": round(random.uniform(70, 95), 2),
            "database_connection_pool": {
                "active": random.randint(5, 20),
                "idle": random.randint(0, 10),
                "total": random.randint(10, 30)
            },
            "queue_sizes": {
                "message_queue": random.randint(0, 100),
                "file_processing": random.randint(0, 50),
                "email_queue": random.randint(0, 20)
            }
        },
        "ai_metrics": {
            "rag_queries_per_hour": random.randint(10, 1000),
            "average_embedding_time_ms": round(random.uniform(20, 100), 2),
            "average_generation_time_ms": round(random.uniform(500, 2000), 2),
            "token_usage": {
                "input_tokens": random.randint(1000, 100000),
                "output_tokens": random.randint(500, 50000),
                "total_cost_usd": round(random.uniform(1, 100), 2)
            },
            "model_performance": {
                "accuracy_score": round(random.uniform(0.8, 0.98), 3),
                "confidence_average": round(random.uniform(0.7, 0.95), 3),
                "hallucination_rate": round(random.uniform(0, 0.1), 3)
            }
        },
        "business_metrics": {
            "daily_active_users": random.randint(50, 5000),
            "monthly_active_users": random.randint(200, 20000),
            "average_session_duration_minutes": round(random.uniform(5, 45), 2),
            "user_retention_rate": round(random.uniform(0.6, 0.9), 3),
            "feature_usage": {
                "rag_queries": random.randint(100, 10000),
                "file_uploads": random.randint(20, 1000),
                "conversations_created": random.randint(50, 2000),
                "messages_sent": random.randint(500, 50000)
            }
        },
        "timestamp": datetime.utcnow().isoformat(),
        "collection_interval_seconds": 60,
        "data_retention_days": 30
    }


# Utility functions for generating complex test scenarios

def generate_conversation_thread(message_count: int = 10) -> List[Dict[str, Any]]:
    """Generate a realistic conversation thread with alternating user/AI messages."""
    conversation_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    messages = []
    
    for i in range(message_count):
        is_user = i % 2 == 0
        
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": "user" if is_user else "assistant",
            "content": fake.sentence() if is_user else fake.text(max_nb_chars=200),
            "timestamp": fake.date_time_between(start_date="-1d", end_date="now").isoformat(),
            "metadata": {
                "sources": [fake.file_name() for _ in range(random.randint(0, 3))] if not is_user else None,
                "confidence": round(random.uniform(0.7, 0.95), 2) if not is_user else None
            }
        }
        messages.append(message)
    
    return messages


def generate_project_with_documents(document_count: int = 5) -> Dict[str, Any]:
    """Generate a project with associated documents."""
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "name": fake.company(),
        "description": fake.text(max_nb_chars=300),
        "created_at": fake.date_time_between(start_date="-6m", end_date="now").isoformat()
    }
    
    documents = []
    for i in range(document_count):
        doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "filename": fake.file_name(extension="md"),
            "content": fake.text(max_nb_chars=1000),
            "created_at": fake.date_time_between(start_date="-3m", end_date="now").isoformat()
        }
        documents.append(doc)
    
    return {"project": project, "documents": documents}


def generate_api_test_scenarios() -> List[Dict[str, Any]]:
    """Generate realistic API test scenarios with expected responses."""
    scenarios = [
        {
            "name": "successful_login",
            "request": {
                "method": "POST",
                "endpoint": "/api/v1/auth/login",
                "payload": {"username": "testuser", "password": "password123"}
            },
            "expected_response": {
                "status_code": 200,
                "body": {"access_token": "jwt_token", "token_type": "bearer"}
            }
        },
        {
            "name": "invalid_login",
            "request": {
                "method": "POST",
                "endpoint": "/api/v1/auth/login",
                "payload": {"username": "invalid", "password": "wrong"}
            },
            "expected_response": {
                "status_code": 401,
                "body": {"error": "Invalid credentials"}
            }
        },
        {
            "name": "create_project",
            "request": {
                "method": "POST",
                "endpoint": "/api/v1/projects",
                "payload": {
                    "name": "Test Project",
                    "description": "A test project",
                    "github_repo": "https://github.com/user/repo"
                }
            },
            "expected_response": {
                "status_code": 201,
                "body": {"id": "uuid", "name": "Test Project", "status": "created"}
            }
        }
    ]
    return scenarios