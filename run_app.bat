@echo off
title WhatsApp AI Chatbot - Smart Launcher
color 0A

echo ============================================================
echo       WhatsApp AI Chatbot - Smart Environment Detector
echo ============================================================
echo.

REM Detect environment and run appropriate command
if exist "venv\Scripts\python.exe" (
    echo [✓] Windows Python environment detected!
    echo.
    echo Starting application with Windows Python...
    venv\Scripts\python.exe app.py
) else if exist "venv/bin/python" (
    echo [!] WSL/Linux environment detected!
    echo.
    echo ============================================================
    echo The virtual environment was created in WSL/Linux.
    echo.
    echo To run the application, use one of these methods:
    echo.
    echo Method 1: From WSL/Linux terminal:
    echo   $ ./start_wsl.sh
    echo   OR
    echo   $ source venv/bin/activate
    echo   $ python app.py
    echo.
    echo Method 2: From Windows with WSL:
    echo   > wsl ./start_wsl.sh
    echo   OR
    echo   > wsl bash -c "source venv/bin/activate && python app.py"
    echo.
    echo Method 3: Reinstall with Windows Python:
    echo   1. Delete the 'venv' folder
    echo   2. Install Python for Windows
    echo   3. Run install_fixed.bat
    echo ============================================================
    echo.
    echo Attempting to run with WSL...
    wsl bash -c "source venv/bin/activate && python app.py"
    if errorlevel 1 (
        echo.
        echo Failed to run with WSL. Please use one of the methods above.
    )
) else (
    echo [!] No virtual environment found!
    echo.
    echo Please run install_fixed.bat first to set up the environment.
    echo.
    echo Attempting to run with system Python...
    python app.py
    if errorlevel 1 (
        echo.
        echo Failed to run. Please install the application first.
    )
)

echo.
pause