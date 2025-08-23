@echo off
title WhatsApp AI Chatbot - Installer
color 0B

cls
echo ============================================================
echo        WhatsApp AI Chatbot - Installation Wizard
echo ============================================================
echo.
echo This installer will set up everything you need to run
echo the WhatsApp AI Chatbot on your system.
echo.
echo Requirements:
echo   - Python 3.11 or higher
echo   - Internet connection for downloading packages
echo   - OpenAI API key (for full functionality)
echo.
echo ============================================================
pause

REM Check Python installation
echo.
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.11+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

python --version
echo Python found!

REM Detect Python environment type (Windows native or WSL)
echo.
echo [2/7] Detecting environment type...
set "PYTHON_CMD=python"
set "PIP_CMD=pip"
set "VENV_PYTHON="
set "VENV_PIP="

REM Check if we're in WSL or have Windows Python
if exist "venv\Scripts\python.exe" (
    echo Windows virtual environment detected!
    set "VENV_PYTHON=venv\Scripts\python.exe"
    set "VENV_PIP=venv\Scripts\pip.exe"
) else if exist "venv/bin/python" (
    echo WSL/Linux virtual environment detected!
    echo.
    echo ============================================================
    echo WARNING: WSL Environment Detected!
    echo ============================================================
    echo.
    echo You appear to be running this from WSL2/Linux.
    echo For best results, use one of these options:
    echo.
    echo Option 1: Use native Linux commands:
    echo   ./venv/bin/pip install -r requirements.txt
    echo   ./venv/bin/python app.py
    echo.
    echo Option 2: Use Windows Python instead:
    echo   1. Close this window
    echo   2. Install Python for Windows
    echo   3. Run this installer again
    echo.
    echo Attempting to continue with WSL Python...
    echo ============================================================
    pause
    
    REM For WSL, we need to use bash or direct python commands
    set "VENV_PYTHON=bash -c './venv/bin/python'"
    set "VENV_PIP=bash -c './venv/bin/pip'"
    
    REM Alternative: Use python directly if in PATH
    set "VENV_PYTHON=python"
    set "VENV_PIP=pip"
) else (
    echo No virtual environment found. Creating one...
    echo.
    echo [2/7] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    
    REM Check again which type was created
    if exist "venv\Scripts\python.exe" (
        set "VENV_PYTHON=venv\Scripts\python.exe"
        set "VENV_PIP=venv\Scripts\pip.exe"
    ) else if exist "venv/bin/python" (
        echo WSL virtual environment created!
        set "VENV_PYTHON=python"
        set "VENV_PIP=pip"
    ) else (
        echo ERROR: Virtual environment creation failed!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

REM Upgrade pip
echo.
echo [3/7] Upgrading pip...
%VENV_PYTHON% -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Could not upgrade pip, continuing anyway...
)
echo Pip upgrade attempted!

REM Install core dependencies
echo.
echo [4/7] Installing core dependencies...
echo This may take a few minutes...
%VENV_PIP% install fastapi uvicorn[standard] flet pydantic pydantic-settings python-dotenv aiofiles aiosqlite
if errorlevel 1 (
    echo WARNING: Some core dependencies may have failed.
    echo Trying alternative installation method...
    %PYTHON_CMD% -m pip install fastapi uvicorn[standard] flet pydantic pydantic-settings python-dotenv aiofiles aiosqlite
)
echo Core dependencies installation attempted!

REM Install AI dependencies
echo.
echo [5/7] Installing AI dependencies...
echo This may take several minutes...
%VENV_PIP% install sqlalchemy chromadb openai langchain langchain-openai tiktoken slowapi watchfiles PyGithub
if errorlevel 1 (
    echo WARNING: Some AI dependencies failed to install.
    echo You can still run the demo mode.
    echo Trying alternative installation method...
    %PYTHON_CMD% -m pip install sqlalchemy chromadb openai
)
echo AI dependencies installation completed!

REM Create necessary directories
echo.
echo [6/7] Creating project directories...
if not exist "data" mkdir data
if not exist "data\projects" mkdir data\projects
if not exist "data\uploads" mkdir data\uploads
if not exist "brain" mkdir brain
if not exist "brain\chroma" mkdir brain\chroma
if not exist "logs" mkdir logs
if not exist "assets" mkdir assets
if not exist "backups" mkdir backups
echo Directories created!

REM Setup configuration
echo.
echo [7/7] Setting up configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Configuration file created!
        echo.
        echo ============================================================
        echo IMPORTANT: Configuration Required!
        echo ============================================================
        echo.
        echo You need to add your OpenAI API key to the .env file.
        echo.
        echo Would you like to open the configuration file now? (Y/N)
        set /p open_env="Your choice: "
        if /i "%open_env%"=="Y" (
            notepad .env
        )
    )
) else (
    echo Configuration file already exists!
)

REM Installation complete
echo.
echo ============================================================
echo        Installation Completed!
echo ============================================================
echo.
if exist "venv\Scripts\python.exe" (
    echo Environment Type: Windows Native Python
    echo.
    echo You can now run the application using:
    echo   - chatbot.bat (Control Center)
    echo   - quick_start.bat (Quick Launch)
    echo   - venv\Scripts\python.exe app.py (Command Line)
) else (
    echo Environment Type: WSL/Linux Python
    echo.
    echo To run the application in WSL/Linux, use:
    echo   - ./venv/bin/python app.py
    echo   - python app.py (if venv is activated)
    echo.
    echo For Windows batch files to work properly, install Windows Python.
)
echo.
echo Next Steps:
echo   1. Edit .env file and add your OpenAI API key
echo   2. Run the application using one of the methods above
echo   3. Access the UI at http://localhost:8550
echo.
echo ============================================================
echo.
pause