@echo off
REM Enhanced launcher for WhatsApp AI Chatbot with GUI options
title WhatsApp AI Chatbot - Interface Selection

echo.
echo ===============================================================
echo        🚀 WhatsApp AI Chatbot - Enhanced Launcher
echo ===============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please run setup first or activate your virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Start the enhanced launcher
echo [INFO] Starting interface selection...
python start_with_options.py

REM Deactivate virtual environment
echo [INFO] Deactivating virtual environment...
call venv\Scripts\deactivate.bat

echo.
echo [INFO] Application closed.
pause