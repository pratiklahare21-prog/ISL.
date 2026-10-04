@echo off
REM ISL MudraVaani - Setup Script for Windows
REM This script attempts to set up the environment despite restrictions

echo ============================================================
echo ISL MudraVaani - Environment Setup
echo ============================================================
echo.

REM Check Python version
echo [1/10] Checking Python version...
python --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    py --version 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python not accessible
        goto :error
    )
)
echo.

REM Check Node.js
echo [2/10] Checking Node.js...
node --version 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found or not accessible
    goto :error
)
echo.

REM Check npm
echo [3/10] Checking npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found
    goto :error
)
echo.

REM Check Docker
echo [4/10] Checking Docker...
docker --version 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Docker not found - you'll need PostgreSQL manually
) else (
    echo Docker detected
)
echo.

REM Check if node_modules exists
echo [5/10] Checking Node.js dependencies...
if exist "node_modules\" (
    echo Node modules already installed
) else (
    echo Node modules NOT installed
    echo Please run: npm install
)
echo.

REM Check if Python venv exists
echo [6/10] Checking Python virtual environment...
if exist "apps\ml-service\.venv\" (
    echo Python venv exists
) else (
    echo Python venv NOT created
    echo Please run: cd apps\ml-service && python -m venv .venv
)
echo.

REM Check model
echo [7/10] Checking for trained model...
if exist "ml\models_out\isl_model.pt" (
    echo Model found at ml\models_out\isl_model.pt
) else if exist "apps\ml\models_out\isl_model.pt" (
    echo Model found at apps\ml\models_out\isl_model.pt
    echo Copying to expected location...
    if not exist "ml\models_out\" mkdir "ml\models_out"
    copy "apps\ml\models_out\isl_model.pt" "ml\models_out\isl_model.pt" >nul
    echo Model copied
) else (
    echo [WARNING] No trained model found
)
echo.

REM Check training data
echo [8/10] Checking training data...
dir /b "ml\data\raw\*.npy" 2>nul | findstr /v "^$" >nul
if %errorlevel% equ 0 (
    echo Training data found
) else (
    echo [WARNING] No training data found
)
echo.

REM Check env files
echo [9/10] Checking environment files...
if exist "apps\server\.env" (
    echo apps\server\.env exists
) else (
    echo [WARNING] apps\server\.env missing
    if exist "apps\server\.env.example" (
        echo Creating from .env.example...
        copy "apps\server\.env.example" "apps\server\.env" >nul
        echo [ACTION REQUIRED] Edit apps\server\.env and set JWT_SECRET
    )
)

if exist "apps\web\.env" (
    echo apps\web\.env exists
) else (
    echo [WARNING] apps\web\.env missing
    if exist "apps\web\.env.example" (
        echo Creating from .env.example...
        copy "apps\web\.env.example" "apps\web\.env" >nul
    )
)
echo.

REM Final status
echo [10/10] Final Status Check
echo ============================================================
echo.

echo PYTHON VERSION CHECK:
python --version 2>nul || py --version
echo NOTE: Requires Python 3.10 or 3.11 (NOT 3.12+)
echo.

echo NODE.JS VERSION CHECK:
node --version 2>nul
echo.

echo CRITICAL ISSUES FOUND:
echo - Python version may be incompatible (need 3.10 or 3.11)
echo - Dependencies may not be installed
echo - Open-weight AI integration is MISSING
echo - Training data not included
echo.

echo NEXT STEPS:
echo 1. Install Python 3.11 from python.org
echo 2. Set execution policy: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
echo 3. Install Node dependencies: npm install
echo 4. Build shared package: npm run build:shared
echo 5. Create Python venv: cd apps\ml-service && py -3.11 -m venv .venv
echo 6. Activate venv: .venv\Scripts\activate
echo 7. Install Python packages: pip install -r requirements.txt
echo 8. Start PostgreSQL: docker compose up -d
echo 9. Run migrations: cd apps\server && npm run db:migrate
echo 10. Start services (see README.md)
echo.

echo See FINAL_QA_REPORT.md for complete details
echo.
pause
goto :end

:error
echo.
echo ============================================================
echo SETUP FAILED - See errors above
echo ============================================================
echo.
pause
exit /b 1

:end
