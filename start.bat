@echo off
title WhatsApp AI Chatbot - WSL Auto-Launcher
color 0A

cls
echo ============================================================
echo       WhatsApp AI Chatbot - WSL Auto-Launcher
echo ============================================================
echo.
echo Detecting environment and starting application...
echo.

REM Check if WSL is available
wsl --status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] WSL is not installed or not available!
    echo.
    echo Please install WSL first:
    echo 1. Open PowerShell as Administrator
    echo 2. Run: wsl --install
    echo 3. Restart your computer
    echo.
    pause
    exit /b 1
)

REM Check if the shell script exists
if not exist "start_wsl.sh" (
    echo [ERROR] start_wsl.sh not found!
    echo Creating it now...
    
    REM Create a basic start script if it doesn't exist
    echo #!/bin/bash > start_wsl.sh
    echo cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot >> start_wsl.sh
    echo source venv/bin/activate 2^>/dev/null >> start_wsl.sh
    echo python app.py >> start_wsl.sh
)

REM Make the script executable and run it
echo [*] Starting WhatsApp AI Chatbot in WSL...
echo.
echo ============================================================
echo Backend API: http://localhost:8000
echo UI Interface: http://localhost:8550
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the application
echo ============================================================
echo.

REM Run the WSL script with proper path conversion
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && chmod +x start_wsl.sh && ./start_wsl.sh"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo Application stopped or encountered an error.
    echo.
    echo If you see dependency errors, run:
    echo   wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install -r requirements.txt"
    echo ============================================================
)

pause