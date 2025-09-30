#!/bin/bash
# Startup script for WeChat Article Style Converter

# Check for auto-restart flag
AUTO_RESTART=false
for arg in "$@"; do
    if [ "$arg" = "--auto-restart" ] || [ "$arg" = "-r" ]; then
        AUTO_RESTART=true
        break
    fi
done

echo "Starting WeChat Article Style Converter..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if project.toml exists
if [ -f "project.toml" ]; then
    echo "Installing dependencies from project.toml..."
    uv pip install -e .
elif [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    uv pip install -r requirements.txt
fi

# Start the server
echo "Starting server on http://localhost:5003"
echo "Frontend available at http://localhost:5003/static/index.html"

if [ "$AUTO_RESTART" = true ]; then
    echo "Auto-restart enabled"
    AUTO_RESTART=1 python main.py
else
    python main.py
fi