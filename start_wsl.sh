#!/bin/bash
# WhatsApp AI Chatbot - WSL/Linux Startup Script

# Change to script directory
cd "$(dirname "$0")"

echo "============================================================"
echo "         WhatsApp AI Chatbot - WSL/Linux Launcher"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment!${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Configuration file not found. Creating .env...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env and add your OpenAI API key!${NC}"
        echo "Press Enter to continue..."
        read
    fi
fi

# Function to check dependencies
check_deps() {
    echo "Checking dependencies..."
    python -c "import fastapi; print('✓ FastAPI installed')" 2>/dev/null || echo "✗ FastAPI not installed"
    python -c "import uvicorn; print('✓ Uvicorn installed')" 2>/dev/null || echo "✗ Uvicorn not installed"
    python -c "import flet; print('✓ Flet installed')" 2>/dev/null || echo "✗ Flet not installed"
    python -c "import sqlalchemy; print('✓ SQLAlchemy installed')" 2>/dev/null || echo "✗ SQLAlchemy not installed"
    python -c "import chromadb; print('✓ ChromaDB installed')" 2>/dev/null || echo "✗ ChromaDB not installed"
    python -c "import openai; print('✓ OpenAI installed')" 2>/dev/null || echo "✗ OpenAI not installed"
}

# Menu function
show_menu() {
    echo ""
    echo "============================================================"
    echo "                    Main Menu"
    echo "============================================================"
    echo "  1) Install/Update Dependencies"
    echo "  2) Start Full Application (Backend + UI)"
    echo "  3) Start Backend Only"
    echo "  4) Start UI Only"
    echo "  5) Start Demo Mode"
    echo "  6) Run Tests"
    echo "  7) Check Dependencies"
    echo "  8) Exit"
    echo "============================================================"
    echo -n "Select an option: "
}

# Main loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            echo -e "${GREEN}Installing dependencies...${NC}"
            pip install --upgrade pip
            pip install -r requirements.txt
            echo -e "${GREEN}Dependencies installed!${NC}"
            ;;
        2)
            echo -e "${GREEN}Starting Full Application...${NC}"
            python app.py
            ;;
        3)
            echo -e "${GREEN}Starting Backend Only...${NC}"
            python app.py backend
            ;;
        4)
            echo -e "${GREEN}Starting UI Only...${NC}"
            python app.py ui
            ;;
        5)
            echo -e "${GREEN}Starting Demo Mode...${NC}"
            python start_demo.py
            ;;
        6)
            echo -e "${GREEN}Running Tests...${NC}"
            python -m pytest tests/ -v
            ;;
        7)
            check_deps
            ;;
        8)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option!${NC}"
            ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read
done