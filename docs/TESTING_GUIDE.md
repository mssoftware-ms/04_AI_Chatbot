# Testing Guide for WhatsApp AI Chatbot

## Overview

This document provides comprehensive guidelines for testing the WhatsApp-like AI Chatbot application. Our testing strategy ensures >80% code coverage and maintains high quality throughout the development lifecycle.

## Testing Philosophy

### Test-Driven Development (TDD)
- Write tests before implementation
- Red-Green-Refactor cycle
- Tests as living documentation
- Continuous feedback loop

### Testing Pyramid
```
        /\
       /  \
      /    \
     / UI   \
    /________\
   /          \
  / Integration \
 /________________\
/                  \
/       Unit        \
/____________________\
```

- **Unit Tests (70%)**: Fast, isolated, focused
- **Integration Tests (20%)**: Component interaction
- **UI/E2E Tests (10%)**: User workflow validation

## Test Categories

### 1. Unit Tests (`tests/unit/`)
Test individual components in isolation.

**Characteristics:**
- Fast execution (< 100ms each)
- No external dependencies
- High code coverage
- Mock external services

**Example Structure:**
```python
class TestRAGSystem:
    @pytest.mark.unit
    @pytest.mark.fast
    async def test_document_chunking(self, mock_text_splitter):
        # Test implementation
        pass
```

### 2. Integration Tests (`tests/integration/`)
Test component interactions and API endpoints.

**Characteristics:**
- Medium execution time (< 5s each)
- Real database connections
- API endpoint testing
- Service integration

**Example Structure:**
```python
class TestAPIEndpoints:
    @pytest.mark.integration
    @pytest.mark.api
    async def test_create_project(self, async_client):
        # Test implementation
        pass
```

### 3. Performance Tests (`tests/performance/`)
Test system performance and scalability.

**Characteristics:**
- Longer execution time
- Load testing scenarios
- Memory usage monitoring
- Response time validation

**Example Structure:**
```python
class TestRAGPerformance:
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_query_response_time(self, performance_benchmark):
        # Test implementation
        pass
```

### 4. UI Tests (`tests/ui/`)
Test user interface components and interactions.

**Characteristics:**
- Visual component testing
- User interaction simulation
- Accessibility validation
- Responsive design testing

## Test Configuration

### pytest.ini Configuration
Located at project root, defines:
- Test discovery patterns
- Coverage requirements (80% minimum)
- Test markers for categorization
- Output formatting
- Asyncio configuration

### conftest.py Fixtures
Global fixtures provide:
- Mock services (OpenAI, ChromaDB, GitHub)
- Test data generators
- Database sessions
- Performance benchmarking
- Cleanup utilities

## Test Markers

Use pytest markers to categorize and filter tests:

```bash
# Run only unit tests
pytest -m unit

# Run fast tests only
pytest -m fast

# Run specific component tests
pytest -m rag

# Run tests excluding slow ones
pytest -m "not slow"

# Run performance tests
pytest -m performance
```

### Available Markers
- `unit` - Unit tests
- `integration` - Integration tests
- `api` - API endpoint tests
- `database` - Database-related tests
- `rag` - RAG system tests
- `ui` - User interface tests
- `performance` - Performance tests
- `security` - Security tests
- `fast` - Fast tests (< 1s)
- `slow` - Slow tests (> 5s)
- `requires_openai` - Requires OpenAI API
- `requires_github` - Requires GitHub API
- `requires_network` - Requires internet

## Writing Effective Tests

### Test Naming Convention
```python
def test_[what_is_being_tested]_[under_what_circumstances]_[expected_behavior]:
    """Clear docstring describing the test purpose."""
    pass

# Examples:
def test_rag_query_with_valid_input_returns_accurate_response():
def test_database_connection_with_invalid_url_raises_exception():
def test_message_bubble_with_long_text_wraps_correctly():
```

### Test Structure (AAA Pattern)
```python
async def test_example():
    # Arrange - Set up test data and mocks
    mock_client = MagicMock()
    test_data = {"key": "value"}
    
    # Act - Execute the function under test
    result = await function_under_test(test_data)
    
    # Assert - Verify the expected outcome
    assert result.success is True
    assert result.data == expected_data
    mock_client.method.assert_called_once()
```

### Effective Mocking
```python
# Mock external services
@patch('src.core.rag_system.OpenAIEmbeddings')
async def test_embedding_generation(mock_embeddings):
    mock_embeddings.return_value.embed_documents.return_value = [[0.1] * 1536]
    # Test implementation

# Mock async operations
@pytest.fixture
def mock_async_service():
    mock = AsyncMock()
    mock.process.return_value = {"status": "success"}
    return mock
```

### Test Data Management
```python
# Use fixtures for reusable test data
@pytest.fixture
def sample_project():
    return {
        "id": 1,
        "name": "Test Project",
        "description": "A test project",
        "settings": {"model": "gpt-4o-mini"}
    }

# Use factory_boy for complex data generation
class ProjectFactory(factory.Factory):
    class Meta:
        model = dict
    
    name = factory.Faker('company')
    description = factory.Faker('text', max_nb_chars=200)
```

## Running Tests

### Local Development
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_rag_system.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto

# Run tests and generate HTML report
pytest --html=tests/reports/report.html
```

### Continuous Integration
Tests run automatically on:
- Pull requests
- Push to main/develop branches
- Nightly comprehensive testing
- Performance regression checks

### Test Coverage Requirements
- Minimum 80% overall coverage
- 90% coverage for critical components (RAG, API)
- 100% coverage for security-related code
- Coverage reports generated for each run

## Performance Testing

### Benchmarking Guidelines
```python
@pytest.mark.performance
async def test_query_performance(performance_benchmark):
    async def query_operation():
        return await rag_system.query("test", project_id=1)
    
    result, execution_time = performance_benchmark(asyncio.run, query_operation())
    
    # Assert performance requirements
    assert execution_time < 2.0  # 2 second limit
    assert result.processing_time_ms < 1500
```

### Performance Thresholds
- Single RAG query: < 2 seconds
- Document processing: < 30 seconds for 10MB
- API response time: < 500ms
- UI interactions: < 100ms
- Memory usage: < 500MB increase during tests

## Mocking External Services

### OpenAI API
```python
@pytest.fixture
def mock_openai_client():
    mock = AsyncMock()
    mock.chat.completions.create.return_value.choices[0].message.content = "AI response"
    mock.embeddings.create.return_value.data[0].embedding = [0.1] * 1536
    return mock
```

### ChromaDB
```python
@pytest.fixture
def mock_chroma_client():
    mock = MagicMock()
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Test doc 1", "Test doc 2"]],
        "metadatas": [[{"source": "doc1.txt"}, {"source": "doc2.txt"}]],
        "distances": [[0.1, 0.2]]
    }
    mock.get_or_create_collection.return_value = mock_collection
    return mock
```

### GitHub API
```python
@pytest.fixture
def mock_github_client():
    mock = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_contents.return_value = [
        MagicMock(decoded_content=b"# README\nTest content")
    ]
    mock.get_repo.return_value = mock_repo
    return mock
```

## Database Testing

### Test Database Setup
```python
@pytest.fixture
async def test_db_session():
    # Create in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()
```

### Database Test Patterns
```python
async def test_create_project(test_db_session):
    # Test database operations
    project = Project(name="Test", description="Test project")
    test_db_session.add(project)
    await test_db_session.commit()
    
    # Verify data persistence
    result = await test_db_session.execute(
        select(Project).where(Project.name == "Test")
    )
    saved_project = result.scalar_one()
    assert saved_project.name == "Test"
```

## UI Testing with Flet

### Component Testing
```python
def test_message_bubble_creation():
    app = WhatsAppChatApp()
    message = {
        "content": "Test message",
        "timestamp": datetime.now().isoformat(),
        "role": "user"
    }
    
    bubble = app.create_message_bubble(message, is_user=True)
    
    assert isinstance(bubble, ft.Container)
    assert bubble.alignment == ft.alignment.center_right
```

### Interaction Testing
```python
async def test_send_message_interaction():
    app = WhatsAppChatApp()
    app.websocket = AsyncMock()
    app.message_input.value = "Hello!"
    
    await app.send_message()
    
    app.websocket.send.assert_called_once()
    assert app.message_input.value == ""
```

## Error Testing

### Exception Handling
```python
async def test_rag_query_with_invalid_project_raises_error():
    rag_system = RAGSystem()
    
    with pytest.raises(ProjectNotFoundError):
        await rag_system.query("test", project_id=999)
```

### Error Recovery
```python
async def test_rag_system_recovers_from_api_failure():
    with patch('openai.ChatCompletion.create', side_effect=APIError()):
        rag_system = RAGSystem()
        response = await rag_system.query("test", project_id=1)
        
        assert "error" in response.answer.lower()
        assert response.confidence == 0.0
```

## Security Testing

### Input Validation
```python
def test_project_name_validation_prevents_injection():
    validator = InputValidator()
    
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE projects; --",
        "../../../etc/passwd"
    ]
    
    for malicious_input in malicious_inputs:
        with pytest.raises(ValidationError):
            validator.validate_project_name(malicious_input)
```

### Authentication Testing
```python
async def test_api_requires_authentication():
    async with AsyncClient(app=app) as client:
        response = await client.post("/api/projects", json={})
        assert response.status_code == 401
```

## Debugging Tests

### Common Issues and Solutions

**1. Async Test Issues**
```python
# Wrong - mixing sync and async
def test_async_function():
    result = async_function()  # Returns coroutine, not result

# Correct - proper async testing
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
```

**2. Mock Configuration**
```python
# Wrong - mock not properly configured
mock_service.method.return_value = "value"
# But method is async, needs AsyncMock

# Correct - use AsyncMock for async methods
mock_service = AsyncMock()
mock_service.method.return_value = "value"
```

**3. Database State Issues**
```python
# Wrong - tests affecting each other
def test_create_user():
    user = create_user("test@example.com")
    # User persists to next test

# Correct - proper cleanup
def test_create_user(test_db_session):
    user = create_user("test@example.com")
    # Session automatically cleaned up
```

### Test Debugging Tools
```bash
# Run single test with full output
pytest -s -v tests/unit/test_specific.py::test_function

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Show detailed assertion info
pytest -vv

# Run with profiling
pytest --profile
```

## Test Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Review test coverage reports
2. **Sprint End**: Update test documentation
3. **Monthly**: Performance baseline updates
4. **Release**: Comprehensive test audit

### Refactoring Tests
- Keep tests simple and focused
- Remove duplicate test logic
- Update tests when requirements change
- Maintain test data consistency

### Test Performance Optimization
- Use appropriate test fixtures
- Minimize setup/teardown time
- Run tests in parallel where possible
- Cache expensive operations

## CI/CD Integration

### GitHub Actions Workflow
- Automated testing on all PRs
- Parallel test execution
- Coverage reporting
- Performance regression detection
- Security vulnerability scanning

### Test Reports
- JUnit XML for CI integration
- HTML coverage reports
- Performance benchmarks
- Security scan results

## Best Practices Summary

### DO:
✅ Write tests before implementation (TDD)  
✅ Use descriptive test names  
✅ Mock external dependencies  
✅ Test edge cases and error conditions  
✅ Maintain >80% code coverage  
✅ Use appropriate test markers  
✅ Keep tests isolated and independent  
✅ Clean up test data  

### DON'T:
❌ Test implementation details  
❌ Create interdependent tests  
❌ Ignore test failures  
❌ Skip error case testing  
❌ Use real external services in tests  
❌ Write overly complex test setups  
❌ Leave broken tests in codebase  

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

### Tools
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-mock` - Enhanced mocking
- `factory-boy` - Test data generation
- `faker` - Fake data generation

### IDE Integration
- VS Code: Python Test Explorer
- PyCharm: Integrated test runner
- Command line: pytest with various plugins

---

**Remember**: Good tests are your safety net. They enable confident refactoring, catch regressions early, and serve as executable documentation for your codebase.