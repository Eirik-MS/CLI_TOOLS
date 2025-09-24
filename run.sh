#!/bin/bash

set -e  # Exit on first error

VENV_DIR=".venv"

echo "Checking Python environment..."

# Step 1: Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it and try again."
    exit 1
fi

# Step 2: Check for venv module
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ Python 3 venv module is missing."
    echo "   Try: sudo apt install python3-venv"
    exit 1
fi

# Step 3: Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "❌ Failed to create virtual environment."
        exit 1
    fi
fi

# Step 4: Activate virtual environment
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "❌ Could not find activate script. Something went wrong with venv setup."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Step 5: Install dependencies
echo "📦 Installing required Python packages..."
pip install --upgrade pip
pip install InquirerPy rich

# Step 6: Run the tool
echo "🚀 Launching Ventoy USB setup tool..."
python3 ventoy_setup.py "$@"

# Step 7: Clean exit
deactivate
