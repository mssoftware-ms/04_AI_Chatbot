@echo off
REM Run the WSL menu script from Windows
title WhatsApp AI Chatbot - WSL Menu
color 0A

cls
echo ============================================================
echo       WhatsApp AI Chatbot - WSL Control Center
echo ============================================================
echo.
echo Launching WSL menu system...
echo.

REM Make script executable and run with menu
wsl bash -c "cd /mnt/d/03_GIT/02_Python/04_AI_Chatbot && chmod +x start_wsl.sh && ./start_wsl.sh"

pause