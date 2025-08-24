# WhatsApp AI Chatbot - Comprehensive Startup Guide

## 🚀 Quick Start (Choose Your Environment)

### For WSL/Linux Users (Current Setup)
```bash
cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot
source venv/bin/activate
python app.py
```

### For Windows Users (Migration Required)
```cmd
cd D:\03_GIT\02_Python\04_AI_Chatbot
install_fixed.bat
chatbot.bat
```

## 📋 Pre-Installation Requirements

### System Requirements
- **Python**: 3.11 or higher (3.12.8 detected ✅)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Disk Space**: 2GB for full installation
- **Internet**: Required for AI API calls and package installation
- **OS**: Windows 10/11, WSL2, or Linux

### Environment Check
```bash
# Check Python version
python --version

# Check pip version  
pip --version

# Check available space
df -h . # Linux/WSL
# OR
dir # Windows
```

## 🔧 Installation Guide

### Option 1: WSL/Linux Environment (Recommended for Current Setup)

#### Step 1: Verify Environment
```bash
# Check WSL version
wsl --version

# Verify current setup
ls -la venv/  # Should show bin/ directory
which python  # Should show Python path
```

#### Step 2: Fix Dependencies
```bash
# Navigate to project
cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show project path)
echo $VIRTUAL_ENV

# Fix specific dependency conflicts
pip install pytest-cov==5.0.0  # Fix queenflow conflict
pip install pydantic-core==2.23.4  # Fix pydantic conflict

# Update all dependencies
pip install -r requirements.txt

# Verify no conflicts
pip check
```

#### Step 3: Configuration
```bash
# Create .env file if it doesn't exist
cp .env.example .env  # If available
# OR manually create .env

# Edit configuration
nano .env  # Or use your preferred editor
```

**Required .env Variables**:
```env
# API Keys (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8550
UI_PORT=8551
RELOAD=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./data/chatbot.db

# AI Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=100

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Step 4: Database Initialization
```bash
# Create data directories
mkdir -p data/chroma data/uploads logs

# Initialize database (if migrations exist)
python -c "from src.database.session import init_db; init_db()"

# OR run migrations
# alembic upgrade head
```

#### Step 5: Start Application
```bash
# Start full application (backend + UI)
python app.py

# OR start components separately
python app.py backend  # API server only
python app.py ui      # UI only  
python app.py test    # Run tests
```

### Option 2: Windows Native Environment

#### Step 1: Clean Installation
```cmd
# Remove existing WSL environment
rmdir /s venv

# Verify Windows Python
python --version
where python
```

#### Step 2: Create Windows Environment
```cmd
# Create virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate.bat

# Verify activation
echo %VIRTUAL_ENV%
```

#### Step 3: Install Dependencies
```cmd
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Fix any conflicts
pip install pytest-cov==5.0.0
pip install pydantic-core==2.23.4

# Verify installation
pip check
```

#### Step 4: Use Batch Files
```cmd
# Start application
chatbot.bat

# OR use quick start
quick_start.bat

# OR manual start
python app.py
```

### Option 3: Docker Environment (Recommended for Production)

#### Step 1: Create Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/chroma data/uploads logs

EXPOSE 8550 8551

CMD ["python", "app.py"]
```

#### Step 2: Build and Run
```bash
# Build image
docker build -t whatsapp-ai-chatbot .

# Run container
docker run -p 8550:8550 -p 8551:8551 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  whatsapp-ai-chatbot
```

## 🔍 Verification and Testing

### Health Check
```bash
# Run health check script
python docs/health_check.py

# Manual verification
curl http://localhost:8550/health
curl http://localhost:8550/api/v1/status
```

### Test Suite
```bash
# Run all tests
python app.py test

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest -m "not slow" -v  # Skip slow tests
```

### System Information
```bash
# Check system resources
python -c "
import sys
import platform
import psutil
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'RAM: {psutil.virtual_memory().total / (1024**3):.1f}GB')
print(f'CPU: {psutil.cpu_count()} cores')
"
```

## 🎯 Application Usage

### Web Interface
1. **Start application**: `python app.py`
2. **Open browser**: http://localhost:8551
3. **API documentation**: http://localhost:8550/docs

### API Usage
```python
import requests

# Send message
response = requests.post("http://localhost:8550/api/v1/chat", json={
    "message": "Hello, how can you help me?",
    "conversation_id": "unique-id-123"
})

print(response.json())
```

### WebSocket Connection
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8550/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Send message
ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Hello!',
    conversation_id: 'unique-id-123'
}));
```

## 🛠️ Configuration Management

### Environment Variables Reference

#### Core Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8550` | API server port |
| `UI_PORT` | `8551` | UI server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RELOAD` | `false` | Hot reload (dev only) |

#### AI Configuration  
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | `100` | Chunk overlap size |

#### Database Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/chatbot.db` | Database connection |
| `CHROMA_PATH` | `./data/chroma` | Vector database path |

### Custom Configuration
```python
# config/custom_settings.py
from pydantic_settings import BaseSettings

class CustomSettings(BaseSettings):
    # Override default settings
    custom_feature_enabled: bool = True
    max_message_length: int = 4000
    
    class Config:
        env_file = ".env"
        env_prefix = "CUSTOM_"

# Usage in application
from config.custom_settings import CustomSettings
custom_config = CustomSettings()
```

## 🚨 Troubleshooting Common Issues

### Issue: "Cannot activate virtual environment"
```bash
# Check environment type
ls venv/

# If shows 'bin/': Use Linux/WSL activation
source venv/bin/activate

# If shows 'Scripts/': Use Windows activation
venv\Scripts\activate.bat
```

### Issue: "Module not found"
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt

# Check specific module
python -c "import fastapi; print(fastapi.__version__)"
```

### Issue: "Port already in use"
```bash
# Find process using port
netstat -tulpn | grep :8550  # Linux
netstat -ano | findstr :8550  # Windows

# Kill process (use PID from above)
kill -9 <PID>  # Linux
taskkill /F /PID <PID>  # Windows

# OR change port in .env
echo "PORT=8552" >> .env
```

### Issue: "Database connection failed"
```bash
# Check database file
ls -la data/chatbot.db

# Create data directory if missing
mkdir -p data

# Reinitialize database
python -c "from src.database.session import init_db; init_db()"
```

### Issue: "AI API calls failing"
```bash
# Check API key
echo $OPENAI_API_KEY  # Should not be empty

# Test API connection
python -c "
import openai
client = openai.OpenAI()
try:
    models = client.models.list()
    print('✅ OpenAI connection successful')
except Exception as e:
    print(f'❌ OpenAI connection failed: {e}')
"
```

## 📊 Performance Optimization

### Resource Monitoring
```bash
# Monitor system resources
top  # Linux/WSL
# OR
htop  # If available

# Monitor specific process
ps aux | grep python

# Check memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB')
"
```

### Performance Tips
1. **Use SSD storage** for better database performance
2. **Increase RAM** if processing large documents
3. **Enable GPU** for faster embedding generation
4. **Use caching** for frequently accessed data
5. **Monitor logs** for performance bottlenecks

## 🔐 Security Considerations

### Production Security Checklist
- [ ] Change default secret key
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS in production
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Monitor for suspicious activity

### Secure Configuration
```env
# Strong secret key (generate new one)
SECRET_KEY=your-super-secret-key-here-min-32-chars

# Production database (not SQLite)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Restrict host binding in production
HOST=127.0.0.1

# Disable debug features
RELOAD=false
LOG_LEVEL=WARNING
```

## 📈 Monitoring and Maintenance

### Log Monitoring
```bash
# View application logs
tail -f logs/app.log

# Filter specific log levels
grep "ERROR" logs/app.log
grep "WARNING" logs/app.log
```

### Database Maintenance
```bash
# Backup database
cp data/chatbot.db data/chatbot_backup_$(date +%Y%m%d).db

# Check database size
du -h data/chatbot.db

# Vacuum SQLite database (optimize)
sqlite3 data/chatbot.db "VACUUM;"
```

### Regular Maintenance Tasks
1. **Daily**: Check logs for errors
2. **Weekly**: Backup database
3. **Monthly**: Update dependencies
4. **Quarterly**: Security audit

## 🎯 Next Steps

### Development Environment
1. Set up IDE with Python support
2. Install development dependencies
3. Configure pre-commit hooks
4. Set up debugging environment

### Production Deployment
1. Set up reverse proxy (nginx)
2. Configure SSL certificates
3. Set up monitoring (Prometheus/Grafana)
4. Implement CI/CD pipeline

### Feature Development
1. Review API documentation
2. Understand RAG system architecture
3. Study testing framework
4. Plan new feature implementation

---

**Startup Guide Created By**: SYSTEM ANALYST Agent (Hive Mind Collective)  
**Last Updated**: 2025-08-24  
**Version**: 1.0  
**Status**: Complete

For additional help, see:
- `docs/TROUBLESHOOTING_GUIDE.md`
- `docs/SYSTEM_ANALYSIS_REPORT.md`
- `docs/TESTING_VALIDATION_REPORT.md`

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>