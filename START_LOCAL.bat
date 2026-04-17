@echo off
title CircuitMind AI — Local Launcher
color 0A
cls

echo.
echo  ============================================================
echo    CircuitMind AI  ^|  EEE Network Analysis Solver
echo  ============================================================
echo.

:: ── Check Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Download Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo  [1/3] Checking dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  [1/3] Dependencies OK.

:: ── Set environment for local run (no PIN needed) ─────────────
echo  [2/3] Configuring local environment...
set APP_PIN=
set FLASK_ENV=development
set PYTHONUNBUFFERED=1

:: ── Open browser after 2s delay ───────────────────────────────
echo  [3/3] Starting server...
echo.
echo  ============================================================
echo   LOCAL URL:    http://localhost:5000
echo   Press Ctrl+C to stop the server
echo  ============================================================
echo.

:: Open browser in background after 2.5 seconds
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

:: ── Start Flask server ────────────────────────────────────────
python app.py

pause
