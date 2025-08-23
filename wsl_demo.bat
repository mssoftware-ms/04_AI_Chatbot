@echo off
title WhatsApp AI Chatbot - Demo Mode
color 0A

cls
echo ============================================================
echo       WhatsApp AI Chatbot - Demo Mode (WSL)
echo ============================================================
echo.
echo Starting demo mode (no AI dependencies required)...
echo.

REM Run demo mode in WSL
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate 2>/dev/null && python start_demo.py api"

pause