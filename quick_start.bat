@echo off
title WhatsApp AI Chatbot - Quick Start
color 0A

echo ============================================================
echo         WhatsApp AI Chatbot - Quick Start
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [!] Virtual environment not found. Running setup...
    echo.
    call chatbot.bat
    exit
)

REM Check if .env exists
if not exist ".env" (
    echo [!] Configuration file not found. Creating .env...
    copy .env.example .env >nul 2>&1
    echo.
    echo ============================================================
    echo IMPORTANT: Please edit .env and add your OpenAI API key!
    echo ============================================================
    echo.
    pause
    notepad .env
)

echo Starting WhatsApp AI Chatbot...
echo.
echo [*] Backend API: http://localhost:8000
echo [*] UI Interface: http://localhost:8550
echo [*] API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the application
echo ============================================================
echo.

venv\Scripts\python.exe app.py