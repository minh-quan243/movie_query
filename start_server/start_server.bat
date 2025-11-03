@echo off
REM MovieVerse - Windows Server Startup Script
REM This script sets up the environment and starts the web application

setlocal EnableDelayedExpansion

REM Get the project root directory (parent of start_server/)
cd /d "%~dp0.."
set PROJECT_ROOT=%CD%

echo ============================================
echo    MovieVerse Server Startup Script
echo ============================================
echo.

REM Step 1: Check Python installation
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://python.org/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Step 2: Set up virtual environment
echo [2/7] Setting up Python virtual environment...
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Step 3: Install Python dependencies
echo [3/7] Checking Python dependencies...
if not exist ".venv\deps_installed" (
    echo Installing Python dependencies from requirements.txt...
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    echo. > .venv\deps_installed
    echo [OK] Python dependencies installed
) else (
    echo [OK] Python dependencies already installed ^(skipping^)
)

REM Step 4: Download spaCy model
echo [4/7] Checking spaCy language model...
python -c "import en_core_web_sm" >nul 2>&1
if %errorlevel% neq 0 (
    echo Downloading spaCy English model ^(en_core_web_sm^)...
    python -m spacy download en_core_web_sm
    echo [OK] spaCy model downloaded
) else (
    echo [OK] spaCy model already installed
)

REM Step 5: Check Node.js installation
echo [5/7] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js 18 or higher from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION% found

REM Step 6: Install frontend dependencies and build
echo [6/7] Setting up frontend...
cd frontend

if not exist "node_modules\" (
    echo Installing Node.js dependencies...
    call npm install
    echo [OK] Node.js dependencies installed
) else (
    echo [OK] Node.js dependencies already installed ^(skipping^)
)

REM Check if build is needed
if not exist "dist\" (
    echo Building frontend application...
    call npm run build
    echo [OK] Frontend built successfully
) else if "%1"=="--rebuild" (
    echo Building frontend application...
    call npm run build
    echo [OK] Frontend built successfully
) else (
    echo [OK] Frontend already built ^(use --rebuild to force rebuild^)
)

cd ..

REM Step 7: Start Flask server
echo [7/7] Starting Flask backend server...
echo.
echo ============================================
echo [OK] Setup complete!
echo ============================================
echo.
echo Starting server at http://127.0.0.1:8000
echo Press CTRL+C to stop the server
echo.

REM Start the Flask application
python app.py

pause
