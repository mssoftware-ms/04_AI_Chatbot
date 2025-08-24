@echo off
setlocal enabledelayedexpansion
title WhatsApp AI Chatbot - Launcher Menu
color 0A

:MAIN_MENU
cls
echo.
echo ===============================================================
echo          🚀 WhatsApp AI Chatbot - Launcher Menu
echo ===============================================================
echo.
echo Current Directory: %CD%
echo Time: %DATE% %TIME:~0,5%
echo.
echo 📋 Available Options:
echo ---------------------------------------------------------------
echo   1. 🌐 Web Interface (Flet) - Browser-based
echo   2. 🖥️  Native GUI (Tkinter) - Desktop App  
echo   3. 🔀 Both Interfaces - Web + Native parallel
echo   4. 🛠️  Backend Only - API Server only
echo   5. 📦 Install/Update Requirements
echo   6. 🔍 Check System Status
echo   7. 🧹 Clean Processes (Kill ports 8000/8550)
echo   8. ❌ Exit
echo ---------------------------------------------------------------
echo.

set /p choice="🎯 Select option (1-8): "

if "%choice%"=="1" goto WEB_INTERFACE
if "%choice%"=="2" goto NATIVE_GUI
if "%choice%"=="3" goto BOTH_INTERFACES
if "%choice%"=="4" goto BACKEND_ONLY
if "%choice%"=="5" goto INSTALL_REQUIREMENTS
if "%choice%"=="6" goto CHECK_STATUS
if "%choice%"=="7" goto CLEAN_PROCESSES
if "%choice%"=="8" goto EXIT
goto INVALID_CHOICE

:WEB_INTERFACE
cls
echo.
echo ===============================================================
echo                     🌐 Starting Web Interface
echo ===============================================================
echo.
call :CHECK_AND_ACTIVATE_VENV
if errorlevel 1 goto MAIN_MENU

echo [INFO] Starting Web Interface (Flet)...
echo [INFO] Backend will start on: http://localhost:8000
echo [INFO] Web UI will start on: http://localhost:8550
echo [INFO] Browser will open automatically
echo.
echo 💡 Press Ctrl+C to stop the application
echo.
python start_windows.py
goto RETURN_TO_MENU

:NATIVE_GUI
cls
echo.
echo ===============================================================
echo                   🖥️  Starting Native GUI
echo ===============================================================
echo.
call :CHECK_AND_ACTIVATE_VENV
if errorlevel 1 goto MAIN_MENU

echo [INFO] Starting Native Desktop Application...
echo [INFO] Backend will start on: http://localhost:8000
echo [INFO] Desktop window will open automatically
echo.
echo 💡 Close the desktop window to stop the application
echo.
python -c "from src.ui.native_chat_app import main; main()"
goto RETURN_TO_MENU

:BOTH_INTERFACES
cls
echo.
echo ===============================================================
echo                  🔀 Starting Both Interfaces
echo ===============================================================
echo.
call :CHECK_AND_ACTIVATE_VENV
if errorlevel 1 goto MAIN_MENU

echo [INFO] Starting both Web and Native interfaces...
echo [INFO] Backend: http://localhost:8000
echo [INFO] Web UI: http://localhost:8550
echo [INFO] Native GUI: Desktop window
echo.
echo 💡 Close the desktop window to stop both applications
echo.
python start_with_options.py
echo y | python start_with_options.py
goto RETURN_TO_MENU

:BACKEND_ONLY
cls
echo.
echo ===============================================================
echo                   🛠️  Starting Backend Only
echo ===============================================================
echo.
call :CHECK_AND_ACTIVATE_VENV
if errorlevel 1 goto MAIN_MENU

echo [INFO] Starting Backend API Server only...
echo [INFO] Backend API: http://localhost:8000
echo [INFO] API Documentation: http://localhost:8000/docs
echo.
echo 💡 Press Ctrl+C to stop the backend server
echo.
python -c "import uvicorn; from src.main import create_app; uvicorn.run(create_app(), host='0.0.0.0', port=8000)"
goto RETURN_TO_MENU

:INSTALL_REQUIREMENTS
cls
echo.
echo ===============================================================
echo                📦 Installing/Updating Requirements
echo ===============================================================
echo.
call :CHECK_AND_ACTIVATE_VENV
if errorlevel 1 goto MAIN_MENU

echo [INFO] Installing/updating Python packages...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo [SUCCESS] Requirements installation completed!
pause
goto MAIN_MENU

:CHECK_STATUS
cls
echo.
echo ===============================================================
echo                   🔍 System Status Check
echo ===============================================================
echo.

echo [INFO] Python Version:
python --version
echo.

echo [INFO] Virtual Environment Status:
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found
) else (
    echo ❌ Virtual environment NOT found
)
echo.

echo [INFO] Port Status:
echo Checking port 8000 (Backend):
netstat -an | findstr :8000 && echo ✅ Port 8000 is in use || echo ⭕ Port 8000 is free

echo Checking port 8550 (UI Server):
netstat -an | findstr :8550 && echo ✅ Port 8550 is in use || echo ⭕ Port 8550 is free
echo.

echo [INFO] Key Package Status:
call :CHECK_AND_ACTIVATE_VENV >nul 2>&1
python -c "
packages = ['flet', 'fastapi', 'uvicorn', 'requests', 'tkinter']
for pkg in packages:
    try:
        if pkg == 'tkinter':
            import tkinter
            print(f'✅ {pkg}: Available')
        else:
            exec(f'import {pkg}; print(f\"✅ {pkg}: {{pkg.__version__ if hasattr(pkg, \"__version__\") else \"OK\"}}\")')
    except ImportError:
        print(f'❌ {pkg}: NOT FOUND')
"
echo.
pause
goto MAIN_MENU

:CLEAN_PROCESSES
cls
echo.
echo ===============================================================
echo                🧹 Cleaning Background Processes
echo ===============================================================
echo.

echo [INFO] Stopping processes on ports 8000 and 8550...
echo.

echo [INFO] Checking for processes on port 8000...
netstat -ano | findstr :8000
if not errorlevel 1 (
    echo [INFO] Found processes on port 8000, terminating...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000') do (
        echo Killing PID: %%i
        taskkill /PID %%i /F >nul 2>&1
    )
) else (
    echo [INFO] No processes found on port 8000
)

echo.
echo [INFO] Checking for processes on port 8550...
netstat -ano | findstr :8550
if not errorlevel 1 (
    echo [INFO] Found processes on port 8550, terminating...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8550') do (
        echo Killing PID: %%i
        taskkill /PID %%i /F >nul 2>&1
    )
) else (
    echo [INFO] No processes found on port 8550
)

echo.
echo [INFO] Cleaning up Python and Flet processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM pythonw.exe /F >nul 2>&1
taskkill /IM fletd.exe /F >nul 2>&1

echo.
echo [SUCCESS] Process cleanup completed!
echo [INFO] Ports should now be free for new applications.
echo.
pause
goto MAIN_MENU

:CHECK_AND_ACTIVATE_VENV
echo [INFO] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please create a virtual environment first:
    echo        python -m venv venv
    echo        venv\Scripts\activate
    echo        pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not accessible in virtual environment!
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment activated successfully!
echo.
exit /b 0

:RETURN_TO_MENU
echo.
echo ===============================================================
echo.
set /p return="🔄 Return to main menu? (Y/N): "
if /i "%return%"=="Y" goto MAIN_MENU
if /i "%return%"=="N" goto EXIT
goto MAIN_MENU

:INVALID_CHOICE
echo.
echo ❌ Invalid choice! Please select a number between 1-8.
timeout /t 2 >nul
goto MAIN_MENU

:EXIT
cls
echo.
echo ===============================================================
echo                          👋 Goodbye!
echo ===============================================================
echo.
echo Thank you for using WhatsApp AI Chatbot!
echo.
echo Deactivating virtual environment...
if defined VIRTUAL_ENV (
    call venv\Scripts\deactivate.bat >nul 2>&1
)

echo.
echo Application closed. Have a great day! 😊
echo.
timeout /t 3 >nul
exit /b 0