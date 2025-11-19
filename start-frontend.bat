@echo off
REM TradeWise Frontend Startup Script (Windows)

echo ==========================================
echo Starting TradeWise Frontend
echo ==========================================
echo.

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo Starting React development server on http://localhost:3000
echo Press Ctrl+C to stop
echo.

cd frontend
npm start
