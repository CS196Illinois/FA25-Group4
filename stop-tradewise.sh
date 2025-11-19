#!/bin/bash
# Stop TradeWise servers

echo "Stopping TradeWise servers..."

if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✓ Backend stopped (PID: $BACKEND_PID)"
    else
        echo "✗ Backend not running"
    fi
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✓ Frontend stopped (PID: $FRONTEND_PID)"
    else
        echo "✗ Frontend not running"
    fi
    rm .frontend.pid
fi

# Also kill any node processes running npm/react-scripts (cleanup)
pkill -f "react-scripts" 2>/dev/null && echo "✓ Cleaned up React processes"

echo ""
echo "TradeWise stopped"
