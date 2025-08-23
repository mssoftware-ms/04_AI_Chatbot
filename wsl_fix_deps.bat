@echo off
title WhatsApp AI Chatbot - Dependency Fixer
color 0E

cls
echo ============================================================
echo       WhatsApp AI Chatbot - Dependency Fixer (WSL)
echo ============================================================
echo.
echo This will fix missing dependencies and common issues.
echo.
pause

echo.
echo [1/5] Activating virtual environment...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate 2>/dev/null || python3 -m venv venv"

echo.
echo [2/5] Upgrading pip...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && python -m pip install --upgrade pip"

echo.
echo [3/5] Installing missing core dependencies...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install python-json-logger python-dotenv pydantic pydantic-settings"

echo.
echo [4/5] Installing minimal requirements for demo...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install fastapi uvicorn[standard] flet aiofiles"

echo.
echo [5/5] Checking installation...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && python -c 'import fastapi; import uvicorn; import flet; print(\"Core modules OK!\")'"

if errorlevel 1 (
    echo.
    echo Some dependencies still missing. Installing one by one...
    wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install fastapi"
    wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install uvicorn"
    wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install flet"
)

echo.
echo ============================================================
echo                    Fix Complete!
echo ============================================================
echo.
echo Now try running the application:
echo   start.bat
echo   OR
echo   wsl_quick_start.bat
echo.
pause