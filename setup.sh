#!/bin/bash
# Start scripts for the project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Enterprise Document Intelligence System ===${NC}"
echo ""

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install requirements
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit .env file and add your OPENAI_API_KEY${NC}"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Choose what to run:"
echo "1) Streamlit UI:    streamlit run ui/streamlit_app.py"
echo "2) FastAPI Server:  python -m uvicorn app.api.main:app --reload"
echo "3) Run Tests:       pytest tests/ -v"
echo "4) Test OCR:        python tests/test_ocr.py"
echo ""
