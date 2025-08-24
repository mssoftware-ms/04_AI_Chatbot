@echo off
REM ASCII-only Windows launcher (no Unicode/Emoji issues)
title WhatsApp AI Chatbot - Windows ASCII

echo.
echo ===============================================================
echo            WhatsApp AI Chatbot - Windows Edition
echo ===============================================================
echo.

REM Show current directory
echo [INFO] Current Directory: %CD%
echo.

REM Check Python
echo [INFO] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo [TIP] Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

REM Create virtual environment if needed
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install minimal requirements only
echo [INFO] Installing minimal requirements...
echo Installing: pip setuptools wheel
pip install --upgrade pip setuptools wheel

echo Installing: pydantic pydantic-settings fastapi
pip install pydantic==2.5.0 pydantic-settings==2.1.0 fastapi==0.109.0

echo Installing: uvicorn flet
pip install "uvicorn[standard]==0.27.0" flet==0.19.0

echo Installing: basic dependencies
pip install python-dotenv requests slowapi

echo.
echo [OK] Basic installation complete!
echo [INFO] Testing imports...

python -c "import pydantic; print('[OK] pydantic')"
python -c "import pydantic_settings; print('[OK] pydantic-settings')"
python -c "import fastapi; print('[OK] fastapi')"
python -c "import flet; print('[OK] flet')"
python -c "import uvicorn; print('[OK] uvicorn')"
python -c "import slowapi; print('[OK] slowapi')"

echo.
echo [INFO] Starting application...
echo [TIP] If this works, we can install more packages later
echo.

python start_windows.py

echo.
echo [INFO] Application stopped
pause