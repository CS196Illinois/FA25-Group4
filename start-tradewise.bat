@echo off
REM TradeWise Complete Startup Script (Windows)
REM Starts both backend and frontend servers automatically

echo ==========================================
echo Starting TradeWise Application
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and add your API keys
    pause
    exit /b 1
)

echo [1/2] Starting Backend Server (Flask)...
start "TradeWise Backend" cmd /k "cd /d %~dp0server && python server.py"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server (React)...
start "TradeWise Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ==========================================
echo TradeWise is starting!
echo ==========================================
echo.
echo Two new windows have opened:
echo   1. Backend Server  (http://localhost:5001)
echo   2. Frontend Server (http://localhost:3000)
echo.
echo Your browser will open automatically in a few seconds.
echo.
echo To stop: Close both terminal windows or press Ctrl+C in each
echo.
pause
