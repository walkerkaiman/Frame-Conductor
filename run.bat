@echo off
REM Conductor - Windows Batch Script to Run Main Application
REM This script starts the Frame Conductor application using main.py

echo 🚂 Starting Conductor...
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo ❌ Error: main.py not found in current directory
    echo Please run this script from the Frame-Conductor directory.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo 📦 Checking dependencies...
python -c "import fastapi, uvicorn, sacn" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: Some dependencies may not be installed
    echo Run 'pip install -r requirements.txt' to install dependencies
    echo.
)

REM Start the application
echo 🎬 Launching Conductor...
echo ================================
python main.py

REM Check exit status
if errorlevel 1 (
    echo.
    echo ❌ Conductor encountered an error
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Conductor stopped successfully
)

pause 