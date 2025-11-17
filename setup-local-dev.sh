#!/bin/bash
set -e

echo "================================================"
echo "Vagrantfile Generator - Local Development Setup"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is installed
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    print_error "Python 3.11+ is required. You have Python $PYTHON_VERSION"
    exit 1
fi

print_info "Python $PYTHON_VERSION detected ✓"

# Check if Node.js is installed
print_info "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ and npm."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_warning "Node.js 18+ is recommended. You have Node.js $(node -v)"
else
    print_info "Node.js $(node -v) detected ✓"
fi

# Setup Backend
echo ""
print_info "Setting up Backend..."

cd "$BACKEND_DIR"

# Create Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv .venv
else
    print_info "Python virtual environment already exists ✓"
fi

# Activate virtual environment and install dependencies
print_info "Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Create data directories if they don't exist
print_info "Creating data directories..."
mkdir -p data/auth
mkdir -p data/shared/boxes
mkdir -p data/shared/plugins
mkdir -p data/shared/projects
mkdir -p data/shared/provisioners
mkdir -p data/shared/triggers
mkdir -p data/users

# Initialize auth data files if they don't exist
if [ ! -f "data/auth/otp-requests.json" ]; then
    echo "[]" > data/auth/otp-requests.json
    print_info "Created data/auth/otp-requests.json"
fi

if [ ! -f "data/auth/rate-limits.json" ]; then
    echo "[]" > data/auth/rate-limits.json
    print_info "Created data/auth/rate-limits.json"
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    print_warning ".env.local not found. Please create it based on .env.example"
else
    print_info "Backend .env.local exists ✓"
fi

deactivate

# Setup Frontend
echo ""
print_info "Setting up Frontend..."

cd "$FRONTEND_DIR"

# Install Node.js dependencies
print_info "Installing Node.js dependencies..."
npm install

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    print_warning ".env.local not found. Please create it if needed"
else
    print_info "Frontend .env.local exists ✓"
fi

# Build Tailwind CSS
print_info "Building Tailwind CSS..."
npm run tailwind

# Return to root directory
cd "$SCRIPT_DIR"

echo ""
print_info "================================================"
print_info "Setup complete! 🎉"
print_info "================================================"
echo ""
print_info "To start development:"
echo ""
echo "  Option 1: Use VS Code tasks"
echo "    - Open the project in VS Code"
echo "    - Press Ctrl+Shift+P (Cmd+Shift+P on Mac)"
echo "    - Type 'Tasks: Run Task'"
echo "    - Select 'Start Both Dev Servers'"
echo ""
echo "  Option 2: Use debugger (recommended)"
echo "    - Open the project in VS Code"
echo "    - Press F5 or go to Run and Debug"
echo "    - Select 'Full Stack (Backend + Frontend)'"
echo ""
echo "  Option 3: Manual start"
echo "    - Backend: cd backend && source .venv/bin/activate && uvicorn src.main:app --reload"
echo "    - Frontend: cd frontend && npm run dev"
echo ""
echo "  URLs:"
echo "    - Frontend: http://localhost:5173"
echo "    - Backend:  http://localhost:8000"
echo "    - API Docs: http://localhost:8000/docs"
echo ""
print_info "For production-like testing, use: make prod-up"
print_info "For user distribution setup, use: podman-compose up"
echo ""
