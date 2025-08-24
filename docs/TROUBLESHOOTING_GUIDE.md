# WhatsApp AI Chatbot - Troubleshooting Guide

## 🔧 Quick Diagnostic Commands

### System Check
```bash
# Run comprehensive system check
python -c "
import sys
import os
import subprocess
from pathlib import Path

print('🏥 WhatsApp AI Chatbot - Quick Diagnostics')
print('=' * 50)

# Python version
print(f'Python: {sys.version}')

# Environment detection
venv_path = Path('venv')
if venv_path.exists():
    if (venv_path / 'bin' / 'python').exists():
        print('Environment: WSL/Linux ✅')
    elif (venv_path / 'Scripts' / 'python.exe').exists():
        print('Environment: Windows ✅')
    else:
        print('Environment: Invalid ❌')
else:
    print('Environment: Not found ❌')

# Virtual environment
venv_active = os.environ.get('VIRTUAL_ENV')
if venv_active:
    print(f'Virtual Env: Active ✅ ({venv_active})')
else:
    print('Virtual Env: Not active ❌')

# Dependencies check
try:
    result = subprocess.run([sys.executable, '-m', 'pip', 'check'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print('Dependencies: Compatible ✅')
    else:
        print(f'Dependencies: Conflicts found ❌')
        print(result.stderr)
except:
    print('Dependencies: Cannot check ❌')
"
```

## 🚨 Common Issues and Solutions

### 1. Environment Issues

#### Issue: "Cannot activate virtual environment"

**Symptoms**:
- `venv\Scripts\activate.bat` file not found (Windows)
- `source venv/bin/activate` fails (WSL/Linux)
- Command not recognized errors

**Diagnosis**:
```bash
# Check environment structure
ls -la venv/  # Should show bin/ (Linux) or Scripts/ (Windows)

# Check current environment
echo $SHELL  # Linux/WSL
echo %COMSPEC%  # Windows
```

**Solutions**:

**For WSL/Linux Environment**:
```bash
# If venv has bin/ directory
source venv/bin/activate

# If activation fails, recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**For Windows Environment**:
```cmd
# If venv has Scripts/ directory
venv\Scripts\activate.bat

# If activation fails, recreate venv
rmdir /s venv
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Mixed Environment Fix (WSL venv on Windows)**:
```cmd
# Option 1: Use WSL to run
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && python app.py"

# Option 2: Recreate for Windows
rmdir /s venv
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

#### Issue: "Wrong Python version"

**Symptoms**:
- Python 3.10 or lower detected
- Syntax errors with newer Python features
- Package compatibility issues

**Solutions**:
```bash
# Check available Python versions
python3.11 --version
python3.12 --version

# Use specific Python version
python3.12 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate.bat
```

### 2. Dependency Issues

#### Issue: "Package conflicts detected"

**Current Known Conflicts**:
```
queenflow 0.1.0 requires pytest-cov<6.0,>=5.0, but you have pytest-cov 6.2.1
pydantic 2.9.2 requires pydantic-core==2.23.4, but you have pydantic-core 2.33.2
```

**Solutions**:
```bash
# Fix specific conflicts
pip install pytest-cov==5.0.0
pip install pydantic-core==2.23.4

# Force reinstall all requirements
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# Alternative: Use pip-tools for exact versions
pip install pip-tools
pip-compile requirements.txt
pip-sync
```

#### Issue: "Module not found" errors

**Symptoms**:
```
ImportError: No module named 'fastapi'
ImportError: No module named 'flet'
ModuleNotFoundError: No module named 'src'
```

**Diagnosis**:
```bash
# Check if package is installed
pip list | grep fastapi
pip list | grep flet

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if in virtual environment
echo $VIRTUAL_ENV  # Linux
echo %VIRTUAL_ENV%  # Windows
```

**Solutions**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux
# OR
venv\Scripts\activate.bat  # Windows

# Reinstall missing packages
pip install fastapi flet uvicorn

# For 'src' module not found
export PYTHONPATH=$PWD:$PYTHONPATH  # Linux
set PYTHONPATH=%CD%;%PYTHONPATH%  # Windows

# Or add to startup script
echo 'import sys; sys.path.insert(0, ".")' > sitecustomize.py
```

### 3. Application Startup Issues

#### Issue: "Port already in use"

**Symptoms**:
```
OSError: [Errno 98] Address already in use
ERROR: [Errno 48] Address already in use (Port 8550)
```

**Diagnosis**:
```bash
# Find process using port
netstat -tulpn | grep :8550  # Linux
netstat -ano | findstr :8550  # Windows

# Check all Python processes
ps aux | grep python  # Linux
tasklist | findstr python  # Windows
```

**Solutions**:
```bash
# Kill process using port (use PID from netstat)
kill -9 <PID>  # Linux
taskkill /F /PID <PID>  # Windows

# Use different ports
export PORT=8552  # Linux
set PORT=8552  # Windows

# Edit .env file
echo "PORT=8552" >> .env
echo "UI_PORT=8553" >> .env
```

#### Issue: "Database connection failed"

**Symptoms**:
```
sqlite3.OperationalError: unable to open database file
SQLAlchemy connection error
Database does not exist
```

**Diagnosis**:
```bash
# Check if database file exists
ls -la data/chatbot.db

# Check directory permissions
ls -ld data/

# Check if data directory exists
mkdir -p data
```

**Solutions**:
```bash
# Create data directories
mkdir -p data/chroma data/uploads logs

# Initialize database
python -c "
from src.database.session import engine, Base
Base.metadata.create_all(bind=engine)
print('Database initialized')
"

# Reset database if corrupted
rm -f data/chatbot.db
python -c "from src.database.session import init_db; init_db()"

# Check SQLite installation
sqlite3 --version
```

### 4. API and External Service Issues

#### Issue: "OpenAI API authentication failed"

**Symptoms**:
```
openai.error.AuthenticationError: Incorrect API key provided
401 Unauthorized
API key not found
```

**Diagnosis**:
```bash
# Check if API key is set
echo $OPENAI_API_KEY  # Should not show key for security

# Check .env file exists
ls -la .env

# Validate API key format
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
if key:
    if key.startswith('sk-'):
        print('API key format: Valid ✅')
    else:
        print('API key format: Invalid ❌')
else:
    print('API key: Not found ❌')
"
```

**Solutions**:
```bash
# Create .env file if missing
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
SECRET_KEY=your_secret_key_here
EOF

# Test API connection
python -c "
import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    models = client.models.list()
    print('✅ OpenAI connection successful')
except Exception as e:
    print(f'❌ OpenAI connection failed: {e}')
"
```

#### Issue: "ChromaDB connection issues"

**Symptoms**:
```
chromadb.errors.ChromaError: Could not connect to Chroma
Connection refused
Database lock error
```

**Solutions**:
```bash
# Check ChromaDB directory
ls -la data/chroma/

# Reset ChromaDB
rm -rf data/chroma
mkdir -p data/chroma

# Test ChromaDB
python -c "
import chromadb
try:
    client = chromadb.PersistentClient(path='./data/chroma')
    print('✅ ChromaDB connection successful')
except Exception as e:
    print(f'❌ ChromaDB connection failed: {e}')
"
```

### 5. UI and WebSocket Issues

#### Issue: "Flet UI not loading"

**Symptoms**:
- Browser shows "This site can't be reached"
- UI port not responding
- Blank page in browser

**Diagnosis**:
```bash
# Check if UI process is running
ps aux | grep flet  # Linux
tasklist | findstr flet  # Windows

# Test UI port
curl http://localhost:8551  # Should return something
telnet localhost 8551  # Should connect
```

**Solutions**:
```bash
# Start UI separately
python app.py ui

# Check firewall settings (Windows)
netsh advfirewall firewall show rule name="Python"

# Try different port
export UI_PORT=8552
python app.py ui

# Restart with debug
python -c "
import flet as ft
print(f'Flet version: {ft.__version__}')
ft.app(lambda page: page.add(ft.Text('Test')), port=8551, view=ft.WEB_BROWSER)
"
```

#### Issue: "WebSocket connection failed"

**Symptoms**:
```
WebSocket connection to 'ws://localhost:8550/ws' failed
Connection closed unexpectedly
WebSocket handshake error
```

**Solutions**:
```javascript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:8550/ws');

ws.onopen = function(event) {
    console.log('✅ WebSocket connected');
};

ws.onerror = function(error) {
    console.log('❌ WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

### 6. Performance Issues

#### Issue: "Slow response times"

**Symptoms**:
- API calls take >5 seconds
- UI becomes unresponsive
- High memory usage

**Diagnosis**:
```bash
# Monitor system resources
top -p $(pgrep -f "python app.py")  # Linux
# OR use Task Manager on Windows

# Check memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB')
print(f'CPU: {process.cpu_percent()}%')
"

# Profile application
pip install py-spy
py-spy top --pid $(pgrep -f "python app.py")
```

**Solutions**:
```bash
# Increase system resources
# - Add more RAM
# - Use SSD storage
# - Close other applications

# Optimize application
export CHUNK_SIZE=500  # Smaller chunks
export MAX_WORKERS=2   # Limit concurrent processing

# Enable caching
export ENABLE_CACHING=true
export CACHE_TTL=3600
```

### 7. File and Permission Issues

#### Issue: "Permission denied"

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied
OSError: [Errno 1] Operation not permitted
Cannot create directory
```

**Solutions**:
```bash
# Fix permissions (Linux/WSL)
chmod +x venv/bin/python
chmod -R 755 data/
chmod +x *.sh

# Run as administrator (Windows)
# Right-click Command Prompt -> "Run as administrator"

# Check file ownership
ls -la data/  # Linux
# Change ownership if needed
sudo chown -R $USER:$USER data/
```

## 🔍 Advanced Diagnostics

### Complete System Diagnostic Script

```bash
#!/bin/bash
# save as: diagnose.sh

echo "🏥 WhatsApp AI Chatbot - Complete System Diagnostics"
echo "=================================================="
echo

# System Information
echo "📊 System Information:"
echo "OS: $(uname -s) $(uname -r)"
echo "Python: $(python --version 2>&1)"
echo "Pip: $(pip --version 2>&1)"
echo "Node: $(node --version 2>&1 || echo 'Not installed')"
echo

# Directory Structure
echo "📁 Directory Structure:"
ls -la | head -10
echo

# Virtual Environment
echo "🐍 Virtual Environment:"
if [ -d "venv" ]; then
    echo "venv directory: ✅ Exists"
    if [ -f "venv/bin/python" ]; then
        echo "Type: Linux/WSL ✅"
        echo "Python: $(venv/bin/python --version 2>&1)"
    elif [ -f "venv/Scripts/python.exe" ]; then
        echo "Type: Windows ✅"
        echo "Python: $(venv/Scripts/python.exe --version 2>&1)"
    else
        echo "Type: ❌ Invalid structure"
    fi
else
    echo "venv directory: ❌ Not found"
fi
echo

# Dependencies
echo "📦 Dependencies:"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Virtual env active: ✅ $VIRTUAL_ENV"
    pip check 2>&1 | head -5
else
    echo "Virtual env active: ❌ Not active"
fi
echo

# Configuration
echo "⚙️ Configuration:"
if [ -f ".env" ]; then
    echo ".env file: ✅ Exists"
    echo "Variables: $(grep -c "=" .env)"
else
    echo ".env file: ❌ Not found"
fi
echo

# Database
echo "💾 Database:"
if [ -f "data/chatbot.db" ]; then
    echo "SQLite DB: ✅ Exists ($(du -h data/chatbot.db | cut -f1))"
else
    echo "SQLite DB: ❌ Not found"
fi
echo

# Ports
echo "🔌 Port Status:"
for port in 8550 8551; do
    if netstat -ln 2>/dev/null | grep ":$port " > /dev/null; then
        echo "Port $port: ❌ In use"
    else
        echo "Port $port: ✅ Available"
    fi
done
echo

echo "🔧 Recommended actions based on findings above:"
if [ ! -d "venv" ]; then
    echo "- Create virtual environment: python -m venv venv"
fi
if [ -z "$VIRTUAL_ENV" ]; then
    echo "- Activate virtual environment: source venv/bin/activate"
fi
if [ ! -f ".env" ]; then
    echo "- Create .env file with API keys"
fi
if [ ! -f "data/chatbot.db" ]; then
    echo "- Initialize database: python -c 'from src.database.session import init_db; init_db()'"
fi
```

### Log Analysis

```bash
# Create log analyzer
cat > analyze_logs.py << 'EOF'
#!/usr/bin/env python3
import re
from collections import Counter
from pathlib import Path

def analyze_logs():
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        print("❌ No log file found at logs/app.log")
        return
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    print(f"📊 Log Analysis ({len(lines)} lines)")
    print("=" * 40)
    
    # Count log levels
    levels = Counter()
    errors = []
    
    for line in lines:
        if " ERROR " in line:
            levels["ERROR"] += 1
            errors.append(line.strip())
        elif " WARNING " in line:
            levels["WARNING"] += 1
        elif " INFO " in line:
            levels["INFO"] += 1
        elif " DEBUG " in line:
            levels["DEBUG"] += 1
    
    print("Log Level Summary:")
    for level, count in levels.items():
        print(f"  {level}: {count}")
    
    if errors:
        print(f"\n🚨 Recent Errors ({len(errors)}):")
        for error in errors[-5:]:  # Last 5 errors
            print(f"  {error[:100]}...")
    
    print("\n💡 Check full log: tail -f logs/app.log")

if __name__ == "__main__":
    analyze_logs()
EOF

python analyze_logs.py
```

## 🆘 Emergency Recovery

### Complete Reset (Nuclear Option)

```bash
#!/bin/bash
echo "🚨 Emergency Reset - This will delete all local data!"
read -p "Are you sure? (type 'yes'): " confirm

if [ "$confirm" = "yes" ]; then
    echo "🔄 Resetting system..."
    
    # Stop all processes
    pkill -f "python app.py" 2>/dev/null
    
    # Remove virtual environment
    rm -rf venv/
    
    # Remove data (backup first!)
    mv data data_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null
    
    # Recreate environment
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Recreate directories
    mkdir -p data/chroma data/uploads logs
    
    echo "✅ Reset complete. Please:"
    echo "1. Update .env with your API keys"
    echo "2. Run: python app.py"
    echo "3. Your old data is in data_backup_* directory"
else
    echo "❌ Reset cancelled"
fi
```

## 📞 Getting Help

### Information to Collect Before Reporting Issues

```bash
# Run this command and share output:
echo "🐞 Bug Report Information"
echo "========================"
echo "Date: $(date)"
echo "OS: $(uname -a)"
echo "Python: $(python --version 2>&1)"
echo "Working Directory: $(pwd)"
echo "Virtual Env: $VIRTUAL_ENV"
echo "Git Branch: $(git branch --show-current 2>/dev/null || echo 'Not a git repo')"
echo "Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'Not available')"
echo
echo "Installed Packages (key ones):"
pip list | grep -E "(fastapi|flet|openai|anthropic|sqlalchemy|chromadb)" 2>/dev/null
echo
echo "Recent Errors:"
grep "ERROR" logs/app.log | tail -3 2>/dev/null || echo "No recent errors"
```

### Support Channels
1. Check existing documentation in `docs/` folder
2. Review GitHub issues (if available)
3. Search Stack Overflow for similar issues
4. Contact system administrator
5. Create detailed bug report with above information

---

**Troubleshooting Guide Created By**: SYSTEM ANALYST Agent (Hive Mind Collective)  
**Last Updated**: 2025-08-24  
**Version**: 1.0  

For more help, see:
- `docs/STARTUP_GUIDE.md` - Complete setup instructions
- `docs/SYSTEM_ANALYSIS_REPORT.md` - System health analysis
- `logs/app.log` - Application logs

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>