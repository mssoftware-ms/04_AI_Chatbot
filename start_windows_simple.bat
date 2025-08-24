@echo off
REM Simple Windows launcher for debugging
title WhatsApp AI Chatbot - Simple Debug Version

echo.
echo ═══════════════════════════════════════════════════════════════
echo             🖥️  WhatsApp AI Chatbot - Simple Debug
echo ═══════════════════════════════════════════════════════════════
echo.

REM Show current directory
echo 📂 Current Directory: %CD%
echo.

REM Check Python
echo 🐍 Checking Python...
python --version
if errorlevel 1 (
    echo ❌ Python not found in PATH
    echo 💡 Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

REM Create virtual environment if needed
if not exist "venv\Scripts\python.exe" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Install minimal requirements only
echo 📦 Installing minimal requirements...
echo Installing: pip setuptools wheel
pip install --upgrade pip setuptools wheel

echo Installing: pydantic pydantic-settings fastapi
pip install pydantic==2.5.0 pydantic-settings==2.1.0 fastapi==0.109.0

echo Installing: uvicorn flet
pip install "uvicorn[standard]==0.27.0" flet==0.19.0

echo Installing: basic dependencies
pip install python-dotenv requests

echo.
echo ✅ Basic installation complete!
echo 📍 Testing imports...

python -c "import pydantic; print('✅ pydantic OK')"
python -c "import pydantic_settings; print('✅ pydantic-settings OK')"
python -c "import fastapi; print('✅ fastapi OK')"
python -c "import flet; print('✅ flet OK')"
python -c "import uvicorn; print('✅ uvicorn OK')"

echo.
echo 🚀 Starting application...
echo 💡 If this works, we can install more packages later
echo.

python start_windows.py

echo.
echo 👋 Application stopped
pause