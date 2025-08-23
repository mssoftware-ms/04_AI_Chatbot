# WhatsApp-like AI Chatbot

A modern, scalable chatbot application with AI-powered conversations, project management capabilities, and WhatsApp-style interface.

## Project Structure

```
03_AI_Chatbot/
├── src/                    # Source code
│   ├── core/              # Core business logic
│   ├── database/          # Database models and operations
│   ├── ui/                # User interface components
│   ├── api/               # FastAPI routes and endpoints
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── config/                # Configuration files
├── scripts/               # Setup and utility scripts
├── data/                  # Data storage
│   ├── projects/          # Project files
│   └── uploads/           # User uploads
├── docs/                  # Documentation
└── logs/                  # Application logs
```

## Quick Start

1. **Setup the project:**
   ```bash
   python scripts/setup.py
   ```

2. **Activate virtual environment:**
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Update with your API keys and settings

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Features

- 🤖 AI-powered chat conversations
- 📁 Project management capabilities
- 📄 File upload and processing
- 🔐 User authentication and security
- 🌐 RESTful API with FastAPI
- 🎨 Modern WhatsApp-style interface
- 📊 Analytics and monitoring
- 🧪 Comprehensive testing suite

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

Key configurations:
- AI service API keys (OpenAI, Anthropic)
- Database settings
- File upload limits
- Security settings
- Feature flags

## Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests:**
   ```bash
   python scripts/run_tests.py
   # or
   pytest tests/ -v --cov=src
   ```

3. **Code formatting:**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **FastAPI** for the web framework and API
- **SQLAlchemy** for database operations
- **Streamlit** for the user interface
- **LangChain** for AI integrations
- **ChromaDB** for vector storage
- **Structured logging** for monitoring

## License

MIT License - see LICENSE file for details.