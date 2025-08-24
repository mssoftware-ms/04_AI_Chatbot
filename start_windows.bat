@echo off
REM WhatsApp AI Chatbot - Windows Batch Launcher
REM Optimized for Windows CMD execution

title WhatsApp AI Chatbot - Windows Edition

echo.
echo ═══════════════════════════════════════════════════════════════
echo                🖥️  WhatsApp AI Chatbot - Windows Edition
echo ═══════════════════════════════════════════════════════════════
echo.

REM Check if we're in the right directory
if not exist "start_windows.py" (
    echo ❌ Error: start_windows.py not found!
    echo 💡 Please run this from the project directory
    echo    Expected: D:\03_GIT\02_Python\04_AI_Chatbot
    echo    Current:  %CD%
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ⚠️  Virtual environment not found
    echo 🔧 Creating Windows virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo 💡 Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Fix distutils issue for Python 3.12+
echo 🔧 Installing distutils fix for Python 3.12...
python -m pip install --upgrade pip
pip install setuptools wheel

REM Check if requirements are installed
python -c "import flet, fastapi" 2>nul
if errorlevel 1 (
    echo 📦 Installing requirements (with distutils fix)...
    echo 💡 This may take a few minutes...
    echo.
    
    REM Install distutils-compatible setuptools first
    echo 📦 Installing setuptools and wheel...
    pip install setuptools wheel
    if errorlevel 1 (
        echo ❌ Failed to install setuptools/wheel
        pause
        exit /b 1
    )
    
    REM Install requirements in stages to avoid conflicts
    echo.
    echo 📦 Stage 1: Core dependencies...
    pip install pydantic==2.5.0 pydantic-settings==2.1.0
    if errorlevel 1 (
        echo ❌ Failed to install pydantic packages
        pause
        exit /b 1
    )
    
    pip install fastapi==0.109.0 uvicorn[standard]==0.27.0
    if errorlevel 1 (
        echo ❌ Failed to install FastAPI/Uvicorn
        pause
        exit /b 1
    )
    
    pip install flet==0.19.0
    if errorlevel 1 (
        echo ❌ Failed to install Flet UI framework
        pause
        exit /b 1
    )
    
    echo.
    echo 📦 Stage 2: Essential packages...
    pip install sqlalchemy==2.0.23 alembic==1.12.1
    pip install requests==2.31.0 websockets==12.0 httpx==0.25.2
    pip install python-dotenv==1.0.0 click==8.1.7
    
    echo.
    echo 📦 Stage 3: Windows-optimized packages...
    pip install -r requirements_windows.txt
    
    echo.
    echo 📦 Stage 4: Attempting remaining packages (may fail on some)...
    pip install --no-build-isolation -r requirements.txt
    
    echo.
    echo ✅ Package installation completed!
    echo 💡 Some advanced packages may have failed - this is normal
    echo 🚀 Core functionality should work fine
    pause
)

REM Show status
echo.
echo ✅ Environment ready!
echo 📂 Project: %CD%
echo 🐍 Python: 
python --version
echo.

REM Check command line argument
if "%1"=="" goto FULL_APP
if "%1"=="backend" goto BACKEND_ONLY
if "%1"=="ui" goto UI_ONLY
if "%1"=="test" goto RUN_TESTS
goto SHOW_HELP

:FULL_APP
echo 🚀 Starting full application...
echo 💡 Browser will open automatically
echo.
python start_windows.py
goto END

:BACKEND_ONLY
echo 🔧 Starting backend only...
python start_windows.py backend
goto END

:UI_ONLY
echo 🖥️  Starting UI only...
python start_windows.py ui
goto END

:RUN_TESTS
echo 🧪 Running tests...
python start_windows.py test
goto END

:SHOW_HELP
echo.
echo Usage:
echo   start_windows.bat           Full application
echo   start_windows.bat backend   Backend only
echo   start_windows.bat ui        UI only
echo   start_windows.bat test      Run tests
echo.
pause
goto END

:END
if errorlevel 1 (
    echo.
    echo ❌ Application ended with error
    pause
)
echo.
echo 👋 WhatsApp AI Chatbot stopped
pause