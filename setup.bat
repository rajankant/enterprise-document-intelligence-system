@echo off
REM Setup script for Windows
REM Enterprise Document Intelligence System

setlocal enabledelayedexpansion

echo.
echo ==================== Enterprise Document Intelligence System ====================
echo.

REM Check if .venv exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Check .env file
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file and add your OPENAI_API_KEY
)

echo.
echo ==================== Setup Complete! ====================
echo.
echo Choose what to run:
echo.
echo 1^) Streamlit UI:    streamlit run ui/streamlit_app.py
echo 2^) FastAPI Server:  python -m uvicorn app.api.main:app --reload
echo 3^) Run Tests:       pytest tests/ -v
echo 4^) Test OCR:        python tests/test_ocr.py
echo.
echo ====================================================================
echo.

pause
