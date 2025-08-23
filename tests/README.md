# WhatsApp AI Chatbot - Test Suite

This directory contains the comprehensive test suite for the WhatsApp-like AI Chatbot application.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m performance   # Performance tests only
pytest -m ui            # UI tests only
```

## Test Structure

```
tests/
├── conftest.py                 # Global fixtures and configuration
├── unit/                       # Unit tests (70% of test suite)
│   ├── test_database_models.py # Database model tests
│   ├── test_rag_system.py     # RAG system unit tests
│   └── test_core_utils.py     # Utility function tests
├── integration/               # Integration tests (20% of test suite)
│   ├── test_api_endpoints.py  # API endpoint tests
│   └── test_rag_integration.py # RAG integration tests
├── performance/               # Performance tests (5% of test suite)
│   └── test_rag_benchmarks.py # Performance benchmarks
├── ui/                        # UI tests (5% of test suite)
│   └── test_flet_components.py # Flet UI component tests
├── fixtures/                  # Test data and fixtures
├── utils/                     # Test utilities and helpers
└── reports/                   # Generated test reports
    ├── coverage/              # Coverage HTML reports
    ├── pytest_report.html    # Test execution report
    └── junit.xml             # CI/CD integration format
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Execution Time**: Fast (< 100ms each)
- **Coverage Target**: 85%+
- **Dependencies**: Mocked external services

**Key Test Files:**
- `test_database_models.py` - SQLAlchemy models, relationships, constraints
- `test_rag_system.py` - RAG system core functionality
- `test_core_utils.py` - Utility functions, validation, error handling

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and API endpoints
- **Execution Time**: Medium (< 5s each)
- **Coverage Target**: 90%+ for critical paths
- **Dependencies**: Test database, mocked external APIs

**Key Test Files:**
- `test_api_endpoints.py` - FastAPI endpoint functionality
- `test_rag_integration.py` - End-to-end RAG pipeline testing

### Performance Tests (`tests/performance/`)
- **Purpose**: Validate performance requirements and detect regressions
- **Execution Time**: Long (may take minutes)
- **Targets**: Response times, throughput, memory usage
- **When to Run**: CI/CD, before releases, nightly builds

**Key Test Files:**
- `test_rag_benchmarks.py` - RAG query performance, document processing speed

### UI Tests (`tests/ui/`)
- **Purpose**: Test Flet UI components and user interactions
- **Execution Time**: Medium
- **Focus**: Component behavior, user workflows, accessibility
- **Tools**: Flet testing utilities, Selenium for complex scenarios

**Key Test Files:**
- `test_flet_components.py` - Chat interface, message bubbles, UI interactions

## Test Configuration

### pytest.ini
Main configuration file defining:
- Test discovery patterns
- Coverage requirements (80% minimum)
- Test markers for categorization
- Output formatting options
- Asyncio test configuration

### conftest.py
Global test configuration providing:
- Fixtures for mock services (OpenAI, ChromaDB, GitHub)
- Test data generators using Faker
- Database session management
- Performance benchmarking utilities
- Automatic cleanup procedures

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Component-specific tests
pytest -m rag              # RAG system tests
pytest -m database         # Database tests
pytest -m api              # API endpoint tests
pytest -m ui               # UI component tests

# Performance categories
pytest -m fast             # Quick tests (< 1s)
pytest -m slow             # Longer tests (> 5s)
pytest -m performance      # Performance benchmarks

# External dependencies
pytest -m requires_openai  # Tests needing OpenAI API
pytest -m requires_github  # Tests needing GitHub API
pytest -m requires_network # Tests needing internet

# Test types
pytest -m unit             # Unit tests
pytest -m integration     # Integration tests
pytest -m security        # Security tests
```

## Running Tests

### Local Development

```bash
# Basic test execution
pytest                          # Run all tests
pytest tests/unit/             # Run unit tests only
pytest tests/integration/      # Run integration tests only

# With coverage reporting
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Parallel execution (faster)
pytest -n auto                 # Auto-detect CPU cores
pytest -n 4                    # Use 4 processes

# Verbose output
pytest -v                      # Verbose test names
pytest -vv                     # Extra verbose with details
pytest -s                      # Show print statements

# Generate reports
pytest --html=tests/reports/report.html --self-contained-html
pytest --junitxml=tests/reports/junit.xml

# Debug options
pytest --pdb                   # Drop into debugger on failure
pytest --lf                    # Run last failed tests
pytest --tb=short              # Shorter traceback format
```

### Specific Test Examples

```bash
# Run single test file
pytest tests/unit/test_rag_system.py

# Run specific test function
pytest tests/unit/test_rag_system.py::TestRAGSystem::test_query_processing

# Run tests matching pattern
pytest -k "test_rag"           # All tests with "rag" in name
pytest -k "not slow"           # Exclude slow tests

# Run with custom markers
pytest -m "unit and not requires_openai"  # Unit tests without OpenAI
```

### CI/CD Pipeline

Tests run automatically on:
- **Pull Requests**: Unit and integration tests
- **Main Branch**: Full test suite including performance
- **Nightly**: Comprehensive testing with security scans
- **Release**: Complete validation including UI tests

**GitHub Actions Workflow:**
- Code quality checks (linting, formatting, security)
- Multi-Python version testing (3.10, 3.11, 3.12)
- Parallel test execution
- Coverage reporting to Codecov
- Performance regression detection
- Docker image building and testing

## Test Data Management

### Fixtures (conftest.py)
Reusable test data and mock services:
- `sample_project` - Test project data
- `sample_conversation` - Test conversation data
- `sample_messages` - Test message data
- `mock_openai_client` - Mocked OpenAI API
- `mock_chroma_client` - Mocked ChromaDB
- `mock_github_client` - Mocked GitHub API

### Factory Pattern
```python
# Using factory-boy for complex data generation
from tests.factories import ProjectFactory, MessageFactory

def test_project_creation():
    project = ProjectFactory()  # Generates realistic test data
    assert project.name is not None
```

### Faker Integration
```python
from faker import Faker
fake = Faker()

def test_with_fake_data():
    email = fake.email()
    text = fake.text(max_nb_chars=100)
    timestamp = fake.date_time()
```

## Mocking Strategy

### External Services
All external services are mocked by default:
- **OpenAI API**: Mocked responses for embeddings and chat completions
- **ChromaDB**: Mocked vector storage operations
- **GitHub API**: Mocked repository and file operations
- **Database**: In-memory SQLite for unit tests

### Mock Examples
```python
# OpenAI API Mock
@patch('src.core.rag_system.OpenAIEmbeddings')
def test_embedding_generation(mock_embeddings):
    mock_embeddings.return_value.embed_documents.return_value = [[0.1] * 1536]
    # Test implementation

# Database Mock
@pytest.fixture
async def mock_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Setup and yield session
```

## Performance Testing

### Benchmarks
Performance tests validate:
- **RAG Query Response Time**: < 2 seconds
- **Document Processing**: < 30 seconds for 10MB
- **API Response Time**: < 500ms
- **Memory Usage**: < 500MB increase during processing
- **Concurrent Users**: Support for 10+ simultaneous queries

### Running Performance Tests
```bash
# Run performance test suite
pytest tests/performance/ -v

# Run with benchmarking
pytest tests/performance/ --benchmark-json=benchmark.json

# Compare performance over time
pytest tests/performance/ --benchmark-compare=baseline.json
```

### Performance Monitoring
```python
@pytest.mark.performance
async def test_query_performance(performance_benchmark):
    async def query_operation():
        return await rag_system.query("test query", project_id=1)
    
    result, execution_time = performance_benchmark(asyncio.run, query_operation())
    assert execution_time < 2.0  # 2 second requirement
```

## Coverage Requirements

### Minimum Coverage Targets
- **Overall**: 80% minimum
- **Critical Components**: 90%+ (RAG system, API endpoints)
- **Security Code**: 100%
- **Database Models**: 85%
- **UI Components**: 70%

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
# View at htmlcov/index.html

# Terminal coverage report
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

### Coverage Exclusions
Some code is excluded from coverage requirements:
- Debug code blocks
- Exception handling for unreachable errors
- Type checking blocks (`if TYPE_CHECKING:`)
- Abstract method definitions

## Database Testing

### Test Database Setup
```python
# Automatic test database setup via fixtures
async def test_database_operation(async_session):
    # async_session is automatically provided
    # In-memory SQLite database, cleaned up after test
    project = Project(name="Test")
    async_session.add(project)
    await async_session.commit()
```

### Database Test Patterns
- **Isolation**: Each test gets clean database state
- **Transactions**: Use database transactions for rollback
- **Realistic Data**: Use factories for complex relationships
- **Performance**: Test query performance with indexes

## Security Testing

### Security Test Categories
- **Input Validation**: SQL injection, XSS prevention
- **Authentication**: API endpoint protection
- **Authorization**: Role-based access control
- **Data Sanitization**: PII and sensitive data handling

### Running Security Tests
```bash
# Run security-focused tests
pytest -m security

# Run security tools
bandit -r src/                  # Security linting
safety check                   # Dependency vulnerability check
```

## Debugging Tests

### Common Issues and Solutions

**1. Async Test Problems**
```python
# Wrong: Missing async/await
def test_async_function():
    result = async_function()  # Returns coroutine

# Correct: Proper async handling
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
```

**2. Mock Configuration Issues**
```python
# Wrong: Sync mock for async function
mock_service.method.return_value = "value"

# Correct: AsyncMock for async methods
mock_service = AsyncMock()
mock_service.method.return_value = "value"
```

**3. Test Isolation Problems**
```python
# Wrong: Shared state between tests
class_variable = []  # Mutated across tests

# Correct: Fresh state per test
@pytest.fixture
def clean_list():
    return []
```

### Debugging Commands
```bash
# Run with debugger
pytest --pdb                   # Drop into pdb on failure
pytest --pdb-trace             # Start pdb at test start

# Verbose output
pytest -s                      # Show print statements
pytest -v                      # Verbose test names
pytest -vv                     # Extra verbose output

# Run subset for debugging
pytest -lf                     # Last failed only
pytest -x                      # Stop on first failure
pytest --maxfail=3             # Stop after 3 failures
```

## Test Maintenance

### Regular Tasks
- **Weekly**: Review coverage reports and update low-coverage areas
- **Sprint End**: Update test documentation and remove obsolete tests
- **Monthly**: Performance baseline updates and optimization
- **Release**: Full test suite audit and cleanup

### Best Practices
- **Keep Tests Simple**: One concept per test
- **Use Descriptive Names**: Test name should explain what's being tested
- **Test Edge Cases**: Boundary conditions and error scenarios
- **Maintain Test Data**: Keep fixtures and factories up to date
- **Regular Cleanup**: Remove obsolete tests and unused fixtures

## Contributing to Tests

### Adding New Tests
1. Choose appropriate test category (unit/integration/performance/ui)
2. Use existing fixtures and patterns
3. Add appropriate pytest markers
4. Follow naming conventions
5. Include docstrings for complex test logic
6. Update this README if adding new test patterns

### Test Review Checklist
- [ ] Tests are properly categorized with markers
- [ ] Mocks are used for external dependencies
- [ ] Tests are isolated and independent
- [ ] Edge cases and error conditions are covered
- [ ] Performance implications are considered
- [ ] Documentation is updated if needed

## Resources

### Documentation
- [Testing Guide](../docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

### Tools and Libraries
- `pytest` - Core testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-mock` - Enhanced mocking capabilities
- `pytest-benchmark` - Performance benchmarking
- `factory-boy` - Test data generation
- `faker` - Realistic fake data
- `httpx` - Async HTTP client for API testing

---

**Need Help?**
- Check the [Testing Guide](../docs/TESTING_GUIDE.md) for detailed explanations
- Look at existing tests for patterns and examples
- Ask team members for test strategy questions
- Consult pytest documentation for advanced features