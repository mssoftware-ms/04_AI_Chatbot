@echo off
REM WhatsApp AI Chatbot - Automatic WSL Launcher (No Menu)
title WhatsApp AI Chatbot
color 0A

cls
echo Starting WhatsApp AI Chatbot...

REM Directly run the application in WSL without menu
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate 2>/dev/null ; python app.py 2>&1"

if errorlevel 1 (
    echo.
    echo Application stopped. Press any key to exit...
    pause >nul
)