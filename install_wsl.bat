@echo off
REM Install dependencies using WSL
title WhatsApp AI Chatbot - WSL Installer
color 0B

cls
echo ============================================================
echo      WhatsApp AI Chatbot - WSL Dependency Installer
echo ============================================================
echo.
echo This will install all required dependencies in WSL.
echo.
pause

echo.
echo [1/4] Checking WSL...
wsl --status >nul 2>&1
if errorlevel 1 (
    echo ERROR: WSL is not installed!
    echo Please install WSL first: wsl --install
    pause
    exit /b 1
)
echo WSL is available!

echo.
echo [2/4] Creating/checking virtual environment...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && if [ ! -d venv ]; then python3 -m venv venv; echo 'Virtual environment created!'; else echo 'Virtual environment exists!'; fi"

echo.
echo [3/4] Installing dependencies...
echo This may take several minutes...
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

if errorlevel 1 (
    echo.
    echo WARNING: Some dependencies may have failed to install.
    echo Trying core dependencies only...
    wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate && pip install fastapi uvicorn flet pydantic pydantic-settings python-dotenv aiofiles"
)

echo.
echo [4/4] Setting up configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Configuration file created!
        echo.
        echo ============================================================
        echo IMPORTANT: Add your OpenAI API key to .env file!
        echo ============================================================
        notepad .env
    )
)

echo.
echo ============================================================
echo            Installation Complete!
echo ============================================================
echo.
echo You can now run the application using:
echo   - wsl_quick_start.bat (Direct start)
echo   - wsl_menu.bat (Interactive menu)
echo   - start.bat (Auto-detect and run)
echo.
echo ============================================================
pause