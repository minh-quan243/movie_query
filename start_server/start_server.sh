#!/bin/bash

# MovieVerse - macOS/Linux Server Startup Script
# This script sets up the environment and starts the web application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory (parent of start_server/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   MovieVerse Server Startup Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Step 1: Check Python installation
echo -e "${YELLOW}[1/7]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Step 2: Set up virtual environment
echo -e "${YELLOW}[2/7]${NC} Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Step 3: Install Python dependencies
echo -e "${YELLOW}[3/7]${NC} Checking Python dependencies..."
if [ ! -f ".venv/deps_installed" ]; then
    echo "Installing Python dependencies from requirements.txt..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    touch .venv/deps_installed
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${GREEN}✓${NC} Python dependencies already installed (skipping)"
fi

# Step 4: Download spaCy model
echo -e "${YELLOW}[4/7]${NC} Checking spaCy language model..."
if ! python3 -c "import en_core_web_sm" 2>/dev/null; then
    echo "Downloading spaCy English model (en_core_web_sm)..."
    python3 -m spacy download en_core_web_sm
    echo -e "${GREEN}✓${NC} spaCy model downloaded"
else
    echo -e "${GREEN}✓${NC} spaCy model already installed"
fi

# Step 5: Check Node.js installation
echo -e "${YELLOW}[5/7]${NC} Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    echo "Download from: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"

# Step 6: Install frontend dependencies and build
echo -e "${YELLOW}[6/7]${NC} Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo -e "${GREEN}✓${NC} Node.js dependencies installed"
else
    echo -e "${GREEN}✓${NC} Node.js dependencies already installed (skipping)"
fi

# Check if build is needed
if [ ! -d "dist" ] || [ "$1" == "--rebuild" ]; then
    echo "Building frontend application..."
    npm run build
    echo -e "${GREEN}✓${NC} Frontend built successfully"
else
    echo -e "${GREEN}✓${NC} Frontend already built (use --rebuild to force rebuild)"
fi

cd ..

# Step 7: Start Flask server
echo -e "${YELLOW}[7/7]${NC} Starting Flask backend server..."
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Starting server at ${GREEN}http://127.0.0.1:8000${NC}"
echo -e "Press ${YELLOW}CTRL+C${NC} to stop the server"
echo ""

# Start the Flask application
python3 app.py
