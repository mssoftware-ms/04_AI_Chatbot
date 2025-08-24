@echo off
REM Debug version that stays open
title Debug WhatsApp AI Chatbot

echo.
echo ===============================================================
echo            Debug WhatsApp AI Chatbot Startup
echo ===============================================================
echo.

echo [DEBUG] Current Directory: %CD%
echo [DEBUG] Checking files...

if not exist "start_windows.py" (
    echo [ERROR] start_windows.py not found!
    pause
    exit /b 1
)

echo [DEBUG] start_windows.py found
echo [DEBUG] Checking virtual environment...

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found
    pause
    exit /b 1
)

echo [DEBUG] Virtual environment found
echo [DEBUG] Activating virtual environment...

call venv\Scripts\activate.bat

echo [DEBUG] Virtual environment activated
echo [DEBUG] Checking Python...

python --version

echo [DEBUG] Checking imports...
python -c "import sys; print('Python path:', sys.executable)"
python -c "import flet; print('Flet version OK')"

if errorlevel 1 (
    echo [ERROR] Import failed
    pause
    exit /b 1
)

echo [DEBUG] Starting application...
python start_windows.py

echo.
echo [DEBUG] Application ended
echo [DEBUG] Error level: %ERRORLEVEL%
pause