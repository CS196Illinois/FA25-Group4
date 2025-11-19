@echo off
REM TradeWise Backend Startup Script (Windows)

echo ==========================================
echo Starting TradeWise Backend Server
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and add your API keys
    pause
    exit /b 1
)

echo Starting Flask server on http://localhost:5001
echo Press Ctrl+C to stop
echo.

cd server
python server.py
