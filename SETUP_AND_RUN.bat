@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo ISL MudraVaani - Complete Setup and Run
echo ================================================================
echo.
echo This script will:
echo 1. Install all dependencies (with Python 3.14 workaround)
echo 2. Generate synthetic training data
echo 3. Train/copy model
echo 4. Start all services
echo.

REM Get Python command
python --version >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM Step 1: Install Node dependencies
echo [1/7] Installing Node.js dependencies...
if not exist "node_modules\" (
    call npm install
)
call npm run build:shared
echo.

REM Step 2: Setup Python venv with workaround for Python 3.14
echo [2/7] Setting up Python environment...
cd apps\ml-service

if not exist ".venv\" (
    %PYTHON_CMD% -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing Python packages (with open-weight AI support)...
pip install --upgrade pip >nul 2>nul
pip install -q -r requirements_py314.txt 2>nul
if %errorlevel% neq 0 (
    echo Trying with original requirements...
    pip install -q -r requirements.txt 2>nul
)

cd ..\..
echo.

REM Step 3: Generate synthetic training data
echo [3/7] Generating synthetic training data...
cd ml\dataset_tool

if not exist "..\data\raw\A.npy" (
    call ..\..\apps\ml-service\.venv\Scripts\python.exe download_isl_dataset.py --dataset synthetic --samples 50 --signs A,B,C,D,E,F,G,H,I,J,HELLO,YES,NO,THANK_YOU,HELP,PLEASE,SORRY,MY,NAME,YOU
)

cd ..\..
echo.

REM Step 4: Copy or train model
echo [4/7] Preparing model...
if not exist "ml\models_out\" mkdir ml\models_out

if exist "apps\ml\models_out\isl_model.pt" (
    copy /Y "apps\ml\models_out\isl_model.pt" "ml\models_out\isl_model.pt" >nul 2>nul
    echo Model copied from apps\ml\
) else if not exist "ml\models_out\isl_model.pt" (
    echo Training model (3-5 minutes)...
    cd ml\training
    call ..\..\apps\ml-service\.venv\Scripts\python.exe train.py --epochs 40 --batch-size 16
    cd ..\..
)
echo.

REM Step 5: Setup environment files
echo [5/7] Setting up environment files...
if not exist "apps\server\.env" (
    copy /Y "apps\server\.env.example" "apps\server\.env" >nul 2>nul
    echo apps\server\.env created - REMEMBER TO SET JWT_SECRET
)
if not exist "apps\web\.env" (
    copy /Y "apps\web\.env.example" "apps\web\.env" >nul 2>nul
)
echo.

REM Step 6: Start PostgreSQL
echo [6/7] Starting PostgreSQL...
docker compose up -d >nul 2>nul
timeout /t 5 >nul 2>nul

cd apps\server
call npm run db:migrate >nul 2>nul
cd ..\..
echo.

REM Step 7: Display run instructions
echo [7/7] Setup complete!
echo ================================================================
echo.
echo OPEN-WEIGHT AI: Integrated with fallback!
echo  - Will attempt to use Phi-3 or TinyLlama if available
echo  - Falls back to rule-based if LLM not available
echo  - Generates natural sentences from sign sequences
echo.
echo TO RUN - Open 3 terminals:
echo.
echo Terminal 1 - ML Service (with AI):
echo   cd apps\ml-service
echo   .venv\Scripts\activate
echo   uvicorn app.main:app --reload --port 8000
echo.
echo Terminal 2 - Backend:
echo   cd apps\server
echo   npm run dev
echo.
echo Terminal 3 - Frontend:
echo   cd apps\web
echo   npm run dev
echo.
echo Then open: http://localhost:5173
echo.
echo ================================================================
echo FEATURES:
echo  [x] Real-time ISL recognition
echo  [x] Open-weight AI sentence generation
echo  [x] Synthetic training data
echo  [x] Model evaluation system
echo  [x] Text-to-speech
echo ================================================================
echo.

pause
