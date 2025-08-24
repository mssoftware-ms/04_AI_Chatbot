@echo off
echo 🚀 Emergency Venv Launcher for 04_AI_Chatbot
echo ==========================================

cd /d "/mnt/d/03_GIT/02_Python/04_AI_Chatbot"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found in PATH
    echo Please install Python 3.12+ and add it to PATH
    pause
    exit /b 1
)

REM Run the universal launcher
python run_project.py %*

if errorlevel 1 (
    echo.
    echo ✗ Project failed to start
    pause
    exit /b 1
)
