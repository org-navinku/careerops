#!/bin/bash
# CareerOps startup helper script
# Usage: bash start.sh [option]

set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 CareerOps Startup Helper"
echo "================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "${YELLOW}⚙️  Virtual environment not found. Creating...${NC}"
    python3 -m venv "$VENV_DIR"
    echo "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
echo "${BLUE}📦 Checking dependencies...${NC}"
if ! python3 -c "import flask, flask_cors, docx" 2>/dev/null; then
    echo "${YELLOW}   Installing requirements...${NC}"
    pip install -q -r "$PROJECT_DIR/requirements.txt"
    echo "${GREEN}   ✓ Dependencies installed${NC}"
else
    echo "${GREEN}✓ All dependencies available${NC}"
fi

echo ""

# Show menu
if [ $# -eq 0 ]; then
    echo "${BLUE}What would you like to do?${NC}"
    echo ""
    echo "  1) Start all services (Ollama, backend, web server)"
    echo "  2) Start backend only (python3 backend.py)"
    echo "  3) Start web server only (python3 -m http.server 8000)"
    echo "  4) Check if services are running"
    echo "  5) Open in browser"
    echo "  6) View documentation"
    echo "  7) Exit"
    echo ""
    read -p "Choose an option (1-7): " choice
else
    choice=$1
fi

case $choice in
    1)
        echo ""
        echo "${GREEN}Starting CareerOps...${NC}"
        echo ""
        echo "${YELLOW}📋 Instructions:${NC}"
        echo ""
        echo "This will start 3 services. Use 3 terminal windows:"
        echo ""
        echo "${BLUE}Terminal 1: Ollama (LLM)${NC}"
        echo "  Run: ollama serve"
        echo "  First time: ollama pull mistral"
        echo ""
        echo "${BLUE}Terminal 2: Backend${NC}"
        echo "  Run: bash start.sh 2"
        echo ""
        echo "${BLUE}Terminal 3: Web Server${NC}"
        echo "  Run: bash start.sh 3"
        echo ""
        echo "Then open: ${BLUE}http://localhost:8000/careerops.html${NC}"
        echo ""
        read -p "Press Enter to continue..."

        echo ""
        echo "${GREEN}✓ Setup instructions shown${NC}"
        echo ""
        echo "Quick commands:"
        echo "  Terminal 1: ollama serve"
        echo "  Terminal 2: cd $PROJECT_DIR && source venv/bin/activate && python3 backend.py"
        echo "  Terminal 3: cd $PROJECT_DIR && python3 -m http.server 8000"
        ;;

    2)
        echo ""
        echo "${GREEN}Starting backend...${NC}"
        echo ""
        python3 "$PROJECT_DIR/backend.py"
        ;;

    3)
        echo ""
        echo "${GREEN}Starting web server...${NC}"
        echo ""
        cd "$PROJECT_DIR"
        echo "${BLUE}Access at: http://localhost:8000/careerops.html${NC}"
        echo ""
        python3 -m http.server 8000
        ;;

    4)
        echo ""
        echo "${BLUE}Checking services...${NC}"
        echo ""

        # Check Ollama
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "${GREEN}✓ Ollama${NC} (http://localhost:11434)"
        else
            echo "${RED}✗ Ollama${NC} (not running - start with: ollama serve)"
        fi

        # Check Backend
        if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
            echo "${GREEN}✓ Backend${NC} (http://localhost:5000)"
        else
            echo "${RED}✗ Backend${NC} (not running - start with: python3 backend.py)"
        fi

        # Check Web Server
        if curl -s http://localhost:8000 > /dev/null 2>&1; then
            echo "${GREEN}✓ Web Server${NC} (http://localhost:8000)"
        else
            echo "${RED}✗ Web Server${NC} (not running - start with: python3 -m http.server 8000)"
        fi

        echo ""
        echo "${BLUE}If all are running, open: http://localhost:8000/careerops.html${NC}"
        ;;

    5)
        echo ""
        echo "${GREEN}Opening browser...${NC}"

        # Try different ways to open browser based on OS
        if command -v open &> /dev/null; then
            open "http://localhost:8000/careerops.html"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:8000/careerops.html"
        elif command -v start &> /dev/null; then
            start "http://localhost:8000/careerops.html"
        else
            echo "${YELLOW}Could not auto-open browser. Visit:${NC}"
            echo "${BLUE}http://localhost:8000/careerops.html${NC}"
        fi
        ;;

    6)
        echo ""
        echo "${BLUE}📚 Documentation Files:${NC}"
        echo ""
        echo "  README.md                    - Project overview & quick start"
        echo "  SETUP.md                     - Detailed installation guide"
        echo "  FEATURES.md                  - What's implemented & roadmap"
        echo "  QUICK_REFERENCE.md           - UI guide & pro tips"
        echo "  IMPLEMENTATION_SUMMARY.md    - Technical details"
        echo ""
        read -p "View which file? (enter name or 'exit'): " doc_choice

        if [ "$doc_choice" != "exit" ] && [ -n "$doc_choice" ]; then
            if [ -f "$PROJECT_DIR/$doc_choice" ]; then
                less "$PROJECT_DIR/$doc_choice"
            else
                echo "${RED}File not found: $doc_choice${NC}"
            fi
        fi
        ;;

    7)
        echo ""
        echo "${GREEN}Goodbye! 👋${NC}"
        exit 0
        ;;

    *)
        echo "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
