@echo off
REM Quick start for WSL - starts app directly without menu
title WhatsApp AI Chatbot - Quick Start
color 0A

echo ============================================================
echo         WhatsApp AI Chatbot - Quick Start (WSL)
echo ============================================================
echo.
echo Starting application...
echo.
echo Backend API: http://localhost:8000
echo UI Interface: http://localhost:8550
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

REM Run Python app directly in WSL
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && source venv/bin/activate 2>/dev/null && python app.py"

pause