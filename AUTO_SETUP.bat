@echo off
REM Automated setup - no pauses
setlocal

echo ================================================================
echo ISL MudraVaani - Automated Setup
echo ================================================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python not found
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo Step 1: Python found
%PYTHON_CMD% --version

REM Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found
    exit /b 1
)
echo Step 2: Node.js found
node --version

REM Install npm packages
echo Step 3: Installing Node packages...
if not exist "node_modules\" (
    call npm install 2>NUL
)

echo Step 4: Building shared package...
call npm run build:shared 2>NUL

REM Setup Python venv
echo Step 5: Setting up Python environment...
cd apps\ml-service
if not exist ".venv\" (
    %PYTHON_CMD% -m venv .venv 2>NUL
)
call .venv\Scripts\activate.bat 2>NUL
pip install -q -r requirements.txt 2>NUL
cd ..\..

REM Generate synthetic data
echo Step 6: Generating synthetic training data...
cd ml\dataset_tool
call ..\..\apps\ml-service\.venv\Scripts\python.exe download_isl_dataset.py --dataset synthetic --samples 40 2>NUL
cd ..\..

REM Copy or train model
echo Step 7: Preparing model...
if exist "apps\ml\models_out\isl_model.pt" (
    if not exist "ml\models_out\" mkdir ml\models_out
    copy "apps\ml\models_out\isl_model.pt" "ml\models_out\isl_model.pt" >nul 2>nul
    echo Model copied from apps\ml\
) else (
    echo Training model (this takes 3-5 minutes)...
    cd ml\training
    call ..\..\apps\ml-service\.venv\Scripts\python.exe train.py --epochs 40 2>NUL
    cd ..\..
)

REM Setup env files
echo Step 8: Setting up environment files...
if not exist "apps\server\.env" (
    if exist "apps\server\.env.example" (
        copy "apps\server\.env.example" "apps\server\.env" >nul 2>nul
    )
)
if not exist "apps\web\.env" (
    if exist "apps\web\.env.example" (
        copy "apps\web\.env.example" "apps\web\.env" >nul 2>nul
    )
)

REM Start PostgreSQL
echo Step 9: Starting PostgreSQL...
docker compose up -d 2>NUL
timeout /t 5 >nul 2>nul

REM Run migrations
echo Step 10: Running database migrations...
cd apps\server
call npm run db:migrate 2>NUL
cd ..\..

echo.
echo ================================================================
echo SETUP COMPLETE
echo ================================================================
echo.
echo Start services in 3 terminals:
echo.
echo Terminal 1: cd apps\ml-service ^&^& .venv\Scripts\activate ^&^& uvicorn app.main:app --port 8000
echo Terminal 2: cd apps\server ^&^& npm run dev
echo Terminal 3: cd apps\web ^&^& npm run dev
echo.
echo Then open: http://localhost:5173
echo.
echo See START_HERE.md for details
