@echo off
REM Install missing authentication packages for Windows
title Installing Missing Packages

echo [INFO] Installing missing authentication packages...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install JWT and authentication packages
echo Installing PyJWT...
pip install PyJWT==2.10.1

echo Installing python-jose with cryptography...
pip install "python-jose[cryptography]==3.3.0"

echo Installing passlib with bcrypt...
pip install "passlib[bcrypt]==1.7.4"

echo Installing additional packages that might be missing...
pip install python-multipart==0.0.6
pip install sqlalchemy==2.0.23
pip install alembic==1.12.1

echo [OK] All packages installed!
echo [INFO] Testing imports...

python -c "import jwt; print('[OK] PyJWT')"
python -c "import jose; print('[OK] python-jose')"
python -c "import passlib; print('[OK] passlib')"
python -c "import slowapi; print('[OK] slowapi')"

echo.
echo [INFO] Starting application...
python start_windows.py

pause