@echo off
REM Stop TradeWise servers (Windows)

echo Stopping TradeWise servers...
echo.

REM Kill Python processes running server.py
taskkill /FI "WINDOWTITLE eq TradeWise Backend*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend server stopped
) else (
    echo [  ] Backend not running or already stopped
)

REM Kill Node processes running npm start
taskkill /FI "WINDOWTITLE eq TradeWise Frontend*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend server stopped
) else (
    echo [  ] Frontend not running or already stopped
)

echo.
echo TradeWise stopped
pause
