@echo off
REM ISL MudraVaani - Complete Run Script (Execution Policy Workaround)
setlocal enabledelayedexpansion

echo ================================================================
echo ISL MudraVaani - Starting All Services
echo ================================================================
echo.

REM Check if setup is needed
if not exist "apps\ml-service\.venv\" (
    echo [SETUP] Python venv not found, creating...
    cd apps\ml-service
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing Python packages...
    pip install -q fastapi uvicorn mediapipe opencv-python-headless numpy torch websockets python-multipart pydantic transformers accelerate 2>nul
    cd ..\..
)

if not exist "ml\data\raw\A.npy" (
    echo [SETUP] Generating synthetic training data...
    cd ml\dataset_tool
    call ..\..\apps\ml-service\.venv\Scripts\python.exe download_isl_dataset.py --dataset synthetic --samples 50 --signs A,B,C,D,E,HELLO,YES,NO,THANK_YOU,HELP 2>nul
    cd ..\..
)

if not exist "ml\models_out\isl_model.pt" (
    echo [SETUP] Copying model...
    if not exist "ml\models_out\" mkdir ml\models_out
    copy /Y "apps\ml\models_out\isl_model.pt" "ml\models_out\isl_model.pt" >nul 2>nul
)

if not exist "apps\server\.env" (
    echo [SETUP] Creating environment files...
    copy /Y "apps\server\.env.example" "apps\server\.env" >nul 2>nul
    echo JWT_SECRET=isl_demo_secret_key_12345678 >> "apps\server\.env"
)

echo.
echo ================================================================
echo Starting Services...
echo ================================================================
echo.

REM Start ML Service
echo [1/3] Starting ML Service (with Open-Weight AI)...
start "ISL ML Service" cmd /k "cd /d %~dp0apps\ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
timeout /t 3 >nul

REM Start Backend (using node directly to bypass execution policy)
echo [2/3] Starting Backend API...
start "ISL Backend" cmd /k "cd /d %~dp0apps\server && node node_modules\tsx\dist\cli.mjs watch src\index.ts"
timeout /t 3 >nul

REM Start Frontend (using vite directly)
echo [3/3] Starting Frontend...
start "ISL Frontend" cmd /k "cd /d %~dp0apps\web && node node_modules\vite\bin\vite.js"
timeout /t 3 >nul

echo.
echo ================================================================
echo All Services Started!
echo ================================================================
echo.
echo Three new windows opened:
echo   1. ISL ML Service (port 8000)
echo   2. ISL Backend (port 3000)
echo   3. ISL Frontend (port 5173)
echo.
echo Wait 10 seconds for services to initialize...
echo.
timeout /t 10
echo.
echo Now opening browser...
start http://localhost:5173
echo.
echo ================================================================
echo FEATURES ENABLED:
echo   [x] Real-time ISL recognition
echo   [x] Open-Weight AI sentence generation (Phi-3/TinyLlama/Rules)
echo   [x] Natural language output
echo   [x] Text-to-speech
echo   [x] Session history
echo.
echo To stop: Close the three terminal windows
echo.
echo For troubleshooting, see FINAL_STATUS.md
echo ================================================================
echo.
pause
