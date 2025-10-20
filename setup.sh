#!/bin/bash

# SFTP Client Setup Script
# This script sets up the Python virtual environment and installs dependencies

echo "Setting up SFTP Client..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the SFTP Client:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""

deactivate