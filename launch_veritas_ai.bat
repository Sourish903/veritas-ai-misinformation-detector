@echo off
echo ============================================
echo  Veritas AI - Launcher
echo ============================================

cd /d "%~dp0"

echo.
echo [1/3] Checking dependencies...
python -c "import fastapi, uvicorn, transformers, torch, pydantic" 2>nul
if %errorlevel% neq 0 (
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt --quiet --no-warn-script-location
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies.
        echo Make sure Python is installed and accessible.
        pause
        exit /b 1
    )
)
echo Dependencies OK.

echo.
echo [2/3] Checking trained model...
if not exist "models\best_model_checkpoint\config.json" (
    if not exist "models\config.json" (
        echo ERROR: No trained model found.
        echo Please run the following scripts first:
        echo   python src/data_preprocessing.py
        echo   python src/train_model.py
        pause
        exit /b 1
    )
)
echo Model found.

echo.
echo [3/3] Starting server...
start "" cmd /k "cd /d "%~dp0" && python -m uvicorn src.api:app --reload"

echo Waiting for server to start...
:wait_loop
timeout /t 2 /nobreak > nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>nul
if %errorlevel% equ 0 goto server_ready
timeout /t 2 /nobreak > nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>nul
if %errorlevel% equ 0 goto server_ready
timeout /t 3 /nobreak > nul

:server_ready
echo Opening browser...
start http://127.0.0.1:8000

echo.
echo Server is running. Close the other window to stop it.
