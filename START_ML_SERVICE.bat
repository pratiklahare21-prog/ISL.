@echo off
echo ================================================================
echo Starting ISL ML Service with Open-Weight AI
echo ================================================================
echo.

cd /d "%~dp0apps\ml-service"

if not exist ".venv\" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Checking/Installing Python packages...
pip install --quiet fastapi uvicorn mediapipe opencv-python-headless numpy torch websockets python-multipart pydantic 2>nul

echo.
echo ================================================================
echo Starting ML Service on port 8000
echo ================================================================
echo.
echo The service includes:
echo   - MediaPipe hand tracking
echo   - BiLSTM sign recognition
echo   - Open-Weight AI sentence generation (Phi-3/TinyLlama/Rules)
echo.
echo Once you see "Application startup complete", refresh your browser!
echo.
echo Browser URL: http://localhost:5175
echo Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the service
echo ================================================================
echo.

uvicorn app.main:app --reload --port 8000
