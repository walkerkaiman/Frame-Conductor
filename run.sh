#!/bin/bash

# Conductor - Bash Script to Run Main Application
# This script starts the Frame Conductor application using main.py

echo "🚂 Starting Conductor..."
echo "================================"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH"
    echo "Please install Python and try again."
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in current directory"
    echo "Please run this script from the Frame-Conductor directory."
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python -c "import fastapi, uvicorn, sacn" 2>/dev/null; then
    echo "⚠️  Warning: Some dependencies may not be installed"
    echo "Run 'pip install -r requirements.txt' to install dependencies"
    echo ""
fi

# Start the application
echo "🎬 Launching Conductor..."
echo "================================"
python main.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Conductor stopped successfully"
else
    echo ""
    echo "❌ Conductor encountered an error"
    exit 1
fi 