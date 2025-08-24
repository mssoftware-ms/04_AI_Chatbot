@echo off
REM Kill existing processes using ports 8000 and 8550
title Killing Existing Processes

echo.
echo ===============================================================
echo            Killing Existing Backend Processes
echo ===============================================================
echo.

echo [INFO] Checking for processes on port 8000...
netstat -ano | findstr :8000
if not errorlevel 1 (
    echo [INFO] Found processes on port 8000, attempting to kill...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000') do (
        echo Killing PID: %%i
        taskkill /PID %%i /F 2>nul
    )
) else (
    echo [INFO] No processes found on port 8000
)

echo.
echo [INFO] Checking for processes on port 8550...
netstat -ano | findstr :8550
if not errorlevel 1 (
    echo [INFO] Found processes on port 8550, attempting to kill...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8550') do (
        echo Killing PID: %%i
        taskkill /PID %%i /F 2>nul
    )
) else (
    echo [INFO] No processes found on port 8550
)

echo.
echo [INFO] Killing any Python processes...
taskkill /IM python.exe /F 2>nul
taskkill /IM pythonw.exe /F 2>nul

echo.
echo [INFO] Killing any Flet server processes...
taskkill /IM fletd.exe /F 2>nul

echo.
echo [SUCCESS] Process cleanup completed!
echo [INFO] Ports should now be free
echo.

echo [INFO] Verifying ports are free...
netstat -ano | findstr :8000
if errorlevel 1 (
    echo [OK] Port 8000 is free
) else (
    echo [WARNING] Port 8000 still in use
)

netstat -ano | findstr :8550
if errorlevel 1 (
    echo [OK] Port 8550 is free
) else (
    echo [WARNING] Port 8550 still in use
)

echo.
echo [INFO] Ready to start application!
pause