#!/bin/bash

# SFTP Client Launcher Script
# This script activates the virtual environment and runs the application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Path to the virtual environment
VENV_PATH="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Please run setup.sh first to create the virtual environment"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Check if requirements are installed
if ! python -c "import paramiko" 2>/dev/null; then
    echo "Dependencies not installed. Installing requirements..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Run the application
echo "Starting SFTP Client..."
cd "$SCRIPT_DIR"
python main.py

# Deactivate virtual environment
deactivate