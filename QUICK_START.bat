@echo off
REM ISL MudraVaani - Quick Start with Synthetic Data
REM This script sets up and runs the project with test data

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo   ISL MudraVaani - Quick Start Setup
echo ================================================================
echo.
echo This script will:
echo 1. Check prerequisites
echo 2. Generate synthetic training data (for testing)
echo 3. Train a test model
echo 4. Set up the environment
echo 5. Attempt to start all services
echo.
echo NOTE: Synthetic data is for TESTING only. Real accuracy requires
echo       recording actual sign language data.
echo.
pause

REM ============================================================
REM STEP 1: Check Prerequisites
REM ============================================================
echo.
echo [STEP 1/8] Checking prerequisites...
echo ----------------------------------------------------------------
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found
        goto :error
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

REM Check Python version
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.
echo [WARNING] This project requires Python 3.10 or 3.11
echo           Python 3.12+ breaks MediaPipe compatibility
echo           Current version: %PYTHON_VERSION%
echo.

REM Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found
    echo Please install Node.js 18.18+ from nodejs.org
    goto :error
)
node --version
echo.

REM ============================================================
REM STEP 2: Install Node Dependencies
REM ============================================================
echo.
echo [STEP 2/8] Installing Node.js dependencies...
echo ----------------------------------------------------------------
echo.

if not exist "node_modules\" (
    echo Running npm install...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed
        echo Try running PowerShell as Admin and execute:
        echo Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        goto :error
    )
) else (
    echo Node modules already installed
)

echo.
echo Building shared package...
call npm run build:shared
if %errorlevel% neq 0 (
    echo [WARNING] Build shared failed, but continuing...
)
echo.

REM ============================================================
REM STEP 3: Setup Python Virtual Environment
REM ============================================================
echo.
echo [STEP 3/8] Setting up Python virtual environment...
echo ----------------------------------------------------------------
echo.

cd apps\ml-service

if not exist ".venv\" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv
        cd ..\..
        goto :error
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [WARNING] Could not activate venv automatically
    echo Please activate manually: .venv\Scripts\activate
)

echo.
echo Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    echo.
    echo This is likely due to Python version incompatibility.
    echo MediaPipe requires Python 3.10 or 3.11 (NOT 3.12+)
    echo.
    echo Please install Python 3.11 from python.org
    cd ..\..
    goto :error
)

cd ..\..
echo.

REM ============================================================
REM STEP 4: Generate Synthetic Training Data
REM ============================================================
echo.
echo [STEP 4/8] Generating synthetic training data...
echo ----------------------------------------------------------------
echo.
echo [IMPORTANT] Generating SYNTHETIC data for testing only.
echo             Real accuracy requires recording actual sign data.
echo.

cd ml\dataset_tool

call ..\..\apps\ml-service\.venv\Scripts\python.exe download_isl_dataset.py --dataset synthetic --signs A,B,C,D,E,F,G,H,I,J,HELLO,YES,NO,THANK_YOU,HELP,PLEASE,SORRY,MY,NAME,YOU --samples 40

if %errorlevel% neq 0 (
    echo [ERROR] Synthetic data generation failed
    cd ..\..
    goto :error
)

cd ..\..
echo.

REM ============================================================
REM STEP 5: Copy Existing Model or Train New One
REM ============================================================
echo.
echo [STEP 5/8] Checking for trained model...
echo ----------------------------------------------------------------
echo.

if exist "apps\ml\models_out\isl_model.pt" (
    echo Found existing model at apps\ml\models_out\isl_model.pt
    echo Copying to expected location...
    
    if not exist "ml\models_out\" mkdir ml\models_out
    copy "apps\ml\models_out\isl_model.pt" "ml\models_out\isl_model.pt" >nul
    echo Model copied
) else (
    echo No existing model found. Training new model...
    echo This will take 3-5 minutes on CPU...
    echo.
    
    cd ml\training
    call ..\..\apps\ml-service\.venv\Scripts\python.exe train.py --epochs 40 --batch-size 16
    
    if %errorlevel% neq 0 (
        echo [ERROR] Model training failed
        cd ..\..
        goto :error
    )
    
    cd ..\..
)
echo.

REM ============================================================
REM STEP 6: Run Model Evaluation
REM ============================================================
echo.
echo [STEP 6/8] Evaluating model accuracy...
echo ----------------------------------------------------------------
echo.

cd ml\evaluation
call ..\..\apps\ml-service\.venv\Scripts\python.exe evaluate_model.py

if %errorlevel% neq 0 (
    echo [WARNING] Evaluation failed, but continuing...
) else (
    echo.
    echo Evaluation results saved to ml/evaluation/evaluation_results/
)

cd ..\..
echo.

REM ============================================================
REM STEP 7: Setup Environment Files
REM ============================================================
echo.
echo [STEP 7/8] Setting up environment files...
echo ----------------------------------------------------------------
echo.

if not exist "apps\server\.env" (
    if exist "apps\server\.env.example" (
        copy "apps\server\.env.example" "apps\server\.env" >nul
        echo Created apps\server\.env
        echo.
        echo [ACTION REQUIRED] Edit apps\server\.env and set JWT_SECRET
        echo Press any key after setting JWT_SECRET...
        pause >nul
    )
) else (
    echo apps\server\.env exists
)

if not exist "apps\web\.env" (
    if exist "apps\web\.env.example" (
        copy "apps\web\.env.example" "apps\web\.env" >nul
        echo Created apps\web\.env
    )
) else (
    echo apps\web\.env exists
)
echo.

REM ============================================================
REM STEP 8: Start PostgreSQL
REM ============================================================
echo.
echo [STEP 8/8] Starting PostgreSQL...
echo ----------------------------------------------------------------
echo.

docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting PostgreSQL container...
    docker compose up -d
    if %errorlevel% equ 0 (
        echo PostgreSQL started successfully
        timeout /t 5 >nul
        
        echo.
        echo Running database migrations...
        cd apps\server
        call npm run db:migrate
        cd ..\..
    ) else (
        echo [WARNING] Docker compose failed
        echo Please start PostgreSQL manually or use docker compose up -d
    )
) else (
    echo [WARNING] Docker not found
    echo Please start PostgreSQL manually or install Docker
)
echo.

REM ============================================================
REM FINAL STATUS
REM ============================================================
echo.
echo ================================================================
echo   Setup Complete!
echo ================================================================
echo.
echo MODEL STATUS:
if exist "ml\models_out\isl_model.pt" (
    echo   [OK] Model trained and ready
) else (
    echo   [MISSING] No model found
)
echo.
echo TRAINING DATA:
dir /b ml\data\raw\*.npy 2>nul | find /c /v "" >nul
if %errorlevel% equ 0 (
    for /f %%i in ('dir /b ml\data\raw\*.npy 2^>nul ^| find /c /v ""') do echo   [OK] %%i sign files
) else (
    echo   [MISSING] No training data
)
echo.
echo EVALUATION RESULTS:
if exist "ml\evaluation\evaluation_results\evaluation_results.json" (
    echo   [OK] Accuracy metrics available
    echo   See: ml\evaluation\evaluation_results\evaluation_results.json
) else (
    echo   [MISSING] Run evaluation: cd ml\evaluation && python evaluate_model.py
)
echo.
echo ================================================================
echo   HOW TO RUN
echo ================================================================
echo.
echo Open 3 SEPARATE terminals and run:
echo.
echo   Terminal 1 - ML Service:
echo   cd apps\ml-service
echo   .venv\Scripts\activate
echo   uvicorn app.main:app --reload --port 8000
echo.
echo   Terminal 2 - Backend API:
echo   cd apps\server
echo   npm run dev
echo.
echo   Terminal 3 - Frontend:
echo   cd apps\web
echo   npm run dev
echo.
echo Then open: http://localhost:5173
echo.
echo ================================================================
echo   IMPORTANT NOTES
echo ================================================================
echo.
echo 1. SYNTHETIC DATA: Current model uses synthetic test data
echo    - This is for PIPELINE TESTING only
echo    - Accuracy will be LOW (synthetic != real signs)
echo    - For real accuracy, record actual sign data:
echo      cd ml\dataset_tool
echo      python collect.py --label A --samples 40
echo.
echo 2. MISSING: Open-weight AI for sentence generation
echo    - Currently: word-by-word recognition only
echo    - Needed: Add Llama-3.2-1B or Phi-3 for natural sentences
echo    - See START_HERE.md section "HOW TO ADD OPEN-WEIGHT AI"
echo.
echo 3. For complete details, read:
echo    - START_HERE.md (quick setup guide)
echo    - FINAL_QA_REPORT.md (comprehensive audit)
echo    - PROJECT_STATUS.md (technical details)
echo.
pause
goto :end

:error
echo.
echo ================================================================
echo   SETUP FAILED
echo ================================================================
echo.
echo See errors above for details.
echo.
echo Common fixes:
echo 1. Install Python 3.11 from python.org
echo 2. Run PowerShell as Admin:
echo    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
echo 3. Install Node.js 18.18+ from nodejs.org
echo 4. Install Docker Desktop from docker.com
echo.
echo For help, see START_HERE.md
echo.
pause
exit /b 1

:end
echo.
echo Script complete. Follow instructions above to start services.
echo.
