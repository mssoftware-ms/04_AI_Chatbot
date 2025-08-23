@echo off
setlocal enabledelayedexpansion
color 0A
title WhatsApp AI Chatbot - Control Center

:MENU
cls
echo ============================================================
echo           WhatsApp AI Chatbot - Control Center
echo ============================================================
echo.
echo   [1] Setup Environment (Erste Installation)
echo   [2] Start Full Application (Backend + UI)
echo   [3] Start Backend Only
echo   [4] Start UI Only
echo   [5] Start Demo Mode
echo   [6] Run Tests
echo   [7] Check Dependencies Status
echo   [8] Update Dependencies
echo   [9] Database Management
echo   [0] Advanced Options
echo.
echo   [X] Exit
echo.
echo ============================================================
set /p choice="Select an option: "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto START_FULL
if "%choice%"=="3" goto START_BACKEND
if "%choice%"=="4" goto START_UI
if "%choice%"=="5" goto START_DEMO
if "%choice%"=="6" goto RUN_TESTS
if "%choice%"=="7" goto CHECK_DEPS
if "%choice%"=="8" goto UPDATE_DEPS
if "%choice%"=="9" goto DB_MENU
if "%choice%"=="0" goto ADVANCED_MENU
if /i "%choice%"=="X" goto EXIT
goto INVALID

:SETUP
cls
echo ============================================================
echo              SETUP - First Time Installation
echo ============================================================
echo.
echo This will:
echo   1. Create virtual environment
echo   2. Install all dependencies
echo   3. Setup database
echo   4. Create .env file
echo.
pause

echo.
echo [1/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists!
)

echo.
echo [2/4] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo [3/4] Installing dependencies...
venv\Scripts\pip.exe install -r requirements.txt

echo.
echo [4/4] Setting up environment file...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo.
        echo ============================================================
        echo IMPORTANT: Please edit .env file and add your API keys!
        echo File location: %cd%\.env
        echo ============================================================
    )
) else (
    echo .env file already exists!
)

echo.
echo ============================================================
echo Setup completed successfully!
echo ============================================================
pause
goto MENU

:START_FULL
cls
echo ============================================================
echo           Starting Full Application (Backend + UI)
echo ============================================================
echo.
echo Starting services...
echo Press Ctrl+C to stop the application
echo.
venv\Scripts\python.exe app.py
pause
goto MENU

:START_BACKEND
cls
echo ============================================================
echo              Starting Backend API Server Only
echo ============================================================
echo.
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
venv\Scripts\python.exe app.py backend
pause
goto MENU

:START_UI
cls
echo ============================================================
echo               Starting UI Interface Only
echo ============================================================
echo.
echo UI will open in your browser at: http://localhost:8550
echo.
echo Press Ctrl+C to stop the UI
echo.
venv\Scripts\python.exe app.py ui
pause
goto MENU

:START_DEMO
cls
echo ============================================================
echo                    Demo Mode Menu
echo ============================================================
echo.
echo   [1] Start Demo API (No dependencies required)
echo   [2] Start Demo UI (Minimal dependencies)
echo   [3] Check Demo Status
echo   [B] Back to Main Menu
echo.
set /p demo_choice="Select demo option: "

if "%demo_choice%"=="1" (
    cls
    echo Starting Demo API...
    venv\Scripts\python.exe start_demo.py api
    pause
)
if "%demo_choice%"=="2" (
    cls
    echo Starting Demo UI...
    venv\Scripts\python.exe start_demo.py ui
    pause
)
if "%demo_choice%"=="3" (
    cls
    venv\Scripts\python.exe start_demo.py
    pause
)
if /i "%demo_choice%"=="B" goto MENU
goto START_DEMO

:RUN_TESTS
cls
echo ============================================================
echo                    Running Tests
echo ============================================================
echo.
echo Select test type:
echo   [1] Run all tests
echo   [2] Run unit tests only
echo   [3] Run integration tests only
echo   [4] Run with coverage report
echo   [B] Back to Main Menu
echo.
set /p test_choice="Select test option: "

if "%test_choice%"=="1" (
    cls
    echo Running all tests...
    venv\Scripts\python.exe -m pytest tests/ -v
    pause
)
if "%test_choice%"=="2" (
    cls
    echo Running unit tests...
    venv\Scripts\python.exe -m pytest tests/ -v -m unit
    pause
)
if "%test_choice%"=="3" (
    cls
    echo Running integration tests...
    venv\Scripts\python.exe -m pytest tests/ -v -m integration
    pause
)
if "%test_choice%"=="4" (
    cls
    echo Running tests with coverage...
    venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=html
    echo.
    echo Coverage report generated in htmlcov/index.html
    pause
)
if /i "%test_choice%"=="B" goto MENU
goto RUN_TESTS

:CHECK_DEPS
cls
echo ============================================================
echo              Checking Dependencies Status
echo ============================================================
echo.
echo Checking Python version...
python --version
echo.
echo Checking installed packages...
venv\Scripts\pip.exe list
echo.
echo ============================================================
echo Checking critical dependencies:
echo ============================================================
venv\Scripts\python.exe -c "import fastapi; print('✓ FastAPI:', fastapi.__version__)" 2>nul || echo ✗ FastAPI: Not installed
venv\Scripts\python.exe -c "import uvicorn; print('✓ Uvicorn: Installed')" 2>nul || echo ✗ Uvicorn: Not installed
venv\Scripts\python.exe -c "import flet; print('✓ Flet:', flet.__version__)" 2>nul || echo ✗ Flet: Not installed
venv\Scripts\python.exe -c "import sqlalchemy; print('✓ SQLAlchemy:', sqlalchemy.__version__)" 2>nul || echo ✗ SQLAlchemy: Not installed
venv\Scripts\python.exe -c "import chromadb; print('✓ ChromaDB:', chromadb.__version__)" 2>nul || echo ✗ ChromaDB: Not installed
venv\Scripts\python.exe -c "import openai; print('✓ OpenAI:', openai.__version__)" 2>nul || echo ✗ OpenAI: Not installed
echo.
pause
goto MENU

:UPDATE_DEPS
cls
echo ============================================================
echo               Updating Dependencies
echo ============================================================
echo.
echo This will update all packages to latest versions.
echo Continue? (Y/N)
set /p confirm="Your choice: "
if /i not "%confirm%"=="Y" goto MENU

echo.
echo Updating pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Updating all packages...
venv\Scripts\pip.exe install --upgrade -r requirements.txt

echo.
echo Update completed!
pause
goto MENU

:DB_MENU
cls
echo ============================================================
echo                 Database Management
echo ============================================================
echo.
echo   [1] Initialize Database
echo   [2] Reset Database (WARNING: Deletes all data!)
echo   [3] Backup Database
echo   [4] Restore Database
echo   [5] View Database Info
echo   [B] Back to Main Menu
echo.
set /p db_choice="Select option: "

if "%db_choice%"=="1" (
    cls
    echo Initializing database...
    venv\Scripts\python.exe -c "import asyncio; from src.database.session import DatabaseManager; asyncio.run(DatabaseManager().initialize())"
    echo Database initialized!
    pause
)
if "%db_choice%"=="2" (
    cls
    echo WARNING: This will delete all data!
    echo Are you sure? (Type YES to confirm)
    set /p confirm_reset="Confirm: "
    if "%confirm_reset%"=="YES" (
        if exist "chatbot.db" del chatbot.db
        if exist "data\chatbot.db" del data\chatbot.db
        echo Database reset completed!
    ) else (
        echo Operation cancelled.
    )
    pause
)
if "%db_choice%"=="3" (
    cls
    echo Creating database backup...
    if not exist "backups" mkdir backups
    copy chatbot.db backups\chatbot_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db 2>nul
    copy data\chatbot.db backups\chatbot_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db 2>nul
    echo Backup created in backups folder!
    pause
)
if "%db_choice%"=="4" (
    cls
    echo Available backups:
    dir backups\*.db /B 2>nul || echo No backups found
    echo.
    echo Enter backup filename to restore (or press Enter to cancel):
    set /p backup_file="Filename: "
    if not "%backup_file%"=="" (
        if exist "backups\%backup_file%" (
            copy backups\%backup_file% chatbot.db
            echo Database restored from %backup_file%!
        ) else (
            echo Backup file not found!
        )
    )
    pause
)
if "%db_choice%"=="5" (
    cls
    echo Database Information:
    echo ============================================================
    if exist "chatbot.db" (
        echo Location: %cd%\chatbot.db
        for %%A in (chatbot.db) do echo Size: %%~zA bytes
        echo Modified: %%~tA
    ) else if exist "data\chatbot.db" (
        echo Location: %cd%\data\chatbot.db
        for %%A in (data\chatbot.db) do echo Size: %%~zA bytes
        echo Modified: %%~tA
    ) else (
        echo No database found!
    )
    pause
)
if /i "%db_choice%"=="B" goto MENU
goto DB_MENU

:ADVANCED_MENU
cls
echo ============================================================
echo                   Advanced Options
echo ============================================================
echo.
echo   [1] Open Project in VS Code
echo   [2] View Logs
echo   [3] Clear Cache
echo   [4] Environment Variables Editor
echo   [5] Generate API Documentation
echo   [6] Performance Monitor
echo   [7] Install Development Tools
echo   [8] Create Desktop Shortcut
echo   [B] Back to Main Menu
echo.
set /p adv_choice="Select option: "

if "%adv_choice%"=="1" (
    cls
    echo Opening project in VS Code...
    code .
    goto MENU
)
if "%adv_choice%"=="2" (
    cls
    echo ============================================================
    echo                     Recent Logs
    echo ============================================================
    if exist "logs\app.log" (
        type logs\app.log | more
    ) else (
        echo No logs found!
    )
    pause
)
if "%adv_choice%"=="3" (
    cls
    echo Clearing cache...
    if exist "__pycache__" rmdir /s /q __pycache__
    if exist "src\__pycache__" rmdir /s /q src\__pycache__
    if exist ".pytest_cache" rmdir /s /q .pytest_cache
    echo Cache cleared!
    pause
)
if "%adv_choice%"=="4" (
    cls
    echo Opening .env file in notepad...
    if exist ".env" (
        notepad .env
    ) else (
        echo .env file not found! Creating from template...
        copy .env.example .env
        notepad .env
    )
    goto MENU
)
if "%adv_choice%"=="5" (
    cls
    echo Generating API documentation...
    echo This feature requires the app to be running.
    echo Documentation will be available at: http://localhost:8000/docs
    pause
)
if "%adv_choice%"=="6" (
    cls
    echo ============================================================
    echo                 Performance Monitor
    echo ============================================================
    echo.
    echo System Resources:
    wmic cpu get loadpercentage /value | find "LoadPercentage"
    wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value | find "Memory"
    echo.
    echo Python Process Information:
    tasklist /fi "imagename eq python.exe" 2>nul | find "python.exe" || echo No Python processes running
    echo.
    pause
)
if "%adv_choice%"=="7" (
    cls
    echo Installing development tools...
    venv\Scripts\pip.exe install black ruff mypy pytest-cov
    echo Development tools installed!
    pause
)
if "%adv_choice%"=="8" (
    cls
    echo Creating desktop shortcut...
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
    echo sLinkFile = "%userprofile%\Desktop\WhatsApp AI Chatbot.lnk" >> CreateShortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
    echo oLink.TargetPath = "%cd%\chatbot.bat" >> CreateShortcut.vbs
    echo oLink.WorkingDirectory = "%cd%" >> CreateShortcut.vbs
    echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll, 13" >> CreateShortcut.vbs
    echo oLink.Description = "WhatsApp AI Chatbot Control Center" >> CreateShortcut.vbs
    echo oLink.Save >> CreateShortcut.vbs
    cscript CreateShortcut.vbs
    del CreateShortcut.vbs
    echo Desktop shortcut created!
    pause
)
if /i "%adv_choice%"=="B" goto MENU
goto ADVANCED_MENU

:INVALID
cls
echo ============================================================
echo                    Invalid Option!
echo ============================================================
echo.
echo Please select a valid option from the menu.
echo.
pause
goto MENU

:EXIT
cls
echo ============================================================
echo           Thank you for using WhatsApp AI Chatbot!
echo ============================================================
echo.
echo Goodbye!
echo.
timeout /t 2 /nobreak >nul
exit